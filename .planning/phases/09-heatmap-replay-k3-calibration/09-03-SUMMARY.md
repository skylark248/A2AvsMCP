---
phase: 09-heatmap-replay-k3-calibration
plan: 03
subsystem: tests
tags:
  - tests
  - calibration
  - python
  - replay-symmetry
  - K=3
dependency_graph:
  requires:
    - "src/a2a_vs_mcp/race/classifier.py (Detector(K), finalize_at_done, finalize_at_race_done_no_done — Phase 7 D-31..D-33)"
    - "tests/race/fixtures/traces/*.json (9 §The Assignment fixtures shipped Phase 7-11)"
  provides:
    - "tests/race/_replay_helpers.py::replay_with_k(events, K, score_pass) — single source of truth for K-replay tag computation"
    - "tests/conftest.py::pytest_addoption(--update-snapshots) — hand-rolled snapshot regen flag"
    - "9 near-K3-boundary fixtures (3 per task at evidence distances 3/4/5) — calibration drift corpus"
    - "HEAT-03 replay symmetry test (18 fixtures) + HEAT-04 K=3 lock test (18 fixtures) + HEAT-04 K-drift test (9 task×K cells)"
  affects:
    - "tests/race/test_classifier_detector.py::test_all_nine_fixtures_present (scoped to non-boundary fixtures)"
    - "tests/__init__.py (NEW package marker — enables 'from tests.race._replay_helpers' imports)"
tech_stack:
  added: []
  patterns:
    - "Hand-rolled snapshot mechanism — fixture JSON files ARE the snapshots"
    - "pytest.parametrize over Path.glob — fixture-driven test sweeps"
    - "Computed-not-authored expected_terminal_tag — boundary fixtures pre-resolved via replay_with_k(K=3)"
key_files:
  created:
    - "tests/__init__.py (package marker)"
    - "tests/race/_replay_helpers.py (replay_with_k helper)"
    - "tests/race/test_replay_symmetry.py (HEAT-03 two-layer fixture test)"
    - "tests/test_recovery_calibration.py (HEAT-04 K=3 lock + K-drift sweep)"
    - "tests/race/fixtures/traces/{summarize_repo,negotiate_meeting,book_travel}_near_k3_boundary_d{3,4,5}.json (9 boundary fixtures)"
  modified:
    - "tests/conftest.py (pytest_addoption hook for --update-snapshots)"
    - "tests/race/test_classifier_detector.py (scope test_all_nine_fixtures_present to non-boundary fixtures)"
decisions:
  - "Honored D-33 symmetry-by-construction — helper reuses production Detector class verbatim, no parallel implementation"
  - "Honored T-09-11 mitigation — boundary fixture expected_terminal_tag computed via replay_with_k(K=3), never hand-authored"
  - "Authored 9 near-K3-boundary fixtures (LANDMINE 9 resolution) instead of declaring K-drift impossible"
metrics:
  duration_min: 35
  completed_date: "2026-04-30"
  tasks_completed: 2
  files_created: 13
  files_modified: 2
  tests_added: 45
  pytest_total: 326
---

# Phase 9 Plan 03: Replay Symmetry + K=3 Calibration Sweep Summary

Hand-rolled two-layer fixture test (HEAT-03) and K∈{2,3,4,5} multi-task calibration sweep (HEAT-04) using a shared `replay_with_k` helper that reuses the production `Detector` class verbatim, with 9 near-K3-boundary fixtures authored to make off-K drift observable for every (task, K) cell.

## What Was Built

- **Shared replay helper** at `tests/race/_replay_helpers.py` — `replay_with_k(events, K, score_pass) -> tag` instantiates a fresh `Detector(K)` from the first `fault_injected` event, feeds every subsequent event through `consume()`, and finalizes via `finalize_at_done(score_pass)` on `done` arrival OR `finalize_at_race_done_no_done()` on `race_done` arrival without a prior `done`.
- **`--update-snapshots` flag** registered in `tests/conftest.py` via `pytest_addoption`. Default mode asserts; `--update-snapshots` rewrites `expected_terminal_tag` in each fixture file with the computed actual.
- **HEAT-03 test** (`tests/race/test_replay_symmetry.py`) — `pytest.mark.parametrize` over every `*.json` fixture; 18 cases (9 §The Assignment + 9 boundary). Each asserts `replay_with_k(K=3) == fixture.expected_terminal_tag`. With `--update-snapshots`, rewrites instead of asserting.
- **HEAT-04 test** (`tests/test_recovery_calibration.py`, ROADMAP-named path) — two halves:
  - `test_k3_produces_expected_tag` — 18 parametrize cases over all fixtures; K=3 lock.
  - `test_off_k_drift_observed_per_task` — 9 parametrize cells (3 tasks × K∈{2,4,5}); for each, asserts at least one fixture in the task's corpus produces `replay_with_k(K=k) != replay_with_k(K=3)`.
- **9 near-K3-boundary fixtures** at `tests/race/fixtures/traces/{task}_near_k3_boundary_d{3,4,5}.json`. Each fixture has `fault_injected` at `turn_index=0` and an `agent_msg` acknowledging-fault event at `turn_index=d` (d∈{3,4,5}), so:
  - d=3: K=2 misses the OBSERVED window (cur_turn-fault_inject_turn = 3 > K=2), K=3 catches → drifts at K=2.
  - d=4: K=3 misses, K=4 catches → drifts at K=4.
  - d=5: K=4 misses, K=5 catches → drifts at K=5.
- **`tests/__init__.py`** package marker — Rule 3 deviation, see below.

## Tests Added

| Test | Cases | Purpose |
|------|-------|---------|
| `test_replay_symmetry` (HEAT-03) | 18 | Default: assert tag == expected. `--update-snapshots`: rewrite fixture JSON. |
| `test_k3_produces_expected_tag` (HEAT-04 lock) | 18 | K=3 produces expected_terminal_tag for every fixture. |
| `test_off_k_drift_observed_per_task` (HEAT-04 calibration claim) | 9 | At least one fixture per (task, K∈{2,4,5}) drifts vs K=3. |

**Total new test cases:** 45. Full pytest suite: **326 passed** (281 prior + 45 new).

## Decisions Made

- **D-33 symmetry-by-construction preserved** — `replay_with_k` reuses `Detector(K)` verbatim from `src/a2a_vs_mcp/race/classifier.py`. There is no parallel implementation. Replay tags are mathematically identical to runtime tags by mathematical construction, not by snapshot match.
- **Hand-rolled snapshot mechanism** — Fixture JSON files double as snapshots. No `pytest-snapshot` or `syrupy` dependency added (over-engineering for two test files; fixture files are human-readable and review-friendly).
- **Single source of truth for K-replay** — Both HEAT-03 (replay symmetry) and HEAT-04 (calibration sweep) import the same `replay_with_k` helper. Per the plan's must-have invariant, drift between the two cannot occur.
- **Boundary fixtures authored, not declared impossible** — RESEARCH LANDMINE 9 anticipated that the 9 §The Assignment fixtures might have evidence-distances ≤ 1 (so all K∈{2,3,4,5} produce identical tags). Verified: that was indeed the case for all 9. Per the plan's Action Step 3, authored 9 boundary fixtures to make every K∈{2,4,5}-drift cell pass.
- **T-09-11 mitigation honored** — Boundary fixtures' `expected_terminal_tag` was COMPUTED via `replay_with_k(K=3)` then written back, never hand-authored. The fixture documents what `Detector(K=3)` actually produces, eliminating the drift-encoding-assumption threat.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] `replay_with_k` initial helper version mishandled `race_done`-without-`done` finalization**
- **Found during:** Task 2 verification — `negotiate_meeting_indeterminate` fixture failed.
- **Issue:** Initial helper called `finalize_at_done(score_pass)` at end-of-events even when the trace ended with `race_done` and had no `done` event. With `score_pass=null` (as in the indeterminate fixture), this returned `kept_going_to_failure` instead of `indeterminate`.
- **Root cause:** `Detector.finalize_at_done(False)` returns `kept_going_to_failure` for AWAITING_OBSERVATION state; `Detector.finalize_at_race_done_no_done()` returns `indeterminate` directly. The helper must branch on `race_done` arrival.
- **Fix:** Helper now branches on `event_type`: `done` → `finalize_at_done(score_pass)`; `race_done` → `finalize_at_race_done_no_done()`.
- **Files modified:** `tests/race/_replay_helpers.py`
- **Commit:** a048cc5

**2. [Rule 3 - Blocking] Missing `tests/__init__.py` package marker**
- **Found during:** Task 2 — collection error: `ModuleNotFoundError: No module named 'tests'` when both new test files attempted `from tests.race._replay_helpers import replay_with_k`.
- **Root cause:** `tests/race/__init__.py` exists but `tests/__init__.py` did not. Without it, `tests.race._replay_helpers` is not an importable absolute path.
- **Fix:** Created `tests/__init__.py` with a docstring explaining the rationale.
- **Files modified:** `tests/__init__.py` (NEW)
- **Commit:** a048cc5

**3. [Rule 3 - Blocking] `test_all_nine_fixtures_present` assertion broken by new boundary fixtures**
- **Found during:** Full pytest regression run after Task 2.
- **Issue:** `tests/race/test_classifier_detector.py::test_all_nine_fixtures_present` asserts `len(glob('*.json')) == 9` to guard the §The Assignment corpus count. Adding 9 boundary fixtures took it to 18.
- **Fix:** Scoped the test's glob filter to exclude `*near_k3_boundary*.json`. Added inline comment naming Phase 9 Plan 03 as the source of the new fixture family. The §The Assignment count assertion is preserved (still 9).
- **Files modified:** `tests/race/test_classifier_detector.py`
- **Commit:** a048cc5

### LANDMINE 9 Resolution — Boundary Fixture Authorship

The plan's Action Step 3 anticipated this: existing 9 §The Assignment fixtures all have evidence at distance ≤ 1 from `fault_inject_turn`, so K∈{2,3,4,5} all reach the same OBSERVED state and produce identical tags. Without near-K3-boundary fixtures, `test_off_k_drift_observed_per_task` cannot pass.

**Authored 9 boundary fixtures** (`{task}_near_k3_boundary_d{3,4,5}.json`):

| Task | d=3 | d=4 | d=5 |
|------|-----|-----|-----|
| summarize_repo | recovered (K=3 catches; K=2 misses) | kept_going_without_noticing (K=3 misses; K=4 catches) | kept_going_without_noticing (K=4 misses; K=5 catches) |
| negotiate_meeting | recovered | kept_going_without_noticing | kept_going_without_noticing |
| book_travel | recovered | kept_going_without_noticing | kept_going_without_noticing |

Each fixture's `expected_terminal_tag` was COMPUTED via `replay_with_k(K=3, score_pass=True)` before write — never hand-authored — per T-09-11 mitigation.

## --update-snapshots Smoke Verification

```bash
pytest tests/race/test_replay_symmetry.py --update-snapshots
# 18 passed in 0.07s

git diff tests/race/fixtures/traces/ | grep '^[+-]\s*"expected_terminal_tag"'
# (empty)
```

**Zero `expected_terminal_tag` value changes after rewrite.** D-33 symmetry-by-construction confirmed end-to-end: replay produces the recorded tag for every fixture. (Note: `--update-snapshots` rewrites the JSON formatting from compact-1-line-per-event to `indent=2` pretty-print, which is a cosmetic diff; the formatting changes were reverted before commit since they are not semantically meaningful.)

## Files Created

| File | Purpose |
|------|---------|
| `tests/__init__.py` | Package marker enabling `tests.race._replay_helpers` imports |
| `tests/race/_replay_helpers.py` | Shared `replay_with_k(events, K, score_pass) -> tag` helper |
| `tests/race/test_replay_symmetry.py` | HEAT-03 two-layer fixture test (assert + --update-snapshots) |
| `tests/test_recovery_calibration.py` | HEAT-04 K=3 lock + K∈{2,4,5} drift sweep |
| `tests/race/fixtures/traces/summarize_repo_near_k3_boundary_d{3,4,5}.json` | summarize_repo K-drift evidence |
| `tests/race/fixtures/traces/negotiate_meeting_near_k3_boundary_d{3,4,5}.json` | negotiate_meeting K-drift evidence |
| `tests/race/fixtures/traces/book_travel_near_k3_boundary_d{3,4,5}.json` | book_travel K-drift evidence |

## Files Modified

| File | Change |
|------|--------|
| `tests/conftest.py` | Add `pytest_addoption(--update-snapshots)` hook |
| `tests/race/test_classifier_detector.py` | Scope `test_all_nine_fixtures_present` to non-boundary fixtures |

## Commits

| Hash | Type | Message |
|------|------|---------|
| `98b861e` | feat | feat(09-03): add --update-snapshots flag + replay_with_k helper |
| `a048cc5` | test | test(09-03): add HEAT-03 replay symmetry + HEAT-04 K-calibration sweep |

## Verification

- [x] `tests/conftest.py` registers `--update-snapshots` flag without breaking existing tests (`pytest --update-snapshots --collect-only -q` exits 0; 281 → 326 collected)
- [x] `tests/race/_replay_helpers.py` exists with `replay_with_k(events, K, score_pass) -> tag`
- [x] `tests/race/test_replay_symmetry.py` exists; 18 fixture-parametrized cases pass; `--update-snapshots` branch works (`request.config.getoption` confirmed)
- [x] `tests/test_recovery_calibration.py` exists at the EXACT ROADMAP-named path; K=3 lock (18 cases) + K-drift sweep (9 cells) both pass
- [x] HEAT-03 success criterion 3 demonstrated: replaying recorded ndjson via `Detector(K=3)` yields identical tags
- [x] HEAT-04 success criterion 4 demonstrated: K=3 produces expected for all 18 fixtures; K∈{2,4,5} drift observable per task
- [x] No external snapshot library added (still no `pytest-snapshot` / `syrupy` in `pyproject.toml`)
- [x] Full project regression `pytest` exits 0 — **326/326 passed**, no test deletions

## Self-Check: PASSED

- File `tests/__init__.py` — FOUND
- File `tests/race/_replay_helpers.py` — FOUND
- File `tests/race/test_replay_symmetry.py` — FOUND
- File `tests/test_recovery_calibration.py` — FOUND
- 9 boundary fixtures under `tests/race/fixtures/traces/` — FOUND
- Commit `98b861e` (feat: helper + flag) — FOUND in `git log`
- Commit `a048cc5` (test: symmetry + calibration) — FOUND in `git log`
- 326/326 pytest passed — VERIFIED
