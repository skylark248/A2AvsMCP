---
phase: "02-backend-trace-enrichment"
status: passed
verified: 2026-04-23
requirements_verified:
  - TRACE-01
  - TRACE-02
  - TRACE-03
  - TRACE-04
  - TRACE-05
---

# Phase 2 Verification: Backend Trace Enrichment

## Goal Verification

**Goal:** All trace events carry the enriched fields (`step_index`, `parallel_batch_id`, timing offsets, `phase`) that downstream UI components depend on, and the broker supports parallel task dispatch.

**Result:** PASSED — all 5 success criteria met, 78 tests pass, TypeScript compiles clean.

## Must-Have Verification

### TRACE-01 — step_index on tool_call and task_submit events

| Check | Evidence | Status |
|-------|----------|--------|
| `_step_counter` field on TraceRecorder | `src/a2a_vs_mcp/trace.py:17` | ✓ |
| `step_index` injected on `tool_call` and `task_submit` only | `trace.py:25-37` | ✓ |
| Sequential starting at 1 | `test_tool_call_gets_step_index_starting_at_1` PASSED | ✓ |
| `task_submit` shares counter with `tool_call` | `test_task_submit_shares_step_counter_with_tool_call` PASSED | ✓ |
| Non-action events have no `step_index` | `test_a2a_message_has_no_step_index` PASSED | ✓ |
| `step_index?: number` in `TraceEvent` (api.ts) | `frontend/src/lib/types/api.ts` | ✓ |
| `step_index?: number \| null` in `TraceEventResponse` (api.generated.ts) | confirmed present | ✓ |

### TRACE-02 — parallel_batch_id, started_at, completed_at on parallel task events

| Check | Evidence | Status |
|-------|----------|--------|
| `send_tasks_parallel()` emits `task_submit` with `parallel_batch_id` | `broker.py:158` | ✓ |
| `_run_parallel_task()` emits `task_complete` with `completed_at` | `broker.py:174` | ✓ |
| `parallel_batch_id` is 12 hex chars | `test_send_tasks_parallel_emits_batch_fields` PASSED | ✓ |
| Both task_submit events share same batch_id | test assertion confirmed | ✓ |
| `started_at` > 0, `completed_at` >= `started_at` | test assertion confirmed | ✓ |
| Fields typed in `TraceEventResponse` | `api_schemas.py:57-61` | ✓ |

### TRACE-03 — phase field on all trace events

| Check | Evidence | Status |
|-------|----------|--------|
| `_PHASE_MAP` ClassVar maps `agent_register`, `capability_advertise` → `"discovery"` | `trace.py:19-22` | ✓ |
| All other event types default to `"execution"` | `trace.py:29` | ✓ |
| `test_trace_enrichment_phase_field_on_all_events` PASSED | 41 events checked | ✓ |
| `phase?: "discovery" \| "execution"` typed in `TraceEvent` | `api.ts` | ✓ |
| Smoke test output: `agent_register \| discovery \| -`, `tool_call \| execution \| 1` | confirmed | ✓ |

### TRACE-04 — send_tasks_parallel() + timeout_ms=5000

| Check | Evidence | Status |
|-------|----------|--------|
| `A2ABroker.__init__` default `timeout_ms=5000` | `broker.py:27` | ✓ |
| `send_tasks_parallel()` method exists | `broker.py:144` | ✓ |
| `_run_parallel_task()` worker exists | `broker.py` | ✓ |
| `test_send_tasks_parallel_emits_batch_fields` asserts `timeout_ms == 5000` | PASSED | ✓ |
| Dispatches concurrently via `ThreadPoolExecutor` | `broker.py` | ✓ |

### TRACE-05 — Three-tier accordion TraceExplorer

| Check | Evidence | Status |
|-------|----------|--------|
| Summary strip always visible (total, tool calls, A2A messages, discovery/execution split) | `TraceExplorer.tsx:157-170` | ✓ |
| Protocol tier Accordion `defaultExpanded={false}` | `TraceExplorer.tsx:171` | ✓ |
| Full Trace tier Accordion `defaultExpanded={false}` | `TraceExplorer.tsx:186` | ✓ |
| `RENDER_CAP = 150` defined | `TraceExplorer.tsx:206` | ✓ |
| Cap banner shown when events > 150 | `ProtocolTier` and `FullTraceTier` both check `isCapped` | ✓ |
| A2A events grouped by `task_id` via `groupA2AEventsByTaskId()` | `TraceExplorer.tsx:213` | ✓ |
| Per-task Accordions collapsed by default | `defaultExpanded={false}` on task group Accordions | ✓ |
| `step_index` chip shown on relevant events | `ProtocolEventRow` conditionally renders `S{step_index}` chip | ✓ |
| `discovery` chip shown on discovery-phase events | `ProtocolEventRow` conditionally renders "discovery" chip | ✓ |
| `npx tsc --noEmit` exits 0 | confirmed — no output | ✓ |

## Test Suite Results

```
78 passed in 36.87s (full suite)
13 passed — Phase 2 specific tests (enrichment + parallel)
```

Phase 2 specific tests verified:
- `test_trace_enrichment_phase_field_on_all_events` PASSED
- `test_trace_enrichment_step_index_on_tool_calls` PASSED
- `test_send_tasks_parallel_emits_batch_fields` PASSED
- `test_tool_call_gets_step_index_starting_at_1` PASSED
- `test_second_tool_call_gets_step_index_2` PASSED
- `test_task_submit_shares_step_counter_with_tool_call` PASSED
- `test_a2a_message_has_no_step_index` PASSED
- `test_tool_call_gets_execution_phase` PASSED
- `test_agent_register_gets_discovery_phase` PASSED
- `test_capability_advertise_gets_discovery_phase` PASSED
- `test_unknown_event_type_defaults_to_execution_phase` PASSED
- `test_fresh_recorder_step_counter_starts_at_zero` PASSED
- `test_send_tasks_parallel_emits_task_submit_events` PASSED

## Requirement Traceability

| Req ID | Verified By | Status |
|--------|-------------|--------|
| TRACE-01 | trace.py enrichment + 5 unit tests + integration test | ✓ Complete |
| TRACE-02 | broker.py send_tasks_parallel + task_complete events + integration test | ✓ Complete |
| TRACE-03 | trace.py _PHASE_MAP + 3 unit tests + integration test | ✓ Complete |
| TRACE-04 | broker.py timeout_ms=5000 + send_tasks_parallel() + test assertion | ✓ Complete |
| TRACE-05 | TraceExplorer.tsx three-tier accordion + tsc clean | ✓ Complete |
