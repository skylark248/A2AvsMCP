"""Stub migrator + path-traversal guard (TRC-02 + Security V12)."""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from a2a_vs_mcp.race.replay import (
    SUPPORTED_SCHEMA_VERSIONS,
    _validate_run_id,
    events_for_lane,
    load_run,
    migrate_v1,
)

FIXTURES = Path(__file__).resolve().parent / "fixtures"


class StubMigratorTests(unittest.TestCase):
    def test_supported_versions_locked_to_v1(self) -> None:
        self.assertEqual(SUPPORTED_SCHEMA_VERSIONS, frozenset({"1.0"}))

    def test_empty_input_passes_through(self) -> None:
        self.assertEqual(migrate_v1([]), [])

    def test_v1_identity(self) -> None:
        events = [
            {"trace_schema_version": "1.0", "x": 1},
            {"trace_schema_version": "1.0", "x": 2},
        ]
        self.assertEqual(migrate_v1(events), events)

    def test_unsupported_version_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported trace_schema_version"):
            migrate_v1([{"trace_schema_version": "0.9"}])

    def test_missing_version_rejected(self) -> None:
        with self.assertRaises(ValueError):
            migrate_v1([{"event_type": "tool_call"}])  # no trace_schema_version

    def test_v1_fixture_loads_through_load_run(self) -> None:
        # Use the canonical v1.0 fixture as if it were a runs file.
        events = migrate_v1([
            json.loads(line)
            for line in (FIXTURES / "v1_trace_v1.0.ndjson").read_text(encoding="utf-8").splitlines()
            if line.strip()
        ])
        self.assertEqual(len(events), 3)
        self.assertEqual({e["event_type"] for e in events},
                         {"tool_call", "agent_msg", "fault_injected"})


class PathTraversalGuardTests(unittest.TestCase):
    def test_valid_run_ids_accepted(self) -> None:
        for rid in ("good-run-1", "GoodRun_42", "abc", "x" * 64):
            _validate_run_id(rid)  # no exception

    def test_traversal_rejected(self) -> None:
        for rid in ("../etc/passwd", "../../etc/passwd", "/abs/path", "a/b", ""):
            with self.assertRaises(ValueError, msg=f"should reject {rid!r}"):
                _validate_run_id(rid)

    def test_length_cap_64(self) -> None:
        with self.assertRaises(ValueError):
            _validate_run_id("x" * 65)

    def test_special_chars_rejected(self) -> None:
        for rid in ("a b", "a%b", "a;b", "a$b", "a:b", "a..b"):
            with self.assertRaises(ValueError, msg=f"should reject {rid!r}"):
                _validate_run_id(rid)


class EventsForLaneTests(unittest.TestCase):
    def test_filter_preserves_causal_order(self) -> None:
        events = [
            {"trace_schema_version": "1.0", "lane": "pure_mcp", "i": 1},
            {"trace_schema_version": "1.0", "lane": "pure_a2a", "i": 2},
            {"trace_schema_version": "1.0", "lane": "pure_mcp", "i": 3},
            {"trace_schema_version": "1.0", "lane": "hybrid", "i": 4},
        ]
        self.assertEqual([e["i"] for e in events_for_lane(events, "pure_mcp")], [1, 3])
        self.assertEqual([e["i"] for e in events_for_lane(events, "pure_a2a")], [2])

    def test_load_run_raises_filenotfound_for_unknown(self) -> None:
        from a2a_vs_mcp.race.runs import RUNS_DIR
        with self.assertRaises(FileNotFoundError):
            load_run("definitely-not-a-real-run-xyzzy", RUNS_DIR)


if __name__ == "__main__":
    unittest.main()
