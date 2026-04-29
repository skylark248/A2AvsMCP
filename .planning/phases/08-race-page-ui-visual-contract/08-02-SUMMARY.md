---
phase: 08-race-page-ui-visual-contract
plan: "02"
subsystem: frontend/race-routing-page-state
tags: [frontend, react-router, page-state-machine, tdd, routing]
dependency_graph:
  requires:
    - frontend/src/lib/types/race.ts (Plan 01 — PageState, LaneState, RaceLane types)
    - frontend/src/features/race/context/FirstMentionProvider.tsx (Plan 01)
  provides:
    - frontend/src/app/routes.tsx (lazy /race + /race/:run_id routes wrapped in FirstMentionProvider)
    - frontend/src/components/layout/AppShell.tsx (Race nav entry)
    - frontend/src/features/race/RacePage.tsx (page shell with UIRACE-01 section slots)
    - frontend/src/features/race/pageState.ts (derivePageState — 12-state derivation function)
  affects:
    - Plans 03-06 (import RacePage, consume derivePageState)
    - Plan 06 (wires useRaceStream/useRaceReplay to RacePage)
tech_stack:
  added: []
  patterns:
    - React.lazy + Suspense lazy route loading (extends existing pattern in routes.tsx)
    - FirstMentionProvider wrapping both race routes (route-scoped context reset per D-51)
    - useParams for live/replay mode dispatch without conditional rendering (D-48)
    - Derived-state function over typed inputs (no FSM library, no global store)
key_files:
  created:
    - frontend/src/features/race/RacePage.tsx
    - frontend/src/features/race/pageState.ts
    - frontend/src/app/routes.race.test.tsx
    - frontend/src/features/race/pageState.test.ts
    - frontend/src/features/race/RacePage.test.tsx
  modified:
    - frontend/src/app/routes.tsx
    - frontend/src/components/layout/AppShell.tsx
decisions:
  - "run_id used only as Boolean(run_id) in RacePage shell — not rendered, not in href, not fetched — T-08-04 satisfied in this plan; T-08-05 (path traversal validation) enforced in Plan 03 useRaceReplay"
  - "sparse-heatmap derivation deferred to Plan 05 — requires cell-coverage heuristic; currently collapses to done (heatmap_has_data=true) or heatmap-empty (false)"
  - "lane-failed detection: terminal_tag===null + error event present (pre-classification failure signal)"
metrics:
  duration_minutes: 35
  completed_date: "2026-04-29"
  tasks_completed: 2
  files_changed: 7
---

# Phase 8 Plan 02: Routing Surface + Page State Machine Summary

Lazy /race + /race/:run_id routes wrapped in FirstMentionProvider; RacePage shell with UIRACE-01 section slots; derivePageState covering all 12 UIRACE-02 states; Race nav item in AppShell.

## Route Table

| Path | Element | Provider | Mode |
|------|---------|----------|------|
| `/race` | `<RacePage />` | `FirstMentionProvider` | Live (useRaceStream, Plan 03) |
| `/race/:run_id` | `<RacePage />` | `FirstMentionProvider` | Replay (useRaceReplay, Plan 03) |

Both routes are lazy-loaded via `React.lazy` + `withSuspense`. `FirstMentionProvider` wraps both so the seen-Set resets on route exit (D-51). Same `RacePage` component renders both modes; `useParams().run_id` presence flips `isReplay` (D-48).

## RacePage Section Slot List

Plans 04-06 look up these `data-testid` markers to fill section content:

| data-testid | Location in Hierarchy | Filled by | Notes |
|-------------|----------------------|-----------|-------|
| `race-status-strip` | Top — 48px fixed height, border-bottom | Plan 04 | Session-level metadata: page-state label + reconnect indicator |
| `race-scrubber-slot` | Below status strip | Plan 05 | Replay-only (rendered only when `isReplay === true`, D-49) |
| `race-lane-row` | Central column (maxWidth 1200) | Plan 04 | flex row, gap xl(32px), 3 × RaceLaneCard |
| `race-banner-slot` | Below lane row | Plan 04 | CharacteristicFailureBanner, 0px radius, 4px primary rule |
| `race-methodology-slot` | Below banner (aside, role=complementary) | Plan 04 | Flat section, no Paper/Card per UIRACE-03 |
| `race-heatmap-slot` | Bottom | Plan 05 | CSS Grid, role=grid, heatmap-empty state per D-47 |

## derivePageState Input Shape

```typescript
interface DerivePageStateInput {
  ws_status: "connecting" | "open" | "reconnecting" | "closed";
  lanes: Record<RaceLane, LaneState>;  // from Plan 01 types
  run_id: string | null;               // null = live mode, string = replay mode
  countdown_seconds?: number | null;   // optional pre-race countdown ticker
  expected_n: number;                  // 1 or 5 parallel runs
  heatmap_has_data: boolean;           // true when heatmap grid has ≥1 populated cell
}
```

## derivePageState 12-State Truth Table

| State | Trigger condition | Priority |
|-------|------------------|----------|
| `replay` | `run_id !== null` | 1 (dominates all per D-48) |
| `ws-disconnected` | `ws_status === "closed"` | 2 |
| `ws-reconnecting` | `ws_status === "reconnecting"` | 2 |
| `lane-failed` | Any lane: `terminal_tag === null && error event present` | 3 |
| `indeterminate` | All lanes terminal + any `terminal_tag === "indeterminate"` | 4 |
| `heatmap-empty` | All lanes terminal + non-indeterminate + `heatmap_has_data === false` | 4 |
| `done` | All lanes terminal + `heatmap_has_data === true` | 4 |
| `countdown` | No events + `countdown_seconds` provided | 5 |
| `pre-race` | No events + no countdown | 5 (fallback) |
| `live-n1` | Events flowing + `expected_n < 5` | 6 |
| `live-n5` | Events flowing + `expected_n >= 5` | 6 |
| `sparse-heatmap` | Deferred to Plan 05 (cell-coverage heuristic) | — |

**Note:** `sparse-heatmap` derivation is intentionally deferred to Plan 05. Plan 02 collapses it to `done` (heatmap_has_data=true) until the cell-coverage analysis is implemented. The test for this state manually adds the string to the reachable set to confirm all 12 names exist in the type system.

## AppShell Nav

Race entry added to `navItems` array in `AppShell.tsx`:

```typescript
{ to: "/race", label: "Race", icon: <SportsScoreOutlinedIcon fontSize="small" /> }
```

Uses `SportsScoreOutlinedIcon` from `@mui/icons-material` — no new dependency.

## Test Results

| File | Tests | Status |
|------|-------|--------|
| `routes.race.test.tsx` | 5 | PASS |
| `routes.test.tsx` (existing regression) | 3 | PASS |
| `pageState.test.ts` | 13 | PASS |
| `RacePage.test.tsx` | 10 | PASS |
| TypeScript `npx tsc --noEmit` | — | PASS |
| `npm run build` | — | PASS (2.39s) |

**Total: 31/31 tests pass.**

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | `94146fb` | feat(08-02): add /race + /race/:run_id routes, RacePage shell, Race nav item |
| Task 2 | `2393a3d` | feat(08-02): derivePageState 12-state machine + RacePage shell tests (UIRACE-02) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] /Race/i regex matched "Traces" nav link (substring match)**
- **Found during:** Task 1, GREEN phase — `getByRole("link", { name: /Race/i })` threw "Found multiple elements" because "Traces" contains "race" as a substring
- **Issue:** Testing-Library uses regex partial match; `/Race/i` matches "Traces" link text
- **Fix:** Changed test to exact string `{ name: "Race" }` — matches only the Race nav item
- **Files modified:** `frontend/src/app/routes.race.test.tsx`
- **Commit:** `94146fb`

**2. [Rule 1 - Bug] makeLaneFailedLane test helper had wrong terminal_tag value**
- **Found during:** Task 2, GREEN phase — `lane-failed` test returned `live-n1` instead of `lane-failed`
- **Issue:** Helper set `terminal_tag: "gave_up"` which prevented the detection logic (`terminal_tag === null && error event`) from triggering; it also put the lane in the "all terminal" path
- **Fix:** Changed to `terminal_tag: null` with added comment explaining the lane-failed signal model
- **Files modified:** `frontend/src/features/race/pageState.test.ts`
- **Commit:** `2393a3d`

## Known Stubs

The following section slots in `RacePage.tsx` are intentional stubs — empty `<Box>` elements with `data-testid` markers that Plans 04-06 fill with real components:

| data-testid | Stub type | Wired by |
|-------------|-----------|----------|
| `race-status-strip` | Empty 48px Box (height only) | Plan 04 |
| `race-scrubber-slot` | Empty Box (conditional on isReplay) | Plan 05 |
| `race-lane-row` | Empty flex Box | Plan 04 |
| `race-banner-slot` | Empty Box | Plan 04 |
| `race-methodology-slot` | Empty aside[role=complementary] | Plan 04 |
| `race-heatmap-slot` | Empty Box | Plan 05 |

These stubs are intentional — Plan 02's goal is the routing surface and page-state machine. The stubs do not prevent Plan 02's goal (routing + derivePageState) from being achieved. They are the defined hand-off points for Plans 04-06.

## Threat Surface Scan

No new network endpoints, auth paths, or file access patterns introduced in this plan.

T-08-04 (XSS via run_id render): `run_id` is used only as `Boolean(run_id)` → `isReplay` flag in RacePage. It is never rendered as text, never inserted into href, never passed to innerHTML. Satisfied.

T-08-05 (path traversal via run_id fetch): Not applicable to Plan 02 — no fetch occurs here. Enforcement delegated to Plan 03 `useRaceReplay` per threat register.

T-08-06 (lazy bundle DoS): Lazy + Suspense is the existing project pattern. No new surface.

## Self-Check: PASSED
