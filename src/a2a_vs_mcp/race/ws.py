"""In-process websocket fan-out for /api/race/ws (D-06..D-09).

ConnectionManager owns:
  * per-(run_id, connection) asyncio.Queue (D-09 pubsub)
  * 5/IP cap (D-06) enforced inline in connect()
  * coalesce when buffer >50 (D-08), preserving NEVER_COALESCE event types
  * 15s heartbeat (RESEARCH.md A3 default)

Phase 7's harness publishes events via MANAGER.publish(run_id, event); the
web.py route handler drains conn.queue and forwards to ws.send_json.
Reconnect replay (D-07) reads from disk via race/replay.load_run, NOT from
an in-memory ring (RESEARCH.md "Anti-Patterns").
"""
from __future__ import annotations

import asyncio
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

from fastapi import WebSocket

HEARTBEAT_S: int = 15  # RESEARCH.md A3 — sensible default; safely under 60s typical idle timeout
COALESCE_THRESHOLD: int = 50  # D-08
PER_IP_CAP: int = 5  # D-06
QUEUE_MAX: int = 10000  # bounded queue per RESEARCH.md "Security Domain" — DoS mitigation

# D-08: tick events are coalesced when buffer >50. Everything else is preserved.
NEVER_COALESCE: frozenset[str] = frozenset({
    "tool_call", "agent_msg",
    "fault_injected", "fault_observed",
    "done", "error", "race_done",
})


@dataclass(eq=False)  # identity-hashable so Connection instances live in set[Connection]
class Connection:
    ws: WebSocket
    queue: asyncio.Queue[dict[str, Any]]
    run_id: str
    client_ip: str
    last_seen_turn_index: int = -1


class ConnectionManager:
    """In-process pubsub fan-out (D-09). Module singleton: MANAGER."""

    def __init__(self) -> None:
        self._by_run: dict[str, set[Connection]] = defaultdict(set)
        self._by_ip: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()  # async-only callers (the ws route handler is async)

    async def connect(
        self,
        ws: WebSocket,
        run_id: str,
        last_seen_turn_index: int,
        client_ip: str,
    ) -> Connection | None:
        """Accept the websocket and register the Connection.

        Returns None if 5/IP cap exceeded (ws closed with code 4290 first).
        """
        async with self._lock:
            if self._by_ip[client_ip] >= PER_IP_CAP:
                await ws.close(code=4290, reason="per-IP cap exceeded")
                return None
            self._by_ip[client_ip] += 1
        await ws.accept()
        conn = Connection(
            ws=ws,
            queue=asyncio.Queue(maxsize=QUEUE_MAX),
            run_id=run_id,
            client_ip=client_ip,
            last_seen_turn_index=last_seen_turn_index,
        )
        async with self._lock:
            self._by_run[run_id].add(conn)
        return conn

    async def disconnect(self, conn: Connection) -> None:
        """Remove conn from registries; safe to call multiple times."""
        async with self._lock:
            self._by_run[conn.run_id].discard(conn)
            self._by_ip[conn.client_ip] = max(0, self._by_ip[conn.client_ip] - 1)

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        """Phase 7 harness calls this. Phase 6 ships the path; tests use it directly."""
        for conn in list(self._by_run.get(run_id, ())):
            try:
                conn.queue.put_nowait(event)
            except asyncio.QueueFull:
                # If the queue is bounded-full, drop the event silently.
                # RESEARCH.md "Security Domain" — DoS mitigation: prefer drop over unbounded growth.
                pass

    @staticmethod
    def coalesce(buffer: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """When len(buffer) > COALESCE_THRESHOLD, coalesce tick events keeping
        latest per (lane, task_id). Never coalesces NEVER_COALESCE event types.

        D-08 verbatim semantics.
        """
        if len(buffer) <= COALESCE_THRESHOLD:
            return buffer
        keepers: list[dict[str, Any]] = []
        latest_tick: dict[tuple[str, str], dict[str, Any]] = {}
        for ev in buffer:
            t = ev.get("event_type")
            if t in NEVER_COALESCE:
                keepers.append(ev)
            elif t == "tick":
                latest_tick[(ev.get("lane", ""), ev.get("task_id", ""))] = ev
            else:
                # Unknown event type — keep verbatim (defensive).
                keepers.append(ev)
        return keepers + list(latest_tick.values())


MANAGER: ConnectionManager = ConnectionManager()  # module singleton; web.py imports
