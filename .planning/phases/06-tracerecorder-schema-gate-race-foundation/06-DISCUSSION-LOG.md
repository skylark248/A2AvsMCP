# Phase 6: TraceRecorder Schema Gate & Race Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-28
**Phase:** 06-tracerecorder-schema-gate-race-foundation
**Areas discussed:** Trace storage shape, Websocket scaffolding scope, FailureConfig migration shape, Turn-index ownership

---

## Trace storage shape

### Q1.1 — Trace file layout for race runs?

| Option | Description | Selected |
|--------|-------------|----------|
| One file per run, lanes inside | data/runs/<run_id>.json contains all 3 lanes' events under a top-level lane key. Replay reads one file. Matches design doc §Replay route exactly. Append-only ndjson within file. | ✓ |
| One file per (run, lane) | data/runs/<run_id>/<lane>.ndjson. Three files per run. Easier concurrent writes; replay merges by glob. Costs: extra glob, more inodes. | |
| Keep v1 path; race writes alongside | v1 keeps {task_id}_{mode}.json. Race adds separate path. Two write paths. | |

**User's choice:** One file per run, lanes inside (Recommended).

### Q1.2 — Where does run_id get generated?

| Option | Description | Selected |
|--------|-------------|----------|
| Harness, before lanes spawn | race/harness.py mints one run_id per (task, n) batch BEFORE forking lane runners; passes to each TraceRecorder. Matches CEO Decision #10. | ✓ |
| TraceRecorder constructor | Recorder generates own run_id if none passed. Simpler API, but 3 lane recorders generate 3 ids — race can't link them. | |
| Web layer (POST /api/race/start) | FastAPI route assigns run_id, returns to client, threads through. Couples web layer to id minting. | |

**User's choice:** Harness, before lanes spawn (Recommended).

### Q1.3 — v1 trace path coexist or migrate?

| Option | Description | Selected |
|--------|-------------|----------|
| Coexist — v1 untouched | Existing {task_id}_{mode}.json save() stays. Add new race-mode write. TraceRecorder gains optional run_id + lane fields. Zero blast radius. | ✓ |
| Migrate v1 to new schema | Rewrite v1 traces to also use data/runs/. Cleaner long-term but touches reasoning.py, persistence.py, report rendering. Out of v2.0 scope. | |
| v1 keeps writing, race only reads via new module | Two recorder classes. | |

**User's choice:** Coexist — v1 untouched (Recommended).

### Q1.4 — Append-only ndjson buffer location?

| Option | Description | Selected |
|--------|-------------|----------|
| In-memory list + flush every 20 events | TraceRecorder.events stays in-memory; new flush() writes ndjson append. Triggers: every 20 events, fault_injected, fault_observed, done. Verbatim CEO Decision #2. | ✓ |
| Per-event direct write | Every record() appends immediately. ~5x I/O overhead at tick rate. Rejected in CEO-T2. | |
| Buffer until done, write once | Loses durability if crash mid-run. Replay-from-disk impossible during live run. Rejected. | |

**User's choice:** In-memory list + flush every 20 events (Recommended).

**Notes:** 3 lane recorders writing to same `data/runs/<run_id>.json` ndjson needs a single-writer arbiter — flagged as D-05 planner note in CONTEXT.md.

---

## Websocket scaffolding scope

### Q2.1 — How much of /api/race/ws should Phase 6 implement?

| Option | Description | Selected |
|--------|-------------|----------|
| Full lifecycle now | Phase 6 ships: endpoint + handshake + 5/IP cap + reconnect-from-turn_index replay + >50-buffer coalesce + heartbeat. Phase 7 only plugs in event source. | ✓ |
| Thin stub now, fill in Phase 7 | Endpoint + accept + in-memory pubsub. Coalesce + replay + cap deferred. Phase 7 inherits hidden TODO list. | |
| Wire format only, no endpoint yet | Define event TypedDicts/Pydantic models; Phase 7 lights up the route. Fails TRC-04 success criterion verbatim. | |

**User's choice:** Full lifecycle now (Recommended).

### Q2.2 — Reconnect/replay source on resume?

| Option | Description | Selected |
|--------|-------------|----------|
| From data/runs/<run_id>.json | Server reads live ndjson, streams events with index > last_seen_turn_index. Matches design doc §Reconnect verbatim. Free durability. | ✓ |
| From in-memory ring buffer | Faster, but loses on server restart and bounded by buffer size. | |
| Hybrid — buffer for hot, file for cold | Adds complexity for a v1 hackathon. | |

**User's choice:** From data/runs/<run_id>.json (Recommended).

### Q2.3 — Backpressure coalesce — where lives?

| Option | Description | Selected |
|--------|-------------|----------|
| Server-side per-connection outbound buffer | Each ws connection has own asyncio.Queue. When len >50, coalesce queued ticks keeping latest per (lane, task_id). tool_call/agent_msg/fault_*/done/error/race_done never coalesced. Verbatim design doc. | ✓ |
| Client-side throttle only | Server can't keep up over slow networks; design doc rules out. | |
| Defer coalescing to Phase 7 | Risky — coalesce rule is part of TRC-04 contract. | |

**User's choice:** Server-side per-connection outbound buffer (Recommended).

### Q2.4 — Pubsub mechanism inside the server?

| Option | Description | Selected |
|--------|-------------|----------|
| asyncio.Queue per (run_id, connection) | In-process dispatcher fans out filtered by run_id. Pure asyncio, no extra deps. | ✓ |
| Redis pubsub | Production-grade, multi-worker. Adds runtime dep. Overkill for hackathon. | |
| TraceRecorder.record() callbacks | Tight coupling between trace and transport. | |

**User's choice:** asyncio.Queue per (run_id, connection) (Recommended).

---

## FailureConfig migration shape

### Q3.1 — How should v1 FailureConfig and race fault injection coexist?

| Option | Description | Selected |
|--------|-------------|----------|
| New race/failure.py module, side-by-side | v1 FailureConfig in schemas.py untouched. New module owns failure_script schema, inject_fault() with IRON RULE atomicity, FaultKind StrEnum. Zero coupling. | ✓ |
| Extend FailureConfig dataclass | Add failure_script field. One module to know about. Different lifecycles, consumers. | |
| Promote FailureConfig to base class | Cleanest OO, but no current call site benefits. YAGNI. | |

**User's choice:** New race/failure.py module, side-by-side (Recommended).

### Q3.2 — Where do fault_injected/fault_observed events get recorded?

| Option | Description | Selected |
|--------|-------------|----------|
| race/failure.py inject_fault() records both | Single helper records fault_injected BEFORE mutating. Atomic by construction (Eng iter 2 Decision #1). fault_observed = recovery state machine's job in Phase 7. | ✓ |
| TraceRecorder gains record_fault() method | Tighter coupling. Cross-concern leak. | |
| Mock APIs record their own faults | Distributed responsibility — atomicity invariant becomes hard to lint. | |

**User's choice:** race/failure.py inject_fault() records both (Recommended).

### Q3.3 — Closed kind: enum location?

| Option | Description | Selected |
|--------|-------------|----------|
| race/failure.py StrEnum | FaultKind StrEnum with 5 v1 values. Pydantic validator on failure_script entries rejects unknown at startup (matches Decision #8 ToolRegistry pattern). | ✓ |
| Module-level constants in trace.py | Strings, no enum. Typos silently misclassify. | |
| Generated from task_config.yaml | Over-engineered — 5 kinds locked in design doc. | |

**User's choice:** race/failure.py StrEnum (Recommended).

### Q3.4 — CI lint enforcement of inject_fault() IRON RULE?

| Option | Description | Selected |
|--------|-------------|----------|
| Module docstring + simple grep CI check | Module docstring states rule. CI grep ensures any race/ file mutating mock response also calls inject_fault() in same fn. ~30 min CC. | ✓ |
| AST-based lint plugin | Stronger guarantee, ~3 hr CC for 1-rule plugin. | |
| Runtime assertion in inject_fault() | Already true by construction (single fn body). Rely on docstring + code review. | |

**User's choice:** Module docstring + simple grep CI check (Recommended).

---

## Turn-index ownership

### Q4.1 — Who counts the per-lane turn_index?

| Option | Description | Selected |
|--------|-------------|----------|
| TraceRecorder per-lane counter | Recorder gains lane field. Counter increments inside record() when event_type is in turn-defining set. Single source of truth. Replay re-fires deterministically. | ✓ |
| Runners pass turn_index in (Phase 7 owns) | 3 runners, 3 implementations, drift risk. | |
| Computed at ws-emit time from event index | Couples ws layer to turn semantics; dual-update risk on lane addition. | |

**User's choice:** TraceRecorder per-lane counter (Recommended).

### Q4.2 — Where does the per-lane turn-definition rule live?

| Option | Description | Selected |
|--------|-------------|----------|
| race/turn.py with lane→predicate map | Single module: TURN_DEFINING_EVENTS = {pure_mcp: {tool_call}, pure_a2a: {agent_msg}, hybrid: {tool_call, agent_msg}}. Easy to test in isolation. | ✓ |
| Hardcoded inside TraceRecorder | Same logic, less testable. | |
| Per-runner method (turn_advances_on(event_type)) | Distributes rule across 3 files. K=3 state machine harder to verify. | |

**User's choice:** race/turn.py with lane→predicate map (Recommended).

### Q4.3 — How does replay re-fire turn_index identically?

| Option | Description | Selected |
|--------|-------------|----------|
| turn_index persisted in event payload | Every event carries turn_index. race/replay.py reads ndjson; turn_index is data. State machine consumes persisted value. Matches HEAT-03. | ✓ |
| Recompute from event types on replay | Catches rule drift loudly. | |
| Both — persist and assert on replay | Catches drift; redundant in steady state. | |

**User's choice:** turn_index persisted in event payload (Recommended).

### Q4.4 — Does TraceRecorder need a lane parameter at construction, or per-event?

| Option | Description | Selected |
|--------|-------------|----------|
| Lane at construction | TraceRecorder(mode, runtime, task_id, run_id, lane). One recorder per (run, lane) — 3 per race. Matches one-file-per-run with lane field per event. | ✓ |
| Lane per record() call | One recorder serves 3 lanes; lane= per call. Concurrent writers need lock. | |
| Lane on a sub-recorder factory | Two-tier API. Mostly cosmetic vs A. | |

**User's choice:** Lane at construction (Recommended).

---

## Claude's Discretion

- Naming of new race submodules within `src/a2a_vs_mcp/race/` (e.g., layout of `replay.py`, `ws.py`, etc.).
- Exact ndjson dispatcher shape vs. asyncio.Lock for the 3-lane single-writer arbiter (D-05). Research surfaces options; planner decides.
- Whether `tick` event coalescing lives in dispatcher module or a small `race/ws.py` helper.
- Heartbeat frequency for /api/race/ws — sensible default unless research surfaces a constraint.

## Deferred Ideas

- **Real (non-stub) trace migrator** — TODO 4. Promote when v1.0 fixtures must replay through race tooling.
- **AST-based lint plugin** for `inject_fault()` IRON RULE.
- **Redis pubsub** for multi-worker ws fanout.
- **In-memory ring buffer** for hot-replay.
- **Schema-version migration semantics beyond v1.0 → v1.0** — only matters when v1.1 ships.
- (User declined to explore additional gray areas — chose "Ready for context".)
