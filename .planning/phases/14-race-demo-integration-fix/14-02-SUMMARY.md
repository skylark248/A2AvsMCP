---
plan: 14-02
phase: 14-race-demo-integration-fix
status: complete
started: "2026-05-03"
completed: "2026-05-03"
requirements:
  - UIRACE-01
  - UIRACE-02
  - UIRACE-03
  - TRC-04
key-files:
  created: []
  modified:
    - frontend/src/features/race/hooks/useRaceStream.ts
    - frontend/src/features/race/RacePage.tsx
    - frontend/src/lib/api/client.ts
    - frontend/src/features/race/hooks/useRaceStream.test.ts
---

## Summary

Fixed gap B2: useRaceStream now accepts `runId` as first parameter and injects `run_id=<id>` into the WebSocket URL. RacePage calls `POST /api/race/run` via `startRace()` on user action, stores the returned `run_id` in local state, and passes it to `useRaceStream` — gating the WS connection until a real run_id is available.

## What Was Built

**client.ts** — Added `StartRaceBody`, `StartRaceResponse` interfaces and `startRace()` function that POSTs to `/api/race/run` and returns `{ run_id }`.

**useRaceStream.ts** — New signature: `useRaceStream(runId: string, enabled: boolean = true)`. Updated `buildWsUrl` to prepend `run_id=${encodeURIComponent(runId)}` as the first query param. Dependency array updated to `[enabled, runId]` so a new WS opens when `runId` changes.

**RacePage.tsx** — Added `wsRunId` state (`useState<string>("")`). Added `handleStartRace` async handler that calls `startRace()` and sets `wsRunId`. Updated `useRaceStream` call: `useRaceStream(wsRunId, !!wsRunId && !isMobile && !isReplay && !isOg)` — WS does not open until run_id is available. Added `data-testid="race-start-button"` button visible in `pre-race` state only.

**useRaceStream.test.ts** — Updated all call-sites to new signature; added 5 tests covering `run_id` in WS URL and `encodeURIComponent`.

## Must-Have Verification

- [x] `useRaceStream(runId, enabled)` — runId first parameter with default `""`
- [x] `buildWsUrl` produces `ws(s)://host/api/race/ws?run_id=X&pure_mcp=N&pure_a2a=N&hybrid=N`
- [x] `RacePage` calls `startRace()` on Start Race action and stores run_id in state
- [x] `useRaceStream` called with `wsRunId` as first arg — no more 422 on WS connect
- [x] `enabled=false` path still prevents WS open (T-08-16 preserved via `!!wsRunId` gate)
- [x] 331 frontend tests pass (0 failures)

## Self-Check: PASSED

All tasks complete. TypeScript clean. 331/331 tests pass. No regressions.
