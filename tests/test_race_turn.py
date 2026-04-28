"""Unit tests for src/a2a_vs_mcp/race/turn.py — per-lane turn-defining events (D-15..D-17)."""
from __future__ import annotations

from a2a_vs_mcp.race.turn import TURN_DEFINING_EVENTS, is_turn_defining


def test_pure_mcp_tool_call_is_turn_defining():
    assert is_turn_defining("pure_mcp", "tool_call") is True


def test_pure_mcp_agent_msg_is_not_turn_defining():
    # pure_mcp does NOT count agent_msg
    assert is_turn_defining("pure_mcp", "agent_msg") is False


def test_pure_a2a_agent_msg_is_turn_defining():
    assert is_turn_defining("pure_a2a", "agent_msg") is True


def test_pure_a2a_tool_call_is_not_turn_defining():
    # pure_a2a does NOT count tool_call
    assert is_turn_defining("pure_a2a", "tool_call") is False


def test_hybrid_is_set_union_of_tool_call_and_agent_msg():
    # D-16: hybrid is a set-union, not a special-cased branch
    assert is_turn_defining("hybrid", "tool_call") is True
    assert is_turn_defining("hybrid", "agent_msg") is True


def test_hybrid_tick_is_not_turn_defining():
    # Only tool_call + agent_msg are turn-defining for hybrid
    assert is_turn_defining("hybrid", "tick") is False


def test_unknown_lane_returns_false_no_keyerror():
    # Silent-fallback contract: unknown lanes never raise KeyError
    assert is_turn_defining("unknown_lane", "tool_call") is False


def test_hybrid_dispatch_table_exact_set():
    assert TURN_DEFINING_EVENTS["hybrid"] == {"tool_call", "agent_msg"}


def test_dispatch_table_full_shape():
    # D-16 verbatim — three lanes, exact mapping
    assert TURN_DEFINING_EVENTS == {
        "pure_mcp": {"tool_call"},
        "pure_a2a": {"agent_msg"},
        "hybrid": {"tool_call", "agent_msg"},
    }
