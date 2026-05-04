---
phase: 14-race-demo-integration-fix
verified: 2026-05-03T21:05:00+05:30
status: human_needed
score: 13/14 must-haves verified
overrides_applied: 0
human_verification:
  - test: "Navigate to /race in a running browser. Click the 'Start Race' button. Observe that the RaceStatusStrip transitions out of 'pre-race' state, the button disappears, and WebSocket events begin streaming into the lane cards."
    expected: "Button visible in pre-race state. After click, wsRunId is set, useRaceStream opens a WS connection to /api/race/ws?run_id=<id>&..., live turn events appear in the three lane cards within a few seconds."
    why_human: "End-to-end WS live-streaming requires a running server and race harness. Cannot verify programmatically without starting the server and triggering real race execution. The wiring is correct in code but the observable behavior (events streaming into the UI) is a runtime property."
  - test: "Navigate to /race/<a valid run_id from data/runs/>. Drag the ReplayScrubber slider from the right end toward position 0. Observe the lane cards updating to reflect fewer events."
    expected: "At position 0, all lane cards show initial/empty state. At max, all events are applied and the done/replay state is shown. Intermediate positions show partial replay. The scrubber max equals (total events - 1), not a pinned turn index."
    why_human: "Seek state is derived via useMemo in the browser. A replay run_id fixture in data/runs/ is needed to confirm the scrubber range and visual update are correct."
---

# Phase 14: Race Demo Integration Fix — Verification Report

**Phase Goal:** Make the race demo functionally end-to-end — user can start a race via HTTP, watch live WebSocket events stream into the Race page, see the heatmap page-state reflect real data, and seek through replay via the scrubber.
**Verified:** 2026-05-03T21:05:00+05:30
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | POST /api/race/run returns HTTP 200 with run_id | ✓ VERIFIED | `api_race_run` at web.py:1039 returns `{"run_id": uuid4().hex[:16]}`; 7/7 endpoint tests pass |
| 2 | run_id matches ^[A-Za-z0-9_-]{1,64}$ | ✓ VERIFIED | `uuid4().hex[:16]` is all-hex [0-9a-f]; `test_happy_path_returns_200_and_run_id` asserts regex + `_validate_run_id` |
| 3 | run_race() launched as background asyncio.create_task | ✓ VERIFIED | web.py:1084 `asyncio.create_task(_do_run())`; `test_background_task_created` patches and asserts called_once |
| 4 | POST with invalid input returns HTTP 422 | ✓ VERIFIED | Pydantic field_validators on lanes/task_ids/n; 3 dedicated 422 tests pass |
| 5 | useRaceStream accepts runId as first param and injects run_id= into WS URL | ✓ VERIFIED | useRaceStream.ts:41 `function useRaceStream(runId: string = "", enabled: boolean = true)`; buildWsUrl:28 `?run_id=${encodeURIComponent(runId)}&${qs}` |
| 6 | RacePage calls POST /api/race/run on Start Race and stores run_id | ✓ VERIFIED | RacePage.tsx:69 `useState<string>("")`; lines 108-120 `handleStartRace` calls `startRace({task_ids, lanes, n})` and calls `setWsRunId(run_id)`; button at lines 206-215 with `data-testid="race-start-button"` |
| 7 | useRaceStream called with wsRunId — no more 422 on WS connect | ✓ VERIFIED | RacePage.tsx:74 `useRaceStream(wsRunId, !!wsRunId && !isMobile && !isReplay && !isOg)` — gated on non-empty wsRunId |
| 8 | enabled=false path still prevents WS open (T-08-16 not broken) | ✓ VERIFIED | useRaceStream.ts:50 `if (!enabled) return;`; dependency array includes runId so new WS opens on runId change |
| 9 | heatmap_has_data derived from real useRaceHeatmap data (not hardcoded false) | ✓ VERIFIED | RacePage.tsx:25 imports `useRaceHeatmap`; line 81 `const { data: heatmapData } = useRaceHeatmap()`; line 164 `const heatmap_has_data = !!heatmapData?.cells?.length` |
| 10 | derivePageState receives real heatmap_has_data and can reach sparse-heatmap | ✓ VERIFIED | RacePage.tsx:170 passes `heatmap_has_data` to `derivePageState`; hardcoded `false` is gone |
| 11 | ReplayScrubber.onScrub is not a no-op | ✓ VERIFIED | RacePage.tsx:223 `onScrub={setSeekPosition}`; stub comment "Phase 9 wires actual scrub-to-turn-index navigation" is absent (grep returned empty) |
| 12 | seekPosition state drives seekedReplayState via useMemo | ✓ VERIFIED | RacePage.tsx:95-106: `useState<number\|null>(null)` + `useMemo` reducing `replay.trace.events.slice(0, seekPosition+1)` through raceReducer |
| 13 | scrubber max = total event count - 1 (not turn index pinned at end) | ✓ VERIFIED | RacePage.tsx:222 `max={Math.max(0, (replay.trace?.events.length ?? 1) - 1)}` |
| 14 | Live WS events stream into Race page after Start Race click (end-to-end) | ? UNCERTAIN | Code wiring is complete but observable runtime behavior requires a running server |

**Score:** 13/14 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/a2a_vs_mcp/web.py` | POST /api/race/run route + RaceRunRequest model | ✓ VERIFIED | Lines 103-130: RaceRunRequest with field_validators; lines 1039-1085: `api_race_run` |
| `tests/race/test_race_run_endpoint.py` | 7-test suite covering happy path, 422s, background task | ✓ VERIFIED | File exists; 7/7 tests pass with `pytest tests/race/test_race_run_endpoint.py` |
| `frontend/src/features/race/hooks/useRaceStream.ts` | useRaceStream(runId, enabled) with run_id in WS URL | ✓ VERIFIED | Line 41: new signature; line 28: `run_id=${encodeURIComponent(runId)}&${qs}` |
| `frontend/src/features/race/RacePage.tsx` | wsRunId state, handleStartRace, useRaceHeatmap wiring, seekPosition+seekedReplayState, onScrub wired | ✓ VERIFIED | All five components present at verified lines |
| `frontend/src/lib/api/client.ts` | startRace() function, StartRaceBody/StartRaceResponse interfaces | ✓ VERIFIED | Lines 181-204; no duplicate declaration (memory obs 735 was a transient worktree state, resolved) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| POST /api/race/run | harness.run_race | `asyncio.create_task(_do_run())` at web.py:1084 | ✓ WIRED | `from .race.harness import run_race` at line 57; `await run_race(...)` at lines 1076-1082 |
| POST /api/race/run | MANAGER.publish | `_sync_ws_emitter` → `loop.create_task(_ws_emitter(event))` | ✓ WIRED | web.py:1067-1073; ws_emitter passed to run_race at line 1081 |
| RacePage startRace() | client.ts startRace() | `import { startRace } from "../../lib/api/client"` | ✓ WIRED | RacePage.tsx:30 |
| RacePage | useRaceStream | `useRaceStream(wsRunId, !!wsRunId && ...)` | ✓ WIRED | RacePage.tsx:74 |
| useRaceStream buildWsUrl | /api/race/ws | `run_id=` query param | ✓ WIRED | useRaceStream.ts:28 |
| RacePage useRaceHeatmap() | derivePageState heatmap_has_data | `!!heatmapData?.cells?.length` | ✓ WIRED | RacePage.tsx:81, 164, 170 |
| ReplayScrubber onScrub | setSeekPosition | `onScrub={setSeekPosition}` | ✓ WIRED | RacePage.tsx:223 |
| seekPosition | seekedReplayState (useMemo) | `events.slice(0, seekPosition+1).reduce(raceReducer, ...)` | ✓ WIRED | RacePage.tsx:99-106 |
| seekedReplayState | baseState | `seekedReplayState ?? replayState` in isReplay branch | ✓ WIRED | RacePage.tsx:157-159 |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| RacePage.tsx | `liveState` (via useRaceStream) | WebSocket `MANAGER.publish(run_id, event)` in `_ws_emitter` → `run_race()` | Yes — run_race() passes real harness events to ws_emitter | ✓ FLOWING (code path verified; end-to-end behavior is human item) |
| RacePage.tsx | `heatmapData` | `useRaceHeatmap()` → `fetchRaceHeatmap()` → GET /api/race/heatmap → `get_heatmap()` | Yes — aggregates from RUNS_DIR | ✓ FLOWING |
| RacePage.tsx | `seekedReplayState` | `replay.trace.events.slice(0, seekPosition+1).reduce(raceReducer, ...)` | Yes — derives from real trace data | ✓ FLOWING |
| RacePage.tsx | `wsRunId` | POST /api/race/run response → `setWsRunId(run_id)` | Yes — uuid4-derived from backend | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| POST /api/race/run returns 200 + run_id | `pytest tests/race/test_race_run_endpoint.py -v` | 7/7 passed | ✓ PASS |
| Invalid lane returns 422 | `pytest tests/race/test_race_run_endpoint.py::TestRaceRunEndpoint::test_invalid_lane_returns_422` | PASSED | ✓ PASS |
| n=0 returns 422 | `pytest tests/race/test_race_run_endpoint.py::TestRaceRunEndpoint::test_n_zero_returns_422` | PASSED | ✓ PASS |
| /api/race/run route registered in FastAPI | `python3 -c "from a2a_vs_mcp.web import app; print('/api/race/run' in [r.path for r in app.routes])"` | True | ✓ PASS |
| Frontend test suite green | `npm test -- --run` | 335/335 passed (38 test files) | ✓ PASS |
| Backend race test suite green | `pytest tests/race/ -q` | 213/213 passed | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| RACE-01 (integration) | 14-01 | HardnessType/HardnessProfile exposed via HTTP trigger | ✓ SATISFIED | HardnessProfile used in TaskSpec construction at web.py:1053-1061; imported at line 61 |
| RACE-02 (integration) | 14-01 | Three runners accessible via POST trigger | ✓ SATISFIED | lanes param passes to run_race(); web.py:1079-1082 |
| RACE-03 (integration) | 14-01 | Harness drives N parallel runs; emits WS events | ✓ SATISFIED | `n=body.n` passed to run_race; ws_emitter wires MANAGER.publish |
| RACE-04 (integration) | 14-01 | Recovery state machine fires during live run | ✓ SATISFIED | run_race() calls harness which calls classifier internally; no code change needed — wiring is the fix |
| RACE-05 (integration) | 14-01 | v1 tasks accessible via task_ids | ✓ SATISFIED | Pydantic validator checks task_ids against TASK_CONFIGS at web.py:116-121 |
| RACE-06 (integration) | 14-01 | failure_mode_classifier fires during run | ✓ SATISFIED | Same as RACE-04 — internal to run_race() harness; wired by the background task |
| RACE-07 (integration) | 14-01 | Mock APIs reachable during live run | ✓ SATISFIED | run_race() launches runners that call mock APIs; web layer trigger wired correctly |
| TRC-04 | 14-01 | WS event schema with turn_index per-lane | ✓ SATISFIED | /api/race/ws already existed (Phase 6/9); Phase 14 wires the trigger so events actually flow |
| UIRACE-01 | 14-02, 14-03 | RacePage renders live data + page-state machine correctly | ✓ SATISFIED | wsRunId state, useRaceStream wired, heatmap_has_data real |
| UIRACE-02 | 14-02 | WS connect/reconnect uses run_id query param | ✓ SATISFIED | buildWsUrl at useRaceStream.ts:28 |
| UIRACE-03 | 14-02 | Visual contract — no regression from wiring changes | ✓ SATISFIED | 335 frontend tests pass; __testState seam preserved |
| HEAT-01 | 14-03 | HardnessFailureHeatmap page state reachable (sparse-heatmap) | ✓ SATISFIED | heatmap_has_data = !!heatmapData?.cells?.length flows to derivePageState |
| HEAT-02 | 14-03 | heatmap_has_data drives page state machine | ✓ SATISFIED | RacePage.tsx:164-170 |
| HEAT-03 | 14-04 | ReplayScrubber seek changes displayed race state | ✓ SATISFIED (code) / ? HUMAN (visual) | onScrub={setSeekPosition}; seekedReplayState useMemo wired; visual confirmation needed |

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
|------|------|---------|----------|--------|
| `tests/race/test_race_run_endpoint.py` | (runtime warning) | `coroutine 'api_race_run.<locals>._do_run' was never awaited` | ℹ️ Info | Expected — tests patch `asyncio.create_task` which prevents the coroutine from running; the warning is a test-environment artifact, not a production code smell. Not a blocker. |

No stub patterns, hardcoded empty returns, or placeholder comments found in the four primary implementation files.

### Human Verification Required

#### 1. Live Race End-to-End Stream

**Test:** With the app running (`python serve_ui.py`), navigate to `/race`. Click the "Start Race" button (data-testid="race-start-button"). Watch the lane cards.
**Expected:** Button appears in pre-race state. After click, the button disappears (pageState transitions away from "pre-race"), RaceStatusStrip updates, and turn events appear in the pure_mcp / pure_a2a / hybrid lane cards within a few seconds. No console errors about 422 on WebSocket connect.
**Why human:** Requires a running server + race harness with mock APIs. The full chain (POST → asyncio.create_task → run_race → ws_emitter → MANAGER.publish → WS → React reducer → lane card render) is wired in code but its observable output is a runtime property that cannot be verified by static analysis or unit tests alone.

#### 2. Replay Scrubber Seek Behavior

**Test:** With the app running, navigate to `/race/<run_id>` using a known run_id from `data/runs/`. Observe the ReplayScrubber. Drag it from the far right toward position 0. Observe the lane cards.
**Expected:** At far right (max = total_events - 1), the full replay state is shown. Dragging left reduces the number of events applied, showing partial race progress. At position 0, only the first event is applied. The scrubber value updates as you drag.
**Why human:** Requires a real trace fixture in data/runs/ and a browser interaction with the MUI Slider component. The useMemo logic is sound but the visual update of lane cards when seekPosition changes is a browser runtime behavior.

### Gaps Summary

No blocking gaps. All 13 programmatically verifiable must-haves are VERIFIED. The single UNCERTAIN item (Truth 14: live WS streaming end-to-end) and the replay scrubber visual behavior both require a running server and browser interaction for final confirmation.

The traceability note: RACE-01 through RACE-07 and TRC-04 were already "Complete" in REQUIREMENTS.md (Phases 6-7). Phase 14's contribution is the **integration wiring** — the HTTP trigger (POST /api/race/run) that bridges the already-complete backend to a callable web surface, plus the frontend changes that consume the run_id and stream events live. This is correctly scoped in the REQUIREMENTS.md traceability table as "(integration)" entries.

---

_Verified: 2026-05-03T21:05:00+05:30_
_Verifier: Claude (gsd-verifier)_
