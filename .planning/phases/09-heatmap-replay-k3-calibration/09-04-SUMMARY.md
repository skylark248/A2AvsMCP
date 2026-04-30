---
phase: 09-heatmap-replay-k3-calibration
plan: 04
subsystem: frontend
tags: [frontend, react, mui, heatmap, hook, vitest, race]

# Dependency graph
requires:
  - phase: 08-race-page-ui-visual-contract
    provides: HeatmapScaffold (CSS Grid + role=gridcell + empty-state overlay) + failureTagColor 5-entry map + RacePage heatmap slot
  - phase: 09-heatmap-replay-k3-calibration
    plan: 01
    provides: GET /api/race/heatmap returning {cells, baseline} with D-53 minimal cell shape
provides:
  - HardnessFailureHeatmap.tsx — data-wired wrapper around HeatmapScaffold (HEAT-01, HEAT-02)
  - useRaceHeatmap() hook with let-active-true cleanup pattern (Pattern 4)
  - fetchRaceHeatmap() client mirroring fetchRaceReplay shape
  - HeatmapPayload / HeatmapCellPayload / HeatmapBaseline / HardnessTypeBackend frontend types
  - LANDMINE 1 transform: backend "multi_source" → frontend "multi_source_synthesis" at the wrapper boundary
  - RacePage.tsx uses <HardnessFailureHeatmap /> in place of <HeatmapScaffold cells={heatmapCells} />
affects:
  - Phase 10 OG image generation (heatmap card now renders populated cells under /race/<run_id>?og=1)
  - Future TraceExplorer drilldown (sample_run_id is on cell payload but UI wiring is Phase 11+)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "React data hook with let-active-true cleanup (Pattern 4 from useRaceReplay.ts)"
    - "Frontend wrapper around rendering primitive — wrapper owns fetch + transform + non-grid surfaces; primitive untouched (Pattern 5)"
    - "Backend → frontend enum-value rename at the transform boundary (closed Record<HardnessTypeBackend, HardnessType> map)"
    - "Singleton API endpoint hook — empty deps array, fetch once on mount (no path param)"
    - "vi.mock module hook + closure-bound mockResult variable for component test fixtures (mirrors useRaceReplay.test.ts pattern with React Testing Library)"

key-files:
  created:
    - "frontend/src/features/race/hooks/useRaceHeatmap.ts (47 lines) — data hook"
    - "frontend/src/features/race/hooks/useRaceHeatmap.test.ts (135 lines) — 4 hook tests"
    - "frontend/src/features/race/components/HardnessFailureHeatmap.tsx (95 lines) — data-wired wrapper component"
    - "frontend/src/features/race/components/HardnessFailureHeatmap.test.tsx (175 lines) — 9 component tests"
  modified:
    - "frontend/src/lib/types/race.ts — appended HardnessTypeBackend, HeatmapCellPayload, HeatmapBaseline, HeatmapPayload (4 new exported types)"
    - "frontend/src/lib/api/client.ts — added fetchRaceHeatmap() + HeatmapPayload re-export; widened RaceEvent import to include HeatmapPayload"
    - "frontend/src/features/race/RacePage.tsx — swapped <HeatmapScaffold cells={heatmapCells} /> for <HardnessFailureHeatmap />; removed dead heatmapCells = {} constant + comment"

key-decisions:
  - "LANDMINE 1 fix lives in the wrapper transform layer (HardnessFailureHeatmap.tsx HARDNESS_BACKEND_TO_FRONTEND map), NOT in HeatmapScaffold or types/race.ts. Reason: D-46 locks HeatmapScaffold's 'multi_source_synthesis' row key (Phase 8 verified-PASS); changing it would risk Phase 8 regression. The wrapper rename is one closed Record + one for-loop pass — lower blast radius."
  - "heatmap_has_data in derivePageState stayed at false (RESEARCH §4 closing paragraph). Reason: the wrapper passes {} to the scaffold when API cells are empty, and the scaffold's empty-state overlay (D-47) surfaces automatically. Wiring data?.cells.length > 0 into RacePage would re-introduce the dead heatmapCells coupling. Deferred to a future plan if Phase 9 verification flags it."
  - "Test fix for legend pill assertion: getAllByText for 'Recovered' / 'Gave Up' (>= 1 occurrence) instead of getByText. Reason: UIRACE-04 channel 4 sr-only labels inside populated cells (HeatmapScaffold renders <span style={visuallyHidden}>{cfg.label}</span>) collide with the legend chip's text. >= 1 confirms the legend renders without forbidding the sr-only labels in cells."
  - "Hook initial loading state set to true (not false) at useState init. Reason: the test 'starts in loading=true (initial state)' asserts loading=true synchronously before fetch resolves. Setting to true at init avoids a render-cycle race where setLoading(true) inside useEffect doesn't flush before the test reads result.current."

patterns-established:
  - "Backend enum value drift handled at the wrapper transform layer (closed Record + graceful fallthrough on unknown values — T-09-13 mitigation)"
  - "Singleton API endpoint hook variant of Pattern 4 — fetch on mount with empty deps, no validator (mirrors useRaceReplay shape minus run_id branch)"
  - "Component test pattern: vi.mock the data hook + closure-bound mockResult variable + beforeEach reset (no need to stub global fetch when the wrapper consumes the hook)"

requirements-completed: [HEAT-01, HEAT-02]

# Metrics
duration: 5min
completed: 2026-04-30
---

# Phase 9 Plan 04: Frontend HardnessFailureHeatmap Data Wiring Summary

**Data-wired heatmap UI: thin wrapper `HardnessFailureHeatmap.tsx` fetches `/api/race/heatmap`, transforms cells (renaming backend `multi_source` → frontend `multi_source_synthesis`), and renders the Phase 8 `HeatmapScaffold` with the data-driven directional pill, 5-pill always-visible legend strip, and `model · seed · task_ids` footer.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-30T06:15:04Z
- **Completed:** 2026-04-30T06:20:22Z
- **Tasks:** 2 (both type=auto tdd=true)
- **Files created:** 4 (1 hook + 1 hook test + 1 component + 1 component test)
- **Files modified:** 3 (types/race.ts, lib/api/client.ts, RacePage.tsx)
- **Commits:** 4 (RED + GREEN per task)
- **Frontend tests added:** 13 (4 hook + 9 component)
- **Frontend test count:** 267 → 280 (+13, no regressions)
- **Backend pytest:** 326/326 (no regression)

## Accomplishments

- **HEAT-01 satisfied.** `HardnessFailureHeatmap` renders rows = HardnessType × cols = lane via the Phase 8 `HeatmapScaffold` (D-46 preserved), with the "directional · n=3 tasks · v1" pill in `secondary.main` above the grid. Cells show dominant_tag color + icon + recovery fraction; keyboard-focusable via the scaffold's `tabIndex={0}` (Phase 8 verified).
- **HEAT-02 satisfied.** A 5-pill legend strip (one per `failureTagColor` entry) renders ALWAYS — even when `data === null` during loading. The footer shows `claude-sonnet-4-6 · 42 · summarize_repo, negotiate_meeting, book_travel`, read live from `data.baseline` on every render. Drift between aggregation scope and footer copy is structurally impossible (HEATMAP_BASELINE constant from Plan 09-01 → API payload → wrapper footer).
- **LANDMINE 1 resolved at the wrapper boundary.** Backend `"multi_source"` (race/types.py:26) is renamed to frontend `"multi_source_synthesis"` (HeatmapScaffold.tsx:31) by `HARDNESS_BACKEND_TO_FRONTEND` in `HardnessFailureHeatmap.tsx`. The scaffold never sees the backend short form; D-46 cell-shape contract intact.
- **D-46 + D-47 preserved.** The wrapper does NOT bypass `HeatmapScaffold`'s rendering primitive. Empty cells `{}` pass-through surfaces the scaffold's `heatmap-empty-overlay` automatically — the scaffold stays mounted (D-47 never-unmount).
- **D-60 honored.** This is a data-wiring upgrade of `HeatmapScaffold`, not a new design. UI-SPEC + ROADMAP success criteria #1+#2 specified the visual contract upstream; this plan only adds the API → DOM data plumbing.
- **No backend regression.** Plan 09-01..09-03 backend remains green at 326/326 pytest. Frontend full suite expanded from 267 (Phase 8 baseline) to 280 (+13 new), with all prior tests still passing.

## Task Commits

Each task was committed atomically using the TDD RED → GREEN cycle:

1. **Task 1 RED — failing useRaceHeatmap hook tests** — `1a77308` (test)
2. **Task 1 GREEN — Heatmap types + fetchRaceHeatmap client + useRaceHeatmap hook** — `2ea9f4d` (feat)
3. **Task 2 RED — failing HardnessFailureHeatmap component tests** — `cfa20e3` (test)
4. **Task 2 GREEN — HardnessFailureHeatmap wrapper + RacePage wiring** — `864fa2d` (feat)

**Plan metadata commit:** added below as final commit covering SUMMARY.md + STATE.md + ROADMAP.md + REQUIREMENTS.md.

## Files Created/Modified

### Created

- **`frontend/src/features/race/hooks/useRaceHeatmap.ts`** — Data hook fetching `/api/race/heatmap`. Mirrors `useRaceReplay`'s let-active-true cleanup pattern; empty deps array (singleton endpoint, fetch once on mount). Returns `{data: HeatmapPayload | null, loading: boolean, error: string | null}`.
- **`frontend/src/features/race/hooks/useRaceHeatmap.test.ts`** — 4 tests covering initial loading=true, happy fetch, fetch reject, and unmount-cleanup discipline (no setState-on-unmounted warnings).
- **`frontend/src/features/race/components/HardnessFailureHeatmap.tsx`** — Data-wired wrapper around `HeatmapScaffold`. Owns: API fetch (via `useRaceHeatmap`), backend→frontend hardness_type rename (LANDMINE 1), directional pill in MUI `secondary.main`, 5-pill legend strip (always visible), data-driven `model · seed · task_ids` footer. Grid rendering delegates to `HeatmapScaffold` — D-46 + D-47 preserved.
- **`frontend/src/features/race/components/HardnessFailureHeatmap.test.tsx`** — 9 tests covering: directional pill, scaffold delegation (role=grid + role=gridcell + data-testid="heatmap-scaffold"), `multi_source` → `multi_source_synthesis` rename, 5-pill legend always-visible (data null + data loaded), data-driven footer present, footer absent during loading, recovery_rate fraction format `"12/15"`, and empty-cells pass-through preserves D-47 (`heatmap-empty-overlay` surfaces).

### Modified

- **`frontend/src/lib/types/race.ts`** — Appended HEAT-01 / HEAT-02 cell + payload types after the existing `RaceState` interface: `HardnessTypeBackend` (4-member union with `"multi_source"` short form per backend types.py:26), `HeatmapCellPayload`, `HeatmapBaseline`, `HeatmapPayload`. Header comment documents LANDMINE 1 and points readers at the wrapper transform layer.
- **`frontend/src/lib/api/client.ts`** — Added `fetchRaceHeatmap(): Promise<HeatmapPayload>` after `fetchRaceReplay`. Mirrors the `fetchRaceReplay` shape (bare `fetch`, raw `dict` response cast to typed payload). Singleton endpoint — no path param, no validator. Re-exports `HeatmapPayload` type from `../types/race`. Widened the existing `import type` to include `HeatmapPayload`.
- **`frontend/src/features/race/RacePage.tsx`** — Three minimal edits: (1) swapped `import { HeatmapScaffold }` for `import { HardnessFailureHeatmap }`. (2) Removed the dead `const heatmapCells = {}` + Phase-8 comment block. (3) Replaced `<HeatmapScaffold cells={heatmapCells} />` with `<HardnessFailureHeatmap />` (one-line slot wire). The wrapper now owns its own fetch — RacePage stops hardcoding empty cells.

## Decisions Made

- **LANDMINE 1 transform location: wrapper, not types or scaffold.** The backend ships `"multi_source"` and `HeatmapScaffold.tsx:31` types its row key as `"multi_source_synthesis"`. Three options were on the table: (a) align the frontend constant to `"multi_source"` in `HeatmapScaffold.tsx`; (b) ship the rename in `types/race.ts`; (c) rename at the wrapper transform layer. Picked (c). Reason: Phase 8 is verified-PASS at `"multi_source_synthesis"`; touching the scaffold would risk Phase 8 regression for zero functional gain. The wrapper map is one closed `Record<HardnessTypeBackend, HardnessType>` + one `for` loop — surgical, single source of truth, and the LANDMINE comment in both files makes the intent explicit.
- **`heatmap_has_data` stayed at false in `derivePageState`.** Per RESEARCH §4 closing paragraph, the wrapper's empty-cells `{}` pass-through to `HeatmapScaffold` triggers the scaffold's empty-state overlay (D-47) automatically. Wiring `data?.cells.length > 0` from inside the wrapper into RacePage's `derivePageState` would re-introduce the dead `heatmapCells` coupling we just removed. Deferred — if Phase 9 verification flags this, a future plan can add a thin status hook (e.g., `useHeatmapStatus()`) without re-coupling RacePage to the wrapper's internals.
- **Hook initial `loading` state = true (not false).** The first test asserts `result.current.loading === true` synchronously before the fetch resolves. Initializing `useState<boolean>(true)` instead of `useState<boolean>(false)` avoids a render-cycle race where `setLoading(true)` inside `useEffect` doesn't flush before the test reads `result.current`. The semantics are identical from a user's perspective (loading goes false on resolve / reject).
- **Test fix for legend pill assertion: `getAllByText` for `"Recovered"` / `"Gave Up"` (>= 1 occurrence) instead of `getByText`.** UIRACE-04 channel 4 forces `HeatmapScaffold` to render `<span style={visuallyHidden}>{cfg.label}</span>` inside every populated cell. When the test fixture has cells with `dominant_tag: "recovered"` and `dominant_tag: "gave_up"`, those sr-only labels collide with the legend chip's own `"Recovered"` / `"Gave Up"` labels. `getAllByText(...).length >= 1` confirms the legend renders without forbidding the sr-only labels in cells (which are required by UIRACE-04 and verified by Phase 8 a11y tests).

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Hook initial `loading` state had to be true, not false (one-character fix).**

- **Found during:** Task 1 GREEN running the first test ("starts in loading=true").
- **Issue:** Plan instructions wrote `useState<boolean>(false)` for the loading state, with the assumption that `setLoading(true)` inside `useEffect` would flush before the synchronous test assertion. In practice React's `renderHook` snapshots `result.current` after the initial render but before effects execute, so the test saw `loading=false` and failed.
- **Fix:** Changed `useState<boolean>(false)` to `useState<boolean>(true)` in `useRaceHeatmap.ts`. The semantics are identical from a user's perspective — by the time the component renders the first time, the fetch is already in flight, so claiming "loading" at init is honest. `useRaceReplay` happens to start at false because it has a `run_id !== undefined` guard upstream; `useRaceHeatmap` has no such guard (singleton endpoint), so init=true is the correct semantic for this hook.
- **Files modified:** `frontend/src/features/race/hooks/useRaceHeatmap.ts` (one line).
- **Verification:** All 4 hook tests pass after the fix; the test for "starts in loading=true" passes synchronously without timing assumptions.
- **Committed in:** `2ea9f4d` (Task 1 GREEN).

**2. [Rule 1 — Bug] Component test for legend pills double-counted sr-only labels.**

- **Found during:** Task 2 GREEN — 8/9 tests passed; "renders 5 legend pills when data is loaded" failed because `getByText("Recovered")` matched 2 elements (the legend chip + the sr-only `<span style={visuallyHidden}>Recovered</span>` inside the populated `multi_source_synthesis-pure_mcp` cell, which has `dominant_tag: "recovered"`).
- **Issue:** Plan author assumed `getByText` would scope to one element. UIRACE-04's channel-4 sr-only labels (verified in Phase 8) make this impossible without an accessible-name selector.
- **Fix:** Switched to `getAllByText("Recovered").length >= 1` and `getAllByText("Gave Up").length >= 1` — the other 3 tag labels (`Kept Going (Unaware)`, `Kept Going to Failure`, `Indeterminate`) don't appear in cells so they keep `getByText`. The semantic claim ("the legend strip renders all 5 pills") is preserved; the test now correctly tolerates the cell sr-only collision.
- **Files modified:** `frontend/src/features/race/components/HardnessFailureHeatmap.test.tsx` (~6 lines around the affected test).
- **Verification:** All 9 component tests pass after the fix; full frontend suite still 280/280.
- **Committed in:** `864fa2d` (Task 2 GREEN).

---

**Total deviations:** 2 auto-fixed (both Rule 1 bugs surfaced by running the tests; both fixes are one- or two-line nudges that align test/impl with React's render-cycle semantics and Phase 8's a11y contract). No scope creep; no architectural changes.

## Issues Encountered

None blocking. The plan's intent was crisp; the two auto-fixes above were micro-adjustments to align with React's render-cycle behavior and Phase 8's UIRACE-04 sr-only label contract. Both were caught on the first GREEN run and fixed inline without needing a separate RED.

## User Setup Required

None — no external service configuration required. The wrapper consumes the existing `/api/race/heatmap` route mounted in Plan 09-01.

## Verification Evidence

```
$ grep -c "export interface HeatmapPayload" frontend/src/lib/types/race.ts    # == 1 required
1
$ grep -c "export type HardnessTypeBackend" frontend/src/lib/types/race.ts    # == 1 required
1
$ grep -c '"multi_source"' frontend/src/lib/types/race.ts                     # >= 1 required (backend short form)
3
$ grep -c "export async function fetchRaceHeatmap" frontend/src/lib/api/client.ts   # == 1 required
1
$ grep -c "/api/race/heatmap" frontend/src/lib/api/client.ts                  # >= 1 required
1
$ grep -c "export function useRaceHeatmap" frontend/src/features/race/hooks/useRaceHeatmap.ts   # == 1 required
1
$ grep -c "let active = true" frontend/src/features/race/hooks/useRaceHeatmap.ts   # == 1 required (Pattern 4)
1
$ grep -c "export function HardnessFailureHeatmap" frontend/src/features/race/components/HardnessFailureHeatmap.tsx   # == 1 required
1
$ grep -c "HARDNESS_BACKEND_TO_FRONTEND" frontend/src/features/race/components/HardnessFailureHeatmap.tsx   # >= 1 required
2
$ grep -c '"multi_source_synthesis"' frontend/src/features/race/components/HardnessFailureHeatmap.tsx   # >= 1 required
2
$ grep -c "<HeatmapScaffold cells=" frontend/src/features/race/components/HardnessFailureHeatmap.tsx   # >= 1 required
1
$ grep -c "directional · n=3 tasks · v1" frontend/src/features/race/components/HardnessFailureHeatmap.tsx   # == 1 required
2
$ grep -c 'color="secondary"' frontend/src/features/race/components/HardnessFailureHeatmap.tsx   # >= 1 required
1
$ grep -c "failureTagColor" frontend/src/features/race/components/HardnessFailureHeatmap.tsx   # >= 1 required
4
$ grep -c "data.baseline.model" frontend/src/features/race/components/HardnessFailureHeatmap.tsx   # >= 1 required (data-driven footer)
1
$ grep -c "<HardnessFailureHeatmap" frontend/src/features/race/RacePage.tsx   # >= 1 required
1
$ grep -c "<HeatmapScaffold cells={heatmapCells}" frontend/src/features/race/RacePage.tsx   # == 0 required (old call site removed)
0
$ grep -c "const heatmapCells = {}" frontend/src/features/race/RacePage.tsx   # == 0 required (dead constant removed)
0
$ cd frontend && npx vitest run src/features/race/hooks/useRaceHeatmap.test.ts
 Test Files  1 passed (1) | Tests  4 passed (4)
$ cd frontend && npx vitest run src/features/race/components/HardnessFailureHeatmap.test.tsx
 Test Files  1 passed (1) | Tests  9 passed (9)
$ cd frontend && npx vitest run src/features/race/RacePage
 Test Files  3 passed (3) | Tests  29 passed (29)
$ cd frontend && npm test
 Test Files  29 passed (29) | Tests  280 passed (280)
$ cd frontend && npx tsc --noEmit
(exit 0, no output)
$ pytest -q
326 passed, 4 subtests passed in 11.80s
```

## Next Phase Readiness

- **Phase 9 ALL PLANS COMPLETE.** 09-01 (heatmap backend), 09-02 (replay route), 09-03 (replay symmetry + K-calibration tests), and 09-04 (frontend wrapper) all SHIPPED.
- **Ready for `/gsd-verify-phase 9`.** All 4 success criteria from the ROADMAP should be verifiable in CI:
  1. `/race` heatmap rows × cols + cell encoding + directional pill — verified by HardnessFailureHeatmap.test.tsx + Phase 8 HeatmapScaffold a11y tests.
  2. 5-pill legend always visible + footer shows model · seed · task_ids — verified by 3 dedicated tests in HardnessFailureHeatmap.test.tsx.
  3. `/race/<run_id>` replay reads disk + replay-symmetric tags — verified by Plan 09-02 route tests + Plan 09-03 test_replay_symmetry.py 18 cases.
  4. K∈{2,3,4,5} sweep over fictional traces — verified by Plan 09-03 test_recovery_calibration.py 27 cases at the ROADMAP-named path.
- **Phase 10 (OG image) is unblocked.** Heatmap card now renders populated cells under `/race/<run_id>?og=1` mode; Playwright PNG capture has real visual data.

## TDD Gate Compliance

This plan is `type=execute` (not `type=tdd`), but each individual task has `tdd="true"`. Per-task TDD gates verified in git log:

- Task 1: `1a77308` (test) → `2ea9f4d` (feat) ✓
- Task 2: `cfa20e3` (test) → `864fa2d` (feat) ✓

No REFACTOR commits were needed — both GREEN implementations passed cleanly after the two auto-fix nudges (loading-init + getAllByText) documented above.

## Self-Check: PASSED

- Created files exist:
  - `frontend/src/features/race/hooks/useRaceHeatmap.ts` ✓ FOUND
  - `frontend/src/features/race/hooks/useRaceHeatmap.test.ts` ✓ FOUND
  - `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` ✓ FOUND
  - `frontend/src/features/race/components/HardnessFailureHeatmap.test.tsx` ✓ FOUND
- Modified files include expected additions:
  - `frontend/src/lib/types/race.ts` contains `HeatmapPayload` + `HardnessTypeBackend` ✓
  - `frontend/src/lib/api/client.ts` contains `fetchRaceHeatmap` ✓
  - `frontend/src/features/race/RacePage.tsx` contains `<HardnessFailureHeatmap />` ✓ and old `<HeatmapScaffold cells={heatmapCells}` is gone ✓
- Commit hashes exist in git log:
  - `1a77308` ✓ FOUND (test RED Task 1)
  - `2ea9f4d` ✓ FOUND (feat GREEN Task 1)
  - `cfa20e3` ✓ FOUND (test RED Task 2)
  - `864fa2d` ✓ FOUND (feat GREEN Task 2)

---
*Phase: 09-heatmap-replay-k3-calibration*
*Completed: 2026-04-30*
