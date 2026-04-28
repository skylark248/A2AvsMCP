"""Per-lane turn-defining event rules (D-15, D-16, D-17).

TraceRecorder.record() lazy-imports is_turn_defining and bumps _turn_index when
the (lane, event_type) pair matches. Module-level constant + helper mirrors
src/a2a_vs_mcp/trace.py:19-22 (_PHASE_MAP) and src/a2a_vs_mcp/config.py:21-49 (PROFILES).
"""
from __future__ import annotations

# D-16 verbatim: hybrid is a set-union, NOT a special branch in TraceRecorder.
TURN_DEFINING_EVENTS: dict[str, set[str]] = {
    "pure_mcp": {"tool_call"},
    "pure_a2a": {"agent_msg"},
    "hybrid": {"tool_call", "agent_msg"},
}


def is_turn_defining(lane: str, event_type: str) -> bool:
    """Return True iff event_type is a turn-defining event for the given lane.

    Unknown lanes return False (silent fallback — TraceRecorder treats lane=None as
    legacy v1 mode and never calls this function in that case, per D-03/D-18).
    """
    return event_type in TURN_DEFINING_EVENTS.get(lane, set())
