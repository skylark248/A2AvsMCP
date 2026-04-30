# Phase 11: Tool Discovery Scenario - Context

**Gathered:** 2026-04-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a new `tool_discovery` scenario in `DemoRepository` that exercises MCP tool discovery and A2A agent-card discovery on the same task — including stale-capability-cache and unknown-tool-fallback failure modes — plus a `DiscoveryPhasePanel.tsx` component rendering the discovery phase as a first-class section above the trace explorer with the MCP tool catalog and A2A agent cards side-by-side and timestamped.

**In scope:**
- New `tool_discovery` scenario row in `src/a2a_vs_mcp/data/seeds/scenarios.json` (TICKET-1013, net-new customer)
- Failure-mode plumbing for stale-capability-cache + unknown-tool-fallback (mechanism = researcher/planner discretion)
- `DiscoveryPhasePanel.tsx` mounted above `TraceExplorer` on TraceWorkspacePage (gated on scenario) and on CompareTracesPanel (single panel above both columns)
- Static placeholder for sibling protocol when only one protocol's run is loaded

**Out of scope (other phases / deferred):**
- Annotated diff + interactive sequence diagram (Phase 12 — VIZ-01/02)
- DESIGN.md formalization (Phase 13 — DSGN-01)
- Inline "Run on sibling protocol" button + cross-run stitching (deferred — see `<deferred>`)

</domain>

<decisions>
## Implementation Decisions

### Scenario Task Framing

- **D-67:** Scenario seeded as a **net-new ticket + net-new customer** in `src/a2a_vs_mcp/data/seeds/scenarios.json` (e.g., `TICKET-1013`). Net-new keeps failure-mode plumbing isolated from v1 scenarios. Researcher/planner fill the customer profile (segment, product owned, history) — not pinned at this layer.
- **D-68:** Task is **discovery-shaped via an unknown product/SKU in the customer query.** The query mentions a product not present in seeded `warranties`/`orders` data, so the agent must list available tools, see the capability gap, and fall back. This naturally exercises BOTH failure modes:
  - **Stale capability cache:** cached tool list returns no match for the unknown SKU
  - **Unknown-tool fallback:** agent must pivot to `search_docs` / generic lookup
- **D-69:** Difficulty `advanced`, tags `["discovery", "fallback"]`. Mirrors v1 advanced scenarios (`vip_parallel_escalation`, `device_failure_warranty_refund`). Tags drive the demo-page badge so reviewers see this scenario probes discovery semantics.

### Single-Protocol Rendering

- **D-70:** On TraceWorkspacePage (single protocol per run), `DiscoveryPhasePanel` renders **the active protocol's column populated; the sibling column dimmed with a placeholder.** Side-by-side intent preserved even when only one run is loaded.
- **D-71:** Sibling-column placeholder is **static hint text only** — copy: `"Run on {A2A|MCP} to populate"`. No interaction, no router coupling, no inline-run button. Smallest blast radius.
- **D-72:** On CompareTracesPanel, **one `DiscoveryPhasePanel` mounted above both `TraceExplorer` columns**, full-width, with the panel's own internal MCP|A2A split. NOT one panel per column. The component's internal layout already expresses the side-by-side intent; per-column duplication would render the split twice.
- **D-73:** Panel mount is **gated on `scenario === "tool_discovery"`** on TraceWorkspacePage. Other scenarios stay unchanged. No always-on shell, no event-presence trigger. Scoped strictly to the new scenario; smallest UX change outside Phase 11 surface.

### Claude's Discretion

The user explicitly skipped these gray areas — researcher and planner have flexibility:

- **Failure-mode injection mechanism** — how stale-capability-cache and unknown-tool-fallback get triggered. Open questions for research: extend the existing `tool_transport_fallback` trace event path? Introduce scenario-bound TTL on broker tool-cache? FailureConfig-style per-run toggle vs. always-on for this scenario? Does `mcp/client.py` cache the `_discovered_tools` list in a way that can be made stale?
- **Panel placement on ReportDetailPage / RacePage** — TraceWorkspacePage + CompareTracesPanel are locked. ReportDetailPage and RacePage are open; default = do not mount unless researcher finds compelling reason.
- **Collapsible default** — open vs. collapsed initial state.
- **`talking_point` copy + customer profile details** — researcher drafts; user did not pin verbatim text.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & Requirements
- `.planning/ROADMAP.md` §"Phase 11: Tool Discovery Scenario" (lines 124-132) — goal, dependencies, success criteria
- `.planning/REQUIREMENTS.md` lines 67-70 — DISC-01 + DISC-02 acceptance text
- `.planning/PROJECT.md` lines 30, 63, 69, 117 — discovery surface positioning + DemoRepository pattern note

### Seeds & DemoRepository
- `src/a2a_vs_mcp/dataset.py` lines 17-120 — `DemoRepository` class; `load_scenarios()` consumes `seeds/scenarios.json` rows with fields `scenario / ticket_id / customer_id / query / title / difficulty / tags / talking_point`
- `src/a2a_vs_mcp/data/seeds/scenarios.json` — append `TICKET-1013` row here
- `src/a2a_vs_mcp/data/seeds/customers.json` — append net-new customer here
- `src/a2a_vs_mcp/schemas.py` — `SupportTicket` Pydantic shape

### Trace Event (already emitted — reuse, do not duplicate)
- `src/a2a_vs_mcp/mcp/client.py` line 78 — MCP `tool_discovery` event payload: `server`, `tools[]`, `protocol="official_mcp_sdk"`, `transport`, `requested_transport`
- `src/a2a_vs_mcp/a2a/remote_broker.py` lines 236-243 — A2A `tool_discovery` event re-emit + `remote_agent` tag

### TraceExplorer Mount Sites
- `frontend/src/features/traces/TraceWorkspacePage.tsx` line 394 — single TraceExplorer (panel mount above, gated on scenario)
- `frontend/src/features/compare/CompareTracesPanel.tsx` lines 97, 106, 126 — dual TraceExplorer columns (single panel mount above both)
- `frontend/src/features/reports/ReportDetailPage.tsx` line 260 — third TraceExplorer (out of scope unless researcher justifies)

### Prior Discovery References (existing surface)
- `frontend/src/features/learn/LearningPage.tsx` lines 66, 90, 107 — current `tool_discovery` traceSignals docs (background context, not a mount site)
- `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` line 65 — existing renderer for `tool_discovery` event payloads inside drawer (consider reusing payload-formatting helpers)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`DemoRepository.load_scenarios()`** (`src/a2a_vs_mcp/dataset.py`) — already returns `dict[str, SupportTicket]` from seed JSON. New scenario = pure data row, no class change.
- **`tool_discovery` trace event** — emitted by both transports today. Panel reads from existing trace stream; no new event_type needed.
- **`ProtocolEnvelopeDrawer`** — already formats `tool_discovery` payloads. Extract or reuse renderer for the panel's tool-catalog / agent-card cells.
- **`TraceExplorer`** — three mount sites already styled consistently; panel can borrow surface-card chrome (Card + shadow + rounded variants) used elsewhere on these pages.

### Established Patterns
- **Scenario adds = JSON row only.** PROJECT.md line 117 confirms: "TICKET-1011 + TICKET-1012 added with no infra change" — Phase 11 follows same pattern.
- **Trace events from broker are mirrored verbatim into trace store** (`a2a/remote_broker.py:237-243`) — keep `tool_discovery` payload shape stable; downstream UI reads existing fields.
- **Failure injection precedent** — Phase 6/7 introduced `FailureConfig` + `inject_fault` for race-demo lanes. Phase 11 runs through the standard `PlatformRunner`, NOT race; researcher decides whether to reuse FailureConfig vocabulary or use a scenario-scoped switch.

### Integration Points
- **Backend:** `src/a2a_vs_mcp/data/seeds/scenarios.json` (+ `customers.json`) → `DemoRepository.load_scenarios()` → `PlatformRunner` → MCP/A2A clients (existing path; failure-mode hook = researcher discretion).
- **Frontend mount #1:** `TraceWorkspacePage.tsx` immediately before line 394 `<TraceExplorer>`, gated on `scenario === "tool_discovery"`.
- **Frontend mount #2:** `CompareTracesPanel.tsx` immediately before line 97's `{/* D-08: Two synchronized TraceExplorer columns */}` block — single panel above the dual-column grid.
- **Data feed:** Panel filters `events` array (already passed to TraceExplorer) for `event_type === "tool_discovery"`; renders MCP-server tool list + A2A `remote_agent` cards with timestamps.

</code_context>

<specifics>
## Specific Ideas

- **Side-by-side intent is the teaching moment.** D-70 + D-72 both reinforce: even when only one protocol ran, the panel shows both columns. The whole purpose of the panel is to make MCP tool catalogs and A2A agent cards comparable at a glance.
- **`tool_transport_fallback` event already exists** (`a2a/remote_broker.py:237`) — researcher should investigate whether unknown-tool-fallback can reuse this signal end-to-end rather than introducing a new event.
- **Phase 11 is NOT race.** Goes through the regular `PlatformRunner` + `DemoRepository` path. Race-demo lanes / `FailureConfig` are reference material, not a hard dependency.

</specifics>

<deferred>
## Deferred Ideas

- **Inline "Run sibling protocol" button on the placeholder** — D-71 chose static hint text instead. Revisit if user feedback shows the static placeholder feels dead. Out of Phase 11 scope.
- **Cross-run stitching** (auto-fetch sibling's most recent `tool_discovery` snapshot for the same scenario) — rejected at D-70. New endpoint + cache invalidation. Reconsider in a v2.1 polish phase if demo viewers consistently want both columns populated from one click.
- **DiscoveryPhasePanel on ReportDetailPage / RacePage** — out of scope unless researcher surfaces a compelling motivation; default = do not mount.
- **Collapsible default state UX polish** — finalize during Phase 13 design lock if not obvious during build.
- **New "expert" difficulty tier** — D-69 chose `advanced` instead. Tier addition would touch demo-page badge rendering; out of scope.

</deferred>

---

*Phase: 11-tool-discovery-scenario*
*Context gathered: 2026-04-30*
