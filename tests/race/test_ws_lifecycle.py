"""WS lifecycle: 5/IP cap, coalesce, reconnect from turn_index, path-traversal rejection (TRC-04)."""
from __future__ import annotations

import asyncio
import json
import unittest
from contextlib import ExitStack
from pathlib import Path

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from a2a_vs_mcp.race.runs import RUNS_DIR, _WRITERS, get_writer
from a2a_vs_mcp.race.ws import (
    COALESCE_THRESHOLD, MANAGER, NEVER_COALESCE, PER_IP_CAP,
    ConnectionManager,
)
from a2a_vs_mcp.web import app


def _cleanup_runfile(run_id: str) -> None:
    _WRITERS.pop(run_id, None)
    path = RUNS_DIR / f"{run_id}.json"
    if path.exists():
        path.unlink()


class CoalesceTests(unittest.TestCase):
    def test_below_threshold_passthrough(self) -> None:
        buf = [{"event_type": "tick", "lane": "a", "task_id": "t", "i": i} for i in range(5)]
        self.assertEqual(ConnectionManager.coalesce(buf), buf)

    def test_above_threshold_coalesces_ticks_keeping_latest(self) -> None:
        # 60 ticks all with same (lane, task_id) -> should coalesce to 1.
        buf = [{"event_type": "tick", "lane": "a", "task_id": "t", "i": i}
               for i in range(COALESCE_THRESHOLD + 10)]
        out = ConnectionManager.coalesce(buf)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0]["i"], COALESCE_THRESHOLD + 9)  # latest

    def test_never_coalesce_events_preserved(self) -> None:
        # Mix coalescable + non-coalescable; non-coalescable preserved verbatim.
        buf: list[dict] = []
        for i in range(40):
            buf.append({"event_type": "tick", "lane": "a", "task_id": "t", "i": i})
        for et in NEVER_COALESCE:
            buf.append({"event_type": et, "lane": "a", "i": -1})
        for i in range(40, 60):
            buf.append({"event_type": "tick", "lane": "a", "task_id": "t", "i": i})
        out = ConnectionManager.coalesce(buf)
        # All 7 NEVER_COALESCE events kept + 1 latest tick = 8 events.
        kept_types = [e["event_type"] for e in out]
        for et in NEVER_COALESCE:
            self.assertIn(et, kept_types)


class FivePerIpCapTests(unittest.TestCase):
    """Unit-level deterministic verification of the 5/IP cap.

    Calls MANAGER.connect directly with a MagicMock WebSocket 6 times and asserts
    the 6th invocation returns None AND closes the mock with code=4290. This is the
    same code path the route handler hits — but bypasses the FastAPI TestClient ws
    wrapper, which is fragile when holding 5+ simultaneous connections via ExitStack
    (httpx may close earlier connections between enter_context calls). Integration-
    level verification via real ws is out of Phase 6 scope; the cap is enforced
    inside MANAGER.connect, and that is what we test.
    """

    def test_sixth_connection_from_same_ip_rejected(self) -> None:
        from unittest.mock import AsyncMock, MagicMock

        async def run() -> None:
            # Drain any state from prior tests on the module-singleton MANAGER.
            MANAGER._by_run.clear()
            MANAGER._by_ip.clear()

            client_ip = "10.0.0.1"
            conns: list = []
            for i in range(PER_IP_CAP):
                ws = MagicMock()
                ws.accept = AsyncMock()
                ws.close = AsyncMock()
                conn = await MANAGER.connect(ws, run_id=f"cap-{i}",
                                             last_seen_turn_index=-1,
                                             client_ip=client_ip)
                self.assertIsNotNone(conn, f"connect {i} should succeed under cap")
                conns.append(conn)
            # 6th connection must be rejected.
            ws6 = MagicMock()
            ws6.accept = AsyncMock()
            ws6.close = AsyncMock()
            rejected = await MANAGER.connect(ws6, run_id="cap-6",
                                             last_seen_turn_index=-1,
                                             client_ip=client_ip)
            self.assertIsNone(rejected, "6th connection must be rejected")
            ws6.close.assert_awaited_once()
            # Verify close called with code=4290 per D-06.
            _, kwargs = ws6.close.call_args
            self.assertEqual(kwargs.get("code"), 4290)
            # Cleanup: disconnect the 5 valid connections so other tests start clean.
            for conn in conns:
                await MANAGER.disconnect(conn)

        asyncio.run(run())


class PathTraversalRejectionTests(unittest.TestCase):
    def test_invalid_run_id_closes_with_4400(self) -> None:
        client = TestClient(app)
        with self.assertRaises(WebSocketDisconnect):
            with client.websocket_connect(
                "/api/race/ws?run_id=..%2F..%2Fetc%2Fpasswd&last_seen_turn_index=-1"
            ) as ws:
                ws.receive_json()


class ReconnectReplayTests(unittest.TestCase):
    """Reconnect-replay test that isolates RUNS_DIR to a TemporaryDirectory.

    Pollution mitigation: writing to production data/runs/ leaks state across test
    runs and dirties the working directory on test failure. We monkeypatch
    race.runs.RUNS_DIR AND race.replay.RUNS_DIR (both modules import the symbol
    at module-load time) to a per-test TemporaryDirectory for the test class
    duration. The /api/race/ws route reads RUNS_DIR via `from .race.runs import
    RUNS_DIR`, so we also patch web.RUNS_DIR if the route imported it eagerly
    (Plan 07 Edit 1 confirms eager import). The cleanest approach: patch all
    three module references using unittest.mock.patch.
    """

    @classmethod
    def setUpClass(cls) -> None:
        import tempfile
        from unittest.mock import patch

        cls._tmpdir = tempfile.TemporaryDirectory()
        cls._tmppath = Path(cls._tmpdir.name)

        # Patch RUNS_DIR everywhere it was bound at import time.
        # replay.py takes runs_dir as a parameter (no module-level RUNS_DIR import),
        # so only patch the symbols actually bound at module load time.
        cls._patches = [
            patch("a2a_vs_mcp.race.runs.RUNS_DIR", cls._tmppath),
            patch("a2a_vs_mcp.web.RUNS_DIR", cls._tmppath),
        ]
        for pp in cls._patches:
            pp.start()

    @classmethod
    def tearDownClass(cls) -> None:
        for pp in cls._patches:
            pp.stop()
        cls._tmpdir.cleanup()

    def setUp(self) -> None:
        self.run_id = "reconnect-1"
        # Drop singleton writer entry so get_writer mints a fresh one bound to
        # the patched RUNS_DIR. Do NOT call _cleanup_runfile (which uses the
        # production RUNS_DIR module attribute pre-patch).
        _WRITERS.pop(self.run_id, None)
        stale = self._tmppath / f"{self.run_id}.json"
        if stale.exists():
            stale.unlink()
        # Pre-populate the run file via RunWriter so the route's load_run path fires.
        w = get_writer(self.run_id)
        for i in range(1, 6):  # turn_index 1..5
            w.append({
                "event_type": "tool_call", "lane": "pure_mcp",
                "run_id": self.run_id, "turn_index": i,
                "tool_name": f"t{i}", "trace_schema_version": "1.0",
            }, force_flush=True)

    def tearDown(self) -> None:
        _WRITERS.pop(self.run_id, None)
        stale = self._tmppath / f"{self.run_id}.json"
        if stale.exists():
            stale.unlink()

    def test_reconnect_skips_seen_turns(self) -> None:
        # Connect with last_seen_turn_index=2; expect events for turn_index 3,4,5 only.
        client = TestClient(app)
        with client.websocket_connect(
            f"/api/race/ws?run_id={self.run_id}&last_seen_turn_index=2"
        ) as ws:
            received: list[dict] = []
            # Read up to 3 replay events (no live publishes — heartbeat would follow at 15s).
            for _ in range(3):
                ev = ws.receive_json()
                if ev.get("event_type") == "heartbeat":
                    break
                received.append(ev)
        turns = [e["turn_index"] for e in received]
        self.assertEqual(turns, [3, 4, 5], f"got {received}")


if __name__ == "__main__":
    unittest.main()
