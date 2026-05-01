---
phase: 12-comparison-visualization-upgrades
plan: "03"
subsystem: frontend/traces
tags: [viz-01, annotated-diff, compare-panel, toggle, vitest, typescript, mui]
dependency_graph:
  requires:
    - frontend/src/components/traces/diffAlign.ts (alignTraces, DiffRow, DiffStatus — Plan 12-01 locked contract)
    - frontend/src/lib/trace/utils.ts (traceLabel, traceEventProtocol)
    - frontend/src/lib/trace/eventColors.ts (failureTagColor, toneColor, getProtocolColor)
    - frontend/src/lib/trace/JsonTree.tsx (expandable payload)
    - frontend/src/lib/types/api.ts (TraceEvent, RunResult)
    - frontend/src/app/theme.ts (appTheme for tests)
  provides:
    - frontend/src/components/traces/AnnotatedDiffView.tsx (VIZ-01 annotated diff component)
    - frontend/src/features/compare/CompareTracesPanel.tsx (augmented with viewMode toggle)
    - frontend/src/components/traces/__tests__/AnnotatedDiffView.test.tsx (9 vitest cases)
    - frontend/src/features/compare/__tests__/CompareTracesPanel.test.tsx (3 vitest cases)
  affects:
    - All mount sites of CompareTracesPanel (currently compare page)
tech_stack:
  added: []
  patterns:
    - MUI ToggleButtonGroup for in-place view mode switching (D-75 pattern)
    - CSS grid layout (gridTemplateColumns: 28px 1fr 28px 1fr) for diff gutter
    - EMPTY_EVENTS module-level stable reference (W-6 useMemo stability)
    - Gutter chip placement in exactly one column per row (W-3 mitigation)
    - failureTagColor/toneColor as single source for diff row tints and borders (Phase 8 contract)
key_files:
  created:
    - frontend/src/components/traces/AnnotatedDiffView.tsx (324 LOC)
    - frontend/src/components/traces/__tests__/AnnotatedDiffView.test.tsx (9 cases)
    - frontend/src/features/compare/__tests__/CompareTracesPanel.test.tsx (3 cases)
  modified:
    - frontend/src/features/compare/CompareTracesPanel.tsx (toggle + AnnotatedDiffView conditional)
decisions:
  - "EMPTY_EVENTS exported as const from AnnotatedDiffView.tsx and re-declared module-level in CompareTracesPanel.tsx (W-6: avoids inline [] defeating useMemo)"
  - "Gutter chip rendered in exactly ONE gutter per row: removed/matched-divergent → Gutter A; added → Gutter B (W-3)"
  - "getByLabelText used for MUI Tooltip assertions — MUI renders title as aria-label on child clone element (not via title attribute)"
  - "getAllByRole('group') used for View mode toggle — CompareTracesPanel + each TraceExplorer instance all share aria-label='View mode'"
  - "Toggle insertion at line 131 in post-edit CompareTracesPanel.tsx (Stack direction row, after Mode A/B Grid, before DiscoveryPhasePanel)"
metrics:
  duration: "~7 minutes"
  completed_date: "2026-05-01"
  tasks_completed: 4
  tasks_total: 4
  files_created: 3
  files_modified: 1
---

# Phase 12 Plan 03: AnnotatedDiffView + CompareTracesPanel Toggle — Summary

VIZ-01 fully delivered: new AnnotatedDiffView component consuming alignTraces from Plan 12-01,
mounted via Side-by-side|Annotated diff ToggleButtonGroup on CompareTracesPanel (D-75), with 12
new vitest cases covering all 4 DiffStatus visuals, fault-cause override, protocol coloring,
empty state, toggle ARIA, and DiscoveryPhasePanel preservation.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Implement AnnotatedDiffView component | 4be18b6 | frontend/src/components/traces/AnnotatedDiffView.tsx |
| 2 | Mount viewMode toggle on CompareTracesPanel | 46a9cb4 | frontend/src/features/compare/CompareTracesPanel.tsx |
| 3 | Vitest coverage for AnnotatedDiffView | 6311245 | frontend/src/components/traces/__tests__/AnnotatedDiffView.test.tsx |
| 4 | Vitest coverage for CompareTracesPanel toggle | 33f9621 | frontend/src/features/compare/__tests__/CompareTracesPanel.test.tsx |

## AnnotatedDiffView Final LOC Count

**324 lines** (within expected range for full-fidelity component with W-3 gutter placement logic,
JSDoc, and module-level helpers).

## Tint + Border Tokens Used Per Status

| DiffStatus | Background | Border | Gutter chip colors |
|------------|------------|--------|--------------------|
| added | `failureTagColor.recovered.bg` (#e8f5e9) | none | bg: `failureTagColor.recovered.bg`, color: `failureTagColor.recovered.text` |
| removed | `failureTagColor.gave_up.bg` (#fce4ec) | none | bg: `failureTagColor.gave_up.bg`, color: `failureTagColor.gave_up.text` |
| matched-divergent (field) | none | `2px solid toneColor.warning` (#ed6c02) | bg: transparent |
| matched-divergent (fault) | none | `2px solid failureTagColor.kept_going_to_failure.text` (#bf360c) | bg: transparent |
| matched-equal | none | none | no chip |

## Vitest Case Names and Counts

**AnnotatedDiffView.test.tsx (9 cases):**
1. `renders empty-state copy when both sides empty`
2. `renders one row per DiffRow across all 4 statuses (D-76)`
3. `shows '+' glyph on added rows`
4. `shows '−' glyph on removed rows`
5. `shows '≠' glyph and field tooltip on matched-divergent (cause=field) rows`
6. `uses fault override copy on matched-divergent (cause=fault) rows`
7. `renders default protocol headers with chips showing event counts`
8. `uses role-first label via traceLabel for row text`
9. `overrides column header labels when leftProtocolLabel and rightProtocolLabel are provided`

**CompareTracesPanel.test.tsx (3 cases):**
1. `renders the View mode toggle with both buttons and Side-by-side selected by default`
2. `swaps to AnnotatedDiffView when Annotated diff is clicked`
3. `preserves DiscoveryPhasePanel above the toggle in both view modes`

**Total new tests:** 12
**Total suite:** 324 (312 prior baseline + 12 new) — all passing

## Toggle Insertion-Point Line Numbers (Post-Edit CompareTracesPanel.tsx)

- Import `ToggleButton`, `ToggleButtonGroup` added at lines 10-11 in `@mui/material` import
- `AnnotatedDiffView` import added at line 15
- `EMPTY_EVENTS` constant at line 23 (module-level, before component)
- `CompareViewMode` type at line 26
- `viewMode` state at line 38
- Toggle JSX `<Stack direction="row" justifyContent="flex-end">` inserted at **line 131** (after Mode A/B Grid closing tag, before DiscoveryPhasePanel)
- Conditional body at line 142 (`viewMode === "side-by-side"` guard wrapping original Grid container)

## Forbidden Import Verification

```
grep -c "@xyflow" frontend/src/components/traces/AnnotatedDiffView.tsx → 0  (D-85 PASS)
grep -cE 'from "motion|framer-motion' frontend/src/components/traces/AnnotatedDiffView.tsx → 0  (D-85 PASS)
```

## D-Number Compliance Confirmation

| Decision | Status |
|----------|--------|
| D-75: In-place toggle on CompareTracesPanel (Side-by-side default) | PASS |
| D-76: Diff scope = all event_types, no pre-filter | PASS — alignTraces called with raw trace arrays |
| D-77: Tint + gutter chip per status | PASS — all 4 statuses with correct failureTagColor tokens |
| D-78: Role-first labels via traceLabel | PASS — `traceLabel(left ?? right)` for every row |
| D-84: Reuse existing theme tokens, no new colors | PASS — failureTagColor, toneColor, getProtocolColor only |
| D-85: No @xyflow/react, no motion imports | PASS — verified by grep |

## Deviations from Plan

### Minor implementation adjustments within Claude's discretion

**1. [Rule 1 - Bug] Tooltip assertion uses getByLabelText, not getByTitle**
- **Found during:** Task 3 test execution
- **Issue:** MUI Tooltip renders its `title` prop as `aria-label` on the cloned child element — not as a `title` HTML attribute. `getByTitle` found no match.
- **Fix:** Changed assertions to `screen.getByLabelText(...)` which matches the `aria-label`.
- **Files modified:** `frontend/src/components/traces/__tests__/AnnotatedDiffView.test.tsx`
- **Commit:** 6311245

**2. [Rule 1 - Bug] Test used getAllByRole("group") for View mode toggle**
- **Found during:** Task 4 test execution
- **Issue:** CompareTracesPanel renders two TraceExplorer columns, each with its own "View mode" ToggleButtonGroup (from Plan 12-02). `getByRole("group", { name: /view mode/i })` found multiple matches.
- **Fix:** Changed to `getAllByRole` and used button-specific assertions (`getByRole("button", { name: /side-by-side/i })`) to target the CompareTracesPanel toggle uniquely.
- **Files modified:** `frontend/src/features/compare/__tests__/CompareTracesPanel.test.tsx`
- **Commit:** 33f9621

**3. [Rule 1 - Bug] fault fixture used wrong event_type pairing**
- **Found during:** Task 3 — fault tooltip test
- **Issue:** Fixture used `event_type: "tool_error"` for both sides — `isTraceFailureEvent` returns true for both, so `isTraceFailureEvent(l) !== isTraceFailureEvent(r)` was false. divergenceCause remained 'field'.
- **Fix:** Changed to same `event_type: "tool_call"` for both sides but added `fault_observed: true` to left side — the `fault_` prefix check in alignTraces correctly classifies divergenceCause='fault'.
- **Files modified:** `frontend/src/components/traces/__tests__/AnnotatedDiffView.test.tsx`
- **Commit:** 6311245

## Known Stubs

None. All data flows from `leftEvents`/`rightEvents` props through `alignTraces` into rendered DOM rows. No hardcoded empty arrays in render path, no placeholder text (empty state uses locked copy, not stubs).

## Threat Flags

None. This plan introduces no new network endpoints, auth paths, file access patterns, or schema changes. AnnotatedDiffView is a pure client-side rendering transform of already-loaded trace data.

## Self-Check

### Files exist:
- `frontend/src/components/traces/AnnotatedDiffView.tsx` — EXISTS (324 LOC)
- `frontend/src/components/traces/__tests__/AnnotatedDiffView.test.tsx` — EXISTS (9 cases)
- `frontend/src/features/compare/__tests__/CompareTracesPanel.test.tsx` — EXISTS (3 cases)
- `frontend/src/features/compare/CompareTracesPanel.tsx` — MODIFIED (toggle added)

### Commits exist:
- `4be18b6` — feat(12-03): implement AnnotatedDiffView component
- `46a9cb4` — feat(12-03): add viewMode toggle to CompareTracesPanel
- `6311245` — test(12-03): vitest coverage for AnnotatedDiffView (9 cases)
- `33f9621` — test(12-03): vitest coverage for CompareTracesPanel toggle (3 cases)

### Test results:
- 324/324 tests passing (vitest run --reporter=dot)
- TypeScript: 0 errors (tsc --noEmit)

## Self-Check: PASSED
