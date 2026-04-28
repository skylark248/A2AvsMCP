"""failure_mode_classifier 6-template headlines per lane (RACE-06, D-35, D-37).

Asserts each of the 6 dominant tags produces a non-empty templated headline,
and that lane-specific characteristic-event phrases (D-37) appear:
- pure_mcp: 'retried {tool} {n} times'
- pure_a2a: 'delegated {n} times'
- hybrid:  'switched protocol path {n} times'
"""
from __future__ import annotations

import unittest

from a2a_vs_mcp.race.classifier import failure_mode_classifier


class TestSixTemplatesPureMcp(unittest.TestCase):
    """All 6 templates exercised for pure_mcp lane."""

    def _agg(self, **overrides) -> dict:
        base = {
            "recovery_rate": 0.6,
            "mean_wasted_tokens": 250.0,
            "mean_ttff_ms": 1500.0,
            "median_turns_after_fault": 4,
            "median_retries": 2,
            "characteristic_tool": "list_files",
        }
        base.update(overrides)
        return base

    def test_recovered_template(self) -> None:
        h = failure_mode_classifier(
            "pure_mcp", "summarize_repo",
            ["recovered", "recovered", "recovered"],
            self._agg(recovery_rate=1.0),
        )
        self.assertIn("recovered", h)
        self.assertIn("pure_mcp", h)

    def test_gave_up_template(self) -> None:
        h = failure_mode_classifier(
            "pure_mcp", "summarize_repo",
            ["gave_up", "gave_up", "gave_up"],
            self._agg(median_give_up_turn=4, recovery_rate=0.0),
        )
        self.assertIn("gave up", h)

    def test_kept_going_without_noticing_template(self) -> None:
        # pure_mcp characteristic phrase: 'retried {tool} {n} times'
        h = failure_mode_classifier(
            "pure_mcp", "summarize_repo",
            ["kept_going_without_noticing", "kept_going_without_noticing"],
            self._agg(median_retries=3, characteristic_tool="list_files"),
        )
        self.assertIn("retried list_files 3 times", h)

    def test_kept_going_to_failure_template(self) -> None:
        h = failure_mode_classifier(
            "pure_mcp", "summarize_repo",
            ["kept_going_to_failure", "kept_going_to_failure"],
            self._agg(),
        )
        self.assertIn("kept going past", h)
        self.assertIn("recovery 0%", h)

    def test_indeterminate_template(self) -> None:
        h = failure_mode_classifier(
            "pure_mcp", "summarize_repo",
            ["indeterminate", "indeterminate", "indeterminate"],
            self._agg(),
        )
        self.assertIn("indeterminate runs", h)

    def test_lane_failed_template(self) -> None:
        h = failure_mode_classifier(
            "pure_mcp", "summarize_repo",
            ["lane_failed", "lane_failed", "lane_failed"],
            self._agg(lane_failed_reason="timeout"),
        )
        self.assertIn("could not complete", h)
        self.assertIn("timeout", h)


class TestSixTemplatesPureA2A(unittest.TestCase):
    """All 6 templates exercised for pure_a2a lane (D-37 phrase = 'delegated N times')."""

    def _agg(self, **overrides) -> dict:
        base = {
            "recovery_rate": 0.6,
            "mean_wasted_tokens": 300.0,
            "mean_ttff_ms": 1700.0,
            "median_turns_after_fault": 4,
            "median_delegations": 2,
        }
        base.update(overrides)
        return base

    def test_recovered_template(self) -> None:
        h = failure_mode_classifier(
            "pure_a2a", "negotiate_meeting",
            ["recovered", "recovered"],
            self._agg(recovery_rate=1.0),
        )
        self.assertIn("recovered", h)
        self.assertIn("pure_a2a", h)

    def test_gave_up_template(self) -> None:
        h = failure_mode_classifier(
            "pure_a2a", "negotiate_meeting",
            ["gave_up", "gave_up"],
            self._agg(median_give_up_turn=3, recovery_rate=0.0),
        )
        self.assertIn("gave up", h)

    def test_kept_going_without_noticing_template(self) -> None:
        h = failure_mode_classifier(
            "pure_a2a", "negotiate_meeting",
            ["kept_going_without_noticing", "kept_going_without_noticing"],
            self._agg(median_delegations=4),
        )
        self.assertIn("delegated 4 times", h)

    def test_kept_going_to_failure_template(self) -> None:
        h = failure_mode_classifier(
            "pure_a2a", "negotiate_meeting",
            ["kept_going_to_failure"],
            self._agg(),
        )
        self.assertIn("kept going past", h)

    def test_indeterminate_template(self) -> None:
        h = failure_mode_classifier(
            "pure_a2a", "negotiate_meeting",
            ["indeterminate"],
            self._agg(),
        )
        self.assertIn("indeterminate runs", h)

    def test_lane_failed_template(self) -> None:
        h = failure_mode_classifier(
            "pure_a2a", "negotiate_meeting",
            ["lane_failed"],
            self._agg(lane_failed_reason="RateLimitError"),
        )
        self.assertIn("could not complete", h)
        self.assertIn("RateLimitError", h)


class TestSixTemplatesHybrid(unittest.TestCase):
    """All 6 templates exercised for hybrid lane (D-37 phrase = 'switched protocol path N times')."""

    def _agg(self, **overrides) -> dict:
        base = {
            "recovery_rate": 0.6,
            "mean_wasted_tokens": 350.0,
            "mean_ttff_ms": 1900.0,
            "median_turns_after_fault": 4,
            "median_switches": 5,
        }
        base.update(overrides)
        return base

    def test_recovered_template(self) -> None:
        h = failure_mode_classifier(
            "hybrid", "book_travel",
            ["recovered"],
            self._agg(recovery_rate=1.0),
        )
        self.assertIn("recovered", h)
        self.assertIn("hybrid", h)

    def test_gave_up_template(self) -> None:
        h = failure_mode_classifier(
            "hybrid", "book_travel",
            ["gave_up", "gave_up"],
            self._agg(median_give_up_turn=5, recovery_rate=0.0),
        )
        self.assertIn("gave up", h)

    def test_kept_going_without_noticing_template(self) -> None:
        h = failure_mode_classifier(
            "hybrid", "book_travel",
            ["kept_going_without_noticing"],
            self._agg(median_switches=6),
        )
        self.assertIn("switched protocol path 6 times", h)

    def test_kept_going_to_failure_template(self) -> None:
        h = failure_mode_classifier(
            "hybrid", "book_travel",
            ["kept_going_to_failure"],
            self._agg(),
        )
        self.assertIn("kept going past", h)

    def test_indeterminate_template(self) -> None:
        h = failure_mode_classifier(
            "hybrid", "book_travel",
            ["indeterminate"],
            self._agg(),
        )
        self.assertIn("indeterminate runs", h)

    def test_lane_failed_template(self) -> None:
        h = failure_mode_classifier(
            "hybrid", "book_travel",
            ["lane_failed"],
            self._agg(lane_failed_reason="APITimeoutError"),
        )
        self.assertIn("could not complete", h)
        self.assertIn("APITimeoutError", h)


if __name__ == "__main__":
    unittest.main()
