---
phase: 06-tracerecorder-schema-gate-race-foundation
plan: 02
subsystem: race-turn-index
tags: [turn-index, dispatch-table, lane-dispatch]
requires:
  - "src/a2a_vs_mcp/race/ package marker (Plan 06-01)"
provides:
  - "src/a2a_vs_mcp/race/turn.py — TURN_DEFINING_EVENTS dict + is_turn_defining() helper"
  - "Verbatim D-16 per-lane dispatch table available for lazy import"
affects:
  - "Plan 06-03 (TraceRecorder): can now lazy-import is_turn_defining inside record() to bump _turn_index"
  - "Plan 06-08 (turn-index integration tests): exercises the dispatch table end-to-end"
tech_stack:
  added: []
  patterns:
    - "Module-level constant + helper (mirrors trace.py:19-22 _PHASE_MAP and config.py:21-49 PROFILES)"
    - ".get(lane, set()) silent fallback for unknown lanes (matches CONVENTIONS.md silent-fallback style)"
key_files:
  created:
    - src/a2a_vs_mcp/race/turn.py
    - tests/test_race_turn.py
  modified: []
decisions:
  - "Module-level constant (no ClassVar) — TURN_DEFINING_EVENTS is module data, not a dataclass field; differs from trace.py:_PHASE_MAP which lives ON the dataclass."
  - "Silent .get(lane, set()) fallback for unknown lanes — D-03/D-18 say lane=None means legacy v1 mode and TraceRecorder never calls is_turn_defining in that path; defensive fallback returns False without raising."
  - "Pure dispatch, no state — D-17 says turn_index is persisted, never recomputed on replay."
metrics:
  duration_minutes: 4
  tasks_completed: 1
  files_created: 2
  files_modified: 0
  completed_date: "2026-04-28"
---

# Phase 6 Plan 2: Race Turn-Index Dispatch Table Summary

Locked the per-lane turn-defining event rule (D-15, D-16, D-17) as a module-level dispatch table + tiny helper, ready for Plan 06-03's `TraceRecorder.record()` lazy import.

## What Shipped

- `src/a2a_vs_mcp/race/turn.py` — `TURN_DEFINING_EVENTS: dict[str, set[str]]` containing the verbatim D-16 mapping (`pure_mcp: {tool_call}`, `pure_a2a: {agent_msg}`, `hybrid: {tool_call, agent_msg}`) plus `is_turn_defining(lane, event_type) -> bool` using `.get(lane, set())` for silent unknown-lane fallback. `from __future__ import annotations` per S-1. No `ClassVar`, no state, pure dispatch.
- `tests/test_race_turn.py` — 9 unit tests covering all 8 plan `<behavior>` assertions (pure_mcp/pure_a2a/hybrid positive + negative cases, hybrid set-union, hybrid `tick`-not-counted, unknown-lane no-`KeyError`, exact set equality on `TURN_DEFINING_EVENTS["hybrid"]`) plus a full-shape lock asserting the entire dict equals D-16 verbatim.

## Tasks

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Create race/turn.py with TURN_DEFINING_EVENTS dispatch table | bb0ed21 | `src/a2a_vs_mcp/race/turn.py`, `tests/test_race_turn.py` |

## Verification — All Must-Haves Truths Satisfied

1. **`TURN_DEFINING_EVENTS` dict maps lane -> {event_types} for pure_mcp, pure_a2a, hybrid** — `python -c "from a2a_vs_mcp.race.turn import TURN_DEFINING_EVENTS; assert TURN_DEFINING_EVENTS == {'pure_mcp': {'tool_call'}, 'pure_a2a': {'agent_msg'}, 'hybrid': {'tool_call', 'agent_msg'}}"` exits 0. Test `test_dispatch_table_full_shape` locks the exact dict.
2. **`is_turn_defining(lane, event_type)` returns True iff event_type is in `TURN_DEFINING_EVENTS[lane]`** — Tests 1-7 cover the truth table including positive, negative, and unknown-lane cases. All 9 tests pass.
3. **Hybrid lane uses set-union `{tool_call, agent_msg}` — not a special-cased branch** — `test_hybrid_is_set_union_of_tool_call_and_agent_msg` and `test_hybrid_dispatch_table_exact_set` together prove this. Implementation is a single `in TURN_DEFINING_EVENTS.get(lane, set())` lookup; no `if lane == "hybrid"` branch in the source.

### Acceptance Criteria — All 8 grep checks pass

```
grep -F 'from __future__ import annotations' src/a2a_vs_mcp/race/turn.py    # OK
grep -E "^TURN_DEFINING_EVENTS" src/a2a_vs_mcp/race/turn.py                  # OK
grep -F '"pure_mcp": {"tool_call"}' src/a2a_vs_mcp/race/turn.py              # OK
grep -F '"pure_a2a": {"agent_msg"}' src/a2a_vs_mcp/race/turn.py              # OK
grep -F '"hybrid": {"tool_call", "agent_msg"}' src/a2a_vs_mcp/race/turn.py   # OK
grep -E "^def is_turn_defining" src/a2a_vs_mcp/race/turn.py                  # OK
```

Plus the plan's `python -c` smoke command exits 0 and prints `OK`.

## Test Results

`pytest tests/test_race_turn.py -q` → `9 passed in 0.01s`.

## Deviations from Plan

### Auto-added (Rule 2 — missing critical functionality)

**1. [Rule 2] Added `tests/test_race_turn.py`**
- **Found during:** Task 1.
- **Issue:** Task 1 was marked `tdd="true"` with 8 `<behavior>` test specifications, but the `<files>` block listed only `src/a2a_vs_mcp/race/turn.py`. No test file path was specified.
- **Fix:** Created `tests/test_race_turn.py` with 9 unit tests mirroring the behavior block (8 cases) plus a full-shape lock (1 extra case) for the dispatch table. Drops into the existing `tests/` tree per `.planning/codebase/TESTING.md`, following the same pattern Plan 06-01 used for `tests/test_race_schemas.py`.
- **Order:** Implementation written first (the plan supplied the EXACT file body verbatim, including the docstring, `from __future__` import, and `.get(lane, set())` fallback), then tests authored against it. Strict RED→GREEN was not followed for the same reason Plan 06-01 documented: with the plan supplying verbatim source, RED would have surfaced only an `ImportError` and provided minimal signal. All 9 tests pass on first run against the implementation.
- **Files modified:** `tests/test_race_turn.py` (new).
- **Commit:** `bb0ed21` (rolled into Task 1 feat commit).

## TDD Gate Compliance

Plan-level type is `execute` (not `tdd`); Task 1 carried `tdd="true"`. Strict RED→GREEN gate sequence was not followed for the reason above (plan supplied verbatim implementation). A single `feat(06-02): ...` commit captures both impl and tests. Same precedent as Plan 06-01. No follow-up cleanup needed; this is pure dispatch data, so refactor phase does not apply.

## Threat Flags

None. The plan's threat register accepts `T-06-02-01` (mutable module-level dict — Phase 7 hybrid extensibility need; CI grep enforces no in-race-code mutation in Plan 08) and marks `T-06-02-02` n/a (lane string is never used in path resolution). No new trust boundaries introduced; lane strings come exclusively from the internal `TraceRecorder` constructor (Plan 06-03), never from untrusted input.

## Known Stubs

None. The dispatch table is final, not a stub — D-16 is locked and the table is the single source of truth for turn-index increments across the entire race subsystem.

## Self-Check: PASSED

- File `src/a2a_vs_mcp/race/turn.py` — FOUND.
- File `tests/test_race_turn.py` — FOUND.
- Commit `bb0ed21` — FOUND in `git log`.
- All 8 acceptance-criterion grep checks exit 0.
- Plan's `python -c` verification command exits 0 and prints `OK`.
- `pytest tests/test_race_turn.py -q` → 9/9 pass.
- All 3 must-haves truths provably satisfied.
