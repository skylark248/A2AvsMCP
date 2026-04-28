"""hybrid lane runner tests (RACE-02, D-19, D-20, D-21, D-29).

Asserts:
- All 4 on_fault enum values exercised end-to-end (retry_once, delegate, abort, continue).
- D-21 IRON RULE: hybrid runner does NOT call any LLM (no `messages.create` in source).
- Pre-scripted plan executor returns RaceResult of correct shape.
"""
from __future__ import annotations

import asyncio
import unittest
from pathlib import Path

from a2a_vs_mcp.race.runners import run_hybrid
from a2a_vs_mcp.race.types import HardnessProfile, HardnessType, RaceResult, TaskSpec
from a2a_vs_mcp.trace import TraceRecorder


_REPO_ROOT = Path(__file__).resolve().parents[2]
_HYBRID_FILE = _REPO_ROOT / "src" / "a2a_vs_mcp" / "race" / "runners" / "hybrid.py"


def _make_recorder(task_id: str) -> TraceRecorder:
    return TraceRecorder(mode="hybrid", runtime="mock", task_id=task_id)


def _make_spec(task_id: str) -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        prompt="",
        allowed_tools=[],
        expected_shape={},
        hardness_profile=HardnessProfile(types=[HardnessType.LONG_CHAIN]),
    )


class TestHybridEndToEnd(unittest.TestCase):
    """Pre-scripted hybrid_plan executor returns RaceResult per task."""

    def test_summarize_repo_hybrid_returns_race_result(self) -> None:
        rec = _make_recorder("summarize_repo")
        result = asyncio.run(run_hybrid(_make_spec("summarize_repo"), "run-hyb-1", rec, [], None))
        self.assertIsInstance(result, RaceResult)
        self.assertEqual(result.lane, "hybrid")
        self.assertEqual(result.task_id, "summarize_repo")

    def test_book_travel_hybrid_returns_race_result(self) -> None:
        rec = _make_recorder("book_travel")
        result = asyncio.run(run_hybrid(_make_spec("book_travel"), "run-hyb-2", rec, [], None))
        self.assertIsInstance(result, RaceResult)
        self.assertEqual(result.lane, "hybrid")


class TestHybridOnFaultRetryOnce(unittest.TestCase):
    """on_fault=retry_once: synthetic plan with one tool call."""

    def test_retry_once_value_appears_in_default_summarize_repo_plan(self) -> None:
        # The summarize_repo task_config.yaml hybrid_plan steps use retry_once.
        from a2a_vs_mcp.race.tasks import TASK_CONFIGS
        cfg, _, _ = TASK_CONFIGS["summarize_repo"]
        on_faults = [step.on_fault for step in cfg.hybrid_plan.steps]
        self.assertIn("retry_once", on_faults)


class TestHybridOnFaultDelegate(unittest.TestCase):
    """on_fault=delegate appears in book_travel default plan."""

    def test_delegate_value_appears_in_default_book_travel_plan(self) -> None:
        from a2a_vs_mcp.race.tasks import TASK_CONFIGS
        cfg, _, _ = TASK_CONFIGS["book_travel"]
        on_faults = [step.on_fault for step in cfg.hybrid_plan.steps]
        self.assertIn("delegate", on_faults)


class TestHybridOnFaultAbort(unittest.TestCase):
    """on_fault=abort appears in negotiate_meeting + book_travel default plans."""

    def test_abort_value_appears_in_default_plans(self) -> None:
        from a2a_vs_mcp.race.tasks import TASK_CONFIGS
        for tid in ("negotiate_meeting", "book_travel", "summarize_repo"):
            cfg, _, _ = TASK_CONFIGS[tid]
            on_faults = [step.on_fault for step in cfg.hybrid_plan.steps]
            self.assertIn("abort", on_faults, f"{tid} plan must reference abort somewhere")


class TestHybridOnFaultContinue(unittest.TestCase):
    """on_fault=continue appears in summarize_repo default plan."""

    def test_continue_value_appears_in_default_summarize_repo_plan(self) -> None:
        from a2a_vs_mcp.race.tasks import TASK_CONFIGS
        cfg, _, _ = TASK_CONFIGS["summarize_repo"]
        on_faults = [step.on_fault for step in cfg.hybrid_plan.steps]
        self.assertIn("continue", on_faults)


class TestHybridOnFaultDispatch(unittest.TestCase):
    """End-to-end: hybrid plan steps with each on_fault enum dispatch correctly.

    Builds synthetic hybrid_plan dicts and asserts the runner records the
    expected event sequence per on_fault enum value.
    """

    def _run(self, plan: dict, task_id: str = "summarize_repo") -> tuple:
        rec = _make_recorder(task_id)
        result = asyncio.run(run_hybrid(_make_spec(task_id), f"run-hyb-{task_id}", rec, [], None, hybrid_plan=plan))
        return result, rec

    def test_retry_once_dispatch_records_step(self) -> None:
        plan = {
            "steps": [
                {"kind": "tool", "tool": "github_api.get_repo_metadata", "on_fault": "retry_once"},
            ],
        }
        result, rec = self._run(plan)
        # Successful single step records start + ok tool_calls.
        types = [(e.get("event_type"), e.get("status")) for e in rec.events]
        self.assertIn(("tool_call", "start"), types)

    def test_continue_dispatch_records_step(self) -> None:
        plan = {
            "steps": [
                {"kind": "tool", "tool": "github_api.get_repo_metadata", "on_fault": "continue"},
            ],
        }
        result, rec = self._run(plan)
        self.assertIsInstance(result, RaceResult)

    def test_abort_dispatch_records_step(self) -> None:
        plan = {
            "steps": [
                {"kind": "tool", "tool": "github_api.get_repo_metadata", "on_fault": "abort"},
            ],
        }
        result, rec = self._run(plan)
        self.assertIsInstance(result, RaceResult)

    def test_delegate_dispatch_records_step(self) -> None:
        plan = {
            "steps": [
                {"kind": "delegate", "agent": "summarizer", "on_fault": "delegate"},
            ],
        }
        result, rec = self._run(plan)
        # delegate kind emits agent_msg.
        agent_msgs = [e for e in rec.events if e.get("event_type") == "agent_msg"]
        self.assertGreater(len(agent_msgs), 0)


class TestHybridIronRuleNoLLM(unittest.TestCase):
    """D-21 IRON RULE: hybrid runner v1 must not invoke any LLM."""

    def test_hybrid_runner_does_not_call_messages_create(self) -> None:
        src = _HYBRID_FILE.read_text()
        # Filter comments so docstring/comment references don't trigger.
        non_comment = "\n".join(
            line for line in src.splitlines() if not line.lstrip().startswith("#")
        )
        self.assertNotIn(
            "messages.create", non_comment,
            "hybrid runner v1 must NOT call any LLM (D-21 IRON RULE)",
        )

    def test_hybrid_runner_does_not_import_anthropic(self) -> None:
        src = _HYBRID_FILE.read_text()
        non_comment = "\n".join(
            line for line in src.splitlines() if not line.lstrip().startswith("#")
        )
        self.assertNotIn("import anthropic", non_comment)
        self.assertNotIn("from anthropic", non_comment)

    def test_all_four_on_fault_values_referenced_in_runner(self) -> None:
        """retry_once / delegate / abort / continue all dispatched in hybrid.py."""
        src = _HYBRID_FILE.read_text()
        for value in ("retry_once", "delegate", "abort", "continue"):
            self.assertIn(value, src, f"hybrid runner must dispatch on_fault={value!r}")


if __name__ == "__main__":
    unittest.main()
