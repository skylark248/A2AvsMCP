---
phase: 14-race-demo-integration-fix
plan: "03"
subsystem: frontend/race
tags: [heatmap, page-state, bug-fix, tdd]
dependency_graph:
  requires: ["14-02"]
  provides: ["heatmap_has_data from live data", "sparse-heatmap state reachable"]
  affects: ["frontend/src/features/race/RacePage.tsx"]
tech_stack:
  added: []
  patterns: ["TDD RED/GREEN", "rules-of-hooks compliant hook call at component scope"]
key_files:
  created:
    - frontend/src/features/race/RacePage.heatmapWiring.test.tsx
  modified:
    - frontend/src/features/race/RacePage.tsx
    - frontend/src/features/race/RacePage.test.tsx
    - frontend/src/features/race/RacePage.a11y.test.tsx
    - frontend/src/features/race/RacePage.responsive.test.tsx
decisions:
  - "Added useRaceHeatmap mock to all three existing RacePage test files (test.tsx, a11y.test.tsx, responsive.test.tsx) to prevent real fetch calls during component renders"
  - "TDD call-count assertion: mock.calls.length >= 2 distinguishes RacePage scope call from HardnessFailureHeatmap internal call"
metrics:
  duration: "~8 minutes"
  completed: "2026-05-03"
  tasks_completed: 1
  tasks_total: 1
  files_changed: 5
---

# Phase 14 Plan 03: B3 heatmap_has_data Wiring Summary

**One-liner:** Replaced `const heatmap_has_data = false` with `!!heatmapData?.cells?.length` via `useRaceHeatmap()` call at RacePage scope, enabling `sparse-heatmap` page state to be reached.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | Add failing test for B3 heatmap_has_data wiring | fd086d5 | RacePage.heatmapWiring.test.tsx |
| 1 (GREEN) | Wire heatmap_has_data from useRaceHeatmap at RacePage scope | 81bd855 | RacePage.tsx + 3 test files |

## What Was Done

### Bug Description (B3)

`RacePage.tsx` had `const heatmap_has_data = false` hardcoded (line 143 pre-fix). This meant `derivePageState` always received `heatmap_has_data=false`, so the page state machine could never transition from "done" to "sparse-heatmap" — permanently broken for post-race heatmap display.

### Fix (3 changes to RacePage.tsx)

1. **Import**: Added `import { useRaceHeatmap } from "./hooks/useRaceHeatmap"` to the race hooks import block (line 25).

2. **Hook call**: Added `const { data: heatmapData } = useRaceHeatmap()` unconditionally in the function body after `useRaceReplay` (line 81). Hooks are called before any conditional returns — rules-of-hooks compliant. The call is independent of `HardnessFailureHeatmap`'s own internal call.

3. **Derivation**: Replaced `const heatmap_has_data = false` with `const heatmap_has_data = !!heatmapData?.cells?.length` (line 148). Optional chaining ensures null/undefined never reaches boolean coercion.

### Test Updates (Rule 2: Required for correctness)

Three existing test files that render `RacePage` needed `useRaceHeatmap` added to their mock registry. The hook executes during component render — without the mock, tests would call the real `fetchRaceHeatmap` API function:

- `RacePage.test.tsx` — added `vi.mock("./hooks/useRaceHeatmap", ...)`
- `RacePage.a11y.test.tsx` — added `vi.mock("./hooks/useRaceHeatmap", ...)`
- `RacePage.responsive.test.tsx` — added `vi.mock("./hooks/useRaceHeatmap", ...)`

All three mock `useRaceHeatmap` returning `{ data: null, loading: false, error: null }` — matching the existing pattern for `useRaceStream` and `useRaceReplay`.

## TDD Gate Compliance

RED commit: `fd086d5` — `test(14-03): add failing test for B3 heatmap_has_data wiring`
GREEN commit: `81bd855` — `feat(14-03): wire heatmap_has_data from useRaceHeatmap at RacePage scope (B3 fix)`

RED test correctly failed: `expected 1 to be greater than or equal to 2` — mock was called once (only from `HardnessFailureHeatmap`), proving `RacePage` did not call `useRaceHeatmap` pre-fix.

## Verification

```
grep -n "heatmap_has_data" frontend/src/features/race/RacePage.tsx
148:  const heatmap_has_data = !!heatmapData?.cells?.length;
154:    heatmap_has_data,

grep -n "useRaceHeatmap" frontend/src/features/race/RacePage.tsx
25:import { useRaceHeatmap } from "./hooks/useRaceHeatmap";
81:  const { data: heatmapData } = useRaceHeatmap();
```

TypeScript: clean (0 errors)
Tests: 335/335 passed (38 test files)

## Deviations from Plan

### Auto-added mock updates (Rule 2 — Missing correctness requirement)

**Found during:** Task 1 GREEN phase

**Issue:** Three existing test files (`RacePage.test.tsx`, `RacePage.a11y.test.tsx`, `RacePage.responsive.test.tsx`) did not mock `useRaceHeatmap`. After adding the hook call to `RacePage`, these tests would call the real `fetchRaceHeatmap` function (network/API call in test environment).

**Fix:** Added `vi.mock("./hooks/useRaceHeatmap", () => ({ useRaceHeatmap: vi.fn(() => ({ data: null, loading: false, error: null })) }))` to all three files.

**Files modified:** RacePage.test.tsx, RacePage.a11y.test.tsx, RacePage.responsive.test.tsx

**Commits:** 81bd855

## Known Stubs

None — `heatmap_has_data` is now wired to real data. No hardcoded false values remain.

## Threat Surface Scan

No new network endpoints, auth paths, or file access patterns introduced. The optional chaining `?.cells?.length` handles all null/undefined cases per T-14-03-01. No new threat surface beyond the existing `/api/race/heatmap` endpoint already in scope.

## Self-Check

- [x] `frontend/src/features/race/RacePage.tsx` exists and contains `useRaceHeatmap` import + call
- [x] `frontend/src/features/race/RacePage.heatmapWiring.test.tsx` exists (new test file)
- [x] RED commit `fd086d5` exists
- [x] GREEN commit `81bd855` exists
- [x] TypeScript clean (0 errors)
- [x] 335 tests passing

## Self-Check: PASSED
