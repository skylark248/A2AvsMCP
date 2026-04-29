---
phase: 08-race-page-ui-visual-contract
plan: "05"
subsystem: frontend/race-components
tags: [frontend, mui, css-grid, slider, accessibility, tdd]
dependency_graph:
  requires:
    - 08-01  # failureTagColor, FailureTag, RaceLane types
    - 08-02  # RacePage shell (heatmap-slot, scrubber-slot slots)
  provides:
    - HeatmapScaffold  # consumed by Plan 06 (RacePage composition)
    - ReplayScrubber   # consumed by Plan 06 (RacePage scrubber-slot)
  affects:
    - frontend/src/features/race/components/
tech_stack:
  added:
    - "@mui/utils visuallyHidden (inline style for sr-only channel 4)"
    - "MUI Slider component (first usage in this codebase)"
    - "CSS Grid with role=grid/gridcell (first grid heatmap in codebase)"
  patterns:
    - "UIRACE-04 4-channel cell encoding: bg color + visible icon + visible fraction + sr-only tag-name"
    - "TDD RED/GREEN on both components"
    - "visuallyHidden applied as inline style (not sx) for jsdom-testable AT-accessible hiding"
key_files:
  created:
    - frontend/src/features/race/components/HeatmapScaffold.tsx
    - frontend/src/features/race/components/HeatmapScaffold.test.tsx
    - frontend/src/features/race/components/ReplayScrubber.tsx
    - frontend/src/features/race/components/ReplayScrubber.test.tsx
  modified: []
decisions:
  - "visuallyHidden applied as HTML inline style attribute (not MUI sx) so jsdom getComputedStyle and AT tooling can read position:absolute/width:1px directly — sx produces className-based styles that are opaque in jsdom"
  - "Icon cast to ComponentType<SvgIconLike> to allow fontSize prop — failureTagColor.Icon is typed as ComponentType with no props; SvgIconLike interface bridges MUI icon shape without importing SvgIconProps"
  - "toSingleValue helper with ?? 0 fallback in ReplayScrubber prevents undefined array-index TypeScript error while maintaining correct runtime behavior (Slider always passes a number)"
metrics:
  duration: "~30 minutes"
  completed_date: "2026-04-29"
  tasks_completed: 2
  files_created: 4
  files_modified: 0
  tests_added: 28  # 19 HeatmapScaffold + 9 ReplayScrubber
---

# Phase 08 Plan 05: HeatmapScaffold + ReplayScrubber Summary

**One-liner:** CSS Grid 4×3 heatmap with UIRACE-04 4-channel cell encoding (color/icon/fraction/sr-only via @mui/utils visuallyHidden) and MUI Slider scrubber with 200ms throttled aria-live announcements flushed on release.

## Files Created

| File | Purpose |
|------|---------|
| `frontend/src/features/race/components/HeatmapScaffold.tsx` | CSS Grid heatmap, 4×3 (HardnessType × RaceLane), 4-channel encoding, empty-state overlay |
| `frontend/src/features/race/components/HeatmapScaffold.test.tsx` | 19 tests: empty state, 4-channel UIRACE-04, structure |
| `frontend/src/features/race/components/ReplayScrubber.tsx` | MUI Slider with throttled aria-live (D-49), 40px hit area |
| `frontend/src/features/race/components/ReplayScrubber.test.tsx` | 9 tests: rendering, onScrub callback, throttle behavior |

## HeatmapScaffold — Props Shape

```typescript
export type HardnessType =
  | "long_chain" | "rate_pressure"
  | "schema_variance" | "multi_source_synthesis";

export interface HeatmapCell {
  tag: FailureTag;
  recoveryFraction: string;  // e.g. "12/15" — visible primary text channel
}

export type HeatmapCells = Partial<
  Record<HardnessType, Partial<Record<RaceLane, HeatmapCell>>>
>;

export function HeatmapScaffold({ cells }: { cells: HeatmapCells })
```

## UIRACE-04 4-Channel Cell Encoding

Each populated cell carries all four channels simultaneously:

| Channel | Content | Visibility |
|---------|---------|------------|
| 1 (color) | `failureTagColor[tag].bg` → `backgroundColor` | Visual only |
| 2 (icon) | `failureTagColor[tag].Icon` rendered inline, `data-testid="heatmap-cell-icon"` | Visual (aria-hidden) |
| 3 (fraction) | `cell.recoveryFraction` text (e.g. "12/15") | Visual primary text |
| 4 (sr-only tag-name) | `failureTagColor[tag].label` inside `<span style={visuallyHidden}>` | Screen-reader only |

Color is **never** the sole channel. SR users hear: icon + fraction + tag-name (via channel 4).

The `visuallyHidden` object from `@mui/utils` is applied as an **inline style** (not `sx`) to ensure `position: absolute` and `width: 1px` are accessible in jsdom and AT inspection.

## Empty-State Contract (D-47)

- The CSS Grid scaffold (role=grid, 12 cells) **never unmounts** in empty state.
- Muted neutral cells render in place (`bgcolor: "action.hover"`).
- An `position: absolute` overlay appears over the grid with:
  - Heading: **"No runs yet"** (verbatim)
  - Body: **"Launch a race to populate the heatmap."** (verbatim)
- `data-testid="heatmap-empty-overlay"` for testing.
- When any cell is populated, the overlay is removed from the DOM (`isEmpty` condition).

## Accessibility Constraints Satisfied

| Constraint | Implementation |
|-----------|----------------|
| `role="grid"` + `aria-label="Hardness vs Failure Heatmap"` | Outer Box |
| `role="gridcell"` + `tabIndex={0}` | Each cell Box |
| `borderRadius: 0` (cells touch, UIRACE-03) | Cell sx |
| `minHeight: 44` (WCAG 2.5.5 touch target, UIRACE-06) | Cell sx + gridTemplateRows minmax(44px, 1fr) |
| Focus-visible: `3px solid #17475f`, offset 2px | `&:focus-visible` sx |
| High-contrast widen: `4px solid #17475f` | `@media (prefers-contrast: more)` nested in sx |
| Zero `dangerouslySetInnerHTML` (T-08-08) | React text children only |

## ReplayScrubber — Props Shape

```typescript
export function ReplayScrubber({
  value,      // current turn index (controlled)
  max,        // total turns
  onScrub,    // callback fired on every change
}: {
  value: number;
  max: number;
  onScrub: (turnIndex: number) => void;
})
```

## Throttle Behavior (D-49)

- **During drag (onChange):** `ANNOUNCE_THROTTLE_MS = 200`. Only the first event in any 200ms window updates the aria-live text. Subsequent events within the window are recorded as `pendingValue` but do not trigger a state update.
- **On release (onChangeCommitted):** Final value always announced regardless of throttle — `lastAnnounceRef` and `pendingValueRef` both reset.
- **On prop change:** `useEffect([value, max])` keeps the announce box in sync when the parent re-renders with a new `value` (e.g., page load or programmatic seek).
- **Announcement format:** `"Turn ${next} of ${max}"` — aria-live="polite" Box with `data-testid="race-scrubber-announce"`.
- **Min hit area:** Container Box has `minHeight: 40` (UI-SPEC line 50).
- **Reduced motion:** `@media (prefers-reduced-motion: reduce)` sets `transitionDuration: "0ms !important"` on Slider and thumb/track subelements (UI-SPEC line 128).

## Plan 06 Composition Notes

Plan 06 (RacePage full composition) will:
- Drop `<HeatmapScaffold cells={...} />` into the `data-testid="race-heatmap-slot"` container.
- Drop `<ReplayScrubber value={...} max={...} onScrub={...} />` into the `data-testid="race-scrubber-slot"` container (replay mode only, per D-49 gate).
- Wire `cells` from the heatmap data hook (Phase 9 HEAT-01/HEAT-02).
- Wire `value/max/onScrub` from `useRaceReplay` output (Phase 9 HEAT-03).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] visuallyHidden applied as inline style instead of sx**
- **Found during:** Task 1 GREEN phase (test failures)
- **Issue:** MUI `sx` prop applies styles via CSS class injection. In jsdom (vitest), injected CSS classes are not reflected in `getComputedStyle` or `element.getAttribute("style")`. The test assertion `style.match(/position:\s*absolute/)` failed because sx styles are opaque to jsdom.
- **Fix:** Applied `visuallyHidden` as `style={visuallyHidden as React.CSSProperties}` on a native `<span>` instead of `<Box sx={visuallyHidden}>`. This produces a real HTML `style` attribute that AT tooling and jsdom can inspect directly.
- **Files modified:** `HeatmapScaffold.tsx`
- **Commits:** `caba3a0`, `f104f75`

**2. [Rule 1 - Bug] TypeScript build errors — Icon typing + array undefined**
- **Found during:** Build verification after GREEN commits
- **Issue 1:** `failureTagColor.Icon` is typed as `ComponentType` (no props). Passing `fontSize="small"` caused TS2769 overload mismatch.
- **Fix 1:** Added local `SvgIconLike` interface; cast `cfg.Icon` to `ComponentType<SvgIconLike>`.
- **Issue 2:** `raw[0]` when `raw` is `number[]` returns `number | undefined`; TypeScript rejects assigning to `number`.
- **Fix 2:** Extracted `toSingleValue` helper with `?? 0` fallback.
- **Files modified:** `HeatmapScaffold.tsx`, `ReplayScrubber.tsx`
- **Commit:** `f104f75`

## TDD Gate Compliance

Both components followed strict RED/GREEN:
- RED: test commit before implementation (`6d408b7` Heatmap, `809dbb3` Scrubber)
- GREEN: implementation commit after tests pass (`caba3a0` Heatmap, `19e2305` Scrubber)
- REFACTOR: build-error fixes committed separately (`f104f75`)

## Threat Surface Scan

No new network endpoints, auth paths, file access patterns, or schema changes introduced.
`cells` prop content renders via React text children (auto-escaped). Slider value bounded [0, max] by MUI Slider primitive. T-08-08 and T-08-12 mitigations confirmed present.

## Self-Check

Files exist:
- `frontend/src/features/race/components/HeatmapScaffold.tsx` — FOUND
- `frontend/src/features/race/components/HeatmapScaffold.test.tsx` — FOUND
- `frontend/src/features/race/components/ReplayScrubber.tsx` — FOUND
- `frontend/src/features/race/components/ReplayScrubber.test.tsx` — FOUND

Commits exist:
- `6d408b7` test(08-05): HeatmapScaffold RED
- `caba3a0` feat(08-05): HeatmapScaffold GREEN
- `809dbb3` test(08-05): ReplayScrubber RED
- `19e2305` feat(08-05): ReplayScrubber GREEN
- `f104f75` fix(08-05): TypeScript build errors

Tests: 19 + 9 = 28 passing. Build: clean. TypeScript: clean.

## Self-Check: PASSED
