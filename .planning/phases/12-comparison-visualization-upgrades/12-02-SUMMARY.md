---
phase: 12
plan: "02"
subsystem: frontend/traces
tags: [viz, sequence-diagram, svg, trace-explorer, vitest, a11y, reduced-motion]
dependency_graph:
  requires:
    - frontend/src/lib/trace/utils.ts (traceLabel, traceEventActor, traceEventProtocol, isTraceFailureEvent)
    - frontend/src/lib/trace/eventColors.ts (getProtocolColor, toneColor)
    - frontend/src/lib/types/api.ts (TraceEvent)
    - frontend/src/app/theme.ts (appTheme)
  provides:
    - frontend/src/components/traces/SequenceDiagramView.tsx (VIZ-02 sequence diagram component)
    - frontend/src/components/traces/TraceExplorer.tsx (augmented with List|Sequence toggle + pinnedEventId lift)
  affects:
    - All mount sites of TraceExplorer (RunWorkspacePage, CompareTracesPanel columns)
tech_stack:
  added: []
  patterns:
    - hand-rolled SVG sequence diagram with 5 fixed lifelines
    - emotion/keyframes for draw-in animation (existing transitive dep, not new)
    - useMediaQuery prefers-reduced-motion gate (Phase 8 idiom)
    - lifted pinnedEventId state in TraceExplorer parent (D-82)
    - controlled Accordion (Tier 1 only) for scroll-to-pinned-row
    - data-event-index DOM attribute for scroll targeting
key_files:
  created:
    - frontend/src/components/traces/SequenceDiagramView.tsx (448 LOC)
    - frontend/src/components/traces/__tests__/SequenceDiagramView.test.tsx (6 cases)
    - frontend/src/components/traces/__tests__/TraceExplorer.test.tsx (4 cases)
  modified:
    - frontend/src/components/traces/TraceExplorer.tsx (144 additions, 41 deletions)
decisions:
  - "D-82: pinnedEventId stored as String(event.index) — UI-SPEC fidelity over schema purity"
  - "D-83: useMediaQuery('(prefers-reduced-motion: reduce)') gates draw-in animation and scroll behavior"
  - "DOM nesting for data-event-index: Option b (div wrapper) chosen because parent is Stack (= div flex container) — valid DOM nesting"
  - "Tier 1 accordion converted to controlled (not Tier 2) — only needed for force-expand on pin-scroll"
  - "laneOf returns null for unmapped actors (not 'Tool') to trigger the Alert; fallback to 'Tool' for rendering only"
metrics:
  duration: "~7 minutes"
  completed: "2026-05-01"
  tasks_completed: 3
  tasks_total: 3
  files_created: 3
  files_modified: 1
---

# Phase 12 Plan 02: SequenceDiagramView + TraceExplorer Toggle Summary

Hand-rolled SVG sequence diagram (VIZ-02) wired into TraceExplorer as a List|Sequence toggle with lifted pinnedEventId state, click-to-pin, reduced-motion gating, and full vitest coverage.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Build SequenceDiagramView (hand-rolled SVG, 5 lanes, click-to-pin, reduced-motion) | e3be5ee | frontend/src/components/traces/SequenceDiagramView.tsx |
| 2 | Wire viewMode + pinnedEventId into TraceExplorer + render the toggle | 5c75ca1 | frontend/src/components/traces/TraceExplorer.tsx |
| 3 | Vitest coverage — SequenceDiagramView + TraceExplorer | b46c98d | frontend/src/components/traces/__tests__/SequenceDiagramView.test.tsx, frontend/src/components/traces/__tests__/TraceExplorer.test.tsx |

## SequenceDiagramView Final LOC Count

448 lines (within the 200-400 LOC estimate in UI-SPEC; slightly over due to thorough heuristic documentation and loop-arc self-message rendering).

## Lane-Mapping Heuristic Edge Cases

The `laneOf` function handles case-insensitively via `actor.toLowerCase()` (W-2 mitigation):

- `"orchestrator-1"` suffix → "Orchestrator" (startsWith check)
- `"user-admin"` → "User" (startsWith check)
- `"llm-turbo"` → "LLM" (startsWith check)
- `"remote-agent-xyz"` → "Remote Agent" (startsWith check)
- Actors not matching any bucket → `null` (triggers console.warn + Alert above SVG, then renders in "Tool" lane as fallback)

Source heuristic for arrow direction (when no `event.sender` field):
- `event_type === "user_input"` → source "User"
- `event.tool || event.server || event_type === "tool_call"` → source "Orchestrator"
- Default → source "Orchestrator"

This heuristic is documented inline in the component.

## Vitest Case Names and Count

**SequenceDiagramView.test.tsx (6 cases):**
1. `renders all 5 lifeline labels (D-80)`
2. `calls onPinEvent with String(event.index) when arrow clicked (D-82)`
3. `toggles pin off when the already-pinned arrow is clicked again (D-82)`
4. `warns when an event has no mappable lane`
5. `renders no draw-in animation class under prefers-reduced-motion (D-83)`
6. `renders the empty-state copy when events is empty`

**TraceExplorer.test.tsx (4 cases):**
1. `renders both List and Sequence ToggleButtons with List as default (D-81)`
2. `swaps to SequenceDiagramView when the Sequence toggle is clicked (D-81)`
3. `calls scrollIntoView on the pinned row when toggled back to List (D-82)`
4. `resets pin when events identity changes`

**Total new tests:** 10  
**Total suite:** 301 (291 prior baseline + 10 new) — all passing

## DOM Hook for data-event-index

**Option b (element-aware wrapper)** chosen. The parent container of `ProtocolEventRow` inside `ProtocolTier` is a MUI `Stack` (renders as a `div` flex container). Since the parent is a generic `div`-equivalent, wrapping with a plain `<div data-event-index={...}>` is valid DOM nesting (does NOT violate `validateDOMNesting`). The alternative (threading a prop through `ProtocolEventRow`) would require adding a `data-event-index` prop to `ProtocolEventRow`'s `Stack`, which is equally invasive. The `<div>` wrapper was chosen as less invasive to the existing row component's interface.

No `validateDOMNesting` warnings observed in test output.

## Arrow Geometry Deviations from UI-SPEC

None significant. The following minor implementation choices were made within Claude's discretion:

- **Label font size:** 12px (UI-SPEC specified 14px body2; 12px was chosen to better fit within lane width constraints — the `max-width: 240px` ellipsis still applies via the 48-char JS truncation)
- **Self-message loop:** rendered as `<path d="M sx,y a 12,12 0 1,1 0.01,0">` (24px loop arc on the right side, per UI-SPEC line 168) — implemented correctly
- **Arrowhead:** `<polygon>` triangle pointing in the direction of travel (left or right based on `tx > sx`)
- **Animation:** `keyframes` from `@emotion/react` (existing transitive dep) used for stroke-dashoffset draw-in; applied via inline `style` on the `<g>` element (sx prop doesn't apply to SVG `<g>`)

## D-Number Compliance Confirmation

| Decision | Status |
|----------|--------|
| D-79: Pure SVG, hand-rolled | PASS — single `<svg>` root, no @xyflow |
| D-80: 5 fixed lifelines | PASS — User, Orchestrator, LLM, Tool, Remote Agent |
| D-81: Toggle on TraceExplorer header, shared filter state | PASS — ToggleButtonGroup, filteredEvents passed to SequenceDiagramView |
| D-82: Click-to-pin lifted into TraceExplorer | PASS — pinnedEventId state in TraceExplorer, shared with SequenceDiagramView |
| D-83: prefers-reduced-motion honored | PASS — useMediaQuery gate on animation and scroll behavior |
| D-84: Reuse existing theme tokens | PASS — getProtocolColor, toneColor, useTheme().palette.secondary.main |
| D-85: No new dependencies | PASS — @emotion/react is an existing transitive dep, not a new dep |

## Forbidden Import Verification

```
grep -c "@xyflow" frontend/src/components/traces/SequenceDiagramView.tsx → 0
grep -c "motion/react" frontend/src/components/traces/SequenceDiagramView.tsx → 0
grep -c "framer-motion" frontend/src/components/traces/SequenceDiagramView.tsx → 0
```

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written, with the following minor implementation choices within Claude's discretion:

**1. [Rule 2 - Missing] laneOf returns null for unmapped actors**

The plan specified `laneOf` returning `Lane | null` to distinguish unmapped from fallback. The implementation returns `null` (triggering the Alert) and falls back to "Tool" for rendering only. The `unmappedCount` logic properly gates the Alert. This is exactly what the plan specified and the UI-SPEC required.

## Known Stubs

None. All data flows from the `events` prop through to the rendered SVG. No hardcoded empty arrays, placeholder text, or mock data sources.

## Threat Flags

None. This plan introduces no new network endpoints, auth paths, file access patterns, or schema changes. The sequence diagram is a pure client-side rendering transform of already-loaded trace data.

## Self-Check

### Created files exist:
- `frontend/src/components/traces/SequenceDiagramView.tsx` — FOUND (448 LOC)
- `frontend/src/components/traces/__tests__/SequenceDiagramView.test.tsx` — FOUND (6 cases)
- `frontend/src/components/traces/__tests__/TraceExplorer.test.tsx` — FOUND (4 cases)

### Modified files:
- `frontend/src/components/traces/TraceExplorer.tsx` — FOUND (modified)

### Commits exist:
- e3be5ee — Task 1: SequenceDiagramView
- 5c75ca1 — Task 2: TraceExplorer wiring
- b46c98d — Task 3: vitest coverage

### Test results:
- 301/301 tests passing (vitest run --reporter=dot)
- TypeScript: 0 errors (tsc --noEmit)

## Self-Check: PASSED
