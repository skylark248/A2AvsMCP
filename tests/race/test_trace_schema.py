"""Trace schema field-presence + ndjson round-trip + per-lane turn_index (TRC-01, TRC-02)."""
from __future__ import annotations

import unittest
from pathlib import Path

from a2a_vs_mcp.trace import TraceRecorder
from a2a_vs_mcp.race.runs import RUNS_DIR, get_writer, _WRITERS
from a2a_vs_mcp.race.replay import load_run, events_for_lane


def _cleanup(run_id: str) -> None:
    # Drop the singleton writer + on-disk file to keep tests isolated.
    _WRITERS.pop(run_id, None)
    path = RUNS_DIR / f"{run_id}.json"
    if path.exists():
        path.unlink()


class LegacyBackwardsCompatTests(unittest.TestCase):
    def test_legacy_v1_recorder_unchanged(self) -> None:
        r = TraceRecorder(mode="mcp", runtime="mock", task_id="t")
        r.record("tool_call", tool_name="x")
        ev = r.events[0]
        self.assertEqual(ev["trace_schema_version"], "1.0")
        self.assertNotIn("lane", ev)
        self.assertNotIn("run_id", ev)
        self.assertNotIn("turn_index", ev)
        self.assertEqual(ev["tool_name"], "x")


class RaceModeFieldsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run_id = "rmt-fields"
        _cleanup(self.run_id)

    def tearDown(self) -> None:
        _cleanup(self.run_id)

    def test_race_mode_stamps_all_fields(self) -> None:
        r = TraceRecorder(mode="mcp", runtime="mock", task_id="t",
                          run_id=self.run_id, lane="pure_mcp")
        r.record("tool_call", tool_name="search", t_call_ms=42, status="ok")
        ev = r.events[0]
        for key in ("trace_schema_version", "lane", "run_id", "turn_index", "tool_name", "t_call_ms", "status"):
            self.assertIn(key, ev, f"missing {key} in {ev!r}")
        self.assertEqual(ev["lane"], "pure_mcp")
        self.assertEqual(ev["run_id"], self.run_id)
        self.assertEqual(ev["turn_index"], 1)
        self.assertEqual(ev["trace_schema_version"], "1.0")


class PerLaneTurnIndexTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run_ids = {"pure_mcp": "ti-mcp", "pure_a2a": "ti-a2a", "hybrid": "ti-hyb"}
        for rid in self.run_ids.values():
            _cleanup(rid)

    def tearDown(self) -> None:
        for rid in self.run_ids.values():
            _cleanup(rid)

    def test_per_lane_turn_index_pure_mcp(self) -> None:
        r = TraceRecorder(mode="mcp", runtime="mock", task_id="t",
                          run_id=self.run_ids["pure_mcp"], lane="pure_mcp")
        for i in range(5):
            r.record("tool_call", tool_name=f"t{i}", t_call_ms=1, status="ok")
        self.assertEqual([e["turn_index"] for e in r.events], [1, 2, 3, 4, 5])

    def test_per_lane_turn_index_pure_a2a_ignores_tool_call(self) -> None:
        r = TraceRecorder(mode="a2a", runtime="mock", task_id="t",
                          run_id=self.run_ids["pure_a2a"], lane="pure_a2a")
        for i in range(5):
            r.record("tool_call", tool_name=f"t{i}", t_call_ms=1, status="ok")
        self.assertEqual([e["turn_index"] for e in r.events], [0, 0, 0, 0, 0])

    def test_hybrid_set_union(self) -> None:
        r = TraceRecorder(mode="hybrid", runtime="mock", task_id="t",
                          run_id=self.run_ids["hybrid"], lane="hybrid")
        r.record("tool_call", tool_name="a", t_call_ms=1, status="ok")  # turn 1
        r.record("agent_msg", sender="x", recipient="y", content="z", t_ms=1)  # turn 2
        r.record("tool_call", tool_name="b", t_call_ms=1, status="ok")  # turn 3
        r.record("tick", task_id="t", t_ms=1)  # NOT turn-defining; inherits 3
        r.record("agent_msg", sender="x", recipient="y", content="z", t_ms=1)  # turn 4
        self.assertEqual([e["turn_index"] for e in r.events], [1, 2, 3, 3, 4])


class NdjsonRoundtripTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run_id = "rt-test-1"
        _cleanup(self.run_id)

    def tearDown(self) -> None:
        _cleanup(self.run_id)

    def test_ndjson_roundtrip_25_events(self) -> None:
        r = TraceRecorder(mode="mcp", runtime="mock", task_id="t",
                          run_id=self.run_id, lane="pure_mcp")
        for i in range(25):
            r.record("tool_call", tool_name=f"t{i}", t_call_ms=1, status="ok")
        # Force final flush of the buffered 5-event tail (after 1x batch of 20).
        get_writer(self.run_id).flush()
        events = load_run(self.run_id, RUNS_DIR)
        self.assertEqual(len(events), 25)
        self.assertEqual([e["turn_index"] for e in events], list(range(1, 26)))
        self.assertEqual([e["tool_name"] for e in events], [f"t{i}" for i in range(25)])


class CausalOrderQueryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.run_id = "rt-test-2"
        _cleanup(self.run_id)

    def tearDown(self) -> None:
        _cleanup(self.run_id)

    def test_query_by_run_id_lane_causal_order(self) -> None:
        r_mcp = TraceRecorder(mode="mcp", runtime="mock", task_id="t",
                              run_id=self.run_id, lane="pure_mcp")
        r_a2a = TraceRecorder(mode="a2a", runtime="mock", task_id="t",
                              run_id=self.run_id, lane="pure_a2a")
        r_mcp.record("tool_call", tool_name="m1", t_call_ms=1, status="ok")
        r_a2a.record("agent_msg", sender="x", recipient="y", content="z", t_ms=1)
        r_mcp.record("tool_call", tool_name="m2", t_call_ms=1, status="ok")
        get_writer(self.run_id).flush()
        all_events = load_run(self.run_id, RUNS_DIR)
        mcp_only = events_for_lane(all_events, "pure_mcp")
        self.assertEqual([e["tool_name"] for e in mcp_only], ["m1", "m2"])
        a2a_only = events_for_lane(all_events, "pure_a2a")
        self.assertEqual([e["sender"] for e in a2a_only], ["x"])


if __name__ == "__main__":
    unittest.main()
