---
phase: 09-heatmap-replay-k3-calibration
plan: 02
subsystem: api
tags: [backend, fastapi, replay, python, race, ndjson]

# Dependency graph
requires:
  - phase: 06-tracerecorder-schema-gate-race-foundation
    provides: load_run + _validate_run_id (path-traversal guard) + RUNS_DIR + ndjson v1.0 schema
  - phase: 08-race-page-ui-visual-contract
    provides: fetchRaceReplay typed stub + RaceReplayPayload TS interface (client.ts:136-163) + useRaceReplay hook
  - phase: 09-heatmap-replay-k3-calibration/01
    provides: web.py race-routes block landing pad (heatmap route mounted at line 858); imports load_run, _validate_run_id, RUNS_DIR already in scope
provides:
  - GET /api/race/runs/{run_id}/trace FastAPI route returning {run_id, events, schema_version: "1.0"}
  - Path-traversal-guarded replay endpoint (400 on malformed run_id; 404 on missing file)
  - Events shipped verbatim (D-59 — backend `event_type` key NOT renamed)
affects:
  - frontend/src/features/race/hooks/useRaceReplay.ts — Phase 8 typed stub now satisfied by live backend
  - 09-03-replay-symmetry-tests — replay route is the operational surface; symmetry tests use the same load_run loader directly

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Validate-then-load route prologue (mirrors web.py:863-868 race_ws + Phase 6 V12 path-traversal guard)"
    - "Sync FastAPI def returning plain dict (matches api_remote_a2a_health style; payload schema locked client-side via TS RaceReplayPayload)"
    - "FastAPI TestClient + monkeypatch RUNS_DIR fixture pattern (mirrors test_replay_stub.py)"

key-files:
  created:
    - "tests/race/test_replay_route.py — 5 tests pinning route contract (happy path, 400 invalid, 404 missing, exact shape, verbatim D-59)"
  modified:
    - "src/a2a_vs_mcp/web.py — mounted GET /api/race/runs/{run_id}/trace immediately after the heatmap route (lines 869-887)"

key-decisions:
  - "Route placed immediately after /api/race/heatmap (web.py:858) and BEFORE the race_ws websocket (web.py:889) — co-locates HTTP race endpoints, mirrors PATTERNS guidance to keep race-routes block contiguous."
  - "No new imports needed — Plan 09-01 already lifted load_run, _validate_run_id, RUNS_DIR into web.py scope (lines 43-45)."
  - "schema_version is the literal string '1.0' (Phase 6 D-03 disk schema). Disk schema and frontend payload schema are the same value — no transform layer."
  - "Events shipped verbatim per D-59 — no backend-side `event_type` → `type` rename. Phase 8 useRaceReplay does not deep-consume events; deferral is safe until a future phase reads raw events on the frontend."
  - "Route is sync def (not async) — load_run is a small synchronous disk read; matches api_remote_a2a_health style and the rest of web.py's race-routes block."

patterns-established:
  - "Co-locate race HTTP routes (heatmap + replay) directly above the race_ws websocket route. Pattern continues for any future race endpoints."
  - "Hand-rolled TestClient + monkeypatch.setattr('a2a_vs_mcp.web.RUNS_DIR', tmp_path) for route tests that need an isolated runs directory."

requirements-completed: [HEAT-03]

# Metrics
duration: 2min
completed: 2026-04-30
---

# Phase 9 Plan 02: Replay Route Summary

**Mounted GET `/api/race/runs/{run_id}/trace` replay endpoint behind the existing `_validate_run_id` path-traversal guard + `load_run` ndjson loader; satisfies the Phase 8 typed `fetchRaceReplay` stub with the locked `{run_id, events, schema_version: "1.0"}` payload (HEAT-03).**

## Performance

- **Duration:** ~2 min
- **Started:** 2026-04-30T05:59:59Z
- **Completed:** 2026-04-30T06:01:48Z
- **Tasks:** 1 (type=auto tdd=true)
- **Files modified:** 2 (1 new test file + 1 modified src file)
- **Commits:** 2 (RED + GREEN)
- **Tests added:** 5 (all passing)
- **Pytest baseline:** 276 → 281 (+5, no regressions); race subset 167 → 172 (+5)

## Accomplishments

- `GET /api/race/runs/{run_id}/trace` is mounted in `web.py` and returns `{run_id, events, schema_version: "1.0"}` — exactly matching the Phase-8 frontend `RaceReplayPayload` interface so the existing `useRaceReplay` hook becomes a drop-in consumer with no client-side changes.
- Path-traversal guard via `_validate_run_id` runs **before** any path resolution — malformed run_ids (special characters, length > 64) return HTTPException 400 with the validator's `invalid run_id: ...` detail string.
- Missing-run files return HTTPException 404 with stable detail `"run not found"` (single string the frontend can pin against in error UIs).
- Events shipped verbatim per D-59. The disk-schema `event_type` discriminator is preserved — no backend-side rename to the frontend's `type` discriminator. Frontend deep-event-consumption is out-of-scope for Phase 9.
- No new imports needed — Plan 09-01 already pulled `load_run`, `_validate_run_id`, and `RUNS_DIR` into `web.py`'s import block (lines 43-45). The change is purely additive: 18 new lines (1 decorator + handler) below the heatmap route at line 858.

## Task Commits

Single task executed via TDD RED → GREEN cycle:

1. **Task 1 RED — failing tests** — `9dc03ec` (test): all 5 tests fail with 404 Not Found (route not mounted yet).
2. **Task 1 GREEN — route mounted** — `51ecc91` (feat): all 5 tests pass; full race regression green; full pytest green.

**Plan metadata commit:** _added below as final commit covering SUMMARY.md + STATE.md + ROADMAP.md._

## Files Created/Modified

### Created

- `tests/race/test_replay_route.py` — 5 tests pinning the route contract:
  - `test_happy_path_returns_payload` — 200 + `{run_id, events: [...], schema_version: "1.0"}` against an isolated tmp_path RUNS_DIR.
  - `test_invalid_run_id_returns_400` — `INVALID@CHAR` and 65-char run_ids both return 400 with `invalid run_id` detail.
  - `test_missing_run_returns_404` — well-formed but absent run_id returns 404 with `detail == "run not found"`.
  - `test_response_shape_matches_frontend_typed_stub` — top-level keys are EXACTLY `{run_id, events, schema_version}` (frontend RaceReplayPayload contract).
  - `test_events_shipped_verbatim_no_normalization` — events keep backend `event_type` key (D-59 deferral).

### Modified

- `src/a2a_vs_mcp/web.py` — added `@app.get("/api/race/runs/{run_id}/trace")` handler `api_race_run_trace` immediately after the heatmap route (mounted at lines 869-887). Sync `def`, plain dict return, validate-then-load prologue mirroring `race_ws`. No new imports (load_run, _validate_run_id, RUNS_DIR already at lines 43-45).

## Decisions Made

- **Route placement immediately after `/api/race/heatmap` (web.py:858) and BEFORE `race_ws` (web.py:889).** Keeps the race-routes block contiguous; matches PATTERNS.md guidance (`web.py — replay route` analog points to the validate-then-load prologue at race_ws line 863-868). Future race endpoints land in the same contiguous block.
- **Sync `def` (not async).** `load_run` is a small synchronous disk read; matches `api_remote_a2a_health` style at web.py:825. Async would have been theatre — bounded v1 trace files are ≤2MB and read in microseconds.
- **No backend-side `event_type` → `type` rename.** D-59 defers normalization. Phase 8 `useRaceReplay` does not deep-consume events (verified by Plan 09-01 RESEARCH §7 — zero `event_type` hits in `useRaceReplay.ts`). The disk schema `event_type` flows through unchanged. Test 5 pins the deferral.
- **schema_version is the literal string `"1.0"`.** Phase 6 D-03 disk schema; the frontend `RaceReplayPayload.schema_version` is typed as `string` so the literal lands cleanly.
- **No need to retire/replace the existing `web.py:43-44` imports of `load_run` and `_validate_run_id`.** Plan 09-01 already mounted those for other purposes (not yet — actually for the same potential replay future); the imports are now load-bearing for both the heatmap route's backend and this new replay route.

## Deviations from Plan

**None — plan executed exactly as written.**

The plan's literal code block at action Step 2 dropped into `web.py` cleanly. The plan's literal test scaffolding at action Step 3 worked verbatim with the `monkeypatch.setattr("a2a_vs_mcp.web.RUNS_DIR", tmp_path)` fixture path (verified by the `web.py:45` import block). No code-level surprises; no API mismatches; no pre-existing regressions surfaced.

The plan's pre-emptive note about `..%2F` URL-encoding being potentially decoded by FastAPI before reaching the route was honored — the test suite uses `INVALID@CHAR` (which DOES reach the route and is rejected by RUN_ID_REGEX) instead of relying on `..%2F`. Test 2 documents this choice inline.

## Authentication Gates

None encountered. The replay endpoint is unauthenticated by design (T-09-07 in the plan's threat register: hackathon-ephemeral demo, auth deferred to post-v2 scope).

## Issues Encountered

None. The plan's intent matched the codebase exactly; the test suite went from RED → GREEN in a single commit each.

## User Setup Required

None — no external service configuration required. The route is mounted in the existing FastAPI app (`a2a_vs_mcp.web.app`) and reads from the existing `data/runs/` directory.

## Verification Evidence

```
$ grep -c "/api/race/runs/{run_id}/trace" src/a2a_vs_mcp/web.py    # >= 1 required
1
$ grep -c "schema_version" src/a2a_vs_mcp/web.py                   # >= 1 required
2
$ grep -c "_validate_run_id" src/a2a_vs_mcp/web.py                 # >= 2 required (existing ws + new replay)
4
$ grep -c "load_run(run_id, RUNS_DIR)" src/a2a_vs_mcp/web.py       # >= 1 required
2
$ python -c "from fastapi.testclient import TestClient; from a2a_vs_mcp.web import app; r = TestClient(app).get('/api/race/runs/INVALID@CHAR/trace'); assert r.status_code == 400, r.status_code; print('OK')"
OK
$ pytest tests/race/test_replay_route.py -x -v          # 5/5 pass
5 passed in 1.09s
$ pytest tests/race/ -q                                  # full race regression
172 passed in 1.28s
$ pytest -q                                              # full project pytest
281 passed, 4 subtests passed in 12.33s
```

## Threat-model Coverage

Threat IDs from the plan's `<threat_model>` register, with implementation evidence:

- **T-09-06 (Tampering / EoP — path traversal):** mitigated. `_validate_run_id` enforces `^[A-Za-z0-9_-]{1,64}$` BEFORE path resolution. Test 2 (`test_invalid_run_id_returns_400`) pins the rejection for both `INVALID@CHAR` (regex-bad chars) and 65-char run_ids (length cap).
- **T-09-07 (Information Disclosure — no auth):** accepted. Hackathon-ephemeral demo; v1.0 already exposes traces via `/api/runs` and `/api/race/ws`. Auth is post-v2 scope.
- **T-09-08 (DoS — large trace files):** accepted. Bounded by harness (per_run_timeout_s=120, n=5 max). Trace files are ≤2MB per run in practice. Stream-read deferred to v2.1+.
- **T-09-09 (Tampering — live-LLM bypass):** mitigated by construction. Handler reads disk only via `load_run`; no LLM client imported in handler scope. HEAT-03 contract preserved.

No new threat surface beyond what the plan's `<threat_model>` already enumerated.

## Next Phase Readiness

- **Plan 09-03 (replay symmetry + K=3 calibration tests) is unblocked.** It does NOT depend on this route — symmetry tests call `load_run` directly. This route is the operational surface for the same loader.
- **Plan 09-04 (frontend HardnessFailureHeatmap.tsx wrapper) was unblocked by Plan 09-01 already.** Plan 09-04 does NOT depend on this replay route; the existing Phase 8 `useRaceReplay` will now succeed against the live backend in dev (`python serve_ui.py` + `cd frontend && npm run dev`, navigate to `/race/<known-run-id>`).
- **Phase 8 frontend contract satisfied.** `frontend/src/lib/api/client.ts:136-163` `fetchRaceReplay` will now receive 200 + `{run_id, events, schema_version}` against any valid run on disk; the typed stub becomes a fully functional client.

## TDD Gate Compliance

This plan is `type=execute` (not `type=tdd`), but its single task has `tdd="true"`. Per-task TDD gates verified in git log:

- Task 1: `9dc03ec` (test, RED) → `51ecc91` (feat, GREEN) ✓

No REFACTOR commit was needed — the GREEN implementation is 18 lines of straight-line code with no internal duplication or restructuring opportunity.

## Self-Check: PASSED

- Created files exist:
  - `tests/race/test_replay_route.py` ✓ FOUND
- Modified files include expected hooks:
  - `src/a2a_vs_mcp/web.py` contains `/api/race/runs/{run_id}/trace` route ✓
  - `src/a2a_vs_mcp/web.py` contains `load_run(run_id, RUNS_DIR)` (2 occurrences — race_ws + replay) ✓
- Commit hashes exist in git log:
  - `9dc03ec` ✓ FOUND (test RED Task 1)
  - `51ecc91` ✓ FOUND (feat GREEN Task 1)

---
*Phase: 09-heatmap-replay-k3-calibration*
*Completed: 2026-04-30*
