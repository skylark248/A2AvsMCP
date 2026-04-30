"""Pinned race-demo configuration constants (D-55, D-56, D-57).

HEATMAP_BASELINE is the single source of truth for the closing-artifact
heatmap's aggregation scope. Footer reads from it. Aggregator filters from
it. Cache key derived from it. Drift kills the demo's honesty pill.

Mirrors the module-constant pattern from runs.py (RUNS_DIR) + types.py
(@dataclass(frozen=True) + to_dict()). Re-exports MODEL / SEED_DISCLOSURE
from harness.py rather than redefining — harness owns the locked values
(harness.py:53,58); this module owns the baseline tuple.
"""
from __future__ import annotations

from dataclasses import dataclass

from .harness import MODEL, SEED_DISCLOSURE  # MODEL='claude-sonnet-4-6'; SEED_DISCLOSURE=42


@dataclass(frozen=True)
class HeatmapBaseline:
    """Frozen pinned-baseline tuple (D-56).

    model + seed + task_ids together define the closing-artifact heatmap's
    aggregation scope. Off-baseline runs are silently excluded by the
    aggregator (D-55, D-57). The footer string is rendered from this same
    constant so the demo never silently lies about what it aggregated.
    """

    model: str
    seed: int
    task_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        """JSON-friendly view: task_ids tuple -> list."""
        return {
            "model": self.model,
            "seed": self.seed,
            "task_ids": list(self.task_ids),
        }


HEATMAP_BASELINE: HeatmapBaseline = HeatmapBaseline(
    model=MODEL,                # claude-sonnet-4-6 (harness.py:53)
    seed=SEED_DISCLOSURE,       # 42 (harness.py:58)
    task_ids=("summarize_repo", "negotiate_meeting", "book_travel"),
)


__all__ = ["HEATMAP_BASELINE", "HeatmapBaseline"]
