# Research Summary
_Synthesized: 2026-04-22_

---

## What This Is

An educational demo platform that runs the same customer support ticket through four execution modes (baseline, MCP, A2A, hybrid) to make protocol differences *visible* — not described, not diagrammed, but live and traceable — for a mixed technical/non-technical audience in a live walkthrough format. The existing codebase is clean and complete; this milestone is about deepening scenarios and sharpening the presentation, not rebuilding infrastructure.

---

## Key Recommendations

**1. Lock demo day to `runtime=mock, transport=in_process` — no exceptions.**
Two critical pitfalls (C2: silent transport fallback, C3: `anyio.run()` inside FastAPI event loop) can kill the demo if HTTP/stdio transport is active. The `in_process` path is the only fully-tested, crash-safe transport. Surface transport mode as a visible badge in the UI so the presenter always knows what's running.

**2. Make protocol differences visible in the result surface, not only in the trace.**
The "same ticket, same answer" trap (Pitfall C1) is the single highest-risk failure mode. The parallel agent scenario must expose wall-clock time, round-trip count, and agent count as first-class result metrics — not buried in trace JSON. Non-technical viewers must see the difference without ever opening the trace panel.

**3. Build backend trace enrichment first; all UI components depend on it.**
Three additive fields — `step_index`, `parallel_batch_id`/`started_at`/`completed_at`, and `phase` — must be added to existing trace events before any new frontend components are built. These fields are the data contract for `ParallelAgentTimeline`, `CompareTracesPanel`, and `DiscoveryPhasePanel`. Do not start frontend work without them.

**4. Define trace view tiers before implementing new scenarios.**
Multi-step and parallel scenarios will produce 60–120+ events per mode (Pitfall C4). Without a tiered view (summary strip → protocol-level → full trace), the trace becomes a liability. Group A2A task lifecycle sub-events into collapsible rows. Set a 150-event soft render cap. This architecture decision must precede scenario coding.

**5. Add `FakeReasoningEngine` before the Real LLM visibility feature ships.**
`reasoning.py` has zero test coverage (Pitfall M3). A `FakeReasoningEngine` returning canned realistic responses enables CI coverage of the LLM path's request/response shape without an API key, and prevents a live demo failure if the OpenAI path is exercised for the first time on stage.

**6. Pin `mcp>=1.27,<2` and hold `a2a-sdk` at `==0.3.26` for this milestone.**
MCP v2 pre-alpha does not exist on PyPI yet; the `FastMCP` → `McpServer` rename is breaking. A2A 1.0.0 is a major breaking release touching the broker core — defer its migration to a dedicated phase. Bump `a2a-sdk` from `0.3.25` to `0.3.26` (safe patch) immediately.

**7. Frame protocols by role before introducing acronyms.**
Non-technical viewers anchor on names not concepts (Pitfall M4). Every UI label and talking-point card must lead with "Tool Access Protocol (MCP)" and "Agent Coordination Protocol (A2A)" on first use. The hybrid mode is the "correct answer" narrative: MCP for tool access, A2A for agent coordination — they are not competitors.

---

## Table Stakes

| Feature | Why Non-Negotiable |
|---|---|
| **Mock runtime stability pass** — all 4 modes run without crashes or API keys | Any crash destroys credibility; this is the demo's reliability floor |
| **Multi-step workflow scenario** (3+ chained tool calls / agent handoffs) | Single-hop scenario makes MCP vs A2A comparison invisible; protocol depth only becomes real with chaining |
| **Parallel agent execution scenario** — multiple A2A specialists simultaneously | The single clearest A2A advantage; without it the comparison lacks its strongest proof point |
| **Outcome metrics on result card** — elapsed time, round-trips, agents involved | Comparison differences must be visible without reading the trace (Pitfall C1) |
| **Talking-point cards per mode/scenario** — one headline, one sentence, one callout | Presenter and non-technical audience both need embedded narration cues |
| **Comparison clarity UI** — side-by-side trace columns, color-coded event families | Non-technical viewers lose the comparison entirely without visual structure |
| **Transport mode badge in run header** | Prevents silent `in_process` fallback going unnoticed (Pitfall C2) |

---

## Differentiators

| Feature | Value | Build Cost |
|---|---|---|
| **Failure mode walkthrough UI** — expose `FailureConfig` paths prominently | Error paths reveal protocol design choices most clearly; earns technical credibility | Low — infrastructure exists |
| **Annotated diff view** — after running two modes, show round-trips, agents, parallelism delta | Decision-makers need a scorecard, not a log | Medium |
| **Protocol glossary popovers** — hover on any protocol term for a one-sentence definition | Removes jargon friction without breaking flow | Low — frontend + content only |
| **Real LLM path clearly surfaced** — visual callout in trace + toggle affordance | Engineers ask "is this real AI?"; easy to add | Low — feature exists, needs callout |
| **`DiscoveryPhasePanel`** — two-column MUI Card display of MCP tool list vs A2A agent cards | Makes the registry vs. announcement distinction immediately legible | Medium |

---

## Critical Risks

**Risk 1: "Same ticket, same answer" makes the comparison invisible (Pitfall C1)**
All four modes produce correct answers. Non-technical viewers see identical results and conclude the protocols are interchangeable. Prevention: outcome metrics (time, agents, round-trips) on the result card; talking-point cards that explicitly state the mechanism difference.

**Risk 2: `anyio.run()` crashes or deadlocks inside FastAPI event loop (Pitfall C3)**
Calling `anyio.run()` from a FastAPI handler creates a nested event loop conflict. Dormant in `in_process` mode; surfaces under `http`/`stdio` transport. Prevention: lock demo profile to `in_process`; add integration test for MCP mode through full FastAPI request path.

**Risk 3: Trace volume explosion breaks the trace UI (Pitfall C4)**
Multi-step + parallel scenarios produce 60–120+ events per mode. Prevention: define trace view tiers before building new scenarios; group A2A task sub-events into collapsible rows; 150-event render cap.

**Risk 4: Transport fallback silently lying about what's running (Pitfall C2)**
`MCPClient` silently falls back to `in_process` when HTTP server fails. Prevention: visible transport badge in UI; startup health check before run begins.

**Risk 5: A2A broker timeout causes intermittent parallel scenario failures (Pitfall M5)**
`timeout_ms=1500` was tuned for sequential flow. Parallel dispatch can exhaust this budget even with mock handlers. Prevention: increase `timeout_ms` to 5000ms for mock parallel scenarios; add integration test asserting no `task_failed` events in parallel trace.

---

## Build Order

**Phase 1 — Demo Stability Foundation**
- Mock runtime stability pass: run all 4 modes × all scenarios, fix crashes
- Pin `mcp>=1.27,<2` and `a2a-sdk==0.3.26`
- Add transport mode badge to run header UI
- Add port availability check at startup
- Add `FakeReasoningEngine` stub for `reasoning.py` test coverage
- Add `pytest` + `pytest-asyncio` + `httpx` to `[dev]` extras; async integration test for MCP mode

**Phase 2 — Backend Trace Enrichment** *(all frontend components depend on this)*
- Add `step_index`, `parallel_batch_id`, `started_at`, `completed_at`, `phase` fields to trace events
- Define trace view tier architecture: summary / protocol-level / full
- Add `send_tasks_parallel()` to `A2ABroker`; tune `timeout_ms` for parallel mode
- Add mock synthetic timing offsets for swimlane visualization

**Phase 3 — New Scenarios**
- Add `multi_step_warranty_escalation` scenario + talking-point card
- Add `parallel_agents` scenario + talking-point card
- Validate trace shapes; add report display handlers for new event types
- Integration test: parallel scenario asserts no `task_failed` events under mock runtime

**Phase 4 — Comparison Clarity UI**
- Add `@xyflow/react`, `recharts`, `react-syntax-highlighter`, `motion` to `package.json`
- Define `eventColors.ts` — single source of event-type color mapping
- Build `ParallelAgentTimeline.tsx` — swimlane timeline from `parallel_batch_id` events
- Build `CompareTracesPanel.tsx` — two synchronized `TraceExplorer` instances side-by-side
- Add outcome metrics (elapsed time, round-trips, agent count) to result card
- Wire new components into `ComparePage.tsx` and `TraceWorkspacePage.tsx`

**Phase 5 — Slide-Companion Content and Polish**
- Write talking-point card content for all modes and scenarios
- Add role-first protocol labels throughout UI
- Add protocol glossary popovers for key terms
- Real LLM path: visual callout in trace + latency expectation badge
- Failure mode walkthrough: make `FailureConfig` paths selectable and visible
- Optional: `DiscoveryPhasePanel.tsx` for tool discovery scenario

---

## What NOT to Build

| Do Not Build | Why | Instead |
|---|---|---|
| WebSocket real-time trace streaming | Mock runs complete in <1s; adds reconnect complexity | Animate playback client-side from completed JSON |
| User accounts / authentication | Zero demo value | Stay session-based; artifacts in `artifacts/` |
| LLM-generated talking-point content | Non-deterministic; presenter loses confidence | Hard-code card content; keep under version control |
| A2A remote transport as demo path | Infra dependency that can fail live | Lock to `in_process` transport |
| Editable scenarios via UI | Form validation + persistence complexity disproportionate to value | Add scenarios via `DemoRepository` code entries |
| A2A SDK 1.0.0 migration (this milestone) | Breaking changes touch broker core | Defer; stay on `0.3.26` |
| MCP SDK v2 pre-alpha | No released Python alpha; `FastMCP` removal is breaking | Pin `mcp>=1.27,<2` |
| OpenTelemetry / Jaeger / Zipkin export | External infra irrelevant for self-contained demo | Native `TraceRecorder` JSON + ZIP export is sufficient |
| New API endpoints for trace visualization | Creates parallel data paths that drift | All visualization reads existing `GET /api/runs/{id}` |
