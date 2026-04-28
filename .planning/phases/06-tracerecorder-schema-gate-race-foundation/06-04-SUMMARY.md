---
phase: 06-tracerecorder-schema-gate-race-foundation
plan: 04
subsystem: race-failure
tags: [fault-injection, iron-rule, pydantic-validator, fault-kind-enum]
requirements: [TRC-03]
dependency-graph:
  requires:
    - "src/a2a_vs_mcp/race/__init__.py (Plan 06-01)"
    - "src/a2a_vs_mcp/race/schemas.py:FaultInjectedEvent (Plan 06-01)"
    - "src/a2a_vs_mcp/trace.py:TraceRecorder.record (Plan 06-03)"
  provides:
    - "FaultKind(str, Enum) — 5 D-12 values"
    - "FailureScriptEntry dataclass"
    - "inject_fault() IRON-RULE helper (records BEFORE mutating)"
    - "validate_failure_script() pydantic loader (rejects unknown kinds)"
  affects:
    - "Plan 06-08 (test_iron_rule_grep.py + test_inject_fault.py atomicity tests)"
    - "Phase 7 mock APIs — call inject_fault() at fault sites"
    - "Phase 7 task_config.yaml loaders — call validate_failure_script() after yaml.safe_load()"
tech-stack:
  added: []
  patterns:
    - "3.10-safe StrEnum analog: class FaultKind(str, Enum) instead of enum.StrEnum (RESEARCH.md Pitfall 6)"
    - "pydantic.TypeAdapter[list[FailureScriptEntry]] for declarative YAML schema validation (no hand-rolled checks)"
    - "Atomic record-then-mutate: t_inject_ms captured, recorder.record() runs BEFORE _apply_mutation()"
    - "Hard-failure faults raise from _apply_mutation so atomicity tests can prove record-before-raise"
key-files:
  created:
    - "src/a2a_vs_mcp/race/failure.py (110 lines)"
  modified: []
decisions:
  - "Used class FaultKind(str, Enum) — NOT enum.StrEnum — to keep Python 3.10 compatibility (RESEARCH.md Pitfall 6 / Open Question O-2)"
  - "Top-level eager import of TraceRecorder is fine: race/* depends on trace one-way; the circular risk only exists when trace lazy-imports race.runs (already handled in Plan 03 via __post_init__)"
  - "rate_limit_429 and partial_commit_5xx implemented as raise-style faults in _apply_mutation; soft mutations (partial_json, schema_drift, eventual_consistency_read) return original response unchanged so the contract is exercisable end-to-end without partial business logic (Phase 7 owns the soft mutation bodies)"
  - "t_inject_ms uses int(time.time() * 1000) — matches Plan 03's started_unix_ms units (POSIX ms wall-clock), NOT time.perf_counter()"
metrics:
  duration: "~10 minutes"
  completed: "2026-04-28"
  tasks: 1
  commits: 1
  files_created: 1
---

# Phase 6 Plan 4: race/failure.py — Fault Injection IRON RULE Summary

Shipped `src/a2a_vs_mcp/race/failure.py` — the canonical record-then-mutate fault helper that all Phase 7 mock APIs will route through, plus the FaultKind enum and pydantic-validated failure_script loader. D-11 IRON RULE atomicity is enforced at runtime; D-13 CI grep prerequisite (literal "IRON RULE" string in module docstring) is satisfied; D-12 enum-rejection test is exercisable.

## What Was Built

A 110-line single-file module containing exactly four public symbols and one private dispatcher:

- **`FaultKind(str, Enum)`** — 3.10-safe StrEnum analog. The 5 D-12 values are present in exact order:
  `RATE_LIMIT_429="rate_limit_429"`, `PARTIAL_JSON="partial_json"`, `SCHEMA_DRIFT="schema_drift"`,
  `EVENTUAL_CONSISTENCY_READ="eventual_consistency_read"`, `PARTIAL_COMMIT_5XX="partial_commit_5xx"`.
  String-to-enum lookup works (`FaultKind("rate_limit_429") is FaultKind.RATE_LIMIT_429`).
- **`FailureScriptEntry`** — `@dataclass` with `kind: FaultKind`, `target: str`, `after_calls: int = 0`, `duration_calls: int = 1`, `extra: dict[str, Any] = field(default_factory=dict)`. Has `to_dict()` matching `schemas.py:30` idiom.
- **`inject_fault(recorder, *, fault_id, kind, target, original_response)`** — IRON RULE atomicity: captures `t_inject_ms = int(time.time() * 1000)` then calls `recorder.record("fault_injected", fault_id=..., fault_kind=kind.value, target=..., t_inject_ms=...)` BEFORE `_apply_mutation()`. All 4 TRC-03 fields stamped. On raise paths (RATE_LIMIT_429 / PARTIAL_COMMIT_5XX), the event is still on the recorder.
- **`_apply_mutation(kind, response)`** — private dispatcher. Raises `RuntimeError("HTTP 429 …")` and `RuntimeError("HTTP 503 …")` for the two hard-failure kinds; returns `response` unchanged for the three soft kinds (Phase 7's mock APIs flesh those out).
- **`validate_failure_script(yaml_data)`** — uses `pydantic.TypeAdapter[list[FailureScriptEntry]]` to validate after `yaml.safe_load()`. Rejects unknown FaultKind strings with `ValidationError` at startup per D-12.

## Verification

All Plan 06-04 acceptance criteria checked:

| Check | Result |
| ----- | ------ |
| Module docstring contains literal `IRON RULE` (D-13 CI grep prerequisite) | PASS |
| `class FaultKind(str, Enum)` (3.10-safe form, NOT StrEnum) | PASS |
| All 5 enum string values present (`rate_limit_429`, `partial_json`, `schema_drift`, `eventual_consistency_read`, `partial_commit_5xx`) | PASS |
| `class FailureScriptEntry`, `def inject_fault`, `def validate_failure_script` declared | PASS |
| `TypeAdapter` used for YAML validation | PASS |
| `recorder.record("fault_injected"` (multiline-formatted call) present | PASS |
| Source-order: `recorder.record` (line 75) precedes `_apply_mutation` call (line 83) | PASS |
| Smoke test: `inject_fault(recorder, kind=PARTIAL_JSON, …)` → recorder.events[-1] has `event_type=fault_injected`, `fault_kind=partial_json`, `fault_id=f1`, `target=github.repos`, `t_inject_ms` present | PASS |
| Atomicity on raise: `inject_fault(kind=RATE_LIMIT_429)` raises `RuntimeError("HTTP 429 …")` AFTER recording event | PASS |
| Pydantic accepts `[{"kind":"rate_limit_429","target":"github.repos","after_calls":2}]` | PASS |
| Pydantic rejects `[{"kind":"WAT_NO","target":"x"}]` with `ValidationError` | PASS |

Full backend pytest suite: **100 passed, 4 subtests passed in 11.03s** — zero regressions across all of `tests/test_api_async.py`, `tests/test_demo_modes.py`, `tests/test_race_schemas.py`, `tests/test_race_turn.py`, `tests/test_web_ui.py`.

## Commits

| Task | Description                                                       | Commit  |
| ---- | ----------------------------------------------------------------- | ------- |
| 1    | feat(06-04): add race/failure.py with FaultKind + IRON-RULE helper | c04653b |

## Deviations from Plan

None. Plan executed exactly as written.

Note on plan's awk acceptance check: The acceptance criterion `awk '/def inject_fault/,/^def /' …` for source-order verification is buggy — the awk range `/def inject_fault/,/^def /` matches only the first `def inject_fault(` line because `def ` itself triggers the closing condition immediately. The underlying invariant (record-before-mutate source order) WAS verified directly: `recorder.record` lives at line 75 and the `_apply_mutation` call at line 83 (definition at line 86). Order holds. This is a plan-quality observation, not a deviation in the implementation.

## Wave Coordination Notes

- This plan completes Wave 2 alongside Plan 06-05 (race/runs.py — RunWriter). Wave 2 is now eligible to merge.
- Plan 06-08 (Wave 4 tests) can now exercise the full race-mode path: instantiate `TraceRecorder(run_id=…, lane=…)`, call `inject_fault(...)`, and assert (a) the on-disk ndjson contains the fault_injected line with all 4 TRC-03 fields, and (b) the test_iron_rule_grep.py CI scan passes against `src/a2a_vs_mcp/race/`.
- `FaultObservedEvent` schema (Plan 06-01) is intentionally untouched in this plan — Phase 7's recovery state machine owns runtime emission per D-14.

## Threat Flags

None. The threat surface introduced (failure_script YAML at startup, `target` dotted strings, `original_response` arbitrary value) is fully covered by the plan's `<threat_model>` section. No new endpoints, no filesystem paths derived from `target`, no untrusted serialization.

## Self-Check: PASSED

- Created file present: `/Users/shivanshchoudhary/Downloads/Projects/A2AvsMCP/src/a2a_vs_mcp/race/failure.py` — FOUND.
- Commit `c04653b` — FOUND in `git log`.
- Full pytest suite: 100/100 PASSED (11.03s).
