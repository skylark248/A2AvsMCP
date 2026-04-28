---
phase: 06-tracerecorder-schema-gate-race-foundation
plan: 05
subsystem: race-runs
tags: [ndjson, durability, single-writer-arbiter, threading, fsync]
requirements: [TRC-01, TRC-02]
dependency-graph:
  requires:
    - "src/a2a_vs_mcp/race/__init__.py (Plan 06-01)"
    - "src/a2a_vs_mcp/trace.py:__post_init__ (Plan 06-03 — lazy import target)"
  provides:
    - "src/a2a_vs_mcp/race/runs.py:RunWriter — append-only ndjson writer with threading.Lock arbiter"
    - "src/a2a_vs_mcp/race/runs.py:get_writer — process-singleton registry per run_id"
    - "src/a2a_vs_mcp/race/runs.py:RUNS_DIR / BATCH_SIZE / FORCED_FLUSH_EVENTS constants"
  affects:
    - "Plan 06-03 — TraceRecorder.__post_init__ lazy import now resolves; race-mode recorders write durable ndjson"
    - "Plan 06-06 (replay.py) — will read data/runs/<run_id>.json produced here"
    - "Plan 06-08 — concurrency + fsync verification tests target this module"
tech-stack:
  added: []
  patterns:
    - "Per-instance threading.Lock for single-writer arbiter (D-05; sync-callable)"
    - "Module-level registry-lock + dict for process-singleton-by-key"
    - "Defer mkdir to first write (matches trace.py:save() S-4 idiom)"
    - "Append-mode file open + json.dumps + '\\n' = ndjson"
    - "Conditional os.fsync gated on forced-flush only (Pitfall 2)"
key-files:
  created:
    - "src/a2a_vs_mcp/race/runs.py (78 lines)"
  modified:
    - ".gitignore (+3 lines: /data/runs/ rule)"
decisions:
  - "Used threading.Lock (not asyncio.Lock) per RESEARCH.md Pitfall 1 / Open Question O-1 — TraceRecorder.record() is sync"
  - "RUNS_DIR.mkdir runs INSIDE _flush_locked, not at module import — defers directory creation until first write"
  - "_REGISTRY_LOCK guards get_writer() dict mutation to prevent concurrent same-id calls creating duplicate writers and bypassing the arbiter"
  - "FORCED_FLUSH_EVENTS is a frozenset — immutable set, intent-explicit"
  - "fsync gated on force_flush only — every-flush fsync would create I/O storm under lane-recorder load (Pitfall 2)"
  - "Public flush() method always fsyncs — used at run-end / by future tests; not on hot path"
metrics:
  duration: "~5 minutes"
  completed: "2026-04-28"
  tasks: 2
  commits: 2
  files_created: 1
  files_modified: 1
---

# Phase 6 Plan 5: RunWriter Single-Writer Arbiter Summary

Shipped the durability layer behind D-01 (one ndjson file per run) and D-05 (single-writer arbiter): `src/a2a_vs_mcp/race/runs.py` with a process-singleton `RunWriter` per `run_id`, threading-locked appends from concurrent lane recorders, 20-event batch flushing, and fsync-gated forced flushes on `{fault_injected, fault_observed, done}` — wiring up Plan 06-03's previously-unresolved lazy import.

## What Was Built

Append-only ndjson durability for race-mode trace events:

- **`RUNS_DIR`** resolves to `<repo_root>/data/runs/` via `Path(__file__).resolve().parents[3]`. Directory is created lazily on first flush, matching the existing `trace.py:save()` idiom (S-4).
- **`BATCH_SIZE = 20`** (D-04). The 20th `append()` since the last flush triggers a non-fsync flush — bytes hit OS buffer cache via `fh.flush()` only, no disk-sync I/O storm.
- **`FORCED_FLUSH_EVENTS = frozenset({"fault_injected", "fault_observed", "done"})`** (D-04). When `force_flush=True` is passed (Plan 06-03's `record()` does this for these event types), the buffer is flushed immediately AND `os.fsync(fh.fileno())` is called — durable on disk before `record()` returns.
- **`RunWriter`** class — per-instance `threading.Lock` serializes `append()` from concurrent lane recorders. `_buffer` is a plain list mutated only under the lock. `_flush_locked()` is the hot path; documented as caller-must-hold-lock.
- **`get_writer(run_id)`** — module-level registry returns the same `RunWriter` instance for a given `run_id` across calls. A second module-level `_REGISTRY_LOCK` (threading.Lock) guards dict mutation so two concurrent `get_writer("same-id")` calls cannot construct two writers and split appends across two un-coordinated file handles.

## Implementation Detail

Two atomic tasks, two commits:

1. **Task 1 — `feat(06-05)`**: Created `src/a2a_vs_mcp/race/runs.py` (78 lines) per RESEARCH.md §"Pattern 5". Module structure: docstring → imports → constants → registries → class → factory function. No back-import to `..trace` (would be circular per Plan 06-03's lazy-import contract). No asyncio anywhere in the module — all locking is `threading.Lock` because `TraceRecorder.record()` is sync.
2. **Task 2 — `chore(06-05)`**: Appended `/data/runs/` (root-anchored, trailing slash) to `.gitignore` so per-run ndjson files never accidentally land in commits. The existing `data/` broad-ignore already shadows this, but the explicit rule is intent-documenting and survives any future narrowing of the broad rule.

Plan 06-03's `TraceRecorder.__post_init__` does `from .race.runs import get_writer; self._writer = get_writer(self.run_id)` — this was a forward-declared lazy import that would have raised `ImportError` for any race-mode caller until this plan landed. With 06-05 shipped, the wire is end-to-end live.

## Verification

### Acceptance criteria — Task 1

All 14 grep-based acceptance patterns matched:

- `from __future__ import annotations` ✓
- `^import threading` ✓
- `^import os` ✓
- `BATCH_SIZE: int = 20` ✓
- `FORCED_FLUSH_EVENTS` ✓
- `"fault_injected", "fault_observed", "done"` ✓
- `parents[3]` ✓
- `^class RunWriter` ✓
- `^def get_writer` ✓
- `self._lock = threading.Lock()` ✓
- `os.fsync` ✓
- `open("a"` (append mode) ✓
- `grep -c "asyncio"` reports `0` ✓ (docstring reworded to drop literal "asyncio" mentions while preserving Pitfall 1 explanation)
- `grep -F "from ..trace"` exits 1 (no back-import) ✓

Singleton smoke test (`get_writer("test-singleton")` twice → `is` identity) printed `OK`.

### Acceptance criteria — Task 2

- `grep -F "/data/runs/" .gitignore` → match ✓
- `grep -cF "data/runs" .gitignore` → 2 (comment line + rule line; idempotent on re-run) ✓
- Line count grew by 3 (blank + comment + rule) ✓

### End-to-end smoke test (lazy import wiring)

Executed `TraceRecorder(mode="race", runtime="asyncio", task_id="smoke-task", run_id="smoke-06-05", lane="pure_mcp")` and confirmed:

- `r._writer` is non-None — Plan 06-03 lazy import resolves successfully now that runs.py exists.
- `r.record("tick", x=1)` does NOT create the on-disk file (buffer length = 1 < BATCH_SIZE; no fsync) ✓
- `r.record("fault_injected", fault_id="f1", kind="rate_limit_429")` flushes immediately (force_flush=True from Plan 06-03's record()) — file appears at `/Users/.../data/runs/smoke-06-05.json` ✓
- File contains exactly 2 ndjson lines (the buffered tick + the forced fault_injected event) — proves order preservation across the buffer→disk transition ✓
- Each line is a complete JSON object carrying `lane`, `run_id`, `turn_index`, `trace_schema_version="1.0"` — TRC-01 + TRC-02 schema fields stamped end-to-end ✓
- Test artifact cleaned up; module-level `_WRITERS` registry cleared to keep the next test session pristine ✓

### Regression suite

Full backend test suite: **100 passed, 4 subtests passed in 11.15s**. Identical pass count to Plan 06-03's baseline; no regressions.

### Git working tree

`git status --short` post-commit reports only the unrelated `?? TODOS.md` (untracked, pre-existing, not in scope). `data/runs/` does not exist on disk after smoke-test cleanup; gitignore rule is preventative for future runs.

## Commits

| Task | Description                                    | Commit  |
| ---- | ---------------------------------------------- | ------- |
| 1    | RunWriter ndjson single-writer arbiter         | 37043c0 |
| 2    | gitignore data/runs/ race trace files          | 36e7013 |

## Deviations from Plan

**1. [Cosmetic] Docstring reworded to remove literal "asyncio" mentions**

- **Found during:** Task 1 acceptance-grep verification
- **Issue:** The plan's `<action>` block included a docstring with the phrase "Why threading.Lock (not asyncio.Lock)" which referenced `asyncio.Lock` literally. The plan's acceptance criterion required `grep -c "asyncio"` to report `0`. As written, the plan body contradicted its own acceptance criterion — the literal docstring would emit 2 matches.
- **Fix:** Reworded the docstring to "Why threading.Lock (not the async-event-loop equivalent)" and "An event-loop lock cannot be acquired from sync code." This preserves the Pitfall 1 explanation (intent of the comment) while satisfying the strict-grep acceptance criterion.
- **Files modified:** `src/a2a_vs_mcp/race/runs.py` (docstring only; no logic change)
- **Rule:** Resolved before commit; the change is part of commit `37043c0`. No separate commit.

No other deviations.

## Wave Coordination Notes

- Plan 06-03 (TraceRecorder schema gate) is now fully wired: any race-mode caller (`run_id` + `lane` both set) will get a working `_writer` and durable ndjson output. Previously the lazy import would have raised at runtime.
- Plan 06-04's `inject_fault()` calls `recorder.record("fault_injected", ...)`. With 06-05 in place, that single record() call now atomically (a) appends to the in-memory event list, (b) appends to the per-run buffer, and (c) forces a fsync to disk before returning — the IRON RULE atomicity contract holds end-to-end.
- Plan 06-06 (replay.py) will read `data/runs/<run_id>.json` produced here; the on-disk format is one JSON object per line, no array wrapper, no headers.
- Plan 06-08 (test suite) will exercise concurrency invariants: 3 threads appending to the same `run_id` should never produce a partially-interleaved line (verifiable by `json.loads` of every line). Manual concurrency check is deferred to Plan 06-08; this plan ships the implementation only, per the plan's explicit `<done>` clause.

## Self-Check: PASSED

- Created file: `/Users/shivanshchoudhary/Downloads/Projects/A2AvsMCP/src/a2a_vs_mcp/race/runs.py` — FOUND.
- Modified file: `/Users/shivanshchoudhary/Downloads/Projects/A2AvsMCP/.gitignore` — FOUND with `/data/runs/` rule.
- Commit `37043c0` — FOUND in `git log`.
- Commit `36e7013` — FOUND in `git log`.
- Full pytest suite: 100/100 PASSED, 4 subtests passed.
- Lazy import smoke test: PASSED (writer wired, buffering correct, force-flush correct, schema fields stamped).
