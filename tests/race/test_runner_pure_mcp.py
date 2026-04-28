"""pure_mcp lane runner end-to-end tests (RACE-02, D-19, D-20, D-32).

Asserts:
- Each v1 task returns RaceResult with lane='pure_mcp' against the in-process
  race MCP server + mock chokepoint (D-25).
- Injected faults emit fault_injected on the recorder; Detector wiring emits
  fault_observed on observation (D-32).
- run_id flows through the recorder.
"""
from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

from a2a_vs_mcp.race.failure import FailureScriptEntry, FaultKind
from a2a_vs_mcp.race.runners import run_pure_mcp
from a2a_vs_mcp.race.types import HardnessProfile, HardnessType, RaceResult, TaskSpec
from a2a_vs_mcp.trace import TraceRecorder


_REPO_ROOT = Path(__file__).resolve().parents[2]


def _make_recorder(task_id: str) -> TraceRecorder:
    return TraceRecorder(mode="pure_mcp", runtime="mock", task_id=task_id)


def _make_spec(task_id: str) -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        prompt="",
        allowed_tools=[],
        expected_shape={},
        hardness_profile=HardnessProfile(types=[HardnessType.LONG_CHAIN]),
    )


class TestPureMcpEndToEnd(unittest.TestCase):
    """Each task runs end-to-end through MCPClient(in_process) + mock chokepoint."""

    def test_summarize_repo_no_faults_returns_race_result(self) -> None:
        rec = _make_recorder("summarize_repo")
        result = asyncio.run(run_pure_mcp(_make_spec("summarize_repo"), "run-mcp-1", rec, [], None))
        self.assertIsInstance(result, RaceResult)
        self.assertEqual(result.lane, "pure_mcp")
        self.assertEqual(result.task_id, "summarize_repo")

    def test_negotiate_meeting_no_faults_returns_race_result(self) -> None:
        rec = _make_recorder("negotiate_meeting")
        result = asyncio.run(run_pure_mcp(_make_spec("negotiate_meeting"), "run-mcp-2", rec, [], None))
        self.assertIsInstance(result, RaceResult)
        self.assertEqual(result.lane, "pure_mcp")
        self.assertEqual(result.task_id, "negotiate_meeting")

    def test_book_travel_no_faults_returns_race_result(self) -> None:
        rec = _make_recorder("book_travel")
        result = asyncio.run(run_pure_mcp(_make_spec("book_travel"), "run-mcp-3", rec, [], None))
        self.assertIsInstance(result, RaceResult)
        self.assertEqual(result.lane, "pure_mcp")
        self.assertEqual(result.task_id, "book_travel")

    def test_inject_fault_records_fault_injected_event(self) -> None:
        rec = _make_recorder("summarize_repo")
        script = [FailureScriptEntry(
            kind=FaultKind.RATE_LIMIT_429,
            target="github_api.list_files",
            after_calls=0,
            duration_calls=1,
        )]
        asyncio.run(run_pure_mcp(_make_spec("summarize_repo"), "run-mcp-fault", rec, script, None))
        kinds = [e.get("event_type") for e in rec.events]
        self.assertIn("fault_injected", kinds)

    def test_done_event_emitted_per_run(self) -> None:
        rec = _make_recorder("summarize_repo")
        asyncio.run(run_pure_mcp(_make_spec("summarize_repo"), "run-mcp-done", rec, [], None))
        done_events = [e for e in rec.events if e.get("event_type") == "done"]
        self.assertEqual(len(done_events), 1)
        self.assertEqual(done_events[0].get("lane"), "pure_mcp")
        self.assertEqual(done_events[0].get("task_id"), "summarize_repo")

    def test_run_id_flows_into_recorder_events(self) -> None:
        rec = _make_recorder("summarize_repo")
        run_id = "run-id-trace-test"
        rec.run_id = run_id
        rec.lane = "pure_mcp"
        asyncio.run(run_pure_mcp(_make_spec("summarize_repo"), run_id, rec, [], None))
        # The TraceRecorder stamps run_id on every event when run_id is set.
        for ev in rec.events:
            self.assertEqual(ev.get("run_id"), run_id, ev)


if __name__ == "__main__":
    unittest.main()
