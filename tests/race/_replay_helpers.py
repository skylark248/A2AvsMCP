"""Shared helper: feed Detector(K) over a fixture trace, return terminal tag.

Single source of truth for replay-symmetric tag computation in tests
(HEAT-03 + HEAT-04). Mirrors the runners' Detector usage at
race/runners/pure_mcp.py:95 / pure_a2a.py:166 / hybrid.py:75.

Phase 7 D-33 symmetry-by-construction is preserved here because both runtime
and replay call ``Detector(K).consume()`` over the same event sequence — this
helper is NOT a parallel implementation, it reuses the production class verbatim.
"""
from __future__ import annotations

from a2a_vs_mcp.race.classifier import Detector


def replay_with_k(events: list[dict], K: int, score_pass: bool) -> str:
    """Replay a fixture trace through Detector(K). Return terminal tag.

    1. Find the first fault_injected event → instantiate Detector(K).
    2. Feed every subsequent event into detector.consume().
    3. On ``done`` event arrival, call finalize_at_done(score_pass) and return.
    4. If no ``done`` event is present, finalize at end-of-events with the same call.
    """
    fi = next((e for e in events if e.get("event_type") == "fault_injected"), None)
    if fi is None:
        raise ValueError("fixture has no fault_injected event")
    detector = Detector(
        fault_id=fi["fault_id"],
        fault_kind=fi["fault_kind"],
        target=fi["target"],
        fault_inject_turn=fi.get("turn_index", 0),
        K=K,
    )
    fi_idx = events.index(fi)
    for ev in events[fi_idx + 1:]:
        if ev.get("event_type") == "done":
            return detector.finalize_at_done(score_pass)
        detector.consume(ev)
    return detector.finalize_at_done(score_pass)
