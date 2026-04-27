# Phase 6: TraceRecorder Schema Gate & Race Foundation - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Land the trace + websocket schema upgrades that the rest of v2.0 depends on, closing the design doc's PRE-DESIGN GATE.

In scope:
- Migrate `TraceRecorder` to emit per-LLM/per-tool/per-inter-agent-message fields with millisecond timestamps and token counts.
- Add `trace_schema_version` field + stub no-op migrator that recognizes v1.0 traces in `race/replay.py`.
- New `race/failure.py` module: `FaultKind` StrEnum, `failure_script` schema, `inject_fault()` atomic helper that records `fault_injected` events before mutating mock responses.
- New websocket endpoint `/api/race/ws` with full lifecycle: handshake, 5/IP cap, reconnect-from-`turn_index` replay, >50-buffer coalesce of `tick` events, asyncio.Queue pubsub.
- New `race/turn.py` per-lane turn-definition rules; `TraceRecorder` gains `lane` + `run_id` constructor args and per-lane `turn_index` counter.
- Append-only ndjson durability at `data/runs/<run_id>.json` with batch-flush every 20 events plus forced flush at `fault_injected | fault_observed | done`.

Out of scope (deferred to later phases):
- Any runner code (`pure_mcp.py`, `pure_a2a.py`, `hybrid.py`) — Phase 7.
- Recovery state machine + `failure_mode_classifier` — Phase 7.
- Race UI / heatmap / banner — Phases 8-9.
- Real (non-stub) trace migrator — TODO 4 stays deferred.
- Mock APIs (GitHub/calendar/travel) — Phase 7.

</domain>

<decisions>
## Implementation Decisions

### Trace storage shape
- **D-01:** One file per run, lanes inside. Path: `data/runs/<run_id>.json` (append-only ndjson, one event per line). Every event carries `lane` + `turn_index` fields. Replay reads one file. Matches design doc §Replay route.
- **D-02:** `run_id` minted by `race/harness.py` (Phase 7) before lanes spawn; threaded into each `TraceRecorder` constructor. Phase 6 only locks the schema field + plumbing — Phase 7 owns the harness call site. Aligns with CEO Decision #10 (POST /api/race/start session-locked).
- **D-03:** v1 trace path coexists. Existing `{task_id}_{mode}.json` `save()` stays untouched. `TraceRecorder` gains optional `run_id` + `lane` fields; when both set, the new ndjson path is used; when unset, legacy save() runs. Zero blast radius on v1 demo code (reasoning.py, persistence.py, reporting.py).
- **D-04:** Buffer = in-memory list + `flush()` writes ndjson append. Triggers: every 20 events, plus forced flush on `fault_injected`, `fault_observed`, `done`. Verbatim CEO Decision #2.
- **D-05 (planner note):** 3 lane recorders all append to the same `data/runs/<run_id>.json` file. Need a single-writer arbiter — `asyncio.Lock` on the path, or one ndjson dispatcher fed by per-lane queues. Research must pick one and surface it before planning locks.

### Websocket scaffolding scope
- **D-06:** Phase 6 ships **full lifecycle** for `/api/race/ws`: endpoint + handshake + 5/IP cap + reconnect-from-`turn_index` + >50-buffer coalesce + heartbeat. Phase 7 only plugs in the event source. Schema gate guarantees the wire is real, not aspirational. Validates TRC-04 success criterion verbatim.
- **D-07:** Reconnect/replay reads from disk. Server tails `data/runs/<run_id>.json` and streams events whose `turn_index > last_seen_turn_index` (carried by client on reconnect). Works for both live (file tail) and dead-run replay (read-once). No in-memory ring needed — durability comes free from the ndjson file.
- **D-08:** Coalesce lives server-side per-connection. Each ws connection owns an `asyncio.Queue`; when `len(queue) > 50`, queued `tick` events coalesce keeping latest per `(lane, task_id)`. `tool_call`, `agent_msg`, `fault_injected`, `fault_observed`, `done`, `error`, `race_done` are never coalesced. Verbatim design doc §Backpressure.
- **D-09:** Pubsub = `asyncio.Queue` per `(run_id, connection)`. In-process dispatcher fans out to subscriber queues filtered by `run_id`. Pure asyncio, no extra deps. Single-process is acceptable for hackathon scope; Redis/multi-worker is leaderboard-10x scope.

### FailureConfig migration shape
- **D-10:** New `src/a2a_vs_mcp/race/failure.py` module, side-by-side with v1 `schemas.FailureConfig`. v1 `FailureConfig` (db_down/docs_timeout/remote_a2a_*) stays untouched and continues to drive v1 demo flags. Race owns: `failure_script` schema, `FaultKind` StrEnum, `inject_fault()` helper. Zero coupling between modules; lint rule scoped to `race/` only.
- **D-11:** `inject_fault()` is the single record-and-mutate helper. Signature roughly `inject_fault(recorder, fault_id, kind, target, mock_response, ...) -> mutated_response`. Atomic by construction: `recorder.record("fault_injected", ...)` runs first; only then does the helper compute and return the mutated response. IRON RULE locked in module docstring (Eng iter 2 Decision #1).
- **D-12:** `FaultKind = StrEnum` with the 5 v1 values: `rate_limit_429`, `partial_json`, `schema_drift`, `eventual_consistency_read`, `partial_commit_5xx`. Pydantic validator on `failure_script[].kind` rejects unknown kinds at startup (matches Decision #8 ToolRegistry pattern). Co-located with `inject_fault()` in `race/failure.py`.
- **D-13:** CI lint = module docstring + simple grep check. CI grep: any file under `src/a2a_vs_mcp/race/` that mutates a mock response must call `inject_fault()` in the same function. Cheap, sufficient for hackathon. ~30 min CC. AST-based lint deferred indefinitely.
- **D-14:** Phase 6 ships `inject_fault()` (records `fault_injected` only). `fault_observed` recording is the recovery state machine's job in Phase 7 — Phase 6 only locks the event schema + emit path.

### Turn-index ownership
- **D-15:** `TraceRecorder` owns the per-lane counter. Recorder gains `lane: str` at construction. The counter increments inside `record()` when `event_type` is in the per-lane turn-defining set. Single source of truth; replay re-fires deterministically because it reads the same recorded events.
- **D-16:** Turn-defining rule lives in new `src/a2a_vs_mcp/race/turn.py`:
  ```python
  TURN_DEFINING_EVENTS = {
      "pure_mcp": {"tool_call"},
      "pure_a2a": {"agent_msg"},
      "hybrid":   {"tool_call", "agent_msg"},
  }
  ```
  `TraceRecorder` imports and queries on each `record()`. Hybrid is a set-union, not a special branch.
- **D-17:** `turn_index` is **persisted** in every event payload. Replay reads ndjson; `turn_index` is just data. Recovery state machine in Phase 7 consumes the persisted value — no recomputation, no rule-drift risk. Storage cost: trivial. Matches HEAT-03 two-layer fixture test contract.
- **D-18:** `TraceRecorder(mode, runtime, task_id, run_id=None, lane=None)`. Lane fixed at construction → one recorder per `(run, lane)`. Three recorders per race append to the same `<run_id>.json` (gated by D-05 single-writer arbiter). Backwards-compatible: when `run_id` and `lane` are unset, recorder behaves as v1.

### Claude's Discretion
- Naming of new race submodules within `src/a2a_vs_mcp/race/` (e.g., whether `replay.py` lives at `race/replay.py` directly or under `race/` subpackage layout) — research can pick.
- Exact ndjson dispatcher shape vs. asyncio.Lock for D-05 — research surfaces options; planner chooses.
- Whether `tick` event coalescing lives in the same module as the dispatcher or in a small `race/ws.py` helper.
- Heartbeat frequency for /api/race/ws — pick a sensible default (e.g., 15s) unless research surfaces a constraint.

### Folded Todos
None folded. TODO 4 (production trace migrator) stays deferred — Phase 6 ships only the stub no-op migrator per REQ TRC-02 and design doc.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project + milestone state
- `.planning/PROJECT.md` — v2.0 milestone scope, core value, active requirements, key decisions table.
- `.planning/REQUIREMENTS.md` §TRC — TRC-01..04 verbatim (the locked requirement text Phase 6 implements).
- `.planning/ROADMAP.md` §Phase 6 — goal, dependencies, success criteria.
- `.planning/STATE.md` — current milestone position; carry-forward decisions from v1.0.

### Master design doc (authoritative for all of v2.0)
- `~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-design-20260427-193227.md` — 918-line approved master design (iter 3, 8.5/10). Sections directly relevant to Phase 6:
  - §Constraints + §Premises — locked premises + budget conditional on PRE-DESIGN gate.
  - §High-Level Architecture / Hardness vector — `HardnessType` StrEnum scope (Phase 7 owns; Phase 6 must not pre-empt).
  - §Recovery detection — locked state machine including `agent_msg_acknowledging_fault` regex with negation guard. Phase 7 implements; Phase 6 must emit the events the rule consumes.
  - §Websocket event schema — verbatim wire format; coalesce rule; reconnect strategy.
  - §Replay & TraceRecorder audit — PRE-DESIGN gate questions (audit confirmed all 5 answers NO; migration is Phase 6's reason for existing).
  - §GSTACK REVIEW REPORT → Iter 2 Decisions 1-10 → CEO Decisions 1-11 — every locked decision Phase 6 inherits.

### Test plan (eng-review iter 2 supplement)
- `~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-eng-review-test-plan-20260427-224635.md` — supplements iter 1 plan with tests for the 10 iter-2 decisions and 4 cross-model tensions. Phase 6 must satisfy the schema-level subset (TraceRecorder field-presence tests, ndjson round-trip, ws schema smoke test, inject_fault atomicity).

### Codebase intel (read before research)
- `.planning/codebase/ARCHITECTURE.md` — current backend layout.
- `.planning/codebase/STRUCTURE.md` — directory map.
- `.planning/codebase/TESTING.md` — pytest layout + existing fixture patterns.
- `.planning/codebase/CONVENTIONS.md` — coding conventions to honor in new race/ modules.

### Existing code that Phase 6 modifies or wraps
- `src/a2a_vs_mcp/trace.py` (65 lines) — current TraceRecorder; Phase 6 adds `lane`, `run_id`, `trace_schema_version`, ndjson flush path. v1 `save()` and `export_external()` stay.
- `src/a2a_vs_mcp/schemas.py:30` — current `FailureConfig`; untouched by Phase 6 (race adds a sibling module, not an extension).
- `src/a2a_vs_mcp/web.py` (850 lines) — Phase 6 adds `/api/race/ws` route + 5/IP cap middleware. Reuse existing FastAPI app instance and `serve_ui.py` mount.

### Deferred-context backlog
- `TODOS.md` §TODO 4 — production trace migrator stays deferred; Phase 6 ships only the stub no-op migrator.
- `TODOS.md` §TODO 8 — multi-task K=3 calibration (Phase 9 scope).
- `TODOS.md` §TODO 10 — paraphrase-resilient recovery detection (Phase 7+ scope).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TraceRecorder` (trace.py): existing `record()` + `_step_counter` + `_PHASE_MAP` patterns are the migration starting point. v1 `save()` and `export_external(ndjson)` already exist — the ndjson path proves the file format works in this codebase.
- `FailureConfig` (schemas.py): proves dataclass + `enabled()` + `to_dict()` pattern is the project's idiom; new `failure_script` schema should mirror it.
- FastAPI app + `serve_ui.py` mount: existing route registration pattern in `web.py`. Adding `/api/race/ws` follows the same idiom — no new framework.
- `default_profile_name()` / `resolve_profile()` (config.py): example of project's "profile" registry; useful pattern for `FaultKind` registration if research finds it cleaner.

### Established Patterns
- Dataclass-first schemas (`schemas.py`) with `to_dict()` for serialization. Race schemas should follow.
- `_PHASE_MAP` constant in TraceRecorder maps event_type → phase. Pattern extends naturally to `TURN_DEFINING_EVENTS` per-lane map.
- Pytest layout under `tests/` with fixtures (per `.planning/codebase/TESTING.md`). Phase 6 tests must drop into the existing `tests/` tree.

### Integration Points
- TraceRecorder constructor — gain optional `run_id` + `lane`; backwards-compatible default (`None`) preserves v1 callers.
- `web.py` route registration — new ws endpoint + 5/IP middleware.
- `serve_ui.py` (mount point) — no change expected; verify port + path collision before planning.
- New `src/a2a_vs_mcp/race/` package directory — first module-creation event in v2.0; planner must add `__init__.py` and the package wiring.

</code_context>

<specifics>
## Specific Ideas

- The user wanted the **full** websocket lifecycle in Phase 6 (handshake + cap + replay + coalesce), not a stub. Schema gate must be real, not aspirational. Phase 7 inherits a working wire.
- Ndjson durability must survive crash-mid-run — that's why D-04 batch-flush forces flush on `fault_injected | fault_observed | done`. Don't let a planner "optimize" by dropping forced flushes.
- Stub no-op migrator per REQ TRC-02 — recognizes v1.0 traces, returns them unchanged. Real migration logic stays in TODO 4 indefinitely.
- The IRON RULE on `inject_fault()` is non-negotiable — `record` BEFORE `mutate`. Module docstring + CI grep enforces.

</specifics>

<deferred>
## Deferred Ideas

- **Real (non-stub) trace migrator** — TODO 4. Promote when v1.0 fixtures must replay through race tooling.
- **AST-based lint plugin** for `inject_fault()` IRON RULE. Module docstring + CI grep is sufficient at v1; AST plugin if a real violation slips through.
- **Redis pubsub** for multi-worker ws fanout. Single-process asyncio.Queue is fine until leaderboard-10x.
- **In-memory ring buffer** for hot-replay. Disk-backed replay from ndjson is sufficient at hackathon scale.
- **Schema-version migration semantics beyond v1.0 → v1.0** — only matters when v1.1 ships.

### Reviewed Todos (not folded)
None. No TODOS.md entries match Phase 6 scope; relevant promotions (3, 5, 8) already mapped to Phases 9/10/13.

</deferred>

---

*Phase: 6-TraceRecorder Schema Gate & Race Foundation*
*Context gathered: 2026-04-28*
