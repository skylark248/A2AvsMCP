# Phase 2: Backend Trace Enrichment - Research

**Researched:** 2026-04-22
**Domain:** Python dataclass enrichment, ThreadPoolExecutor parallel dispatch, React/MUI accordion UI, FastAPI Pydantic schema extension
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**step_index (TRACE-01)**
- D-01: `step_index` is a per-run global sequence — a single counter that increments across all `tool_call` and `task_submit` events in the entire run, regardless of which agent emits them.
- D-02: Only `tool_call` and `task_submit` event types receive a `step_index`. Protocol bookkeeping events do not.
- D-03: Counter maintained in `TraceRecorder`. On every `record()` call, if `event_type in {"tool_call", "task_submit"}`, increment and attach. No changes at call sites.

**Phase tagging (TRACE-03)**
- D-04: `phase` field applied automatically in `TraceRecorder.record()` using a fixed event-type map — `_PHASE_MAP` private constant in `trace.py`. Zero changes to call sites.
- D-05: Map: `"discovery"` → `agent_register`, `capability_advertise`; `"execution"` → everything else.
- D-06: Any `event_type` not in the map defaults to `"execution"`.

**Parallel dispatch + timing (TRACE-02, TRACE-04)**
- D-07: `A2ABroker.send_tasks_parallel(messages: list[A2AMessage]) -> list[AgentResult]` dispatches all tasks concurrently using `ThreadPoolExecutor(max_workers=len(messages))`. Returns results in submission order.
- D-08: `timeout_ms` default raised from 1500ms to 5000ms in `A2ABroker.__init__()`.
- D-09: Each parallel task event carries `parallel_batch_id` (UUID, shared across all tasks in the same batch), `started_at` (epoch ms), `completed_at` (epoch ms).
- D-10: In mock mode, synthetic timing offsets are scenario-defined deterministic deltas (no `random`).

### Claude's Discretion
- Exact synthetic timing offset values for each specialist in mock parallel dispatch
- Whether `parallel_batch_id` is generated with `uuid4()` or a simpler incrementing token
- `conftest.py` additions for Phase 2 test fixtures

### Deferred Ideas (OUT OF SCOPE)
- Virtual scroll for large traces
- `phase: "discovery"` rendering in a `DiscoveryPhasePanel` (DISC-02)
- Synthetic timing driven by a per-scenario config file
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TRACE-01 | `step_index` field added to `tool_call` and `task_submit` trace events | TraceRecorder.record() verified — add `_step_counter` field, inject in record() when event_type matches |
| TRACE-02 | `parallel_batch_id`, `started_at`, `completed_at` added to parallel task events; mock mode injects deterministic synthetic timing | broker.py send_tasks_parallel() — ThreadPoolExecutor already imported; timing via time.time()*1000 for epoch ms |
| TRACE-03 | `phase` field (`"discovery"` / `"execution"`) added to all trace event types | Inject in record() via `_PHASE_MAP` constant — zero call site changes needed |
| TRACE-04 | `A2ABroker` gains `send_tasks_parallel()` method; `timeout_ms` raised to 5000ms | broker.py line 25: `timeout_ms: int = 1500` — one-line change; send_tasks_parallel adds new method |
| TRACE-05 | Trace view tier architecture — summary strip / protocol-level / full trace (A2A sub-events collapsible; 150-event soft cap) | TraceExplorer.tsx currently a flat list — needs new tier structure; MUI Accordion available, not yet used |
</phase_requirements>

---

## Summary

Phase 2 enriches the trace data model and trace viewer. The backend work is contained to two files: `trace.py` (add `_step_counter`, `_PHASE_MAP`, inject `step_index` and `phase` in `record()`) and `a2a/broker.py` (add `send_tasks_parallel()`, raise `timeout_ms` default). The frontend work replaces the flat `TraceExplorer` flat-list render with a three-tier accordion structure.

The codebase is clean for this phase. `TraceRecorder.record()` already centralises all event construction — the `index` and `timestamp_ms` fields are injected there, and `step_index`/`phase` follow exactly the same pattern. `ThreadPoolExecutor` is already imported in `broker.py` for `_execute_with_timeout`; `send_tasks_parallel()` reuses that import with `max_workers=len(messages)`. On the frontend, MUI 7.3.1 is installed and `Accordion`/`AccordionSummary`/`AccordionDetails` are available but not yet used in any trace component.

The critical integration point is the `task_submit` event type: it does not currently exist in the codebase. `send_task()` in broker.py records `a2a_message` events with `message_type="task_request"` — there is no separate `task_submit` event. The planner must decide whether `task_submit` is a new event emitted alongside `task_request` inside `send_tasks_parallel()`, or whether `step_index` is attached to the existing `a2a_message:task_request` events that represent task dispatch. The CONTEXT.md D-02 specifies `task_submit` as a distinct event type, so `send_tasks_parallel()` must emit it explicitly.

**Primary recommendation:** Wire `step_index` and `phase` into `TraceRecorder.record()` first (one file, zero call-site changes), then implement `send_tasks_parallel()` in broker.py (new method, no existing method changes), then extend the Pydantic schema and TypeScript types, then build the tier UI as a new `TraceExplorerV2` component that wraps or replaces `TraceExplorer`.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| step_index injection | Backend (trace.py) | — | All event construction is centralised in TraceRecorder.record(); no frontend logic needed |
| phase tagging | Backend (trace.py) | — | Same pattern as step_index; purely a record() concern |
| parallel_batch_id generation | Backend (broker.py) | — | Generated at dispatch time in send_tasks_parallel(); not a UI concern |
| started_at / completed_at timing | Backend (broker.py) | — | Captured via time.time() around _execute_with_timeout() calls in the executor |
| Pydantic schema extension | Backend (api_schemas.py) | — | TraceEventResponse uses ConfigDict(extra="allow") — new fields pass through automatically; explicit fields added for documentation |
| TypeScript type extension | Frontend (api.ts / api.generated.ts) | — | TraceEvent has `[key: string]: unknown` index signature — new fields already accessible; explicit optional fields added for IDE support |
| Tier accordion UI | Frontend (TraceExplorer.tsx or new component) | — | Purely rendering concern; reads existing trace array |
| 150-event soft cap | Frontend | — | Client-side slice of rendered events; backend always saves complete trace |

---

## Standard Stack

### Core (already installed — no new dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python dataclasses | stdlib | TraceRecorder fields | Already used; `_step_counter` and `_PHASE_MAP` are plain Python |
| concurrent.futures.ThreadPoolExecutor | stdlib | Parallel task dispatch | Already imported in broker.py line 2 |
| time (stdlib) | stdlib | epoch ms for started_at/completed_at | time.time()*1000 gives epoch ms; consistent with existing perf_counter usage |
| uuid (stdlib) | stdlib | parallel_batch_id generation | Already used in schemas.py via `new_id()` helper |
| @mui/material Accordion | 7.3.1 (installed) | Three-tier collapsible UI | MUI already the design system; Accordion not yet used in trace components |
| Pydantic BaseModel | already used | Schema extension | TraceEventResponse uses ConfigDict(extra="allow") — new optional fields are additive |

### No New Packages Required

All Phase 2 work uses libraries already present. `[VERIFIED: direct codebase inspection]`

---

## Architecture Patterns

### System Architecture Diagram

```
Run execution (DemoPlatform._run_a2a / _run_hybrid)
        │
        ▼
TraceRecorder.record(event_type, **payload)
        │
        ├─ event_type in {"tool_call","task_submit"}? → attach step_index (incremented _step_counter)
        ├─ _PHASE_MAP lookup → attach phase ("discovery" | "execution")
        └─ append event dict to self.events
        │
        ▼
A2ABroker.send_tasks_parallel(messages)          [NEW METHOD]
        │
        ├─ generate parallel_batch_id (uuid4 hex)
        ├─ ThreadPoolExecutor(max_workers=N)
        │   ├─ submit(send_task_with_timing, msg_0) → future_0
        │   ├─ submit(send_task_with_timing, msg_1) → future_1
        │   └─ submit(send_task_with_timing, msg_N) → future_N
        │       each wrapper records started_at=time.time()*1000 before, completed_at after
        │       and emits "task_submit" event with parallel_batch_id
        └─ results = [f.result() for f in futures_in_order]
        │
        ▼
GET /api/runs/{id} → RunResultResponse.trace: list[TraceEventResponse]
  (extra fields pass through via ConfigDict(extra="allow"))
        │
        ▼
TraceExplorer (frontend) receives TraceEvent[]
        │
        ├─ Summary Strip (always visible)
        │   total events | tool_call count | A2A msg count | discovery/execution split
        │
        ├─ Protocol Tier (Accordion, expandable)
        │   one row per meaningful event
        │   A2A events grouped by task_id → collapsed Accordion sub-group
        │   shows outcome (completed/failed) → expands to full lifecycle
        │   capped at 150 events → banner if truncated
        │
        └─ Full Trace Tier (Accordion, expandable)
            raw JSON, one object per event
            capped at 150 → banner if truncated
```

### Recommended File Modification Map

```
src/a2a_vs_mcp/
├── trace.py                  MODIFY — add _step_counter, _PHASE_MAP, update record()
└── a2a/
    └── broker.py             MODIFY — add send_tasks_parallel(), raise timeout_ms default

src/a2a_vs_mcp/
└── api_schemas.py            MODIFY — add optional fields to TraceEventResponse

frontend/src/lib/types/
└── api.ts                    MODIFY — add optional fields to TraceEvent interface
    (api.generated.ts also needs TraceEventResponse updated — but generator output)

frontend/src/components/traces/
└── TraceExplorer.tsx         MODIFY — replace flat list render with three-tier accordion

tests/
└── test_demo_modes.py        MODIFY — add Phase 2 trace field assertions
    conftest.py               MODIFY (minor) — add TraceRecorder fixture if needed
```

---

## Current Code State (exact signatures)

### TraceRecorder.record() — current shape [VERIFIED: trace.py]

```python
def record(self, event_type: str, **payload: Any) -> None:
    self.events.append(
        {
            "index": len(self.events) + 1,          # 1-based global counter, ALL events
            "event_type": event_type,
            "timestamp_ms": round((time.perf_counter() - self.started_at) * 1000, 3),
            **payload,
        }
    )
```

**Current fields on every event:** `index`, `event_type`, `timestamp_ms`, then whatever `**payload` provides.

**After Phase 2 — `record()` addition:**
```python
_step_counter: int = field(default=0)   # new dataclass field

_PHASE_MAP: ClassVar[dict[str, str]] = {
    "agent_register": "discovery",
    "capability_advertise": "discovery",
    # everything else defaults to "execution"
}

def record(self, event_type: str, **payload: Any) -> None:
    step_index = None
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

Key: `ClassVar` requires `from typing import ClassVar` — not yet imported in trace.py.

### A2ABroker — current state [VERIFIED: broker.py]

```python
class A2ABroker:
    def __init__(self, trace: TraceRecorder, max_retries: int = 1, timeout_ms: int = 1500) -> None:
```

- `ThreadPoolExecutor` already imported (line 2): `from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError`
- `_execute_with_timeout()` uses `ThreadPoolExecutor(max_workers=1)` — the parallel method will use `max_workers=len(messages)`
- `send_task()` does NOT currently emit a `task_submit` event — it records `a2a_message` with `message_type="task_request"`

**send_tasks_parallel() must:**
1. Generate `parallel_batch_id = uuid.uuid4().hex[:12]` (matches existing `new_id()` pattern in schemas.py)
2. For each message, record a `task_submit` event (this is how TRACE-01 step_index gets attached)
3. Capture `started_at = round(time.time() * 1000)` before executor submit, `completed_at` after result
4. Inject `parallel_batch_id`, `started_at`, `completed_at` into each parallel task's trace events
5. Return results list in submission order

**Implementation risk:** `send_task()` records trace events synchronously on the calling thread, but the executor runs on worker threads. Trace event ordering for parallel tasks will be interleaved — this is expected and desirable (shows actual concurrency). The `parallel_batch_id` groups them for the swimlane view in Phase 4.

**Thread-safety:** `TraceRecorder.events` is a plain Python `list`. Appending from multiple threads is GIL-protected in CPython (list.append is atomic in CPython), but this is an implementation detail, not a guarantee. For Phase 2 mock mode (fast, no real I/O), this is safe in practice. Flag for Phase 4 if real concurrent load is introduced.

### task_submit event — gap analysis [VERIFIED: full broker.py search]

The string `"task_submit"` does not appear anywhere in the current codebase. It is a new event type introduced in Phase 2. The CONTEXT.md D-02 specifies it as one of two event types that receive `step_index`. It must be explicitly emitted inside `send_tasks_parallel()` before dispatching each task.

Proposed emission point inside `send_tasks_parallel()`:
```python
self.trace.record(
    "task_submit",
    task_id=message.task_id,
    target=message.target_agent,
    capability=message.capability,
    parallel_batch_id=batch_id,
    started_at=round(time.time() * 1000),
)
```

### MCPClient.call() — step_index compatibility [VERIFIED: mcp/client.py line 106]

```python
self.trace.record(
    "tool_call",
    tool=tool,
    arguments=arguments,
    server=self.server_module,
    protocol="official_mcp_sdk",
    transport=self.transport,
    requested_transport=self.requested_transport,
)
```

`tool_call` events are recorded via `trace.record()` — the central injection in `record()` will attach `step_index` automatically. No changes needed in `mcp/client.py`.

### API Schema — TraceEventResponse [VERIFIED: api_schemas.py]

```python
class TraceEventResponse(BaseModel):
    model_config = ConfigDict(extra="allow")
    index: int
    event_type: str
    timestamp_ms: float
    message_type: str | None = None
    # ... other known fields ...
```

`ConfigDict(extra="allow")` means new fields (`step_index`, `phase`, `parallel_batch_id`, `started_at`, `completed_at`) pass through the API automatically without any schema change. However, adding them as explicit optional fields documents them and enables IDE completion for downstream consumers (Phase 4 swimlane).

### TypeScript TraceEvent type [VERIFIED: frontend/src/lib/types/api.ts]

```typescript
export interface TraceEvent {
  index: number;
  event_type: string;
  timestamp_ms: number;
  message_type?: string;
  // ... other known fields ...
  [key: string]: unknown;  // index signature — new fields already accessible
}
```

The `[key: string]: unknown` index signature means new fields are already accessible as `event.step_index`, `event.phase`, etc. without any TypeScript error. Explicit optional fields are still recommended for:
1. IDE autocomplete in the accordion UI component
2. Type narrowing (`event.step_index !== undefined`)

**Addition needed in api.ts TraceEvent:**
```typescript
step_index?: number;
phase?: "discovery" | "execution";
parallel_batch_id?: string;
started_at?: number;
completed_at?: number;
```

Note: `api.generated.ts` is generated by `scripts/generate_api_types.py` — if the generator is re-run after adding Pydantic fields, it will update `TraceEventResponse` there. The planner should decide whether to add the fields to `api.generated.ts` manually or re-run the generator. Safest: add to both `api.ts` (hand-maintained) and `api.generated.ts` (to keep in sync).

---

## Frontend Tier Architecture — Current vs Target

### Current TraceExplorer.tsx state [VERIFIED: direct inspection]

- Flat list of event cards, one `<Card>` per event
- 5 dropdown filters (Event, Actor, Tool, Protocol, Failures)
- 4 stat chips (Tool Calls, A2A Messages, Failures, Visible Events)
- `ProtocolEnvelopeDrawer` for raw JSON popup
- No pagination, no event cap, no accordion grouping
- No tiers — all events rendered at same visual weight
- MUI 7.3.1 installed; `Accordion` is available via `@mui/material` but not currently imported

### Target tier structure (from CONTEXT.md specifics)

**Tier 0: Summary Strip** (always visible, not collapsible)
- Total event count, tool_call count, A2A message count
- Phase breakdown: N discovery events / M execution events
- One compact row; scannable before expanding

**Tier 1: Protocol-Level Tier** (MUI Accordion, collapsed by default)
- One row per meaningful event
- A2A events grouped by `task_id` — each group collapses to show task outcome; expands to full lifecycle
- 150-event soft cap + banner

**Tier 2: Full Trace Tier** (MUI Accordion, collapsed by default)
- Raw JSON, one object per event
- 150-event soft cap + banner

### MUI Accordion usage [VERIFIED: MUI 7.3.1 installed, Accordion not used in traces]

MUI 7.3.1's Accordion API:
```tsx
import Accordion from '@mui/material/Accordion';
import AccordionSummary from '@mui/material/AccordionSummary';
import AccordionDetails from '@mui/material/AccordionDetails';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

<Accordion defaultExpanded={false}>
  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
    <Typography>Protocol Events</Typography>
  </AccordionSummary>
  <AccordionDetails>
    {/* event rows */}
  </AccordionDetails>
</Accordion>
```

`[ASSUMED]` — MUI 7.x Accordion API is stable and matches this pattern; verified that the package is installed but full API was not fetched from Context7.

### A2A sub-event grouping logic

A2A events in `broker.py` all carry `task_id` from the `A2AMessage`. The grouping key for the protocol-tier accordion is `event.task_id`. Events in a group span from the first `agent_register` through to `task_result` / `a2a_task_artifact`. The group header should show:
- `task_id`
- Final `status` (from the last `task_status` event in the group)
- Count of sub-events

Helper to add in `utils.ts`:
```typescript
export function groupA2AEventsByTaskId(events: TraceEvent[]): Map<string, TraceEvent[]> { ... }
```

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Parallel futures with ordered results | Custom queue + lock | `executor.map()` or `[futures[i].result() for i in range(n)]` | stdlib already handles ordering; `executor.map()` returns in submission order |
| UUID generation for batch_id | Custom counter string | `uuid.uuid4().hex[:12]` via existing `new_id()` pattern | Already established in `schemas.py` |
| Event grouping in frontend | Custom linked-list | `Map<string, TraceEvent[]>` with `reduce` | One-pass O(n) grouping; no library needed |
| Accordion expand/collapse state | Custom useState toggle per tier | MUI `Accordion` with `defaultExpanded` | Zero state management needed for static default |
| Thread-safe list appends (CPython, mock mode) | explicit `threading.Lock` around `events.append` | Plain list.append (GIL protects in CPython) | Sufficient for mock mode; note if real concurrency added in Phase 4 |

---

## Common Pitfalls

### Pitfall 1: `_step_counter` not reset between runs
**What goes wrong:** If a `TraceRecorder` instance is reused across runs (it is not currently — a fresh instance is created in `DemoPlatform.run()` per call), `step_index` would continue from the previous run's counter.
**Why it happens:** The counter is an instance field.
**How to avoid:** Current code already creates `trace = TraceRecorder(...)` fresh in `DemoPlatform.run()`. The dataclass `field(default=0)` initialises to 0 per instance. Safe as-is.
**Warning signs:** step_index starting at a value > 1 on the first event of a new run.

### Pitfall 2: `ClassVar` import missing from trace.py
**What goes wrong:** `_PHASE_MAP: ClassVar[dict[str, str]]` raises `NameError: name 'ClassVar' is not defined`.
**Why it happens:** `trace.py` currently only imports `from typing import Any`. `ClassVar` is in `typing`.
**How to avoid:** Add `ClassVar` to the import: `from typing import Any, ClassVar`.

### Pitfall 3: `task_submit` never recorded in serial send_task()
**What goes wrong:** Tests check for `task_submit` events with `step_index` — but `send_task()` never emits this event type. Tests pass for `send_tasks_parallel()` but `step_index` count is 0 for serial A2A runs.
**Why it happens:** `send_task()` emits `a2a_message:task_request`, not `task_submit`.
**How to avoid:** Decision D-02 scopes `task_submit` to `send_tasks_parallel()` only. Serial runs do not emit `task_submit` — their `step_index` count comes only from `tool_call` events. This is correct per the spec. Test assertions must account for this.

### Pitfall 4: Accordion import from wrong MUI path
**What goes wrong:** `import { Accordion } from '@mui/material'` — not all MUI components are exported from the top-level in MUI v7.
**Why it happens:** MUI v7 changed some tree-shaking defaults.
**How to avoid:** Use direct imports: `import Accordion from '@mui/material/Accordion'` — consistent with the pattern used for other MUI icons in the codebase (which use `@mui/icons-material/...`).
**Warning signs:** `Module not found` or `undefined` Accordion at runtime.

### Pitfall 5: 150-event cap applied to full events array, not per-tier
**What goes wrong:** Filtering the events array to 150 before grouping means A2A task groups that span event 148-162 are partially shown.
**Why it happens:** Cap applied too early in the pipeline.
**How to avoid:** Apply the 150-event cap to the rendered output of each tier independently, after grouping. For Protocol Tier: cap the number of rendered rows (groups count as one row). For Full Trace Tier: cap individual events.

### Pitfall 6: started_at / completed_at vs timestamp_ms confusion
**What goes wrong:** `started_at` and `completed_at` are epoch milliseconds (`time.time() * 1000`), while `timestamp_ms` is relative to `TraceRecorder.started_at` (a `perf_counter` offset). These are different time bases and must not be compared directly.
**Why it happens:** Two timing systems exist in the codebase.
**How to avoid:** Name the fields clearly (`started_at_epoch_ms`, `completed_at_epoch_ms`) — or document in code comments. The Phase 4 swimlane uses relative ordering, not absolute epoch values, so the difference matters.

---

## Code Examples

### Pattern 1: TraceRecorder enrichment (central injection)

```python
# Source: verified pattern from existing trace.py record() method
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, ClassVar

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

    def record(self, event_type: str, **payload: Any) -> None:
        step_index = None
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

Note: `_step_counter` uses `init=False` so it is excluded from `__init__` parameters and always starts at 0.

### Pattern 2: send_tasks_parallel() structure

```python
# Source: derived from existing _execute_with_timeout() in broker.py
import time
import uuid

def send_tasks_parallel(self, messages: list[A2AMessage]) -> list[AgentResult]:
    batch_id = uuid.uuid4().hex[:12]
    futures = []
    with ThreadPoolExecutor(max_workers=len(messages)) as executor:
        for message in messages:
            started_at = round(time.time() * 1000)
            self.trace.record(
                "task_submit",
                task_id=message.task_id,
                target=message.target_agent,
                capability=message.capability,
                parallel_batch_id=batch_id,
                started_at=started_at,
            )
            futures.append(executor.submit(self._run_parallel_task, message, batch_id, started_at))
        return [f.result() for f in futures]  # preserves submission order

def _run_parallel_task(self, message: A2AMessage, batch_id: str, started_at: int) -> AgentResult:
    result = self.send_task(message)
    completed_at = round(time.time() * 1000)
    self.trace.record(
        "task_submit",          # second task_submit marks completion (or use a new event type)
        task_id=message.task_id,
        target=message.target_agent,
        parallel_batch_id=batch_id,
        started_at=started_at,
        completed_at=completed_at,
        status="completed",
    )
    return result
```

**Design note:** The above pattern emits `task_submit` twice — once for dispatch, once for completion — to capture `completed_at`. Alternative: emit only one `task_submit` at dispatch and record a `task_status` with `completed_at` at completion. The planner should choose one pattern and be consistent. Both give the Phase 4 swimlane the data it needs. A simpler approach: emit a single `task_submit` at dispatch with `started_at`, and emit a separate `task_complete` event with `completed_at` (not counted toward `step_index`).

### Pattern 3: TypeScript TraceEvent extension

```typescript
// Source: extending existing api.ts TraceEvent interface
export interface TraceEvent {
  index: number;
  event_type: string;
  timestamp_ms: number;
  message_type?: string;
  agent?: string;
  sender?: string;
  target?: string;
  tool?: string;
  server?: string;
  status?: string;
  protocol?: string;
  transport?: string;
  requested_transport?: string;
  error?: string;
  // Phase 2 additions:
  step_index?: number;
  phase?: "discovery" | "execution";
  parallel_batch_id?: string;
  started_at?: number;
  completed_at?: number;
  [key: string]: unknown;
}
```

### Pattern 4: Summary Strip data derivation

```typescript
// Source: derived from existing stats computation in TraceExplorer.tsx
const summaryStats = useMemo(() => {
  const total = events.length;
  const toolCalls = events.filter(e => e.event_type === "tool_call").length;
  const a2aMessages = events.filter(isA2AEvent).length;
  const discoveryEvents = events.filter(e => e.phase === "discovery").length;
  const executionEvents = events.filter(e => e.phase === "execution").length;
  return { total, toolCalls, a2aMessages, discoveryEvents, executionEvents };
}, [events]);
```

### Pattern 5: A2A event grouping for Protocol Tier

```typescript
// Source: derived from isA2AEvent helper in utils.ts
export function groupA2AEventsByTaskId(events: TraceEvent[]): Map<string, TraceEvent[]> {
  const groups = new Map<string, TraceEvent[]>();
  for (const event of events) {
    if (isA2AEvent(event) || event.event_type === "task_status") {
      const taskId = String(event.task_id ?? event.a2a_task?.id ?? "unknown");
      if (!groups.has(taskId)) groups.set(taskId, []);
      groups.get(taskId)!.push(event);
    }
  }
  return groups;
}
```

---

## Files Modified vs Created

| File | Action | What Changes |
|------|--------|-------------|
| `src/a2a_vs_mcp/trace.py` | MODIFY | Add `_step_counter`, `_PHASE_MAP`, `ClassVar` import; update `record()` |
| `src/a2a_vs_mcp/a2a/broker.py` | MODIFY | Raise `timeout_ms=5000`; add `send_tasks_parallel()`; add `uuid` import; add `time` import |
| `src/a2a_vs_mcp/api_schemas.py` | MODIFY | Add 5 optional fields to `TraceEventResponse` |
| `frontend/src/lib/types/api.ts` | MODIFY | Add 5 optional fields to `TraceEvent` interface |
| `frontend/src/lib/types/api.generated.ts` | MODIFY | Add same 5 optional fields to `TraceEventResponse` |
| `frontend/src/components/traces/TraceExplorer.tsx` | MODIFY | Replace flat list with three-tier accordion structure |
| `frontend/src/lib/trace/utils.ts` | MODIFY | Add `groupA2AEventsByTaskId()` helper |
| `tests/test_demo_modes.py` | MODIFY | Add assertions for `step_index`, `phase`, `parallel_batch_id` on events |
| `frontend/src/features/traces/TraceWorkspacePage.tsx` | NO CHANGE | Already consumes `<TraceExplorer>` — tier structure is internal to that component |

**No new files required** — all work is additive modifications to existing files.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| No step ordering on events | `step_index` on action events | Phase 2 | UI can render step N-of-M for tool calls and task submits |
| No phase classification | `phase: "discovery"\|"execution"` on every event | Phase 2 | Enables Phase 4 DiscoveryPhasePanel and phase-filter dropdowns |
| No parallel dispatch | `send_tasks_parallel()` with batch UUID | Phase 2 | Enables Phase 4 swimlane timeline (UI-02) |
| Flat trace list (all events same weight) | Three-tier accordion | Phase 2 | Presenter can navigate large traces without scrolling through 80+ protocol bookkeeping events |
| `timeout_ms=1500` default | `timeout_ms=5000` | Phase 2 | Parallel mock tasks have headroom; real MCP transports (stdio, http) won't false-timeout |

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | MUI 7.x `Accordion` component API matches standard `Accordion`/`AccordionSummary`/`AccordionDetails` import pattern | Standard Stack, Code Examples | Low — MUI Accordion is stable API; would need to adjust import path |
| A2 | `task_submit` is a net-new event type emitted only from `send_tasks_parallel()` (not retrofitted into `send_task()`) | Architecture Patterns | Medium — if step_index is also wanted on serial A2A task dispatch, send_task() needs modification too |
| A3 | CPython GIL makes list.append thread-safe for Phase 2 mock-only usage | Common Pitfalls | Low for mock mode; would need explicit lock if Phase 3 introduces real concurrent HTTP calls |
| A4 | `started_at`/`completed_at` use epoch ms (`time.time()*1000`) for swimlane compatibility in Phase 4 | Code Examples | Low — either epoch or relative works; Phase 4 uses relative ordering |

---

## Open Questions

1. **Does `send_task()` (serial) also need to emit `task_submit`?**
   - What we know: CONTEXT.md D-02 says `task_submit` events get `step_index`. Serial A2A runs only call `send_task()`. Currently `send_task()` emits `a2a_message:task_request` instead.
   - What's unclear: Whether `step_index` should appear in serial A2A traces (currently it would not, since no `task_submit` events exist in that path).
   - Recommendation: If `step_index` should also count serial A2A dispatch, add a `task_submit` record at the top of `send_task()`. If `step_index` is exclusively for the parallel path, leave `send_task()` unchanged. The CONTEXT.md is silent on this — the planner should decide and document.

2. **`completed_at` capture location**
   - What we know: `completed_at` must be set after the task completes, before results are returned.
   - What's unclear: Should completion timing be recorded inside a wrapper called from the executor, or should the executor submit `send_task()` directly and the completion time be recorded in a wrapper?
   - Recommendation: Use a thin `_run_parallel_task()` wrapper (see Code Examples Pattern 2 above) that captures timing around the `send_task()` call.

3. **`api.generated.ts` regeneration vs manual edit**
   - What we know: `api.generated.ts` has a header comment: "Do not edit by hand; update backend schemas and rerun the generator."
   - What's unclear: Whether the generator (`scripts/generate_api_types.py`) is in scope to run as part of Phase 2.
   - Recommendation: Check if the generator can be run cleanly. If yes, add Pydantic fields to `api_schemas.py` and re-run the generator. If no (requires running server), manually patch `api.generated.ts` and add a comment.

---

## Environment Availability

Step 2.6: SKIPPED — Phase 2 is purely code modifications. No new external tools, services, databases, or CLI utilities are introduced. All dependencies (`ThreadPoolExecutor`, `uuid`, MUI Accordion) are already available in the installed environment.

---

## Validation Architecture

Step 4: SKIPPED — `workflow.nyquist_validation` is explicitly `false` in `.planning/config.json`.

---

## Security Domain

This phase adds new fields to an internal trace data structure and a new method to a local broker. No authentication, no new API endpoints, no external data ingestion. ASVS V5 (Input Validation) is the only potentially applicable category — `parallel_batch_id` is a UUID generated internally, never from user input. No security concerns for this phase.

---

## Sources

### Primary (HIGH confidence)
- Direct inspection: `src/a2a_vs_mcp/trace.py` (52 lines) — exact record() signature verified
- Direct inspection: `src/a2a_vs_mcp/a2a/broker.py` (192 lines) — exact send_task(), _execute_with_timeout() signatures verified
- Direct inspection: `src/a2a_vs_mcp/mcp/client.py` (344 lines) — tool_call record() call verified
- Direct inspection: `src/a2a_vs_mcp/platform.py` (317 lines) — dispatch flow for all 4 modes verified
- Direct inspection: `src/a2a_vs_mcp/api_schemas.py` — TraceEventResponse, ConfigDict(extra="allow") verified
- Direct inspection: `frontend/src/lib/types/api.ts` — TraceEvent interface with index signature verified
- Direct inspection: `frontend/src/components/traces/TraceExplorer.tsx` (284 lines) — flat list render pattern verified
- Direct inspection: `frontend/src/lib/trace/utils.ts` (86 lines) — isA2AEvent, helpers verified
- Direct inspection: `frontend/package.json` — MUI 7.3.1 confirmed
- Direct inspection: `tests/test_demo_modes.py` — existing test patterns, TraceRecorder fixture usage verified
- Direct inspection: `.planning/config.json` — nyquist_validation: false confirmed
- Direct inspection: `.planning/phases/02-backend-trace-enrichment/02-CONTEXT.md` — all D-01 through D-10 decisions

### Secondary (MEDIUM confidence)
- MUI Accordion API usage pattern [ASSUMED based on MUI stable API; not fetched from Context7]

---

## Metadata

**Confidence breakdown:**
- Backend changes (trace.py, broker.py): HIGH — exact current signatures verified, changes are additive
- Schema extension (api_schemas.py, api.ts): HIGH — ConfigDict(extra="allow") and index signature verified; extension is trivial
- Frontend tier architecture: HIGH for structure; MEDIUM for exact MUI Accordion import path (assumed stable)
- Test patterns: HIGH — existing test patterns verified; new assertions follow same shape

**Research date:** 2026-04-22
**Valid until:** 2026-05-22 (stable codebase; MUI 7.x is stable)
