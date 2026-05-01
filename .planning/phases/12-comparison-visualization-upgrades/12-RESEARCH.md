---
phase: 12
slug: comparison-visualization-upgrades
status: draft
created: 2026-05-01
researcher: gsd-researcher
domain: React + MUI v5 frontend (TypeScript strict)
confidence: HIGH
---

# Phase 12: Comparison Visualization Upgrades — Research

> Two visualizations on **existing surfaces**, no new deps, no new routes.
> VIZ-01 = annotated diff toggle on `CompareTracesPanel`. VIZ-02 = hand-rolled SVG sequence diagram toggle on `TraceExplorer`.

---

## Goal

Ship VIZ-01 and VIZ-02 as in-place header toggles on `CompareTracesPanel.tsx` and `TraceExplorer.tsx` respectively, honoring all 12 LOCKED decisions D-74..D-85 in `12-CONTEXT.md` and the approved `12-UI-SPEC.md` component contract.

**Primary recommendation:** Build `AnnotatedDiffView.tsx` and `SequenceDiagramView.tsx` as net-new components in `frontend/src/components/traces/`, both consuming `TraceEvent[]` props, both using only MUI primitives + existing `lib/trace/` utilities. Lift `pinnedEventId` into `TraceExplorer` parent state (D-82). Pure-function `useMemo`-cached diff alignment. SVG-only sequence diagram with per-arrow `<rect>` 24px hit areas and `useMediaQuery('(prefers-reduced-motion: reduce)')` gate. NO `@xyflow/react`. NO `motion` lib unless behind reduced-motion gate (D-85).

---

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| VIZ-01 | Annotated diff between two protocol traces — line-by-line, role-first labels, reachable from CompareTracesPanel header | §1 alignment algorithm, §2 mount integration |
| VIZ-02 | Interactive sequence diagram per trace — vertical lifelines, horizontal arrows, click-to-pin, prefers-reduced-motion | §3 mount integration, §4 SVG patterns, §5 reduced-motion |

---

## User Constraints (from CONTEXT.md)

### Locked Decisions

**VIZ-01 — Diff Alignment & Layout**
- **D-74:** Alignment = `(turn_index, event_type)` exact match. Unmatched on either side = added/removed. Matched events compared field-by-field for "matched-divergent" (e.g., one has `fault_observed`, the other doesn't).
- **D-75:** Diff entry = toggle on `CompareTracesPanel` header (`Side-by-side | Annotated diff`). In-place. No new route.
- **D-76:** Diff scope = ALL `event_type`s. NO pre-filter. Discovery divergence is a feature.
- **D-77:** Divergence visual = bg tint + gutter chip (added=`success.main` `+`, removed=`error.main` `−`, matched-divergent=`warning.main` left-border, override to `failureTagColor.kept_going_to_failure.text` when fault-related).
- **D-78:** Role-first labels via `traceLabel(event)`.

**VIZ-02 — Sequence Diagram**
- **D-79:** Pure SVG, hand-rolled. Single `<svg>` root.
- **D-80:** 5 fixed lifelines: `User`, `Orchestrator`, `LLM`, `Tool`, `Remote Agent`. Tool/agent name on the arrow label, not as separate lane.
- **D-81:** Mount = toggle on `TraceExplorer` header (`List | Sequence`). Filter state shared across both views.
- **D-82:** Click-to-pin persists pinned event id; lifted into `TraceExplorer` parent. Toggling back to List scrolls to + highlights the pinned row.
- **D-83:** `prefers-reduced-motion` honored — no animated arrow draw-in, no scroll easing.

**Cross-cutting**
- **D-84:** Reuse existing tokens (`failureTagColor`, `getProtocolColor`, MUI palette). NO new color tokens.
- **D-85:** NO new dependencies. `@xyflow/react` is **NOT** used. `motion` only behind reduced-motion gate.

### Claude's Discretion
- Animation timing curves and easing values (when motion permitted).
- Internal `DiffRow[]` shape (UI-SPEC pre-fills a recommended shape; planner may refine).
- Hit-target sizing and z-order for SVG arrow click areas (UI-SPEC sets minimum 24px).
- Whether the diff view reuses TraceExplorer's filter chrome at the top (planner decides — recommend YES; see §2).
- Pinned-event state location (UI-SPEC settled this: lifted into `TraceExplorer`).

### Deferred Ideas (OUT OF SCOPE)
- TraceExplorer event filters applied to sequence diagram (UI-SPEC says shared state implied; per-instance filter divergence out).
- Connector lines between matched events in side-by-side mode.
- Per-instance lifelines (one lane per distinct tool/agent).
- Sequence diagram on RacePage / ReportDetailPage.
- Diff export (copy as markdown / share URL).
- Cross-trace pinning in Diff view.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|--------------|----------------|-----------|
| Diff alignment compute | Frontend / Browser (pure fn) | — | Pure transform of in-memory `TraceEvent[]` already on the page; no server round-trip needed |
| Diff render | Frontend / Browser | — | MUI + CSS Grid; data already loaded |
| Sequence diagram render | Frontend / Browser | — | SVG-in-DOM; data already loaded |
| Pinned event state | Frontend / Browser (`TraceExplorer` `useState`) | — | Component-local; no persistence required (UI-SPEC: not session-persisted) |
| Filter state share | Frontend / Browser (`TraceExplorer` `useState`, existing) | — | Already lives there; reused by both List and Sequence views |
| `traceEventActor` → lane mapping | Frontend / Browser (existing helper) | — | Pure function, already shipped |
| Theme tokens | Frontend / Browser (`appTheme` + `eventColors.ts`) | — | Single source of truth from Phase 8 |

---

## Project Constraints (from CLAUDE.md)

- Frontend tests: `cd frontend && npm test` (vitest)
- Backend tests: `pytest` (not exercised by Phase 12 — frontend-only)
- Frontend dev: `cd frontend && npm run dev`
- claude-mem: save significant decisions via POST `/api/memory/save` with `project: "A2AvsMCP"` (planner discretion)
- graphify: run `graphify update .` after code modifications

---

## Standard Stack

### Core (already installed; no new deps per D-85)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `react` | 18.x | UI rendering | Project baseline | [VERIFIED: package.json] |
| `@mui/material` | v5 | Components — `ToggleButtonGroup`, `Chip`, `Tooltip`, `Alert`, `Paper`, `Grid`, `Stack` | Project baseline (MUI-only by Phase 8 contract) [VERIFIED: codebase grep] |
| `@mui/icons-material` | v5 | Outlined icons (matches TraceExplorer + DiscoveryPhasePanel convention) | Project baseline |
| TypeScript strict | — | Type safety | Project baseline |
| `vitest` + `@testing-library/react` | — | Component tests | Project baseline (`frontend/src/test/setup.ts`) |

### Forbidden (D-85)
| Library | Status | Reason |
|---------|--------|--------|
| `@xyflow/react` | **INSTALLED but FORBIDDEN** for VIZ-02 | D-85 explicit; free-form graph fights sequence-diagram constraints |
| `motion` (framer-motion alias) | INSTALLED, conditionally allowed | Only behind `useMediaQuery('(prefers-reduced-motion: reduce)') === false` gate (D-85) |
| Any diff library (`diff`, `jsdiff`, `react-diff-viewer`) | NOT INSTALLED, FORBIDDEN | D-85; alignment is `O(n+m)` bucket-by-`(turn_index, event_type)` — trivial to hand-roll |

### Reuse (existing project utilities — DO NOT DUPLICATE)
| Helper | Location | Used For |
|--------|----------|----------|
| `traceLabel(event)` | `frontend/src/lib/trace/utils.ts:7` | Row label (role-first) [VERIFIED] |
| `traceEventActor(event)` | `frontend/src/lib/trace/utils.ts:52` | Lane mapping for sequence diagram [VERIFIED] |
| `traceEventProtocol(event)` | `frontend/src/lib/trace/utils.ts:56` | Arrow stroke color via `getProtocolColor()` [VERIFIED] |
| `traceEventTone(event)` | `frontend/src/lib/trace/utils.ts:34` | Fault detection for matched-divergent override [VERIFIED] |
| `isTraceFailureEvent(event)` | `frontend/src/lib/trace/utils.ts:22` | Fault classification for divergence cause [VERIFIED] |
| `failureTagColor` | `frontend/src/lib/trace/eventColors.ts:54` | Added/removed row tints (UI-SPEC mapping) [VERIFIED] |
| `getProtocolColor(mode)` | `frontend/src/lib/trace/eventColors.ts:30` | Arrow + column header color [VERIFIED] |
| `eventBorderColor(event)` | `frontend/src/lib/trace/eventColors.ts:35` | Optional matched-equal row decoration source |
| `toneColor.warning` / `toneColor.error` | `frontend/src/lib/trace/eventColors.ts:20` | Matched-divergent border + error states [VERIFIED] |
| `JsonTree` | `frontend/src/lib/trace/JsonTree.tsx` | Expandable payload inside diff rows [VERIFIED] |

**Installation:** _none — D-85_

---

## 1. Diff Alignment Algorithm Specifics

### `TraceEvent` field inventory (from `frontend/src/lib/types/api.ts:34-56`)

**Required fields (all events):**
- `index: number` — sequential index within the trace
- `event_type: string` — primary alignment key (D-74)
- `timestamp_ms: number`

**Optional, declared:**
- `message_type?: string` (used by `traceLabel` to disambiguate `event_type:message_type`)
- `agent? | sender? | target? | tool? | server?: string`
- `status? | protocol? | transport? | requested_transport? | error?: string`
- `step_index? | started_at? | completed_at?: number`
- `phase?: "discovery" | "execution"`
- `parallel_batch_id?: string`

**Open-ended index signature** `[key: string]: unknown` — events carry arbitrary additional fields (e.g., `task_id`, `remote_agent`, `tools`, `wasted_tokens_before_detection`, `evidence`, `fault_id`, `fault_kind`).

**`turn_index` IS NOT statically declared on `TraceEvent`** but is emitted by `TraceRecorder` (`src/a2a_vs_mcp/trace.py:60` confirmed). It arrives via the index signature as `unknown` and the planner must coerce: `(event as { turn_index?: number }).turn_index ?? 0`. [VERIFIED: backend grep]

### Alignment algorithm (recommended shape)

```ts
type DiffStatus = "added" | "removed" | "matched-equal" | "matched-divergent";

interface DiffRow {
  status: DiffStatus;
  left?: TraceEvent;
  right?: TraceEvent;
  turnIndex: number;
  divergenceCause?: "fault" | "field";
  // optional: which field(s) differ — useful for tooltip body
  differingFields?: string[];
}

export function alignTraces(left: TraceEvent[], right: TraceEvent[]): DiffRow[] {
  // 1. Bucket each side by `${turn_index}::${event_type}` -> TraceEvent[]
  //    (Lists, not sets — duplicates within same turn+type are paired by order.)
  // 2. For each unique key in union(leftKeys, rightKeys):
  //    pair leftBucket[i] with rightBucket[i] until one runs out;
  //    surplus on left -> "removed"; surplus on right -> "added".
  // 3. For each paired (l, r): compute IGNORE-set diff.
  //    Equal => "matched-equal".
  //    Differs => "matched-divergent" with divergenceCause = "fault" if
  //    (isTraceFailureEvent(l) !== isTraceFailureEvent(r))
  //    OR either side has fault_observed/fault_injected fields differing;
  //    else "field".
  // 4. Sort: by turnIndex asc, then within turn:
  //    matched-equal first, matched-divergent next, added/removed last.
  //    (Per UI-SPEC line 212.)
  return rows;
}
```

### Field comparison set ("non-trivial" fields)

**IGNORE during equality comparison** (these always differ across protocol runs and are not signals of behavioral divergence):
- `timestamp_ms`, `started_at`, `completed_at` (wall-clock will always differ)
- `index` (per-trace ordering)
- `parallel_batch_id` (per-run UUID)
- `task_id` (per-A2A-task UUID; differs between runs even when both succeed)
- `messageId`, `contextId`, `artifactId` (A2A-protocol UUIDs)
- `run_id` if present
- `lane` if present (one trace is MCP-lane, other is A2A-lane — that's the comparison axis itself)

**COMPARE** (these signal real divergence):
- `event_type`, `message_type`, `status`, `error`
- `agent`, `sender`, `target`, `tool`, `server`
- `protocol`, `transport`, `requested_transport`
- `phase`
- `fault_id`, `fault_kind`, `fault_observed`, `evidence`, `wasted_tokens_before_detection` (THE headline divergence signal — see UI-SPEC tooltip "Fault observed on one side only")
- `step_index`
- All other index-signature fields not in IGNORE

### Recommended pure-function shape

- Pure function `alignTraces(left, right): DiffRow[]` in `frontend/src/components/traces/diffAlign.ts` (or co-located in `AnnotatedDiffView.tsx` if planner prefers; UI-SPEC doesn't pin location).
- Memoized via `useMemo([leftEvents, rightEvents])` inside `AnnotatedDiffView`.
- `O(n + m)` — bucket pass + pairing pass.
- Returns `DiffRow[]` flattened in turn-order.
- **Test surface:** unit-test the pure function with fixture pairs covering all 4 statuses + fault-vs-field divergence-cause split.

**Confidence: HIGH** — every claim verified against codebase or backend grep.

---

## 2. `CompareTracesPanel.tsx` Integration Shape

### Current structure (verified, lines 22-165)

- **Props:** `{ results: RunResult[] }` — array of 1+ runs.
- **State:** `modeA`, `modeB` (mode selectors); refs `scrollRefA`, `scrollRefB` for sync-scroll mutex (`syncing` ref + `requestAnimationFrame` reset).
- **Layout:**
  1. Two `<Select>` mode pickers in a top `Grid` (lines 64-109).
  2. Conditional `<DiscoveryPhasePanel>` full-width above dual-column when `showDiscoveryPanel` is true (lines 112-118).
  3. Two `<TraceExplorer>` columns inside `Grid` with sync-scrolled `<Box>` parents (lines 121-162).
- **Sync-scroll mutex:** `handleScroll` callback at lines 32-43; uses `syncing.current` + `requestAnimationFrame`. Phase-6 anti-cascade pattern.

### Integration plan for VIZ-01

1. **Add header-level `viewMode` state:** `const [viewMode, setViewMode] = useState<"side-by-side" | "diff">("side-by-side");`
2. **Insert MUI `ToggleButtonGroup`** after the Mode A/B `Grid` (line 109) and before the optional `DiscoveryPhasePanel` (line 112). Right-aligned via `Stack direction="row" justifyContent="flex-end"`. Two buttons: `"Side-by-side"` and `"Annotated diff"` (UI-SPEC copy lines 238-239).
3. **Conditionally render the body:**
   - When `viewMode === "side-by-side"`: existing dual-column `Grid` (lines 121-162) — UNCHANGED.
   - When `viewMode === "diff"`: `<AnnotatedDiffView leftEvents={resultA?.trace ?? []} rightEvents={resultB?.trace ?? []} leftProtocolLabel={resultA?.mode ? \`${resultA.mode.toUpperCase()} — Trace A\` : undefined} rightProtocolLabel={...} />` (defaults from UI-SPEC).
4. **DiscoveryPhasePanel stays mounted in both view modes** — it sits ABOVE the toggle's swap region. (Recommended; UI-SPEC doesn't say otherwise.)
5. **Sync-scroll mutex:** does NOT apply to diff view (single scroll container — diff is one grid). Refs stay attached to side-by-side mode only. No conflict.

### Existing tests for `CompareTracesPanel.tsx`

- **NO dedicated test file exists** — verified via `find ... -name "*test*"` (no `CompareTracesPanel.test.tsx` in repo).
- **Indirect coverage:** rendered through Phase 11 `TraceWorkspacePage` integration tests (Plan 11-04). Diff toggle behavior MUST get its own test in Phase 12.

### Filter chrome reuse

UI-SPEC and CONTEXT both leave this to planner discretion. **Recommendation:** the diff view does NOT need `TraceExplorer`'s filter chrome (event/actor/tool/protocol/failure dropdowns). Diff renders ALL event types per D-76 ("no pre-filter") — the whole point is to show every divergence, including in event types a user might filter out. Adding filter chrome on top would let users defeat D-76. Keep diff view filter-free in v1; defer to v2 if user demand surfaces.

**Confidence: HIGH** — all line numbers verified.

---

## 3. `TraceExplorer.tsx` Integration Shape

### Current structure (verified, lines 39-223)

- **Props:** `{ events: TraceEvent[]; title?, subtitle?, runtime? }`.
- **State (5 filters):** `eventFilter`, `actorFilter`, `toolFilter`, `protocolFilter`, `failureFilter` — all `useState<string>`.
- **Memoized:** `eventTypes`, `actors`, `tools`, `protocols`, `filteredEvents`, `stats`.
- **Layout (lines 91-222):**
  1. `<Card><CardContent><Stack>` outer wrap.
  2. Header row (lines 95-110): title + subtitle on left, optional `Expect 2-5s per LLM call` chip on right when `runtime === "llm"`.
  3. 4-tile stats `Grid` (lines 112-133).
  4. 5-filter `Grid` (lines 135-162).
  5. `<Divider />`.
  6. Optional warning `<Alert>` if `runtime` is real LLM.
  7. **Tier 0 summary strip** (always visible).
  8. **Tier 1 Accordion** "Protocol Events" (default collapsed) — renders `<ProtocolTier>`.
  9. **Tier 2 Accordion** "Full Trace" (default collapsed) — renders `<FullTraceTier>` (raw JSON).

### Integration plan for VIZ-02

1. **Add header-level `viewMode` state:** `const [viewMode, setViewMode] = useState<"list" | "sequence">("list");`
2. **Add lifted `pinnedEventId` state (D-82):** `const [pinnedEventId, setPinnedEventId] = useState<string | null>(null);`
   - **Note on `TraceEvent.id`:** The schema does NOT declare `id`. Use `index` (always present, monotonic per trace) as the pin key. `pinnedEventIndex: number | null` is more accurate than `pinnedEventId: string | null` per the actual schema. UI-SPEC says "event id" — planner should clarify in plan but this is a minor type-name issue, not a behavior change. Recommend: keep prop name `pinnedEventId: string | null` for UI-SPEC fidelity, store `String(event.index)` as the value.
3. **Insert MUI `ToggleButtonGroup`** at the right end of the header `<Stack direction="row">` (currently at line 95) — replace the conditional `runtime === "llm"` chip placement with a flex stack containing both the chip AND the toggle. Two buttons: `"List"`, `"Sequence"` (UI-SPEC lines 240-241).
4. **Body branching:**
   - When `viewMode === "list"`: render the existing Tier 0 + Tier 1 + Tier 2 stack (lines 172-217) UNCHANGED. When `pinnedEventId !== null` and just toggled FROM sequence, scroll the matching `ProtocolEventRow` into view via `scrollIntoView({ behavior: prefersReducedMotion ? 'auto' : 'smooth', block: 'center' })` and apply a 1.5s `secondary.main` outline (UI-SPEC line 222).
   - When `viewMode === "sequence"`: render `<SequenceDiagramView events={filteredEvents} pinnedEventId={pinnedEventId} onPinEvent={setPinnedEventId} protocol={inferProtocolFromEvents(events)} />`.
5. **Stats + summary strip + filter chrome stay rendered in both views** — they sit ABOVE the toggle swap region. Filter state is shared (D-81). **`SequenceDiagramView` consumes `filteredEvents`, NOT raw `events`** — so filter dropdowns affect both views identically. (CONTEXT `<deferred>` already implies this is intended.)

### Existing tests for `TraceExplorer.tsx`

- **NO dedicated test file exists** — verified via repo `find`. Closest is `DiscoveryPhasePanel.test.tsx` (an in-place component, similar pattern). Planner MUST add `TraceExplorer.test.tsx` (or expand to a new test file for the toggle + sequence view) covering: toggle keyboard nav, pin propagation, scroll-to-pinned-row on toggle.

### State location decision

Both `viewMode` and `pinnedEventId` are component-local (`useState` inside `TraceExplorer`). **No Redux, no Context — verified by codebase grep:** the only React Context in the project is `FirstMentionProvider` (race-page-scoped) and `AppUiProvider` (test wrapper). No state-management library. Component-local `useState` + prop drill into `SequenceDiagramView` is the correct pattern.

**Confidence: HIGH** — all line numbers verified.

---

## 4. SVG Sequence Diagram Patterns for React

### Hand-rolled SVG fundamentals

- **Single root `<svg>` element**, `width="100%"`, `viewBox="0 0 W H"` (responsive, retains aspect ratio).
- **Layers via `<g>`:** lifelines layer (back), arrows layer (front), foreignObject overlay layer (top, for MUI Chip on pinned arrow).
- **Lifelines:** `<line x1={laneX} y1={48} x2={laneX} y2={canvasHeight} stroke="rgba(16,32,51,0.18)" strokeDasharray="4 4" strokeWidth={1} aria-hidden="true" />`.
- **Lane headers:** `<text x={laneX} y={24} textAnchor="middle" fontSize={11} fontWeight={600}>{role}</text>` per UI-SPEC `overline` variant (raw SVG `<text>` since MUI Typography doesn't render inside `<svg>`).
- **Arrows:** `<line>` body + `<polygon>` arrowhead at target end. For self-messages: `<path d="M ... a r,r ..." />` 24px loop arc.

### Click-to-pin technique (a11y)

- Each arrow rendered as a `<g role="button" tabIndex={0}>` containing:
  1. **Visible stroke** `<line strokeWidth="1.5">` (or `2` if pinned) + arrowhead `<polygon>`.
  2. **Hit-area** `<rect>` 24px tall, transparent fill (`fill="transparent"` — NOT `fill="none"`; `none` makes the rect un-hittable). This is the actual click target. (UI-SPEC spacing exception: 24px = a11y minimum.)
  3. **Label** `<text>` above arrow midpoint, `<text>` is naturally not the click target.
- `onClick={() => onPinEvent(currentlyPinned ? null : eventId)}` on the `<g>`.
- `onKeyDown` handler on the `<g>` for Enter/Space → same toggle (UI-SPEC line 227).
- `aria-label="{actor source} → {actor target}: {role-first label}, turn {turn_index}"` on the `<g>`.

### `<foreignObject>` for MUI Chip (UI-SPEC line 172)

- `<foreignObject x={...} y={...} width={80} height={24}><Chip label="Pinned" size="small" color="secondary" /></foreignObject>`.
- **Browser quirk: Safari `<foreignObject>` rendering bugs.** Safari < 16 has known issues clipping content inside `<foreignObject>` and incorrect z-stacking. As of mid-2025, Safari ≥ 16 (released Sep 2022) renders MUI components inside `<foreignObject>` correctly per general WebKit docs. **Mitigation: don't rely on `<foreignObject>` for critical UI** — the underlying pin state must remain accurate even if the chip mis-renders. The `<rect>` outline (the 4px secondary.main border per UI-SPEC) is the primary signal; the Chip is a redundant secondary indicator. **[CITED: developer.mozilla.org/en-US/docs/Web/SVG/Element/foreignObject — MDN notes long-standing Safari quirks; specific version threshold is approximate.] [ASSUMED: Safari ≥ 16 renders cleanly — verify in QA.]**
- Alternative if Safari issues surface: render the "Pinned" indicator as raw SVG `<g>` (rect background + `<text>`) instead of `<foreignObject> + Chip`.

### Animation gating (D-83)

```ts
const prefersReducedMotion = useMediaQuery('(prefers-reduced-motion: reduce)');
// Arrow draw-in animation: gate via CSS-in-JS sx or a single useEffect
// Recommended: use SVG SMIL <animate> attribute conditionally OR a CSS class on the <g>
//   that triggers `stroke-dasharray` + `stroke-dashoffset` transition (200ms ease-out).
//   Skip applying the class entirely when prefersReducedMotion === true.
```

The Phase 8 baseline pattern is `useMediaQuery('(prefers-reduced-motion: reduce)')` (verified at `RaceLaneCard.tsx:42` and tested at `RacePage.a11y.test.tsx:114` with `mockMatchMedia`). **Use this pattern, not raw `@media` blocks**, so vitest can `vi.mock("@mui/material/useMediaQuery")` deterministically.

### Performance notes

- For 100-event traces (typical demo size), one `<svg>` with `events.length * 32px` rows = ~3200px tall. Browser handles this trivially; no virtualization needed.
- For traces with > 500 events (rare in this project — `RENDER_CAP = 150` in `TraceExplorer`), consider future virtualization. Out of scope for v1.

**Confidence: HIGH** for SVG technique, MEDIUM for Safari `<foreignObject>` version threshold (cited but not re-verified in this session).

---

## 5. `prefers-reduced-motion` Enforcement Pattern

**Verified codebase idiom** (Phase 8 baseline):

| File | Line | Pattern |
|------|------|---------|
| `frontend/src/features/race/components/RaceLaneCard.tsx` | 42 | `const highContrast = useMediaQuery("(prefers-contrast: more)");` (same hook family) |
| `frontend/src/features/race/components/ReplayScrubber.tsx` | 78-80 | `sx: { "@media (prefers-reduced-motion: reduce)": { transition: "none" } }` (CSS-in-JS form) |
| `frontend/src/features/race/RacePage.a11y.test.tsx` | 113-114 | `mockMatchMedia("(prefers-reduced-motion: reduce)")` test helper |
| `frontend/src/features/race/components/RaceLaneCard.test.tsx` | 8, 187 | `vi.mock("@mui/material/useMediaQuery", () => ({ default: vi.fn() }))` — mockable for deterministic tests |

**Recommendation for VIZ-02:** mirror `RaceLaneCard` — use `useMediaQuery('(prefers-reduced-motion: reduce)')` (the JS form, not the CSS form) inside `SequenceDiagramView`. This makes the same `vi.mock(...)` pattern from `RaceLaneCard.test.tsx:8` directly reusable in the new test file.

**Recommendation for the toggle-back-to-list scroll behavior** (UI-SPEC line 222): use the JS hook return value to conditionally pass `behavior: 'auto' | 'smooth'` to `scrollIntoView`. CSS-in-JS won't apply here because `scrollIntoView` is a JS API.

**Confidence: HIGH** — all line numbers verified.

---

## 6. Test Scaffolding

### Frontend test setup (verified, per `.planning/codebase/TESTING.md`)

- **Framework:** Vitest + `@testing-library/react` + `@testing-library/user-event`
- **Config:** `frontend/vite.config.ts` — `test.environment: "jsdom"`, `globals: true`, `setupFiles: "./src/test/setup.ts"`
- **Setup file:** `frontend/src/test/setup.ts` — jest-dom matchers, clipboard + URL.createObjectURL mocks
- **Render helper:** `frontend/src/test/renderWithProviders.tsx` (`ThemeProvider + AppUiProvider + MemoryRouter`)

### Pattern for component tests (from `DiscoveryPhasePanel.test.tsx`, the most-recent-shipped in-place panel test)

```tsx
import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { appTheme } from "../../../app/theme";

function renderComponent(props) {
  return render(
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <AnnotatedDiffView {...props} />
    </ThemeProvider>,
  );
}
```

This is the simpler `ThemeProvider + CssBaseline` form (no `MemoryRouter`, no `AppUiProvider`). Use this form when the component does NOT touch routing or app-wide UI context. Both `AnnotatedDiffView` and `SequenceDiagramView` qualify — they take props, don't read context, don't navigate.

### Testing toggle visibility

```tsx
import userEvent from "@testing-library/user-event";

it("toggles between Side-by-side and Annotated diff views", async () => {
  renderCompareTracesPanel({ results: twoResultsFixture });
  expect(screen.getByText("MCP Trace")).toBeInTheDocument(); // side-by-side default
  await userEvent.click(screen.getByRole("button", { name: /annotated diff/i }));
  expect(screen.getByText(/MCP — Trace A/)).toBeInTheDocument(); // diff column header
});
```

### Testing SVG click handlers

`react-testing-library` `fireEvent.click` works on SVG elements. The `<g role="button">` is found via `screen.getByRole("button", { name: /User → Tool: tool_call, turn 3/i })`. Click handlers fire normally.

```tsx
it("pins event on arrow click and unpins on second click", async () => {
  const onPin = vi.fn();
  renderSequenceDiagram({ events: threeFixture, onPinEvent: onPin });
  const arrow = screen.getByRole("button", { name: /User → Tool/i });
  await userEvent.click(arrow);
  expect(onPin).toHaveBeenCalledWith("0"); // String(event.index)
  await userEvent.click(arrow);
  expect(onPin).toHaveBeenLastCalledWith(null);
});
```

### Testing reduced-motion

```tsx
vi.mock("@mui/material/useMediaQuery", () => ({ default: vi.fn() }));
// ...
test("static render under prefers-reduced-motion", async () => {
  const useMediaQuery = await import("@mui/material/useMediaQuery");
  (useMediaQuery.default as ReturnType<typeof vi.fn>).mockReturnValue(true);
  renderSequenceDiagram({ events: fixture });
  // assert: arrow elements have no transition style / no animate elements
  const arrow = screen.getByRole("button", { name: /User → Tool/i }).querySelector("line");
  expect(arrow).not.toHaveStyle({ transition: expect.stringContaining("stroke-dashoffset") });
});
```

This is the pattern from `RaceLaneCard.test.tsx:185-188` adapted for reduced-motion (instead of high-contrast).

### Pure-function test (`alignTraces`)

A pure-function test of `alignTraces(left, right)` does NOT need React or theme; just `vitest`:

```ts
import { describe, it, expect } from "vitest";
import { alignTraces } from "../diffAlign";

it("classifies turn-index match with identical fields as matched-equal", () => {
  const a = [{ index: 0, event_type: "tool_call", timestamp_ms: 1, turn_index: 0, tool: "x" }];
  const b = [{ index: 0, event_type: "tool_call", timestamp_ms: 99, turn_index: 0, tool: "x" }];
  const rows = alignTraces(a as any, b as any);
  expect(rows).toHaveLength(1);
  expect(rows[0].status).toBe("matched-equal");
});
```

**Recommended new test files (planner discretion on naming/colocation):**
- `frontend/src/components/traces/__tests__/AnnotatedDiffView.test.tsx`
- `frontend/src/components/traces/__tests__/SequenceDiagramView.test.tsx`
- `frontend/src/components/traces/__tests__/diffAlign.test.ts` (pure function)
- Augment or create `frontend/src/components/traces/__tests__/TraceExplorer.test.tsx` for toggle wiring + pin propagation
- Augment `frontend/src/features/compare/__tests__/CompareTracesPanel.test.tsx` (new) for diff toggle wiring

**Confidence: HIGH** — all patterns verified against existing tests.

---

## 7. Validation Architecture (lightweight coverage map)

> `nyquist_validation: false` in `.planning/config.json` — this section is informational. Planner may use as a checklist when authoring task verification steps.

### Test framework

| Property | Value |
|----------|-------|
| Framework | Vitest (frontend) — `cd frontend && npm test` |
| Config | `frontend/vite.config.ts`, setup `frontend/src/test/setup.ts` |
| Quick run | `cd frontend && npx vitest run --reporter=dot src/components/traces` |
| Full suite | `cd frontend && npm test` (current baseline 291/291 passing per STATE.md) |

### Decision-to-validation map

| Decision | What validates it | Type |
|----------|------------------|------|
| D-74 (alignment by `turn_index + event_type`) | `diffAlign.test.ts` — pair fixture pairs across all 4 statuses | unit |
| D-75 (toggle on CompareTracesPanel header, in-place) | `CompareTracesPanel.test.tsx` — toggle click swaps body, no router nav | component |
| D-76 (no pre-filter; all event types) | `diffAlign.test.ts` — fixture with `tool_discovery`, `agent_msg`, `fault_observed`, `llm_*` all appear in `DiffRow[]` | unit |
| D-77 (gutter chip + tint + matched-divergent border) | `AnnotatedDiffView.test.tsx` — render-time DOM assertions (`+`, `−`, `≠` chips visible; `data-status` attribute on row) | component |
| D-78 (role-first labels via `traceLabel`) | grep — `traceLabel(...)` invoked in row label render | static check |
| D-79 (pure SVG, hand-rolled) | grep — no `import` from `@xyflow/react` in `SequenceDiagramView.tsx` | static check |
| D-80 (5 fixed lifelines) | `SequenceDiagramView.test.tsx` — 5 `<text>` lane headers in document; `traceEventActor` mapped to one of 5 | component |
| D-81 (toggle on TraceExplorer header, shared filter state) | `TraceExplorer.test.tsx` — apply event-type filter, toggle to sequence, only filtered events render | component |
| D-82 (click-to-pin + scroll-to-pinned-row on toggle back) | `TraceExplorer.test.tsx` — click arrow in Sequence, toggle to List, pinned row has highlight + `scrollIntoView` was called | component |
| D-83 (`prefers-reduced-motion` honored) | `SequenceDiagramView.test.tsx` — mock `useMediaQuery` to return `true`, assert no transition styles, no SMIL `<animate>` elements | component |
| D-84 (no new color tokens) | grep — no new hex literals in `AnnotatedDiffView.tsx` / `SequenceDiagramView.tsx` outside `eventColors.ts` imports | static check + manual UAT |
| D-85 (no new dependencies) | `git diff package.json` — no additions; grep — no `import.*@xyflow` in either new component | static check |

### Manual UAT items (non-automatable)

- Visual confirmation that gutter chips align consistently across rows.
- Visual confirmation that arrow strokes and arrowheads render correctly on Safari, Firefox, Chrome.
- Keyboard-only interaction: Tab to toggle, arrow-keys cycle, Tab to first arrow, Enter pins, Escape... (Escape behavior not in UI-SPEC — flag if planner wants Escape-to-unpin).
- Screen reader narration: VoiceOver/NVDA reads `aria-label` on arrows and announces `aria-live` pin changes.

---

## Common Pitfalls

### 1. `turn_index` is on `[key: string]: unknown` not declared statically
**What goes wrong:** TypeScript `event.turn_index` is `unknown`, breaks comparisons with `===`.
**Why:** The `TraceEvent` interface (`api.ts:34-56`) declares index signature `[key: string]: unknown` rather than typing race-schema fields. `turn_index` is emitted by backend (`trace.py:60`) but not declared frontend-side.
**How to avoid:** Always coerce: `const turnIdx = (event as { turn_index?: number }).turn_index ?? 0;`. Or define a local `TraceEventWithRaceFields` type alias inside `diffAlign.ts`.
**Warning sign:** TS error "Operator '===' cannot be applied to types 'unknown' and 'number'" during alignment implementation.

### 2. `useMemo` invalidation when `leftEvents` / `rightEvents` are recreated each render
**What goes wrong:** `CompareTracesPanel` re-derives `resultA?.trace ?? []` inline — every render returns a NEW array reference. `useMemo([leftEvents, rightEvents], ...)` will then recompute alignment every render, defeating the cache.
**How to avoid:** Pass `resultA?.trace` (not `resultA?.trace ?? []`) and handle null inside `AnnotatedDiffView`, OR memoize the `?? []` defaults at the parent: `const leftEvents = useMemo(() => resultA?.trace ?? EMPTY_ARRAY, [resultA]); const EMPTY_ARRAY: TraceEvent[] = [];` (module-level constant).
**Warning sign:** React DevTools Profiler shows `useMemo` recomputing on every parent render.

### 3. `<foreignObject>` Safari rendering quirks
**What goes wrong:** MUI Chip rendered inside `<foreignObject>` may clip, mis-stack, or fail to receive events on older Safari (< 16).
**How to avoid:** Don't make pinned-state visibility depend solely on the `<foreignObject>` Chip. The 4px `secondary.main` `<rect>` outline around the arrow hit-area (UI-SPEC line 172) is the redundant primary signal. If QA flags Safari issues, swap the Chip for raw SVG `<g><rect/><text/>`.
**Warning sign:** "Pinned" chip appears clipped or misaligned on QA in Safari.

### 4. `@xyflow/react` accidentally imported (D-85 violation)
**What goes wrong:** It's installed in `package.json` and IDE auto-import will offer it.
**How to avoid:** Add a grep step to phase verification: `! grep -r "@xyflow" frontend/src/components/traces/SequenceDiagramView.tsx` (must exit non-zero, i.e. zero matches). Land this grep as an `npm run lint:no-xyflow` script if the planner wants belt-and-suspenders.
**Warning sign:** Sequence diagram has nodes that drag, snap-to-grid, or auto-layout — that's xyflow, not hand-rolled SVG.

### 5. `motion` library used without reduced-motion gate
**What goes wrong:** `motion` (framer-motion) is installed; auto-imports happen.
**How to avoid:** The ONLY allowed `motion` use per D-85 is gated on `!useMediaQuery('(prefers-reduced-motion: reduce)')`. Recommend NOT using `motion` at all for v1 — CSS transitions on `stroke-dashoffset` (toggled via class) achieve the 200ms arrow draw-in cleanly without dependency surface.
**Warning sign:** `import { motion } from "motion/react";` in either new component without an explicit reduce-motion guard wrapping the motion-tagged element.

### 6. Sync-scroll mutex conflicts when diff view is in place
**What goes wrong:** The existing sync-scroll mutex (`scrollRefA`, `scrollRefB`, `syncing.current`) was designed for two side-by-side TraceExplorer columns. When the diff view replaces the body, those refs point to nothing.
**How to avoid:** Sync-scroll is a side-by-side-mode-only feature. Refs only matter while side-by-side renders. When diff renders, the refs are detached (the elements unmount); React handles this cleanly. **No code change needed beyond conditional rendering — but planner should test that toggling back to side-by-side restores sync-scroll** (re-mounting the columns re-binds the refs).
**Warning sign:** After toggle round-trip, scrolling in column A doesn't move column B.

### 7. 5-role lifeline aggregation hides multi-tool divergence
**What goes wrong:** Both `db_server` and `docs_server` events map to lane "Tool" — visual collapse may hide that one trace called `db_server` and the other called `docs_server`. (Already deferred per CONTEXT `<deferred>` "per-instance lifelines".)
**How to avoid:** UI-SPEC line 168 specifies arrow label includes the tool/agent name (max-width 240px with ellipsis). Confirm in code that `traceEventSummary(event)` or a similar helper feeds the arrow label. **Planner: ensure the arrow label is the FULL `traceLabel(event) + " · " + (event.tool ?? event.remote_agent ?? "")` form, not just `traceLabel`.**
**Warning sign:** Two arrows on the Tool lane have identical labels but represent different tools.

### 8. Event ordering inside a turn bucket
**What goes wrong:** D-74 pairs events by `(turn_index, event_type)` but a single turn can emit multiple events of the same type (e.g., two `tool_call` in one turn). Naive bucketing pairs them in arrival order; if the two protocols call the same two tools but in opposite order, alignment will report two false matched-divergent rows.
**How to avoid:** Within a turn-bucket, prefer pairing by `(event_type, tool/agent name)` first, then fall back to arrival order. Document this in the `alignTraces` function comment so future changes don't regress.
**Warning sign:** A demo with mirror-image tool ordering across MCP and A2A shows red "matched-divergent" rows where the user expected matched-equal.

---

## Risk Landmines (Phase-12-specific)

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| `turn_index` missing on legacy events | LOW (Phase 6 closed; all events carry it per `trace.py:60`) | Diff alignment falls back to `0`, all events bucket together | Default to `0` in coercion; add error state in UI-SPEC line 254 |
| Pure-function diff drift from D-74 contract | MEDIUM | Plans land but matched-divergent fires falsely | Mandatory unit test in `diffAlign.test.ts` covering all 4 statuses + fault-vs-field cause |
| TraceExplorer test file does NOT yet exist | HIGH (verified) | Can't simply "extend tests"; must create | Plan should call out new test file creation as a discrete task |
| CompareTracesPanel test file does NOT yet exist | HIGH (verified) | Same as above | Same |
| Pin survives across runs (state lifecycle) | MEDIUM | Confusion if user runs a new trace and the old pin id no longer exists | When `events` prop changes identity (new trace loaded), reset pin: `useEffect(() => setPinnedEventId(null), [events]);` in `TraceExplorer` |
| `traceEventActor` returns names outside the 5 fixed roles | LOW–MEDIUM | Events fall off all lanes; UI-SPEC says render warning Alert | Map `traceEventActor()` output to one of 5 roles via a lookup table (`agent` → "Orchestrator" or "LLM" depending on agent name); unmapped → "Tool" fallback (default lane) and emit a `console.warn` so QA catches it |
| Scroll-to-pinned-row uses `scrollIntoView` but row is inside collapsed Accordion | MEDIUM | Click pin in Sequence → toggle to List → row exists in DOM but parent Accordion is collapsed, so visually nothing happens | When toggling to List with a pinned id, force-expand the matching tier Accordion. Or: pin row in Tier 0 summary as well as deep tier. Planner's call. |

---

## Code Examples

### Pure-function alignment skeleton

```ts
// frontend/src/components/traces/diffAlign.ts
import type { TraceEvent } from "../../lib/types/api";
import { isTraceFailureEvent } from "../../lib/trace/utils";

export type DiffStatus = "added" | "removed" | "matched-equal" | "matched-divergent";

export interface DiffRow {
  status: DiffStatus;
  left?: TraceEvent;
  right?: TraceEvent;
  turnIndex: number;
  divergenceCause?: "fault" | "field";
  differingFields?: string[];
}

const IGNORE_FIELDS = new Set([
  "timestamp_ms", "started_at", "completed_at", "index",
  "parallel_batch_id", "task_id", "messageId", "contextId",
  "artifactId", "run_id", "lane",
]);

function turnIndexOf(e: TraceEvent): number {
  return Number((e as { turn_index?: unknown }).turn_index ?? 0);
}

function compareFields(l: TraceEvent, r: TraceEvent): { equal: boolean; diffs: string[] } {
  const keys = new Set([...Object.keys(l), ...Object.keys(r)]);
  const diffs: string[] = [];
  for (const k of keys) {
    if (IGNORE_FIELDS.has(k)) continue;
    if (JSON.stringify((l as any)[k]) !== JSON.stringify((r as any)[k])) {
      diffs.push(k);
    }
  }
  return { equal: diffs.length === 0, diffs };
}

export function alignTraces(left: TraceEvent[], right: TraceEvent[]): DiffRow[] {
  const key = (e: TraceEvent) => `${turnIndexOf(e)}::${e.event_type}`;
  const bucket = (events: TraceEvent[]) => {
    const m = new Map<string, TraceEvent[]>();
    for (const e of events) {
      const k = key(e);
      if (!m.has(k)) m.set(k, []);
      m.get(k)!.push(e);
    }
    return m;
  };
  const lb = bucket(left);
  const rb = bucket(right);
  const allKeys = new Set([...lb.keys(), ...rb.keys()]);
  const rows: DiffRow[] = [];
  for (const k of allKeys) {
    const ls = lb.get(k) ?? [];
    const rs = rb.get(k) ?? [];
    const max = Math.max(ls.length, rs.length);
    for (let i = 0; i < max; i++) {
      const l = ls[i];
      const r = rs[i];
      if (l && r) {
        const { equal, diffs } = compareFields(l, r);
        if (equal) {
          rows.push({ status: "matched-equal", left: l, right: r, turnIndex: turnIndexOf(l) });
        } else {
          const faulty = isTraceFailureEvent(l) !== isTraceFailureEvent(r) ||
                         diffs.some(d => d.startsWith("fault_"));
          rows.push({
            status: "matched-divergent", left: l, right: r,
            turnIndex: turnIndexOf(l),
            divergenceCause: faulty ? "fault" : "field",
            differingFields: diffs,
          });
        }
      } else if (l) {
        rows.push({ status: "removed", left: l, turnIndex: turnIndexOf(l) });
      } else if (r) {
        rows.push({ status: "added", right: r, turnIndex: turnIndexOf(r) });
      }
    }
  }
  // D-spec line 212: turn-index asc, then matched-equal, matched-divergent, added/removed
  const order: Record<DiffStatus, number> = {
    "matched-equal": 0, "matched-divergent": 1, "removed": 2, "added": 3,
  };
  rows.sort((a, b) => a.turnIndex - b.turnIndex || order[a.status] - order[b.status]);
  return rows;
}
```

### Lane mapping helper

```ts
// inside SequenceDiagramView.tsx
const LANES = ["User", "Orchestrator", "LLM", "Tool", "Remote Agent"] as const;
type Lane = typeof LANES[number];

function laneOf(event: TraceEvent): Lane {
  const actor = traceEventActor(event); // existing helper
  // Map known actor names to fixed lanes
  if (event.event_type === "user_input" || actor === "user") return "User";
  if (actor === "orchestrator" || actor === "system") return "Orchestrator";
  if (event.event_type.startsWith("llm_") || actor === "llm" || actor === "claude") return "LLM";
  if (event.remote_agent || event.event_type.startsWith("a2a_remote_")) return "Remote Agent";
  if (event.tool || event.server) return "Tool";
  return "Tool"; // safe fallback per Risk Landmine row 6
}
```

(Planner will refine; this is the spine.)

### Toggle button group skeleton (both surfaces)

```tsx
import { ToggleButton, ToggleButtonGroup } from "@mui/material";

<ToggleButtonGroup
  value={viewMode}
  exclusive
  size="small"
  onChange={(_, next) => { if (next) setViewMode(next); }}
  aria-label="View mode"
>
  <ToggleButton value="side-by-side">Side-by-side</ToggleButton>
  <ToggleButton value="diff">Annotated diff</ToggleButton>
</ToggleButtonGroup>
```

(MUI `ToggleButtonGroup` `exclusive` mode + `aria-label` matches UI-SPEC interaction contract lines 200-206.)

---

## State of the Art

| Old Approach | Current Approach | Why |
|--------------|------------------|-----|
| Render diffs with a third-party diff library | Hand-rolled `(turn_index, event_type)` bucketing | D-85 forbids new deps; the alignment is `O(n+m)` simple — diff libraries are overkill for paired structured-event comparison |
| Render sequence diagrams with `mermaid` / `@xyflow/react` | Hand-rolled SVG | D-85 forbids new deps + D-79 explicit; full control over click-to-pin, reduced-motion, role-first labels in ~200-400 LOC |
| Lift selection state to global store (Redux) | Component-local `useState` lifted to nearest common ancestor (`TraceExplorer`) | No state-management library in the project; component-local is the project idiom |

**Deprecated/outdated:** none introduced; all reuse passes.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Safari ≥ 16 renders MUI Chip inside `<foreignObject>` cleanly | §4 | Pinned-chip mis-renders on older Safari; mitigation already documented (rect outline is primary signal) |
| A2 | `traceEventActor()` output set is small enough to enumerate against the 5 lanes without major rewrites | §1, Code Examples | Some events fall off all lanes; UI-SPEC error-state Alert covers this; lane-mapping helper has fallback to "Tool" |
| A3 | `events` array identity changes when a new run is loaded (so `useEffect([events], () => setPinnedEventId(null))` fires) | Risk Landmines row 5 | If `events` is mutated in place, pin won't reset on new run; verify in plan that `events` is recreated, not mutated |
| A4 | `motion` library is not needed at all for v1 (CSS transitions suffice) | Risk Landmines row 5, §4 | If planner finds CSS transitions insufficient for arrow draw-in polish, gating `motion` is allowed but adds surface |

**No critical assumptions blocking planning.** All assumptions are mitigated.

---

## Open Questions

**None blocking.** All decisions D-74..D-85 are LOCKED in `12-CONTEXT.md` and the UI-SPEC has approved checker sign-off (6/6 dimensions PASS).

Three minor planner-discretion items resolved by recommendations above:
1. Diff view filter chrome reuse → recommend NO (defeats D-76 if added).
2. Pinned-event state location → already settled by UI-SPEC (lifted into `TraceExplorer`).
3. `pinnedEventId` type vs `index: number` reality → use `String(event.index)` as the pin value; keep prop name from UI-SPEC.

One soft question for planner:
- **Q:** Should toggling to List view auto-expand the Accordion containing the pinned row?
- **Recommendation:** YES (UX continuity). Implementation: lift `expandedTier: 0 | 1 | 2 | null` into `TraceExplorer`, default null, set to the matching tier when pin propagates from sequence view. Out of strict UI-SPEC scope — flag in plan as Claude's discretion.

---

## Sources

### Primary (HIGH confidence)
- `frontend/src/lib/types/api.ts` — `TraceEvent` schema [VERIFIED: codebase read]
- `frontend/src/features/compare/CompareTracesPanel.tsx` — current dual-column structure, sync-scroll pattern lines 27-43, mode-selector + DiscoveryPhasePanel + dual-column body lines 64-162 [VERIFIED]
- `frontend/src/components/traces/TraceExplorer.tsx` — current 3-tier accordion structure, filter state, header pattern lines 91-222 [VERIFIED]
- `frontend/src/lib/trace/utils.ts` — `traceLabel`, `traceEventActor`, `traceEventProtocol`, `isTraceFailureEvent`, `traceEventTone` [VERIFIED]
- `frontend/src/lib/trace/eventColors.ts` — `failureTagColor`, `getProtocolColor`, `toneColor`, `eventBorderColor` [VERIFIED]
- `frontend/src/lib/trace/JsonTree.tsx` — Phase-11-extracted, reusable [VERIFIED]
- `frontend/src/app/theme.ts` — palette, MuiCard override [VERIFIED]
- `src/a2a_vs_mcp/trace.py` line 60 — `turn_index` emitted by backend [VERIFIED via grep]
- `frontend/src/features/race/components/RaceLaneCard.tsx` line 42 — `useMediaQuery` idiom [VERIFIED]
- `frontend/src/features/race/components/RaceLaneCard.test.tsx` lines 8, 187-188 — `vi.mock("@mui/material/useMediaQuery")` test pattern [VERIFIED]
- `frontend/src/features/race/RacePage.a11y.test.tsx` line 113-114 — `mockMatchMedia` helper for prefers-reduced-motion [VERIFIED]
- `frontend/src/components/traces/__tests__/DiscoveryPhasePanel.test.tsx` — `ThemeProvider + CssBaseline` test wrapper pattern [VERIFIED]
- `.planning/phases/12-comparison-visualization-upgrades/12-CONTEXT.md` — D-74..D-85 [VERIFIED]
- `.planning/phases/12-comparison-visualization-upgrades/12-UI-SPEC.md` — approved component contract [VERIFIED]
- `.planning/codebase/CONVENTIONS.md`, `TESTING.md` — naming + test conventions [VERIFIED]

### Secondary (MEDIUM confidence)
- MDN `<foreignObject>` notes — long-standing browser quirks documented [CITED: developer.mozilla.org]

### Tertiary (LOW confidence)
- Safari `<foreignObject>` version threshold for clean MUI rendering — approximate (Safari ≥ 16); QA verification required [ASSUMED]

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed, all helpers already shipped
- Architecture / mount integration: HIGH — both files read line-by-line, integration insertion points verified
- Diff alignment algorithm: HIGH — pure function with clear contract from D-74 + UI-SPEC line 210-212
- SVG sequence diagram patterns: HIGH for technique, MEDIUM for `<foreignObject>` Safari threshold
- `prefers-reduced-motion` pattern: HIGH — Phase 8 baseline + Phase 11 patterns verified
- Test scaffolding: HIGH — DiscoveryPhasePanel test pattern is the direct precedent
- Pitfalls: HIGH — all 8 grounded in actual code or schema reads

**Research date:** 2026-05-01
**Valid until:** 2026-06-01 (30 days; stable frontend, decisions locked, no upstream library churn expected)

---

## RESEARCH COMPLETE

VIZ-01 + VIZ-02 fully scoped from D-74..D-85 + UI-SPEC. Two net-new components in `frontend/src/components/traces/` (plus pure `diffAlign.ts`), MUI-only, no new deps. All 8 pitfalls and 7 risks have concrete mitigations. Test patterns have direct in-repo precedents. Planner has everything needed to split into 3 plans without further input.
