---
phase: 04-comparison-ui
plan: 04
subsystem: frontend/compare
tags: [traces, side-by-side, scroll-sync, compare-page]
dependency_graph:
  requires: [eventColors.ts, TraceExplorer]
  provides: [CompareTracesPanel]
  affects: []
tech_stack:
  added: []
  patterns: [scroll-sync-mutex, dual-panel-comparison]
key_files:
  created:
    - frontend/src/features/compare/CompareTracesPanel.tsx
  modified:
    - frontend/src/features/compare/ComparePage.tsx
decisions:
  - "D-07: CompareTracesPanel is standalone, imported only by ComparePage"
  - "D-08: Two mode selectors default to first two available modes"
  - "D-09: Scroll sync uses useRef mutex + requestAnimationFrame to prevent infinite loop"
  - "Kept ProtocolEnvelopeDrawer and envelopeEvent state for future event selection pass-through"
metrics:
  duration: 2m 01s
  completed: 2026-04-26T19:38:30Z
  tasks_completed: 2
  tasks_total: 2
  files_changed: 2
---

# Phase 4 Plan 4: CompareTracesPanel with Synchronized Dual TraceExplorer Summary

Two side-by-side TraceExplorer instances with Mode A/B selectors and scroll-sync mutex guard, integrated into ComparePage replacing the old MiniEventRow/ModeColumn grid.

## What Was Done

### Task 1: Create CompareTracesPanel component
- Created `frontend/src/features/compare/CompareTracesPanel.tsx` with:
  - Mode A / Mode B dropdown selectors using MUI FormControl/Select with protocol-colored labels via `getProtocolColor`
  - Two TraceExplorer instances in a responsive Grid (xs:12, md:6)
  - Synchronized scrolling: `syncing` useRef mutex guard prevents infinite scroll loops; `requestAnimationFrame` defers mutex release
  - maxHeight: 600 on outer scroll Box containers (not on TraceExplorer internally)
  - Fallback text when mode not yet selected
- **Commit:** 6b6f611

### Task 2: Integrate CompareTracesPanel into ComparePage
- Removed `MiniEventRow` function (57 lines) and `ModeColumn` function (56 lines)
- Removed `MODE_ICONS`, `BASELINE_ICON`, and `getModeIcon` helper (only used by deleted components)
- Removed unused imports: `HubOutlinedIcon`, `PrecisionManufacturingOutlinedIcon`, `RouteOutlinedIcon`, `AccountTreeOutlinedIcon`, `Chip`, `Tooltip`, `Box`, `getProtocolColor`, `eventBorderColor`, `isA2AEvent`, `isTraceFailureEvent`, `traceEventProtocol`, `traceEventTone`, `traceLabel`
- Kept `CompareArrowsOutlinedIcon` (used in report selector)
- Kept `ProtocolEnvelopeDrawer` and `envelopeEvent` state (renders nothing when null; future enhancement can wire event selection)
- Replaced ModeColumn grid with `<CompareTracesPanel results={orderedResults} />`
- Removed `cols` variable (no longer needed)
- Updated loading skeleton from 4 columns (xs:12, sm:6, xl:3) to 2 columns (xs:12, md:6)
- Net change: -150 lines (4 added, 150 removed)
- **Commit:** 8575150

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Cleanup] Removed unused Box import**
- **Found during:** Task 2 post-commit review
- **Issue:** `Box` was imported in ComparePage but no longer used after ModeColumn removal
- **Fix:** Removed from MUI import block
- **Files modified:** frontend/src/features/compare/ComparePage.tsx
- **Commit:** included in 8575150

## Verification Results

| Check | Result |
|-------|--------|
| `npx tsc --noEmit` | PASS (exit 0) |
| `npm run build` | PASS (built in 2.23s) |
| CompareTracesPanel count in ComparePage | 2 (import + usage) |
| ModeColumn count in ComparePage | 0 |
| MiniEventRow count in ComparePage | 0 |

## Known Stubs

None. Both mode selectors are wired to state, TraceExplorer receives real trace data from results.

## Self-Check: PASSED

- [x] frontend/src/features/compare/CompareTracesPanel.tsx exists
- [x] frontend/src/features/compare/ComparePage.tsx modified
- [x] Commit 6b6f611 exists in git log
- [x] Commit 8575150 exists in git log
