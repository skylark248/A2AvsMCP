---
plan: "02-01"
phase: "02-backend-trace-enrichment"
status: complete
completed: 2026-04-22
requirements_covered:
  - TRACE-01
  - TRACE-02
  - TRACE-03
  - TRACE-04
---

## Summary

Enriched the backend trace data model so every event carries the fields required by Phase 4 UI components. Three files modified: `trace.py`, `broker.py`, and `api_schemas.py`.

## What Was Built

### Task 1: TraceRecorder.record() enrichment (trace.py)

- Added `_step_counter: int` instance field (starts at 0, excluded from `__init__` and repr)
- Added `_PHASE_MAP: ClassVar[dict[str, str]]` mapping `agent_register` and `capability_advertise` → `"discovery"`; all other event types default to `"execution"`
- `record()` now injects `phase` on every event unconditionally
- `record()` injects `step_index` only on `tool_call` and `task_submit` events (shared counter, starts at 1)

### Task 2: A2ABroker enhancements (broker.py)

- Raised `timeout_ms` default from `1500` to `5000` (per TRACE-04)
- Added `send_tasks_parallel(messages)` — dispatches all messages concurrently via `ThreadPoolExecutor`, returns results in submission order
- Added `_run_parallel_task(message, batch_id, started_at)` worker — calls `send_task()` and emits `task_complete` event with `completed_at`
- `task_submit` events carry `parallel_batch_id` (12-char hex), `started_at` (epoch ms), and `step_index` (via TraceRecorder automatically)

### Task 3: TraceEventResponse schema extension (api_schemas.py)

- Added 5 explicit optional fields to `TraceEventResponse`: `step_index`, `phase`, `parallel_batch_id`, `started_at`, `completed_at`
- `extra="allow"` retained — fields pass through even without explicit declaration, but now documented for IDE completion

## Key Files

- `src/a2a_vs_mcp/trace.py` — `_step_counter`, `_PHASE_MAP`, enriched `record()`
- `src/a2a_vs_mcp/a2a/broker.py` — `send_tasks_parallel()`, `_run_parallel_task()`, `timeout_ms=5000`
- `src/a2a_vs_mcp/api_schemas.py` — 5 new optional fields on `TraceEventResponse`

## Verification

- Smoke test: `agent_register | discovery | -`, `tool_call | execution | 1`, `task_submit | execution | 2` ✓
- `A2ABroker().timeout_ms` prints `5000` ✓
- `TraceEventResponse` instantiates with all 5 fields ✓
- Full pytest suite: 38 passed ✓

## Self-Check: PASSED

All acceptance criteria met. No call sites were modified — enrichment is entirely within `record()`. Existing tests pass without changes.
