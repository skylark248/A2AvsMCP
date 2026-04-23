---
phase: "02-backend-trace-enrichment"
plan: "03"
subsystem: "frontend-trace-ui, backend-test-coverage"
tags: ["trace-ui", "accordion", "tdd", "pytest", "phase2"]
completed_date: "2026-04-23"
duration_minutes: 20
tasks_completed: 2
tasks_total: 2
files_created:
  - frontend/src/components/traces/TraceExplorer.tsx
files_modified:
  - tests/test_demo_modes.py
key_decisions:
  - "Tests pass immediately (GREEN at RED phase) because Plan 01 already fully implemented enrichment fields — documented as TDD gate note"
  - "handler.handle_task() used (not handle()) to match FlakyHandler pattern in existing test suite"
  - "A2AMessage constructed with message_type/payload fields (not content) per actual schema"
  - "max_retries=0 set in parallel broker test to avoid retry noise on simple handler pass-through"
dependency_graph:
  requires:
    - "02-01 (TraceRecorder enrichment — phase, step_index, parallel_batch_id, started_at, completed_at)"
    - "02-02 (groupA2AEventsByTaskId helper in utils.ts)"
  provides:
    - "TRACE-05: Three-tier accordion TraceExplorer UI"
    - "Phase 2 regression test coverage for TRACE-01/02/03/04"
  affects:
    - "Phase 3 scenarios (will produce 60-120+ events; tiers now handle the volume)"
tech_stack:
  added: []
  patterns:
    - "MUI Accordion with defaultExpanded={false} for collapsible tiers"
    - "RENDER_CAP=150 slice pattern with warning banner"
    - "useMemo phase breakdown counting from event.phase field"
    - "TDD: test commit before implementation (implementation pre-existed from Plan 01)"
requirements_completed:
  - TRACE-01
  - TRACE-02
  - TRACE-03
  - TRACE-04
  - TRACE-05
---

# Phase 2 Plan 03: Three-Tier TraceExplorer UI + Phase 2 Test Coverage Summary

**One-liner:** Three-tier MUI accordion TraceExplorer with always-visible Summary Strip, collapsible Protocol/Full Trace tiers, 150-event cap banners, and pytest coverage for all Phase 2 trace enrichment fields.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Replace TraceExplorer flat list with three-tier accordion | e4fa23b | frontend/src/components/traces/TraceExplorer.tsx |
| 2 | Add Phase 2 trace field assertions to test_demo_modes.py | 35e4aa1 | tests/test_demo_modes.py |

## What Was Built

### Task 1 — TraceExplorer Three-Tier Accordion (TRACE-05)

`frontend/src/components/traces/TraceExplorer.tsx` was created (new file, untracked before this plan) with the full three-tier architecture:

**Tier 0 — Summary Strip (always visible):**
- Total event count, tool call count, A2A message count
- Discovery / execution phase split (computed via `useMemo` from `event.phase`)

**Tier 1 — Protocol Events (collapsed by default):**
- Non-A2A events rendered as `ProtocolEventRow` with step_index chip (S1, S2...) and discovery phase chip
- A2A events grouped by task_id via `groupA2AEventsByTaskId()` with collapsible sub-accordions showing last status and event count
- 150-event RENDER_CAP with "Showing N of M events. Open Full Trace to see all." banner

**Tier 2 — Full Trace (collapsed by default):**
- Raw JSON per event via `JSON.stringify(event, null, 2)`
- 150-event RENDER_CAP with "Showing 150 of N events. The saved JSON file contains the complete trace." banner

All existing filter dropdowns (Event, Actor, Tool, Protocol, Failures) are preserved and flow `filteredEvents` to both tiers.

### Task 2 — Phase 2 Pytest Assertions (TRACE-01/02/03/04)

Three new test methods added to `DemoModeTests` class in `tests/test_demo_modes.py`:

1. **`test_trace_enrichment_phase_field_on_all_events`** — Every trace event from `mcp` mode has `phase` in `{"discovery", "execution"}` (covers TRACE-03)

2. **`test_trace_enrichment_step_index_on_tool_calls`** — `tool_call` events have sequential `step_index` starting at 1 with no gaps; non-action event types (`a2a_message`, `task_status`, `agent_reasoning`, `agent_register`) do NOT have `step_index` (covers TRACE-01)

3. **`test_send_tasks_parallel_emits_batch_fields`** — Direct broker test: two fake handlers registered, `send_tasks_parallel([msg_a, msg_b])` produces 2 `task_submit` events sharing one 12-char `parallel_batch_id`, each with `step_index` (int) and `started_at` (> 0); 2 `task_complete` events each with `completed_at >= started_at`. Also asserts `broker.timeout_ms == 5000` (covers TRACE-02, TRACE-04)

## Verification Results

**TypeScript build:** `npx tsc --noEmit` — 0 errors

**New tests:** 3 passed in 0.99s
```
PASSED tests/test_demo_modes.py::DemoModeTests::test_trace_enrichment_phase_field_on_all_events
PASSED tests/test_demo_modes.py::DemoModeTests::test_trace_enrichment_step_index_on_tool_calls
PASSED tests/test_demo_modes.py::DemoModeTests::test_send_tasks_parallel_emits_batch_fields
```

**Full test suite:** 78 passed in 37.37s — no regressions

## Deviations from Plan

### Auto-corrected API mismatches

**1. [Rule 1 - Bug] Corrected A2AMessage constructor in test**
- **Found during:** Task 2 implementation
- **Issue:** Plan's test template used `A2AMessage(task_id=..., content=...)` — actual schema requires `message_type` and `payload` fields; `content` does not exist
- **Fix:** Used `A2AMessage(message_type="task_request", ..., payload={"query": "..."})` matching actual dataclass
- **Files modified:** tests/test_demo_modes.py

**2. [Rule 1 - Bug] Corrected handler method name**
- **Found during:** Task 2 implementation
- **Issue:** Plan's test template used `handler.handle()` — actual handler protocol is `handle_task()` (per `FlakyHandler` in existing test suite)
- **Fix:** Used `handle_task(self, message)` in inline handler classes
- **Files modified:** tests/test_demo_modes.py

**3. [Rule 1 - Bug] Corrected platform.run() argument order**
- **Found during:** Task 2 implementation
- **Issue:** Plan's test template used `self.platform.run(ticket, mode="mcp")` — actual signature is `run(mode, ticket)` (mode is first positional)
- **Fix:** Used `self.platform.run("mcp", ticket)`
- **Files modified:** tests/test_demo_modes.py

## TDD Gate Compliance

The task had `tdd="true"`. The RED commit (35e4aa1) was made before any GREEN phase. However, all 3 tests passed immediately at the RED commit because Plan 01 (02-01) already fully implemented the enrichment fields (`phase`, `step_index`, `parallel_batch_id`, `started_at`, `completed_at`) in `TraceRecorder` and `A2ABroker.send_tasks_parallel()`.

This is expected behavior for a test-writing plan that follows a backend implementation plan. The tests are regression guards, not driving new implementation.

- RED gate commit: 35e4aa1 (test(02-03): add failing tests...)
- GREEN gate: tests passed immediately at RED commit — no separate implementation commit needed
- REFACTOR gate: not applicable

## Known Stubs

None. All three tiers render live data from the `events` prop. The Summary Strip computes phase counts from real `event.phase` values. No placeholder or hardcoded empty values exist.

## Threat Flags

No new security-relevant surface introduced. TraceExplorer is a read-only display component consuming the `events` prop. No network endpoints, auth paths, or schema changes at trust boundaries.

## Self-Check: PASSED

- [x] `frontend/src/components/traces/TraceExplorer.tsx` — exists (349 lines)
- [x] `tests/test_demo_modes.py` — contains all 3 new test methods
- [x] Commit e4fa23b — exists (TraceExplorer)
- [x] Commit 35e4aa1 — exists (test methods)
- [x] 78 tests pass, 0 failures
- [x] TypeScript 0 errors
