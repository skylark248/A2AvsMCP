# Phase 11: Tool Discovery Scenario - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-30
**Phase:** 11-tool-discovery-scenario
**Areas discussed:** Scenario task framing, Single-protocol rendering
**Areas skipped (Claude/researcher discretion):** Failure-mode mechanics, DiscoveryPhasePanel placement (ReportDetailPage / RacePage / collapsible)

---

## Gray-Area Selection

| Option | Description | Selected |
|--------|-------------|----------|
| Scenario task framing | What ticket/query drives tool_discovery? Seed strategy? | ✓ |
| Failure-mode mechanics | How is stale-cache + unknown-tool-fallback triggered? | |
| DiscoveryPhasePanel placement | Above TraceExplorer where; collapsible defaults? | |
| Single-protocol rendering | TraceWorkspacePage shows one proto; how does panel render? | ✓ |

**User's choice:** Scenario task framing + Single-protocol rendering.
**Notes:** Failure-mode mechanics + panel placement deferred to research/planner.

---

## Scenario Task Framing

### Q1 — Seed strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Net-new ticket + customer | Add fresh customer + TICKET-1013; cleanest separation; failure modes don't bleed into v1 scenarios. | ✓ |
| Net-new ticket, reuse existing customer | Append TICKET-1013 to enterprise customer; less seed churn, reuses fixture data. | |
| Reuse existing scenario, add discovery hook | Pick `setup_and_warranty`, re-discover tools each turn; smallest seed change but conflates v1 + v2. | |

**User's choice:** Net-new ticket + customer.

### Q2 — What forces discovery phase

| Option | Description | Selected |
|--------|-------------|----------|
| Unknown product/SKU in query | Query mentions a SKU not in seeded data; agent lists tools, sees gap, falls back. Naturally exercises both failure modes. | ✓ |
| Multi-domain query requiring catalog scan | Crosses customer + payment + warranty + docs; discovery as planning step, not error-driven. Failure modes feel bolted-on. | |
| Explicit "what can you do?" meta query | Customer asks agent's capabilities; trivial for tool listing but failure modes hard to motivate. | |

**User's choice:** Unknown product/SKU in query.

### Q3 — Difficulty + tags

| Option | Description | Selected |
|--------|-------------|----------|
| advanced + [discovery, fallback] | Mirrors v1 advanced scenarios; tags drive demo-page badge. | ✓ |
| standard + [discovery] | Treats discovery as routine; loses signal that failure modes raise difficulty. | |
| expert + [discovery, fallback, capability_gap] | New tier above advanced; UI doesn't render today. | |

**User's choice:** advanced + [discovery, fallback].

### Q4 — Anything else / move on

| Option | Description | Selected |
|--------|-------------|----------|
| Move on | Researcher fills query text + customer details. | ✓ |
| Lock talking_point copy now | Pin exact one-line demo narration. | |
| Lock seed customer profile | Specify segment / product / prior tickets. | |

**User's choice:** Move on. Researcher drafts copy + profile.

---

## Single-Protocol Rendering

### Q1 — Single-protocol render approach

| Option | Description | Selected |
|--------|-------------|----------|
| Show selected column, dim+placeholder for sibling | Active column populated; sibling at reduced opacity with hint. Side-by-side intent preserved. | ✓ |
| Show only the active column, hide sibling | Single column expands full-width; loses side-by-side teaching moment. | |
| Auto-fetch sibling's most recent run | Backend stitches sibling's last snapshot; richer demo but new endpoint + cache invalidation. | |

**User's choice:** Show selected column, dim sibling with placeholder.

### Q2 — Placeholder behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Static hint text only | "Run on {A2A\|MCP} to populate." No interaction; no router coupling. | ✓ |
| Active link to re-run on sibling protocol | Click → navigates with protocol toggled; better UX, needs route+state plumbing. | |
| Inline "Run now" button | Triggers backend run in-place; biggest implementation surface (loading, error, lifecycle). | |

**User's choice:** Static hint text only.

### Q3 — Compare page alignment

| Option | Description | Selected |
|--------|-------------|----------|
| One panel above both columns, internal MCP\|A2A split | Single panel spans full-width; matches its own internal split intent. | ✓ |
| Two panels, one per column | Symmetric with TraceExplorer layout but redundant with the panel's internal split. | |
| Hide panel on Compare page | Compare already does diff; loses discovery-phase signal where comparison matters most. | |

**User's choice:** One panel above both columns.

### Q4 — Mount trigger on TraceWorkspacePage

| Option | Description | Selected |
|--------|-------------|----------|
| Only when scenario == tool_discovery | Scoped to new scenario; smallest blast radius outside Phase 11 surface. | ✓ |
| Whenever any tool_discovery event exists | Becomes permanent header for all traces; UX shift outside Phase 11 scope. | |
| Always mount, render empty state otherwise | Permanent shell; consistent layout but vertical-space cost on every run. | |

**User's choice:** Only when scenario == tool_discovery.

---

## Claude's Discretion

- **Failure-mode injection mechanism** — how stale-capability-cache and unknown-tool-fallback are triggered. Researcher to investigate reusing existing `tool_transport_fallback` event vs. new mechanism, scenario-bound TTL on broker tool-cache, FailureConfig-style toggle vs. always-on-for-this-scenario.
- **Panel placement on ReportDetailPage / RacePage** — out of scope unless researcher finds compelling motivation.
- **Collapsible default** — open vs. collapsed initial state.
- **`talking_point` copy text** — researcher drafts.
- **Customer profile details** — segment, product, history; researcher drafts.

## Deferred Ideas

- Inline "Run sibling protocol" button on placeholder (rejected at Q2; revisit if static hint feels dead in user testing).
- Cross-run stitching for auto-populating both columns (rejected at Q1; reconsider in v2.1 polish).
- DiscoveryPhasePanel on ReportDetailPage / RacePage.
- New "expert" difficulty tier (rejected at Scenario-Q3; tier addition would touch demo-page badge).
- Phase 13 design lock will formalize panel typography / spacing tokens.
