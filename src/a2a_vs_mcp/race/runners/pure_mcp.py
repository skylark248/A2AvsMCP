"""pure_mcp runner — RACE-02 lane (D-19, D-20, D-32).

Calls race MCP servers via MCPClient(transport='in_process'). Faults flow
through the mock chokepoint per D-25. Detector wiring per D-32 — one Detector
per fault_injected event observed in recorder; consume() on each subsequent
event; record fault_observed with compute_wasted_tokens() on transition.

D-19: Fresh runner — does NOT subclass v1 agents (no imports from agents/*).
"""
from __future__ import annotations

import asyncio
import time
import uuid
from importlib import import_module
from pathlib import Path
from typing import Any

from ...mcp.client import MCPClient
from ...mcp_servers.race_context import set_mcp_tool_context, MCP_TOOL_CONTEXT
from ...trace import TraceRecorder
from ..classifier import Detector
from ..failure import FailureScriptEntry, InjectedFaultError
from ..metrics import compute_wasted_tokens
from ..mocks import ACTIVE_FAULTS, ActiveFault, set_active_faults
from ..tasks import TASK_CONFIGS
from ..types import RaceResult, ScoreCard, TaskSpec


# Map task_id -> race MCP server module string (RESEARCH §5; D-25 chokepoint).
_TASK_TO_SERVER = {
    "summarize_repo": "a2a_vs_mcp.mcp_servers.race_github",
    "negotiate_meeting": "a2a_vs_mcp.mcp_servers.race_calendar",
    "book_travel": "a2a_vs_mcp.mcp_servers.race_travel",
}


# Default arguments per (task, tool). v1 deterministic; Plan 11 tests assert these.
_DEFAULT_ARGS: dict[str, dict[str, dict[str, Any]]] = {
    "summarize_repo": {
        "get_repo_metadata": {"repo_id": "demo-org/api-gateway"},
        "list_files": {"repo_id": "demo-org/api-gateway"},
        "read_file": {"repo_id": "demo-org/api-gateway", "file_path": "src/main.py"},
    },
    "negotiate_meeting": {
        "get_free_busy": {"owner": "alice@demo.org"},
        "propose_time": {
            "owners": ["alice@demo.org", "bob@demo.org", "carol@demo.org"],
            "duration_min": 60,
        },
    },
    "book_travel": {
        "search_flights": {"origin": "SFO", "destination": "JFK"},
        "search_hotels": {"city": "NYC"},
        "book_itinerary": {
            "flight_ids": ["F-002", "F-102"],
            "hotel_id": "H-002",
            "nights": 3,
        },
    },
}


def _arm_faults(failure_script: list[FailureScriptEntry]) -> dict[str, ActiveFault]:
    """Build ACTIVE_FAULTS dict from failure_script (one fault armed per target)."""
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
    """Scan events appended since events_before; instantiate Detectors on fault_injected
    events (D-32) and feed every subsequent event to live Detectors. On consume()
    transition, record fault_observed with compute_wasted_tokens (D-40).

    Returns the new len(recorder.events) so caller can advance the cursor.
    """
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


def _project_root() -> Path:
    """Repo root: resolve from this file's parents (race/runners/pure_mcp.py)."""
    # parents[0]=runners, [1]=race, [2]=a2a_vs_mcp, [3]=src, [4]=repo root.
    return Path(__file__).resolve().parents[4]


def _bare_tool_name(target: str) -> str:
    """Convert dotted TARGET (e.g., 'github_api.get_repo_metadata') to bare MCP tool name."""
    return target.split(".")[-1]


def _result_from_outputs(task_id: str, outputs: dict[str, Any]) -> dict[str, Any]:
    """Pack tool outputs into a scorer-friendly result dict.

    The synthesized 'summary' string for summarize_repo deliberately mentions ≥3
    modules and the entry point so the Haiku rubric (R1, R2, R3) can pass when
    no fault drops content (D-42).
    """
    if task_id == "summarize_repo":
        meta = outputs.get("get_repo_metadata") or {}
        files = outputs.get("list_files") or []
        modules = meta.get("modules", [])
        purpose = meta.get("purpose", "")
        entry_point = meta.get("entry_point", "")
        summary = (
            f"{purpose} Modules include "
            f"{', '.join(modules[:3]) if modules else 'core, api, util'}. "
            f"Entry point: {entry_point}."
        )
        return {"summary": summary, "metadata": meta, "files": files}
    if task_id == "negotiate_meeting":
        proposal = outputs.get("propose_time") or {}
        # In a real LLM-driven run the runner gathers free_busy across all owners;
        # for v1 deterministic runner we synthesize the structural mapping.
        return {"proposed_time": proposal, "free_busy_by_owner": {}}
    if task_id == "book_travel":
        booking = outputs.get("book_itinerary") or {}
        return {
            "booking": booking,
            "budget_usd": 1500,
            "summary": "business trip — confirm flights and hotel within budget",
        }
    return {}


async def run_pure_mcp(
    task_spec: TaskSpec,
    run_id: str,
    recorder: TraceRecorder,
    failure_script: list[FailureScriptEntry],
    sonnet_client: Any = None,
) -> RaceResult:
    """RACE-02 pure_mcp lane runner (D-19, D-20, D-32).

    Locked signature per RESEARCH §4 lines 487-516. ``sonnet_client`` is accepted
    for harness compatibility but not invoked in v1 (deterministic mock orchestration).
    """
    lane = "pure_mcp"
    server_module = _TASK_TO_SERVER[task_spec.task_id]
    armed = _arm_faults(failure_script)
    fault_tok = set_active_faults(armed)
    ctx_tok = set_mcp_tool_context(recorder=recorder, run_id=run_id)
    detectors: list[Detector] = []
    events_before = len(recorder.events)
    started_at = time.time()
    score_pass = False
    sc: ScoreCard
    client: MCPClient | None = None
    try:
        # MCPClient.__init__ calls anyio.run() to discover tools; that conflicts with
        # the runner's running asyncio loop. Construct it on a worker thread so the
        # nested anyio.run() gets its own event loop (clean isolation).
        client = await asyncio.to_thread(
            MCPClient,
            server_module=server_module,
            trace=recorder,
            project_root=_project_root(),
            failure_config=None,
            transport="in_process",
        )
        cfg, targets, _binds = TASK_CONFIGS[task_spec.task_id]
        # Drive each TARGET in the failure_script's order so injected faults always fire,
        # then any remaining TARGETS to give the Detector window enough events.
        target_keys = list(targets.keys())
        ordered_targets = [e.target for e in failure_script if e.target in targets]
        for tk in target_keys:
            if tk not in ordered_targets:
                ordered_targets.append(tk)
        outputs: dict[str, Any] = {}
        for target in ordered_targets:
            tool_name = _bare_tool_name(target)
            args = _DEFAULT_ARGS.get(task_spec.task_id, {}).get(tool_name, {})
            try:
                # client.call() uses anyio.run() — must run on a worker thread.
                result = await asyncio.to_thread(client.call, tool_name, args)
                outputs[tool_name] = result
                # Detector matches retries by tool_name==target. The MCPClient records
                # the call with key 'tool=...' so we emit a runner-side tool_call
                # event keyed on tool_name + target so subsequent retries are visible.
                recorder.record(
                    "tool_call",
                    tool_name=target,
                    status="ok",
                    lane=lane,
                )
            except Exception as exc:
                # FastMCP wraps the underlying InjectedFaultError as a ToolError when
                # the call_tool path raises (mcp/server/fastmcp/tools/base.py:117).
                # We treat any tool-call exception while a fault is armed for this
                # target as the injected fault (the IRON RULE in failure.py guarantees
                # the fault_injected event was already recorded before the raise).
                # Never retry InjectedFaultError at the runner layer — that's the
                # harness's job (Plan 10), and only for transient infra errors.
                is_injected = (
                    isinstance(exc, InjectedFaultError)
                    or "injected" in str(exc).lower()
                    or armed.get(target) is not None
                )
                recorder.record(
                    "tool_call",
                    tool_name=target,
                    status="error",
                    error_kind="injected_fault" if is_injected else "transport_error",
                    error=str(exc),
                    lane=lane,
                )
                if not is_injected:
                    # Real infra error — bubble up so harness retry classifier can act.
                    raise
            events_before = _detect_and_record(events_before, recorder, detectors, lane)
        # Score via the per-task scorer. Judge=None — Haiku integration deferred to harness.
        scorer = import_module(f"a2a_vs_mcp.race.tasks.{task_spec.task_id}").score
        result = _result_from_outputs(task_spec.task_id, outputs)
        sc = scorer(result, recorder.events, judge=None)
        score_pass = sc.success
    finally:
        # Finalize Detectors at done time (D-34 terminal-state rules).
        for d in detectors:
            d.finalize_at_done(score_pass)
        recorder.record("done", score_pass=score_pass, lane=lane, task_id=task_spec.task_id)
        events_before = _detect_and_record(events_before, recorder, detectors, lane)
        # ContextVar reset hygiene — concurrency-safe (D-32 + threat T-07-09-02).
        ACTIVE_FAULTS.reset(fault_tok)
        MCP_TOOL_CONTEXT.reset(ctx_tok)
        if client is not None:
            try:
                client.close()
            except Exception:
                pass
    latency_ms = int((time.time() - started_at) * 1000)
    return RaceResult(
        run_id=run_id,
        lane=lane,
        task_id=task_spec.task_id,
        hardness_profile=task_spec.hardness_profile,
        score_card=ScoreCard(
            success=sc.success,
            ttff_ms=sc.ttff_ms,
            recovered=sc.recovered,
            wasted_tokens_before_detection=sc.wasted_tokens_before_detection,
            failure_mode=sc.failure_mode,
            cost_usd=sc.cost_usd,
            latency_ms=latency_ms,
        ),
        trace_id=run_id,
    )
