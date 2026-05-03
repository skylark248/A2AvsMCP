---
phase: 14-race-demo-integration-fix
plan: "01"
subsystem: backend-api
tags: [race-demo, api, fastapi, pydantic, asyncio]
dependency_graph:
  requires: []
  provides:
    - POST /api/race/run endpoint (B1 gap closure)
    - RaceRunRequest Pydantic model with field validators
  affects:
    - src/a2a_vs_mcp/web.py
    - tests/race/test_race_run_endpoint.py
tech_stack:
  added: []
  patterns:
    - asyncio.create_task for non-blocking background race execution
    - Pydantic field_validator for input validation at parse time (HTTP 422 on bad input)
    - uuid4().hex[:16] for run_id generation (all-hex, passes _RUN_ID_RE)
key_files:
  created:
    - tests/race/test_race_run_endpoint.py
  modified:
    - src/a2a_vs_mcp/web.py
decisions:
  - "Use asyncio.create_task (not FastAPI BackgroundTasks) — matches existing harness.py CLI pattern"
  - "ws_emitter wraps async MANAGER.publish via loop.create_task to satisfy sync Callable[[dict], None] signature"
  - "run_id = uuid4().hex[:16] — all hex chars [0-9a-f], deterministically passes _RUN_ID_RE fullmatch"
  - "TASK_CONFIGS imported at module level (not inside route) — validation fires at startup time"
metrics:
  duration: "~15 minutes"
  completed_date: "2026-05-03"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 1
---

# Phase 14 Plan 01: Add POST /api/race/run Endpoint Summary

POST /api/race/run wired to run_race() via asyncio.create_task with Pydantic input validation, closing gap B1 (race demo static display → live execution).

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add RaceRunRequest model and POST /api/race/run endpoint | 057caed | src/a2a_vs_mcp/web.py |
| 2 | Write test_race_run_endpoint.py | 6f823e1 | tests/race/test_race_run_endpoint.py |

## What Was Built

### Task 1: POST /api/race/run Endpoint

Added to `src/a2a_vs_mcp/web.py`:

**New imports:**
- `import uuid` (stdlib)
- `from pydantic import BaseModel, field_validator`
- `from .race.harness import run_race`
- `from .race.tasks import TASK_CONFIGS`
- `from .race.types import HardnessProfile, HardnessType, TaskSpec`
- `from .trace import TraceRecorder`

**New model `RaceRunRequest(BaseModel)`:**
- `task_ids: list[str]` — validated against `TASK_CONFIGS` keys at parse time
- `lanes: list[str]` — validated against `_VALID_LANES` frozenset `{"pure_mcp", "pure_a2a", "hybrid"}`
- `n: int = 1` — validated `>= 1`
- Invalid input returns HTTP 422 before any background task is created

**New endpoint `POST /api/race/run`:**
- Generates `run_id = uuid.uuid4().hex[:16]` (all-hex, passes `_validate_run_id`)
- Builds `list[TaskSpec]` from validated `task_ids`
- Defines `_recorder_factory` and `_sync_ws_emitter` (wraps async MANAGER.publish for sync Callable contract)
- Calls `asyncio.create_task(_do_run())` — race runs in background, response returns immediately
- Returns `{"run_id": run_id}` with HTTP 200

### Task 2: Test Suite

Created `tests/race/test_race_run_endpoint.py` with `TestRaceRunEndpoint` (7 tests):
- `test_happy_path_returns_200_and_run_id` — valid body → 200 + run_id matching `[A-Za-z0-9_-]{1,64}` + passes `_validate_run_id`
- `test_background_task_created` — `asyncio.create_task` called once per POST
- `test_invalid_lane_returns_422` — `lanes=["bad_lane"]` → 422
- `test_n_zero_returns_422` — `n=0` → 422
- `test_unknown_task_id_returns_422` — `task_ids=["nonexistent_task_xyz"]` → 422
- `test_missing_task_ids_returns_422` — missing `task_ids` field → 422
- `test_all_three_lanes_accepted` — all three valid lanes → 200

## Test Results

- New tests: 7/7 passed
- Race test suite: 213/213 passed (206 pre-existing + 7 new)
- Pre-existing failures in `test_demo_modes.py`, `test_web_ui.py`, `test_api_async.py`, `test_tool_discovery_scenario.py` are worktree data path issues (`FileNotFoundError: seeds/orders.json`) — not caused by this plan's changes

## Deviations from Plan

None — plan executed exactly as written. All imports, model definitions, endpoint implementation, and test cases match the plan specification verbatim.

## Known Stubs

None — `run_id` is real (uuid4-based), task specs are built from TASK_CONFIGS, and the background run is wired to the real `run_race()` harness.

## Threat Surface Scan

All threats in the plan's STRIDE threat register are mitigated as specified:

| Threat ID | Mitigation | Implemented |
|-----------|-----------|-------------|
| T-14-01-01 | `field_validator` rejects unknown task_ids → 422 | Yes |
| T-14-01-02 | `field_validator` rejects unknown lanes → 422 | Yes |
| T-14-01-03 | `field_validator` rejects `n < 1` → 422 | Yes |
| T-14-01-04 | `uuid4().hex[:16]` — no user input reaches run_id | Yes |

No new threat surface introduced beyond what the plan's threat model covers.

## Self-Check: PASSED

- `src/a2a_vs_mcp/web.py` — modified and contains `RaceRunRequest`, `api_race_run`
- `tests/race/test_race_run_endpoint.py` — created and contains `TestRaceRunEndpoint`
- Commit `057caed` — feat(14-01): add RaceRunRequest model and POST /api/race/run endpoint
- Commit `6f823e1` — test(14-01): add test_race_run_endpoint.py for POST /api/race/run
