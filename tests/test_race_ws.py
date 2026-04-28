"""Unit tests for race/ws.py — ConnectionManager + coalesce + constants (Plan 06-07).

Plan 06-08 covers the lifecycle integration tests (TestClient.websocket_connect).
This file exercises ConnectionManager in isolation.
"""
from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from a2a_vs_mcp.race.ws import (
    COALESCE_THRESHOLD,
    HEARTBEAT_S,
    MANAGER,
    NEVER_COALESCE,
    PER_IP_CAP,
    Connection,
    ConnectionManager,
)


def test_constants_exact() -> None:
    assert HEARTBEAT_S == 15
    assert COALESCE_THRESHOLD == 50
    assert PER_IP_CAP == 5
    assert NEVER_COALESCE == frozenset({
        "tool_call", "agent_msg",
        "fault_injected", "fault_observed",
        "done", "error", "race_done",
    })
    # tick is the ONLY coalesce-eligible event type
    assert "tick" not in NEVER_COALESCE
    assert len(NEVER_COALESCE) == 7


def test_module_singleton_manager() -> None:
    assert isinstance(MANAGER, ConnectionManager)


def test_coalesce_below_threshold_returns_unchanged() -> None:
    buf: list[dict[str, Any]] = [
        {"event_type": "tick", "lane": "a", "task_id": "t1"} for _ in range(50)
    ]
    assert ConnectionManager.coalesce(buf) == buf


def test_coalesce_above_threshold_keeps_latest_tick_per_lane_task() -> None:
    # 60 ticks: 30 for (a,t1) and 30 for (b,t2). Latest of each survives.
    buf: list[dict[str, Any]] = []
    for i in range(30):
        buf.append({"event_type": "tick", "lane": "a", "task_id": "t1", "t_ms": i})
    for i in range(30):
        buf.append({"event_type": "tick", "lane": "b", "task_id": "t2", "t_ms": 100 + i})
    out = ConnectionManager.coalesce(buf)
    # Two coalesced ticks remain
    ticks = [e for e in out if e["event_type"] == "tick"]
    assert len(ticks) == 2
    # Latest per (lane, task_id) preserved
    by_key = {(e["lane"], e["task_id"]): e["t_ms"] for e in ticks}
    assert by_key[("a", "t1")] == 29
    assert by_key[("b", "t2")] == 129


def test_coalesce_preserves_never_coalesce_events_verbatim() -> None:
    buf: list[dict[str, Any]] = []
    # 51 ticks to exceed threshold
    for i in range(51):
        buf.append({"event_type": "tick", "lane": "a", "task_id": "t1", "t_ms": i})
    # Plus one of each NEVER_COALESCE type — none should be dropped
    never = [
        {"event_type": "tool_call", "lane": "a", "turn_index": 0},
        {"event_type": "agent_msg", "lane": "a", "turn_index": 1},
        {"event_type": "fault_injected", "lane": "a", "turn_index": 2},
        {"event_type": "fault_observed", "lane": "a", "turn_index": 3},
        {"event_type": "done", "lane": "a", "turn_index": 4},
        {"event_type": "error", "lane": "a", "turn_index": 5},
        {"event_type": "race_done", "turn_index": 6},
    ]
    buf.extend(never)
    out = ConnectionManager.coalesce(buf)
    for ev in never:
        assert ev in out, f"NEVER_COALESCE event dropped: {ev}"


@pytest.mark.asyncio
async def test_connect_enforces_per_ip_cap() -> None:
    mgr = ConnectionManager()
    # 5 connects from same IP succeed; 6th rejected
    conns = []
    for i in range(PER_IP_CAP):
        ws = MagicMock()
        ws.accept = AsyncMock()
        ws.close = AsyncMock()
        c = await mgr.connect(ws, run_id=f"run-{i}", last_seen_turn_index=-1, client_ip="1.2.3.4")
        assert c is not None
        conns.append((ws, c))
    # 6th from same IP — rejected, ws.close called with 4290, no accept
    ws6 = MagicMock()
    ws6.accept = AsyncMock()
    ws6.close = AsyncMock()
    c6 = await mgr.connect(ws6, run_id="run-x", last_seen_turn_index=-1, client_ip="1.2.3.4")
    assert c6 is None
    ws6.close.assert_awaited_once()
    args, kwargs = ws6.close.call_args
    assert kwargs.get("code") == 4290
    ws6.accept.assert_not_called()


@pytest.mark.asyncio
async def test_disconnect_decrements_ip_and_removes_from_run() -> None:
    mgr = ConnectionManager()
    ws = MagicMock()
    ws.accept = AsyncMock()
    ws.close = AsyncMock()
    conn = await mgr.connect(ws, run_id="run-a", last_seen_turn_index=-1, client_ip="9.9.9.9")
    assert conn is not None
    assert mgr._by_ip["9.9.9.9"] == 1
    assert conn in mgr._by_run["run-a"]
    await mgr.disconnect(conn)
    assert mgr._by_ip["9.9.9.9"] == 0
    assert conn not in mgr._by_run["run-a"]
    # Idempotent — calling again does not go negative
    await mgr.disconnect(conn)
    assert mgr._by_ip["9.9.9.9"] == 0


@pytest.mark.asyncio
async def test_publish_enqueues_to_all_connections_for_run() -> None:
    mgr = ConnectionManager()
    ws_a = MagicMock(); ws_a.accept = AsyncMock(); ws_a.close = AsyncMock()
    ws_b = MagicMock(); ws_b.accept = AsyncMock(); ws_b.close = AsyncMock()
    ws_other = MagicMock(); ws_other.accept = AsyncMock(); ws_other.close = AsyncMock()
    ca = await mgr.connect(ws_a, "run-1", -1, "10.0.0.1")
    cb = await mgr.connect(ws_b, "run-1", -1, "10.0.0.2")
    co = await mgr.connect(ws_other, "run-2", -1, "10.0.0.3")
    assert ca and cb and co

    event = {"event_type": "tick", "lane": "a", "task_id": "t1", "t_ms": 0}
    await mgr.publish("run-1", event)
    assert ca.queue.qsize() == 1
    assert cb.queue.qsize() == 1
    assert co.queue.qsize() == 0  # different run


@pytest.mark.asyncio
async def test_publish_no_subscribers_is_noop() -> None:
    mgr = ConnectionManager()
    # Should not raise
    await mgr.publish("nonexistent-run", {"event_type": "tick"})
