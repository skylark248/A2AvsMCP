"""Heatmap aggregator + route tests (D-52..D-57).

Pins all four invariants:
1. Pinned-baseline filter (D-55, D-57) — silent exclusion of off-baseline runs.
2. Cell shape (D-53) — exactly 5 keys; recovery_rate is {num, den}.
3. Cache invalidation (D-54) — invalidate_cache empties _CACHE; next get rebuilds.
4. Off-baseline exclusion — missing run_meta, wrong model, wrong seed, off-task.

Plus the FastAPI route smoke test: GET /api/race/heatmap returns the locked
{cells, baseline} payload with baseline = HEATMAP_BASELINE.to_dict().
"""
from __future__ import annotations

import importlib
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any
from unittest.mock import patch

from fastapi.testclient import TestClient

from a2a_vs_mcp.race import heatmap as heatmap_mod
from a2a_vs_mcp.race.config import HEATMAP_BASELINE


def _write_run(runs_dir: Path, run_id: str, events: list[dict[str, Any]]) -> Path:
    """Write a list of events as ndjson (one event per line) to runs_dir/run_id.json.

    Mirrors the on-disk format produced by RunWriter (race/runs.py).
    """
    runs_dir.mkdir(parents=True, exist_ok=True)
    path = runs_dir / f"{run_id}.json"
    with path.open("w", encoding="utf-8") as fh:
        for ev in events:
            fh.write(json.dumps(ev) + "\n")
    return path


def _baseline_run_events(
    *,
    task_id: str = "summarize_repo",
    lane: str = "pure_mcp",
    run_id: str = "pure_mcp-summarize_repo-0-abc123",
    score_pass: bool = True,
    include_run_meta: bool = True,
    model: str = "claude-sonnet-4-6",
    seed: int = 42,
) -> list[dict[str, Any]]:
    """Build a minimal trace event list for an aggregator-friendly run."""
    events: list[dict[str, Any]] = []
    if include_run_meta:
        events.append({
            "event_type": "run_meta",
            "trace_schema_version": "1.0",
            "model": model,
            "seed": seed,
            "task_id": task_id,
            "lane": lane,
            "run_id": run_id,
        })
    else:
        # Need trace_schema_version on the first event for migrate_v1.
        events.append({
            "event_type": "tick",
            "trace_schema_version": "1.0",
            "lane": lane,
        })
    events.append({
        "event_type": "done",
        "score_pass": score_pass,
        "lane": lane,
    })
    return events


class _IsolatedRunsDirMixin:
    """Patches RUNS_DIR (in both runs.py and heatmap.py) to a per-test tmp dir."""

    def setUp(self) -> None:
        self._tmp = TemporaryDirectory()
        self.runs_dir = Path(self._tmp.name) / "runs"
        self.runs_dir.mkdir(parents=True, exist_ok=True)
        # Patch RUNS_DIR in BOTH modules: runs.py (where load_run will look up
        # the constant transitively if we call it), and heatmap.py (which
        # captures RUNS_DIR via from-import at module load).
        self._patches = [
            patch("a2a_vs_mcp.race.heatmap.RUNS_DIR", self.runs_dir),
            patch("a2a_vs_mcp.race.runs.RUNS_DIR", self.runs_dir),
        ]
        for p in self._patches:
            p.start()
        # Always start with an empty cache so cache state never bleeds across tests.
        heatmap_mod.invalidate_cache()

    def tearDown(self) -> None:
        for p in self._patches:
            p.stop()
        heatmap_mod.invalidate_cache()
        self._tmp.cleanup()


class TestHeatmapPayloadShape(_IsolatedRunsDirMixin, unittest.TestCase):
    """D-52: get_heatmap returns {cells, baseline}; baseline = HEATMAP_BASELINE.to_dict()."""

    def test_get_heatmap_returns_payload_with_baseline(self) -> None:
        payload = heatmap_mod.get_heatmap()
        self.assertEqual(set(payload.keys()), {"cells", "baseline"})
        self.assertEqual(payload["baseline"], HEATMAP_BASELINE.to_dict())
        self.assertEqual(
            payload["baseline"],
            {
                "model": "claude-sonnet-4-6",
                "seed": 42,
                "task_ids": ["summarize_repo", "negotiate_meeting", "book_travel"],
            },
        )

    def test_empty_corpus_returns_empty_cells(self) -> None:
        """Zero matching runs -> {cells: [], baseline: {...}} (no error)."""
        payload = heatmap_mod.get_heatmap()
        self.assertEqual(payload["cells"], [])
        # Baseline still present for the footer pass-through.
        self.assertIn("baseline", payload)


class TestBaselineFilter(_IsolatedRunsDirMixin, unittest.TestCase):
    """D-55, D-57: off-baseline runs silently excluded."""

    def test_baseline_filter_excludes_off_model(self) -> None:
        _write_run(
            self.runs_dir,
            "pure_mcp-summarize_repo-0-aaa111",
            _baseline_run_events(model="claude-haiku-3-5"),
        )
        payload = heatmap_mod.get_heatmap()
        self.assertEqual(payload["cells"], [])

    def test_baseline_filter_excludes_off_seed(self) -> None:
        _write_run(
            self.runs_dir,
            "pure_mcp-summarize_repo-0-aaa222",
            _baseline_run_events(seed=99),
        )
        payload = heatmap_mod.get_heatmap()
        self.assertEqual(payload["cells"], [])

    def test_baseline_filter_excludes_missing_run_meta(self) -> None:
        """Pre-D-58 legacy runs (no run_meta event) silently excluded (D-57)."""
        _write_run(
            self.runs_dir,
            "pure_mcp-summarize_repo-0-aaa333",
            _baseline_run_events(include_run_meta=False),
        )
        payload = heatmap_mod.get_heatmap()
        self.assertEqual(payload["cells"], [])

    def test_baseline_filter_excludes_off_task(self) -> None:
        _write_run(
            self.runs_dir,
            "pure_mcp-out_of_scope_task-0-aaa444",
            _baseline_run_events(task_id="out_of_scope_task"),
        )
        payload = heatmap_mod.get_heatmap()
        self.assertEqual(payload["cells"], [])


class TestCellShape(_IsolatedRunsDirMixin, unittest.TestCase):
    """D-53: cells have EXACTLY {hardness_type, lane, dominant_tag, recovery_rate, sample_run_id}."""

    def test_cell_shape_exact_d53_keys(self) -> None:
        _write_run(
            self.runs_dir,
            "pure_mcp-summarize_repo-0-bbb111",
            _baseline_run_events(score_pass=True),
        )
        payload = heatmap_mod.get_heatmap()
        self.assertGreater(len(payload["cells"]), 0)
        cell = payload["cells"][0]
        self.assertEqual(
            set(cell.keys()),
            {"hardness_type", "lane", "dominant_tag", "recovery_rate", "sample_run_id"},
        )
        self.assertEqual(set(cell["recovery_rate"].keys()), {"num", "den"})
        self.assertIsInstance(cell["recovery_rate"]["num"], int)
        self.assertIsInstance(cell["recovery_rate"]["den"], int)
        self.assertEqual(cell["lane"], "pure_mcp")
        # summarize_repo hardness_profile = [long_chain, rate_pressure, schema_variance]
        self.assertIn(cell["hardness_type"], {"long_chain", "rate_pressure", "schema_variance"})
        # dominant_tag should be one of the 5 terminal tags.
        self.assertIn(cell["dominant_tag"], {
            "recovered", "gave_up", "kept_going_without_noticing",
            "kept_going_to_failure", "indeterminate",
        })

    def test_recovery_rate_counts_score_pass(self) -> None:
        """recovery_rate.num counts score_pass=True; .den counts all runs in bucket."""
        # 2 baseline runs same lane/task; 1 passes, 1 fails.
        _write_run(
            self.runs_dir,
            "pure_mcp-summarize_repo-0-ccc111",
            _baseline_run_events(score_pass=True),
        )
        _write_run(
            self.runs_dir,
            "pure_mcp-summarize_repo-1-ccc222",
            _baseline_run_events(score_pass=False),
        )
        payload = heatmap_mod.get_heatmap()
        # All cells share the same recovery_rate because both runs contribute
        # to all 3 hardness rows of summarize_repo, same lane.
        for cell in payload["cells"]:
            self.assertEqual(cell["recovery_rate"]["num"], 1)
            self.assertEqual(cell["recovery_rate"]["den"], 2)

    def test_no_extra_keys_on_cells(self) -> None:
        """No tag_distribution / per_fault_array / extra_meta keys (D-53 minimal shape)."""
        _write_run(
            self.runs_dir,
            "pure_mcp-summarize_repo-0-ddd111",
            _baseline_run_events(),
        )
        payload = heatmap_mod.get_heatmap()
        for cell in payload["cells"]:
            self.assertNotIn("tag_distribution", cell)
            self.assertNotIn("per_fault_array", cell)
            self.assertNotIn("extra_meta", cell)


class TestCacheBehavior(_IsolatedRunsDirMixin, unittest.TestCase):
    """D-54: in-memory cache + invalidate_cache() rebuild contract."""

    def test_invalidate_cache_clears_state(self) -> None:
        _write_run(
            self.runs_dir,
            "pure_mcp-summarize_repo-0-eee111",
            _baseline_run_events(),
        )
        # First call populates cache.
        heatmap_mod.get_heatmap()
        self.assertGreater(len(heatmap_mod._CACHE), 0)
        # Invalidate -> empty.
        heatmap_mod.invalidate_cache()
        self.assertEqual(len(heatmap_mod._CACHE), 0)
        # Subsequent get rebuilds.
        heatmap_mod.get_heatmap()
        self.assertGreater(len(heatmap_mod._CACHE), 0)

    def test_cache_key_uses_sorted_task_ids(self) -> None:
        """Cache key tuple is order-independent: sorted task_ids tuple in slot 2."""
        heatmap_mod.get_heatmap()
        keys = list(heatmap_mod._CACHE.keys())
        self.assertEqual(len(keys), 1)
        key = keys[0]
        # Slot 0 = model, 1 = seed, 2 = sorted-task_ids tuple.
        self.assertEqual(key[0], "claude-sonnet-4-6")
        self.assertEqual(key[1], 42)
        self.assertEqual(
            key[2],
            tuple(sorted(("summarize_repo", "negotiate_meeting", "book_travel"))),
        )
        # Sorted tuple confirms order-independence.
        self.assertEqual(list(key[2]), sorted(key[2]))

    def test_cache_hit_does_not_rebuild(self) -> None:
        """Second get_heatmap() call returns the same cells list (object identity)."""
        _write_run(
            self.runs_dir,
            "pure_mcp-summarize_repo-0-fff111",
            _baseline_run_events(),
        )
        first = heatmap_mod.get_heatmap()
        second = heatmap_mod.get_heatmap()
        # Cache hit: cells list is the SAME list object.
        self.assertIs(first["cells"], second["cells"])


class TestRouteSmoke(_IsolatedRunsDirMixin, unittest.TestCase):
    """GET /api/race/heatmap returns the locked payload (route mounted in web.py)."""

    def test_route_returns_payload_with_baseline(self) -> None:
        # Import inside the test so RUNS_DIR patches are active when web.py loads.
        from a2a_vs_mcp.web import app
        client = TestClient(app)
        res = client.get("/api/race/heatmap")
        self.assertEqual(res.status_code, 200)
        payload = res.json()
        self.assertEqual(set(payload.keys()), {"cells", "baseline"})
        self.assertEqual(payload["baseline"]["model"], "claude-sonnet-4-6")
        self.assertEqual(payload["baseline"]["seed"], 42)
        self.assertEqual(
            payload["baseline"]["task_ids"],
            ["summarize_repo", "negotiate_meeting", "book_travel"],
        )
        # Empty corpus -> empty cells; route still 200.
        self.assertIsInstance(payload["cells"], list)


if __name__ == "__main__":
    unittest.main()
