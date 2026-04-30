---
phase: 09-heatmap-replay-k3-calibration
plan: 01
subsystem: api
tags: [backend, fastapi, aggregator, python, heatmap, ndjson, race]

# Dependency graph
requires:
  - phase: 06-tracerecorder-schema-gate-race-foundation
    provides: TraceRecorder.record() additive event API + RunWriter ndjson persistence + load_run + _validate_run_id path-traversal guard
  - phase: 07-race-backend-lanes-harness-recovery
    provides: harness.run_race + MODEL/SEED_DISCLOSURE constants + race_done emit point + per-task hardness_profile registries
  - phase: 08-race-page-ui-visual-contract
    provides: HeatmapScaffold cell-shape contract + failureTagColor map + RacePage heatmap slot
provides:
  - HEATMAP_BASELINE frozen-dataclass module singleton (D-56)
  - get_heatmap() aggregator with in-process cache + invalidate_cache() hook (D-52, D-54)
  - Pinned-baseline filter silently excluding off-model/off-seed/off-task/missing-run_meta runs (D-55, D-57)
  - GET /api/race/heatmap FastAPI route returning {cells, baseline} payload locked to D-53
  - run_meta as the FIRST per-run trace event with model + seed + task_id (D-58)
  - harness invalidate_cache() hook fired immediately after race_done (D-54)
affects:
  - 09-04-frontend-heatmap-wrapper (consumes /api/race/heatmap payload + footer baseline)
  - 09-02-replay-route (shares run_meta envelope contract; replay still loads off-baseline runs)
  - 09-03-replay-symmetry-tests (run_meta is now part of every recorded trace)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Module-level frozen dataclass + to_dict() for pinned config (mirrors race/types.py HardnessProfile)"
    - "Process-local _CACHE dict keyed by tuple(sorted(...)) for order-independent cache keys (D-54)"
    - "Late import inside function body to break would-be circular dependency between harness.py and heatmap.py (heatmap -> config -> harness)"
    - "Pure-function aggregator over event lists with next((e for e in ... if ...), None) idiom (mirrors metrics.py)"
    - "Sync FastAPI def returning plain dict (not Pydantic) — payload schema locked client-side via TS types (mirrors fetchRaceReplay)"

key-files:
  created:
    - "src/a2a_vs_mcp/race/config.py — HEATMAP_BASELINE singleton + HeatmapBaseline frozen dataclass"
    - "src/a2a_vs_mcp/race/heatmap.py — aggregator + cache + filter + per-run terminal-tag helper"
    - "tests/race/test_run_meta_event.py — 7 tests pinning HEATMAP_BASELINE values + run_meta first-event invariant"
    - "tests/race/test_heatmap_aggregator.py — 13 tests pinning aggregator behavior + route smoke"
  modified:
    - "src/a2a_vs_mcp/race/harness.py — emits run_meta after recorder construction (D-58); calls invalidate_cache() after race_done emit (D-54)"
    - "src/a2a_vs_mcp/web.py — imports get_heatmap; mounts GET /api/race/heatmap"

key-decisions:
  - "Late import of invalidate_cache inside run_race body (after race_done) to avoid module-load-order issues between harness.py and heatmap.py"
  - "heatmap.py landed FULLY in Task 1 GREEN (not split across Task 1 stub + Task 2 implementation) because the harness late import requires the module to be importable for the test suite to run"
  - "_per_run_terminal_tag() reads done.score_pass + presence/absence of fault_observed event to map to one of the 5 terminal tags, mirroring harness._per_run_tag without re-running the Detector state machine"
  - "TraceRecorder.record() takes positional event_type + **payload (not a dict argument); plan instructions assumed dict argument so emission code rewrote to recorder.record('run_meta', model=..., seed=..., task_id=...) and let the recorder auto-stamp lane/run_id/turn_index/trace_schema_version"
  - "Cache key uses tuple(sorted(HEATMAP_BASELINE.task_ids)) per CONTEXT §Specifics for order-independence"

patterns-established:
  - "Pinned-baseline aggregator + cache pattern: filter on first-event run_meta; rebuild on demand from disk; clear cache on race_done lifecycle event"
  - "D-57 silent-exclusion contract: missing/wrong run_meta is dropped without log or visual marker"
  - "Sync FastAPI route co-located with race_ws (web.py:857-868) for race-domain endpoints"

requirements-completed: [HEAT-01, HEAT-02]

# Metrics
duration: 6min
completed: 2026-04-30
---

# Phase 9 Plan 01: Heatmap Backend Summary

**Pinned-baseline (model=claude-sonnet-4-6, seed=42, 3 v1 task_ids) heatmap aggregator with in-process cache, run_meta first-event envelope, and GET /api/race/heatmap returning the locked {cells, baseline} payload.**

## Performance

- **Duration:** 6 min
- **Started:** 2026-04-30T05:49:46Z
- **Completed:** 2026-04-30T05:55:25Z
- **Tasks:** 2 (both type=auto tdd=true)
- **Files modified:** 5 (2 created src + 2 created tests + 2 modified src)
- **Commits:** 4 (RED + GREEN per task)
- **Tests added:** 20 (all passing)
- **Pytest baseline:** 256 → 276 (+20, no regressions)

## Accomplishments

- `HEATMAP_BASELINE` is now the single source of truth for the closing-artifact heatmap. The constant lives in `src/a2a_vs_mcp/race/config.py`; the footer baseline payload is rendered from it; the aggregator filter consults it; the cache key is derived from it. Drift between aggregation scope and footer copy is now structurally impossible.
- The harness emits `run_meta` as the first event of every per-run trace (D-58). The event carries `model`, `seed`, `task_id`, `lane`, `run_id`, and `trace_schema_version` — enough to filter aggregation downstream without coupling to filename parsing.
- `GET /api/race/heatmap` returns `{cells, baseline}` server-side. Cells follow the D-53 minimal shape exactly: `{hardness_type, lane, dominant_tag, recovery_rate {num, den}, sample_run_id}`. No tag distribution, no per-fault array, no extra metadata.
- Off-baseline runs (off-model, off-seed, off-task, missing run_meta) are silently excluded (D-55, D-57). Pre-D-58 legacy runs in `data/runs/` cannot pollute the closing artifact.
- The harness fires `invalidate_cache()` immediately after the `race_done` ws emit (D-54). The next GET rebuilds from disk in microseconds for the bounded v1 corpus.

## Task Commits

Each task was committed atomically using the TDD RED → GREEN cycle:

1. **Task 1 RED — failing tests for HEATMAP_BASELINE + run_meta** — `7f2d03b` (test)
2. **Task 1 GREEN — config.py + heatmap.py + harness emit/invalidate** — `1a58496` (feat)
3. **Task 2 RED — failing route test + aggregator pinning tests** — `1c7aae4` (test)
4. **Task 2 GREEN — mount /api/race/heatmap route** — `0ecd137` (feat)

**Plan metadata commit:** _added below as final commit covering SUMMARY.md + STATE.md + ROADMAP.md._

## Files Created/Modified

### Created

- `src/a2a_vs_mcp/race/config.py` — `HeatmapBaseline` frozen dataclass + module-level `HEATMAP_BASELINE` singleton, re-exporting `MODEL`/`SEED_DISCLOSURE` from `harness.py` to avoid value drift.
- `src/a2a_vs_mcp/race/heatmap.py` — `get_heatmap()`, `invalidate_cache()`, `_build_cells()`, `_matches_baseline()`, `_per_run_terminal_tag()`. Pure aggregator with module-level `_CACHE` keyed by `tuple(sorted(task_ids))`.
- `tests/race/test_run_meta_event.py` — 7 tests covering `HEATMAP_BASELINE` values + `to_dict()` shape + frozen invariant + run_meta first-event + payload shape + per-run emission.
- `tests/race/test_heatmap_aggregator.py` — 13 tests covering payload shape, empty-corpus state, baseline-filter exclusion (4 cases), cell-shape exactness (3 cases), cache invalidation + key shape + identity, and FastAPI route smoke.

### Modified

- `src/a2a_vs_mcp/race/harness.py` — added `recorder.record("run_meta", model=MODEL, seed=SEED_DISCLOSURE, task_id=spec.task_id)` immediately after `recorder = recorder_factory(...)` in the schedule loop, and `from .heatmap import invalidate_cache; invalidate_cache()` immediately after the `ws_emitter({"event_type": "race_done", ...})` call.
- `src/a2a_vs_mcp/web.py` — added `from .race.heatmap import get_heatmap` to the existing race import block, and mounted `@app.get("/api/race/heatmap")` returning `get_heatmap()` directly. Sync `def`, plain dict return, mirrors `api_remote_a2a_health`.

## Decisions Made

- **`heatmap.py` landed in full during Task 1 GREEN rather than split across Task 1 (stub) and Task 2 (full implementation).** The harness's late `from .heatmap import invalidate_cache` must resolve for `run_race` to complete; landing only a stub would leave Task 1's tests passing but Task 2's tests blocked behind a half-built module. Full implementation in one shot is also lower risk because the cache + filter + cell-shape logic is tightly coupled. Task 2 then needed only the FastAPI route + the test suite — a clean separation of unit-level (Task 1) vs HTTP-level (Task 2) verification.
- **Late `from .heatmap import invalidate_cache` inside the `run_race` function body** (rather than at the top of `harness.py`). Reason: `config.py` imports from `harness.py`, and `heatmap.py` imports from `config.py`. A top-level harness → heatmap import would create a circular dependency at module load. The late import keeps the dependency graph one-directional (`heatmap → config → harness`) while still ensuring cache invalidation fires once per `race_done`. This pattern is documented inline in `harness.py`.
- **`_per_run_terminal_tag` reads `done.score_pass` + presence/absence of `fault_observed`** rather than re-running the K=3 Detector state machine inside the aggregator. The runner's scorer already minted the per-run outcome via `Detector` (D-31..D-34); the aggregator's job is to bucket + count. Mirroring `harness._per_run_tag` semantics keeps a single classification source of truth in the codebase.
- **`TraceRecorder.record()` API discovery — positional event_type + kwargs, not a dict argument.** The Plan instructions wrote the run_meta emit as `recorder.record({"event_type": "run_meta", ...})`. Reading `src/a2a_vs_mcp/trace.py:36` confirmed the actual signature is `def record(self, event_type: str, **payload: Any)`, with `trace_schema_version`/`lane`/`run_id`/`turn_index`/`index` auto-stamped. The implementation uses `recorder.record("run_meta", model=MODEL, seed=SEED_DISCLOSURE, task_id=spec.task_id)` and lets the recorder's auto-stamping fill in the envelope fields. This is captured in the test `test_run_meta_payload_shape` which asserts both the explicit fields and the auto-stamped `trace_schema_version`.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Plan's `recorder.record({...})` dict-argument call did not match the actual `TraceRecorder.record(event_type: str, **payload)` signature.**

- **Found during:** Task 1 GREEN (writing the harness run_meta emit).
- **Issue:** The plan's verbatim code block called `recorder.record({"event_type": "run_meta", ...})` — passing a dict positionally would have stored `event_type="{'event_type': 'run_meta', ...}"` (the entire dict as the event_type string) and dropped every payload field on the floor. Tests would have failed on `first["event_type"] == "run_meta"`.
- **Fix:** Used the recorder's actual API: `recorder.record("run_meta", model=MODEL, seed=SEED_DISCLOSURE, task_id=spec.task_id)`. Let `TraceRecorder.record()` auto-stamp `trace_schema_version`, `lane`, `run_id`, `turn_index`, `index`, `timestamp_ms`, and `phase` (lines 36-72 of `src/a2a_vs_mcp/trace.py`). The decision is captured in `key-decisions` above and in the harness inline comment.
- **Files modified:** `src/a2a_vs_mcp/race/harness.py`.
- **Verification:** `tests/race/test_run_meta_event.py::test_run_meta_payload_shape` asserts both the explicit fields (`model`, `seed`, `task_id`, `lane`, `run_id`) AND the auto-stamped `trace_schema_version == "1.0"`.
- **Committed in:** `1a58496` (Task 1 GREEN).

**2. [Rule 3 — Blocking] `heatmap.py` landed earlier than the plan structured it.**

- **Found during:** Task 1 GREEN (running `pytest tests/race/test_run_meta_event.py`).
- **Issue:** The plan placed `heatmap.py` creation in Task 2, but Task 1 modifies `harness.py` to call `from .heatmap import invalidate_cache` after every race. Task 1's tests run `harness.run_race(...)` end-to-end — the late import would fail with `ModuleNotFoundError` if `heatmap.py` did not exist yet, blocking Task 1's GREEN gate.
- **Fix:** Landed the FULL `heatmap.py` (including `get_heatmap()` + `_build_cells()` + helpers) during Task 1 GREEN. Task 2 then narrowed to: route mount + aggregator/route test suite.
- **Files modified:** `src/a2a_vs_mcp/race/heatmap.py` (created in Task 1 instead of Task 2).
- **Verification:** Task 1 tests pass (`pytest tests/race/test_run_meta_event.py`); Task 2 tests pass (`pytest tests/race/test_heatmap_aggregator.py`); no integration gap.
- **Committed in:** `1a58496` (Task 1 GREEN). Task 2 GREEN (`0ecd137`) only added the FastAPI route.

---

**Total deviations:** 2 auto-fixed (1 bug in plan instructions, 1 task-ordering blocker).
**Impact on plan:** Both auto-fixes were necessary for correctness. No scope creep — the same files and tests landed; only the order of file creation across the two tasks shifted. Net commits remain RED → GREEN per task as TDD specified.

## Issues Encountered

None. The plan's intent was crisp; only the two auto-fixes above (recorder API mismatch + heatmap.py ordering) needed adjustment from the literal plan text. All 20 new tests passed on the first GREEN run after each adjustment, and all 256 prior pytest tests remain green.

## User Setup Required

None — no external service configuration required. The route is mounted in the existing FastAPI app and runs against the existing `data/runs/` directory.

## Verification Evidence

```
$ grep -c "HEATMAP_BASELINE" src/a2a_vs_mcp/race/config.py    # >= 2 required
3
$ grep -c "frozen=True" src/a2a_vs_mcp/race/config.py         # >= 1 required
2
$ python -c "from a2a_vs_mcp.race.config import HEATMAP_BASELINE; print(HEATMAP_BASELINE.to_dict())"
{'model': 'claude-sonnet-4-6', 'seed': 42, 'task_ids': ['summarize_repo', 'negotiate_meeting', 'book_travel']}
$ grep -c "run_meta" src/a2a_vs_mcp/race/harness.py           # >= 1 required
4
$ grep -c "invalidate_cache" src/a2a_vs_mcp/race/harness.py   # >= 1 required
2
$ grep -c "def get_heatmap" src/a2a_vs_mcp/race/heatmap.py    # == 1 required
1
$ grep -c "def invalidate_cache" src/a2a_vs_mcp/race/heatmap.py   # == 1 required
1
$ grep -c "tuple(sorted" src/a2a_vs_mcp/race/heatmap.py       # >= 1 required
2
$ grep -c "/api/race/heatmap" src/a2a_vs_mcp/web.py           # >= 1 required
1
$ grep -c "from .race.heatmap import get_heatmap" src/a2a_vs_mcp/web.py   # == 1 required
1
$ grep -E "tag_distribution|per_fault_array|extra_meta" src/a2a_vs_mcp/race/heatmap.py | grep -v '^#'   # 0 matches required
(no output)
$ python -c "from fastapi.testclient import TestClient; from a2a_vs_mcp.web import app; r = TestClient(app).get('/api/race/heatmap'); assert r.status_code == 200; p = r.json(); assert set(p.keys()) == {'cells', 'baseline'}; assert p['baseline']['model'] == 'claude-sonnet-4-6'; print('OK')"
OK
$ pytest tests/race/test_run_meta_event.py -x       # 7/7 pass
7 passed in 0.68s
$ pytest tests/race/test_heatmap_aggregator.py -x   # 13/13 pass
13 passed in 0.79s
$ pytest tests/race/ -q                             # full race regression
167 passed in 1.24s
$ pytest -x -q                                      # full project pytest
276 passed, 4 subtests passed in 11.82s
```

## Next Phase Readiness

- **Plan 09-02 (replay route) is unblocked.** It can proceed in parallel; no shared files conflict (web.py route additions are append-only and the replay route lives in a different decorator block).
- **Plan 09-03 (replay symmetry + K=3 calibration tests) is unblocked.** The new `run_meta` envelope is harmless to the symmetry test (it does not affect `Detector(K=3)` consumption — Detector reads only post-`fault_injected` events).
- **Plan 09-04 (frontend wrapper) is unblocked.** The locked payload contract (`{cells, baseline}` + D-53 cell shape + `baseline.task_ids` as list) matches what the wrapper expects per `09-RESEARCH.md` §HEAT-02.

## TDD Gate Compliance

This plan is `type=execute` (not `type=tdd`), but each individual task has `tdd="true"`. Per-task TDD gates verified in git log:

- Task 1: `7f2d03b` (test) → `1a58496` (feat) ✓
- Task 2: `1c7aae4` (test) → `0ecd137` (feat) ✓

No REFACTOR commits were needed — both GREEN implementations passed cleanly without restructuring.

## Self-Check: PASSED

- Created files exist:
  - `src/a2a_vs_mcp/race/config.py` ✓ FOUND
  - `src/a2a_vs_mcp/race/heatmap.py` ✓ FOUND
  - `tests/race/test_run_meta_event.py` ✓ FOUND
  - `tests/race/test_heatmap_aggregator.py` ✓ FOUND
- Modified files include expected hooks:
  - `src/a2a_vs_mcp/race/harness.py` contains `run_meta` and `invalidate_cache` ✓
  - `src/a2a_vs_mcp/web.py` contains `/api/race/heatmap` route ✓
- Commit hashes exist in git log:
  - `7f2d03b` ✓ FOUND (test RED Task 1)
  - `1a58496` ✓ FOUND (feat GREEN Task 1)
  - `1c7aae4` ✓ FOUND (test RED Task 2)
  - `0ecd137` ✓ FOUND (feat GREEN Task 2)

---
*Phase: 09-heatmap-replay-k3-calibration*
*Completed: 2026-04-30*
