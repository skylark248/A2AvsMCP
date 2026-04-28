---
phase: 07-race-backend-lanes-harness-recovery
plan: 01
subsystem: race
tags: [phase6-delta, dependency, exception-class, harness-prereq]
requires: []
provides: [InjectedFaultError, anthropic-dep, pyyaml-dep]
affects: [src/a2a_vs_mcp/race/failure.py, src/a2a_vs_mcp/race/__init__.py, tests/race/test_inject_fault.py, pyproject.toml]
tech_stack_added:
  - "anthropic>=0.40 (Sonnet runner + Haiku judge per D-42)"
  - "pyyaml>=6.0 (explicit; task_config.yaml is v2.0 first-class file format)"
patterns:
  - "Custom exception subclassing RuntimeError for retry-classifier disambiguation"
  - "IS-A hierarchy preserves backward compatibility with broader exception catchers"
key_files_created: []
key_files_modified:
  - src/a2a_vs_mcp/race/failure.py
  - src/a2a_vs_mcp/race/__init__.py
  - tests/race/test_inject_fault.py
  - pyproject.toml
decisions:
  - "InjectedFaultError IS-A RuntimeError (preserves compatibility)"
  - "Re-export InjectedFaultError from race/__init__.py so downstream plans can `from a2a_vs_mcp.race import InjectedFaultError`"
  - "Pin anthropic>=0.40 (not exact) so minor-version drift doesn't break re-resolves"
metrics:
  duration_seconds: 137
  tasks_completed: 3
  files_modified: 4
  files_created: 0
  commits: 3
  tests_added: 0
  tests_modified: 2
  tests_passing: 37
completed_date: "2026-04-28"
---

# Phase 07 Plan 01: Wave-0 Substrate (InjectedFaultError + anthropic/pyyaml deps) Summary

Phase 6 → Phase 7 substrate: rename the bare `RuntimeError` raised by `_apply_mutation()` to a dedicated `InjectedFaultError(RuntimeError)` so the Plan-10 harness retry classifier can `except InjectedFaultError` instead of catching real `anthropic.RateLimitError` and accidentally retrying the test; also pin `anthropic>=0.40` and `pyyaml>=6.0` as explicit direct deps.

## Objective

Land the Phase 6 delta required by Phase 7's harness retry classifier (per RESEARCH §2 — `InjectedFaultError(RuntimeError)`) and add two missing direct dependencies (`anthropic>=0.40` and explicit `pyyaml`) that the rest of Phase 7 imports from. The harness MUST distinguish `anthropic.RateLimitError` (real 429 — RETRY) from injected `FaultKind.RATE_LIMIT_429` (the test — NEVER RETRY); Phase 6 raised bare `RuntimeError` for both, so the classifier in Plan 10 cannot tell them apart. Changing the raise type unblocks every downstream plan to use `except InjectedFaultError` cleanly.

## Tasks Completed

| # | Name | Commit | Files |
|---|------|--------|-------|
| 1 | Add InjectedFaultError class and update _apply_mutation | `9270526` | src/a2a_vs_mcp/race/failure.py, src/a2a_vs_mcp/race/__init__.py |
| 2 | Update Phase 6 atomicity test to assert InjectedFaultError | `139f75b` | tests/race/test_inject_fault.py |
| 3 | Add anthropic and pyyaml direct deps to pyproject.toml | `d59d060` | pyproject.toml |

## What Shipped

### `src/a2a_vs_mcp/race/failure.py`
- New `InjectedFaultError(RuntimeError)` class inserted directly above `FaultKind`, with a docstring explaining the Phase 7 D-38 retry-classifier contract and the IS-A RuntimeError compatibility guarantee.
- `_apply_mutation` updated: both `raise RuntimeError(...)` sites (RATE_LIMIT_429 and PARTIAL_COMMIT_5XX) now raise `InjectedFaultError(...)` with identical messages.
- IRON RULE atomicity body untouched: `recorder.record("fault_injected", ...)` still runs in `inject_fault()` BEFORE `_apply_mutation()` is invoked.

### `src/a2a_vs_mcp/race/__init__.py`
- Added `from .failure import InjectedFaultError` and an explicit `__all__ = ["InjectedFaultError"]` so downstream plans can write `from a2a_vs_mcp.race import InjectedFaultError`.

### `tests/race/test_inject_fault.py`
- Import line extended with `InjectedFaultError`.
- `test_record_runs_before_raise`: `assertRaises(RuntimeError)` → `assertRaises(InjectedFaultError)` (locks the tighter contract).
- `test_all_5_fault_kinds`: `except RuntimeError` → `except InjectedFaultError`.
- All 7 tests in the file pass; full `tests/race/` suite (37 tests) remains green.

### `pyproject.toml`
- Added `anthropic>=0.40` (sorted alphabetically — first entry in `[project] dependencies`).
- Added `pyyaml>=6.0` (explicit; alphabetically before `uvicorn`).
- Editable reinstall (`pip install -e .`) resolved cleanly: `anthropic 0.97.0` + `pyyaml 6.0.3`.

## Verification

All 5 `must_haves.truths` from PLAN.md frontmatter pass:

| # | Truth | Result |
|---|-------|--------|
| 1 | `race/failure.py` exports `InjectedFaultError` (subclass of `RuntimeError`) | PASS — `issubclass(InjectedFaultError, RuntimeError)` is True |
| 2 | `_apply_mutation` raises `InjectedFaultError` for RATE_LIMIT_429 + PARTIAL_COMMIT_5XX | PASS — `grep -c "raise InjectedFaultError"` outputs `2`; no bare `raise RuntimeError` remains |
| 3 | Tests assert `InjectedFaultError`; Phase 6 atomicity test still green | PASS — 7 occurrences across the file; `pytest tests/race/test_inject_fault.py` 7/7 green |
| 4 | `pyproject.toml [project] dependencies` includes anthropic>=0.40 and pyyaml>=6.0 | PASS — both entries present |
| 5 | `python -c "import anthropic, yaml"` exits 0 after editable reinstall | PASS — anthropic 0.97.0, yaml 6.0.3 |

Additional checks:
- IRON RULE atomicity preserved: `grep -B 2 -A 10 "Step 1 (record)"` shows `recorder.record(...)` still precedes `_apply_mutation()` call (lines 86–95 unchanged).
- Phase 6 full race suite: `pytest tests/race/ -x -q` → 37/37 passed in 0.53s.
- Anthropic version gate: `assert tuple(int(x) for x in anthropic.__version__.split('.')[:2]) >= (0, 40)` passes (0.97.0 ≥ 0.40).

## Deviations from Plan

None — plan executed exactly as written. No bugs found, no missing functionality, no blocking issues, no architectural changes.

## Authentication Gates

None — this plan only adds the `anthropic` package as a dependency. `ANTHROPIC_API_KEY` is documented in `user_setup` for downstream plans (Plan 06 Haiku judge, Plan 09 race runners) but is NOT required for any Plan-01 task; nothing in this plan calls the API.

## Threat Surface Scan

No new attack surface introduced. The `_apply_mutation` raise-class change is internal-only; the new dependencies (`anthropic`, `pyyaml`) are well-known PyPI packages with established trust. T-07-01-01 (tampering: harness must not retry injected faults) is **mitigated** by the new exception class as planned.

## Next

Wave 0 complete. Wave 1 (Plans 02 + 03) can begin in parallel:
- **Plan 02** (race types and protocol enums) imports `InjectedFaultError` for type hints in the harness retry classifier signature.
- **Plan 03** (mock APIs scaffold) consumes the updated `_apply_mutation` raise contract.

The `anthropic` dep unblocks Plans 06 (Haiku judge), 09 (Sonnet race runners), and 10 (harness with retry classifier).

## Self-Check: PASSED

- [x] `src/a2a_vs_mcp/race/failure.py` modified — confirmed `class InjectedFaultError(RuntimeError):` at line 26
- [x] `src/a2a_vs_mcp/race/__init__.py` modified — confirmed re-export
- [x] `tests/race/test_inject_fault.py` modified — confirmed 3 occurrences of `InjectedFaultError`
- [x] `pyproject.toml` modified — confirmed both deps present
- [x] Commit `9270526` exists in `git log` (Task 1)
- [x] Commit `139f75b` exists in `git log` (Task 2)
- [x] Commit `d59d060` exists in `git log` (Task 3)
- [x] All 37 Phase 6 race tests still pass
