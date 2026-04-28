"""Race harness — concurrency, retry classifier, race_done emitter, headlines.

Owns:

  * D-38 ``asyncio.Semaphore(8)`` concurrency cap (env-overridable via
    ``RACE_HARNESS_CONCURRENCY``) so all in-flight (lane × task × run_idx)
    coroutines share one budget instead of stampeding the Anthropic Tier-1
    rate cap.
  * Closed-tuple retry classifier ``TRANSIENT_RETRY_TYPES`` — only the four
    Anthropic transient infra exceptions are retried; the injected-fault
    exception type from race/failure.py is NEVER caught here. Adding it would
    silently mask the very faults the race demo is testing.
  * Per-run ``asyncio.wait_for(..., PER_RUN_TIMEOUT_S)`` so a wedged runner
    cannot deadlock the harness.
  * D-39 ``race_done`` event emission (single per ``run_race`` call) with
    ``t_end_ms``, ``total_runs``, ``lane_failed_reasons``, and the per-(lane,
    task) headline sentence produced by ``failure_mode_classifier``
    (RACE-06).
  * D-41 + Phase 6 D-08 NEVER_COALESCE preservation: ``fault_observed``
    events are forwarded by recorders inside runners; the harness does not
    filter, coalesce, or re-emit them.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import time
import uuid
from typing import Any, Awaitable, Callable

import anthropic

from ..trace import TraceRecorder
from .classifier import failure_mode_classifier
# NOTE: race/failure.py exports the injected-fault exception type; it is
# DELIBERATELY not imported here. Including it in TRANSIENT_RETRY_TYPES (or
# referencing it in any except arm) would mask the faults under test.
from .failure import FailureScriptEntry  # typing only
from .metrics import aggregate_for_classifier
from .runners import run_hybrid, run_pure_a2a, run_pure_mcp
from .tasks import TASK_CONFIGS
from .types import HardnessProfile, HardnessType, RaceResult, ScoreCard, TaskSpec


# ---------------------------------------------------------------------------
# Module constants — pinned at load time per RESEARCH §2 + master design.
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-6"
# SEED_DISCLOSURE: Anthropic's chat-completion SDK has NO seed parameter
# (RESEARCH §3). This constant is a methodology-disclosure token only —
# documented in the README as part of the harness reproducibility statement
# alongside temperature=0 and the locked failure_script.
SEED_DISCLOSURE = 42
TEMPERATURE = 0.0
PER_RUN_TIMEOUT_S = 120

# D-38: Tier-1 sized default; envvar override allowed for power users.
_CONC: int = int(os.getenv("RACE_HARNESS_CONCURRENCY", "8"))
_SEMAPHORE: asyncio.Semaphore = asyncio.Semaphore(_CONC)

# Closed tuple — no Exception fallback, no broad catch. If a new transient
# Anthropic type appears, the harness fails loudly so we add it explicitly.
TRANSIENT_RETRY_TYPES: tuple[type[BaseException], ...] = (
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.InternalServerError,
    anthropic.RateLimitError,
)


# Runner registry — keyed by lane string. Imported once at module load so the
# closed set is a structural constant.
_RUNNERS: dict[str, Callable[..., Awaitable[RaceResult]]] = {
    "pure_mcp": run_pure_mcp,
    "pure_a2a": run_pure_a2a,
    "hybrid": run_hybrid,
}


__all__ = [
    "run_race",
    "MODEL",
    "TEMPERATURE",
    "PER_RUN_TIMEOUT_S",
    "SEED_DISCLOSURE",
    "TRANSIENT_RETRY_TYPES",
]


# ---------------------------------------------------------------------------
# Per-run retry classifier (D-38) + lane_failed result builder.
# ---------------------------------------------------------------------------


def _build_lane_failed_result(
    run_id: str,
    lane: str,
    task_spec: TaskSpec,
    *,
    reason: str,
) -> RaceResult:
    """Construct a RaceResult representing a lane infra failure (D-39).

    ``reason`` is one of: ``"timeout"`` (per-run wait_for fired) or the
    ``type(exc).__name__`` of the transient Anthropic exception that
    exhausted the 3-attempt retry budget — e.g., ``"RateLimitError"``,
    ``"APIConnectionError"``, ``"APITimeoutError"``,
    ``"InternalServerError"``.

    The reason is stashed on ``ScoreCard.failure_mode`` (set to
    ``"lane_failed"``) and surfaced separately as ``RaceResult``-level
    metadata via the ``hardness_profile`` passthrough so the
    classifier's ``lane_failed`` template (D-35 sixth template) can
    look it up at race_done aggregation time.
    """
    sc = ScoreCard(
        success=False,
        ttff_ms=0,
        recovered=False,
        wasted_tokens_before_detection=0,
        failure_mode="lane_failed",
        cost_usd=0.0,
        latency_ms=0,
    )
    # Attach reason as a runtime attribute so the post-run classifier
    # aggregator can pick it up without a schema change to ScoreCard.
    # (Plan 11 test_harness asserts the reason flows through.)
    setattr(sc, "lane_failed_reason", reason)
    return RaceResult(
        run_id=run_id,
        lane=lane,
        task_id=task_spec.task_id,
        hardness_profile=task_spec.hardness_profile,
        score_card=sc,
        trace_id=run_id,
    )


async def _run_one_with_retry(
    lane: str,
    task_spec: TaskSpec,
    run_id: str,
    recorder: TraceRecorder | None,
    failure_script: list[FailureScriptEntry],
    sonnet_client: Any,
    hybrid_plan: dict[str, Any] | None = None,
) -> RaceResult:
    """Per-(lane × run_idx) execution with closed-tuple retry classifier.

    Backoff math: worst-case 3-attempt window = (2^0+1)+(2^1+1) ≈ 4-6s
    cumulative sleep, well inside the 120s per-run timeout. Each attempt
    itself is wrapped in ``asyncio.wait_for(..., PER_RUN_TIMEOUT_S)``;
    the harness-level cap on total wall-clock per cell is the caller's
    responsibility.

    ContextVar safety (D-38 + threat T-07-09-02): the runners (Plan 09)
    own ``ACTIVE_FAULTS`` / ``MCP_TOOL_CONTEXT`` reset in their own
    ``finally`` blocks. The harness MUST NOT touch those contextvars
    directly here — but the harness MUST NEVER swallow ``BaseException``,
    so a cancellation (e.g., wait_for timeout) propagates into the
    runner's ``finally`` and the contextvar reset runs even if the worker
    task is cancelled.
    """
    runner = _RUNNERS[lane]
    runner_kwargs: dict[str, Any] = {}
    if lane == "hybrid":
        runner_kwargs["hybrid_plan"] = hybrid_plan
    last_exc: BaseException | None = None
    for attempt in range(3):
        try:
            return await asyncio.wait_for(
                runner(
                    task_spec,
                    run_id,
                    recorder,
                    failure_script,
                    sonnet_client,
                    **runner_kwargs,
                ),
                timeout=PER_RUN_TIMEOUT_S,
            )
        except TRANSIENT_RETRY_TYPES as exc:
            last_exc = exc
            await asyncio.sleep(2 ** attempt + random.uniform(0, 1))
            continue
        except asyncio.TimeoutError:
            return _build_lane_failed_result(
                run_id, lane, task_spec, reason="timeout"
            )
        # NOTE: no broad-Exception arm — the injected-fault type MUST bubble.
    # Exhausted 3 transient retries.
    return _build_lane_failed_result(
        run_id, lane, task_spec, reason=type(last_exc).__name__
    )


async def _run_one_under_semaphore(
    lane: str,
    task_spec: TaskSpec,
    run_id: str,
    recorder: TraceRecorder | None,
    failure_script: list[FailureScriptEntry],
    sonnet_client: Any,
    hybrid_plan: dict[str, Any] | None = None,
) -> RaceResult:
    """Acquire the harness-wide ``_SEMAPHORE`` then run with retry policy.

    Semaphore acquire wraps the ENTIRE retry loop so the cap (D-38)
    measures concurrent in-flight runs, not concurrent retry attempts.
    """
    async with _SEMAPHORE:
        return await _run_one_with_retry(
            lane,
            task_spec,
            run_id,
            recorder,
            failure_script,
            sonnet_client,
            hybrid_plan,
        )


# ---------------------------------------------------------------------------
# Headline templates (D-35) — six locked sentence templates.
#
# The classifier in race/classifier.py returns the FULL templated sentence
# directly (not just the enum tag), so HEADLINE_SENTENCES is unused — kept
# here as a documentation marker for the six template categories so the
# Plan 11 enum-drift integrity check has a stable reference.
# ---------------------------------------------------------------------------

HEADLINE_TEMPLATE_TAGS: frozenset[str] = frozenset({
    "recovered",
    "gave_up",
    "kept_going_without_noticing",
    "kept_going_to_failure",
    "indeterminate",
    "lane_failed",
})


_VALID_LANES: frozenset[str] = frozenset({"pure_mcp", "pure_a2a", "hybrid"})


def _per_run_tag(result: RaceResult) -> str:
    """Map a RaceResult back to one of the five Detector terminal tags + lane_failed.

    Used by the harness to reduce per-run RaceResults into the ``per_run_tags``
    list consumed by ``failure_mode_classifier``. Mirrors Detector.finalize_at_done
    semantics (D-34) without re-running the state machine — the runner already
    minted these via its scorer.
    """
    sc = result.score_card
    if sc.failure_mode == "lane_failed":
        return "lane_failed"
    # Runner scorers in Plan 09 set failure_mode in
    # {"ok", "schema_drift_pass", "rate_limit_recovered", ...} on success and
    # task-specific failure strings on failure. Reduce to the 5-tag space.
    if sc.success and sc.recovered:
        return "recovered"
    if sc.success and not sc.recovered:
        return "kept_going_without_noticing"
    if not sc.success and sc.recovered:
        return "gave_up"
    if not sc.success and not sc.recovered:
        return "kept_going_to_failure"
    return "indeterminate"


def _characteristic_tool_for(task_id: str) -> str | None:
    """First failure_script target's bare tool name — used by pure_mcp's
    headline phrase generator (D-37). Pulled from the locked TASK_CONFIGS.
    """
    cfg, _, _ = TASK_CONFIGS[task_id]
    if not cfg.failure_script:
        return None
    target = cfg.failure_script[0].target
    return target.split(".")[-1] if "." in target else target


# ---------------------------------------------------------------------------
# run_race — fan-out orchestrator (D-38, D-39, D-41).
# ---------------------------------------------------------------------------

async def run_race(
    task_specs: list[TaskSpec],
    lanes: list[str],
    n: int,
    *,
    recorder_factory: Callable[..., TraceRecorder],
    ws_emitter: Callable[[dict[str, Any]], None],
    hybrid_plans: dict[str, Any] | None = None,
) -> dict[tuple[str, str], list[RaceResult]]:
    """Fan out (lane × task × run_idx) tuples under ``_SEMAPHORE``.

    Args:
      task_specs: list of TaskSpec — every ``task_id`` MUST be present in
        ``TASK_CONFIGS`` (Plan 08); else ValueError at validation time.
      lanes: subset of ``{"pure_mcp", "pure_a2a", "hybrid"}``.
      n: runs per (task, lane) cell, ≥1.
      recorder_factory: callable ``(run_id, lane, task_id) -> TraceRecorder``
        — Phase 6 wires this to a RunWriter-backed recorder + ws fan-out.
      ws_emitter: callable ``(event_dict) -> None`` — Phase 6 ws bus.
      hybrid_plans: optional per-task hybrid plan override; falls back to the
        cfg.hybrid_plan from task_config.yaml.

    Returns:
      dict keyed by ``(lane, task_id)`` with the n RaceResults for that cell.

    fault_observed forwarding: runners emit ``fault_observed`` to their per-run
    recorder; the recorder (Phase 6 wiring) is responsible for forwarding to
    ws_emitter. The harness MUST NOT re-forward — that would double-emit. The
    harness MUST NOT filter or coalesce — D-41 + Phase 6 D-08 NEVER_COALESCE
    list reaffirms ``fault_observed`` is preserved verbatim end-to-end.
    """
    # Input validation — fail fast on bad caller args.
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    bad_lanes = [ln for ln in lanes if ln not in _VALID_LANES]
    if bad_lanes:
        raise ValueError(
            f"unknown lanes {bad_lanes!r}; valid: {sorted(_VALID_LANES)}"
        )
    bad_tasks = [s.task_id for s in task_specs if s.task_id not in TASK_CONFIGS]
    if bad_tasks:
        raise ValueError(
            f"unknown task_ids {bad_tasks!r}; valid: {sorted(TASK_CONFIGS.keys())}"
        )

    # Single shared Anthropic client per run_race call — runners use it at
    # most once each (v1 deterministic runners may not invoke it at all).
    sonnet_client: Any
    try:
        sonnet_client = anthropic.AsyncAnthropic()
    except Exception:  # noqa: BLE001 — ANTHROPIC_API_KEY missing is a configuration error
        sonnet_client = None  # runners tolerate None in v1 (D-21 + Plan 09)

    # Build the work list and per-run recorder map (so we can pull events
    # post-run for classifier aggregation).
    schedule: list[tuple[str, TaskSpec, str, TraceRecorder]] = []
    for spec in task_specs:
        cfg, _targets, _binds = TASK_CONFIGS[spec.task_id]
        # Materialize failure_script entries from the cfg's pydantic models
        # into FailureScriptEntry dataclasses (race/failure.py contract).
        failure_script: list[FailureScriptEntry] = [
            FailureScriptEntry(
                kind=e.kind,
                target=e.target,
                after_calls=e.after_calls,
                duration_calls=e.duration_calls,
            )
            for e in cfg.failure_script
        ]
        for lane in lanes:
            for run_idx in range(n):
                run_id = (
                    f"{lane}-{spec.task_id}-{run_idx}-{uuid.uuid4().hex[:6]}"
                )
                recorder = recorder_factory(
                    run_id=run_id, lane=lane, task_id=spec.task_id
                )
                schedule.append((lane, spec, run_id, recorder))

        # Stash per-task failure_script + hybrid plan in a closure-readable map.
    # We rebuild per-cell below; doing it inline keeps the schedule list flat.

    # Schedule each tuple as a task. We use create_task so the semaphore
    # acquire happens cooperatively as runners race for the budget.
    async def _one(
        lane: str,
        spec: TaskSpec,
        run_id: str,
        recorder: TraceRecorder,
    ) -> RaceResult:
        cfg, _t, _b = TASK_CONFIGS[spec.task_id]
        failure_script = [
            FailureScriptEntry(
                kind=e.kind,
                target=e.target,
                after_calls=e.after_calls,
                duration_calls=e.duration_calls,
            )
            for e in cfg.failure_script
        ]
        hp: dict[str, Any] | None = None
        if lane == "hybrid":
            if hybrid_plans is not None and spec.task_id in hybrid_plans:
                hp = hybrid_plans[spec.task_id]
            else:
                hp = cfg.hybrid_plan.model_dump()
        return await _run_one_under_semaphore(
            lane,
            spec,
            run_id,
            recorder,
            failure_script,
            sonnet_client,
            hp,
        )

    pending = [
        asyncio.create_task(_one(lane, spec, run_id, rec))
        for (lane, spec, run_id, rec) in schedule
    ]
    # No return_exceptions: the retry classifier converts everything except
    # the injected-fault type into a RaceResult; injected-fault propagation
    # here is a real bug — let it crash with a full traceback.
    results: list[RaceResult] = await asyncio.gather(*pending)

    # Build (lane, task_id) -> [RaceResult] grouping AND collect per-run
    # recorder events for the classifier.
    grouped: dict[tuple[str, str], list[RaceResult]] = {}
    events_by_cell: dict[tuple[str, str], list[list[dict[str, Any]]]] = {}
    for (lane, spec, _run_id, rec), rr in zip(schedule, results):
        key = (lane, spec.task_id)
        grouped.setdefault(key, []).append(rr)
        events_by_cell.setdefault(key, []).append(list(rec.events))

    # Per-(lane, task) headline + lane_failed_reasons aggregation.
    headlines: dict[tuple[str, str], str] = {}
    lane_failed_reasons: dict[str, list[str]] = {ln: [] for ln in lanes}
    for (lane, task_id), cell_results in grouped.items():
        per_run_tags = [_per_run_tag(rr) for rr in cell_results]
        # Capture lane_failed_reason runtime attrs for D-39 race_done payload.
        for rr in cell_results:
            reason = getattr(rr.score_card, "lane_failed_reason", None)
            if reason:
                lane_failed_reasons.setdefault(lane, []).append(reason)
        agg = aggregate_for_classifier(
            events_by_cell[(lane, task_id)],
            task_id=task_id,
            lane=lane,
            characteristic_tool=_characteristic_tool_for(task_id),
        )
        # If every run in the cell failed at the lane level, surface the
        # most common reason for the sixth-template lane_failed clause.
        if all(t == "lane_failed" for t in per_run_tags):
            reasons = [
                getattr(rr.score_card, "lane_failed_reason", "infra error")
                for rr in cell_results
            ]
            agg = dict(agg)
            agg["lane_failed_reason"] = max(set(reasons), key=reasons.count)
        headline = failure_mode_classifier(
            lane=lane,
            task_id=task_id,
            per_run_tags=per_run_tags,
            agg=agg,
        )
        if not isinstance(headline, str) or not headline:
            raise RuntimeError(
                f"classifier returned empty/non-str headline for "
                f"{(lane, task_id)!r}: {headline!r}"
            )
        headlines[(lane, task_id)] = headline

    # D-39: emit the single race_done event. Tuple keys flattened to
    # 'lane|task_id' since tuples aren't JSON-serializable across the
    # ws bus (Phase 6 ws.py expects dict[str, Any]).
    ws_emitter({
        "event_type": "race_done",
        "t_end_ms": int(time.time() * 1000),
        "total_runs": len(results),
        "lane_failed_reasons": lane_failed_reasons,
        "headlines": {
            f"{lane}|{task_id}": h
            for (lane, task_id), h in headlines.items()
        },
    })

    return grouped
