# Phase 4: Comparison UI - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Build the comparison UI that makes protocol differences visually unmissable: outcome metrics on result cards, a swimlane timeline for parallel A2A execution, a side-by-side trace comparison panel on the Compare page, and a unified color system (`eventColors.ts`) as single source of truth. All visualization reads existing trace data (enriched in Phase 2, scenarios added in Phase 3) — no new API endpoints or backend changes.

This phase does NOT add talking-point cards for existing modes (Phase 5 PRES-01), glossary popovers (Phase 5 PRES-02), failure-mode UI (Phase 5 PRES-04), or new scenarios.

</domain>

<decisions>
## Implementation Decisions

### Outcome Metrics Card (UI-01)
- **D-01:** Metrics appear as an **inline row of MUI Chips** below the mode header inside each result card in `RunWorkspacePage.tsx`. Three chips: elapsed time, round-trip count, agent count. Minimal layout change, consistent with existing Chip usage.
- **D-02:** **Round-trip count is a single combined number** (`tool_calls + a2a_messages`). The viewer doesn't need the breakdown at the card level — the trace explorer already has that detail.
- **D-03:** Only the **core three metrics** are shown: elapsed time (`latency_ms`), round-trip count, agent count (`agents_involved.length`). No failure chip at this stage (Phase 5 handles failure-mode walkthrough).

### Swimlane Timeline (UI-02)
- **D-04:** `ParallelAgentTimeline` uses **recharts `BarChart` with horizontal bars** per agent. Each bar spans `started_at` to `completed_at`. Simple, responsive, already in the UI-05 dependency list.
- **D-05:** For modes **without parallel execution** (MCP, baseline), render **sequential non-overlapping bars** derived from `step_index` order and `timestamp_ms`. The visual contrast with A2A's overlapping bars IS the demo point.
- **D-06:** Timeline is **embedded inside each result card, above the trace explorer**. Only appears for scenarios that have parallel events (tag `parallel_investigation`) or relevant step data.

### Side-by-side Panel (UI-03)
- **D-07:** `CompareTracesPanel` lives on the **existing ComparePage only** — not embedded in RunWorkspacePage. RunWorkspacePage shows individual result cards with metrics + swimlane; ComparePage shows the synchronized side-by-side trace diff. Separation of concerns.
- **D-08:** Panel shows **two modes at a time**. User picks Mode A and Mode B from selectors. Two synchronized `TraceExplorer` columns. The typical demo compares MCP vs A2A.
- **D-09:** **Synchronized scrolling** between the two trace columns. When one column scrolls, the other follows. Implemented via shared scroll ref.

### Color System (UI-04)
- **D-10:** `eventColors.ts` exports **both protocol colors AND event tone colors**. Single source of truth replacing all hardcoded color values in `ComparePage.tsx`, `RunWorkspacePage.tsx`, and `TraceExplorer.tsx`.
- **D-11:** **Canonical protocol palette** is the MUI-based values from `RunWorkspacePage.tsx`: mcp=#1976d2 (blue), a2a=#7b1fa2 (purple), hybrid=#2e7d32 (green), baseline=#757575 (grey). `ComparePage.tsx`'s darker MODE_META colors are replaced.
- **D-12:** File lives at **`frontend/src/lib/trace/eventColors.ts`** — co-located with `utils.ts` in the trace utilities directory.

### Claude's Discretion
- Exact recharts `BarChart` configuration (bar height, axis labels, responsive breakpoints)
- Whether to extract `ParallelAgentTimeline` as a separate component file or keep it inline
- Synchronized scroll implementation detail (shared ref, scroll event listener, or IntersectionObserver)
- How to derive sequential bars for non-parallel modes from `step_index` + `timestamp_ms`
- Whether `eventColors.ts` also exports the `eventBorderColor()` helper or keeps that in `utils.ts`
- Installation order and exact versions for UI-05 dependencies (`@xyflow/react`, `recharts`, `react-syntax-highlighter`, `motion`)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project requirements
- `.planning/PROJECT.md` -- Core value, constraints, out-of-scope boundaries
- `.planning/REQUIREMENTS.md` -- UI-01 through UI-05 acceptance criteria (primary spec for this phase)

### Existing code (must read before implementing)
- `frontend/src/features/run-workspace/RunWorkspacePage.tsx` -- Result card layout; `protocolColor` map at line 49 to be replaced by `eventColors.ts`; inline metrics chips go here
- `frontend/src/features/compare/ComparePage.tsx` -- Existing comparison page with `MODE_META` colors and `ModeColumn`; `CompareTracesPanel` replaces/enhances this
- `frontend/src/components/traces/TraceExplorer.tsx` -- Three-tier accordion trace viewer; two instances used in `CompareTracesPanel`; hardcoded colors in `ProtocolEventRow` to be replaced
- `frontend/src/lib/trace/utils.ts` -- Trace event helpers (`isA2AEvent`, `traceEventProtocol`, `traceEventTone`); `eventBorderColor()` logic may move to `eventColors.ts`
- `frontend/src/lib/types/api.ts` -- `TraceEvent` with Phase 2 enrichment fields (`step_index`, `phase`, `parallel_batch_id`, `started_at`, `completed_at`); `ComparisonMetrics` with `latency_ms`, `tool_calls`, `a2a_messages`, `agents_involved`

### Prior phase context
- `.planning/phases/01-demo-stability-foundation/01-CONTEXT.md` -- MUI Chip patterns, frontend conventions
- `.planning/phases/02-backend-trace-enrichment/02-CONTEXT.md` -- `parallel_batch_id` design, timing fields, TraceExplorer tier architecture
- `.planning/phases/03-new-scenarios/03-CONTEXT.md` -- D-14 (TalkingPointCard inline), D-15 (protocolColor hardcoded, Phase 4 subsumes)

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TraceExplorer` component -- Full three-tier accordion with filters; `CompareTracesPanel` wraps two instances
- `ComparisonMetrics` on `RunResult` -- Already computed by backend; `latency_ms`, `tool_calls`, `a2a_messages`, `agents_involved` available without new API work
- `ComparePage.tsx` `ModeColumn` + `MiniEventRow` -- Existing comparison layout; `CompareTracesPanel` replaces the mini event rows with full `TraceExplorer` instances
- MUI `Chip` component -- Used extensively for badges, stats, labels; inline metrics chips follow the same pattern
- `protocolColor` map in `RunWorkspacePage.tsx:49` -- Current protocol color source; migrates to `eventColors.ts`
- `eventBorderColor()` in `ComparePage.tsx:43` -- Current tone+protocol color logic; migrates to `eventColors.ts`

### Established Patterns
- Result cards are rendered in a `.map()` over `results` array in `RunWorkspacePage.tsx` -- metrics chips and swimlane are inserted per-card
- `ComparePage` loads data from saved reports via `fetchReportDetail()` -- `CompareTracesPanel` continues this pattern
- MUI `Grid` for responsive column layout -- used in both `RunWorkspacePage` and `ComparePage`
- Three-tier trace accordion (summary strip / protocol-level / full trace) with 150-event soft render cap

### Integration Points
- `RunWorkspacePage.tsx` result card section -- insert metrics chip row and `ParallelAgentTimeline` component
- `ComparePage.tsx` -- replace `ModeColumn` with `CompareTracesPanel` (mode selectors + two `TraceExplorer` columns)
- `frontend/src/lib/trace/eventColors.ts` -- new file; imported by `TraceExplorer.tsx`, `ComparePage.tsx`, `RunWorkspacePage.tsx`, `ProtocolEnvelopeDrawer.tsx`
- `package.json` -- add `recharts`, `@xyflow/react`, `react-syntax-highlighter`, `motion` dependencies

</code_context>

<specifics>
## Specific Ideas

- **Metrics chips**: `<Chip label="142ms" size="small" />`, `<Chip label="7 round-trips" size="small" variant="outlined" />`, `<Chip label="3 agents" size="small" variant="outlined" />` -- consistent with existing transport badge chip pattern
- **Swimlane contrast**: The parallel scenario should make the A2A advantage immediately visible -- three overlapping colored bars vs three sequential bars. The time axis should have ms labels.
- **Synchronized scroll**: When presenter scrolls one trace column, the other follows -- lets the audience see what each protocol does at each "step" simultaneously
- **Color unification**: After Phase 4, `grep -r '#1976d2\|#7b1fa2\|#c62828'` should find zero results outside of `eventColors.ts`

</specifics>

<deferred>
## Deferred Ideas

- `@xyflow/react` for interactive flow diagrams -- installed in UI-05 but not used in this phase; available for v2 VIZ-02 interactive sequence diagram
- `react-syntax-highlighter` -- installed in UI-05 but not used in this phase; available for Phase 5 or v2 features
- `motion` (framer-motion) -- installed in UI-05 but not used in this phase; available for Phase 5 presentation polish animations
- Four-column comparison (all modes simultaneously) -- deferred; two-at-a-time is sufficient for the demo point and avoids cramped layout

None beyond the above -- discussion stayed within phase scope.

</deferred>

---

*Phase: 04-comparison-ui*
*Context gathered: 2026-04-27*
