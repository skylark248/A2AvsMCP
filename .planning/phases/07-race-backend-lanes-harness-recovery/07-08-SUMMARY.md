---
phase: 07-race-backend-lanes-harness-recovery
plan: 08
subsystem: race-tasks
tags: [tasks, registries, pydantic, scorers, yaml, haiku-judge]

# Dependency graph
requires:
  - phase: 07
    provides: race/mocks/{github,calendar,travel}.py (Plan 03) + race/failure.FaultKind enum (Plan 06-04) + race/judges/haiku.py (Plan 06)
provides:
  - 3 v1 task packages (summarize_repo, negotiate_meeting, book_travel) with task_config.yaml + TARGETS + BINDS + score()
  - race/tasks/loader.py — TaskConfig pydantic model + load_task_config() cross-validator (D-28)
  - race/tasks/__init__.py — V1_TASK_IDS + TASK_CONFIGS module-load validation hook
affects: [07-09-pure-mcp-runner, 07-10-hybrid-runner, 07-11-chokepoint-tests-and-hardness-coverage]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Pydantic BaseModel + ConfigDict(extra='forbid') for strict YAML schema; extra='allow' only on FailureScriptYAMLEntry for per-kind extras"
    - "yaml.safe_load (NEVER yaml.load) — single security gate at loader entry"
    - "Cross-validation via __import__(pkg, fromlist=['TARGETS','BINDS']) so loader can resolve identifier names against task module's callable registries"
    - "Module-load dict-comp TASK_CONFIGS = {tid: load_task_config(tid) for tid in V1_TASK_IDS} fires startup validation at first import"

key-files:
  created:
    - src/a2a_vs_mcp/race/tasks/__init__.py
    - src/a2a_vs_mcp/race/tasks/loader.py
    - src/a2a_vs_mcp/race/tasks/summarize_repo/__init__.py
    - src/a2a_vs_mcp/race/tasks/summarize_repo/task_config.yaml
    - src/a2a_vs_mcp/race/tasks/negotiate_meeting/__init__.py
    - src/a2a_vs_mcp/race/tasks/negotiate_meeting/task_config.yaml
    - src/a2a_vs_mcp/race/tasks/book_travel/__init__.py
    - src/a2a_vs_mcp/race/tasks/book_travel/task_config.yaml
  modified: []

key-decisions:
  - "Loader raises plain ValueError (not pydantic ValidationError.from_exception_data) for unknown target/bind identifiers — RESEARCH §7's from_exception_data pattern is awkward and a bare ValueError still crashes module-load loudly per D-28"
  - "TaskConfig + HybridPlan + HybridStep all extra='forbid' (typo in field name = startup error); only FailureScriptYAMLEntry uses extra='allow' so per-kind YAML extras (drift, target_calendar_id, ...) survive without per-kind subclasses"
  - "negotiate_meeting docstring deliberately avoids the substrings 'HaikuJudge' and 'race.judges' so the D-43 grep gate (Plan 11) reports 0 matches — phrased as 'does NOT import any LLM judge'"
  - "book_travel _legs_connect treats <2-flight bookings as trivially connected (single-leg trips legal); multi-leg checks origin/destination chain"

patterns-established:
  - "Per-task callable registry shape: TARGETS: dict[str, Callable] (failure_script.target → mock fn), BINDS: dict[str, Callable[[ExecutionContext], Any]] (hybrid_plan.bind → ctx resolver)"
  - "Per-task scorer signature: score(result, trace, judge) -> ScoreCard; judge=None branch always degrades to failure_mode='judge_failed'"
  - "D-30 hardness coverage matrix encoded directly in YAML (no Python const list); coverage check runs at Plan 05 module-load + Plan 11 unit test"

requirements-completed: [RACE-01, RACE-05]

# Metrics
duration: ~5min
completed: 2026-04-29
---

# Phase 7 Plan 08: Task Configs + Per-Task TARGETS/BINDS Registries Summary

**Three v1 task packages (summarize_repo, negotiate_meeting, book_travel) — each ships a `task_config.yaml` (failure_script + hybrid_plan + hardness_profile) and an `__init__.py` (TARGETS callable registry + BINDS resolver registry + per-task `score()`), validated at first import by a Pydantic loader that cross-checks every target/bind identifier against the task's registries — typo = ValidationError at `pytest --collect-only` time.**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-29T02:42:52+05:30
- **Completed:** 2026-04-29T02:47:02+05:30
- **Tasks:** 5

## Commits

| Task | Description | Hash |
|------|-------------|------|
| 1 | TaskConfig pydantic loader with cross-validation | `1b62f26` |
| 2 | summarize_repo task — TARGETS, BINDS, Haiku 3/3 scorer | `da71d8a` |
| 3 | negotiate_meeting task — structural-only scorer (D-43) | `d01c36d` |
| 4 | book_travel task — composite (structural + Haiku) scorer | `dbe09b4` |
| 5 | finalize race/tasks/__init__.py — module-load validation hook (D-28) | `c583463` |

## What Shipped

### `race/tasks/loader.py`

Pydantic-based TaskConfig schema:

- `OnFault = Literal["retry_once", "delegate", "abort", "continue"]` (D-29 locked enum)
- `HybridStep` — `kind: Literal["tool","delegate"]`, optional tool/agent/goal/bind/on_fault, `extra="forbid"`
- `HybridPlan` — `steps: list[HybridStep]`, `extra="forbid"`
- `FailureScriptYAMLEntry` — `kind: FaultKind`, `target: str`, defaults `after_calls=0/duration_calls=1`, `extra="allow"` for per-kind extras (drift, etc.)
- `TaskConfig` — `task_id`, `hardness_profile: list[HardnessType]`, `failure_script`, `hybrid_plan`, `extra="forbid"` + `_profile_nonempty` field validator

`load_task_config(task_id)` returns `(TaskConfig, TARGETS, BINDS)` after:
1. `yaml.safe_load(resources.files(pkg).joinpath('task_config.yaml').read_text())` (T-07-08-01 mitigation)
2. `TaskConfig.model_validate(raw)` (rejects unknown FaultKind/HardnessType/OnFault)
3. `__import__(pkg, fromlist=['TARGETS','BINDS'])` then cross-checks every `entry.target in targets` and every `step.bind in binds` (T-07-08-03 mitigation)

### `race/tasks/__init__.py`

```
V1_TASK_IDS = ["summarize_repo", "negotiate_meeting", "book_travel"]
TASK_CONFIGS = {tid: load_task_config(tid) for tid in V1_TASK_IDS}
```

The dict-comp at module top-level is the validation hook — first import of `a2a_vs_mcp.race.tasks` runs the loader for all three tasks. Any typo in any YAML or registry mismatch raises before pytest collection finishes.

### Per-Task Packages

| Task | Hardness Profile (D-30) | Failure Script | Scorer Type (D-42/43) |
|------|-------------------------|----------------|-----------------------|
| summarize_repo | long_chain, rate_pressure, schema_variance | rate_limit_429 (get_repo_metadata), schema_drift (list_files) | Haiku 3/3 (R1 purpose, R2 ≥3 modules, R3 entry point) |
| negotiate_meeting | schema_variance, multi_source | schema_drift (get_free_busy), eventual_consistency_read (propose_time) | Structural-only (proposed time fits all 3 owners' free windows) — NO LLM (D-43) |
| book_travel | long_chain, rate_pressure, multi_source | rate_limit_429 (search_hotels), partial_commit_5xx (book_itinerary) | Composite — structural (cost ≤ budget AND legs connect) AND Haiku R1 (purpose match) |

D-30 coverage matrix verified at Task 5 module-load:

| HardnessType | Tasks |
|--------------|-------|
| LONG_CHAIN | summarize_repo, book_travel (2/3) |
| RATE_PRESSURE | summarize_repo, book_travel (2/3) |
| SCHEMA_VARIANCE | summarize_repo, negotiate_meeting (2/3) |
| MULTI_SOURCE_SYNTHESIS | negotiate_meeting, book_travel (2/3) |

Each of the 4 v1 hardness types appears in ≥2 of 3 tasks (Phase 7 Success Criterion #5).

## Verification

- [x] All 5 tasks committed individually (1b62f26, da71d8a, d01c36d, dbe09b4, c583463)
- [x] Three task_config.yaml files exist and Pydantic-validate at first import
- [x] All 6 TARGETS keys (3 + 2 + 3) and all 3 BINDS keys cross-validate against YAML targets/binds
- [x] negotiate_meeting/__init__.py contains 0 references to HaikuJudge or race.judges (D-43 grep gate)
- [x] summarize_repo + book_travel scorers wire HaikuJudge with verbatim RESEARCH §3 rubrics
- [x] D-30 hardness coverage matrix holds (each type in ≥2 tasks)
- [x] `pytest tests/race/ -x -q` → 37 passed
- [x] `pytest -q` → 146 passed (37 race + 109 v1) — no regressions

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] negotiate_meeting docstring tripped D-43 grep gate**

- **Found during:** Task 3 verification
- **Issue:** Original docstring contained the literal string `NO HaikuJudge import (D-43)`. Acceptance criterion `grep -c "HaikuJudge\|race.judges" ... outputs 0` matched the docstring substring and reported `1`, even though the file has no actual import.
- **Fix:** Rephrased docstring as `D-43: this task does NOT import any LLM judge.` — semantically identical but doesn't contain the forbidden substrings.
- **Files modified:** `src/a2a_vs_mcp/race/tasks/negotiate_meeting/__init__.py`
- **Commit:** Folded into `d01c36d` (rephrased before initial commit landed)

No other deviations. Plan executed exactly as written.

## Threat Surface

All `<threat_model>` entries from PLAN frontmatter materialized as designed:

| Threat ID | Mitigation Verified |
|-----------|---------------------|
| T-07-08-01 (malicious YAML executes Python) | `yaml.safe_load` only — `grep -c "yaml.load(" loader.py` = 0 |
| T-07-08-02 (unknown FaultKind/OnFault enum) | Pydantic Literal types + `extra="forbid"` — schema test rejects bad enums (Task 1 verify block) |
| T-07-08-03 (unknown failure_script.target) | `load_task_config` raises ValueError on cross-validation miss; module-load test exercises all 3 tasks |
| T-07-08-04 (trip purpose disclosed to Haiku) | Accepted — synthetic mock data only |
| T-07-08-05 (negotiate_meeting bypasses D-43) | grep gate reports 0 matches; Plan 11 will lock this in via test |

No new threat flags introduced (no novel network endpoints, auth paths, or schema mutations beyond what the plan declared).

## Self-Check: PASSED

- File `src/a2a_vs_mcp/race/tasks/loader.py` — FOUND
- File `src/a2a_vs_mcp/race/tasks/__init__.py` — FOUND
- File `src/a2a_vs_mcp/race/tasks/summarize_repo/task_config.yaml` — FOUND
- File `src/a2a_vs_mcp/race/tasks/summarize_repo/__init__.py` — FOUND
- File `src/a2a_vs_mcp/race/tasks/negotiate_meeting/task_config.yaml` — FOUND
- File `src/a2a_vs_mcp/race/tasks/negotiate_meeting/__init__.py` — FOUND
- File `src/a2a_vs_mcp/race/tasks/book_travel/task_config.yaml` — FOUND
- File `src/a2a_vs_mcp/race/tasks/book_travel/__init__.py` — FOUND
- Commit `1b62f26` — FOUND
- Commit `da71d8a` — FOUND
- Commit `d01c36d` — FOUND
- Commit `dbe09b4` — FOUND
- Commit `c583463` — FOUND
