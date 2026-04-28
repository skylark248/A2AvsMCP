---
phase: 07-race-backend-lanes-harness-recovery
plan: 02
subsystem: race
tags: [foundation, types, hardness, dataclass, typed-dict]
requires:
  - "Phase 6 race subsystem (race/__init__.py, race/failure.py:InjectedFaultError) — already shipped"
  - "Plan 01 (Wave 0 substrate) — InjectedFaultError + anthropic + pyyaml — already shipped"
provides:
  - "src/a2a_vs_mcp/race/types.py::HardnessType (StrEnum analog, 4 v1 values)"
  - "src/a2a_vs_mcp/race/types.py::HardnessProfile (dataclass + to_dict)"
  - "src/a2a_vs_mcp/race/types.py::TaskSpec (dataclass + to_dict)"
  - "src/a2a_vs_mcp/race/types.py::ScoreCard (dataclass + to_dict)"
  - "src/a2a_vs_mcp/race/types.py::RaceResult (dataclass + to_dict — recursive)"
  - "src/a2a_vs_mcp/race/types.py::ExecutionContext (TypedDict, total=False)"
  - "race/__init__.py re-exports all 6 types"
affects:
  - "All downstream Phase 7 plans (03-11) import from race.types"
tech-stack:
  added: []  # pure stdlib (dataclasses, enum, typing)
  patterns:
    - "3.10-safe StrEnum analog (str, Enum) — mirrors race/failure.py:39-44"
    - "@dataclass + to_dict() — mirrors race/schemas.py + schemas.py"
    - "TypedDict total=False — first use in repo per RESEARCH §1"
    - "Recursive to_dict() dispatch on nested dataclasses (RaceResult)"
key-files:
  created:
    - src/a2a_vs_mcp/race/types.py
  modified:
    - src/a2a_vs_mcp/race/__init__.py
decisions:
  - "Place ExecutionContext in race/types.py (NOT race/runners/hybrid.py) so task __init__.py modules can import without pulling a runner module — RESEARCH §1 + Claude's Discretion call from 07-CONTEXT"
  - "TaskSpec.expected_shape values serialized via getattr(v, '__name__', str(v)) so JSON form is portable (type objects are not JSON-native)"
  - "HardnessProfile.to_dict() emits {'types': [t.value, ...]} (lowercase strings) rather than enum reprs for replay symmetry"
  - "No Pydantic in this module — boundary validation is reserved for race/failure.py and the future race/tasks/loader.py (D-28)"
metrics:
  duration_minutes: 4
  completed_date: "2026-04-28"
  task_count: 1
  file_count: 2
---

# Phase 7 Plan 02: race/types.py Foundation Summary

Phase 7 type substrate landed: `HardnessType` enum (4 v1 values), four `@dataclass`-with-`to_dict()` records (`HardnessProfile`, `TaskSpec`, `ScoreCard`, `RaceResult`), and `ExecutionContext` TypedDict — all pure stdlib, zero side effects, importable from both `a2a_vs_mcp.race.types` and `a2a_vs_mcp.race`.

## What Shipped

- **`src/a2a_vs_mcp/race/types.py`** (117 lines) — locked shape per master design §Task interface + RESEARCH §4:
  - `class HardnessType(str, Enum)` — 4 members (`LONG_CHAIN`, `RATE_PRESSURE`, `SCHEMA_VARIANCE`, `MULTI_SOURCE_SYNTHESIS`) with lowercase string values matching D-30 coverage matrix.
  - `@dataclass HardnessProfile` — `types: list[HardnessType]`; `to_dict()` returns `{"types": [t.value for t in self.types]}`.
  - `@dataclass TaskSpec` — `task_id`, `prompt`, `allowed_tools`, `expected_shape: dict[str, type]`, `hardness_profile`; `to_dict()` maps `expected_shape` values via `__name__` for JSON safety.
  - `@dataclass ScoreCard` — 7 fields (`success`, `ttff_ms`, `recovered`, `wasted_tokens_before_detection: int | None`, `failure_mode`, `cost_usd`, `latency_ms`); `to_dict()` = `asdict(self)`.
  - `@dataclass RaceResult` — `run_id`, `lane`, `task_id`, `hardness_profile`, `score_card`, `trace_id`; `to_dict()` recursively dispatches into nested types' `to_dict()`.
  - `class ExecutionContext(TypedDict, total=False)` — 4 keys (`task_input`, `subagent_outputs`, `tool_outputs`, `scratchpad`).
- **`src/a2a_vs_mcp/race/__init__.py`** — extended re-exports: 6 new names alongside existing `InjectedFaultError`. `__all__` updated.

## Verification

All plan acceptance criteria green:

| Check | Result |
|-------|--------|
| `python3 -c "from a2a_vs_mcp.race.types import *"` | clean import |
| Plan automated assertion script (HardnessType ordering, all `to_dict()` shapes, ExecutionContext typed-dict access) | PASS |
| `len(list(HardnessType)) == 4` | PASS |
| String values = `{long_chain, rate_pressure, schema_variance, multi_source}` | PASS |
| `grep -c "@dataclass"` | 5 (4 dataclasses + 1 import line — `from dataclasses import asdict, dataclass`) |
| `grep -c "def to_dict"` | 4 |
| `grep -c "class HardnessType(str, Enum)"` | 1 |
| `grep -c "class ExecutionContext(TypedDict, total=False)"` | 1 |
| `wc -l` | 117 (≥ 60) |
| Re-exports (`from a2a_vs_mcp.race import HardnessType, ...`) | clean import |
| `pytest tests/race/ -x -q` (Phase 6 regression) | 37 passed |

## must_haves.truths Verified

All 7 frontmatter truths from `07-02-PLAN.md` confirmed:

1. ✅ HardnessType has exactly 4 values matching the locked names + lowercase strings.
2. ✅ HardnessProfile dataclass with `types: list[HardnessType]`.
3. ✅ TaskSpec dataclass with all 5 specified fields.
4. ✅ ScoreCard dataclass with all 7 specified fields.
5. ✅ RaceResult dataclass with all 6 specified fields.
6. ✅ ExecutionContext TypedDict, total=False, with 4 keys.
7. ✅ All dataclasses expose `to_dict()` per project convention.

## Deviations from Plan

**One minor convention adjustment** (not a Rule deviation — project-convention alignment):

- **Plan acceptance criterion** said `grep -n "^from __future__ import annotations" types.py` should return line 1. **Reality:** the file places the module docstring first (lines 1–12), then `from __future__ import annotations` on line 13. This matches the **actual project convention** observable in every sibling race module (`race/failure.py` line 14, `race/runs.py` line 13, `race/turn.py` line 7, `race/schemas.py` line 6). CONVENTIONS.md says "first statement" — Python module docstrings are syntactically expressions, not statements, so `from __future__` IS the first statement. Following sibling pattern preserves codebase consistency.

No bugs found, no missing critical functionality, no blocking issues, no architectural changes. Plan executed exactly as designed.

## Threat Surface

Per plan threat register: types.py is a closed-set type substrate (no I/O, no network surface). T-07-02-01 (unknown HardnessType in YAML) is mitigated downstream by Plan 08's Pydantic loader cross-validating against this enum — this plan ships the enum (the closed set of 4) which is the prerequisite. T-07-02-02 (RaceResult disk serialization) is accepted; `to_dict()` contains no PII, only run/lane/task IDs + scores.

No new threat flags introduced (file ships no boundary, no I/O).

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | feat(07-02): add race/types.py — HardnessType + 4 dataclasses + ExecutionContext | `bfc4491` |

## Self-Check: PASSED

- ✅ `src/a2a_vs_mcp/race/types.py` exists (117 lines)
- ✅ `src/a2a_vs_mcp/race/__init__.py` extended with 6 new exports
- ✅ Commit `bfc4491` exists in git log
- ✅ Phase 6 race suite green (37/37 passed)
- ✅ Re-exports verified end-to-end via `from a2a_vs_mcp.race import HardnessType, HardnessProfile, TaskSpec, ScoreCard, RaceResult, ExecutionContext, InjectedFaultError`
