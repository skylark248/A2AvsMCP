"""Race metrics tests (RACE-04, D-37, D-40).

Asserts:
- compute_wasted_tokens sums llm_call.tokens only within [t_inject_ms, t_observed_ms].
- median_retries / median_delegations / median_switches / median_turns_after_fault
  produce expected counts for hand-built event lists.
- aggregate_for_classifier returns the required keys.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from a2a_vs_mcp.race.metrics import (
    aggregate_for_classifier,
    compute_wasted_tokens,
    median_delegations,
    median_retries,
    median_switches,
    median_turns_after_fault,
)


_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "traces"


def _load(name: str) -> dict:
    return json.loads((_FIXTURES_DIR / f"{name}.json").read_text())


class TestComputeWastedTokens(unittest.TestCase):
    """D-40: window math sums tokens only within [t_inject_ms, t_observed_ms]."""

    def test_window_math_sums_only_within_inject_to_observed(self) -> None:
        events = [
            {"event_type": "llm_call", "lane": "pure_mcp", "tokens_in": 100, "tokens_out": 50, "t_call_start_ms": 500},  # before inject; excluded
            {"event_type": "fault_injected", "fault_id": "f1", "fault_kind": "rate_limit_429", "target": "x", "turn_index": 1, "t_inject_ms": 1000},
            {"event_type": "llm_call", "lane": "pure_mcp", "tokens_in": 200, "tokens_out": 100, "t_call_start_ms": 1100},  # included (1000<=1100<=1500)
            {"event_type": "llm_call", "lane": "pure_mcp", "tokens_in": 150, "tokens_out": 75,  "t_call_start_ms": 1300},  # included (1000<=1300<=1500)
            {"event_type": "fault_observed", "fault_id": "f1", "fault_kind": "rate_limit_429", "target": "x", "t_observed_ms": 1500},
            {"event_type": "llm_call", "lane": "pure_mcp", "tokens_in": 50, "tokens_out": 25, "t_call_start_ms": 1700},   # after observed; excluded
        ]
        # Expected: (200+100) + (150+75) = 525.
        self.assertEqual(compute_wasted_tokens(events, "f1", "pure_mcp"), 525)

    def test_returns_zero_when_no_observation(self) -> None:
        events = [
            {"event_type": "fault_injected", "fault_id": "f1", "fault_kind": "rate_limit_429", "target": "x", "turn_index": 1, "t_inject_ms": 1000},
            {"event_type": "llm_call", "lane": "pure_mcp", "tokens_in": 100, "tokens_out": 50, "t_call_start_ms": 1100},
        ]
        self.assertEqual(compute_wasted_tokens(events, "f1", "pure_mcp"), 0)

    def test_lane_filter_excludes_other_lanes(self) -> None:
        events = [
            {"event_type": "fault_injected", "fault_id": "f1", "fault_kind": "rate_limit_429", "target": "x", "turn_index": 1, "t_inject_ms": 1000},
            {"event_type": "llm_call", "lane": "pure_mcp", "tokens_in": 100, "tokens_out": 50, "t_call_start_ms": 1100},
            {"event_type": "llm_call", "lane": "pure_a2a", "tokens_in": 999, "tokens_out": 999, "t_call_start_ms": 1200},
            {"event_type": "fault_observed", "fault_id": "f1", "fault_kind": "rate_limit_429", "target": "x", "t_observed_ms": 1500},
        ]
        self.assertEqual(compute_wasted_tokens(events, "f1", "pure_mcp"), 150)


class TestMedianRetries(unittest.TestCase):
    def test_counts_retries_after_fault_inject_turn(self) -> None:
        events = [
            {"event_type": "tool_call", "tool_name": "github_api.list_files", "status": "ok", "turn_index": 1},
            {"event_type": "fault_injected", "fault_id": "f1", "fault_kind": "rate_limit_429", "target": "github_api.list_files", "turn_index": 2},
            {"event_type": "tool_call", "tool_name": "github_api.list_files", "status": "error", "turn_index": 2},
            {"event_type": "tool_call", "tool_name": "github_api.list_files", "status": "ok", "turn_index": 3},
            {"event_type": "tool_call", "tool_name": "github_api.list_files", "status": "ok", "turn_index": 4},
        ]
        self.assertEqual(median_retries(events, "f1", "github_api.list_files"), 2)


class TestMedianDelegations(unittest.TestCase):
    def test_counts_task_submit_after_fault_inject_turn(self) -> None:
        events = [
            {"event_type": "agent_msg", "message_type": "task_submit", "turn_index": 1},
            {"event_type": "fault_injected", "fault_id": "f1", "fault_kind": "schema_drift", "target": "x", "turn_index": 2},
            {"event_type": "agent_msg", "message_type": "task_submit", "turn_index": 3},
            {"event_type": "agent_msg", "message_type": "task_submit", "turn_index": 4},
            {"event_type": "agent_msg", "message_type": "task_result", "turn_index": 5},
        ]
        self.assertEqual(median_delegations(events, "f1"), 2)


class TestMedianSwitches(unittest.TestCase):
    def test_counts_protocol_boundary_crossings(self) -> None:
        events = [
            {"event_type": "fault_injected", "fault_id": "f1", "fault_kind": "rate_limit_429", "target": "x", "turn_index": 1},
            {"event_type": "tool_call", "tool_name": "x", "status": "ok", "turn_index": 2},
            {"event_type": "agent_msg", "content": "delegating", "turn_index": 3},
            {"event_type": "tool_call", "tool_name": "y", "status": "ok", "turn_index": 4},
            {"event_type": "agent_msg", "content": "summarizing", "turn_index": 5},
        ]
        # qual sequence: tool_call -> agent_msg -> tool_call -> agent_msg = 3 transitions.
        self.assertEqual(median_switches(events, "f1"), 3)


class TestMedianTurnsAfterFault(unittest.TestCase):
    def test_returns_difference_between_max_turn_and_inject_turn(self) -> None:
        events = [
            {"event_type": "fault_injected", "fault_id": "f1", "fault_kind": "rate_limit_429", "target": "x", "turn_index": 2},
            {"event_type": "tool_call", "tool_name": "x", "status": "ok", "turn_index": 5},
        ]
        self.assertEqual(median_turns_after_fault(events, "f1"), 3)


class TestMedianRetriesOverFixture(unittest.TestCase):
    """Pull a known fixture and assert the metric matches the hand-counted value."""

    def test_summarize_repo_recovered_retry_count(self) -> None:
        fx = _load("summarize_repo_recovered")
        # Fixture has list_files: start (turn 1), error (turn 2 — same as inject_turn),
        # ok (turn 4). Only the turn-4 call is *after* inject_turn 2 -> 1 retry.
        self.assertEqual(median_retries(fx["events"], "f1", "github_api.list_files"), 1)


class TestAggregateForClassifier(unittest.TestCase):
    """Aggregate dict shape contract — required keys per (lane) variant."""

    def test_aggregate_returns_required_keys_pure_mcp(self) -> None:
        fx = _load("summarize_repo_recovered")
        per_run = [fx["events"]]
        agg = aggregate_for_classifier(
            per_run, task_id="summarize_repo", lane="pure_mcp",
            characteristic_tool="github_api.list_files",
        )
        for key in (
            "recovery_rate", "mean_wasted_tokens", "mean_ttff_ms",
            "median_turns_after_fault", "median_retries", "characteristic_tool",
        ):
            self.assertIn(key, agg)

    def test_aggregate_returns_required_keys_pure_a2a(self) -> None:
        fx = _load("negotiate_meeting_recovered")
        per_run = [fx["events"]]
        agg = aggregate_for_classifier(
            per_run, task_id="negotiate_meeting", lane="pure_a2a",
        )
        for key in (
            "recovery_rate", "mean_wasted_tokens", "mean_ttff_ms",
            "median_turns_after_fault", "median_delegations",
        ):
            self.assertIn(key, agg)

    def test_aggregate_returns_required_keys_hybrid(self) -> None:
        fx = _load("book_travel_recovered")
        per_run = [fx["events"]]
        agg = aggregate_for_classifier(
            per_run, task_id="book_travel", lane="hybrid",
        )
        for key in (
            "recovery_rate", "mean_wasted_tokens", "mean_ttff_ms",
            "median_turns_after_fault", "median_switches",
        ):
            self.assertIn(key, agg)


if __name__ == "__main__":
    unittest.main()
