---
phase: "03-new-scenarios"
plan: "02"
subsystem: "backend-agents"
tags: [triage, parallel-dispatch, a2a, scen-02, tdd]
dependency_graph:
  requires: ["03-01"]
  provides: ["SCEN-02 parallel dispatch path in TriageAgent"]
  affects: ["src/a2a_vs_mcp/agents/triage.py", "tests/test_demo_modes.py"]
tech_stack:
  added: []
  patterns: ["tag-based dispatch branch", "parallel fan-out via ThreadPoolExecutor", "TDD RED/GREEN"]
key_files:
  created: []
  modified:
    - src/a2a_vs_mcp/agents/triage.py
    - tests/test_demo_modes.py
decisions:
  - "Tag check inserted as first line of resolve_with_broker() before intent classification — deterministic, crash-safe (D-06)"
  - "_resolve_parallel() placed between _request_specialist() and _merge() — consistent with class method ordering"
  - "Used existing _merge(ticket, results, issue_type) with issue_type='parallel_investigation' rather than a simple join fallback"
metrics:
  duration: "~8 minutes"
  completed: "2026-04-23T16:09:05Z"
  tasks_completed: 2
  files_modified: 2
  commits: 2
---

# Phase 3 Plan 02: SCEN-02 Parallel Dispatch — Summary

**One-liner:** Tag-based parallel branch in TriageAgent fans out 3 specialist messages via broker.send_tasks_parallel(), producing a shared parallel_batch_id across all task_submit trace events.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 (RED) | SCEN-02 failing tests | ca807ce | tests/test_demo_modes.py |
| 1 (GREEN) | TriageAgent parallel dispatch branch + _resolve_parallel() | 0633e6b | src/a2a_vs_mcp/agents/triage.py |

## What Was Built

**resolve_with_broker() parallel branch:**
- First two lines of method body: `if "parallel_investigation" in ticket.tags: return self._resolve_parallel(ticket, broker)`
- All existing sequential intent-classification logic is byte-for-byte unchanged when tag is absent

**_resolve_parallel() method:**
- Records `agent_reasoning` trace event with `issue_type="parallel_investigation"`
- Builds 3 `A2AMessage` objects (one each for `customer_data`, `documentation`, `policy_billing`) using `broker.find_by_capability().agent_id`
- Calls `broker.send_tasks_parallel(messages)` in a single dispatch
- Calls `self._merge(ticket, results, "parallel_investigation")` to produce final_answer
- Records `triage_merge` trace event with contributors list and final_answer
- Returns `AgentResult(agent_id=self.agent_id, summary=final_answer, details=merged_details)`

**SCEN-02 pytest assertions (3 tests):**
- `test_scen02_parallel_emits_shared_batch_id`: all task_submit events share one non-None parallel_batch_id
- `test_scen02_parallel_produces_no_failures`: zero task_failed events in trace
- `test_scen02_parallel_triggers_three_specialists`: >= 3 task_submit events in trace

## TDD Gate Compliance

| Gate | Commit | Status |
|------|--------|--------|
| RED (test) | ca807ce | 2/3 failing as expected — no task_submit events before implementation |
| GREEN (feat) | 0633e6b | All 3 SCEN-02 tests passing, 46/46 total passing |

## Verification

```
46 passed in 14.57s
```

All pre-existing tests unaffected. SCEN-02 parallel path fully exercised under mock runtime.

## Deviations from Plan

None — plan executed exactly as written. `_merge()` existed with the expected `(ticket, results, issue_type)` signature, no fallback needed.

## Known Stubs

None.

## Threat Flags

None. All new code paths operate within existing trust boundaries (static seed tags, in-process mock agents).

## Self-Check

- [x] `src/a2a_vs_mcp/agents/triage.py` modified with parallel branch and `_resolve_parallel()`
- [x] `tests/test_demo_modes.py` modified with 3 SCEN-02 tests
- [x] RED commit ca807ce exists
- [x] GREEN commit 0633e6b exists
- [x] 46/46 tests passing
