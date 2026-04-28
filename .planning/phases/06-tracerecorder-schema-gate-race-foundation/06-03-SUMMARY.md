---
phase: 06-tracerecorder-schema-gate-race-foundation
plan: 03
subsystem: trace
tags: [trace, schema-version, ndjson, backwards-compat, race-foundation]
requirements: [TRC-01, TRC-02]
dependency-graph:
  requires:
    - "src/a2a_vs_mcp/race/__init__.py (Plan 06-01)"
    - "src/a2a_vs_mcp/race/turn.py:is_turn_defining (Plan 06-02)"
  provides:
    - "TraceRecorder.run_id / lane / turn_index / trace_schema_version on every event"
    - "ndjson durability hook (_writer.append) for race-mode runs"
  affects:
    - "Plan 06-04 (failure.py inject_fault) — consumes recorder.record('fault_injected', ...)"
    - "Plan 06-05 (race/runs.py get_writer) — supplies the lazy-imported RunWriter"
    - "Plan 06-06 (replay.py) — consumes the on-disk schema with trace_schema_version + turn_index"
tech-stack:
  added: []
  patterns:
    - "Lazy intra-package imports inside method bodies to avoid bootstrap cycles"
    - "Additive dataclass extension with ClassVar version stamp (RESEARCH §Pattern 1)"
key-files:
  created: []
  modified:
    - "src/a2a_vs_mcp/trace.py (+32 lines, additive)"
decisions:
  - "Annotated _writer as Any (not 'RunWriter | None') — keeps mypy happy without forward-ref or TYPE_CHECKING import churn"
  - "trace_schema_version stamped on EVERY event including legacy v1 callers — required by TRC-02 so the migrator can recognize files; additive change is harmless to v1 consumers"
  - "force_flush set is exactly {fault_injected, fault_observed, done} per D-04 — did NOT add 'error' (D-04 forbids)"
metrics:
  duration: "~10 minutes"
  completed: "2026-04-28"
  tasks: 1
  commits: 1
  files_modified: 1
---

# Phase 6 Plan 3: TraceRecorder Schema Gate Summary

Extended TraceRecorder additively with `run_id`/`lane`/`turn_index`/`trace_schema_version`/`started_unix_ms` fields and an ndjson durability hook, preserving full v1 backwards-compatibility (D-03) — legacy callers continue to work unchanged and the entire pre-existing pytest suite (100 tests) remains green.

## What Was Built

A dual-mode `TraceRecorder` that gracefully degrades:

- **Legacy mode** (`run_id=None`, `lane=None`): every event now carries `trace_schema_version="1.0"` (TRC-02) but otherwise produces the v1 event shape. No `lane`/`run_id`/`turn_index` keys leak into legacy traces. `save()` / `export_external()` / `latency_ms()` are byte-for-byte unchanged.
- **Race mode** (`run_id` and `lane` both set): every event additionally carries `lane`, `run_id`, and `turn_index`. `_turn_index` increments per `is_turn_defining(lane, event_type)` call (lazy-imported from `race.turn`). The recorder's `_writer` slot is populated by lazy-importing `race.runs.get_writer` (Plan 06-05 — Wave 2). Each `record()` call appends to the writer with `force_flush=True` on `{fault_injected, fault_observed, done}` per D-04.

## Implementation Detail

Single-task plan, single commit. All edits applied in place to `src/a2a_vs_mcp/trace.py`:

1. Added 5 fields after `_step_counter`: `run_id`, `lane`, `started_unix_ms`, `_turn_index`, `_writer`.
2. Added `trace_schema_version: ClassVar[str] = "1.0"` after `_PHASE_MAP`.
3. Added `__post_init__` that conditionally lazy-imports `get_writer` only when both `run_id` and `lane` are set.
4. Modified `record()`: lazy turn-index bump at top, `trace_schema_version` stamped unconditionally, `lane`/`turn_index`/`run_id` stamped conditionally, `_writer.append(...)` invoked at end if `_writer is not None`.

## Verification

- Plan smoke test (legacy path) passed: `legacy_ok`.
- All 13 acceptance-criterion `grep` patterns matched (run_id/lane/turn_index/started_unix_ms/__post_init__/lazy imports/schema-version stamp/force-flush set, plus `def save` / `def export_external` / `def latency_ms` confirming v1 methods untouched).
- Full backend test suite: **100 passed** in 11.00s (`tests/test_api_async.py`, `tests/test_demo_modes.py`, `tests/test_race_schemas.py`, `tests/test_race_turn.py`, `tests/test_web_ui.py`). D-03 backwards-compat invariant proven.

## Commits

| Task | Description                                                | Commit  |
| ---- | ---------------------------------------------------------- | ------- |
| 1    | Extend TraceRecorder with race fields + ndjson hook        | 83d3a5e |

## Deviations from Plan

None — plan executed exactly as written.

## Wave Coordination Notes

- The `__post_init__` lazy import of `race.runs.get_writer` will raise `ImportError` if a caller instantiates `TraceRecorder(run_id="x", lane="pure_mcp")` BEFORE Plan 06-05 lands. This is documented and EXPECTED per the plan's `must_haves.truths` and Plan 06's wave structure: legacy path (run_id=None) is unaffected; integrated race-mode tests live in Wave 4 (Plan 06-08).
- Plan 06-04 (`failure.py / inject_fault`) can now safely call `recorder.record("fault_injected", ...)` and rely on the `force_flush` semantics being honored once a writer is bound.

## Self-Check: PASSED

- Created files: none (plan modifies existing file only).
- Modified file present: `/Users/shivanshchoudhary/Downloads/Projects/A2AvsMCP/src/a2a_vs_mcp/trace.py` — FOUND.
- Commit `83d3a5e` — FOUND in `git log`.
- Full pytest suite: 100/100 PASSED.
