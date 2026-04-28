# Phase 6: TraceRecorder Schema Gate & Race Foundation - Pattern Map

**Mapped:** 2026-04-28
**Files analyzed:** 14 (8 new, 1 modified, 5 new tests)
**Analogs found:** 13 / 14 (one new file — `race/runs.py` RunWriter — has no direct analog; closest is `TraceRecorder.save()` + `export_external()`)

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/a2a_vs_mcp/race/__init__.py` | package-init | n/a | `src/a2a_vs_mcp/__init__.py` (empty) | exact |
| `src/a2a_vs_mcp/race/schemas.py` | model (dataclass) | transform | `src/a2a_vs_mcp/schemas.py` (FailureConfig, A2AMessage) | exact |
| `src/a2a_vs_mcp/race/failure.py` | utility (record-then-mutate) | event-driven | `src/a2a_vs_mcp/schemas.py:30-55` (FailureConfig) + `src/a2a_vs_mcp/trace.py:24-39` (record) | role-match |
| `src/a2a_vs_mcp/race/turn.py` | config (constant table) | transform | `src/a2a_vs_mcp/trace.py:19-22` (`_PHASE_MAP`) + `src/a2a_vs_mcp/config.py:21-49` (`PROFILES`) | exact |
| `src/a2a_vs_mcp/race/replay.py` | service (file I/O loader) | file-I/O | `src/a2a_vs_mcp/trace.py:50-65` (`export_external` ndjson write) — read variant | role-match |
| `src/a2a_vs_mcp/race/runs.py` | service (single-writer arbiter) | file-I/O batch-flush | `src/a2a_vs_mcp/trace.py:44-65` (`save` + `export_external`) | partial — no concurrency analog exists |
| `src/a2a_vs_mcp/race/ws.py` | service (ConnectionManager + pubsub) | streaming/pub-sub | (none — first websocket in codebase) | NO ANALOG (use FastAPI canonical pattern from RESEARCH.md) |
| `src/a2a_vs_mcp/trace.py` (MODIFIED) | model | event-driven | `src/a2a_vs_mcp/trace.py` itself (extend in place) | self |
| `src/a2a_vs_mcp/web.py` (MODIFIED — add `@app.websocket`) | route registration | request-response (ws upgrade) | `src/a2a_vs_mcp/web.py:680-697` (`/api/health`) + `src/a2a_vs_mcp/web.py:706-711` (`/api/run`) | role-match (no ws analog yet) |
| `tests/race/__init__.py` | package-init | n/a | (must be created — no analog; `tests/` itself has no `__init__.py`) | exact |
| `tests/race/test_trace_schema.py` | test (sync) | request-response | `tests/test_demo_modes.py:1-65` | exact |
| `tests/race/test_inject_fault.py` | test (sync) | event-driven | `tests/test_demo_modes.py:38-50` | exact |
| `tests/race/test_replay_stub.py` | test (sync) | file-I/O | `tests/test_demo_modes.py:1-30` | exact |
| `tests/race/test_ws_schema.py` | test (sync — TestClient.websocket_connect) | streaming | `tests/test_web_ui.py:15-23` (TestClient pattern) + `tests/test_api_async.py:1-33` (async pattern) | role-match |
| `tests/race/test_ws_lifecycle.py` | test (async) | streaming | `tests/test_api_async.py:1-33` (`asyncio_mode="auto"` bare `async def test_*`) | role-match |

## Pattern Assignments

---

### `src/a2a_vs_mcp/race/__init__.py` (package-init)

**Analog:** `src/a2a_vs_mcp/__init__.py` (empty package marker; project convention)

**Pattern:** Empty file (or thin re-export of public types). The project's existing top-level `__init__.py` is empty — submodules import directly from `a2a_vs_mcp.<module>`. RESEARCH.md §Recommended Project Structure suggests re-exporting `FaultKind`, `inject_fault`, `TURN_DEFINING_EVENTS` from `race.__init__` for ergonomic `from a2a_vs_mcp.race import inject_fault`.

**Recommended content:**
```python
"""Race subsystem: trace schema v1.0, ndjson durability, websocket fan-out, fault helpers."""
from .failure import FaultKind, FailureScriptEntry, inject_fault
from .turn import TURN_DEFINING_EVENTS, is_turn_defining
__all__ = ["FaultKind", "FailureScriptEntry", "inject_fault", "TURN_DEFINING_EVENTS", "is_turn_defining"]
```

---

### `src/a2a_vs_mcp/race/schemas.py` (model — dataclass + to_dict idiom)

**Analog:** `src/a2a_vs_mcp/schemas.py` lines 1-92

**Imports pattern** (lines 1-6):
```python
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid
```

**Core dataclass + helper-method pattern** (lines 30-55, `FailureConfig`):
```python
@dataclass
class FailureConfig:
    db_down: bool = False
    docs_timeout: bool = False
    unavailable_agents: list[str] = field(default_factory=list)
    # ... boolean fields with `field(default_factory=list)` for list defaults

    def enabled(self) -> bool:
        return (
            self.db_down
            or self.docs_timeout
            or ...
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

**A2A message-style dataclass** (lines 66-80, `A2AMessage` — closest to a `WsEvent` payload):
```python
@dataclass
class A2AMessage:
    message_type: str
    sender_agent: str
    target_agent: str
    capability: str
    payload: dict[str, Any]
    task_id: str
    context: dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: new_id("msg"))
    timestamp: str = field(default_factory=utc_now)
    attempt: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

**Apply to race/schemas.py:** Define 8 `WsEvent`-shaped dataclasses (`TickEvent`, `ToolCallEvent`, `AgentMsgEvent`, `FaultInjectedEvent`, `FaultObservedEvent`, `DoneEvent`, `ErrorEvent`, `RaceDoneEvent`). Each carries `lane: str`, `turn_index: int`, `event_type: str` (literal), and event-specific fields. Add `to_dict()` returning `asdict(self)`. Match `A2AMessage`'s style precisely — the project's existing idiom.

---

### `src/a2a_vs_mcp/race/failure.py` (utility — IRON RULE record-then-mutate)

**Analog (schema half):** `src/a2a_vs_mcp/schemas.py:30-55` (`FailureConfig` dataclass + `to_dict()`)
**Analog (record-emit half):** `src/a2a_vs_mcp/trace.py:24-39` (`TraceRecorder.record()`)

**Imports + module docstring pattern** (mirror `src/a2a_vs_mcp/schemas.py:1-7` + RESEARCH.md §Pattern 3):
```python
"""IRON RULE: record before mutate.

Every fault injection MUST flow through inject_fault(). Direct mutation of
mock responses is forbidden under src/a2a_vs_mcp/race/. CI grep enforces.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any
import time

from ..trace import TraceRecorder
```

**FaultKind enum pattern** (Python 3.10-safe per RESEARCH.md Pitfall 6 — `pyproject.toml:10` requires `>=3.10`; `StrEnum` is 3.11+):
```python
class FaultKind(str, Enum):
    RATE_LIMIT_429 = "rate_limit_429"
    PARTIAL_JSON = "partial_json"
    SCHEMA_DRIFT = "schema_drift"
    EVENTUAL_CONSISTENCY_READ = "eventual_consistency_read"
    PARTIAL_COMMIT_5XX = "partial_commit_5xx"
```

**FailureScriptEntry dataclass** (mirror `FailureConfig` shape from `schemas.py:30-55`):
```python
@dataclass
class FailureScriptEntry:
    kind: FaultKind
    target: str
    after_calls: int = 0
    duration_calls: int = 1
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict
        return asdict(self)
```

**`inject_fault()` IRON RULE function** (record-then-mutate; D-11 + RESEARCH.md Pitfall 3):
```python
def inject_fault(
    recorder: TraceRecorder,
    *,
    fault_id: str,
    kind: FaultKind,
    target: str,
    original_response: Any,  # MUST be already-built (Pitfall 3)
) -> Any:
    """Atomic record-then-mutate. Returns the mutated response."""
    t_inject_ms = int(time.time() * 1000)
    recorder.record(
        "fault_injected",
        fault_id=fault_id,
        fault_kind=kind.value,
        target=target,
        t_inject_ms=t_inject_ms,
    )
    return _apply_mutation(kind, original_response)
```

**Recorder.record() invocation pattern** (from `src/a2a_vs_mcp/trace.py:24-39`):
```python
def record(self, event_type: str, **payload: Any) -> None:
    # ...
    event: dict[str, Any] = {
        "index": len(self.events) + 1,
        "event_type": event_type,
        "timestamp_ms": round((time.perf_counter() - self.started_at) * 1000, 3),
        "phase": phase,
    }
    # ...
    event.update(payload)
    self.events.append(event)
```
**Apply:** `inject_fault()` calls `recorder.record("fault_injected", **payload)` — kwargs flow through `event.update(payload)`. No new recorder API needed; existing kwargs interface absorbs `fault_id`, `fault_kind`, `target`, `t_inject_ms`.

---

### `src/a2a_vs_mcp/race/turn.py` (config — constant dispatch table)

**Analog:** `src/a2a_vs_mcp/trace.py:19-22` (`_PHASE_MAP`); secondary `src/a2a_vs_mcp/config.py:21-49` (`PROFILES`)

**ClassVar dispatch table pattern** (`trace.py:19-22`):
```python
_PHASE_MAP: ClassVar[dict[str, str]] = {
    "agent_register": "discovery",
    "capability_advertise": "discovery",
}
# Lookup: phase = self._PHASE_MAP.get(event_type, "execution")
```

**Module-level constant + helper pattern** (`config.py:21-49` — `PROFILES` dict + `default_profile_name()`/`resolve_profile()`):
```python
PROFILES: dict[str, ProfileConfig] = {
    "dev": ProfileConfig(...),
    "demo": ProfileConfig(...),
}

def default_profile_name() -> str:
    return os.getenv("A2A_VS_MCP_PROFILE", "dev")
```

**Apply to race/turn.py** (verbatim from CONTEXT.md D-16):
```python
from __future__ import annotations

TURN_DEFINING_EVENTS: dict[str, set[str]] = {
    "pure_mcp": {"tool_call"},
    "pure_a2a": {"agent_msg"},
    "hybrid":   {"tool_call", "agent_msg"},
}

def is_turn_defining(lane: str, event_type: str) -> bool:
    return event_type in TURN_DEFINING_EVENTS.get(lane, set())
```
Hybrid is a set-union, not a special branch (D-16). Module-level constant + small helper mirrors `_PHASE_MAP` lookup style and `default_profile_name()` shape.

---

### `src/a2a_vs_mcp/race/replay.py` (service — ndjson read + stub migrator)

**Analog:** `src/a2a_vs_mcp/trace.py:50-65` (`export_external` — ndjson WRITE; `replay.py` is the READ variant of the same idiom)

**Ndjson write pattern (to invert for read)** (`trace.py:50-65`):
```python
def export_external(self, output_dir: Path, **metadata: Any) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{self.task_id}_{self.mode}.ndjson"
    with path.open("w", encoding="utf-8") as handle:
        for event in self.events:
            record = {...}
            handle.write(json.dumps(record) + "\n")
    return path
```

**Apply (read inversion + stub migrator per RESEARCH.md Pattern 2):**
```python
from __future__ import annotations
from pathlib import Path
from typing import Any
import json

SUPPORTED_SCHEMA_VERSIONS = {"1.0"}


def migrate_v1(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Stub no-op migrator. v1.0 -> v1.0 identity. Real migration is TODO 4."""
    if not events:
        return events
    version = events[0].get("trace_schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(
            f"Unsupported trace_schema_version: {version!r}; supported={SUPPORTED_SCHEMA_VERSIONS}"
        )
    return events


def load_run(run_id: str, runs_dir: Path) -> list[dict[str, Any]]:
    path = runs_dir / f"{run_id}.json"
    events = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    return migrate_v1(events)
```

**Path-validation pattern** (per RESEARCH.md §Security V12 — `run_id` traversal guard):
```python
import re
_RUN_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")

def _validate_run_id(run_id: str) -> None:
    if not _RUN_ID_RE.fullmatch(run_id):
        raise ValueError(f"invalid run_id: {run_id!r}")
```

---

### `src/a2a_vs_mcp/race/runs.py` (service — RunWriter, threading.Lock single-writer arbiter)

**No direct analog.** Closest existing patterns:

**Analog (file write + mkdir):** `src/a2a_vs_mcp/trace.py:44-48` (`save()`):
```python
def save(self, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{self.task_id}_{self.mode}.json"
    path.write_text(json.dumps(self.events, indent=2), encoding="utf-8")
    return path
```

**Analog (ndjson append-style write):** `src/a2a_vs_mcp/trace.py:50-65` (`export_external` — uses `open("w")`; runs.py uses `open("a")` for append-only).

**Apply (per RESEARCH.md Pattern 5 — note `threading.Lock`, NOT `asyncio.Lock`, per Pitfall 1):**
```python
from __future__ import annotations
import json
import os
import threading
from pathlib import Path
from typing import Any

# Repo root / data / runs (matches conftest.py:8 PROJECT_ROOT idiom: parents[1] from tests/)
RUNS_DIR = Path(__file__).resolve().parents[3] / "data" / "runs"
BATCH_SIZE = 20  # D-04
FORCED_FLUSH_EVENTS = {"fault_injected", "fault_observed", "done"}  # D-04

_LOCKS: dict[str, threading.Lock] = {}
_WRITERS: dict[str, "RunWriter"] = {}
_REGISTRY_LOCK = threading.Lock()


class RunWriter:
    """Single-writer arbiter for data/runs/<run_id>.json (D-05)."""

    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.path = RUNS_DIR / f"{run_id}.json"
        self._buffer: list[dict[str, Any]] = []
        self._lock = _LOCKS.setdefault(run_id, threading.Lock())

    def append(self, event: dict[str, Any], *, force_flush: bool = False) -> None:
        with self._lock:
            self._buffer.append(event)
            if force_flush or len(self._buffer) >= BATCH_SIZE:
                self._flush_locked(fsync=force_flush)

    def _flush_locked(self, *, fsync: bool) -> None:
        if not self._buffer:
            return
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            for event in self._buffer:
                fh.write(json.dumps(event) + "\n")
            fh.flush()
            if fsync:  # only on forced flushes per RESEARCH.md Pitfall 2
                os.fsync(fh.fileno())
        self._buffer.clear()


def get_writer(run_id: str) -> RunWriter:
    with _REGISTRY_LOCK:
        if run_id not in _WRITERS:
            _WRITERS[run_id] = RunWriter(run_id)
        return _WRITERS[run_id]
```

**`mkdir(parents=True, exist_ok=True)` idiom** is verbatim from `trace.py:45` and `trace.py:51` — already an established project convention.

---

### `src/a2a_vs_mcp/race/ws.py` (service — ConnectionManager + per-connection asyncio.Queue + coalesce)

**No direct in-codebase analog** (first websocket in repo). Reference RESEARCH.md §Pattern 4 (FastAPI canonical `ConnectionManager` pattern verified via Context7 `/fastapi/fastapi`).

**Apply:** Per CONTEXT.md D-06..D-09 + RESEARCH.md Pattern 4. Module exports a singleton `MANAGER = ConnectionManager()`. Per-connection `asyncio.Queue`, 5/IP cap inside `connect()`, coalesce when buffer >50 keeping `NEVER_COALESCE` events intact. Constants: `HEARTBEAT_S = 15`, `COALESCE_THRESHOLD = 50`, `PER_IP_CAP = 5`.

The dataclass shape for `Connection` mirrors `src/a2a_vs_mcp/schemas.py:66-80` (`A2AMessage`) idiom — plain `@dataclass` with mixed-type fields:
```python
@dataclass
class Connection:
    ws: WebSocket
    queue: asyncio.Queue[dict[str, Any]]
    run_id: str
    last_seen_turn_index: int = -1
```

---

### `src/a2a_vs_mcp/trace.py` (MODIFIED — additive only per D-03)

**Analog:** itself — extend in place. Existing structure at `src/a2a_vs_mcp/trace.py:1-65`.

**Existing constructor + ClassVar pattern** (`trace.py:10-22`):
```python
@dataclass
class TraceRecorder:
    mode: str
    runtime: str
    task_id: str
    started_at: float = field(default_factory=time.perf_counter)
    events: list[dict[str, Any]] = field(default_factory=list)
    _step_counter: int = field(default=0, init=False, repr=False)

    _PHASE_MAP: ClassVar[dict[str, str]] = {
        "agent_register": "discovery",
        "capability_advertise": "discovery",
    }
```

**Existing record() pattern to extend** (`trace.py:24-39`):
```python
def record(self, event_type: str, **payload: Any) -> None:
    step_index: int | None = None
    if event_type in {"tool_call", "task_submit"}:
        self._step_counter += 1
        step_index = self._step_counter
    phase = self._PHASE_MAP.get(event_type, "execution")
    event: dict[str, Any] = {
        "index": len(self.events) + 1,
        "event_type": event_type,
        "timestamp_ms": round((time.perf_counter() - self.started_at) * 1000, 3),
        "phase": phase,
    }
    if step_index is not None:
        event["step_index"] = step_index
    event.update(payload)
    self.events.append(event)
```

**Required additions per D-03/D-15/D-17/D-18 + TRC-02** (RESEARCH.md Pattern 1):

1. New constructor fields (after existing ones, default `None` for backwards-compat):
   ```python
   run_id: str | None = None        # NEW (D-18)
   lane: str | None = None          # NEW (D-18)
   started_unix_ms: int = field(default_factory=lambda: int(time.time() * 1000))
   _turn_index: int = field(default=0, init=False, repr=False)  # NEW (D-15)
   _writer: "RunWriter | None" = field(default=None, init=False, repr=False)
   ```

2. New ClassVar (after `_PHASE_MAP`):
   ```python
   trace_schema_version: ClassVar[str] = "1.0"  # NEW (TRC-02)
   ```

3. New `__post_init__()`:
   ```python
   def __post_init__(self) -> None:
       if self.run_id and self.lane:
           from .race.runs import get_writer
           self._writer = get_writer(self.run_id)
   ```

4. Extend `record()` body — insert turn-index logic before the existing event-dict construction, stamp version, lane, run_id, turn_index conditionally; call `self._writer.append(event, force_flush=...)` at end:
   ```python
   from .race.turn import is_turn_defining
   if self.lane and is_turn_defining(self.lane, event_type):
       self._turn_index += 1
   # ... build event as today ...
   event["trace_schema_version"] = self.trace_schema_version
   if self.lane:
       event["lane"] = self.lane
       event["turn_index"] = self._turn_index
   if self.run_id:
       event["run_id"] = self.run_id
   # ... existing event.update(payload); self.events.append(event) ...
   if self._writer:
       self._writer.append(
           event,
           force_flush=event_type in {"fault_injected", "fault_observed", "done"},
       )
   ```

**Backwards-compat invariant:** When `run_id` and `lane` are both `None`, the new branches are no-ops. v1 callers (`platform.py`, `reasoning.py`) keep their current behavior. v1 `save()` and `export_external()` (lines 44-65) are UNTOUCHED.

---

### `src/a2a_vs_mcp/web.py` (MODIFIED — add `@app.websocket("/api/race/ws")`)

**Analog:** `src/a2a_vs_mcp/web.py:680-697` (`/api/health`); `src/a2a_vs_mcp/web.py:706-711` (`/api/run`)

**Existing imports pattern** (lines 1-42 — append to this block):
```python
from __future__ import annotations
# ... stdlib ...
from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, Response
# ...
from .api_schemas import (...)
from .config import PROFILES, default_profile_name, resolve_profile
# ... etc
```

**Apply:** Add to import block:
```python
from fastapi import WebSocket, WebSocketDisconnect, Query  # NEW
import asyncio  # NEW
import time as _time  # avoid clash; or move existing
from .race.ws import MANAGER, HEARTBEAT_S  # NEW
from .race.replay import load_run, _validate_run_id  # NEW
from .race.runs import RUNS_DIR  # NEW
```

**Existing route registration pattern** (`web.py:680-697`):
```python
@app.get("/api/health", response_model=HealthResponse)
def api_health() -> HealthResponse:
    platform = build_platform(...)
    return HealthResponse(...)
```

**New ws route** (RESEARCH.md Pattern 4 — append after the existing `/api/...` block, lines ~803+):
```python
@app.websocket("/api/race/ws")
async def race_ws(
    websocket: WebSocket,
    run_id: str = Query(...),
    last_seen_turn_index: int = Query(-1),
) -> None:
    _validate_run_id(run_id)  # path-traversal guard
    client_ip = websocket.client.host if websocket.client else "unknown"
    conn = await MANAGER.connect(websocket, run_id, last_seen_turn_index, client_ip)
    if conn is None:
        return  # 5/IP cap exceeded; ws already closed inside connect()
    try:
        # D-07 reconnect replay from disk
        if last_seen_turn_index >= 0:
            try:
                for ev in load_run(run_id, RUNS_DIR):
                    if ev.get("turn_index", -1) > last_seen_turn_index:
                        await websocket.send_json(ev)
            except FileNotFoundError:
                pass  # no run file yet; nothing to replay
        # Live tail loop
        while True:
            try:
                event = await asyncio.wait_for(conn.queue.get(), timeout=HEARTBEAT_S)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat", "ts_ms": int(_time.time() * 1000)})
    except WebSocketDisconnect:
        pass
    finally:
        await MANAGER.disconnect(conn, client_ip)
```

**Path-prefix consistency:** existing routes all use `/api/<noun>` (`/api/health`, `/api/run`, `/api/scenarios`, `/api/reports`, `/api/telemetry`). `/api/race/ws` matches the convention.

---

### `tests/race/__init__.py` (package marker)

**Analog:** None — `tests/` itself has no `__init__.py` (verified). RESEARCH.md Open Question O-5 recommends adding `tests/race/__init__.py` (empty) since pytest discovers recursively (`pyproject.toml:37` `testpaths = ["tests"]`) but a flat-named subpackage avoids name collisions.

**Apply:** Empty file. One line docstring optional:
```python
"""Race subsystem tests (Phase 6 schema gate)."""
```

---

### `tests/race/test_trace_schema.py` (test — sync, field presence + ndjson round-trip)

**Analog:** `tests/test_demo_modes.py:1-65` (sys.path bootstrap + `unittest.TestCase` style)

**sys.path bootstrap pattern** (`tests/test_demo_modes.py:1-16`):
```python
import json
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("A2A_VS_MCP_ARTIFACT_ROOT", str(PROJECT_ROOT / ".tmp" / "test_artifacts"))
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a2a_vs_mcp.trace import TraceRecorder
```
**Note:** For `tests/race/*.py`, `parents[1]` becomes `parents[2]` (because `__file__` is now two levels deep). Use `Path(__file__).resolve().parents[2]`. Or rely on the existing `tests/conftest.py` bootstrap (it already adds `src/` to `sys.path` for ALL tests including subdirs).

**unittest.TestCase pattern** (`test_demo_modes.py:38-50`):
```python
class DemoModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.platform = DemoPlatform(PROJECT_ROOT, runtime="mock")

    def test_all_modes_return_answers(self) -> None:
        ticket = self.platform.get_ticket("order_status", None, None)
        for mode in ("baseline", "mcp", "a2a", "hybrid"):
            result = self.platform.run(mode, ticket)
            self.assertTrue(result.final_answer)
```

**Apply:** Tests assert `trace_schema_version`, `lane`, `run_id`, `turn_index` keys present on every event when `run_id`+`lane` set; absent in v1 mode. Round-trip: instantiate `TraceRecorder(mode="mock", runtime="mock", task_id="t", run_id="r-1", lane="pure_mcp")`, call `.record("tool_call", tool="search")` 25 times (forces a batch flush at 20), assert ndjson at `data/runs/r-1.json` has 25 lines + each line parses + `turn_index` increments 1..25 for `tool_call` events.

---

### `tests/race/test_inject_fault.py` (test — IRON RULE atomicity)

**Analog:** `tests/test_demo_modes.py:38-50` (TestCase + setUp)

**Apply:** Mirror the `DemoModeTests` shape:
```python
class InjectFaultTests(unittest.TestCase):
    def setUp(self) -> None:
        self.recorder = TraceRecorder(
            mode="mock", runtime="mock", task_id="t",
            run_id="r-test", lane="pure_mcp",
        )

    def test_record_runs_before_mutation(self) -> None:
        from a2a_vs_mcp.race.failure import inject_fault, FaultKind
        original = {"data": "ok"}
        result = inject_fault(
            self.recorder, fault_id="f1", kind=FaultKind.PARTIAL_JSON,
            target="github.repos", original_response=original,
        )
        # IRON RULE: fault_injected event recorded BEFORE return
        self.assertEqual(self.recorder.events[-1]["event_type"], "fault_injected")
        self.assertEqual(self.recorder.events[-1]["fault_kind"], "partial_json")
```

---

### `tests/race/test_replay_stub.py` (test — ndjson round-trip + version validation)

**Analog:** `tests/test_demo_modes.py:1-30` (sys.path bootstrap + module imports)

**Apply:** Create a `tests/race/fixtures/v1_trace_v1.0.ndjson` file with 3 hand-crafted v1.0 events; assert `migrate_v1(load_run(...))` returns them unchanged; assert `migrate_v1([{"trace_schema_version": "0.9"}])` raises `ValueError`.

---

### `tests/race/test_ws_schema.py` (test — TestClient.websocket_connect for 8 event types)

**Analog (TestClient setup):** `tests/test_web_ui.py:15-23`:
```python
from fastapi.testclient import TestClient
from a2a_vs_mcp.web import app

class WebUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)
```

**Apply** (RESEARCH.md §Code Examples — websocket_connect pattern):
```python
class WsSchemaTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def test_handshake_accepts_run_id(self) -> None:
        with self.client.websocket_connect(
            "/api/race/ws?run_id=test-run&last_seen_turn_index=-1"
        ) as ws:
            # Phase 6 ships scaffold; live event source is Phase 7.
            # Heartbeat fires after HEARTBEAT_S — but for unit test, we
            # publish directly via MANAGER.publish in test setup, then receive.
            ...
```

---

### `tests/race/test_ws_lifecycle.py` (test — async, 5/IP cap + coalesce + reconnect)

**Analog:** `tests/test_api_async.py:1-33` (bare `async def test_*` under `asyncio_mode = "auto"`)

**Async test pattern** (`tests/test_api_async.py:1-20`):
```python
"""Async FastAPI integration tests — exercises ASGI app in-process via httpx."""
from __future__ import annotations

from httpx import ASGITransport, AsyncClient

from a2a_vs_mcp.web import app


async def test_api_mcp_mode_end_to_end_async() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/run", json={...})
    assert response.status_code == 200
```
**Note:** `pyproject.toml:36` sets `asyncio_mode = "auto"` — bare `async def test_*` works without `@pytest.mark.asyncio`.

**Apply:** Tests for: (a) 5/IP cap — 6 connections from same IP, 6th rejected; (b) coalesce — publish 60 `tick` events with same `(lane, task_id)`, expect ≤ original count after coalesce; (c) reconnect — write run file, connect with `last_seen_turn_index=10`, expect events with `turn_index > 10` only; (d) heartbeat — wait > `HEARTBEAT_S` (15s; use a tunable constant for testability), expect heartbeat frame.

---

## Shared Patterns

### Pattern S-1: `from __future__ import annotations` everywhere

**Source:** `src/a2a_vs_mcp/trace.py:1`, `src/a2a_vs_mcp/schemas.py:1`, `src/a2a_vs_mcp/web.py:1`, `src/a2a_vs_mcp/config.py:1`, `tests/conftest.py:2`, `tests/test_api_async.py:2`

**Apply to:** Every new `.py` file under `src/a2a_vs_mcp/race/` and `tests/race/`. Project convention; CONVENTIONS.md confirms.

```python
from __future__ import annotations
```

---

### Pattern S-2: `dataclass` + `to_dict()` for domain objects

**Source:** `src/a2a_vs_mcp/schemas.py:30-55` (FailureConfig), `:66-80` (A2AMessage), `:83-92` (AgentResult); also `src/a2a_vs_mcp/config.py:7-18` (ProfileConfig)

**Apply to:** All race domain dataclasses (`FailureScriptEntry`, `WsEvent` payload classes in `race/schemas.py`).

```python
from dataclasses import asdict, dataclass, field
from typing import Any

@dataclass
class X:
    field_a: str
    field_b: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

**Anti-pattern (do NOT use):** Pydantic `BaseModel` for domain objects. Per RESEARCH.md, Pydantic is reserved for `api_schemas.py` (the FastAPI wire layer). Race domain stays plain `@dataclass` for symmetry with `schemas.py`. Pydantic is acceptable ONLY for the YAML loader of `failure_script` (per `pydantic.TypeAdapter`).

---

### Pattern S-3: ClassVar for module-level dispatch tables on dataclasses

**Source:** `src/a2a_vs_mcp/trace.py:5,19-22`

```python
from typing import Any, ClassVar

@dataclass
class TraceRecorder:
    # ... fields ...
    _PHASE_MAP: ClassVar[dict[str, str]] = {...}
```

**Apply to:** New `trace_schema_version: ClassVar[str] = "1.0"` on `TraceRecorder` (TRC-02 — version stamp).

---

### Pattern S-4: `pathlib.Path` for all file operations + `mkdir(parents=True, exist_ok=True)` before write

**Source:** `src/a2a_vs_mcp/trace.py:44-48` (save), `:50-53` (export_external)

```python
def save(self, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{self.task_id}_{self.mode}.json"
    path.write_text(json.dumps(self.events, indent=2), encoding="utf-8")
    return path
```

**Apply to:** `race/runs.py` `RunWriter._flush_locked()` and `race/replay.py` `load_run()`. Use `path.open("a", encoding="utf-8")` for append-only ndjson.

---

### Pattern S-5: FastAPI route registration on existing `app` singleton

**Source:** `src/a2a_vs_mcp/web.py:55` (`app = FastAPI(title="A2A vs MCP Demo UI")`); routes registered at lines 432-819.

**Apply to:** New `@app.websocket("/api/race/ws")` registration in `web.py`. Reuse the same `app` instance — no second FastAPI instance, no APIRouter. Path prefix `/api/...` matches existing convention.

---

### Pattern S-6: Test sys.path bootstrap + artifact-root env var

**Source:** `tests/conftest.py:1-17` — already configures sys.path + `A2A_VS_MCP_ARTIFACT_ROOT` for all tests recursively.

```python
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.environ.setdefault("A2A_VS_MCP_ARTIFACT_ROOT", str(PROJECT_ROOT / ".tmp" / "test_artifacts"))
```

**Apply to:** Tests under `tests/race/` inherit `conftest.py` automatically (pytest rootdir discovery). No per-test bootstrap needed; just `from a2a_vs_mcp.race.failure import inject_fault`.

---

### Pattern S-7: unittest.TestCase classes runnable under pytest

**Source:** `tests/test_demo_modes.py:38` (`class DemoModeTests(unittest.TestCase)`); `tests/test_web_ui.py:20` (`class WebUiTests`); `tests/test_api_async.py` uses bare async functions (alternative).

**Apply to:** New tests under `tests/race/`. Mix-and-match per RESEARCH.md §Open Question O-5:
- Sync tests: `class XTests(unittest.TestCase)` with `setUp` / `setUpClass` + `self.assertX(...)` assertions.
- Async tests (`test_ws_lifecycle.py`): bare `async def test_*` (relies on `asyncio_mode = "auto"` from `pyproject.toml:36`).

---

### Pattern S-8: Errors via `ValueError` / `RuntimeError` with descriptive messages

**Source:** CONVENTIONS.md (`.planning/codebase/CONVENTIONS.md`) — confirmed by `pattern in trace.py` (none — silent fallbacks) but standard for explicit failures.

**Apply to:** `replay.py` `migrate_v1()` raises `ValueError(f"Unsupported trace_schema_version: {version!r}; supported={SUPPORTED_SCHEMA_VERSIONS}")`. `failure.py` `_apply_mutation()` raises `RuntimeError("HTTP 429 rate_limit (injected)")` for the rate-limit kind.

---

### Pattern S-9: Lazy import to break circular dependencies

**Source:** RESEARCH.md Pattern 1 — `from .race.runs import get_writer` inside `TraceRecorder.__post_init__()`, NOT at module top. Otherwise `race/runs.py` cannot import `from ..trace import TraceRecorder` (circular).

**Apply to:**
- `trace.py`: lazy-import `RunWriter`/`get_writer` from `race.runs` in `__post_init__()`.
- `trace.py`: lazy-import `is_turn_defining` from `race.turn` in `record()`.
- `failure.py`: top-level `from ..trace import TraceRecorder` is fine (one-way arrow `race/* -> trace`).

---

### Pattern S-10: FastAPI `Query(...)` for required ws query-string params

**Source:** RESEARCH.md §Open Question O-4 — recommended over first-message handshake.

**Apply to:** `/api/race/ws?run_id=X&last_seen_turn_index=N` route signature uses `run_id: str = Query(...)` and `last_seen_turn_index: int = Query(-1)`. Default `-1` means "no replay; live-only."

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `src/a2a_vs_mcp/race/ws.py` | service (websocket fan-out) | streaming/pub-sub | First websocket in repo. Use FastAPI canonical `ConnectionManager` pattern from RESEARCH.md §Pattern 4 (verified via Context7 `/fastapi/fastapi`). |
| `src/a2a_vs_mcp/race/runs.py` | service (single-writer arbiter w/ threading.Lock) | concurrent file-I/O | No concurrent-write file in the codebase today. Closest is `TraceRecorder.save()` (single-threaded write). Use stdlib `threading.Lock` per Pitfall 1 (NOT `asyncio.Lock`). |

For both, RESEARCH.md provides full sketches that the planner can adopt directly. No further codebase analog needs to be hunted.

---

## Metadata

**Analog search scope:**
- `src/a2a_vs_mcp/` (all modules read or grep'd: `trace.py`, `schemas.py`, `web.py`, `config.py`, `api_schemas.py`)
- `tests/` (all modules: `conftest.py`, `test_demo_modes.py`, `test_web_ui.py`, `test_api_async.py`)
- `pyproject.toml` (Python pin, asyncio_mode, testpaths)

**Files scanned:** 9 (5 source + 4 test + 1 config)
**Pattern extraction date:** 2026-04-28
**Phase:** 6 — TraceRecorder Schema Gate & Race Foundation
