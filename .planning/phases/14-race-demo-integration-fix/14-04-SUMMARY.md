---
plan: 14-04
phase: 14-race-demo-integration-fix
status: complete
started: "2026-05-03"
completed: "2026-05-03"
requirements:
  - HEAT-03
key-files:
  created: []
  modified:
    - frontend/src/features/race/RacePage.tsx
---

## Summary

Fixed gap W2: ReplayScrubber was a no-op stub. Added `seekPosition` state and `seekedReplayState` useMemo to RacePage — dragging the scrubber now folds `replay.trace.events.slice(0, seekPosition+1)` through `raceReducer` and displays the partial replay state. `baseState` in replay mode now uses `seekedReplayState ?? replayState` so seek takes priority when active.

## What Was Built

**RacePage.tsx** — Five surgical changes:
1. Added `useMemo` to React imports
2. Added `seekPosition: number | null` state (null = show full replay)
3. Added `seekedReplayState` useMemo — folds event slice up to seek position via pure `raceReducer`
4. Updated `baseState` derivation: `{ ...(seekedReplayState ?? replayState), run_id }` 
5. Wired `ReplayScrubber`: `value={seekPosition ?? lastEventIndex}`, `max={lastEventIndex}`, `onScrub={setSeekPosition}`

`max` now reflects total event count (not turn index) — scrubber range matches actual replay granularity.

## Must-Have Verification

- [x] `onScrub={setSeekPosition}` — no longer a no-op
- [x] Seeking to 0 shows initial state (empty slice → initialRaceState)
- [x] Seeking to max (events.length-1) shows full replay state
- [x] `scrubber max` = total event count - 1, not turn index
- [x] `scrubber value` = `seekPosition` when seeking, else `max`
- [x] Full `replayState` (useEffect-folded) unchanged — seek is a derived useMemo view on top
- [x] 335 frontend tests pass (0 failures)

## Self-Check: PASSED

TypeScript clean. 335/335 tests pass. Stub comment removed. All acceptance criteria met.
