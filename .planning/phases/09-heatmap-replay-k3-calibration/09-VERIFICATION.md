---
phase: 09-heatmap-replay-k3-calibration
verified: 2026-04-30T06:27:31Z
status: passed
score: 21/21 must-haves verified
overrides_applied: 0
---

# Phase 9: Heatmap, Replay & K=3 Calibration Verification Report

**Phase Goal:** Heatmap, Replay & K=3 Calibration — Hardness-vs-failure heatmap, deterministic replay, multi-task K=3 sweep
**Verified:** 2026-04-30T06:27:31Z
**Status:** passed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

ROADMAP Success Criteria + must-haves merged from 4 PLAN.md frontmatters.

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1   | ROADMAP SC1 — `/race` heatmap rows × cols, cell encoding, keyboard focus, "directional · n=3 tasks · v1" pill in `secondary.main` | ✓ VERIFIED | HardnessFailureHeatmap.tsx renders directional Chip (`color="secondary"`, label literal at line 62), delegates to HeatmapScaffold (line 67); 9 component tests pass |
| 2   | ROADMAP SC2 — 5-pill legend always visible + footer shows model · seed · pinned task IDs | ✓ VERIFIED | Legend maps `failureTagColor` (line 71) including data=null branch; footer reads `data.baseline.model · seed · task_ids.join(", ")` at line 93 |
| 3   | ROADMAP SC3 — `/race/<run_id>` reads `data/runs/<run_id>.json` (no live LLM); recovery state machine identical on replay; two-layer fixture test (snapshot + `--update-snapshots`) | ✓ VERIFIED | web.py:869 mounts replay route via `load_run` (disk-only); test_replay_symmetry.py 18 fixtures parametrized; conftest.py registers `--update-snapshots` |
| 4   | ROADMAP SC4 — K∈{2,3,4,5} sweep across 3 v1 tasks confirms K=3 expected for every trace; test at `tests/test_recovery_calibration.py` | ✓ VERIFIED | tests/test_recovery_calibration.py exists at exact ROADMAP path; K=3 lock + K-drift sweep (3 tasks × 3 K values); all parametrize cases pass |
| 5   | GET /api/race/heatmap returns `{cells, baseline}` with baseline = HEATMAP_BASELINE.to_dict() | ✓ VERIFIED | TestClient smoke: `{'model': 'claude-sonnet-4-6', 'seed': 42, 'task_ids': [...]}` returned; web.py:858 |
| 6   | Aggregator silently excludes off-baseline runs (D-55, D-57) | ✓ VERIFIED | test_heatmap_aggregator.py 13 tests pass; 4 distinct exclusion cases (off-model, off-seed, off-task, missing run_meta) |
| 7   | Cache invalidates on race_done — first GET after race_done rebuilds from disk (D-54) | ✓ VERIFIED | harness.py:493-494 late-imports + calls `invalidate_cache()` after race_done emit; test_invalidate_cache_clears_state pass |
| 8   | Harness emits run_meta as the first event of every run (D-58) | ✓ VERIFIED | harness.py:367-374 emits run_meta immediately after recorder construction; test_run_meta_event.py 7/7 pass |
| 9   | Cells contain only D-53 keys (hardness_type, lane, dominant_tag, recovery_rate, sample_run_id) | ✓ VERIFIED | grep `tag_distribution\|per_fault_array\|extra_meta` in heatmap.py returned 0; cell-shape exactness tests pass |
| 10  | GET /api/race/runs/{run_id}/trace returns `{run_id, events, schema_version: "1.0"}` | ✓ VERIFIED | test_replay_route.py 5/5 pass; happy-path returns expected shape |
| 11  | Malformed run_id → 400 with `_validate_run_id`-derived detail | ✓ VERIFIED | TestClient smoke `INVALID@CHAR` → 400 confirmed; test_invalid_run_id_returns_400 pass |
| 12  | Valid-format but non-existent run_id → 404 | ✓ VERIFIED | TestClient smoke `r-doesnotexist` → 404 confirmed; test_missing_run_returns_404 pass |
| 13  | Response payload matches frontend `RaceReplayPayload` shape (drop-in for useRaceReplay) | ✓ VERIFIED | test_response_shape_matches_frontend_typed_stub asserts exact key set |
| 14  | No live LLM, events shipped verbatim from disk | ✓ VERIFIED | Handler at web.py:869+ uses `load_run` only; test_events_shipped_verbatim_no_normalization pass |
| 15  | For K=3, every fixture produces expected_terminal_tag | ✓ VERIFIED | test_k3_produces_expected_tag passes 18 parametrize cases (9 §Assignment + 9 boundary) |
| 16  | For each task × K∈{2,4,5}, ≥1 fixture's terminal tag differs from K=3 | ✓ VERIFIED | test_off_k_drift_observed_per_task passes all 9 cells; 9 boundary fixtures authored to make drift observable |
| 17  | --update-snapshots rewrites instead of asserting; default mode asserts | ✓ VERIFIED | test_replay_symmetry.py uses `request.config.getoption("--update-snapshots")` branch |
| 18  | Both replay-symmetry & calibration sweep import same `replay_with_k` helper | ✓ VERIFIED | Both test files contain `from tests.race._replay_helpers import replay_with_k` |
| 19  | HardnessFailureHeatmap renders directional pill in secondary.main | ✓ VERIFIED | grep returns `color="secondary"` + label match in component |
| 20  | Backend `multi_source` → frontend `multi_source_synthesis` mapped at wrapper transform | ✓ VERIFIED | HARDNESS_BACKEND_TO_FRONTEND map at line 32-37 of HardnessFailureHeatmap.tsx |
| 21  | useRaceHeatmap follows let-active-true cleanup pattern | ✓ VERIFIED | grep `let active = true` returns 1 in useRaceHeatmap.ts:23 |

**Score:** 21/21 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `src/a2a_vs_mcp/race/config.py` | HEATMAP_BASELINE frozen singleton | ✓ VERIFIED | 49 lines; 3× HEATMAP_BASELINE references; 2× frozen=True |
| `src/a2a_vs_mcp/race/heatmap.py` | get_heatmap + invalidate_cache + _build_cells | ✓ VERIFIED | 182 lines; 1 get_heatmap, 1 invalidate_cache, 2 tuple(sorted) |
| `src/a2a_vs_mcp/web.py` | /api/race/heatmap + /api/race/runs/{run_id}/trace | ✓ VERIFIED | Lines 43, 858, 869 |
| `src/a2a_vs_mcp/race/harness.py` | run_meta first event + invalidate_cache after race_done | ✓ VERIFIED | Lines 367-374 (run_meta), 493-494 (invalidate_cache) |
| `tests/race/test_run_meta_event.py` | 7 tests pinning run_meta | ✓ VERIFIED | All pass |
| `tests/race/test_heatmap_aggregator.py` | 13 tests pinning aggregator | ✓ VERIFIED | All pass |
| `tests/race/test_replay_route.py` | 5 tests pinning route contract | ✓ VERIFIED | All pass |
| `tests/conftest.py` | --update-snapshots flag | ✓ VERIFIED | pytest_addoption at line 20 |
| `tests/race/_replay_helpers.py` | replay_with_k helper | ✓ VERIFIED | Function at line 16; reuses Detector verbatim |
| `tests/race/test_replay_symmetry.py` | HEAT-03 two-layer fixture sweep | ✓ VERIFIED | 18 parametrize cases pass |
| `tests/test_recovery_calibration.py` | HEAT-04 K-sweep at ROADMAP-named path | ✓ VERIFIED | Exact path; K=3 lock + K-drift sweep all pass |
| `tests/race/fixtures/traces/*_near_k3_boundary_d{3,4,5}.json` | 9 boundary fixtures | ✓ VERIFIED | 9 files present (LANDMINE 9 resolution) |
| `frontend/src/lib/types/race.ts` | HeatmapPayload, HeatmapCellPayload, HeatmapBaseline, HardnessTypeBackend | ✓ VERIFIED | All 4 types exported; uses `"multi_source"` short form |
| `frontend/src/lib/api/client.ts` | fetchRaceHeatmap | ✓ VERIFIED | Line 173; targets `/api/race/heatmap`; type re-exported |
| `frontend/src/features/race/hooks/useRaceHeatmap.ts` | useRaceHeatmap with let-active-true cleanup | ✓ VERIFIED | 50 lines; cleanup pattern present |
| `frontend/src/features/race/hooks/useRaceHeatmap.test.ts` | 4 hook tests | ✓ VERIFIED | All 4 pass |
| `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` | Data-wired wrapper | ✓ VERIFIED | 98 lines; transform map + scaffold + legend + footer |
| `frontend/src/features/race/components/HardnessFailureHeatmap.test.tsx` | 9 component tests | ✓ VERIFIED | All 9 pass |
| `frontend/src/features/race/RacePage.tsx` | <HardnessFailureHeatmap /> mount | ✓ VERIFIED | Line 175; old `<HeatmapScaffold cells={heatmapCells}` removed |

### Key Link Verification

| From | To  | Via | Status | Details |
| ---- | --- | --- | ------ | ------- |
| heatmap.py | config.py | `from .config import HEATMAP_BASELINE` | ✓ WIRED | Confirmed via grep |
| harness.py | heatmap.py | `from .heatmap import invalidate_cache` (late import) | ✓ WIRED | Line 493 |
| web.py | heatmap.py | `from .race.heatmap import get_heatmap` | ✓ WIRED | Line 43 |
| web.py replay route | replay.py | `_validate_run_id + load_run(run_id, RUNS_DIR)` | ✓ WIRED | Existing imports lines 43-45 |
| frontend client | /api/race/heatmap | `fetch('/api/race/heatmap')` | ✓ WIRED | client.ts:174 |
| HardnessFailureHeatmap | HeatmapScaffold | `<HeatmapScaffold cells={cells} />` | ✓ WIRED | Component line 67 |
| HardnessFailureHeatmap | /api/race/heatmap | `useRaceHeatmap → fetchRaceHeatmap → fetch GET` | ✓ WIRED | Hook line 27 |
| RacePage | HardnessFailureHeatmap | `<HardnessFailureHeatmap />` | ✓ WIRED | RacePage.tsx:175 |
| test_replay_symmetry | _replay_helpers | `from tests.race._replay_helpers import replay_with_k` | ✓ WIRED | Confirmed |
| test_recovery_calibration | _replay_helpers | shared K-replay helper | ✓ WIRED | Line 16 |
| _replay_helpers | classifier.py | `from a2a_vs_mcp.race.classifier import Detector` | ✓ WIRED | Confirmed; uses Detector(K) verbatim |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
| -------- | ------------- | ------ | ------------------ | ------ |
| HardnessFailureHeatmap | `data` from `useRaceHeatmap()` | `fetchRaceHeatmap` → GET /api/race/heatmap → `get_heatmap()` → `_build_cells()` over RUNS_DIR | Yes — full data pipeline from disk ndjson scan to React render | ✓ FLOWING |
| /api/race/heatmap response | `cells` + `baseline` | `_build_cells()` filters runs by run_meta match against HEATMAP_BASELINE | Yes — when matching runs exist; empty list (with baseline footer) when none | ✓ FLOWING |
| /api/race/runs/{id}/trace response | `events` | `load_run(run_id, RUNS_DIR)` reads ndjson from disk | Yes — verbatim from disk; no static fallback | ✓ FLOWING |
| Footer baseline display | `data.baseline.{model,seed,task_ids}` | API response sourced from `HEATMAP_BASELINE.to_dict()` | Yes — server-side singleton, never hardcoded in UI | ✓ FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
| -------- | ------- | ------ | ------ |
| HEATMAP_BASELINE produces expected dict | `python -c "from a2a_vs_mcp.race.config import HEATMAP_BASELINE; print(HEATMAP_BASELINE.to_dict())"` | `{'model': 'claude-sonnet-4-6', 'seed': 42, 'task_ids': [...]}` | ✓ PASS |
| GET /api/race/heatmap returns 200 + baseline | TestClient probe | `{'cells': [...], 'baseline': {...}}` 200 OK | ✓ PASS |
| Replay route 400 on malformed run_id | TestClient probe `INVALID@CHAR` | 400 | ✓ PASS |
| Replay route 404 on missing run | TestClient probe `r-doesnotexist` | 404 | ✓ PASS |
| Backend Phase-09 test suites pass | `pytest tests/race/test_run_meta_event.py tests/race/test_heatmap_aggregator.py tests/race/test_replay_route.py tests/race/test_replay_symmetry.py tests/test_recovery_calibration.py -q` | 70 passed in 0.75s | ✓ PASS |
| Frontend Phase-09 test suites pass | `npx vitest run useRaceHeatmap + HardnessFailureHeatmap` | 13/13 pass | ✓ PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| HEAT-01 | 09-01, 09-04 | HardnessFailureHeatmap renders rows × cols, cell encoding, keyboard focus, directional pill in secondary.main | ✓ SATISFIED | Component test "renders directional pill" + grid delegation tests + Phase 8 a11y still green |
| HEAT-02 | 09-01, 09-04 | 5-pill legend always visible; footer shows model · seed · pinned task IDs | ✓ SATISFIED | Component tests "5-pill legend always visible" + "footer renders model · seed · task_ids from API baseline" |
| HEAT-03 | 09-02, 09-03 | Replay route reads disk (no live LLM); state machine replay-identical; two-layer fixture (`--update-snapshots`) | ✓ SATISFIED | Replay route 5/5 + test_replay_symmetry.py 18 cases + conftest --update-snapshots hook |
| HEAT-04 | 09-03 | K=3 sweep over §Assignment fictional traces × 3 v1 tasks; test at `tests/test_recovery_calibration.py` | ✓ SATISFIED | Test exists at exact ROADMAP path; K=3 lock pass + K-drift sweep pass |

No orphaned requirements — all 4 IDs declared in plans match REQUIREMENTS.md (HEAT-01..HEAT-04 all marked Phase 9 / Complete).

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| (none) | - | - | - | No TODO/FIXME/placeholder/empty-impl anti-patterns introduced; no hardcoded empty props at call sites; no LLM bypasses |

### Human Verification Required

(None — every Phase 9 must-have was verifiable programmatically through tests + smoke checks. Visual polish has been pinned by component tests inheriting Phase 8's verified contract; the wrapper is a data-wiring upgrade rather than a new design — D-60 honored.)

### Gaps Summary

No gaps. The phase goal is achieved end-to-end:

1. Heatmap backend (config.py + heatmap.py + harness run_meta + invalidate_cache hook + GET /api/race/heatmap) lands the locked {cells, baseline} payload with D-53 minimal cell shape and D-55/D-57 silent off-baseline exclusion. 20 backend tests pass.
2. Replay route (GET /api/race/runs/{run_id}/trace) ships the typed payload matching the Phase 8 frontend stub, with path-traversal guard and verbatim event passthrough. 5 route tests pass.
3. Replay symmetry + K=3 calibration test infrastructure (shared `replay_with_k` helper + `--update-snapshots` flag + 9 boundary fixtures) makes off-K drift observable for every (task, K) cell. 45 new test cases pass; HEAT-04 ROADMAP-named path satisfied.
4. Frontend wrapper (HardnessFailureHeatmap.tsx + useRaceHeatmap hook + RacePage swap) data-wires the heatmap UI, performs the LANDMINE 1 backend→frontend hardness rename at the transform layer, preserves D-46 (CSS Grid + role=gridcell) and D-47 (empty-state never-unmount), and renders the data-driven footer + always-visible 5-pill legend + directional pill in secondary.main. 13 frontend tests pass.

All 4 ROADMAP success criteria are observable in code and exercised by tests. All 4 phase requirement IDs (HEAT-01..HEAT-04) are satisfied with cross-referenced evidence.

---

_Verified: 2026-04-30T06:27:31Z_
_Verifier: Claude (gsd-verifier)_
