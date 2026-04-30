---
phase: 10-og-image-and-sharing
plan: 03
subsystem: ui
tags: [racepage, og-mode, useSearchParams, data-og-anchor, heatmap-strip, websocket-gate]

requires:
  - phase: 10-og-image-and-sharing
    provides: cache + render fns wired to /race/{run_id}/og.png + /race/{run_id}/heatmap.png (10-01 + 10-02)
  - phase: 09-heatmap-replay-k3-calibration
    provides: HardnessFailureHeatmap (data-wired wrapper), HeatmapPayload type with baseline.{model,seed,task_ids} + cells[].recovery_rate.den
  - phase: 08-race-page-ui-visual-contract
    provides: RacePage scaffolding (D-44 useReducer, D-48 same-component variant, T-08-16 useRaceStream gate)
provides:
  - RacePage `?og=1` mode (chrome hidden; 1200-wide og-anchor wraps title + lanes + banner)
  - RacePage `?og=1&surface=heatmap` mode (1200-wide heatmap-anchor wraps HardnessFailureHeatmap with ogAnnotation+runId)
  - data-og-anchor + data-og-ready + data-heatmap-anchor sentinels for Playwright wait_for_selector
  - useRaceStream gate: !isOg (Risk-4 — no WS in OG mode)
  - HeatmapAnnotationStrip component (run_id · model · seed=N · n=M · task_ids)
  - HardnessFailureHeatmap optional ogAnnotation + runId props (additive, D-47 preserved)
affects: [phase-10-og-routes (10-02 Playwright targets these selectors), phase-10-og-clientside (10-04 mounts CopyHeadlineImageButton beside data-og-anchor)]

tech-stack:
  added: []
  patterns:
    - "Same-component variant via URL query: ?og=1 + ?surface=heatmap conditionally hides chrome and remounts the screenshot region inside a fixed-width sentinel Box. Avoids a parallel /og-render route."
    - "Playwright readiness sentinel: data-og-ready set ONLY after replay fold completes. React omits an attribute when its value is undefined, so the selector [data-og-anchor][data-og-ready=\"true\"] correctly waits."
    - "Annotation-strip pattern: a presentational component (HeatmapAnnotationStrip) lives inside the populated branch of a data-fetching wrapper (HardnessFailureHeatmap), keeping the empty-state never-unmount guard (D-47) as the OUTER guard."

key-files:
  created:
    - frontend/src/features/race/components/HeatmapAnnotationStrip.tsx
    - frontend/src/features/race/components/HeatmapAnnotationStrip.test.tsx
  modified:
    - frontend/src/features/race/RacePage.tsx (Phase 10 OG-mode wiring)
    - frontend/src/features/race/components/HardnessFailureHeatmap.tsx (ogAnnotation + runId optional props)

key-decisions:
  - "isOgReady derivation: replay-trace-non-null is the simplest reliable fold-complete signal. After replay.trace becomes non-null, the useEffect dispatches every event into the local reducer, populating baseState.lanes for the title/lanes/banner anchor."
  - "Heatmap-anchor uses [data-testid=\"heatmap-annotation-strip\"] as its own ready signal — the strip only mounts when HardnessFailureHeatmap has data, so Playwright can wait on the strip selector instead of needing a separate data-heatmap-ready attribute."
  - "Live-OG mode (no run_id) sets data-og-ready=\"true\" immediately because liveState always provides a baseState with default lane values. This is the dev-smoke path; production OG renders flow through replay URLs."
  - "deriveN() inside HardnessFailureHeatmap reads max(recovery_rate.den) across cells. Phase 9 D-58 baseline-locked shared denominator means this is the canonical n. Plan referenced data.n_runs which doesn't exist on HeatmapPayload — substituted the actual field per Task 1's verify-via-actual-type instruction."

patterns-established:
  - "URL-flag-driven variant rendering: same component, different visible regions controlled by useSearchParams. Easier to maintain than a separate route + duplicated layout."
  - "data-og-ready=true sentinel pattern: gate on the data-fetch completion signal of whichever fold powers the variant being rendered."

requirements-completed: [OG-01, OG-02]

duration: 16min (8min initial agent + 8min orchestrator-resume)
completed: 2026-04-30
---

# Phase 10 — Plan 03 Summary

**RacePage `?og=1` and `?og=1&surface=heatmap` modes with data-og-anchor/data-og-ready/data-heatmap-anchor sentinels, WS gating, and an additive OG-02 heatmap annotation strip — Phase 9 D-46/D-47 invariants preserved.**

## Performance

- **Duration:** ~16 min total (initial executor 8 min before quota kill + 8 min orchestrator-resume).
- **Started:** 2026-04-30T18:46:00Z
- **Completed:** 2026-04-30T21:50:00Z
- **Tasks:** 2/2
- **Files modified:** 4 (2 created, 2 modified)

## Accomplishments

- Shipped `HeatmapAnnotationStrip.tsx` with the OG-02 annotation contract: `{runId} · {baseline.model} · seed={baseline.seed} · n={n} · {baseline.task_ids.join(", ")}`.
- Added optional `ogAnnotation` + `runId` props to `HardnessFailureHeatmap.tsx`; strip mounts only when ogAnnotation && runId && data (additive, D-47 empty-state never-unmount preserved).
- RacePage reads `?og=1` and `?surface=heatmap` via `useSearchParams`; chrome (status strip, scrubber, methodology) hidden in OG mode; title+lanes+banner wrapped in `<Box data-og-anchor data-og-ready=…>`; heatmap wrapped in `<Box data-heatmap-anchor>` with `ogAnnotation={true}` when surface=heatmap.
- Risk-4 mitigation: `useRaceStream(!isMobile && !isReplay && !isOg)` gates the WebSocket so Playwright's `wait_until=domcontentloaded` never blocks on an open WS.
- Risk-10 mitigation: `data-og-ready="true"` only when the replay trace has folded (live mode + no-replay always ready).
- Mobile branch preserved verbatim — Phase 8 placeholder line 79-85 untouched (10-05 owns its closure).

## Task Commits

1. **Task 1: HeatmapAnnotationStrip + ogAnnotation/runId on HardnessFailureHeatmap** — `f9973ba` (RED test) + `9a23eb3` (GREEN component+wiring; recovery commit, orchestrator-salvaged from quota-killed agent).
2. **Task 2: RacePage `?og=1` mode + sentinels** — `9a64914` (feat).

## Files Created/Modified

- `frontend/src/features/race/components/HeatmapAnnotationStrip.tsx` (created, 31 LOC) — presentational component; data-testid="heatmap-annotation-strip".
- `frontend/src/features/race/components/HeatmapAnnotationStrip.test.tsx` (created, 57 LOC, 2 tests) — asserts OG-02 contract render shape + selector.
- `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` (modified, +45/-1) — ogAnnotation + runId props; deriveN() helper; strip mount inside populated branch.
- `frontend/src/features/race/RacePage.tsx` (modified, +90/-50) — useSearchParams import + read; isOg + ogSurface flags; isOgReady derivation; chrome-hide gates; data-og-anchor + data-og-ready + data-heatmap-anchor wrappers.

## Decisions Made

- **deriveN() reads max(cell.recovery_rate.den).** HeatmapPayload has no `n_runs` field; the planner referenced it speculatively. Per Phase 9 D-58 baseline-lock, every cell shares the same denominator, so taking the max across populated cells equals reading the canonical n. Empty cells → n=0.
- **Heatmap-anchor uses the strip's testid as its own readiness signal.** The strip only mounts after data fetch resolves, so Playwright can `wait_for_selector('[data-heatmap-anchor] [data-testid="heatmap-annotation-strip"]')` without needing a separate `data-heatmap-ready` attribute.
- **isOgReady defaults to true in live + no-replay branches.** liveState always provides a baseState with default lane values; production OG renders flow through replay URLs where `replay.trace !== null` is the meaningful signal.
- **Methodology section wrapped in a guard `<Box sx={{ mt: 6 }}>`.** Plan suggested keeping `<Stack spacing={6}>` semantics but the OG-anchor split moved methodology + heatmap outside the Stack; the explicit `mt: 6` preserves the 6-unit spacing the Stack used to provide.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 4 — Spec drift] Substituted `data.n_runs` → `deriveN(data)`**
- **Found during:** Task 1 (HeatmapAnnotationStrip mount).
- **Issue:** Plan listed `n={data.n_runs}` but `HeatmapPayload` (frontend/src/lib/types/race.ts) has no `n_runs` field. Plan annotated this with "verify via actual type — could be different field name".
- **Fix:** Added `deriveN(payload)` helper that returns `max(cell.recovery_rate.den)` across populated cells. Phase 9 D-58 baseline-lock guarantees this is the shared denominator.
- **Files modified:** frontend/src/features/race/components/HardnessFailureHeatmap.tsx.
- **Verification:** TypeScript compiles; HardnessFailureHeatmap 9 existing tests pass; new HeatmapAnnotationStrip 2 tests pass.
- **Committed in:** 9a23eb3.

**2. [Rule 1 — Required] Wrapped Methodology + Heatmap in mt-6 Boxes after splitting OG anchor**
- **Found during:** Task 2 (RacePage refactor).
- **Issue:** Plan's outer `<Stack spacing={6}>` wrapped title + lanes + banner + methodology + heatmap. Splitting title/lanes/banner into the OG anchor required removing them from the outer Stack. Without an explicit margin-top, methodology and heatmap collapsed against the og-anchor.
- **Fix:** Wrapped methodology and heatmap branches in `<Box sx={{ mt: 6 }}>` to preserve the 6-unit spacing.
- **Files modified:** frontend/src/features/race/RacePage.tsx.
- **Verification:** All 282 frontend tests pass. Visual smoke deferred (no dev-server in this orchestrator session).
- **Committed in:** 9a64914.

---

**Total deviations:** 2 auto-fixed (1 spec drift, 1 layout-spacing fix).
**Impact on plan:** No scope creep. Both fixes essential for type safety / visual continuity.

## Issues Encountered

- **Quota exhaustion mid-execution.** Initial gsd-executor agent for plan 10-03 hit Anthropic extra-usage quota during Task 2 (RacePage edit). Per `feedback_subagent_quota_recovery` memory: pre-existing committed RED test (f9973ba) preserved; uncommitted Task 1 GREEN files (HeatmapAnnotationStrip.tsx + HardnessFailureHeatmap.tsx wiring) salvaged + committed (9a23eb3); Task 2 written inline by orchestrator (9a64914). No work duplicated.

## User Setup Required

None — frontend-only edits.

## Next Phase Readiness

- 10-04 (CopyHeadlineImageButton) can mount beside CharacteristicFailureBanner inside the data-og-anchor — query selector `document.querySelector('[data-og-anchor]')` is ready.
- 10-05 (mobile `<img>` consumer) can replace the unchanged Phase 8 placeholder branch (line 79-85) without conflict.
- Wave 2 backend (10-02) can serve `/race/{run_id}/og.png` whose Playwright render targets `[data-og-anchor][data-og-ready="true"]`.

---
*Phase: 10-og-image-and-sharing*
*Completed: 2026-04-30*
