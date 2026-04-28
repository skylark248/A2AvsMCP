"""hybrid runner — RACE-02 lane (D-19, D-20, D-21, D-29).

V1 contract: pre-scripted plan executor (NOT agent-driven). Interprets
``task_config.hybrid_plan.steps`` linearly; on InjectedFaultError raised by a
step, dispatches per ``step.on_fault`` enum (retry_once | delegate | abort |
continue) per D-29.

Deliberately does NOT call any LLM (D-21 IRON RULE for v1). Real plan-emitter
hybrid is TODO 1, deferred to v2+.

D-19: Fresh runner — does NOT subclass v1 agents.
"""
from __future__ import annotations

import time
import uuid
from importlib import import_module
from typing import Any

from ...trace import TraceRecorder
from ..classifier import Detector
from ..failure import FailureScriptEntry, InjectedFaultError
from ..metrics import compute_wasted_tokens
from ..mocks import ACTIVE_FAULTS, ActiveFault, set_active_faults
from ..tasks import TASK_CONFIGS
from ..types import ExecutionContext, RaceResult, ScoreCard, TaskSpec


# Default positional args per dotted target. v1 deterministic; matches mock signatures.
_DEFAULT_ARGS: dict[str, dict[str, Any]] = {
    "github_api.get_repo_metadata": {"repo_id": "demo-org/api-gateway"},
    "github_api.list_files": {"repo_id": "demo-org/api-gateway"},
    "github_api.read_file": {"repo_id": "demo-org/api-gateway", "file_path": "src/main.py"},
    "calendar_api.get_free_busy": {"owner": "alice@demo.org"},
    "calendar_api.propose_time": {
        "owners": ["alice@demo.org", "bob@demo.org", "carol@demo.org"],
        "duration_min": 60,
    },
    "travel_api.search_flights": {"origin": "SFO", "destination": "JFK"},
    "travel_api.search_hotels": {"city": "NYC"},
    "travel_api.book_itinerary": {
        "flight_ids": ["F-002", "F-102"],
        "hotel_id": "H-002",
        "nights": 3,
    },
}


def _arm_faults(failure_script: list[FailureScriptEntry]) -> dict[str, ActiveFault]:
    armed: dict[str, ActiveFault] = {}
    for entry in failure_script:
        armed[entry.target] = ActiveFault(
            fault_id=f"fault-{uuid.uuid4().hex[:8]}",
            kind=entry.kind,
            target=entry.target,
        )
    return armed


def _detect_and_record(
    events_before: int,
    recorder: TraceRecorder,
    detectors: list[Detector],
    lane: str,
) -> int:
    """Detector wiring per D-32 — identical algorithm as classifier.py replay path,
    so by-construction replay-symmetric (D-33)."""
    events = recorder.events
    for event in events[events_before:]:
        if event.get("event_type") == "fault_injected":
            detectors.append(Detector(
                fault_id=event["fault_id"],
                fault_kind=event.get("fault_kind", ""),
                target=event.get("target", ""),
                fault_inject_turn=event.get("turn_index", 0),
            ))
        for d in list(detectors):
            if d.state.value == "observed":
                continue
            if d.consume(event):
                wasted = compute_wasted_tokens(events, d.fault_id, lane)
                recorder.record(
                    "fault_observed",
                    fault_id=d.fault_id,
                    fault_kind=d.fault_kind,
                    target=d.target,
                    t_observed_ms=d.t_observed_ms or int(time.time() * 1000),
                    evidence=d.evidence_kind or "",
                    wasted_tokens_before_detection=wasted,
                )
    return len(events)


async def _dispatch_step(
    step: dict,
    ctx: ExecutionContext,
    targets: dict,
    binds: dict,
    recorder: TraceRecorder,
) -> Any:
    """Execute a single hybrid_plan step.

    For ``kind: tool`` steps: invokes ``targets[step.tool]`` with bound args
    (or default args if no bind). For ``kind: delegate`` steps in v1 there is
    no real subagent — emits an ``agent_msg`` event so the trace records the
    delegation boundary, and pulls the bind value from ctx if present.
    """
    kind = step.get("kind")
    on_fault = step.get("on_fault", "abort")
    bind_key = step.get("bind")
    if kind == "tool":
        target_name = step.get("tool")
        if target_name not in targets:
            raise KeyError(f"hybrid step targets unknown TARGETS key: {target_name}")
        if bind_key and bind_key in binds:
            bound = binds[bind_key](ctx)
            args = bound if isinstance(bound, dict) else (
                _DEFAULT_ARGS.get(target_name, {}) if bound in (None, [], {}) else {}
            )
        else:
            args = dict(_DEFAULT_ARGS.get(target_name, {}))
        recorder.record(
            "tool_call",
            tool_name=target_name,
            status="start",
            on_fault=on_fault,
            lane="hybrid",
        )
        fn = targets[target_name]
        result = fn(**args, recorder=recorder, run_id=ctx.get("run_id"))
        recorder.record(
            "tool_call",
            tool_name=target_name,
            status="ok",
            lane="hybrid",
        )
        return result
    if kind == "delegate":
        agent = step.get("agent", "subagent")
        # v1 has no real subagent runtime — emit a marker agent_msg so Detector
        # path 3 (agent_msg ack) can fire if the prior step raised an injected fault.
        bound = binds[bind_key](ctx) if (bind_key and bind_key in binds) else None
        recorder.record(
            "agent_msg",
            message_type="task_submit",
            sender="hybrid_lead",
            target=agent,
            content=f"delegating to {agent} (v1 stub)",
            lane="hybrid",
        )
        # Surface the bound value (if any) into ctx for downstream steps that
        # bind the same key. v1 stub: pass-through.
        ctx.setdefault("subagent_outputs", {})[agent] = bound
        return bound
    raise ValueError(f"unknown hybrid step kind: {kind!r}")


async def _execute_step_with_on_fault(
    step: dict,
    ctx: ExecutionContext,
    targets: dict,
    binds: dict,
    recorder: TraceRecorder,
) -> Any:
    """Execute a step with on_fault dispatch per D-29 enum.

    Handles all four values: retry_once, delegate, abort, continue.
    """
    on_fault = step.get("on_fault", "abort")
    try:
        return await _dispatch_step(step, ctx, targets, binds, recorder)
    except InjectedFaultError as exc:
        recorder.record(
            "tool_call",
            tool_name=step.get("tool") or step.get("agent", ""),
            status="error",
            error_kind="injected_fault",
            error=str(exc),
            on_fault=on_fault,
            lane="hybrid",
        )
        if on_fault == "retry_once":
            try:
                return await _dispatch_step(step, ctx, targets, binds, recorder)
            except InjectedFaultError:
                raise
        elif on_fault == "delegate":
            # Switch to a delegate fallback: same step recast as kind=delegate.
            alt = dict(step)
            alt["kind"] = "delegate"
            alt["agent"] = step.get("agent") or "fallback_subagent"
            return await _dispatch_step(alt, ctx, targets, binds, recorder)
        elif on_fault == "abort":
            raise
        elif on_fault == "continue":
            return None
        raise


async def run_hybrid(
    task_spec: TaskSpec,
    run_id: str,
    recorder: TraceRecorder,
    failure_script: list[FailureScriptEntry],
    sonnet_client: Any = None,
    *,
    hybrid_plan: dict[str, Any] | None = None,
) -> RaceResult:
    """RACE-02 hybrid lane runner — pre-scripted plan executor (D-21).

    Locked signature per RESEARCH §4 + extra ``hybrid_plan`` kwarg per Plan 09
    must_haves.truths line 3. ``sonnet_client`` accepted for harness compat but
    NEVER invoked (D-21 IRON RULE; the grep gate enforces that no
    Anthropic chat-completion entrypoint string appears in this file).
    """
    lane = "hybrid"
    armed = _arm_faults(failure_script)
    fault_tok = set_active_faults(armed)
    detectors: list[Detector] = []
    events_before = len(recorder.events)
    started_at = time.time()
    score_pass = False
    sc: ScoreCard
    cfg, targets, binds = TASK_CONFIGS[task_spec.task_id]
    # Resolve the hybrid_plan: caller-provided override OR cfg default.
    if hybrid_plan is None:
        plan = cfg.hybrid_plan.model_dump() if hasattr(cfg.hybrid_plan, "model_dump") else cfg.hybrid_plan
    else:
        plan = hybrid_plan
    ctx: ExecutionContext = {
        "task_input": {},
        "subagent_outputs": {},
        "tool_outputs": {},
        "scratchpad": {},
        "run_id": run_id,  # not in TypedDict but TypedDict total=False allows extras at runtime
    }  # type: ignore[typeddict-unknown-key]
    aborted = False
    try:
        steps = plan.get("steps", []) if isinstance(plan, dict) else getattr(plan, "steps", [])
        for step in steps:
            step_dict = step if isinstance(step, dict) else step.model_dump()
            try:
                result = await _execute_step_with_on_fault(
                    step_dict, ctx, targets, binds, recorder,
                )
                key = step_dict.get("tool") or step_dict.get("agent") or "step"
                ctx["tool_outputs"][key] = result
            except InjectedFaultError as exc:
                recorder.record(
                    "step_failed",
                    target=step_dict.get("tool") or step_dict.get("agent", ""),
                    error_kind="injected_fault",
                    reason=str(exc),
                    lane="hybrid",
                )
                aborted = True
                break
            events_before = _detect_and_record(events_before, recorder, detectors, lane)
        # Score via the per-task scorer. judge=None (deferred to harness).
        scorer = import_module(f"a2a_vs_mcp.race.tasks.{task_spec.task_id}").score
        sc = scorer(
            {"tool_outputs": ctx["tool_outputs"], "aborted": aborted},
            recorder.events,
            judge=None,
        )
        score_pass = sc.success and not aborted
    finally:
        for d in detectors:
            d.finalize_at_done(score_pass)
        recorder.record("done", score_pass=score_pass, lane=lane, task_id=task_spec.task_id)
        events_before = _detect_and_record(events_before, recorder, detectors, lane)
        ACTIVE_FAULTS.reset(fault_tok)
    latency_ms = int((time.time() - started_at) * 1000)
    return RaceResult(
        run_id=run_id,
        lane=lane,
        task_id=task_spec.task_id,
        hardness_profile=task_spec.hardness_profile,
        score_card=ScoreCard(
            success=sc.success and not aborted,
            ttff_ms=sc.ttff_ms,
            recovered=sc.recovered,
            wasted_tokens_before_detection=sc.wasted_tokens_before_detection,
            failure_mode=sc.failure_mode,
            cost_usd=sc.cost_usd,
            latency_ms=latency_ms,
        ),
        trace_id=run_id,
    )
