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
# run_race stub — filled in Task 3.
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

    Filled in Task 3.
    """
    raise NotImplementedError("filled in Task 3")
