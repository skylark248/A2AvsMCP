"""8 wire event types over /api/race/ws (TRC-04)."""
from __future__ import annotations

import asyncio
import threading
import time
import unittest

from fastapi.testclient import TestClient

from a2a_vs_mcp.race.schemas import WIRE_EVENT_TYPES
from a2a_vs_mcp.race.ws import MANAGER
from a2a_vs_mcp.web import app


class WsSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_wire_event_types_locked(self) -> None:
        self.assertEqual(WIRE_EVENT_TYPES, frozenset({
            "tick", "tool_call", "agent_msg",
            "fault_injected", "fault_observed",
            "done", "error", "race_done",
        }))

    def test_handshake_accepts_run_id(self) -> None:
        with self.client.websocket_connect(
            "/api/race/ws?run_id=ws-schema-1&last_seen_turn_index=-1"
        ) as ws:
            # Publish from the same thread via run_until_complete on a fresh loop?
            # The TestClient's ws context manager runs ASGI in a thread; the
            # MANAGER.publish coroutine needs the loop the ws handler is running on.
            # Solution: schedule via asyncio.run_coroutine_threadsafe against the
            # TestClient's portal.
            def emit_one(event_type: str) -> dict:
                payload = {"event_type": event_type, "lane": "pure_mcp",
                           "turn_index": 1, "x": event_type}
                # Drive the publish from the test thread by reaching into the
                # ASGI test loop via the running event loop captured by the ws
                # handler. Simpler: directly populate the queue of the (single)
                # connection registered under this run_id.
                conns = list(MANAGER._by_run.get("ws-schema-1", ()))
                self.assertTrue(conns, "expected one connection registered")
                conns[0].queue.put_nowait(payload)
                return payload

            received: list[dict] = []
            for et in ["tick", "tool_call", "agent_msg",
                       "fault_injected", "fault_observed",
                       "done", "error", "race_done"]:
                sent = emit_one(et)
                msg = ws.receive_json()
                received.append(msg)
                self.assertEqual(msg["event_type"], et,
                                 f"sent {sent!r}, received {msg!r}")

            # Every received event has turn_index per-lane.
            for ev in received:
                self.assertIn("turn_index", ev,
                              f"missing turn_index on {ev!r} (TRC-04)")


if __name__ == "__main__":
    unittest.main()
