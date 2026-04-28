"""pure_a2a runner — RACE-02 lane (D-19, D-20, D-24, D-32).

Routes task work via real A2ABroker.send_task. Per task, registers
fixture-backed agent handlers that delegate to race.mocks.<module>. Faults
flow through the mock chokepoint per D-25; Detector wiring per D-32.

NOTE: actual broker method is ``send_task`` (the legacy CONTEXT.md D-24 typo
is corrected — RESEARCH §5 line 733 confirmed via a2a/broker.py:61).

D-19: Fresh runner — does NOT subclass v1 agents.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from importlib import import_module
from typing import Any

from ...a2a.broker import A2ABroker
from ...schemas import A2AMessage, AgentCard, AgentResult
from ...trace import TraceRecorder
from ..classifier import Detector
from ..failure import FailureScriptEntry, InjectedFaultError
from ..metrics import compute_wasted_tokens
from ..mocks import ACTIVE_FAULTS, ActiveFault, set_active_faults
from ..mocks import calendar as calendar_mock
from ..mocks import github as github_mock
from ..mocks import travel as travel_mock
from ..tasks import TASK_CONFIGS
from ..types import RaceResult, ScoreCard, TaskSpec


# Map (task_id, capability) -> (mock fn name, mock module, dotted target).
# capability is the A2A capability name; the dotted target matches the TARGETS
# registry key so fault arming uses identical strings across lanes.
_HANDLER_TABLE: dict[tuple[str, str], tuple[str, Any, str]] = {
    ("summarize_repo", "fetch_repo_metadata"): (
        "get_repo_metadata", github_mock, "github_api.get_repo_metadata",
    ),
    ("summarize_repo", "list_repo_files"): (
        "list_files", github_mock, "github_api.list_files",
    ),
    ("summarize_repo", "read_repo_file"): (
        "read_file", github_mock, "github_api.read_file",
    ),
    ("negotiate_meeting", "fetch_free_busy"): (
        "get_free_busy", calendar_mock, "calendar_api.get_free_busy",
    ),
    ("negotiate_meeting", "compute_proposal"): (
        "propose_time", calendar_mock, "calendar_api.propose_time",
    ),
    ("book_travel", "search_flights"): (
        "search_flights", travel_mock, "travel_api.search_flights",
    ),
    ("book_travel", "search_hotels"): (
        "search_hotels", travel_mock, "travel_api.search_hotels",
    ),
    ("book_travel", "book_itinerary"): (
        "book_itinerary", travel_mock, "travel_api.book_itinerary",
    ),
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


@dataclass
class FixtureBackedAgentHandler:
    """A2A agent handler that delegates to race.mocks (single chokepoint).

    Threat T-07-09-04 mitigation: handler delegates ONLY to race.mocks.<module>;
    no direct fixture access in this class. Plan 11 chokepoint test enforces.

    NOTE on fault armament: the broker dispatches handlers via stdlib
    ThreadPoolExecutor, which does NOT propagate ContextVars from the runner's
    thread. The handler therefore re-arms ACTIVE_FAULTS inside ``handle_task``
    using ``armed_faults`` captured at registration time, ensuring the chokepoint
    sees the active fault per D-25.
    """

    capability: str
    recorder: TraceRecorder
    run_id: str
    task_id: str
    armed_faults: dict[str, ActiveFault]

    def handle_task(self, message: A2AMessage) -> AgentResult:
        key = (self.task_id, self.capability)
        if key not in _HANDLER_TABLE:
            return AgentResult(
                agent_id=f"race_{self.task_id}_agent",
                summary=f"unknown capability {self.capability}",
                details={}, confidence=0.0, status="failed",
            )
        fn_name, mock_mod, target = _HANDLER_TABLE[key]
        fn = getattr(mock_mod, fn_name)
        payload = dict(message.payload or {})
        # Re-arm in this worker thread (stdlib ThreadPoolExecutor doesn't propagate
        # ContextVars). Reset on exit to keep this thread clean for any reuse.
        thread_token = set_active_faults(self.armed_faults)
        # agent_msg event so Detector retry-detection (path 2) and ack-detection
        # (path 3) can see the per-capability turn boundary.
        self.recorder.record(
            "agent_msg",
            message_type="task_submit",
            sender=message.sender_agent,
            target=message.target_agent,
            capability=self.capability,
            tool_name=target,
            content=f"invoking {self.capability}",
            lane="pure_a2a",
        )
        try:
            try:
                data = fn(**payload, recorder=self.recorder, run_id=self.run_id)
            finally:
                ACTIVE_FAULTS.reset(thread_token)
            return AgentResult(
                agent_id=f"race_{self.task_id}_agent",
                summary=f"{self.capability} ok",
                details={"data": data}, confidence=1.0, status="completed",
            )
        except InjectedFaultError as exc:
            # Emit an agent_msg acknowledging the fault so Detector path 3 fires.
            self.recorder.record(
                "agent_msg",
                message_type="task_error",
                sender=message.target_agent,
                target=message.sender_agent,
                capability=self.capability,
                tool_name=target,
                content=f"failed {self.capability}: encountered injected error: {exc}",
                error_kind="injected_fault",
                lane="pure_a2a",
            )
            return AgentResult(
                agent_id=f"race_{self.task_id}_agent",
                summary=f"{self.capability} fault: {exc}",
                details={"error_kind": "injected_fault", "error": str(exc)},
                confidence=0.0, status="failed",
            )


def _detect_and_record(
    events_before: int,
    recorder: TraceRecorder,
    detectors: list[Detector],
    lane: str,
) -> int:
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


def _capabilities_for_task(task_id: str) -> list[tuple[str, dict[str, Any]]]:
    """v1 hardcoded capability sequence per task: list of (capability, payload).

    Drives the runner deterministically — Plan 11 tests assert these defaults.
    """
    if task_id == "summarize_repo":
        return [
            ("fetch_repo_metadata", {"repo_id": "demo-org/api-gateway"}),
            ("list_repo_files", {"repo_id": "demo-org/api-gateway"}),
            ("read_repo_file", {
                "repo_id": "demo-org/api-gateway", "file_path": "src/main.py",
            }),
        ]
    if task_id == "negotiate_meeting":
        return [
            ("fetch_free_busy", {"owner": "alice@demo.org"}),
            ("fetch_free_busy", {"owner": "bob@demo.org"}),
            ("fetch_free_busy", {"owner": "carol@demo.org"}),
            ("compute_proposal", {
                "owners": ["alice@demo.org", "bob@demo.org", "carol@demo.org"],
                "duration_min": 60,
            }),
        ]
    if task_id == "book_travel":
        return [
            ("search_flights", {"origin": "SFO", "destination": "JFK"}),
            ("search_flights", {"origin": "JFK", "destination": "SFO"}),
            ("search_hotels", {"city": "NYC"}),
            ("book_itinerary", {
                "flight_ids": ["F-002", "F-102"],
                "hotel_id": "H-002",
                "nights": 3,
            }),
        ]
    return []


def _result_from_outputs(task_id: str, outputs: dict[str, list[Any]]) -> dict[str, Any]:
    """Pack per-capability outputs into the scorer-friendly result dict."""
    if task_id == "summarize_repo":
        meta_list = outputs.get("fetch_repo_metadata") or [None]
        meta = (meta_list[0] or {}) if meta_list else {}
        modules = meta.get("modules", [])
        purpose = meta.get("purpose", "")
        entry_point = meta.get("entry_point", "")
        summary = (
            f"{purpose} Modules include "
            f"{', '.join(modules[:3]) if modules else 'core, api, util'}. "
            f"Entry point: {entry_point}."
        )
        return {"summary": summary, "metadata": meta}
    if task_id == "negotiate_meeting":
        proposals = outputs.get("compute_proposal") or [None]
        proposal = (proposals[0] or {}) if proposals else {}
        free_busy_list = outputs.get("fetch_free_busy") or []
        fb_by_owner = {fb["owner"]: fb for fb in free_busy_list if isinstance(fb, dict) and fb.get("owner")}
        return {"proposed_time": proposal, "free_busy_by_owner": fb_by_owner}
    if task_id == "book_travel":
        bookings = outputs.get("book_itinerary") or [None]
        booking = (bookings[0] or {}) if bookings else {}
        return {
            "booking": booking,
            "budget_usd": 1500,
            "summary": "business trip — confirm flights and hotel within budget",
        }
    return {}


async def run_pure_a2a(
    task_spec: TaskSpec,
    run_id: str,
    recorder: TraceRecorder,
    failure_script: list[FailureScriptEntry],
    sonnet_client: Any = None,
) -> RaceResult:
    """RACE-02 pure_a2a lane runner (D-19, D-20, D-24, D-32).

    Locked signature per RESEARCH §4. ``sonnet_client`` accepted for harness
    compatibility but not invoked in v1 (deterministic mock orchestration).
    """
    lane = "pure_a2a"
    armed = _arm_faults(failure_script)
    fault_tok = set_active_faults(armed)
    detectors: list[Detector] = []
    events_before = len(recorder.events)
    started_at = time.time()
    score_pass = False
    sc: ScoreCard
    try:
        broker = A2ABroker(trace=recorder)
        # Register one handler per unique capability used by this task.
        seen: set[str] = set()
        for cap, _ in _capabilities_for_task(task_spec.task_id):
            if cap in seen:
                continue
            seen.add(cap)
            card = AgentCard(
                agent_id=f"race_{task_spec.task_id}_{cap}",
                name=f"race {task_spec.task_id} {cap} agent",
                capabilities=[cap],
                description=f"v1 race fixture-backed agent for {cap}",
            )
            broker.register(
                card,
                FixtureBackedAgentHandler(
                    capability=cap,
                    recorder=recorder,
                    run_id=run_id,
                    task_id=task_spec.task_id,
                    armed_faults=armed,
                ),
            )
        # Drive each capability via broker.send_task (D-24 corrected).
        outputs: dict[str, list[Any]] = {}
        for cap, payload in _capabilities_for_task(task_spec.task_id):
            msg = A2AMessage(
                message_type="task_submit",
                sender_agent="race_lead",
                target_agent=f"race_{task_spec.task_id}_{cap}",
                capability=cap,
                payload=payload,
                task_id=f"task-{uuid.uuid4().hex[:8]}",
            )
            try:
                res = broker.send_task(msg)
                data = res.details.get("data") if res.status == "completed" else None
            except RuntimeError:
                # broker wraps handler errors in RuntimeError after retry exhaustion;
                # the FixtureBackedAgentHandler catches InjectedFaultError and returns
                # an AgentResult(status='failed') so this path is rare. Treat as None.
                data = None
            outputs.setdefault(cap, []).append(data)
            events_before = _detect_and_record(events_before, recorder, detectors, lane)
        scorer = import_module(f"a2a_vs_mcp.race.tasks.{task_spec.task_id}").score
        result = _result_from_outputs(task_spec.task_id, outputs)
        sc = scorer(result, recorder.events, judge=None)
        score_pass = sc.success
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
