"""Single-writer arbiter for data/runs/<run_id>.json (D-01, D-04, D-05).

Three lane recorders (pure_mcp / pure_a2a / hybrid) all append to the same
run file. RunWriter holds a per-run-id threading.Lock during writes so the
bytes never interleave across threads. Phase 7 harness will spawn lanes
concurrently — this module guarantees serialization at the file boundary.

Why threading.Lock (not the async-event-loop equivalent): TraceRecorder.record()
is sync (trace.py:24) and v1 callers in platform.py are sync. An event-loop lock
cannot be acquired from sync code. threading.Lock works under both sync and async
callers. RESEARCH.md Open Question O-1 surfaces this; planner accepts.
"""
from __future__ import annotations

import json
import os
import threading
from pathlib import Path
from typing import Any

# Repo root: parents[0]=race/, [1]=a2a_vs_mcp/, [2]=src/, [3]=<root>
RUNS_DIR: Path = Path(__file__).resolve().parents[3] / "data" / "runs"

BATCH_SIZE: int = 20  # D-04: batch flush every 20 events
FORCED_FLUSH_EVENTS: frozenset[str] = frozenset({"fault_injected", "fault_observed", "done"})

# Module-level registries (process-singleton per run_id).
_WRITERS: dict[str, "RunWriter"] = {}
_REGISTRY_LOCK = threading.Lock()


class RunWriter:
    """Append-only ndjson writer with single-writer arbiter (D-05).

    Per-instance threading.Lock serializes append() calls from concurrent
    lane recorders. Buffer flushes on BATCH_SIZE (20) or force_flush=True
    (D-04). os.fsync runs only on forced flushes (Pitfall 2 — every-flush
    fsync would create an I/O storm).
    """

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.path: Path = RUNS_DIR / f"{run_id}.json"
        self._buffer: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def append(self, event: dict[str, Any], *, force_flush: bool = False) -> None:
        """Append one event. Flushes on BATCH_SIZE or force_flush."""
        with self._lock:
            self._buffer.append(event)
            if force_flush or len(self._buffer) >= BATCH_SIZE:
                self._flush_locked(fsync=force_flush)

    def flush(self) -> None:
        """Public flush — used at run end / by tests. Holds lock; runs fsync."""
        with self._lock:
            self._flush_locked(fsync=True)

    def _flush_locked(self, *, fsync: bool) -> None:
        """Internal flush. CALLER MUST HOLD self._lock."""
        if not self._buffer:
            return
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            for event in self._buffer:
                fh.write(json.dumps(event) + "\n")
            fh.flush()
            if fsync:  # only on forced flushes per Pitfall 2
                os.fsync(fh.fileno())
        self._buffer.clear()


def get_writer(run_id: str) -> RunWriter:
    """Return the process-singleton RunWriter for run_id (D-05)."""
    with _REGISTRY_LOCK:
        if run_id not in _WRITERS:
            _WRITERS[run_id] = RunWriter(run_id)
        return _WRITERS[run_id]
