"""Unit tests for race wire schemas (Plan 06-01).

Mirrors the 5 <behavior> tests from .planning/phases/06-tracerecorder-schema-gate-race-foundation/06-01-PLAN.md.
"""
from __future__ import annotations


def test_all_eight_wire_dataclasses_importable() -> None:
    from a2a_vs_mcp.race.schemas import (  # noqa: F401
        AgentMsgEvent,
        DoneEvent,
        ErrorEvent,
        FaultInjectedEvent,
        FaultObservedEvent,
        RaceDoneEvent,
        TickEvent,
        ToolCallEvent,
        WIRE_EVENT_TYPES,
    )


def test_wire_event_types_matches_d06_verbatim() -> None:
    from a2a_vs_mcp.race.schemas import WIRE_EVENT_TYPES

    assert WIRE_EVENT_TYPES == frozenset(
        {
            "tick",
            "tool_call",
            "agent_msg",
            "fault_injected",
            "fault_observed",
            "done",
            "error",
            "race_done",
        }
    )


def test_tick_event_to_dict_shape() -> None:
    from a2a_vs_mcp.race.schemas import TickEvent

    assert TickEvent(lane="pure_mcp", turn_index=3, task_id="t1", t_ms=12).to_dict() == {
        "event_type": "tick",
        "lane": "pure_mcp",
        "turn_index": 3,
        "task_id": "t1",
        "t_ms": 12,
    }


def test_fault_injected_carries_trc03_fields() -> None:
    from a2a_vs_mcp.race.schemas import FaultInjectedEvent

    d = FaultInjectedEvent(
        lane="pure_mcp",
        turn_index=4,
        fault_id="f1",
        fault_kind="rate_limit_429",
        target="github.repos",
        t_inject_ms=1730000000000,
    ).to_dict()
    assert d["event_type"] == "fault_injected"
    assert {"fault_id", "fault_kind", "target", "t_inject_ms"} <= set(d)


def test_fault_observed_carries_all_seven_trc03_fields() -> None:
    from a2a_vs_mcp.race.schemas import FaultObservedEvent

    d = FaultObservedEvent(
        lane="pure_mcp",
        turn_index=7,
        fault_id="f1",
        fault_kind="rate_limit_429",
        target="github.repos",
        t_observed_ms=1730000005000,
        evidence="429 retry-after",
        wasted_tokens_before_detection=1234,
    ).to_dict()
    assert d["event_type"] == "fault_observed"
    assert {
        "fault_id",
        "fault_kind",
        "target",
        "t_observed_ms",
        "evidence",
        "wasted_tokens_before_detection",
    } <= set(d)
