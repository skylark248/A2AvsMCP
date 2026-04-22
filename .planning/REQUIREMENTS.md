# Requirements: A2A vs MCP Demo Platform

**Defined:** 2026-04-22
**Core Value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A *visible* — not described, not diagrammed, but live and traceable.

## v1 Requirements

### Stability

- [ ] **STAB-01**: All 4 demo modes (baseline, mcp, a2a, hybrid) run without crashes using `runtime=mock, transport=in_process`
- [ ] **STAB-02**: Run header displays a visible transport mode badge so the presenter always knows what transport is active
- [ ] **STAB-03**: Dependency pins updated — `mcp>=1.27,<2` and `a2a-sdk==0.3.26` in `pyproject.toml`
- [ ] **STAB-04**: `FakeReasoningEngine` stub added so `reasoning.py` LLM path has test coverage without an API key
- [ ] **STAB-05**: Test suite migrated to `pytest` + `pytest-asyncio` + `httpx`; async FastAPI integration test covers MCP mode end-to-end

### Scenarios

- [ ] **SCEN-01**: Multi-step workflow scenario added — a ticket that requires 3+ chained tool calls (MCP) or agent handoffs (A2A), making protocol depth visible
- [ ] **SCEN-02**: Parallel agent scenario added — A2A dispatches multiple specialist agents simultaneously; trace shows overlapping execution vs MCP's sequential tool calls
- [ ] **SCEN-03**: Each new scenario ships with a talking-point card (8-word headline, one sentence, one callout) embedded in the run UI

### Trace Enrichment

- [ ] **TRACE-01**: `step_index` field added to `tool_call` and `task_submit` trace events
- [ ] **TRACE-02**: `parallel_batch_id`, `started_at`, and `completed_at` fields added to parallel task events; mock mode injects deterministic synthetic timing offsets
- [ ] **TRACE-03**: `phase` field (`"discovery"` / `"execution"`) added to all trace event types
- [ ] **TRACE-04**: `A2ABroker` gains `send_tasks_parallel()` method; `timeout_ms` raised to 5000ms for mock parallel scenarios
- [ ] **TRACE-05**: Trace view tier architecture implemented — summary strip / protocol-level / full trace (with A2A task sub-events collapsible; 150-event soft render cap)

### Comparison UI

- [ ] **UI-01**: Result card displays outcome metrics — elapsed time, round-trip count, and agent count — as first-class visible elements
- [ ] **UI-02**: `ParallelAgentTimeline` component built — swimlane timeline showing parallel A2A agent execution from `parallel_batch_id` events
- [ ] **UI-03**: `CompareTracesPanel` component built — two synchronized trace explorer instances shown side-by-side for direct mode comparison
- [ ] **UI-04**: `eventColors.ts` created as single source of truth for event-type color constants across all trace components
- [ ] **UI-05**: Frontend dependencies added — `@xyflow/react`, `recharts`, `react-syntax-highlighter`, `motion`

### Presentation Polish

- [ ] **PRES-01**: Talking-point cards added for all existing modes and new scenarios; all protocol labels use role-first phrasing ("Tool Access Protocol (MCP)", "Agent Coordination Protocol (A2A)")
- [ ] **PRES-02**: Protocol glossary popovers added — hovering any protocol term in the UI shows a one-sentence definition
- [ ] **PRES-03**: Real LLM path visually called out in trace explorer with a latency expectation badge on the LLM toggle
- [ ] **PRES-04**: `FailureConfig` failure paths made selectable and visible in the UI for a failure-mode walkthrough

## v2 Requirements

### Tool Discovery

- **DISC-01**: Tool discovery scenario added — shows MCP's dynamic tool listing (server announces capabilities) vs A2A's agent card registry (agents self-describe)
- **DISC-02**: `DiscoveryPhasePanel` component — two-column MUI Card display of MCP tool list vs A2A agent cards, rendered from `phase: "discovery"` trace events

### Advanced Visualization

- **VIZ-01**: Annotated diff view after running two modes — shows round-trips, agents, parallelism delta as a comparison scorecard
- **VIZ-02**: Interactive sequence diagram animated from trace events (protocol message flow visualization)

### SDK Migrations

- **SDK-01**: A2A SDK 1.0.0 migration (dedicated phase — major breaking release touching broker core)
- **SDK-02**: MCP SDK v2 migration (`FastMCP` → `McpServer` rename)

## Out of Scope

| Feature | Reason |
|---------|--------|
| WebSocket real-time trace streaming | Mock runs complete in <1s; adds reconnect complexity and partial-state rendering bugs with near-zero value |
| User accounts / authentication | Zero demo value for a single-presenter tool |
| Cloud / production deployment | Localhost is the delivery format |
| LLM-generated talking-point content | Non-deterministic; presenter loses confidence in what cards will say |
| A2A remote transport as demo path | Infra dependency that can fail live; local is sufficient to demonstrate the protocol |
| Editable scenarios via UI | Form validation + persistence complexity disproportionate to value |
| OpenTelemetry / Jaeger / Zipkin export | External infra irrelevant for self-contained demo; native ZIP export is sufficient |
| New API endpoints for trace visualization | All visualization should read existing `GET /api/runs/{id}` to prevent data path drift |
| Separate `MCPToolCard` / `A2AAgentCard` components | Creates asymmetry and doubles maintenance; use one `CapabilityCard` with protocol prop |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| STAB-01 | Phase 1 | Pending |
| STAB-02 | Phase 1 | Pending |
| STAB-03 | Phase 1 | Pending |
| STAB-04 | Phase 1 | Pending |
| STAB-05 | Phase 1 | Pending |
| TRACE-01 | Phase 2 | Pending |
| TRACE-02 | Phase 2 | Pending |
| TRACE-03 | Phase 2 | Pending |
| TRACE-04 | Phase 2 | Pending |
| TRACE-05 | Phase 2 | Pending |
| SCEN-01 | Phase 3 | Pending |
| SCEN-02 | Phase 3 | Pending |
| SCEN-03 | Phase 3 | Pending |
| UI-01 | Phase 4 | Pending |
| UI-02 | Phase 4 | Pending |
| UI-03 | Phase 4 | Pending |
| UI-04 | Phase 4 | Pending |
| UI-05 | Phase 4 | Pending |
| PRES-01 | Phase 5 | Pending |
| PRES-02 | Phase 5 | Pending |
| PRES-03 | Phase 5 | Pending |
| PRES-04 | Phase 5 | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-22*
*Last updated: 2026-04-22 after initial definition*
