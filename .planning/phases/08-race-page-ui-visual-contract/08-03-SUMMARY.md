---
phase: 08-race-page-ui-visual-contract
plan: "03"
subsystem: frontend/race-data-layer
tags: [frontend, websocket, useReducer, state-machine, replay, tdd]
dependency_graph:
  requires:
    - frontend/src/lib/types/race.ts (Plan 01 — RaceEvent union, LaneState, RaceState, RaceLane)
    - frontend/src/features/race/raceReducer.ts (Task 1 output — consumed by Task 2 hooks)
  provides:
    - frontend/src/features/race/raceReducer.ts (pure reducer — testable without WS)
    - frontend/src/features/race/hooks/useRaceStream.ts (WS lifecycle + per-lane cursor + enabled gate)
    - frontend/src/features/race/hooks/useRaceReplay.ts (fetch trace + run_id validation)
    - frontend/src/lib/api/client.ts (fetchRaceReplay typed call signature)
  affects:
    - Plans 04-06 (consume RaceState shape from useRaceStream / useRaceReplay)
    - Plan 06 (wires useRaceStream(enabled) into RacePage — passes enabled=!isMobile)
tech_stack:
  added: []
  patterns:
    - useReducer over closed event union (D-44 — no global store, no provider)
    - Per-lane cursor in WS URL query string for reconnect resume (D-45)
    - enabled flag gates WebSocket open without violating rules-of-hooks (T-08-16)
    - let active = true cleanup flag (mirrors ReportDetailPage.tsx fetch pattern)
    - run_id validation regex before fetch URL construction (T-08-05)
    - Events feed cap EVENTS_FEED_CAP=200 per lane (T-08-09)
    - vi.stubGlobal('WebSocket', MockWebSocket) test pattern (no prior precedent)
key_files:
  created:
    - frontend/src/features/race/raceReducer.ts
    - frontend/src/features/race/raceReducer.test.ts
    - frontend/src/features/race/hooks/useRaceStream.ts
    - frontend/src/features/race/hooks/useRaceStream.test.ts
    - frontend/src/features/race/hooks/useRaceReplay.ts
    - frontend/src/features/race/hooks/useRaceReplay.test.ts
  modified:
    - frontend/src/lib/api/client.ts
decisions:
  - "race_done event produces no per-lane mutation — session-level signal; derivePageState (Plan 02) reads it from the event feed"
  - "ttff_ms set exactly once per lane — first fault_observed event wins; subsequent fault_observed calls preserve original value"
  - "useRaceStream effect dep is [enabled] only — reducer holds cursor state across messages; no state in effect dependency array avoids stale closure"
  - "useRaceReplay initializes loading=false (not true) on mount — state is set to true inside the effect after run_id validation passes; avoids flash of loading=true for invalid run_ids"
  - "fetchRaceReplay calls the bare fetch() not requestJson() helper — stub endpoint is race-specific and the response shape (RaceReplayPayload) is outside the existing helper's error-handling convention"
metrics:
  duration_minutes: 35
  completed_date: "2026-04-29"
  tasks_completed: 2
  files_changed: 7
---

# Phase 8 Plan 03: Race Data Layer (Reducer + Hooks) Summary

Pure `raceReducer` over closed 10-event union with monotonic per-lane cursor; `useRaceStream(enabled?)` owning the WebSocket lifecycle with D-45 reconnect resume and T-08-16 enabled gate; `useRaceReplay` fetching the stubbed trace endpoint with T-08-05 run_id validation.

## Reducer Event-Type-to-State-Transition Table

| Event type | Per-lane state change | Global state change | Notes |
|---|---|---|---|
| `tick` | `last_turn_index = max(cursor, turn_index)` + append to events | — | Cursor monotonic; events capped at 200 |
| `tool_call` | `last_turn_index` advance + append to events | — | Same as tick |
| `agent_msg` | `last_turn_index` advance + append to events | — | Same as tick |
| `fault_injected` | append to faults with `observed: false` + advance cursor + append to events | — | fault_id keyed |
| `fault_observed` | mark fault `observed: true` + set `ttff_ms` once (first obs wins) + advance cursor | — | T-08-05: ttff_ms immutable after first set |
| `done` | `terminal_tag = event.tag`, `headline = event.headline` + advance cursor + append to events | — | Downstream: derivePageState reads terminal_tag |
| `error` | append to events + advance cursor | — | terminal_tag stays null (lane-failed signal, not classification) |
| `race_done` | **no change** | — | Session-level; consumed by derivePageState (Plan 02) |
| `ws_closed` | **no change** | `ws_status = "closed"` | Lane state preserved |
| `ws_error` | **no change** | `ws_status = "closed"` | Lane state preserved |

## WS Reconnect Cursor URL Format (D-45)

```
ws://<host>/api/race/ws?pure_mcp=<N>&pure_a2a=<N>&hybrid=<N>
```

Example on fresh connect (no events received yet):
```
ws://localhost:8008/api/race/ws?pure_mcp=-1&pure_a2a=-1&hybrid=-1
```

Example after receiving events on pure_mcp (turn 7) and pure_a2a (turn 3) before disconnect:
```
ws://localhost:8008/api/race/ws?pure_mcp=7&pure_a2a=3&hybrid=-1
```

The backend resumes each lane stream from its cursor — no replay of events the client already has for non-lagging lanes (D-45 rationale).

## run_id Validation Regex (T-08-05)

```
^[a-zA-Z0-9_-]{1,64}$
```

Reasoning:
- Rejects `/` — prevents path traversal (`../../etc/passwd`)
- Rejects `.` — prevents double-dot sequences
- Rejects `%` — prevents URL encoding bypass attempts
- 64-char max — bounded path segment length
- Only alphanumeric + `_` + `-` — minimal surface, consistent with UUID/slug run_id shapes

Belt-and-suspenders: `encodeURIComponent(run_id)` still applied in URL construction (T-08-04).

## Hook Return Shapes for Plans 04-06

### useRaceStream(enabled?: boolean): RaceState

```typescript
{
  pageState: PageState;         // "pre-race" on init → derivePageState feeds this in Plan 06
  lanes: {
    pure_mcp: LaneState;
    pure_a2a: LaneState;
    hybrid:   LaneState;
  };
  ws_status: "connecting" | "open" | "reconnecting" | "closed";
  run_id: string | null;        // always null in live mode
}
```

### useRaceReplay(run_id?: string): UseRaceReplayResult

```typescript
{
  trace:   RaceReplayPayload | null;  // null until fetch resolves
  loading: boolean;                   // true while fetch pending
  error:   string | null;             // null on success; "Invalid run_id" for bad IDs
}
```

### RaceReplayPayload (Phase 9 backend will return this)

```typescript
{
  run_id:         string;
  events:         RaceEvent[];   // full event log for replay scrubber
  schema_version: string;
}
```

## useRaceStream(enabled) Signature Note for Plan 06 Mobile Branch

```typescript
// Plan 06 usage in RacePage (mobile-summary gating):
const isMobile = useMediaQuery("(max-width:480px)");
const raceState = useRaceStream(!isMobile);
//                               ^^^^^^^^ enabled=false on mobile: no WS opened
//                                        hook still called unconditionally (rules-of-hooks safe)
```

The `enabled` flag is owned by Plan 03 and documented here so Plan 06 can wire it without needing to modify the hook. Plan 06 passes `enabled=!isMobile`; when false the effect returns immediately and no WebSocket is opened.

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED (raceReducer) | `2540490` | PASS — tests failed (module not found) before implementation |
| GREEN (raceReducer) | `036a38c` | PASS — 22/22 tests pass |
| RED (hooks) | `d98bc0c` | PASS — tests failed (module not found) before implementation |
| GREEN (hooks) | `67abe78` | PASS — 23/23 tests pass |

## Test Results

| File | Tests | Status |
|------|-------|--------|
| `raceReducer.test.ts` | 22 | PASS |
| `hooks/useRaceStream.test.ts` | 13 | PASS |
| `hooks/useRaceReplay.test.ts` | 10 | PASS |
| TypeScript `npx tsc --noEmit` | — | PASS |
| `npm run build` | — | PASS (3.65s) |

**Total: 45/45 tests pass.**

## Commits

| Task | Phase | Commit | Description |
|------|-------|--------|-------------|
| Task 1 | RED | `2540490` | test(08-03): add failing tests for raceReducer |
| Task 1 | GREEN | `036a38c` | feat(08-03): implement raceReducer pure state machine |
| Task 2 | RED | `d98bc0c` | test(08-03): add failing tests for useRaceStream + useRaceReplay |
| Task 2 | GREEN | `67abe78` | feat(08-03): implement useRaceStream and useRaceReplay hooks |

## Deviations from Plan

None — plan executed exactly as written.

The plan provided complete implementation code in the `<action>` blocks. Implementation followed the provided code with minor adaptations:

1. `useRaceReplay` initializes `loading: false` (not `Boolean(run_id)`) — the effect sets `loading=true` after validating the run_id, avoiding a flash of `loading=true` for invalid IDs.
2. `fetchRaceReplay` uses raw `fetch()` instead of the `requestJson<T>` helper — the stub endpoint has a race-specific error message pattern and its own validation gate that precedes the HTTP call.

Neither adaptation changes the observable contract consumed by Plans 04-06.

## Known Stubs

| Stub | File | Line | Reason |
|------|------|------|--------|
| `/api/race/runs/:run_id/trace` fetch endpoint | `frontend/src/lib/api/client.ts` | fetchRaceReplay body | Backend ships in Phase 9 HEAT-03 (D-48 deferred item). Call signature is complete; HTTP 404 returned until backend lands. |

The stub does not prevent Plan 03's goal (typed call signature + run_id validation) from being achieved. Plans 04-06 do not call fetchRaceReplay directly — they consume `useRaceReplay.trace` which will be null until Phase 9 ships the endpoint.

## Threat Surface Scan

No new network endpoints or auth paths introduced. All mitigations from the plan's threat register are implemented:

| Threat ID | Mitigation Applied |
|---|---|
| T-08-07 | `JSON.parse` in try/catch in `useRaceStream.onmessage`; malformed payloads silently dropped; reducer default `never` case |
| T-08-05 | `isValidRunId` regex check in `useRaceReplay` + `fetchRaceReplay` before any fetch |
| T-08-04 | `encodeURIComponent(run_id)` in `fetchRaceReplay` URL construction |
| T-08-09 | `EVENTS_FEED_CAP = 200` per lane in `raceReducer.ts` |
| T-08-16 | `enabled` flag gates WebSocket open in `useRaceStream`; effect returns early when false |
| T-08-10 | WS URL pinned to `window.location.host`; same-origin enforced by browser |

## Self-Check: PASSED
