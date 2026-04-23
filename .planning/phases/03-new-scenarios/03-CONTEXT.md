# Phase 3: New Scenarios - Context

**Gathered:** 2026-04-23
**Status:** Ready for planning

<domain>
## Phase Boundary

Add two new runnable scenarios — multi-step workflow (SCEN-01) and parallel-agent (SCEN-02) — plus talking-point cards for all scenarios (SCEN-03). Both new scenarios must work across all four modes using `runtime=mock` and produce rich traces that make protocol depth immediately visible.

This phase does NOT build the comparison UI components (Phase 4), add glossary popovers (Phase 5), or add new specialist agent classes.

</domain>

<decisions>
## Implementation Decisions

### Multi-step Scenario (SCEN-01)
- **D-01:** Ticket theme: **device failure + warranty + refund**. A customer whose device failed mid-warranty, wants a refund OR replacement. This guarantees all 3 specialist agents are triggered: CustomerData (order + warranty lookup) → Documentation (troubleshooting steps) → PolicyBilling (refund/warranty policy).
- **D-02:** In A2A mode, TriageAgent routes to all 3 specialists sequentially (existing `resolve_with_broker()` flow). 3 `task_submit` trace events = 3 agent handoffs, satisfying SCEN-01.
- **D-03:** In MCP mode, SingleSupportAgent makes 4 sequential MCP tool calls: `get_customer_profile` → `get_order_history` → `search_docs` → `get_policy`. Explicit, traceable chain.
- **D-04:** New scenario entry in `data/seeds/scenarios.json` with appropriate `ticket_id`, `customer_id`, `query`, `scenario`, `title`, `difficulty`, and `tags` fields.

### Parallel Scenario (SCEN-02)
- **D-05:** Ticket theme: **high-priority VIP escalation requiring complete parallel investigation**. Narrative: "A2A can parallelize all departments simultaneously; MCP must call tools sequentially." Maximum visual impact — 3 overlapping swimlane bars vs 3 sequential tool calls.
- **D-06:** In A2A mode, TriageAgent **unconditionally dispatches all 3 specialists in parallel** via `send_tasks_parallel()` when it detects the parallel scenario tag (e.g., `tags` contains `"parallel_investigation"`). No intent-based branching — deterministic for demo reliability.
- **D-07:** In MCP mode, same SingleSupportAgent sequential tool call flow as always — the contrast with A2A parallel execution is the demo point.
- **D-08:** In baseline mode, SingleSupportAgent handles the ticket without MCP tools — sequential, no specialists.
- **D-09:** In hybrid mode, TriageAgent routes to MCP-backed specialists but sequentially (existing `resolve_with_broker()`) — shows MCP tools within A2A structure but without parallelism.
- **D-10:** The parallel scenario must produce zero `task_failed` events under mock runtime (SCEN-02 success criterion).

### Talking-Point Cards (SCEN-03)
- **D-11:** Card structure: `{headline: str, sentence: str, callout: str}` — exactly the 8-word headline + one sentence + one callout format from SCEN-03.
- **D-12:** Card data lives in **scenario seed JSON** (`data/seeds/scenarios.json`). Each scenario entry gets a `talking_point` object. Static, deterministic, presenter-controlled. New AND existing scenarios all get cards (PRES-01 in Phase 5 calls for this anyway — deliver it now).
- **D-13:** `SupportTicket` dataclass gains a `talking_point: dict | None = None` field. `DemoRepository.load_scenarios()` reads it from seed. `RunOutput` and `RunResultResponse` pass it through to the frontend.
- **D-14:** UI placement: **below the trace panel, per mode result card** in `RunWorkspacePage.tsx`. Always visible after a run without expanding anything.
- **D-15:** MUI component: **Paper with colored left border** — protocol color accent (blue=MCP, purple=A2A, green=hybrid, grey=baseline). Headline bold, sentence body text, callout as italic line or Chip. Consistent with existing protocol color usage in the codebase.

### New Agents
- **D-16:** No new specialist agent classes. Existing `CustomerDataAgent`, `DocumentationAgent`, `PolicyBillingAgent` (and their MCP-backed hybrid variants) cover all required steps for both new scenarios.
- **D-17:** Parallel dispatch behavior is added to `TriageAgent.resolve_with_broker()` — a tag-based branch that calls `send_tasks_parallel()` when the scenario is tagged `"parallel_investigation"`.

### Claude's Discretion
- Exact `ticket_id`, `customer_id`, `query` wording for both new scenario seed entries
- Synthetic timing offset values for parallel specialist mock execution (must be deterministic, non-random, show visible overlap in swimlane)
- Exact left-border color values (use existing protocol color tokens if defined, or introduce `eventColors.ts` early from Phase 4 scope — Claude's call)
- Whether `talking_point` in the API response is a typed `TalkingPointCard` model or a plain dict

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project requirements
- `.planning/PROJECT.md` — Core value, constraints, out-of-scope boundaries
- `.planning/REQUIREMENTS.md` — SCEN-01, SCEN-02, SCEN-03 acceptance criteria (primary spec for this phase)

### Existing code (must read before implementing)
- `src/a2a_vs_mcp/agents/triage.py` — `TriageAgent.resolve_with_broker()` — parallel dispatch branch goes here; understand existing intent-routing before modifying
- `src/a2a_vs_mcp/a2a/broker.py` — `A2ABroker.send_tasks_parallel()` — already implemented in Phase 2; wire it from TriageAgent here
- `src/a2a_vs_mcp/agents/specialists.py` — `CustomerDataAgent`, `DocumentationAgent`, `PolicyBillingAgent` — no changes needed, but read to understand what each agent returns
- `src/a2a_vs_mcp/agents/hybrid_specialists.py` — MCP-backed hybrid specialist variants — same agents, MCP tool calls instead of direct repo access
- `src/a2a_vs_mcp/dataset.py` — `DemoRepository.load_scenarios()` — extend to read `talking_point` from seed JSON
- `src/a2a_vs_mcp/schemas.py` — `SupportTicket`, `RunOutput` — extend with `talking_point` field
- `src/a2a_vs_mcp/api_schemas.py` — `RunResultResponse` — extend to expose `talking_point` to frontend
- `src/a2a_vs_mcp/data/seeds/scenarios.json` — add two new scenario entries with `talking_point` objects; add `talking_point` to all existing entries
- `frontend/src/features/run-workspace/RunWorkspacePage.tsx` — add TalkingPointCard component below trace panel per result
- `frontend/src/lib/types/api.generated.ts` — extend `TraceEvent` / run result types with `talking_point`

### Prior phase context
- `.planning/phases/01-demo-stability-foundation/01-CONTEXT.md` — MUI patterns, FakeReasoningEngine, pytest shape
- `.planning/phases/02-backend-trace-enrichment/02-CONTEXT.md` — `send_tasks_parallel()` design, `parallel_batch_id` timing fields, TraceRecorder enrichment

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TriageAgent.resolve_with_broker()` — existing intent-based routing to 1-3 specialists; parallel branch is an additive tag-check before the existing flow
- `A2ABroker.send_tasks_parallel()` — implemented in Phase 2; takes `list[A2AMessage]`, returns `list[AgentResult]` in submission order
- `DemoRepository.load_scenarios()` — reads seed JSON, constructs `SupportTicket`; straightforward to add `talking_point` field
- MUI `Paper` component — already in use throughout the frontend; left-border styling via `sx={{ borderLeft: '4px solid color' }}`
- `data/seeds/scenarios.json` — 10 existing scenarios, all need `talking_point` objects added

### Established Patterns
- New scenarios are added as entries in `data/seeds/scenarios.json` — no new Python files for scenario content
- Mock runtime: `MockReasoner` returns canned responses; agents still make real data repo calls in mock mode (SQLite seed data)
- Tags array on `SupportTicket` is already in schema — `"parallel_investigation"` tag is the detection mechanism for parallel dispatch
- All 4 modes share the same ticket; mode dispatch is in `DemoPlatform.run()`

### Integration Points
- `TriageAgent.resolve_with_broker()` — detect `ticket.tags` containing `"parallel_investigation"` → call `send_tasks_parallel()` with all 3 capability messages instead of sequential `_request_specialist()` calls
- `SupportTicket.talking_point` → `RunOutput.ticket.talking_point` → `RunResultResponse` → `RunWorkspacePage.tsx` TalkingPointCard component
- Phase 4 will add `eventColors.ts` as a color token file — if TalkingPointCard needs protocol colors now, either hardcode temporarily or introduce `eventColors.ts` early (Claude's discretion)

</code_context>

<specifics>
## Specific Ideas

- **Multi-step scenario ticket query:** Something like "My SmartHome Hub failed after 6 months — it's still under warranty but I want a refund, not a replacement. Can you check my order, find the troubleshooting steps, and confirm what your return policy covers?" — forces all 3 agents.
- **Parallel scenario ticket query:** A VIP/enterprise customer with an urgent escalation where speed matters — triage immediately fans out to all specialists simultaneously rather than waiting for each in turn.
- **Talking-point card examples (for new scenarios):**
  - Multi-step: Headline "Three agents, one chained investigation" | Sentence: "MCP makes 4 sequential tool calls; A2A hands off across 3 specialists — same result, visible protocol difference." | Callout: "Watch step_index climb in the trace."
  - Parallel: Headline "Three specialists, one simultaneous dispatch" | Sentence: "A2A sends all three specialists at once; MCP calls tools one by one — the swimlane shows the difference instantly." | Callout: "Overlapping timestamps in the trace = parallel execution."

</specifics>

<deferred>
## Deferred Ideas

- Tool discovery scenario (DISC-01/02) — v2 backlog, confirmed at project init
- `EscalationAgent` specialist class — not needed; TriageAgent handles coordination
- Intent-driven parallelism detection — rejected in favor of tag-based deterministic dispatch for demo reliability
- Introducing `eventColors.ts` now (Phase 4 scope) — left to Claude's discretion during implementation

None other — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-new-scenarios*
*Context gathered: 2026-04-23*
