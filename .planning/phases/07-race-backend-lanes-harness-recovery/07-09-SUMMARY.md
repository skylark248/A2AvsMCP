---
phase: 07-race-backend-lanes-harness-recovery
plan: 09
subsystem: race-runners
tags: [runners, lanes, transport, detector-wiring, race-02, race-04]
requires: [07-04, 07-05, 07-07, 07-08]
provides:
  - "race/runners/__init__.py — package re-exports of run_pure_mcp, run_pure_a2a, run_hybrid"
  - "race/runners/pure_mcp.py — pure_mcp lane runner (RACE-02)"
  - "race/runners/pure_a2a.py — pure_a2a lane runner (RACE-02)"
  - "race/runners/hybrid.py — hybrid pre-scripted plan executor (RACE-02, D-21)"
  - "End-to-end Detector(K=3) wiring: fault_injected → fault_observed with compute_wasted_tokens (D-32, D-40)"
affects:
  - "Plan 10 (harness): consumes the 3 runner coroutines via Semaphore(8) parallel scheduler"
  - "Plan 11 (chokepoint + integration tests): asserts D-21 grep gate, D-24 send_task method, single chokepoint"
tech-stack:
  added: ["asyncio.to_thread (nested anyio loop isolation)"]
  patterns:
    - "ContextVar-snapshot-and-rearm-in-worker-thread for stdlib ThreadPoolExecutor handlers"
    - "Detector instantiation per fault_injected event (replay-symmetric construction with classifier.py)"
    - "fault-armed-target Exception classification (FastMCP ToolError unwrap)"
key-files:
  created:
    - "src/a2a_vs_mcp/race/runners/__init__.py (12 LOC)"
    - "src/a2a_vs_mcp/race/runners/pure_mcp.py (267 LOC)"
    - "src/a2a_vs_mcp/race/runners/pure_a2a.py (332 LOC)"
    - "src/a2a_vs_mcp/race/runners/hybrid.py (289 LOC)"
  modified: []
decisions:
  - "Runners are module-level async coroutines (not classes) per RESEARCH §4 + project evidence.py idiom"
  - "MCPClient construction + .call() wrapped in asyncio.to_thread because the SDK uses anyio.run internally (nested loop incompatibility)"
  - "FixtureBackedAgentHandler re-arms ACTIVE_FAULTS inside the broker's worker thread (stdlib ThreadPoolExecutor doesn't propagate ContextVars)"
  - "pure_mcp catches Exception (not just InjectedFaultError) when a fault is armed for the target — FastMCP wraps the underlying error as ToolError"
  - "Hybrid v1 deliberately stays pre-scripted (D-21 IRON RULE); the sonnet_client parameter exists for harness compat but is never invoked"
metrics:
  duration_seconds: 588
  duration: "9m 48s"
  tasks_completed: 3
  commits: 4
  files_created: 4
  files_modified: 0
  loc_added: ~900
  completed_date: "2026-04-29"
---

# Phase 7 Plan 09: Race Lane Runners Summary

Three race runners (`pure_mcp`, `pure_a2a`, `hybrid`) shipped with end-to-end Detector(K=3) wiring; all three produce a `RaceResult` of identical shape and run cleanly across the 9 (lane × task) combinations. Faults arm/observe correctly across all transports. RACE-02 + RACE-04 satisfied.

## What Was Built

| File | Lines | Purpose |
|------|------:|---------|
| `src/a2a_vs_mcp/race/runners/__init__.py` | 12 | Package re-exports |
| `src/a2a_vs_mcp/race/runners/pure_mcp.py` | 267 | pure_mcp lane via real `MCPClient(transport='in_process')` |
| `src/a2a_vs_mcp/race/runners/pure_a2a.py` | 332 | pure_a2a lane via real `A2ABroker.send_task` |
| `src/a2a_vs_mcp/race/runners/hybrid.py` | 289 | hybrid pre-scripted plan executor (D-21) |

Each runner exposes `async def run_<lane>(task_spec, run_id, recorder, failure_script, sonnet_client) -> RaceResult` per the locked RESEARCH §4 signature. The `hybrid` runner accepts an extra keyword `hybrid_plan` per Plan 09 must_haves.truths line 3.

## Detector Wiring (D-32 + D-33 + D-40)

Each runner runs the same `_detect_and_record` algorithm against `recorder.events`:

1. Scan for `fault_injected` events → instantiate one `Detector(K=3)` per event.
2. Feed every subsequent event into all live (non-OBSERVED) Detectors via `consume()`.
3. On `consume()` returning True, record `fault_observed` with `compute_wasted_tokens(events, fault_id, lane)` populating `wasted_tokens_before_detection`.
4. At `done` time, call `finalize_at_done(score_pass)` on every Detector (terminal-state recovery tag — D-34).

The algorithm is deliberately identical across all three runners and identical to what the replay path will run in Phase 9 — replay symmetry by construction (D-33).

## Single Fault Chokepoint (D-25 honored)

| Lane | Mock entry path | Fault armament |
|------|-----------------|----------------|
| pure_mcp | `MCPClient.call` → `mcp_servers/race_*` (FastMCP) → `race.mocks.<m>.<fn>` | `set_active_faults` (ContextVar) wrapped by `set_mcp_tool_context` |
| pure_a2a | `broker.send_task` → `FixtureBackedAgentHandler.handle_task` (worker thread) → `race.mocks.<m>.<fn>` | Handler captures `armed_faults` and re-arms inside its worker thread (stdlib ThreadPoolExecutor does not propagate ContextVars) |
| hybrid | `_dispatch_step` → direct `targets[step.tool](**args, recorder=…, run_id=…)` (resolves to `race.mocks.<m>.<fn>`) | `set_active_faults` in the same async context (no thread crossing) |

All three converge on `race.mocks.<m>.<fn>` → `race.failure.inject_fault()` → `_apply_mutation()`. Plan 11 chokepoint test enforces.

## End-to-end Smoke Test Results (with armed `rate_limit_429`)

| Lane | `fault_injected` events | `fault_observed` events | success |
|------|------------------------:|------------------------:|---------|
| pure_mcp | 1 | 1 (evidence=tool_error) | False |
| pure_a2a | 1 | 1 (evidence=tool_error) | False |
| hybrid | 2 | 1 (evidence=tool_error) | False |

(Hybrid logs 2 `fault_injected` because `on_fault: retry_once` re-invokes the chokepoint; the OBSERVED Detector locks after the first observation, exactly as the state machine specifies — D-31.)

The 9 clean-runs (no faults) across all 3 lanes × 3 tasks all complete and return a properly shaped `RaceResult`; success is governed by the v1 scoring stubs and not by runner correctness.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] MCPClient/MCPClient.call use anyio.run() inside an asyncio loop**
- **Found during:** Task 1 smoke test
- **Issue:** `MCPClient.__init__` calls `anyio.run(self._list_tools_in_process)` which raises `RuntimeError: Already running asyncio in this thread` when invoked from inside the runner's `async def`.
- **Fix:** Wrapped both the `MCPClient(...)` constructor and every `client.call(...)` invocation in `asyncio.to_thread(...)` so the nested anyio loop runs on a worker thread.
- **Files modified:** `src/a2a_vs_mcp/race/runners/pure_mcp.py`
- **Commit:** `7cc4be2` (rolled into the runner Task 1 commit `734455c` + the follow-up fix commit)

**2. [Rule 1 - Bug] FastMCP wraps InjectedFaultError as ToolError**
- **Found during:** Detector wiring smoke test (after Task 3)
- **Issue:** When the in-process MCP server tool function raises `InjectedFaultError`, FastMCP wraps it as `mcp.server.fastmcp.exceptions.ToolError` at `tools/base.py:117`. The runner's narrow `except InjectedFaultError` missed it, so no `tool_call status=error` event was recorded — Detector path 1 (tool_error) never fired and `fault_observed` was missing.
- **Fix:** Catch `Exception` while a fault is armed for the target. The IRON RULE in `failure.py` guarantees the `fault_injected` event was recorded BEFORE the raise, so this is safe. Real infra errors still bubble up via `if not is_injected: raise`.
- **Files modified:** `src/a2a_vs_mcp/race/runners/pure_mcp.py`
- **Commit:** `7cc4be2`

**3. [Rule 1 - Bug] A2ABroker uses stdlib ThreadPoolExecutor → ContextVars don't propagate**
- **Found during:** Detector wiring smoke test (after Task 3)
- **Issue:** `A2ABroker._execute_with_timeout` dispatches handlers via `concurrent.futures.ThreadPoolExecutor`, which does NOT propagate ContextVars from the runner's thread. The runner's `set_active_faults(...)` therefore never reached the handler thread; `get_active_fault(target)` returned `None`; faults never fired in the pure_a2a lane.
- **Fix:** `FixtureBackedAgentHandler` now stores `armed_faults` at registration time and re-arms `ACTIVE_FAULTS` inside its `handle_task` worker thread (with proper `reset` in finally for cleanliness).
- **Files modified:** `src/a2a_vs_mcp/race/runners/pure_a2a.py`
- **Commit:** `7cc4be2`

No Rule 4 (architectural) deviations. No checkpoints. No auth gates.

## must_haves.truths Verification

| Truth | Status |
|-------|--------|
| `run_pure_mcp` defined with locked signature | ✓ pure_mcp.py:140 |
| `run_pure_a2a` defined with same signature; uses `broker.send_task` | ✓ pure_a2a.py |
| `run_hybrid` defined with extra `hybrid_plan` kwarg; full on_fault enum dispatch | ✓ hybrid.py |
| Detector instantiated per `fault_injected`; emits `fault_observed` with `compute_wasted_tokens` | ✓ all 3 runners (smoke-tested) |
| `pure_mcp` uses `MCPClient(transport='in_process')` + `set_mcp_tool_context` | ✓ |
| `pure_a2a` uses `A2ABroker(trace=recorder)` + `FixtureBackedAgentHandler` + `broker.send_task` | ✓ |
| Hybrid is pre-scripted plan executor; D-21 IRON RULE (no LLM call) | ✓ grep `messages.create` returns 0 |
| Each runner is a module-level async coroutine, not a class | ✓ |
| Faults raise `InjectedFaultError`; runners catch and feed Detector; never retry at runner layer | ✓ |
| Each runner emits `done` with `score_pass` and finalizes Detectors | ✓ |

## Acceptance Grep Gates

| Gate | Expected | Actual |
|------|---------:|-------:|
| `grep -c "async def run_pure_mcp" pure_mcp.py` | 1 | 1 |
| `grep -c "Detector(" pure_mcp.py` | ≥1 | 1 |
| `grep -c "compute_wasted_tokens" pure_mcp.py` | ≥1 | 4 |
| `grep -cE "set_mcp_tool_context|MCP_TOOL_CONTEXT" pure_mcp.py` | ≥2 | 3 |
| `grep -cE "ACTIVE_FAULTS|set_active_faults" pure_mcp.py` | ≥2 | 4 |
| `grep -c 'transport="in_process"' pure_mcp.py` | ≥1 | 1 |
| `grep -c "InjectedFaultError" pure_mcp.py` | ≥1 | 3 |
| `grep -c "async def run_pure_a2a" pure_a2a.py` | 1 | 1 |
| `grep -cE "broker.send_task|send_task" pure_a2a.py` | ≥1 | 4 |
| **`grep -c "send_message" pure_a2a.py`** | **0** | **0** ✓ |
| `grep -c "FixtureBackedAgentHandler" pure_a2a.py` | ≥1 | 3 |
| `grep -c "async def run_hybrid" hybrid.py` | 1 | 1 |
| **`grep -c "messages.create" hybrid.py`** | **0** | **0** ✓ |
| `grep -cE "retry_once\|delegate\|abort\|continue" hybrid.py` | ≥4 | 19 |
| `grep -c "InjectedFaultError" hybrid.py` | ≥2 | 5 |
| `grep -c "ExecutionContext" hybrid.py` | ≥1 | 4 |
| `grep -c "ACTIVE_FAULTS.reset" hybrid.py` | ≥1 | 1 |

## Test Suite

- 146 pre-existing tests still green (no regressions).
- Plan 11 will add the runner-specific tests (chokepoint, D-21 grep, D-24 grep, Detector wiring tests).

## Threat Model Outcome

| Threat ID | Mitigation Status |
|-----------|-------------------|
| T-07-09-01 (retry InjectedFaultError) | mitigated — runners catch only to feed Detector + record `tool_call status=error`; never retry |
| T-07-09-02 (ContextVar leakage) | mitigated — every runner uses try/finally with `ACTIVE_FAULTS.reset(token)` (and pure_mcp also `MCP_TOOL_CONTEXT.reset`) |
| T-07-09-03 (hybrid sneaks LLM call) | mitigated — grep gate `messages.create` = 0 in hybrid.py |
| T-07-09-04 (A2A bypass mocks chokepoint) | mitigated — `FixtureBackedAgentHandler` only delegates to `race.mocks.<module>` |
| T-07-09-05 (D-24 typo `send_message`) | mitigated — grep gate `send_message` = 0 in pure_a2a.py |

## Commits

- `734455c` feat(07-09): pure_mcp lane runner + runners package init
- `3644805` feat(07-09): pure_a2a lane runner with FixtureBackedAgentHandler
- `f09a135` feat(07-09): hybrid lane runner — pre-scripted plan executor
- `7cc4be2` fix(07-09): wire faults end-to-end through MCP ToolError + A2A worker thread

## Self-Check: PASSED

Verified against disk:

- `src/a2a_vs_mcp/race/runners/__init__.py` exists and re-exports all 3 runners
- `src/a2a_vs_mcp/race/runners/pure_mcp.py` exists (267 lines, `async def run_pure_mcp` present)
- `src/a2a_vs_mcp/race/runners/pure_a2a.py` exists (332 lines, `async def run_pure_a2a` present, `send_message` count = 0)
- `src/a2a_vs_mcp/race/runners/hybrid.py` exists (289 lines, `async def run_hybrid` present, `messages.create` count = 0)
- All 4 commits (`734455c`, `3644805`, `f09a135`, `7cc4be2`) present in `git log`
- 146 pre-existing tests still passing
- All 9 (lane × task) clean-run combos return well-formed RaceResults
- All 3 runners produce fault_injected + fault_observed pairs when a fault is armed
