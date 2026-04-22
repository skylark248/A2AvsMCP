# Phase 2: Backend Trace Enrichment - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Add `step_index`, `parallel_batch_id`, timing offsets, and `phase` fields to trace events so that downstream UI components (Phase 4 swimlane timeline, comparison panel) have the data they need. Add `send_tasks_parallel()` to A2ABroker. Implement the three-tier trace view in the frontend with collapsible A2A sub-events and a 150-event soft render cap.

This phase does NOT add new scenarios (Phase 3), build the comparison UI components (Phase 4), or add talking-point cards (Phase 5).

</domain>

<decisions>
## Implementation Decisions

### step_index (TRACE-01)
- **D-01:** `step_index` is a **per-run global sequence** — a single counter that increments across all `tool_call` and `task_submit` events in the entire run, regardless of which agent emits them. Event 1 is the first action across the whole run.
- **D-02:** Only `tool_call` and `task_submit` event types receive a `step_index` — exactly the TRACE-01 spec. Protocol bookkeeping events (`a2a_message`, `task_status`, `agent_register`, etc.) do not get `step_index`. This preserves the semantic distinction: `step_index` counts protocol boundary crossings, not internal lifecycle messages.
- **D-03:** The counter is maintained in `TraceRecorder`. On every `record()` call, if `event_type in {"tool_call", "task_submit"}`, increment and attach `step_index`. No changes required at call sites.

### Phase tagging (TRACE-03)
- **D-04:** `phase` field (`"discovery"` / `"execution"`) is applied automatically in `TraceRecorder.record()` using a **fixed event-type map** — a private constant in `trace.py`. Zero changes to call sites.
- **D-05:** The map:
  - `"discovery"`: `agent_register`, `capability_advertise`
  - `"execution"`: everything else (`tool_call`, `task_submit`, `task_status`, `a2a_message`, `tool_error`, `agent_reasoning`, `a2a_task_artifact`, `tool_transport_fallback`, etc.)
- **D-06:** Any `event_type` not in the map defaults to `"execution"` — safe for future event types.

### Parallel dispatch + timing (TRACE-02, TRACE-04)
- **D-07:** `A2ABroker.send_tasks_parallel(messages: list[A2AMessage]) -> list[AgentResult]` dispatches all tasks concurrently using `ThreadPoolExecutor(max_workers=len(messages))`. Returns results in submission order.
- **D-08:** `timeout_ms` default raised from 1500ms to **5000ms** in `A2ABroker.__init__()`. Existing `send_task()` uses this same default.
- **D-09:** Each parallel task event carries `parallel_batch_id` (UUID, shared across all tasks in the same batch), `started_at` (epoch ms), and `completed_at` (epoch ms).
- **D-10:** In mock mode, synthetic timing offsets are **scenario-defined deterministic deltas** — Claude's discretion on exact values (e.g., each specialist offset by a fixed amount so the swimlane shows visible overlap). Must be deterministic (no `random`) so traces are reproducible.

### Claude's Discretion
- Exact synthetic timing offset values for each specialist in mock parallel dispatch
- Whether `parallel_batch_id` is generated with `uuid4()` or a simpler incrementing token
- `conftest.py` additions for Phase 2 test fixtures

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project requirements
- `.planning/PROJECT.md` — Core value, constraints, out-of-scope boundaries
- `.planning/REQUIREMENTS.md` — TRACE-01 through TRACE-05 acceptance criteria (primary spec for this phase)

### Existing code (must read before implementing)
- `src/a2a_vs_mcp/trace.py` — `TraceRecorder.record()` — all new fields (`step_index`, `phase`) are added here
- `src/a2a_vs_mcp/a2a/broker.py` — `A2ABroker.send_task()` — `send_tasks_parallel()` is added here; `timeout_ms` default raised here
- `src/a2a_vs_mcp/mcp/client.py` — Existing `tool_call` event shape; verify `step_index` injection works for MCP tool calls
- `src/a2a_vs_mcp/platform.py` — Entry point for all 4 modes; `_safe_tool_call` wraps MCP calls; understand dispatch flow before modifying trace
- `frontend/src/features/traces/TraceWorkspacePage.tsx` — Current trace frontend; tier architecture is built here or in a child component
- `frontend/src/lib/types/api.generated.ts` — TypeScript `TraceEvent` type; must be extended with `step_index?`, `phase?`, `parallel_batch_id?`, `started_at?`, `completed_at?`

### Prior phase context
- `.planning/phases/01-demo-stability-foundation/01-CONTEXT.md` — Established patterns (MUI Chip, FakeReasoningEngine, pytest shape)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TraceRecorder.record()` in `trace.py` — all field injection goes here; already handles `index` and `timestamp_ms` per event; `step_index` and `phase` follow the same pattern
- `ThreadPoolExecutor` already imported in `broker.py` (used for `_execute_with_timeout`) — `send_tasks_parallel()` reuses it with `max_workers=len(messages)`
- `frontend/src/lib/trace/utils.ts` — `isA2AEvent`, `isTraceFailureEvent` helpers already exist; phase/tier filtering helpers can be added here

### Established Patterns
- All `TraceRecorder.record()` call sites pass `event_type` as the first positional arg, then keyword payload fields — new fields are injected centrally without touching call sites
- The existing `index` field on every event is a 1-based global counter for all events; `step_index` is a separate narrower counter for action events only
- Frontend uses MUI throughout; the accordion expansion pattern is available via MUI `Accordion` / `AccordionSummary` / `AccordionDetails`

### Integration Points
- `trace.py` `TraceRecorder` — add `_step_counter: int = 0` field and `_PHASE_MAP` constant; update `record()` to inject `step_index` and `phase`
- `a2a/broker.py` `A2ABroker` — add `send_tasks_parallel()` method; raise `timeout_ms=5000`
- `frontend/src/features/traces/TraceWorkspacePage.tsx` or a new `TraceExplorer` child — implement three-tier accordion
- `frontend/src/lib/types/api.generated.ts` `TraceEvent` — extend with optional new fields

</code_context>

<specifics>
## Specific Ideas

### Trace tier accordion structure
- **Summary strip** (always visible): total event count, `tool_call` count, A2A message count, phase breakdown (N discovery / M execution events). One compact row, scannable before expanding.
- **Protocol-level tier** (expandable): one row per meaningful event. A2A events grouped by `task_id`, **collapsed by default** — each group shows the task outcome (completed/failed) and expands to reveal the full lifecycle (register → accept → progress → result).
- **Full trace tier** (expandable): raw JSON, one object per event. All events, unfiltered.
- **150-event soft cap**: render exactly 150 events in protocol/full tiers. Show a banner: `"Showing 150 of N events. Open full trace JSON to see all."` The saved JSON file is always complete.

</specifics>

<deferred>
## Deferred Ideas

- Virtual scroll for large traces — acceptable for Phase 2's 150-event cap; revisit if scenarios in Phase 3 produce 300+ events regularly
- `phase: "discovery"` rendering in a `DiscoveryPhasePanel` — deferred to v2 backlog (DISC-02)
- Synthetic timing driven by a per-scenario config file — keeping it as hardcoded deterministic offsets for Phase 2 simplicity

None beyond the above — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-backend-trace-enrichment*
*Context gathered: 2026-04-22*
