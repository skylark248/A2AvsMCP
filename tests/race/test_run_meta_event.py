"""run_meta first-event emission + HEATMAP_BASELINE singleton tests (D-56, D-58).

D-58: harness emits run_meta as the FIRST event of every per-run trace.
D-56: HEATMAP_BASELINE is the single source of truth for the pinned (model,
seed, task_ids) tuple — frozen dataclass + module singleton.

Mirrors the test_harness.py recorder-mock idiom (factory-returns-TraceRecorder)
so the run_meta assertion runs against real recorder.events buffers without
hitting disk.
"""
from __future__ import annotations

import asyncio
import unittest
from typing import Any
from unittest.mock import patch

from a2a_vs_mcp.race import harness as harness_mod
from a2a_vs_mcp.race.config import HEATMAP_BASELINE, HeatmapBaseline
from a2a_vs_mcp.race.types import (
    HardnessProfile,
    HardnessType,
    RaceResult,
    ScoreCard,
    TaskSpec,
)
from a2a_vs_mcp.trace import TraceRecorder


def _make_spec(task_id: str = "summarize_repo") -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        prompt="",
        allowed_tools=[],
        expected_shape={},
        hardness_profile=HardnessProfile(types=[HardnessType.LONG_CHAIN]),
    )


def _good_result(lane: str, task_id: str, run_id: str) -> RaceResult:
    return RaceResult(
        run_id=run_id,
        lane=lane,
        task_id=task_id,
        hardness_profile=HardnessProfile(types=[HardnessType.LONG_CHAIN]),
        score_card=ScoreCard(
            success=True, ttff_ms=10, recovered=True,
            wasted_tokens_before_detection=0,
            failure_mode="success", cost_usd=0.0, latency_ms=10,
        ),
        trace_id=run_id,
    )


class TestHeatmapBaselineSingleton(unittest.TestCase):
    """D-56: HEATMAP_BASELINE is the single source of truth for the pinned baseline."""

    def test_baseline_values(self) -> None:
        """HEATMAP_BASELINE pins the v1 baseline (D-55)."""
        self.assertEqual(HEATMAP_BASELINE.model, "claude-sonnet-4-6")
        self.assertEqual(HEATMAP_BASELINE.seed, 42)
        self.assertEqual(
            HEATMAP_BASELINE.task_ids,
            ("summarize_repo", "negotiate_meeting", "book_travel"),
        )

    def test_baseline_to_dict_returns_list_task_ids(self) -> None:
        """to_dict() converts task_ids tuple -> list for JSON-serializable payload."""
        d = HEATMAP_BASELINE.to_dict()
        self.assertEqual(
            d,
            {
                "model": "claude-sonnet-4-6",
                "seed": 42,
                "task_ids": ["summarize_repo", "negotiate_meeting", "book_travel"],
            },
        )
        # Critical: list, not tuple, for JSON compatibility.
        self.assertIsInstance(d["task_ids"], list)

    def test_baseline_is_frozen(self) -> None:
        """Frozen dataclass — mutation must raise."""
        with self.assertRaises(Exception):  # FrozenInstanceError or AttributeError
            HEATMAP_BASELINE.model = "haiku"  # type: ignore[misc]

    def test_baseline_class_is_dataclass_frozen(self) -> None:
        """Sanity: HeatmapBaseline is a frozen dataclass (D-56)."""
        # frozen dataclasses set __hash__ to a non-None default
        b = HeatmapBaseline(model="m", seed=1, task_ids=("a",))
        # Hashable means frozen succeeded.
        self.assertIsNotNone(hash(b))


class TestRunMetaFirstEvent(unittest.TestCase):
    """D-58: run_meta is the first event of every per-run trace."""

    def _capture_recorders(self) -> tuple[list[TraceRecorder], Any]:
        """Build a recorder_factory that captures every TraceRecorder created."""
        captured: list[TraceRecorder] = []

        def factory(*, run_id: str, lane: str, task_id: str) -> TraceRecorder:
            rec = TraceRecorder(mode=lane, runtime="mock", task_id=task_id,
                                run_id=run_id, lane=lane)
            captured.append(rec)
            return rec

        return captured, factory

    def test_run_meta_is_first_event(self) -> None:
        """run_meta event lives at recorder.events[0] for every run (D-58)."""
        captured, factory = self._capture_recorders()

        async def fake_runner(task_spec, run_id, recorder, *args, **kw) -> RaceResult:
            # Simulate runner adding an event AFTER recorder construction.
            # run_meta MUST already be at index 0 by the time the runner runs.
            recorder.record("tick", note="runner started")
            return _good_result("pure_mcp", task_spec.task_id, run_id)

        with patch.dict(harness_mod._RUNNERS, {"pure_mcp": fake_runner}):
            asyncio.run(harness_mod.run_race(
                [_make_spec("summarize_repo")], ["pure_mcp"], n=1,
                recorder_factory=factory,
                ws_emitter=lambda ev: None,
            ))

        self.assertEqual(len(captured), 1)
        rec = captured[0]
        self.assertGreaterEqual(len(rec.events), 1)
        first = rec.events[0]
        self.assertEqual(first["event_type"], "run_meta")

    def test_run_meta_payload_shape(self) -> None:
        """run_meta carries model, seed, task_id, lane, run_id (+ trace_schema_version
        auto-stamped by the recorder)."""
        captured, factory = self._capture_recorders()

        async def fake_runner(task_spec, run_id, recorder, *args, **kw) -> RaceResult:
            return _good_result("pure_mcp", task_spec.task_id, run_id)

        with patch.dict(harness_mod._RUNNERS, {"pure_mcp": fake_runner}):
            asyncio.run(harness_mod.run_race(
                [_make_spec("summarize_repo")], ["pure_mcp"], n=1,
                recorder_factory=factory,
                ws_emitter=lambda ev: None,
            ))

        first = captured[0].events[0]
        self.assertEqual(first["event_type"], "run_meta")
        self.assertEqual(first["model"], "claude-sonnet-4-6")
        self.assertEqual(first["seed"], 42)
        self.assertEqual(first["task_id"], "summarize_repo")
        self.assertEqual(first["lane"], "pure_mcp")
        self.assertIn("run_id", first)
        # TraceRecorder auto-stamps trace_schema_version on every event.
        self.assertEqual(first.get("trace_schema_version"), "1.0")

    def test_run_meta_emitted_for_every_run(self) -> None:
        """Each (lane, task, run_idx) tuple gets its own run_meta event."""
        captured, factory = self._capture_recorders()

        async def fake_runner(task_spec, run_id, recorder, *args, **kw) -> RaceResult:
            return _good_result("pure_mcp", task_spec.task_id, run_id)

        with patch.dict(harness_mod._RUNNERS, {"pure_mcp": fake_runner}):
            asyncio.run(harness_mod.run_race(
                [_make_spec("summarize_repo")], ["pure_mcp"], n=3,
                recorder_factory=factory,
                ws_emitter=lambda ev: None,
            ))

        # n=3 runs → 3 recorders, each with run_meta as first event.
        self.assertEqual(len(captured), 3)
        for rec in captured:
            self.assertGreaterEqual(len(rec.events), 1)
            self.assertEqual(rec.events[0]["event_type"], "run_meta")
            # Each run has a distinct run_id.
            self.assertIn(rec.events[0]["run_id"], rec.run_id or "")


if __name__ == "__main__":
    unittest.main()
