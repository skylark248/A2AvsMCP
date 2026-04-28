"""IRON RULE atomicity + Pydantic failure_script validator (TRC-03)."""
from __future__ import annotations

import unittest

from pydantic import ValidationError

from a2a_vs_mcp.trace import TraceRecorder
from a2a_vs_mcp.race.failure import FaultKind, inject_fault, validate_failure_script
from a2a_vs_mcp.race.schemas import FaultInjectedEvent, FaultObservedEvent


def _make_recorder(run_id: str = "if-test", lane: str = "pure_mcp") -> TraceRecorder:
    # Use a recorder that does NOT bind to a writer (run_id=None) so the test
    # doesn't touch disk and we don't fight singleton state. The IRON RULE
    # invariant is per-recorder; on-disk durability is covered by Plan 08 Task 2.
    return TraceRecorder(mode="mock", runtime="mock", task_id="t")


class IronRuleAtomicityTests(unittest.TestCase):
    def test_record_runs_before_mutation(self) -> None:
        r = _make_recorder()
        inject_fault(
            r, fault_id="f1", kind=FaultKind.PARTIAL_JSON,
            target="github.repos", original_response={"ok": 1},
        )
        ev = r.events[-1]
        self.assertEqual(ev["event_type"], "fault_injected")
        self.assertEqual(ev["fault_kind"], "partial_json")
        for k in ("fault_id", "fault_kind", "target", "t_inject_ms"):
            self.assertIn(k, ev)

    def test_record_runs_before_raise(self) -> None:
        r = _make_recorder()
        with self.assertRaises(RuntimeError):
            inject_fault(
                r, fault_id="f2", kind=FaultKind.RATE_LIMIT_429,
                target="github.repos", original_response={"ok": 1},
            )
        # Event recorded EVEN though the call raised — IRON RULE atomicity.
        self.assertEqual(r.events[-1]["event_type"], "fault_injected")
        self.assertEqual(r.events[-1]["fault_kind"], "rate_limit_429")

    def test_all_5_fault_kinds(self) -> None:
        expected = {
            FaultKind.RATE_LIMIT_429: "rate_limit_429",
            FaultKind.PARTIAL_JSON: "partial_json",
            FaultKind.SCHEMA_DRIFT: "schema_drift",
            FaultKind.EVENTUAL_CONSISTENCY_READ: "eventual_consistency_read",
            FaultKind.PARTIAL_COMMIT_5XX: "partial_commit_5xx",
        }
        for kind, value in expected.items():
            r = _make_recorder()
            try:
                inject_fault(r, fault_id="x", kind=kind, target="t", original_response={})
            except RuntimeError:
                # rate_limit_429 + partial_commit_5xx raise; that's fine.
                pass
            self.assertEqual(r.events[-1]["fault_kind"], value, f"kind {kind!r}")


class WireSchemaConstructibilityTests(unittest.TestCase):
    def test_fault_injected_event_dataclass_constructible(self) -> None:
        ev = FaultInjectedEvent(
            lane="pure_mcp", turn_index=1, fault_id="f1",
            fault_kind="rate_limit_429", target="github.repos", t_inject_ms=1,
        )
        d = ev.to_dict()
        self.assertEqual(d["event_type"], "fault_injected")
        for k in ("lane", "turn_index", "fault_id", "fault_kind", "target", "t_inject_ms"):
            self.assertIn(k, d)

    def test_fault_observed_event_dataclass_constructible(self) -> None:
        # Phase 6 schema only; Phase 7 wires emission (D-14).
        ev = FaultObservedEvent(
            lane="pure_mcp", turn_index=4, fault_id="f1",
            fault_kind="rate_limit_429", target="github.repos",
            t_observed_ms=1730000005000, evidence="429 retry-after",
            wasted_tokens_before_detection=1234,
        )
        d = ev.to_dict()
        self.assertEqual(d["event_type"], "fault_observed")
        for k in ("evidence", "wasted_tokens_before_detection", "t_observed_ms"):
            self.assertIn(k, d)


class PydanticValidatorTests(unittest.TestCase):
    def test_accepts_known_kinds(self) -> None:
        entries = validate_failure_script([{"kind": "rate_limit_429", "target": "github.repos"}])
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].kind, FaultKind.RATE_LIMIT_429)
        self.assertEqual(entries[0].target, "github.repos")

    def test_rejects_unknown_kind(self) -> None:
        with self.assertRaises(ValidationError):
            validate_failure_script([{"kind": "WAT_NO_SUCH_KIND", "target": "x"}])


if __name__ == "__main__":
    unittest.main()
