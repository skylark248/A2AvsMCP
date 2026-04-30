---
phase: 10-og-image-and-sharing
plan: 02
subsystem: api
tags: [fastapi, og-image, meta-tag-injection, mock-render, single-flight-cache, lifespan]

requires:
  - phase: 10-og-image-and-sharing
    provides: og_lifespan, OG_RENDER_LOCK, OG_DIR, og_cache_path, cleanup_stale, render_og_png, render_heatmap_png, OG_LAYOUT_VERSION (10-01)
  - phase: 06-tracerecorder-schema-gate-race-foundation
    provides: _validate_run_id (race/replay.py), RUNS_DIR (race/runs.py)
provides:
  - GET /race (SPA root)
  - GET /race/{run_id} HTML route with og:image + twitter:image meta-tag injection (OG-01)
  - GET /race/{run_id}/og.png — single-flight cached PNG route (404-before-spawn, 503-no-cache-write)
  - GET /race/{run_id}/heatmap.png — heatmap surface mirror
  - og_lifespan registered on FastAPI app (singleton Browser across requests, D-61)
  - 10-test mock-render matrix (D-63: zero Chromium in CI)
affects: [phase-10-og-frontend (10-03/10-04/10-05 consumers)]

tech-stack:
  added: []
  patterns:
    - "Module-level binding of optional-dep render fns enables monkeypatch.setattr injection in tests (D-63)."
    - "html.escape(quote=True) on every interpolated value defends against attribute-injection in OG meta tags (T-10-02-04)."
    - "Single-flight cache: outer-then-inner cache.exists() check inside `async with OG_RENDER_LOCK` prevents duplicate Chromium spawns under race (Pitfall 6)."
    - "Test fixture replaces app.router.lifespan_context with a no-op asynccontextmanager so TestClient's `with` block populates app.state.og_browser without needing Playwright."

key-files:
  created:
    - tests/race/test_og_routes.py (10 tests)
  modified:
    - src/a2a_vs_mcp/web.py (lifespan kwarg, _read_index_html, _inject_og_meta, /race, /race/{run_id} HTML, /race/{run_id}/og.png, /race/{run_id}/heatmap.png)

key-decisions:
  - "Adopted `with TestClient(app) as client:` per test (instead of bare `client = TestClient(app)`) so the no-op lifespan_context fires and stamps app.state.og_browser. Plan acceptance criterion of `grep -c 'TestClient(app)' >= 8` still satisfied (count = 9)."
  - "Tests collected = 10 (vs plan-stated 9). 9 def test_ functions; test 7 parametrized 2 ways = 10 collected. Plan miscounted parametrize expansion."
  - "Test fixture monkeypatches both `a2a_vs_mcp.race.og.OG_DIR` and `a2a_vs_mcp.web.OG_DIR` (raising=False) because web.py imports OG_DIR at module load time and the route reads the bound name."

patterns-established:
  - "Lifespan-bypass test fixture: replace `app.router.lifespan_context` with a no-op asynccontextmanager that pre-stamps app.state, then use `with TestClient(app) as client:` for each test."
  - "Module-level render-fn imports + monkeypatch.setattr targeting the consumer module — keeps integration tests (route-level) free from Chromium while still verifying every code path of the route handler."

requirements-completed: [OG-01, OG-02, OG-04]

duration: 18min (combined: ~10min initial agent execution + ~8min recovery)
completed: 2026-04-30
---

# Phase 10 — Plan 02 Summary

**FastAPI route mount: HTML route with OG/Twitter meta-tag injection, two PNG routes (og + heatmap) with single-flight cache + 503 fail-path, all gated under a 10-test D-63 mock-render matrix.**

## Performance

- **Duration:** ~18 min total (initial executor 10 min before quota kill + 8 min orchestrator-resume).
- **Started:** 2026-04-30T18:46:00Z
- **Completed:** 2026-04-30T21:50:00Z
- **Tasks:** 3/3
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments

- Registered `og_lifespan` on the FastAPI app (D-61: singleton Browser + asyncio.Lock alive across requests).
- Mounted `GET /race` (SPA root) + `GET /race/{run_id}` (HTML w/ OG meta-tag injection on known runs, crawler-safe omission on unknown).
- Mounted `GET /race/{run_id}/og.png` and `GET /race/{run_id}/heatmap.png` with single-flight `OG_RENDER_LOCK`-serialized renders, double-checked cache, 404-before-Chromium-spawn for unknown runs, 503-no-cache-write on render exception (D-62).
- Shipped 10-test D-63 matrix (`tests/race/test_og_routes.py`) covering OG-01/OG-02/OG-04 invariants without spawning Chromium.

## Task Commits

1. **Task 1: Wire og_lifespan + /race + /race/{run_id} HTML route** — `28299a6` (feat)
2. **Task 2: /race/{run_id}/og.png + /race/{run_id}/heatmap.png routes** — `12cffd7` (feat, recovery commit; orchestrator-salvaged from quota-killed agent)
3. **Task 3: D-63 mocked-render matrix (10 tests)** — `b574912` (test, recovery commit)

## Files Created/Modified

- `tests/race/test_og_routes.py` (created, 196 LOC) — 10-test D-63 mock matrix; lifespan-bypass fixture; helper `_write_run` for run_meta NDJSON seeding.
- `src/a2a_vs_mcp/web.py` (modified, +135 LOC) — imports from `race.og`/`race.replay`/`race.runs`/`race.config`; `app = FastAPI(..., lifespan=og_lifespan)`; `_INDEX_HTML_CACHE` + `_read_index_html()` + `_inject_og_meta()`; 4 new routes.

## Decisions Made

- **Lifespan-bypass test pattern.** og_lifespan imports playwright lazily; in CI playwright is uninstalled. Replacing `app.router.lifespan_context` with a no-op asynccontextmanager (and using `with TestClient(app) as client:` per test) populates `app.state.og_browser=None` without spawning Chromium. Routes pass that None to monkeypatched render fns, which never dereference it.
- **Test count: 10 (plan said 9).** 9 def test_ functions; test 7 parametrized 2 ways. Plan miscounted parametrize expansion (5*1 + 1*2 + 3*1 = 10, not 9).
- **monkeypatch both OG_DIR re-exports.** `a2a_vs_mcp.web.OG_DIR` is the binding the route reads; `a2a_vs_mcp.race.og.OG_DIR` is the binding `cleanup_stale()` and `og_cache_path()` read internally. Both must be patched for the fixture-tmp_path to win.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Required] Added lifespan-bypass to og_env fixture**
- **Found during:** Task 3 (test_cache_miss_renders_once_and_writes returned 503 instead of 200).
- **Issue:** Plan's fixture monkeypatched config + dirs but did not address the og_lifespan import-time playwright dep. TestClient(app) without `with` block doesn't run lifespan, so app.state.og_browser is never set; with `with` block, real og_lifespan tries to import playwright and crashes.
- **Fix:** Added `monkeypatch.setattr(app.router, "lifespan_context", _noop_lifespan)` where `_noop_lifespan` is an asynccontextmanager that sets `app.state.og_browser = None` and yields. Wrapped each test's `client = TestClient(app)` in a `with TestClient(app) as client:` block so the no-op lifespan fires.
- **Files modified:** tests/race/test_og_routes.py.
- **Verification:** All 10 tests pass; full backend suite 342 passed (no regression).
- **Committed in:** b574912 (Task 3 commit).

**2. [Rule 4 — Spec drift] Deviated from grep counts in plan acceptance criteria**
- **Found during:** Final verification.
- **Issue:** Plan said `grep -c '^def test_' returns 8`. Actual count = 9 (Test 1-9 unique functions). Plan said `grep -c 'TestClient(app)' >= 8`. Actual count = 9 (one per test, including parametrized).
- **Fix:** Documented in this SUMMARY. The plan's grep targets reflect a transient draft; the actual implementation is more rigorous (one TestClient(app) per test, not one shared at module level).
- **Files modified:** none (deviation is in test count, not test content).
- **Verification:** `grep -c '^def test_' tests/race/test_og_routes.py` = 9; `grep -c 'TestClient(app)' tests/race/test_og_routes.py` = 9.
- **Committed in:** b574912 (Task 3 commit).

---

**Total deviations:** 2 auto-fixed (1 required correctness fix, 1 spec drift).
**Impact on plan:** Lifespan-bypass essential for D-63 (zero Chromium in CI). Spec-drift deviation is bookkeeping only — test coverage exceeds plan.

## Issues Encountered

- **Quota exhaustion mid-execution.** Initial gsd-executor agent for plan 10-02 hit Anthropic extra-usage quota during Task 2 commit + Task 3 file creation. Per `feedback_subagent_quota_recovery` memory: pre-existing committed work (Task 1: 28299a6) preserved; uncommitted Task 2 web.py modifications salvaged + committed as recovery commit (12cffd7); Task 3 written inline by orchestrator (b574912). No work duplicated.

## User Setup Required

None — backend route mount only.

## Next Phase Readiness

- Wave 2 sibling 10-03 (RacePage `?og=1` + heatmap strip) can target `data-og-anchor` knowing the backend route exists.
- Wave 3 10-04 (CopyHeadlineImageButton) does not depend on these routes (client-side canvas snapshot fallback).
- Wave 4 10-05 (mobile `<img>` consumer) can rely on `/race/{run_id}/og.png` being live.

---
*Phase: 10-og-image-and-sharing*
*Completed: 2026-04-30*
