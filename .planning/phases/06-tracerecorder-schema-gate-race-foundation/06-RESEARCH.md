# Phase 6: TraceRecorder Schema Gate & Race Foundation - Research

**Researched:** 2026-04-28
**Domain:** Python/FastAPI backend — trace schema upgrade, ndjson durability, websocket lifecycle, fault-event emission
**Confidence:** HIGH (codebase patterns) / HIGH (FastAPI/websocket reference) / MEDIUM (cross-trace metric computation — single inferred pattern)

## Summary

Phase 6 is unusually well-specified — 18 locked decisions in CONTEXT.md leave only fill-in details. Research confirms the locked architecture is consistent with the codebase's existing dataclass-first idiom (`schemas.py`), the `_PHASE_MAP` dispatch pattern in `TraceRecorder` (which extends naturally to `TURN_DEFINING_EVENTS`), and the FastAPI route-registration convention in `web.py:432-819`. The four open fill-ins are: **(1)** the single-writer arbiter for `data/runs/<run_id>.json` (D-05, planner must pick one), **(2)** the in-process pubsub dispatcher shape, **(3)** the `wasted_tokens_before_detection` running-sum dict (master design §`race/cost.py`, line 772), and **(4)** the per-connection asyncio.Queue coalesce helper. None of these need new dependencies — `fastapi>=0.135.3` ships native websockets, `pytest-asyncio>=0.24` is already configured (`pyproject.toml:24-36` + `asyncio_mode="auto"`), and `TestClient.websocket_connect()` is the standard test idiom.

**Primary recommendation:** Mirror the dataclass + `to_dict()` idiom for every new race schema (`failure_script`, `WsEvent` payloads). Place the single-writer arbiter as a module-level `asyncio.Lock` keyed by `run_id` inside a small `race/runs.py` writer module — simpler than a queue dispatcher and matches the codebase's preference for in-method primitives. Use a `ConnectionManager`-style class for the websocket fan-out (FastAPI's canonical pattern). Add `trace_schema_version: ClassVar[str] = "1.0"` to `TraceRecorder` so it's stamped on every event without per-call cost.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Trace schema (v1.0 fields, version stamp) | Backend / `trace.py` | — | Trace is a backend domain object; v1 callers in `platform.py` use it via `TraceRecorder(...)` constructor |
| Ndjson durability (per-run file) | Backend / `race/runs.py` (new) | OS filesystem | Single-writer concurrency primitive lives in process; durability comes from `os.fsync` + append-only |
| Trace migrator stub | Backend / `race/replay.py` (new) | — | Read-only loader; pure function v1.0 → v1.0 |
| Fault-event emission | Backend / `race/failure.py` (new) | TraceRecorder | `inject_fault()` calls `recorder.record(...)` then mutates response — atomic by single function |
| Websocket lifecycle | Backend / `web.py` (route) + `race/ws.py` (helper) | asyncio | FastAPI native `@app.websocket()`; per-connection queue + coalesce in helper module |
| Per-lane turn_index | Backend / `trace.py` + `race/turn.py` (new) | — | Counter incremented inside `record()` based on `TURN_DEFINING_EVENTS[lane]` lookup |
| Pubsub fanout (run_id → connections) | Backend / `race/ws.py` | asyncio | In-process `dict[run_id, set[asyncio.Queue]]` registry; Phase 7 publishes |

## User Constraints (from CONTEXT.md)

### Locked Decisions

**Trace storage (D-01..D-05):**
- D-01: One file per run at `data/runs/<run_id>.json` (append-only ndjson, one event per line). Every event carries `lane` + `turn_index`. Replay reads one file.
- D-02: `run_id` minted by `race/harness.py` (Phase 7); Phase 6 only locks the schema field + plumbing.
- D-03: v1 trace path coexists. Existing `{task_id}_{mode}.json` `save()` stays untouched. New ndjson path activates only when `run_id` AND `lane` both set.
- D-04: Buffer = in-memory list + `flush()` writes ndjson append. Triggers: every 20 events, plus forced flush on `fault_injected`, `fault_observed`, `done`.
- D-05 (planner note): 3 lane recorders all append to same `<run_id>.json`. Need single-writer arbiter — `asyncio.Lock` on the path, OR one ndjson dispatcher fed by per-lane queues. **Research recommends `asyncio.Lock` (see Approach 1 below).**

**Websocket scaffolding (D-06..D-09):**
- D-06: Phase 6 ships full lifecycle for `/api/race/ws`: endpoint + handshake + 5/IP cap + reconnect-from-`turn_index` + >50-buffer coalesce + heartbeat. Phase 7 plugs in event source.
- D-07: Reconnect/replay reads from disk. Server tails `data/runs/<run_id>.json` and streams events whose `turn_index > last_seen_turn_index`.
- D-08: Coalesce lives server-side per-connection. Each ws connection owns an `asyncio.Queue`; when `len(queue) > 50`, queued `tick` events coalesce keeping latest per `(lane, task_id)`. `tool_call`, `agent_msg`, `fault_injected`, `fault_observed`, `done`, `error`, `race_done` are never coalesced.
- D-09: Pubsub = `asyncio.Queue` per `(run_id, connection)`. In-process dispatcher fans out to subscriber queues filtered by `run_id`. Pure asyncio, no extra deps.

**FailureConfig migration (D-10..D-14):**
- D-10: New `src/a2a_vs_mcp/race/failure.py` module, side-by-side with v1 `schemas.FailureConfig`. v1 stays untouched.
- D-11: `inject_fault()` is the single record-and-mutate helper. Atomic: `recorder.record("fault_injected", ...)` runs first; THEN computes/returns mutated response. IRON RULE locked in module docstring.
- D-12: `FaultKind = StrEnum` with 5 values: `rate_limit_429`, `partial_json`, `schema_drift`, `eventual_consistency_read`, `partial_commit_5xx`. Pydantic validator on `failure_script[].kind` rejects unknowns at startup.
- D-13: CI lint = module docstring + simple grep check. CI grep: any file under `src/a2a_vs_mcp/race/` that mutates a mock response must call `inject_fault()` in same function. ~30 min CC.
- D-14: Phase 6 ships `inject_fault()` (records `fault_injected` only). `fault_observed` recording is the recovery state machine's job in Phase 7 — Phase 6 only locks the event schema + emit path.

**Turn-index ownership (D-15..D-18):**
- D-15: `TraceRecorder` owns the per-lane counter. Recorder gains `lane: str` at construction. Counter increments inside `record()` when `event_type` is in per-lane turn-defining set.
- D-16: Turn-defining rule lives in new `src/a2a_vs_mcp/race/turn.py`:
  ```python
  TURN_DEFINING_EVENTS = {
      "pure_mcp": {"tool_call"},
      "pure_a2a": {"agent_msg"},
      "hybrid":   {"tool_call", "agent_msg"},
  }
  ```
- D-17: `turn_index` is **persisted** in every event payload. Recovery state machine in Phase 7 consumes the persisted value — no recomputation.
- D-18: `TraceRecorder(mode, runtime, task_id, run_id=None, lane=None)`. Lane fixed at construction. Three recorders per race append to same `<run_id>.json` (gated by D-05 arbiter). Backwards-compatible.

### Claude's Discretion
- Naming of new race submodules within `src/a2a_vs_mcp/race/` (e.g., whether `replay.py` lives at `race/replay.py` directly or under subpackage layout) — **research picks flat layout: `race/__init__.py`, `race/failure.py`, `race/turn.py`, `race/replay.py`, `race/runs.py`, `race/ws.py`**.
- Exact ndjson dispatcher shape vs. `asyncio.Lock` for D-05 — **research surfaces both, recommends `asyncio.Lock` (see Approach Recommendations §1)**.
- Whether `tick` event coalescing lives in same module as dispatcher or in small `race/ws.py` helper — **research recommends `race/ws.py` helper**.
- Heartbeat frequency for `/api/race/ws` — **research recommends 15s** (rationale below).

### Deferred Ideas (OUT OF SCOPE)
- Real (non-stub) trace migrator — TODO 4. Promote when v1.0 fixtures must replay through race tooling.
- AST-based lint plugin for `inject_fault()` IRON RULE. Module docstring + CI grep is sufficient at v1.
- Redis pubsub for multi-worker ws fanout. Single-process asyncio.Queue is fine until leaderboard-10x.
- In-memory ring buffer for hot-replay. Disk-backed replay from ndjson is sufficient.
- Schema-version migration semantics beyond v1.0 → v1.0 — only matters when v1.1 ships.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TRC-01 | TraceRecorder emits `t_call_start_ms`, `tokens_in`, `tokens_out` per LLM call; `t_call_ms`, `tool_name`, `status`, `error_kind` per tool call; `t_ms`, `sender`, `recipient`, `content` per inter-agent message; queryable post-run by `(run_id, lane)` in causal order | §Approach Recommendations 1 (TraceRecorder schema upgrade); §Codebase Patterns to Mirror (existing `record(**payload)` already accepts kwargs — additions are caller-side); D-15..D-18 |
| TRC-02 | `trace_schema_version` field added to TraceRecorder; stub no-op migrator recognizes v1.0 traces in `race/replay.py` | §Approach Recommendations 2 (Stub migrator); `ClassVar` constant pattern matches `_PHASE_MAP` at `trace.py:19-22` |
| TRC-03 | FailureConfig emits `fault_injected` events to TraceRecorder with `fault_id`, `fault_kind`, `target`, `t_inject_ms`; emits `fault_observed` events with `evidence`, `wasted_tokens_before_detection`, `t_observed_ms` | §Approach Recommendations 3 (Fault-event emission via `inject_fault()` helper); D-10..D-14; §`wasted_tokens_before_detection` computation pattern (running token-sum dict, master design line 772) |
| TRC-04 | Websocket event schema (`/api/race/ws`) supports `tick`, `tool_call`, `agent_msg`, `fault_injected`, `fault_observed`, `done`, `error`, `race_done`; every event carries `turn_index` per-lane | §Approach Recommendations 4 (FastAPI websocket lifecycle); D-06..D-09; master design lines 316-334 (verbatim wire format) |

## Standard Stack

### Core (already in pyproject.toml)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | `>=0.135.3` (pinned) | Websocket endpoint + route registration | Already used; native websocket support via `@app.websocket(...)` |
| uvicorn | `>=0.30.0` (pinned) | ASGI server | Already used; serves both HTTP + ws on same process |
| pytest | `>=8.0` (dev) | Backend tests | Existing test runner |
| pytest-asyncio | `>=0.24` (dev) | Async test fixtures | Already configured `asyncio_mode = "auto"` (`pyproject.toml:36`) — async tests need no decorator |
| httpx | `>=0.28` (dev) | TestClient backend | FastAPI's `TestClient.websocket_connect()` uses this |

### Supporting (stdlib only — no new deps required)
| Module | Purpose | When to Use |
|--------|---------|-------------|
| `asyncio.Lock` | Single-writer arbiter for `data/runs/<run_id>.json` (D-05) | One lock per active `run_id`, held during ndjson append |
| `asyncio.Queue` | Per-connection event buffer for ws backpressure | One queue per `(run_id, connection)` pair |
| `enum.StrEnum` (Python 3.11+) or `str` + `Enum` (3.10) | `FaultKind` enum (D-12) | Project targets Python 3.10+ (`pyproject.toml:10`); use `class FaultKind(str, Enum)` for 3.10 compat |
| `dataclasses` + `asdict` | Race schemas (`failure_script`, `WsEvent`, `RunMeta`) | Mirror `schemas.py` idiom |
| `typing.ClassVar` | `trace_schema_version` constant on `TraceRecorder` | Already used at `trace.py:19` |
| `pathlib.Path` | `data/runs/<run_id>.json` path resolution | Already used; matches `trace.py:44-65` and `web.py:43` |

### Pydantic note
Project does **not** use Pydantic for domain dataclasses (`schemas.py` is plain `@dataclass`). Pydantic is only used in `api_schemas.py` for the FastAPI request/response wire layer. **Research recommends:** keep `failure_script` schema as plain `@dataclass` for symmetry with `FailureConfig`; use Pydantic ONLY if `failure_script` is loaded from YAML and needs validators (it is — D-12 requires startup validation). Use `pydantic.TypeAdapter` for the YAML-loaded variant; the in-memory dataclass is the canonical type. *(Pattern: `api_schemas.py` already shows the project's Pydantic style.)*

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `asyncio.Lock` per `run_id` for D-05 | Single ndjson writer task fed by per-lane `asyncio.Queue` | Queue-based dispatcher is more code (~50 LoC) and adds a lifecycle (start/stop). Lock is ~5 LoC, identical correctness for hackathon scale. **Recommend Lock.** |
| `ConnectionManager` class | Module-level `_CONNECTIONS: dict[str, set[Connection]]` | Class form is the FastAPI canonical pattern (docs §"handling-disconnections-and-multiple-clients"); easier to test |
| StrEnum for `FaultKind` (Python 3.11+) | `class FaultKind(str, Enum)` (3.10 compat) | Project targets `>=3.10`; CONTEXT.md D-12 says "StrEnum" but this requires 3.11+. **Use the 3.10-compatible idiom** unless planner confirms 3.11+ minimum. |
| `os.fsync` on every flush | Buffered writes only | Crash-mid-run is the failure mode D-04 protects against. **Use `fsync` after `fault_injected | fault_observed | done` flushes only** (the forced flush triggers); skip on the every-20-events flush to avoid I/O storm. |

**Installation:** No new dependencies. Phase 6 uses only stdlib + already-pinned FastAPI/pytest.

**Version verification:** Skipped — every dependency required is already pinned in `pyproject.toml` and verified present.

## Architecture Patterns

### System Architecture Diagram

```
                     ┌─────────────────────────────────────┐
                     │ Phase 7 Race Harness (NOT Phase 6)  │
                     │  mints run_id, spawns 3 lanes       │
                     └──────────────┬──────────────────────┘
                                    │ run_id, lane∈{pure_mcp, pure_a2a, hybrid}
                                    ▼
                     ┌──────────────────────────────────┐
              ┌──────│  TraceRecorder(mode, runtime,    │──────┐
              │      │   task_id, run_id, lane)         │      │
              │      │  trace_schema_version="1.0"      │      │
              │      │  per-lane turn_index counter     │      │
              │      └──────────────┬───────────────────┘      │
              │ record()            │ record()                 │ record()
              │   tool_call         │  agent_msg               │  fault_injected
              ▼                     ▼                          ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │  race/runs.py — single-writer arbiter (asyncio.Lock per run_id)    │
   │   buffer 20 events → fsync flush                                    │
   │   forced flush on fault_injected | fault_observed | done            │
   └──────────────────────────────┬─────────────────────────────────────┘
                                  │ ndjson append
                                  ▼
                     data/runs/<run_id>.json (one event per line)
                                  │
                                  │ tail / read-once
                                  ▼
   ┌────────────────────────────────────────────────────────────────────┐
   │  race/ws.py — per-connection asyncio.Queue + coalesce when len>50  │
   │   pubsub: dict[run_id, set[Queue]]   5/IP cap   15s heartbeat      │
   └──────────────────────────────┬─────────────────────────────────────┘
                                  │
                                  ▼
                     web.py @app.websocket("/api/race/ws")
                                  │
                                  ▼
                          Browser ws client (Phase 12)
                          on reconnect: send last_seen_turn_index
                          server replays events from ndjson where
                          turn_index > last_seen_turn_index
```

| Component | File (new or extended) | Responsibility |
|-----------|------------------------|----------------|
| TraceRecorder (extended) | `src/a2a_vs_mcp/trace.py` (+~40 LoC) | Schema v1.0 fields; per-lane turn_index; ndjson flush |
| Race package init | `src/a2a_vs_mcp/race/__init__.py` (NEW) | Empty (or re-export public types) |
| Turn rules | `src/a2a_vs_mcp/race/turn.py` (NEW) | `TURN_DEFINING_EVENTS` constant + `is_turn_defining(lane, event_type)` |
| Fault helper | `src/a2a_vs_mcp/race/failure.py` (NEW) | `FaultKind` enum, `failure_script` schema, `inject_fault()` IRON-RULE helper |
| Replay/migrator | `src/a2a_vs_mcp/race/replay.py` (NEW) | `migrate_v1(events) -> events` no-op stub; `load_run(run_id) -> RunReplay` |
| Run writer | `src/a2a_vs_mcp/race/runs.py` (NEW) | `RunWriter` (single-writer arbiter via `asyncio.Lock` per run_id); `run_path(run_id)` helper |
| WS dispatcher | `src/a2a_vs_mcp/race/ws.py` (NEW) | `ConnectionManager`; per-connection `asyncio.Queue`; coalesce; reconnect replay |
| WS route | `src/a2a_vs_mcp/web.py` (extended) | `@app.websocket("/api/race/ws")` — handshake, 5/IP cap, calls `ConnectionManager.connect()` |
| Wire schemas | `src/a2a_vs_mcp/race/schemas.py` (NEW) — race-local | 8 `WsEvent` payload dataclasses + `to_dict()`; isolated from `schemas.py` |

### Recommended Project Structure
```
src/a2a_vs_mcp/
├── trace.py                    # EXTENDED: +run_id, +lane, +trace_schema_version, +ndjson flush
├── schemas.py                  # UNTOUCHED: v1 FailureConfig stays
├── web.py                      # EXTENDED: +/api/race/ws route, +5/IP cap dependency
└── race/                       # NEW PACKAGE
    ├── __init__.py             # public re-exports (FaultKind, inject_fault, etc.)
    ├── failure.py              # FaultKind enum, failure_script dataclass, inject_fault()
    ├── turn.py                 # TURN_DEFINING_EVENTS constant + helper
    ├── replay.py               # stub migrator + load_run()
    ├── runs.py                 # RunWriter (asyncio.Lock per run_id)
    ├── ws.py                   # ConnectionManager + per-connection queues + coalesce
    └── schemas.py              # WsEvent payload dataclasses (8 types)

tests/
├── conftest.py                 # UNTOUCHED
├── race/                       # NEW
│   ├── __init__.py
│   ├── test_trace_schema.py    # field-presence tests, ndjson round-trip, turn_index per-lane
│   ├── test_inject_fault.py    # IRON RULE atomicity (record-before-mutate)
│   ├── test_replay_stub.py     # v1.0 fixture round-trip through stub migrator
│   ├── test_ws_schema.py       # 8 event types via TestClient.websocket_connect
│   ├── test_ws_lifecycle.py    # 5/IP cap, coalesce, reconnect-from-turn_index, heartbeat
│   └── fixtures/
│       └── v1_trace_v1.0.ndjson # canonical v1.0 fixture for migrator test

data/                            # NEW directory (gitignore /data/runs/*.json)
└── runs/                        # ndjson run files
```

### Pattern 1: Extend TraceRecorder additively (D-03 backwards-compat)
**What:** Add optional `run_id`, `lane` to constructor; gate ndjson flush behind `_use_ndjson` property.
**When to use:** Any time both fields are set; v1 callers (`platform.py`) pass neither and get legacy behavior.
**Example:**
```python
# trace.py — extended
from __future__ import annotations
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar
import json
import os
import time

from .race.runs import RunWriter  # lazy import — only used when run_id set


@dataclass
class TraceRecorder:
    mode: str
    runtime: str
    task_id: str
    run_id: str | None = None        # NEW (D-18)
    lane: str | None = None          # NEW (D-18)
    started_at: float = field(default_factory=time.perf_counter)
    started_unix_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    events: list[dict[str, Any]] = field(default_factory=list)
    _step_counter: int = field(default=0, init=False, repr=False)
    _turn_index: int = field(default=0, init=False, repr=False)  # NEW (D-15)
    _writer: RunWriter | None = field(default=None, init=False, repr=False)

    trace_schema_version: ClassVar[str] = "1.0"  # NEW (TRC-02) — stamped on every event
    _PHASE_MAP: ClassVar[dict[str, str]] = {...}  # unchanged

    def __post_init__(self) -> None:
        if self.run_id and self.lane:
            from .race.runs import get_writer
            self._writer = get_writer(self.run_id)  # asyncio.Lock-backed singleton per run_id

    def record(self, event_type: str, **payload: Any) -> None:
        # Existing step_counter logic stays
        # NEW: turn_index increment per D-15/D-16
        from .race.turn import is_turn_defining
        if self.lane and is_turn_defining(self.lane, event_type):
            self._turn_index += 1
        event: dict[str, Any] = {
            "index": len(self.events) + 1,
            "event_type": event_type,
            "timestamp_ms": round((time.perf_counter() - self.started_at) * 1000, 3),
            "phase": self._PHASE_MAP.get(event_type, "execution"),
            "trace_schema_version": self.trace_schema_version,  # NEW (TRC-02)
        }
        if self.lane:                          # NEW (D-15)
            event["lane"] = self.lane
            event["turn_index"] = self._turn_index
        if self.run_id:
            event["run_id"] = self.run_id
        # ... step_index, payload merge unchanged
        self.events.append(event)
        # NEW: ndjson flush gating (D-04)
        if self._writer:
            self._writer.append(event, force_flush=event_type in {"fault_injected", "fault_observed", "done"})
```
*Source: extends `src/a2a_vs_mcp/trace.py:10-65` patterns; `_PHASE_MAP` at line 19-22 is the model for `TURN_DEFINING_EVENTS`.*

### Pattern 2: Stub no-op migrator (TRC-02)
**What:** A function that reads ndjson, validates `trace_schema_version == "1.0"`, returns events unchanged.
**When to use:** Replay path in `race/replay.py`. Phase 6 ships ONLY the v1.0 → v1.0 identity migrator. TODO 4 captures the real migrator.
**Example:**
```python
# race/replay.py
from __future__ import annotations
from pathlib import Path
from typing import Any
import json

SUPPORTED_SCHEMA_VERSIONS = {"1.0"}


def migrate_v1(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Stub no-op migrator. v1.0 → v1.0 identity. Real migration is TODO 4."""
    if not events:
        return events
    version = events[0].get("trace_schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(f"Unsupported trace_schema_version: {version!r}; supported={SUPPORTED_SCHEMA_VERSIONS}")
    return events


def load_run(run_id: str, runs_dir: Path) -> list[dict[str, Any]]:
    path = runs_dir / f"{run_id}.json"
    events = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return migrate_v1(events)
```

### Pattern 3: `inject_fault()` IRON RULE (TRC-03, D-11..D-14)
**What:** Single function records `fault_injected` event THEN mutates response. Atomic by construction.
**When to use:** Every place a mock API in `race/` would mutate a response under fault injection.
**Example:**
```python
# race/failure.py
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


class FaultKind(str, Enum):  # 3.10-compatible StrEnum analog
    RATE_LIMIT_429 = "rate_limit_429"
    PARTIAL_JSON = "partial_json"
    SCHEMA_DRIFT = "schema_drift"
    EVENTUAL_CONSISTENCY_READ = "eventual_consistency_read"
    PARTIAL_COMMIT_5XX = "partial_commit_5xx"


@dataclass
class FailureScriptEntry:
    kind: FaultKind
    target: str
    after_calls: int = 0
    duration_calls: int = 1
    extra: dict[str, Any] = field(default_factory=dict)  # eg truncate_at_byte, drift, behavior


def inject_fault(
    recorder: TraceRecorder,
    *,
    fault_id: str,
    kind: FaultKind,
    target: str,
    original_response: Any,
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


def _apply_mutation(kind: FaultKind, response: Any) -> Any:
    # Phase 7's mock APIs flesh this out; Phase 6 ships dispatcher only.
    if kind is FaultKind.RATE_LIMIT_429:
        raise RuntimeError("HTTP 429 rate_limit (injected)")
    # ... other kinds
    return response
```

### Pattern 4: FastAPI websocket lifecycle with reconnect-from-turn_index (TRC-04, D-06..D-09)
**What:** `@app.websocket()` route + `ConnectionManager` + per-connection queue + coalesce + heartbeat.
**When to use:** `/api/race/ws` endpoint in `web.py`; helper logic in `race/ws.py`.
**Example:**
```python
# race/ws.py (sketch — planner expands)
from __future__ import annotations
import asyncio
import json
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any
from fastapi import WebSocket, WebSocketDisconnect

HEARTBEAT_S = 15
COALESCE_THRESHOLD = 50
PER_IP_CAP = 5
NEVER_COALESCE = {"tool_call", "agent_msg", "fault_injected", "fault_observed", "done", "error", "race_done"}


@dataclass
class Connection:
    ws: WebSocket
    queue: asyncio.Queue[dict[str, Any]]
    run_id: str
    last_seen_turn_index: int = -1


class ConnectionManager:
    def __init__(self) -> None:
        self._by_run: dict[str, set[Connection]] = defaultdict(set)
        self._by_ip: dict[str, int] = defaultdict(int)
        self._lock = asyncio.Lock()

    async def connect(self, ws: WebSocket, run_id: str, last_seen_turn_index: int, client_ip: str) -> Connection | None:
        async with self._lock:
            if self._by_ip[client_ip] >= PER_IP_CAP:
                await ws.close(code=4290, reason="per-IP cap exceeded")
                return None
            self._by_ip[client_ip] += 1
        await ws.accept()
        conn = Connection(ws=ws, queue=asyncio.Queue(), run_id=run_id, last_seen_turn_index=last_seen_turn_index)
        self._by_run[run_id].add(conn)
        return conn

    async def disconnect(self, conn: Connection, client_ip: str) -> None:
        self._by_run[conn.run_id].discard(conn)
        self._by_ip[client_ip] = max(0, self._by_ip[client_ip] - 1)

    async def publish(self, run_id: str, event: dict[str, Any]) -> None:
        """Phase 7 calls this from harness; Phase 6 ships the path."""
        for conn in list(self._by_run.get(run_id, ())):
            await conn.queue.put(event)

    @staticmethod
    def coalesce(buffer: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if len(buffer) <= COALESCE_THRESHOLD:
            return buffer
        # Keep all non-coalescable events; for `tick`, keep latest per (lane, task_id)
        keepers: list[dict[str, Any]] = []
        latest_tick: dict[tuple[str, str], dict[str, Any]] = {}
        for ev in buffer:
            t = ev.get("event_type") or ev.get("type")
            if t in NEVER_COALESCE:
                keepers.append(ev)
            elif t == "tick":
                latest_tick[(ev.get("lane", ""), ev.get("task_id", ""))] = ev
            else:
                keepers.append(ev)
        return keepers + list(latest_tick.values())


MANAGER = ConnectionManager()  # module singleton; web.py imports
```

```python
# web.py — new route block
from fastapi import WebSocket, WebSocketDisconnect, Query
from .race.ws import MANAGER, HEARTBEAT_S
from .race.replay import load_run

@app.websocket("/api/race/ws")
async def race_ws(
    websocket: WebSocket,
    run_id: str = Query(...),
    last_seen_turn_index: int = Query(-1),
) -> None:
    client_ip = websocket.client.host if websocket.client else "unknown"
    conn = await MANAGER.connect(websocket, run_id, last_seen_turn_index, client_ip)
    if conn is None:
        return
    try:
        # Reconnect replay (D-07): stream events from disk where turn_index > last_seen
        if last_seen_turn_index >= 0:
            try:
                for ev in load_run(run_id, RUNS_DIR):
                    if ev.get("turn_index", -1) > last_seen_turn_index:
                        await websocket.send_json(ev)
            except FileNotFoundError:
                pass  # live-only run, nothing to replay
        # Live tail loop
        while True:
            try:
                event = await asyncio.wait_for(conn.queue.get(), timeout=HEARTBEAT_S)
                await websocket.send_json(event)
            except asyncio.TimeoutError:
                await websocket.send_json({"type": "heartbeat", "ts_ms": int(time.time() * 1000)})
    except WebSocketDisconnect:
        pass
    finally:
        await MANAGER.disconnect(conn, client_ip)
```
*Source pattern: FastAPI docs §"WebSockets" + §"handling-disconnections-and-multiple-clients" (Context7 `/fastapi/fastapi`, topic "websocket connection lifecycle"); FastAPI canonical `ConnectionManager` class.*

### Pattern 5: Single-writer arbiter via `asyncio.Lock` per run_id (D-05)
**What:** A module-level dict of `run_id → asyncio.Lock`; the lock is held while a `TraceRecorder` writes its event line. Three concurrent lane recorders never interleave bytes.
**When to use:** Inside `RunWriter.append()` in `race/runs.py`.
**Example:**
```python
# race/runs.py (sketch)
from __future__ import annotations
import asyncio
import json
import os
from pathlib import Path
from typing import Any

RUNS_DIR = Path(__file__).resolve().parents[3] / "data" / "runs"  # repo root / data / runs
BATCH_SIZE = 20

_LOCKS: dict[str, asyncio.Lock] = {}
_WRITERS: dict[str, "RunWriter"] = {}


class RunWriter:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.path = RUNS_DIR / f"{run_id}.json"
        self._buffer: list[dict[str, Any]] = []

    def append(self, event: dict[str, Any], *, force_flush: bool = False) -> None:
        self._buffer.append(event)
        if force_flush or len(self._buffer) >= BATCH_SIZE:
            self.flush()

    def flush(self) -> None:
        if not self._buffer:
            return
        RUNS_DIR.mkdir(parents=True, exist_ok=True)
        # Hold lock for the duration of the write — three lane recorders serialize here.
        # NOTE: TraceRecorder.record() is sync; in Phase 6 we use a *threading* Lock here
        # since callers may not be in the asyncio loop. Phase 7 harness can switch to
        # asyncio.Lock if all lanes are on the loop. Decision lives in planning.
        with self.path.open("a", encoding="utf-8") as fh:
            for event in self._buffer:
                fh.write(json.dumps(event) + "\n")
            fh.flush()
            os.fsync(fh.fileno())  # crash-mid-run safety on forced flushes (D-04)
        self._buffer.clear()


def get_writer(run_id: str) -> RunWriter:
    if run_id not in _WRITERS:
        _WRITERS[run_id] = RunWriter(run_id)
    return _WRITERS[run_id]
```
*Note for planner:* `TraceRecorder.record()` today is sync (`trace.py:24`) and is called from sync code paths (`platform.py`). Phase 6 should use `threading.Lock` here, NOT `asyncio.Lock`, because the harness in Phase 7 will spawn lanes via threads or run them concurrently with `asyncio.gather` of sync wrappers. Either way, `threading.Lock` is correct for both. **Open question O-1 below covers this.**

### Anti-Patterns to Avoid
- **Subclassing TraceRecorder for race mode:** breaks D-03 (v1 callers must keep working with the same class). Add fields with `None` defaults instead.
- **Pydantic `BaseModel` for race domain dataclasses:** project uses plain `@dataclass` for domain objects (`schemas.py`); Pydantic only for `api_schemas.py`. Mixing the two creates inconsistency. Use Pydantic ONLY for YAML-load validators of `failure_script`.
- **In-memory event ring for reconnect replay:** D-07 specifies disk replay. Adding an in-memory ring duplicates state and risks divergence. Disk is single source of truth.
- **Custom websocket framing:** FastAPI's `send_json()` / `receive_json()` is canonical. Do not roll your own message framing.
- **Coalescing `done`, `error`, `race_done`:** D-08 forbids it explicitly. The coalesce predicate must be a hardcoded set, not a heuristic.
- **`asyncio.Lock` from sync code:** if the recorder is called from a sync function (likely in Phase 7), `asyncio.Lock` does not apply. Use `threading.Lock` in `RunWriter` to be safe across both call modes.
- **Recomputing turn_index on replay:** D-17 says it's persisted. Trust the on-disk value.
- **Coupling `FailureConfig` (v1, schemas.py) to `TraceRecorder`:** D-10 keeps them separate. The race module is a sibling, not an extension.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Websocket protocol framing | Custom JSON-over-text envelope | `WebSocket.send_json()` / `receive_json()` | FastAPI/Starlette already handles; reduces bugs |
| WebSocket testing | Real socket against running server | `TestClient(app).websocket_connect()` (`fastapi.testclient`) | Direct ASGI call, no port juggling |
| Per-IP rate limiting | Custom middleware | Inline check inside `ConnectionManager.connect()` | 5/IP cap is per-process and small; full middleware is overkill |
| StrEnum (Python 3.11+) | `class FaultKind(StrEnum)` | `class FaultKind(str, Enum)` | Project pins `>=3.10`; 3.11 idiom would break compat. Validate with planner if 3.11+ minimum is acceptable. |
| Atomic file write | Temp file + rename | Append + `os.fsync` on key events | Append-only ndjson means every line is a complete event — partial line on crash is detected by JSON parse and skipped (`json.JSONDecodeError` already handled silently in `dataset.py`/`persistence.py` per CONVENTIONS.md §Silent fallbacks) |
| YAML schema validation | Hand-rolled type checks | `pydantic.TypeAdapter` against the `FailureScriptEntry` dataclass | One-line validator: `TypeAdapter(list[FailureScriptEntry]).validate_python(yaml_data)` |
| Token counting between fault inject & observation | Loop over trace at `fault_observed` time | Running token-sum dict per active `fault_id` (master design line 772, "race/cost.py") | O(1) per event vs O(N²) trace scan in live ws emit path |

**Key insight:** Phase 6 introduces zero new dependencies. Every problem in this phase has a stdlib or already-installed answer. The temptation is to reach for `websockets` library or `aiofiles` — neither is needed. FastAPI ships its own websocket; ndjson append is sync stdlib I/O held under a lock.

## Runtime State Inventory

> Phase 6 is a greenfield-additive phase (new modules, additive constructor args). It does not rename or migrate existing data. This section is included for completeness but most categories are empty by design.

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | None — `data/runs/` directory does not exist yet (verified by `ls /data/`). v1 trace files at `artifacts/traces/{task_id}_{mode}.json` are UNTOUCHED per D-03. | Create `data/runs/` at first write (handled by `RUNS_DIR.mkdir(parents=True, exist_ok=True)` in `RunWriter.flush`). Add `data/runs/*.json` to `.gitignore`. |
| Live service config | None — single-process FastAPI app, no external services impacted. | None |
| OS-registered state | None — no scheduled tasks, daemons, or system services. | None |
| Secrets/env vars | No new secrets. Existing `A2A_VS_MCP_PROFILE`, `A2A_VS_MCP_ARTIFACT_ROOT` (`identity.py`, `conftest.py:14`) remain authoritative. | None |
| Build artifacts | `__pycache__` may need clearing after the new race/ package is imported by tests; `pip install -e .` is already in editable mode. | None expected; if `from a2a_vs_mcp.race import ...` fails in tests, re-run `pip install -e .` |

**The canonical question:** *After every file in the repo is updated, what runtime systems still have the old string cached, stored, or registered?* — **Answer: nothing.** Phase 6 is purely additive. The v1 demo modes (`baseline`, `mcp`, `a2a`, `hybrid`) continue to call `TraceRecorder(mode, runtime, task_id)` with no `run_id`/`lane`, and the new code path activates only when both new fields are set.

## Common Pitfalls

### Pitfall 1: `asyncio.Lock` vs `threading.Lock` mismatch
**What goes wrong:** Phase 6 spec says `asyncio.Lock` for the writer arbiter (D-05). But `TraceRecorder.record()` is sync (`trace.py:24`), called from sync `platform.py` paths. An `asyncio.Lock` cannot be acquired from sync code without `asyncio.run_coroutine_threadsafe()`.
**Why it happens:** Phase 7's harness might run lanes via `asyncio.gather`, but the recorder API is sync today and v1 callers (D-03) call it sync.
**How to avoid:** Use `threading.Lock` in `RunWriter`. It is correct under both sync and async callers (a coroutine acquiring `threading.Lock` blocks only the current task — same effect as `asyncio.Lock`, slightly less efficient under heavy contention but Phase 6 has 3 lanes, not 30).
**Warning signs:** `RuntimeError: There is no current event loop` or `coroutine was never awaited` warnings during sync test runs.

### Pitfall 2: forced flush without `os.fsync` doesn't survive crash
**What goes wrong:** D-04 mandates "forced flush" on `fault_injected | fault_observed | done`. A naive `fh.flush()` only pushes to OS buffer cache, not disk. A power loss or kernel crash mid-run loses the event.
**Why it happens:** Python's file `.flush()` ≠ `fsync`. Most developers conflate them.
**How to avoid:** Pair `fh.flush()` with `os.fsync(fh.fileno())` on forced flushes only. Skip on the every-20-events flush to avoid I/O storm.
**Warning signs:** Phase 9 replay test fails with "missing fault_observed event" after a kill -9 mid-run; recovery state machine in Phase 7 sees inconsistent traces.

### Pitfall 3: `inject_fault()` called inside the response builder
**What goes wrong:** A planner writes `inject_fault(recorder, ..., original_response=build_response())` where `build_response()` itself records events. Now the order is: response build → events → fault_injected event. The fault appears AFTER the events that triggered it.
**Why it happens:** Argument evaluation order in Python is left-to-right; `original_response` is built before `inject_fault` runs `recorder.record`.
**How to avoid:** Pass already-built `original_response` from the OUTSIDE caller. The IRON RULE applies to the function body of `inject_fault` (record-then-mutate), not to the caller's argument prep. Document this in the module docstring with an example.
**Warning signs:** CI grep doesn't catch it; only the atomicity test (`test_inject_fault.py: assert event_index_of(fault_injected) < return`) does.

### Pitfall 4: `turn_index` stamped from stale counter on the LAST event
**What goes wrong:** If a `done` event is recorded immediately after a `tool_call`, the counter has just incremented. The `done` event inherits the bumped index — fine. But if a `tick` event (non-turn-defining) fires between, the `done` event's `turn_index` is the same as the `tick`'s — confusing for replay.
**Why it happens:** Per D-15, only turn-defining events bump the counter; all others read the current value.
**How to avoid:** Document explicitly that `turn_index` on a non-turn-defining event = "the turn during which this event was recorded." Recovery state machine consumes events with `turn_index >= K` semantics, which already handles this correctly. Add a test fixture that demonstrates the expected sequence.
**Warning signs:** Phase 7 K=3 window misfires by one turn in edge cases; recovery tags are wrong.

### Pitfall 5: ws reconnect replay floods the client
**What goes wrong:** A long-running race has 5000 events on disk. Client reconnects with `last_seen_turn_index=10`. Server reads all 5000 lines and dumps them in one tight loop, blocking the event loop and flooding the client.
**Why it happens:** Naive implementation reads + sends in a sync loop.
**How to avoid:** Use `await websocket.send_json(ev)` (already `await`); FastAPI's send is non-blocking but has internal buffering. For very long replays, yield control between batches: `if i % 100 == 0: await asyncio.sleep(0)`. For Phase 6 demo scale (one race ≈ 200-500 events), this isn't critical but planner should reference it.
**Warning signs:** Heartbeats stop firing during replay; client's UI freezes briefly.

### Pitfall 6: `FaultKind` declared as `StrEnum` on Python 3.10
**What goes wrong:** `from enum import StrEnum` raises `ImportError` on Python 3.10. CONTEXT.md D-12 names "StrEnum" but the project pins `>=3.10` (`pyproject.toml:10`).
**Why it happens:** `StrEnum` was added in Python 3.11.
**How to avoid:** Use `class FaultKind(str, Enum)` (the canonical 3.10 idiom — same `.value` semantics). Or bump the project minimum to 3.11+ if planner agrees. **Open question O-2 below.**
**Warning signs:** ImportError on first test run if Python 3.10 is the test interpreter.

### Pitfall 7: ndjson file grows unbounded across phases (no rotation)
**What goes wrong:** Demo runs accumulate in `data/runs/*.json` indefinitely. Disk fills.
**Why it happens:** Phase 6 ships durability but no rotation/cleanup.
**How to avoid:** Out of scope for Phase 6 per CONTEXT.md (deferred). But add a TODO comment in `race/runs.py` referencing it. Phase 10's OG-04 has cleanup logic for `data/og/`; the same pattern can be cloned for runs in a later phase.
**Warning signs:** Long demo session disk usage; not a Phase 6 acceptance criterion.

## Code Examples

Verified patterns from official sources and existing codebase:

### FastAPI websocket — minimal endpoint with disconnect handling
```python
# Source: Context7 /fastapi/fastapi (topic: "websocket connection lifecycle")
from fastapi import FastAPI, WebSocket, WebSocketDisconnect

app = FastAPI()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Message: {data}")
    except WebSocketDisconnect:
        pass  # client closed; clean up here
```

### FastAPI websocket — TestClient pattern for Phase 6 schema test
```python
# Source: Context7 /fastapi/fastapi (topic: "websocket testing TestClient")
from fastapi.testclient import TestClient

def test_ws_emits_8_event_types():
    client = TestClient(app)
    with client.websocket_connect("/api/race/ws?run_id=test-run&last_seen_turn_index=-1") as ws:
        # Phase 6 publishes test events via MANAGER.publish in test setup
        ev = ws.receive_json()
        assert ev["type"] in {"tick","tool_call","agent_msg","fault_injected","fault_observed","done","error","race_done","heartbeat"}
        assert "turn_index" in ev or ev["type"] == "race_done"  # race_done is the only no-turn_index event
```

### Existing dataclass + `to_dict()` idiom (mirror this for race schemas)
```python
# Source: src/a2a_vs_mcp/schemas.py:30-55 (FailureConfig)
@dataclass
class FailureConfig:
    db_down: bool = False
    docs_timeout: bool = False
    # ...
    def enabled(self) -> bool:
        return self.db_down or self.docs_timeout or ...

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
```

### Existing ClassVar dispatch table (mirror for `TURN_DEFINING_EVENTS`)
```python
# Source: src/a2a_vs_mcp/trace.py:19-22 (_PHASE_MAP)
class TraceRecorder:
    _PHASE_MAP: ClassVar[dict[str, str]] = {
        "agent_register": "discovery",
        "capability_advertise": "discovery",
    }
    # ... record() does: phase = self._PHASE_MAP.get(event_type, "execution")
```

### Existing FastAPI route registration (mirror for `/api/race/ws`)
```python
# Source: src/a2a_vs_mcp/web.py:680-819 — pattern of @app.get("/api/...") with response_model
@app.get("/api/health", response_model=HealthResponse)
async def api_health() -> HealthResponse:
    ...
# New: @app.websocket("/api/race/ws") follows the same /api prefix; no response_model needed.
```

### Existing pytest pattern (extend for race tests)
```python
# Source: tests/test_demo_modes.py:1-30 — sys.path bootstrap + dataclass imports
# Source: tests/test_web_ui.py:23 — TestClient(app) pattern
# Source: tests/test_api_async.py:9 — bare `async def test_*` (asyncio_mode="auto")
import unittest
from fastapi.testclient import TestClient
from a2a_vs_mcp.web import app

class WsSchemaTests(unittest.TestCase):
    def test_handshake(self) -> None:
        with TestClient(app).websocket_connect("/api/race/ws?run_id=t&last_seen_turn_index=-1") as ws:
            ...
```

### `wasted_tokens_before_detection` — running token-sum dict (Phase 6 stamps; Phase 7 fills)
```python
# Source: master design doc line 301 + iter 2 Decision #10 (race/cost.py)
# Phase 6 only ships the FIELD on the fault_observed event payload; Phase 7 adds the harness logic that
# maintains the dict and reads it on observation. Phase 6's contract is the field name + type.
# Pattern (planner can reference for Phase 7):
class FaultTokenAccumulator:
    def __init__(self) -> None:
        self._sums: dict[str, int] = {}  # fault_id -> tokens accumulated
    def on_llm_call(self, active_fault_ids: list[str], tokens_in: int, tokens_out: int) -> None:
        for fid in active_fault_ids:
            self._sums[fid] = self._sums.get(fid, 0) + tokens_in + tokens_out
    def consume(self, fault_id: str) -> int:
        return self._sums.pop(fault_id, 0)  # read-and-clear on fault_observed
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `flask-socketio` / standalone `websockets` lib | FastAPI native `@app.websocket()` | FastAPI 0.27+ (2019); now mature in 0.135 | Single dep, unified routing with HTTP |
| Per-event `os.fsync` for crash safety | Batch flush every N + forced fsync on key events | Modern SSD I/O practice | 10x throughput; key-event flushes give ≥99% durability for the events that matter |
| `aiofiles` for async file I/O | Sync I/O under a lock | Phase 6 scale (3 lanes, 200-500 events/run) | Sync is correct + simpler; aiofiles helps only at much higher write rates |
| Custom enum classes with `.value` lookups | `class X(str, Enum)` (3.10) or `StrEnum` (3.11+) | PEP 663 / Python 3.11 | Enum value equality with strings; cleaner JSON serialization |

**Deprecated/outdated:**
- `flask-socketio` style "emit" patterns: superseded by FastAPI's per-connection async loop.
- `pickle` for trace persistence: ndjson is human-readable, line-oriented, append-only — strictly better for replay debugging.

## Project Constraints (from CLAUDE.md)

- **Backend tests:** `pytest` (already configured; `tests/` is the testpath).
- **Frontend tests:** `cd frontend && npm test` (Phase 6 is backend-only — frontend ws consumer lands in Phase 12 per task instructions).
- **Start app:** `python serve_ui.py` (`uvicorn serve_ui:app` mounts FastAPI at port 8008 — verify `/api/race/ws` does not collide with existing routes — confirmed clean by grep on `web.py:432-819`).
- **Web browsing:** Use `/browse` skill, NEVER `mcp__claude-in-chrome__*`. *(N/A for Phase 6 — pure backend.)*
- **gstack skills available** for plan review (`/plan-eng-review`, `/review`, `/qa`). Worth invoking after planning.
- **graphify knowledge graph** at `graphify-out/` — no graph queried in this research because the affected files are well-known and small (5 files modified, 7 new files), but planner can `graphify query "TraceRecorder"` if structural questions arise.
- **claude mem** at `localhost:37701` — observations 80 (7:58p Apr 27) and 121 (10:17p Apr 27) confirm the PRE-DESIGN gate audit found ALL 5 fields missing. This Phase 6 is the migration the design doc gated on.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Project Python minimum is 3.10 (per `pyproject.toml:10`); `StrEnum` (3.11+) is unsafe — use `class X(str, Enum)`. `[VERIFIED: pyproject.toml:10]` | Pattern 3, Pitfall 6 | If project actually requires 3.11+, the `(str, Enum)` form still works (forward-compat); zero risk. |
| A2 | `asyncio.Lock` is wrong primitive for D-05 because `TraceRecorder.record()` is sync. Recommended `threading.Lock`. `[CITED: trace.py:24, platform.py existing call sites — sync]` | Pattern 5, Pitfall 1, Open Question O-1 | If Phase 7 makes the recorder fully async, `asyncio.Lock` becomes correct. Planner should confirm Phase 7's harness shape OR keep `threading.Lock` (correct under both). |
| A3 | Heartbeat at 15s is sensible default. `[ASSUMED]` — D-CONTEXT explicitly said "pick a sensible default". | CONTEXT § Claude's Discretion | If too long, transient TCP middleboxes drop the connection (60s is the typical idle timeout for Cloudflare/AWS). 15s is well within safe range. If too short, mobile battery cost. 15s is the canonical default for socket.io-style protocols. |
| A4 | `os.fsync` only on forced flushes (not every-20-events) is the right durability/throughput tradeoff. `[CITED: master design line 866 — "TraceRecorder append-only ndjson + batch-flush every 20 events"]` | Pitfall 2, §Don't Hand-Roll | If durability requirement is stricter ("no event loss tolerated under any crash"), every flush needs fsync — but that contradicts the design doc's batch-flush recommendation. |
| A5 | The `FailureScriptEntry.extra` dict for kind-specific fields (`truncate_at_byte`, `drift`, `behavior`, `target_calendar_id`, `serve_stale_for_calls`) is acceptable for Phase 6 — Phase 7 fleshes out per-kind validators. `[ASSUMED]` — master design YAML examples (lines 203-285) show heterogeneous fields per kind. | Pattern 3 | If user wants Pydantic discriminated-union validation per kind in Phase 6, this is more work (~1 hr). Recommend deferring until Phase 7 mock APIs land. |
| A6 | The `wasted_tokens_before_detection` running-sum dict (master design line 772 / iter 2 Decision #10 / `race/cost.py`) is **Phase 7 scope**, not Phase 6. Phase 6 only ships the FIELD on the `fault_observed` event payload schema. `[CITED: CONTEXT.md D-14 + master design line 301 — "computed server-side from authoritative TraceRecorder at fault_observed time"]` | §Code Examples (last block), §User Constraints | If user wants the cost accumulator now, Phase 6 grows by ~1 hr. Phase 6's TRC-03 contract is the schema field, not the computation. |
| A7 | The 5/IP cap is enforced inside the `ConnectionManager.connect()` method (counted via `_by_ip` dict), not via FastAPI middleware. `[ASSUMED]` — CONTEXT.md D-06 says "5/IP cap" without specifying mechanism; inline check is simpler and adequate at hackathon scale. | Pattern 4 | If a true rate-limiter is wanted (slowapi, fastapi-limiter), that's a new dep — out of scope per CONTEXT.md "no extra deps". Inline is correct here. |

**If this table is empty:** Not the case. 7 assumptions surfaced for planner/discuss-phase to ratify before plan locks.

## Open Questions

1. **`asyncio.Lock` vs `threading.Lock` for D-05 single-writer arbiter**
   - What we know: D-05 says "asyncio.Lock OR ndjson dispatcher fed by per-lane queues — research must pick one."
   - What's unclear: whether `TraceRecorder` becomes async in Phase 7 or stays sync. Today it's sync (`trace.py:24`).
   - Recommendation: **`threading.Lock`** in `RunWriter`. Correct under both sync and async callers, no API change to recorder needed for Phase 6. Planner can revisit if Phase 7 spec specifies async-only call sites.

2. **Python 3.10 vs 3.11 minimum (affects `StrEnum`)**
   - What we know: `pyproject.toml:10` pins `requires-python = ">=3.10"`. CONTEXT.md D-12 names "StrEnum" but `StrEnum` is 3.11+.
   - What's unclear: Is the project intentionally 3.10-compatible, or is the pin stale?
   - Recommendation: **Use `class FaultKind(str, Enum)` (3.10-safe).** Same `.value` and JSON serialization semantics. Bump to 3.11+ minimum is a separate decision that affects deployment + Docker base images.

3. **`ConnectionManager` lifecycle vs FastAPI app lifespan**
   - What we know: D-09 says "in-process dispatcher fans out to subscriber queues filtered by run_id." Currently sketched as module-level singleton `MANAGER = ConnectionManager()`.
   - What's unclear: When does it get cleaned up on app shutdown? FastAPI's lifespan context manager is the canonical home.
   - Recommendation: Module singleton is fine for Phase 6 (process-scoped lifetime = app lifetime). If planner wants explicit teardown, wire into `app.router.lifespan_context` later — not blocking.

4. **`/api/race/ws` query-param vs first-message handshake**
   - What we know: D-06 says "handshake + reconnect-from-turn_index"; doesn't mandate transport.
   - What's unclear: Whether `run_id` and `last_seen_turn_index` come from query string (`?run_id=X&last_seen_turn_index=N`) or from the first JSON message after `accept()`.
   - Recommendation: **Query string** for both (sketched in Pattern 4). Simpler client; no extra round-trip; consistent with HTTP `/api/...` style. First-message handshake adds ~20 LoC for no Phase-6 benefit.

5. **`tests/race/` vs flat `tests/test_race_*.py`**
   - What we know: Existing tests are flat under `tests/` (`test_demo_modes.py`, `test_web_ui.py`, `test_api_async.py`).
   - What's unclear: Does adding `tests/race/` break test discovery? `pyproject.toml:37` sets `testpaths = ["tests"]` — pytest discovers recursively.
   - Recommendation: **`tests/race/`** subdirectory. Phase 6 adds 5+ new test files; flat layout becomes hard to scan. Add `tests/race/__init__.py` (empty) to match Python package convention.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | All | ✓ | 3.10+ (per `pyproject.toml:10`) | — |
| FastAPI | `/api/race/ws` route + websocket primitives | ✓ | `>=0.135.3` (pinned in `pyproject.toml:12`) | — |
| uvicorn | ASGI server | ✓ | `>=0.30.0` (pinned in `pyproject.toml:16`) | — |
| pytest | Backend tests | ✓ | `>=8.0` (dev) | — |
| pytest-asyncio | `async def test_*` (already used in `test_api_async.py`) | ✓ | `>=0.24` + `asyncio_mode="auto"` | — |
| httpx | `TestClient` backend | ✓ | `>=0.28` (dev) | — |
| `data/runs/` directory | ndjson durability | ✗ | — | Created at first write via `RUNS_DIR.mkdir(parents=True, exist_ok=True)` — no manual setup |
| `src/a2a_vs_mcp/race/` package | New race module | ✗ | — | Created in Phase 6 plans (first plan adds `__init__.py`) |
| Python `enum.StrEnum` | `FaultKind` enum (CONTEXT.md D-12 wording) | ✗ on 3.10 / ✓ on 3.11+ | 3.11+ only | Use `class X(str, Enum)` — semantically identical for the project's needs |

**Missing dependencies with no fallback:** None.

**Missing dependencies with fallback:** `data/runs/` (auto-created), `race/` package (created by Phase 6 plans), `StrEnum` (use `(str, Enum)` form).

## Security Domain

> Phase 6 is a backend-only schema + websocket scaffolding phase with no auth, no PII, no external network surface. Master design `security_enforcement` is not explicitly set in `.planning/config.json` — defaulting to enabled per researcher contract.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | no | The `/api/race/ws` endpoint is unauthenticated by design (hackathon scope; CEO Decision #10 is a session lock, not auth) |
| V3 Session Management | partial | `run_id` acts as a soft session token; 404 on unknown `run_id` is a control. HMAC signing deferred to TODO 9. |
| V4 Access Control | no | All races are publicly viewable in v2.0 (anonymous shareable URLs explicitly in scope per `REQUIREMENTS.md` line 122) |
| V5 Input Validation | yes | `failure_script` YAML validated by Pydantic at startup (D-12); `run_id` query param sanitized to alphanumeric+hyphen before path resolution |
| V6 Cryptography | no | No crypto in Phase 6 — HMAC URL signing is TODO 9 (Phase 10 deferred) |
| V12 File and Resource | yes | `load_run(run_id, runs_dir)` MUST validate `run_id` against `^[A-Za-z0-9_-]+$` to prevent path traversal (`run_id="../../etc/passwd"`) |

### Known Threat Patterns for FastAPI/asyncio websocket

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Path traversal via `run_id` | Tampering | Regex-validate `run_id` in the ws route handler before passing to `load_run()`. Use `re.fullmatch(r"[A-Za-z0-9_-]{1,64}", run_id)`. |
| Connection flood / DoS | Denial of Service | 5/IP cap (D-06) + per-connection asyncio.Queue with bounded size (consider `asyncio.Queue(maxsize=10000)`) |
| Memory exhaustion via long-running coalesce buffer | Denial of Service | Coalesce kicks in at >50 events (D-08); buffer never grows unboundedly |
| Slowloris-style ws keepalive | Denial of Service | 15s heartbeat with timeout cuts dead connections; `WebSocketDisconnect` cleans state |
| Unbounded ndjson disk write | Denial of Service | Out of scope for Phase 6; defer to runs-rotation (later phase or TODO) |
| Worker-process race condition on `data/runs/<run_id>.json` | Tampering | Single-writer arbiter (D-05); single-process app (`serve_ui.py`); multi-worker is leaderboard-10x scope |

## Sources

### Primary (HIGH confidence)
- **CONTEXT.md** (`.planning/phases/06-tracerecorder-schema-gate-race-foundation/06-CONTEXT.md`) — 18 locked decisions D-01..D-18; this research is constrained to fill-in details only.
- **REQUIREMENTS.md** (`.planning/REQUIREMENTS.md` lines 18-21) — TRC-01..TRC-04 verbatim.
- **ROADMAP.md** (`.planning/ROADMAP.md` lines 36-45) — Phase 6 success criteria (4 items).
- **Master design doc** (`~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-design-20260427-193227.md`):
  - Lines 144-184 (Recovery state machine — what Phase 7 needs Phase 6 to emit).
  - Lines 316-334 (Websocket event schema verbatim wire format).
  - Lines 301-306 (`wasted_tokens_before_detection` server-side computation rule).
  - Lines 651-657 (PRE-DESIGN gate audit — the 5 questions Phase 6 closes).
  - Line 866 (CEO Decision #2: batch-flush every 20 events + key-event flushes).
  - Line 772 (Iter 2 Decision #10: running token-sum dict in `race/cost.py`).
- **Eng-review test plan** (`~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-eng-review-test-plan-20260427-224635.md`):
  - Lines 13, 28-32 (`inject_fault` IRON RULE atomicity tests).
  - Lines 41-44 (cost.py running token-sum dict).
  - Line 113, 146 (Phase 0 backwards-compat — v1 trace JSON schema-valid after additions).
- **trace.py** (`src/a2a_vs_mcp/trace.py:1-65`) — entire current TraceRecorder; v1 `save()`/`export_external()` proven idioms to extend.
- **schemas.py** (`src/a2a_vs_mcp/schemas.py:30-55`) — `FailureConfig` dataclass + `to_dict()` + `enabled()` pattern to mirror.
- **web.py** (`src/a2a_vs_mcp/web.py:432-819`) — FastAPI route registration patterns; no existing websocket endpoints — `/api/race/ws` is the first.
- **config.py** (`src/a2a_vs_mcp/config.py:1-76`) — `default_profile_name()`/`resolve_profile()` registry pattern (analog for `FaultKind` registry if needed).
- **CONVENTIONS.md** (`.planning/codebase/CONVENTIONS.md`) — Python style: `from __future__ import annotations`, `snake_case`, `PascalCase` classes, dataclasses over dicts, `to_dict()` pattern, lowercase generics, `X | Y` union syntax, descriptive `RuntimeError`/`ValueError` raise style.
- **TESTING.md** (`.planning/codebase/TESTING.md`) — `unittest`-style classes runnable under pytest, `TestClient(app)` pattern, mock runtime via `runtime="mock"`.
- **pyproject.toml** (`pyproject.toml:1-46`) — confirms FastAPI, pytest-asyncio, httpx already present; `asyncio_mode = "auto"` already set.
- **Context7** `/fastapi/fastapi`, topics: "websocket connection lifecycle accept disconnect broadcast", "websocket testing TestClient", "websocket ConnectionManager broadcast multiple clients".

### Secondary (MEDIUM confidence)
- FastAPI advanced docs §"handling-disconnections-and-multiple-clients" (cited via Context7 — official doc page) for the `ConnectionManager` canonical pattern.
- claude mem observations #80 (Apr 27 7:58p) and #121 (Apr 27 10:17p) confirming the TraceRecorder PRE-DESIGN gate audit found all 5 fields missing.

### Tertiary (LOW confidence)
- None. All claims verified against the codebase or master design doc.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every dep already pinned in `pyproject.toml`; no new deps required.
- Architecture: HIGH — 18 CONTEXT.md decisions already fix the architecture; research only fills naming/idiom gaps.
- Pitfalls: HIGH — derived from concrete code paths (`trace.py:24` sync; `pyproject.toml:10` Python 3.10 minimum) and master design constraints (D-04 forced flush; D-08 coalesce predicate).
- FastAPI websocket idioms: HIGH — verified via Context7 against official `/fastapi/fastapi` docs.
- `wasted_tokens_before_detection` computation: MEDIUM — design doc specifies the formula (line 301) and Phase 7 ownership (CONTEXT.md D-14); Phase 6 only ships the field.
- Single-writer arbiter choice (`threading.Lock` recommended over `asyncio.Lock`): MEDIUM-HIGH — based on `trace.py:24` sync signature, but planner should confirm in plan-checker pass.

**Research date:** 2026-04-28
**Valid until:** 2026-05-28 (30 days — stack is stable; only risk is FastAPI websocket breaking change between minor versions, vanishingly rare).

---

## RESEARCH COMPLETE

**Phase:** 6 - TraceRecorder Schema Gate & Race Foundation
**Confidence:** HIGH

### Key Findings
- All four phase requirements (TRC-01..04) map cleanly to existing codebase idioms — `_PHASE_MAP` extends to `TURN_DEFINING_EVENTS`, `FailureConfig`'s dataclass+`to_dict()` mirrors for `failure_script`, FastAPI `@app.get()` style mirrors to `@app.websocket()`. No new dependencies required.
- D-05 single-writer arbiter: research recommends **`threading.Lock`** (not `asyncio.Lock`) because `TraceRecorder.record()` is sync at `trace.py:24` and v1 callers in `platform.py` are sync. Open Question O-1 surfaces this for planner confirmation.
- D-12 `FaultKind` "StrEnum": research recommends **`class FaultKind(str, Enum)`** (Python 3.10-compatible idiom; semantically identical) — `pyproject.toml:10` pins `>=3.10` and `StrEnum` is 3.11+. Open Question O-2.
- Heartbeat = 15s default; reconnect handshake via query string (`run_id`, `last_seen_turn_index`); `tests/race/` subdirectory for new test files.
- 7 assumptions surfaced (A1..A7) and 5 open questions (O-1..O-5) for planner ratification.

### File Created
`.planning/phases/06-tracerecorder-schema-gate-race-foundation/06-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | Every dep pinned in `pyproject.toml`; zero new deps; FastAPI 0.135 ships native websockets |
| Architecture | HIGH | 18 locked CONTEXT decisions + master design verbatim wire format leave no architectural ambiguity |
| Pitfalls | HIGH | Pulled from concrete code paths (sync `record()`, Python 3.10 floor, D-04 forced-flush rule) |
| FastAPI websocket idioms | HIGH | Verified via Context7 against `/fastapi/fastapi` official docs |
| wasted_tokens computation | MEDIUM | Design doc specifies formula + Phase 7 ownership; Phase 6 ships field only |

### Open Questions
1. `threading.Lock` vs `asyncio.Lock` for D-05 (recommend `threading.Lock`)
2. Python 3.10 vs 3.11 minimum for `StrEnum` (recommend `(str, Enum)` 3.10-safe form)
3. `ConnectionManager` lifespan binding (recommend module singleton; revisit if needed)
4. Handshake transport: query string vs first-message JSON (recommend query string)
5. `tests/race/` subdirectory vs flat `tests/test_race_*.py` (recommend subdirectory)

### Ready for Planning
Research complete. Planner can now create PLAN.md files for Phase 6.
