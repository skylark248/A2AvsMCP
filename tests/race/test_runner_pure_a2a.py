"""pure_a2a lane runner tests (RACE-02, D-19, D-20, D-24, D-32).

Asserts:
- Each v1 task returns RaceResult via real A2ABroker.send_task path.
- Recorder captures agent_msg events (broker handler dispatch).
- Source grep gate: send_message NEVER appears in pure_a2a.py (D-24
  legacy typo enforcement); send_task DOES appear.
"""
from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

from a2a_vs_mcp.race.runners import run_pure_a2a
from a2a_vs_mcp.race.types import HardnessProfile, HardnessType, RaceResult, TaskSpec
from a2a_vs_mcp.trace import TraceRecorder


_REPO_ROOT = Path(__file__).resolve().parents[2]
_RUNNER_FILE = _REPO_ROOT / "src" / "a2a_vs_mcp" / "race" / "runners" / "pure_a2a.py"


def _make_recorder(task_id: str) -> TraceRecorder:
    return TraceRecorder(mode="pure_a2a", runtime="mock", task_id=task_id)


def _make_spec(task_id: str) -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        prompt="",
        allowed_tools=[],
        expected_shape={},
        hardness_profile=HardnessProfile(types=[HardnessType.MULTI_SOURCE_SYNTHESIS]),
    )


class TestPureA2AEndToEnd(unittest.TestCase):
    """Real A2ABroker + FixtureBackedAgentHandler dispatch."""

    def test_negotiate_meeting_via_broker_returns_race_result(self) -> None:
        rec = _make_recorder("negotiate_meeting")
        result = asyncio.run(run_pure_a2a(_make_spec("negotiate_meeting"), "run-a2a-1", rec, [], None))
        self.assertIsInstance(result, RaceResult)
        self.assertEqual(result.lane, "pure_a2a")
        self.assertEqual(result.task_id, "negotiate_meeting")

    def test_negotiate_meeting_recorder_has_agent_msg_event(self) -> None:
        rec = _make_recorder("negotiate_meeting")
        asyncio.run(run_pure_a2a(_make_spec("negotiate_meeting"), "run-a2a-2", rec, [], None))
        agent_msgs = [e for e in rec.events if e.get("event_type") == "agent_msg"]
        self.assertGreater(len(agent_msgs), 0, "expected at least one agent_msg event from broker dispatch")

    def test_summarize_repo_via_a2a_returns_race_result(self) -> None:
        rec = _make_recorder("summarize_repo")
        result = asyncio.run(run_pure_a2a(_make_spec("summarize_repo"), "run-a2a-3", rec, [], None))
        self.assertIsInstance(result, RaceResult)
        self.assertEqual(result.lane, "pure_a2a")

    def test_book_travel_via_a2a_returns_race_result(self) -> None:
        rec = _make_recorder("book_travel")
        result = asyncio.run(run_pure_a2a(_make_spec("book_travel"), "run-a2a-4", rec, [], None))
        self.assertIsInstance(result, RaceResult)
        self.assertEqual(result.lane, "pure_a2a")
        self.assertEqual(result.task_id, "book_travel")


class TestPureA2ASourceGrepGates(unittest.TestCase):
    """D-24 typo gate + send_task presence gate (negative + positive grep)."""

    def test_send_message_method_does_not_appear_in_runner(self) -> None:
        """D-24: legacy CONTEXT.md typo. broker method is send_task, not send_message."""
        src = _RUNNER_FILE.read_text()
        # Filter comments to avoid matching documentation references.
        non_comment = "\n".join(
            line for line in src.splitlines() if not line.lstrip().startswith("#")
        )
        self.assertNotIn(
            "send_message", non_comment,
            "pure_a2a.py must use broker.send_task, not send_message (D-24 enforcement)",
        )

    def test_send_task_method_appears_in_runner(self) -> None:
        src = _RUNNER_FILE.read_text()
        self.assertIn("send_task", src)


if __name__ == "__main__":
    unittest.main()
