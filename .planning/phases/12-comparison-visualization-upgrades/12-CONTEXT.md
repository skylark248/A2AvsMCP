# Phase 12: Comparison Visualization Upgrades - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Two visualization upgrades on existing trace surfaces:

1. **VIZ-01 — Annotated diff** between two protocol traces, reachable from `CompareTracesPanel` header. Aligns matching events line-by-line, highlights divergence (added/removed/matched-divergent).
2. **VIZ-02 — Interactive sequence diagram** for a single trace, reachable from `TraceExplorer`. Vertical lifelines per actor, horizontal arrows per message, click-to-pin, honors `prefers-reduced-motion`.

In scope: new diff view + new sequence-diagram view, both mounted as in-place toggles on existing surfaces.
Out of scope: changes to `RacePage`, new routes, new event types, schema changes, new dependencies.

</domain>

<decisions>
## Implementation Decisions

### VIZ-01 — Diff Alignment & Layout
- **D-74:** Alignment strategy = **turn_index + event_type**. Two events match iff `a.turn_index === b.turn_index && a.event_type === b.event_type`. Unmatched on either side = added/removed. Matched events compared field-by-field for "matched-divergent" status (e.g., one has `fault_observed`, the other doesn't).
- **D-75:** Diff entry point = **toggle on `CompareTracesPanel` header** (`Side-by-side | Annotated diff`). Switches the dual-column TraceExplorer in place — same panel, same mount, no new route.
- **D-76:** Diff scope = **all event_types**. No pre-filter. Diff renders every event including `tool_discovery`, `a2a_remote_discovery`, `agent_msg`, `fault_*`, `llm_*`, `tool_call`. Discovery divergence is a feature, not a bug to hide.
- **D-77:** Divergence visual = **background tint + gutter chip**:
  - Added rows: subtle `success.main` tint + `+` chip in gutter
  - Removed rows: subtle `error.main` tint + `−` chip in gutter
  - Matched-divergent rows: `warning.main` left-border (use `failureTagColor` from `eventColors.ts` when divergence is fault-related)
  - Matched-equal rows: no decoration
- **D-78:** Role-first labels apply to row headers (carrying Phase 8 convention forward — see Phase 13 scope).

### VIZ-02 — Sequence Diagram
- **D-79:** Rendering = **pure SVG, hand-rolled** (no new dep). Vertical lifelines + horizontal arrows in one SVG element. Full control over click-to-pin, reduced-motion, role-first labels. Estimated component size: ~200–400 LOC.
- **D-80:** Lifeline model = **5 fixed roles** — `User`, `Orchestrator`, `LLM`, `Tool`, `Remote Agent`. Every event maps to one lane via existing `traceEventActor()` helper in `frontend/src/lib/trace/utils.ts`. Tool/agent name shown on the arrow label, not as a separate lane.
- **D-81:** Mount = **toggle on `TraceExplorer` header** (`List | Sequence`). Same surface, same component. Diagram and list share filter state.
- **D-82:** Click-to-pin behavior = clicking an arrow in the diagram **persists a pinned event id**; toggling back to List view scrolls to and highlights the pinned row. One source of truth for selection across both views.
- **D-83:** `prefers-reduced-motion` = no animated arrow draw-in, no scroll easing. Static render when honored.

### Cross-cutting
- **D-84:** Both upgrades reuse existing theme tokens (`failureTagColor`, `getProtocolColor`, MUI palette). No new color tokens introduced — Phase 13 (Design System Lock) consolidates afterward.
- **D-85:** No new dependencies. `@xyflow/react` is **not** used for the sequence diagram (free-form graph model fights sequence-diagram constraints). `motion` is reused only if needed for entry/exit transitions and gated on reduced-motion.

### Claude's Discretion
- Animation timing curves and easing values when motion is permitted.
- Internal data structures for the alignment algorithm output (e.g., `DiffRow[]` shape).
- Hit-target sizing and z-order for SVG arrow click areas (must meet a11y minimums).
- Whether the diff view reuses TraceExplorer's filter chrome at the top (likely yes, but planner decides).
- Pinned-event state location (component-local `useState` vs lifted into TraceExplorer parent).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Roadmap & Requirements
- `.planning/ROADMAP.md` §"Phase 12: Comparison Visualization Upgrades" — goal + success criteria
- `.planning/REQUIREMENTS.md` — VIZ-01 and VIZ-02 acceptance bullets

### Phase 6 trace schema (alignment depends on this)
- `.planning/phases/06-tracerecorder-schema-gate-race-foundation/06-CONTEXT.md` — `turn_index`, `event_type`, `actor`, `lane`, `run_id` fields
- `frontend/src/lib/types/api.ts` — `TraceEvent`, `RunResult` TypeScript types

### Existing surfaces being upgraded
- `frontend/src/features/compare/CompareTracesPanel.tsx` — current dual-column layout + sync scroll; toggle mounts here
- `frontend/src/components/traces/TraceExplorer.tsx` — current List view; Sequence toggle mounts here
- `frontend/src/lib/trace/utils.ts` — `traceEventActor`, `traceEventProtocol`, `traceLabel`, `groupA2AEventsByTaskId` helpers (reuse, do not duplicate)
- `frontend/src/lib/trace/eventColors.ts` — `failureTagColor`, `getProtocolColor`, `eventBorderColor` (single source of truth for colors per Phase 8 contract)
- `frontend/src/lib/trace/JsonTree.tsx` — extracted in Phase 11; reuse for any expandable detail rendering

### Prior phase decisions that constrain Phase 12
- `.planning/phases/08-race-page-ui-visual-contract/08-CONTEXT.md` — `prefers-reduced-motion` contract, `failureTagColor` as single source
- `.planning/phases/11-tool-discovery-scenario/11-CONTEXT.md` — D-72 (single panel above dual column), D-73 (scenario-gated mounts) — pattern precedent for in-place toggles

### Codebase maps (relevant for planner)
- `.planning/codebase/STRUCTURE.md`, `.planning/codebase/CONVENTIONS.md`, `.planning/codebase/ARCHITECTURE.md`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `traceEventActor(event)` in `frontend/src/lib/trace/utils.ts` — already classifies events into actor categories; foundation for the 5-lane mapping in D-80.
- `eventColors.ts` exports — `failureTagColor` map (5 entries), `getProtocolColor`, `eventBorderColor`. All visual decoration must source from here.
- `JsonTree.tsx` (extracted in Phase 11, lib/trace) — for any expandable payload rendering inside diff rows or seq-diagram detail popovers.
- `TraceExplorer` filter chrome (event/actor/tool/protocol/failure dropdowns) — reusable shell that the diff view and the sequence view should sit beside.
- Sync-scroll mutex pattern in `CompareTracesPanel.tsx` (lines 27–43) — applicable if the diff view ever needs paired scroll.

### Established Patterns
- Header toggle for view switching (precedent: TraceWorkspacePage scenario-gated panels in Phase 11).
- MUI Accordion + Grid for paneled content (Phase 11 DiscoveryPhasePanel).
- `prefers-reduced-motion` is honored via `useMediaQuery('(prefers-reduced-motion: reduce)')` and CSS `@media (prefers-reduced-motion: reduce)` blocks (Phase 8 baseline).
- Vitest + Testing Library wrapped in `ThemeProvider + CssBaseline` (Phase 11 pattern).

### Integration Points
- `CompareTracesPanel.tsx` — add `viewMode` state (`'side-by-side' | 'diff'`) + header toggle. Render diff component when `viewMode === 'diff'`, dual-column TraceExplorer otherwise.
- `TraceExplorer.tsx` — add `viewMode` state (`'list' | 'sequence'`) + header toggle. Sequence diagram component receives the same `events` prop. Filter state shared.
- New component locations (planner confirms): `frontend/src/components/traces/AnnotatedDiffView.tsx` and `frontend/src/components/traces/SequenceDiagramView.tsx`.
- Pinned event id: lift into `TraceExplorer` so both List and Sequence views read/write the same value.

</code_context>

<specifics>
## Specific Ideas

- Diff "matched-divergent" status is the most novel signal — explicitly call out fault-only-on-one-side in the divergence chip, since the headline value of MCP-vs-A2A comparison is showing where one protocol notices a failure the other doesn't.
- 5-role lane choice (User / Orchestrator / LLM / Tool / Remote Agent) intentionally matches the role-first labels convention — keeps Phase 13 design-system-lock work clean.
- Click-to-pin sharing state across List ↔ Sequence views is the interaction that makes the sequence diagram feel like a navigation tool, not a separate exhibit.

</specifics>

<deferred>
## Deferred Ideas

- **TraceExplorer event filters applied to sequence diagram** — likely useful but planner can decide if it's in scope or a follow-up. Default: filters apply to both views (shared state already implies it).
- **Connector lines between matched events in side-by-side mode** — rejected as the diff layout (D-75 picked in-place toggle), but could resurface for a future "compare" enhancement.
- **Per-instance lifelines in sequence diagram** (one lane per distinct tool/agent) — rejected for v1 (D-80); revisit if 5-role aggregation hides important detail.
- **Sequence diagram on RacePage / ReportDetailPage** — out of scope; Phase 12 only touches TraceExplorer + CompareTracesPanel surfaces.
- **Diff export (copy as markdown / share URL)** — not in VIZ-01 scope; backlog candidate.

</deferred>

---

*Phase: 12-comparison-visualization-upgrades*
*Context gathered: 2026-05-01*
