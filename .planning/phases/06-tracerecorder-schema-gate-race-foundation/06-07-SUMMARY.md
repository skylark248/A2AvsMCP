---
phase: 06-tracerecorder-schema-gate-race-foundation
plan: 07
subsystem: race
tags: [websocket, fastapi, connection-manager, coalesce, heartbeat, rate-limit]
requires:
  - "src/a2a_vs_mcp/race/replay.py:_validate_run_id"
  - "src/a2a_vs_mcp/race/replay.py:load_run"
  - "src/a2a_vs_mcp/race/runs.py:RUNS_DIR"
  - "src/a2a_vs_mcp/web.py:app (FastAPI singleton)"
provides:
  - "src/a2a_vs_mcp/race/ws.py:ConnectionManager"
  - "src/a2a_vs_mcp/race/ws.py:Connection"
  - "src/a2a_vs_mcp/race/ws.py:MANAGER (module singleton)"
  - "src/a2a_vs_mcp/race/ws.py:HEARTBEAT_S=15, COALESCE_THRESHOLD=50, PER_IP_CAP=5, QUEUE_MAX=10000"
  - "src/a2a_vs_mcp/race/ws.py:NEVER_COALESCE (frozenset of exactly 7 wire types)"
  - "/api/race/ws route on the existing FastAPI app"
affects:
  - "src/a2a_vs_mcp/web.py (imports + new ws route only; existing routes untouched)"
tech-stack:
  added:
    - "asyncio.Queue (bounded, maxsize=10000) for in-process pubsub fan-out (D-09)"
    - "asyncio.Lock for ConnectionManager registry (async callers — D-06)"
  patterns:
    - "Module-singleton MANAGER (RESEARCH.md O-3) — Phase 7 harness will call MANAGER.publish"
    - "Inline 5/IP cap inside connect() (RESEARCH.md 'Don't Hand-Roll' — no middleware)"
    - "Query-string handshake (run_id, last_seen_turn_index) — RESEARCH.md O-4"
    - "Defense-in-depth path-traversal: _validate_run_id in route AND inside load_run"
key-files:
  created:
    - "src/a2a_vs_mcp/race/ws.py"
    - "tests/test_race_ws.py"
  modified:
    - "src/a2a_vs_mcp/web.py"
decisions:
  - "Connection is @dataclass(eq=False) for identity-based hashing in set[Connection] — Rule 1 fix; plan-spec @dataclass alone made it unhashable"
  - "5/IP cap enforced inline in MANAGER.connect (D-06); 6th rejected with code 4290 before accept"
  - "Path-traversal guard runs FIRST in route — invalid run_id closes with 4400 before accept"
  - "Reconnect replay reads ndjson from disk via load_run when last_seen_turn_index >= 0 (D-07); FileNotFoundError caught for live-only runs"
  - "Heartbeat: asyncio.wait_for(conn.queue.get(), timeout=15) — emits {event_type: heartbeat, ts_ms} on idle"
  - "Bounded queue (QUEUE_MAX=10000); publish drops on QueueFull (DoS mitigation per RESEARCH.md Security Domain)"
metrics:
  duration_minutes: 4
  completed: 2026-04-28
  tasks_completed: 2
  tests_added: 9
  tests_passing_total: 109
---

# Phase 6 Plan 07: Race WebSocket Lifecycle Summary

Full `/api/race/ws` lifecycle (D-06): ConnectionManager with 5/IP cap, per-connection bounded asyncio.Queue, server-side coalesce of `tick` events when buffer >50, 15s heartbeat, disk-backed reconnect replay via `load_run`, all wired onto the existing FastAPI app via `@app.websocket`.

## Tasks Completed

| Task | Name                                         | Commit  | Files                                           |
| ---- | -------------------------------------------- | ------- | ----------------------------------------------- |
| 1    | Create race/ws.py + ConnectionManager + tests | 7b73415 | src/a2a_vs_mcp/race/ws.py, tests/test_race_ws.py |
| 2    | Register /api/race/ws route in web.py         | 7f61300 | src/a2a_vs_mcp/web.py                            |

## Must-Have Truths Satisfied

- `/api/race/ws` registered on existing FastAPI app via `@app.websocket` — verified by `python -c "from a2a_vs_mcp.web import app; assert '/api/race/ws' in [r.path for r in app.routes]"` returning OK.
- Handshake reads `run_id` (required) and `last_seen_turn_index: int = Query(-1)` from query string.
- ConnectionManager enforces `PER_IP_CAP=5` inline before `ws.accept()`; 6th connection from same IP closed with code 4290.
- Per-connection `asyncio.Queue(maxsize=10000)`; static `coalesce()` keeps latest tick per `(lane, task_id)` when buffer >50, never coalescing the 7 NEVER_COALESCE wire types.
- `HEARTBEAT_S=15` — emitted via `asyncio.wait_for(conn.queue.get(), timeout=15)` then `{"event_type": "heartbeat", "ts_ms": ...}` on TimeoutError.
- Reconnect replay: when `last_seen_turn_index >= 0`, calls `load_run(run_id, RUNS_DIR)` and streams events with `turn_index > last_seen_turn_index` BEFORE entering live loop.
- `_validate_run_id` runs FIRST, before `MANAGER.connect` and any file resolution; invalid run_id closes with 4400.
- `MANAGER.publish` is callable; tests exercise it directly. Phase 7 harness will wire the producer.

## Constants Audit (verified by tests/test_race_ws.py::test_constants_exact)

```
HEARTBEAT_S        == 15
COALESCE_THRESHOLD == 50
PER_IP_CAP         == 5
NEVER_COALESCE     == {tool_call, agent_msg, fault_injected, fault_observed, done, error, race_done}  # exactly 7
"tick" not in NEVER_COALESCE  # tick is the ONLY coalesce-eligible event
```

## Tests Added (tests/test_race_ws.py — 9 tests)

1. `test_constants_exact` — values + 7-member NEVER_COALESCE
2. `test_module_singleton_manager` — MANAGER is ConnectionManager instance
3. `test_coalesce_below_threshold_returns_unchanged` — 50 ticks pass through
4. `test_coalesce_above_threshold_keeps_latest_tick_per_lane_task` — 60 ticks → 2 latest survive
5. `test_coalesce_preserves_never_coalesce_events_verbatim` — all 7 NEVER_COALESCE types kept
6. `test_connect_enforces_per_ip_cap` — 5 succeed, 6th gets `close(code=4290)` and no accept
7. `test_disconnect_decrements_ip_and_removes_from_run` — including idempotent double-disconnect
8. `test_publish_enqueues_to_all_connections_for_run` — fan-out filtered by run_id
9. `test_publish_no_subscribers_is_noop` — empty registry doesn't raise

All 9 pass. Plan 06-08 ships the `TestClient.websocket_connect` lifecycle integration tests.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Bug] Connection dataclass made non-hashable, breaking `set[Connection]`**
- **Found during:** Task 1 first test run.
- **Issue:** Plan spec used `@dataclass` (default `eq=True`) on `Connection`. Default `eq=True` sets `__hash__=None`, so storing instances in `self._by_run: dict[str, set[Connection]]` raised `TypeError: unhashable type: 'Connection'` on `_by_run[run_id].add(conn)`.
- **Fix:** Changed to `@dataclass(eq=False)` — instances become identity-hashable (default `__hash__` from `object`). Identity semantics are correct here: each connection is a unique object, comparing by field equality would be meaningless.
- **Files modified:** `src/a2a_vs_mcp/race/ws.py`
- **Commit:** 7b73415 (folded into Task 1 — caught before commit by tests)

No other deviations. The websocket lifecycle, constants, NEVER_COALESCE membership, and route registration match the plan verbatim.

## Threat Model Status

All `mitigate` dispositions in plan 06-07's threat register are satisfied:

| Threat ID    | Mitigation in this plan                                                                          |
| ------------ | ------------------------------------------------------------------------------------------------ |
| T-06-07-01   | `_validate_run_id` runs FIRST in route handler; close 4400 before accept. Defense-in-depth: `load_run` re-validates. |
| T-06-07-02   | 5/IP cap inline in `MANAGER.connect`; 6th gets `close(code=4290)` before accept (test 6).        |
| T-06-07-03   | `coalesce()` static + bounded `asyncio.Queue(maxsize=10000)`; `publish` drops on `QueueFull`.   |
| T-06-07-04   | 15s heartbeat via `asyncio.wait_for`; dead connections cleaned up via `WebSocketDisconnect` + `finally MANAGER.disconnect`. |

`accept` dispositions (T-06-07-05/06/07) are out-of-scope per plan; documented for Phase 7+ promotion.

## Verification

- `pytest -q` → **109 passed, 4 subtests passed in 10.89s** (full sweep, no regressions)
- `pytest tests/test_web_ui.py tests/test_api_async.py -x` → **37 passed in 4.52s** (existing route tests intact)
- `pytest tests/test_race_ws.py -q` → **9 passed in 0.20s**
- Route registration verified at runtime: `'/api/race/ws' in [r.path for r in app.routes]`
- All 16 grep-based acceptance criteria in plan 06-07 exit 0.

## Self-Check: PASSED

Files created and verified present:
- `src/a2a_vs_mcp/race/ws.py` — FOUND (4.5 KB, 113 lines)
- `tests/test_race_ws.py` — FOUND
- `.planning/phases/06-tracerecorder-schema-gate-race-foundation/06-07-SUMMARY.md` — FOUND (this file)

Commits verified in `git log --oneline`:
- `7b73415` feat(06-07): add ConnectionManager + coalesce + module singleton in race/ws.py — FOUND
- `7f61300` feat(06-07): register /api/race/ws on existing FastAPI app (D-06 lifecycle) — FOUND
