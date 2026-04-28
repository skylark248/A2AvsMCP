"""D-30 hardness coverage matrix: each v1 HardnessType in >=2 of 3 tasks (RACE-01).

Locked matrix per master design + 07-CONTEXT.md D-30:
  LONG_CHAIN              ⊆ {summarize_repo, book_travel}
  RATE_PRESSURE           ⊆ {summarize_repo, book_travel}
  SCHEMA_VARIANCE         ⊆ {summarize_repo, negotiate_meeting}
  MULTI_SOURCE_SYNTHESIS  ⊆ {negotiate_meeting, book_travel}
"""
from __future__ import annotations

import unittest

from a2a_vs_mcp.race.tasks import TASK_CONFIGS
from a2a_vs_mcp.race.types import HardnessType


def _types_for(task_id: str) -> set[str]:
    cfg, _, _ = TASK_CONFIGS[task_id]
    return {h.value for h in cfg.hardness_profile}


class TestHardnessCoverageMatrix(unittest.TestCase):
    """D-30 locked matrix: every HardnessType -> exact set of tasks."""

    def test_long_chain_in_summarize_and_book_travel(self) -> None:
        self.assertIn(HardnessType.LONG_CHAIN.value, _types_for("summarize_repo"))
        self.assertIn(HardnessType.LONG_CHAIN.value, _types_for("book_travel"))

    def test_rate_pressure_in_summarize_and_book_travel(self) -> None:
        self.assertIn(HardnessType.RATE_PRESSURE.value, _types_for("summarize_repo"))
        self.assertIn(HardnessType.RATE_PRESSURE.value, _types_for("book_travel"))

    def test_schema_variance_in_summarize_and_negotiate_meeting(self) -> None:
        self.assertIn(HardnessType.SCHEMA_VARIANCE.value, _types_for("summarize_repo"))
        self.assertIn(HardnessType.SCHEMA_VARIANCE.value, _types_for("negotiate_meeting"))

    def test_multi_source_synthesis_in_negotiate_and_book_travel(self) -> None:
        self.assertIn(HardnessType.MULTI_SOURCE_SYNTHESIS.value, _types_for("negotiate_meeting"))
        self.assertIn(HardnessType.MULTI_SOURCE_SYNTHESIS.value, _types_for("book_travel"))

    def test_each_v1_hardness_type_covers_at_least_two_tasks(self) -> None:
        """D-30: every HardnessType appears in >= 2 of 3 v1 tasks."""
        all_tasks = ["summarize_repo", "negotiate_meeting", "book_travel"]
        for ht in HardnessType:
            count = sum(1 for tid in all_tasks if ht.value in _types_for(tid))
            self.assertGreaterEqual(
                count, 2,
                f"HardnessType {ht.value} only covers {count} task(s); D-30 requires >= 2",
            )


if __name__ == "__main__":
    unittest.main()
