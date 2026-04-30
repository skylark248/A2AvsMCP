"""Heatmap aggregator + in-process cache (D-52, D-54, D-55, D-57).

get_heatmap() walks RUNS_DIR/*.json, filters runs by run_meta event match
against HEATMAP_BASELINE (model, seed, task_id in baseline.task_ids), buckets
cells by (HardnessType, lane), picks dominant_tag per cell, computes
recovery_rate = {num: count(score_pass=True), den: total}, and returns
{cells, baseline}.

Cache invalidated on race_done by harness via invalidate_cache(). Counts are
NEVER persisted; rebuilt on demand. NO live LLM. NO network. Pure ndjson scan
+ bucket. Mirrors the pure-function aggregator pattern of metrics.py.

NOTE: Plan 09-01 Task 1 only needs invalidate_cache() to satisfy the harness
race_done hook. Full get_heatmap() + _build_cells() implementation lands in
Plan 09-01 Task 2 alongside the FastAPI route.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from .config import HEATMAP_BASELINE, HeatmapBaseline
from .replay import load_run
from .runs import RUNS_DIR
from .tasks import TASK_CONFIGS


# Module-level cache. Key: (model, seed, sorted-task_ids tuple) — see
# tuple(sorted(...)) below for order-independence per CONTEXT §Specifics.
_CACHE: dict[tuple, list[dict[str, Any]]] = {}


def invalidate_cache() -> None:
    """Drop the entire heatmap cache (D-54). Called by harness post-race_done."""
    _CACHE.clear()


def get_heatmap() -> dict[str, Any]:
    """Return {cells, baseline}. Rebuilds from disk on cache miss (D-52, D-54)."""
    key = (
        HEATMAP_BASELINE.model,
        HEATMAP_BASELINE.seed,
        tuple(sorted(HEATMAP_BASELINE.task_ids)),  # order-independent cache key
    )
    if key not in _CACHE:
        _CACHE[key] = _build_cells(HEATMAP_BASELINE)
    return {
        "cells": _CACHE[key],
        "baseline": HEATMAP_BASELINE.to_dict(),
    }


# ---------------------------------------------------------------------------
# Internal: cell builder + helpers (Task 2 — Plan 09-01).
# ---------------------------------------------------------------------------


def _matches_baseline(meta: dict[str, Any] | None, baseline: HeatmapBaseline) -> bool:
    """D-55 + D-57 filter: run_meta must exist + match model/seed/task_id.

    Missing run_meta (legacy pre-D-58 runs) is silent exclusion.
    """
    if meta is None:
        return False
    if meta.get("model") != baseline.model:
        return False
    if meta.get("seed") != baseline.seed:
        return False
    if meta.get("task_id") not in baseline.task_ids:
        return False
    return True


def _per_run_terminal_tag(events: list[dict[str, Any]]) -> str:
    """Map a single run's events to one of the 5 terminal tags.

    Mirrors harness._per_run_tag semantics (the runner's scorer already minted
    these via the Detector; we read the run-level outcome from the `done`
    event without re-running the state machine).

    Reduction rules (matches harness._per_run_tag):
      score_pass True            -> "recovered" (success + recovery)
      score_pass False, observed -> "kept_going_to_failure"
      score_pass False, missed   -> "kept_going_without_noticing"
      no done event              -> "indeterminate"
    """
    done = next((e for e in events if e.get("event_type") == "done"), None)
    if done is None:
        return "indeterminate"
    score_pass = done.get("score_pass")
    has_observed = any(e.get("event_type") == "fault_observed" for e in events)
    if score_pass is True:
        return "recovered"
    if score_pass is False and has_observed:
        return "kept_going_to_failure"
    if score_pass is False and not has_observed:
        return "kept_going_without_noticing"
    return "indeterminate"


def _build_cells(baseline: HeatmapBaseline) -> list[dict[str, Any]]:
    """Walk RUNS_DIR; bucket baseline-matching runs by (hardness_type, lane).

    Each task's hardness_profile (from task_config.yaml) determines which
    rows the run contributes to — a run with hardness_profile=[long_chain,
    rate_pressure] contributes to BOTH the long_chain row and the
    rate_pressure row in its lane column.

    Returns cells with the EXACT D-53 5-key shape:
      {hardness_type, lane, dominant_tag, recovery_rate, sample_run_id}
    """
    # Bucket: (hardness_type, lane) -> {tags: [...], score_passes: [...], sample_run_id: str}
    buckets: dict[tuple[str, str], dict[str, Any]] = {}

    if not RUNS_DIR.exists():
        return []

    for path in sorted(RUNS_DIR.glob("*.json")):
        run_id = path.stem
        try:
            events = load_run(run_id, RUNS_DIR)
        except (FileNotFoundError, ValueError):
            # Path-traversal-rejected or unreadable file — silent skip.
            continue
        if not events:
            continue

        meta = next((e for e in events if e.get("event_type") == "run_meta"), None)
        if not _matches_baseline(meta, baseline):
            continue  # D-57 silent exclusion

        task_id = meta["task_id"]
        lane = meta.get("lane")
        if lane not in {"pure_mcp", "pure_a2a", "hybrid"}:
            continue

        # Look up hardness types from task config (rows this run contributes to).
        try:
            cfg, _t, _b = TASK_CONFIGS[task_id]
        except KeyError:
            continue
        hardness_types = [
            ht.value if hasattr(ht, "value") else str(ht)
            for ht in cfg.hardness_profile
        ]

        # Per-run terminal tag + score_pass for the recovery_rate numerator.
        tag = _per_run_terminal_tag(events)
        done = next((e for e in events if e.get("event_type") == "done"), None)
        score_pass = bool(done.get("score_pass")) if done is not None else False

        for hardness_type in hardness_types:
            key = (hardness_type, lane)
            bucket = buckets.setdefault(key, {
                "tags": [],
                "score_passes": [],
                "sample_run_id": run_id,
            })
            bucket["tags"].append(tag)
            bucket["score_passes"].append(score_pass)

    # Materialize cells.
    cells: list[dict[str, Any]] = []
    for (hardness_type, lane), bucket in sorted(buckets.items()):
        tags = bucket["tags"]
        score_passes = bucket["score_passes"]
        # Counter.most_common is stable: ties resolved by insertion order.
        dominant_tag = Counter(tags).most_common(1)[0][0]
        cells.append({
            "hardness_type": hardness_type,
            "lane": lane,
            "dominant_tag": dominant_tag,
            "recovery_rate": {
                "num": sum(1 for sp in score_passes if sp),
                "den": len(score_passes),
            },
            "sample_run_id": bucket["sample_run_id"],
        })
    return cells


__all__ = ["get_heatmap", "invalidate_cache"]
