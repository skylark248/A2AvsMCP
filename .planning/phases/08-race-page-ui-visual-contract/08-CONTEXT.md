# Phase 8: Race Page UI & Visual Contract - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

`/race` page rendering live websocket race telemetry — three-lane scoreboard (pure_mcp / pure_a2a / hybrid), characteristic-failure banner, methodology section, hardness-vs-failure heatmap, full set of 12 page states, plus the visual / responsive / accessibility contract. Live mode reads `/api/race/ws` (Phase 6 + Phase 7); replay mode reads recorded trace at `/race/<run_id>`.

In scope:
- `frontend/src/features/race/RacePage.tsx` + child components
- `frontend/src/lib/trace/eventColors.ts` extension (failureTagColor map)
- WS client integration with Phase 7 harness event stream
- 8 new glossary terms + first-mention popover
- Responsive contract + a11y contract
- Replay route `/race/<run_id>` (data fetch + scrubber UX; replay backend lands in Phase 9 HEAT-03)

Out of scope:
- Heatmap data backend (Phase 9 HEAT-01/02)
- OG image / sharing (Phase 10)
- Discovery panel (Phase 11)
- Comparison visualization upgrades (Phase 12)
- DESIGN.md token lock (Phase 13)
</domain>

<decisions>
## Implementation Decisions

### WS State Architecture
- **D-44:** `useRaceStream(run_id?)` custom hook owns the websocket connection + a `useReducer` over the event stream. State is scoped to the `RacePage` component tree (no global store, no provider). Events are reduced into a typed `RaceState` shape carrying per-lane TaskOutcome, fault list, headline, page-state enum, and per-lane `last_turn_index` cursor.
  - **Why:** No new dep; mirrors existing react-router-only patterns in this app; reducer over typed events maps 1:1 onto the closed Phase 7 ws event union.
- **D-45:** Reconnect resume uses **per-lane** `last_turn_index` carried to backend as query params on the ws URL. Backend resumes stream from each lane's cursor (matches harness emission shape — events are already lane-tagged).
  - **Why:** Single global cursor would replay events the client already has for non-laggy lanes; per-lane resume is exact and matches the lane-segregated harness output.

### Heatmap Rendering
- **D-46:** Heatmap is **CSS Grid + DOM `<div role="gridcell">` cells**. `failureTagColor` (UIRACE-04, 5 entries) drives `backgroundColor`; cells carry icon + label per UIRACE-04 (color is never sole channel). UIRACE-03 cell radius=0 is a single `border-radius: 0` on the cell class.
  - **Why:** Native focus + keyboard nav for free; UIRACE-06 a11y contract is essentially already satisfied; SVG / canvas would each require a parallel DOM mirror for screen readers; v1 grid sizes do not need canvas-class throughput.
- **D-47:** **heatmap-empty** state preserves the full grid scaffold with neutral muted cells + centered overlay copy ("No runs yet — launch a race to populate."). The grid does **not** unmount or change dimensions.
  - **Why:** Prevents cumulative layout shift when the first cell lands; visual contract stays stable; "skeleton" was rejected because heatmap-empty is terminal, not loading.

### Replay Mode UX
- **D-48:** Replay is a **separate route `/race/<run_id>`** (not a query param, not a toggle). Live mode = `/race`. Both routes render the same `RacePage` component; the route param flips the data source from `useRaceStream` (live ws) to `useRaceReplay` (fetched trace JSON).
  - **Why:** Bookmarkable + shareable links matter for Phase 10 (OG sharing); refresh preserves state; `/race/<run_id>` is the deep-link target Phase 10 will share.
- **D-49:** Replay state shows a **right-aligned pill in the status strip** ("REPLAY · run abc123", radius=999 per UIRACE-03 pill scale, neutral grey fill) plus a **scrubber below the status strip** that lets viewers step through `turn_index`. `aria-live="polite"` announcements (UIRACE-06) are rate-limited during scrub to avoid screen-reader flooding.
  - **Why:** Status strip is the existing canonical place for session-level metadata; banner-level callout would compete with the locked characteristic-failure banner; watermark-only loses interactive replay control.

### First-Mention Popover Semantics
- **D-50:** First mention of each glossary term: dashed underline + **click → MUI Popover** with full definition + a "Got it" dismiss button. Subsequent mentions on the same page: existing `GlossaryTerm` Tooltip on hover. Both first-mention popover and subsequent tooltip read from the same `glossaryTerms` map.
  - **Why:** Hover-only Tooltip is unsafe for mobile + keyboard-only users (UIRACE-06); inline expansion disrupts reading flow. Click + Popover is focusable and a11y-safe; Tooltip thereafter avoids over-emphasis on repeated terms.
- **D-51:** First-mention is tracked in a **route-scoped React Context** (`<FirstMentionProvider>` wrapping the `/race` route). A `Set<term>` records which terms have rendered their first instance; the set is reset on route exit. **No** sessionStorage / localStorage persistence.
  - **Why:** Demo platform — every viewer should get the educational moment fresh on a new visit; localStorage would mean a repeat-viewer demo audience never sees the popover. Route-scoped context resets cleanly without hydration complexity.

### Claude's Discretion
- Page-state machine **surface** (explicit FSM enum + transition function vs derived state computed from event-tail + ws status) — researcher decides; both approaches fit D-44 reducer.
- Mobile fallback `?mode=summary` rendering approach (client-side from existing data vs backend-prerendered PNG fetched) — coordinate with Phase 10 OG image work; Phase 8 ships only the trigger condition (viewport <480) and a placeholder loader, not the rendered output itself.
- Scrubber visual design (D-49) — researcher / planner pick the MUI Slider variant; UIRACE-03 doesn't lock this.
- Specific MUI Popover anchor positioning (top-start vs auto-fit) — planner decides per term.

### Folded Todos
None — no TODOS.md items matched Phase 8 scope.
</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 8 requirements + visual contract
- `.planning/REQUIREMENTS.md` (UIRACE-01..UIRACE-07) — file paths, radii scale, breakpoint boundaries, a11y rules, failureTagColor map, glossary term list
- `.planning/ROADMAP.md` §"Phase 8: Race Page UI & Visual Contract" — phase goal + 5 success criteria

### Upstream phases (data contract)
- `.planning/phases/06-tracerecorder-schema-gate-race-foundation/06-CONTEXT.md` — TraceRecorder schema, ws event shapes
- `.planning/phases/06-tracerecorder-schema-gate-race-foundation/06-04-SUMMARY.md` — `fault_injected` / `fault_observed` event field shapes
- `.planning/phases/06-tracerecorder-schema-gate-race-foundation/06-07-SUMMARY.md` — `/api/race/ws` route + ConnectionManager lifecycle
- `.planning/phases/07-race-backend-lanes-harness-recovery/07-CONTEXT.md` — D-19..D-43 race backend decisions
- `.planning/phases/07-race-backend-lanes-harness-recovery/07-10-SUMMARY.md` — harness ws emission contract (`race_done` + per-lane events)
- `.planning/phases/07-race-backend-lanes-harness-recovery/VERIFICATION.md` — locked event union + headline templates
- `src/a2a_vs_mcp/race/classifier.py` — 6 headline templates + 5 terminal recovery tags (drives failureTagColor + glossary)

### Frontend reusable assets
- `frontend/src/lib/trace/eventColors.ts` — extend with `failureTagColor` map (5 entries per UIRACE-04)
- `frontend/src/lib/glossary/glossaryTerms.ts` — extend with 8 new race terms (UIRACE-07)
- `frontend/src/components/glossary/GlossaryTerm.tsx` — current Tooltip component; D-50 extends with click→Popover for first mention
- `frontend/src/app/routes.tsx` — add `/race` and `/race/:run_id` routes
- `frontend/package.json` — MUI 7, recharts, react-router-dom already present; no new deps required by these decisions
</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `GlossaryTerm` component (`frontend/src/components/glossary/GlossaryTerm.tsx`): Tooltip-based; extend for D-50 first-mention popover by branching on `FirstMentionProvider` context.
- `glossaryTerms` map (`frontend/src/lib/glossary/glossaryTerms.ts`): module-level Record; UIRACE-07 just adds 8 entries.
- `eventColors.ts` `protocolColor` + `toneColor` patterns: matches the "single source of truth" expectation for D-46's `failureTagColor` map.
- React Router lazy-route pattern in `frontend/src/app/routes.tsx`: matches expectation for `/race` + `/race/:run_id` lazy mounts.

### Established Patterns
- MUI 7 components: use `<Tooltip>`, `<Popover>`, `<Slider>` directly without a UI wrapper layer.
- Route-scoped lazy loading via React.lazy + Suspense: applies to RacePage as well.
- Module-level Record for static lookup data (glossary, color maps): the project preference; D-46/D-50 follow this.

### Integration Points
- WS endpoint: `/api/race/ws` (Phase 6 Plan 07).
- Replay data fetch: TBD endpoint — Phase 9 HEAT-03 ships the trace JSON read API; Phase 8 stubs the call signature.
- Trace event types: existing `frontend/src/lib/types/api.ts` `TraceEvent` type — Phase 8 extends with the Phase 6/7 ws event union (tick, tool_call, agent_msg, fault_injected, fault_observed, done, error, race_done).
- Mobile `?mode=summary`: handoff to Phase 10 OG image generation; Phase 8 only emits the viewport check + redirect/render-decision.
</code_context>

<specifics>
## Specific Ideas

- **Live-vs-replay parity**: same `RacePage` component for both modes. Single page-state enum drives both code paths; replay just provides scrubbed events instead of streamed events. This is also what makes the 12-state matrix tractable — no parallel component trees.
- **Popover dismiss copy**: "Got it" (decided D-50). Single-button dismiss; no "don't show again" because D-51 already short-circuits per-route.
- **Keyboard navigation through heatmap cells**: Tab into the grid lands on first cell; arrow keys move between cells; Enter/Space opens cell detail. Native CSS Grid + role=grid gives this for free.
- **`aria-live` rate limit during scrub**: throttle to one announcement per 200ms during scrubber drag; full announcements resume on scrubber release.
</specifics>

<deferred>
## Deferred Ideas

- **OG image rendering** — surfaced during D-48 deep-link discussion. Lives in Phase 10 (OG Image & Sharing). Phase 8 only ships the deep-link route shape; Phase 10 produces the PNG.
- **Heatmap data backend** — heatmap-empty state (D-47) implies a data source. Backend lives in Phase 9 (HEAT-01/HEAT-02). Phase 8 ships the rendering layer + empty-state contract; data wiring lands in Phase 9.
- **Multi-task K=3 calibration UI** — surfaced as "what does the heatmap show across tasks". Phase 9 HEAT-04 ships the calibration data; Phase 8 renders whatever the API returns.
- **Replay backend trace fetch** — D-48 replay route assumes a `/api/race/runs/<run_id>/trace` endpoint. Phase 9 HEAT-03 ships the deterministic replay path. Phase 8 stubs the fetch with a typed call signature.

### Reviewed Todos (not folded)
None — no TODOS.md items matched Phase 8 scope.
</deferred>

---

*Phase: 8-race-page-ui-visual-contract*
*Context gathered: 2026-04-29*
