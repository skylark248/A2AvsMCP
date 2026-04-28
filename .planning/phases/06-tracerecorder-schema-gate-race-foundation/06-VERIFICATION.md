---
phase: 06-tracerecorder-schema-gate-race-foundation
verified: 2026-04-28T07:00:00Z
status: passed
score: 4/4 success criteria verified, 4/4 TRC requirements satisfied
overrides_applied: 0
---

# Phase 6: TraceRecorder Schema Gate & Race Foundation — Verification Report

**Phase Goal:** Land the trace + websocket schema upgrades that the rest of v2.0 depends on, closing the design doc's PRE-DESIGN GATE.

**Verified:** 2026-04-28
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (ROADMAP Success Criteria)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | A developer can replay a recorded run and query its events filtered by `(run_id, lane)` in causal order, with LLM, tool, and inter-agent message events all carrying their per-event timing fields. | VERIFIED | `race/replay.py:load_run` + `events_for_lane` compose to deliver causal-ordered per-lane query. `tests/race/test_trace_schema.py::CausalOrderQueryTests::test_query_by_run_id_lane_causal_order` passes. `tests/race/test_trace_schema.py::NdjsonRoundtripTests::test_ndjson_roundtrip_25_events` confirms 25 events round-trip with strictly increasing turn_index 1..25 and matching tool_name fields. TRC-01 timing fields (`t_call_ms`, `tool_name`, `status`, `error_kind`, `t_ms`, `sender`, `recipient`, `content`) flow through `**payload` kwargs in `trace.py:record()` and survive the ndjson roundtrip. |
| 2 | Every trace file written by TraceRecorder carries `trace_schema_version`, and a v1.0 fixture loaded through `race/replay.py` is recognized by the stub no-op migrator without error. | VERIFIED | `trace.py:54` stamps `"trace_schema_version": self.trace_schema_version` on EVERY event (including legacy v1 callers). `race/replay.py:migrate_v1` is identity for v1.0 and raises `ValueError` on other versions. `tests/race/fixtures/v1_trace_v1.0.ndjson` (3 events) loads cleanly via `tests/race/test_replay_stub.py::StubMigratorTests::test_v1_fixture_loads_through_load_run`. |
| 3 | When FailureConfig fires, both `fault_injected` and `fault_observed` events appear in the trace with `fault_id`, `fault_kind`, `target`, `t_inject_ms`, `t_observed_ms`, `evidence`, and `wasted_tokens_before_detection`. | VERIFIED (schema half — runtime emission of fault_observed deferred to Phase 7 per D-14, which is explicit in plan + ROADMAP). `race/failure.py:inject_fault` records `fault_injected` with all 4 TRC-03 fields atomically (record-before-mutate IRON RULE). `race/schemas.py:FaultObservedEvent` declares all 7 TRC-03 fields and is constructible end-to-end (`tests/race/test_inject_fault.py::WireSchemaConstructibilityTests::test_fault_observed_event_dataclass_constructible` passes). All 5 D-12 FaultKind values present and exercised. Override is implicit per D-14; user explicitly noted not to penalize. |
| 4 | A websocket client connecting to `/api/race/ws` receives `tick`, `tool_call`, `agent_msg`, `fault_injected`, `fault_observed`, `done`, `error`, and `race_done` events, each tagged with a per-lane `turn_index`. | VERIFIED | `web.py:857 @app.websocket("/api/race/ws")` registered on existing FastAPI app. Full lifecycle present (handshake → `_validate_run_id` guard → 5/IP cap → reconnect-from-disk → 15s heartbeat). All 8 wire literals locked in `race/schemas.py:WIRE_EVENT_TYPES`. `tests/race/test_ws_schema.py::WsSchemaTests::test_handshake_accepts_run_id` exercises sending and receiving each of the 8 event types over a real `TestClient.websocket_connect` and asserts `turn_index` field presence on each received event. |

**Score:** 4/4 truths verified.

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/a2a_vs_mcp/race/__init__.py` | Race package marker | VERIFIED | Present, 2 lines, has docstring + `__future__` import. Imports cleanly. |
| `src/a2a_vs_mcp/race/schemas.py` | 8 WsEvent dataclasses + WIRE_EVENT_TYPES | VERIFIED | All 8 dataclasses (TickEvent, ToolCallEvent, AgentMsgEvent, FaultInjectedEvent, FaultObservedEvent, DoneEvent, ErrorEvent, RaceDoneEvent) present; each has `to_dict()` returning dict with `event_type` matching wire literal. `WIRE_EVENT_TYPES` frozenset matches D-06 verbatim. |
| `src/a2a_vs_mcp/race/turn.py` | TURN_DEFINING_EVENTS dispatch + is_turn_defining | VERIFIED | Verbatim D-16 dispatch table. `is_turn_defining()` uses `.get(lane, set())` silent fallback. Pure dispatch, no state. |
| `src/a2a_vs_mcp/trace.py` | TraceRecorder extended with run_id/lane/turn_index/schema_version + ndjson hook | VERIFIED | Additive extension: `run_id: str \| None`, `lane: str \| None`, `started_unix_ms`, `_turn_index`, `_writer` fields; `trace_schema_version: ClassVar[str] = "1.0"`. `__post_init__` lazy-imports `get_writer`. `record()` stamps schema_version unconditionally; lane/turn_index/run_id conditional. ndjson force_flush set is exact `{fault_injected, fault_observed, done}` per D-04. Legacy `save()`, `export_external()`, `latency_ms()` UNTOUCHED — D-03 verified by 100/100 legacy tests still passing. |
| `src/a2a_vs_mcp/race/failure.py` | FaultKind enum + FailureScriptEntry + inject_fault + Pydantic loader | VERIFIED | Module docstring contains literal `IRON RULE` (D-13 grep prereq). `class FaultKind(str, Enum)` with 5 D-12 values. `inject_fault` records BEFORE `_apply_mutation` (verified by source-order at lines 75/83 + atomicity test on raise paths). `validate_failure_script` uses `pydantic.TypeAdapter`. |
| `src/a2a_vs_mcp/race/runs.py` | RunWriter + get_writer + threading.Lock arbiter | VERIFIED | `BATCH_SIZE = 20`, `FORCED_FLUSH_EVENTS = frozenset({"fault_injected","fault_observed","done"})`, `RUNS_DIR = parents[3] / "data" / "runs"`. `RunWriter` uses `threading.Lock` (NOT asyncio); `os.fsync` only on forced flush. `get_writer` is process-singleton via `_REGISTRY_LOCK`. Append-only `open("a")` mode. No back-import to `..trace` (no circular). |
| `src/a2a_vs_mcp/race/replay.py` | load_run + migrate_v1 + _validate_run_id + events_for_lane | VERIFIED | `SUPPORTED_SCHEMA_VERSIONS = frozenset({"1.0"})`. `_RUN_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")` applied via `re.fullmatch`. `migrate_v1` raises `ValueError` on missing/wrong version. `events_for_lane` is causal-order-preserving list comprehension. |
| `src/a2a_vs_mcp/race/ws.py` | ConnectionManager + Connection + MANAGER + constants + coalesce | VERIFIED | Constants exact: `HEARTBEAT_S=15`, `COALESCE_THRESHOLD=50`, `PER_IP_CAP=5`, `QUEUE_MAX=10000`. `NEVER_COALESCE` is exact 7-element D-08 set (tick excluded). `Connection` is `@dataclass(eq=False)` (identity-hashable for `set[Connection]`). `MANAGER` module singleton. 5/IP cap enforced inline in `connect()` with code 4290. `coalesce()` static method preserves NEVER_COALESCE events; coalesces tick by `(lane, task_id)`. |
| `src/a2a_vs_mcp/web.py` | `/api/race/ws` route registered | VERIFIED | `@app.websocket("/api/race/ws")` at line 857 on existing app. Imports at lines 43-45: `load_run, _validate_run_id, RUNS_DIR, MANAGER, HEARTBEAT_S`. Path-traversal guard runs FIRST (close 4400). Reconnect replay reads disk via `load_run`. 15s heartbeat via `asyncio.wait_for(conn.queue.get(), timeout=HEARTBEAT_S)`. `WebSocketDisconnect` caught; `finally` always disconnects. |
| `tests/race/__init__.py` + 6 test modules + fixture | Full TRC test suite | VERIFIED | All 8 expected files present. `tests/race/fixtures/v1_trace_v1.0.ndjson` has 3 valid JSON-per-line events. 37 tests across 6 modules; `pytest tests/race/` reports 37/37 pass in 0.42s. |
| `.gitignore` | `/data/runs/` ignored | VERIFIED | `grep -F "/data/runs/" .gitignore` — confirmed by Plan 05 summary. |

**Artifact Status:** 11/11 VERIFIED.

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|-----|-----|--------|---------|
| `trace.py:__post_init__` | `race/runs.py:get_writer` | lazy import after `run_id+lane` set | WIRED | Line 33: `from .race.runs import get_writer`. Verified by Plan 05 smoke test (writer wired, file appears on first force_flush event). |
| `trace.py:record` | `race/turn.py:is_turn_defining` | lazy import inside record() | WIRED | Line 40: `from .race.turn import is_turn_defining`. Drives turn_index increments verified across pure_mcp/pure_a2a/hybrid lanes in test_trace_schema.py. |
| `race/failure.py:inject_fault` | `trace.py:TraceRecorder.record` | direct call BEFORE `_apply_mutation` | WIRED | Source-order: line 75 (`recorder.record("fault_injected", ...)`) precedes line 83 (`_apply_mutation`). IRON RULE atomicity verified by `test_record_runs_before_raise` (event present even when mutation raises). |
| `race/runs.py:RunWriter._flush_locked` | `data/runs/<run_id>.json` | `path.open("a") + os.fsync` on forced flush | WIRED | Append mode confirmed (`open("a"`); fsync conditional on `force_flush=True` from D-04 set. |
| `web.py:race_ws` | `race/ws.py:MANAGER` | module singleton import | WIRED | Line 45: `from .race.ws import MANAGER, HEARTBEAT_S`. `MANAGER.connect`, `.disconnect`, queue.get all reachable in route body. |
| `web.py:race_ws` | `race/replay.py:load_run, _validate_run_id` | explicit import | WIRED | Line 43; `_validate_run_id(run_id)` runs FIRST in route body (line 865), `load_run` on reconnect path (line 879). |
| `web.py:race_ws` | `race/runs.py:RUNS_DIR` | explicit import | WIRED | Line 44; passed to `load_run(run_id, RUNS_DIR)`. |

**Key Links:** 7/7 WIRED.

---

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| `trace.py:TraceRecorder` | `events` list + ndjson disk file | `record(**payload)` from caller | YES — verified end-to-end via 25-event ndjson roundtrip test | FLOWING |
| `race/ws.py:MANAGER._by_run` | `dict[run_id, set[Connection]]` | `MANAGER.connect()` populates; `MANAGER.publish()` reads | YES — `test_publish_enqueues_to_all_connections_for_run` + reconnect tests prove fan-out | FLOWING |
| `race/runs.py:RunWriter.path` | ndjson file at `RUNS_DIR / f"{run_id}.json"` | `_flush_locked` writes; `load_run` reads | YES — round-trip test confirms 25 events written and read back | FLOWING |
| `race/replay.py:load_run` | event list | reads ndjson from disk | YES — `test_reconnect_skips_seen_turns` proves disk read populates ws stream | FLOWING |
| `web.py:race_ws` queue | `dict[str, Any]` events sent over ws | `conn.queue.put_nowait` from `MANAGER.publish` or test | YES — `test_handshake_accepts_run_id` sends + receives all 8 wire types | FLOWING |

**Note:** `MANAGER.publish` has no production call site in Phase 6 — Phase 7's harness wires the producer per D-14/D-06. This is explicit in plan and roadmap; the wire is complete and unit-testable. Tests exercise both direct queue insertion and `MANAGER.publish` paths. NOT a gap.

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Full pytest suite green | `pytest -q` | `146 passed, 4 subtests passed in 11.39s` | PASS |
| Race subdirectory tests green | `pytest tests/race/ -v` | `37 passed in 0.42s` | PASS |
| Legacy v1 backwards-compat (D-03) | `pytest tests/test_demo_modes.py tests/test_web_ui.py tests/test_api_async.py -x` | All 100+ legacy tests pass (per Plan 03/05/07 SUMMARY logs) | PASS |
| Route registration | `grep -nE '@app.websocket\("/api/race/ws"\)' src/a2a_vs_mcp/web.py` | line 857 — registered on existing FastAPI app | PASS |
| All 8 wire literals importable | Plan 01 smoke test from SUMMARY | All 8 dataclasses + `WIRE_EVENT_TYPES` import | PASS |
| Path-traversal regex active | `tests/race/test_replay_stub.py::PathTraversalGuardTests` | 4 sub-tests covering `../../etc/passwd`, length cap, special chars, valid IDs | PASS |
| 5/IP cap enforces 4290 close | `tests/race/test_ws_lifecycle.py::FivePerIpCapTests::test_sixth_connection_from_same_ip_rejected` | 6th connection rejected with code=4290 | PASS |

All spot-checks PASS.

---

### Requirements Coverage

| Requirement | Source Plans | Description | Status | Evidence |
|-------------|--------------|-------------|--------|----------|
| TRC-01 | 06-02, 06-03, 06-05, 06-06, 06-08 | Per-LLM/tool/agent timing fields + queryable post-run by `(run_id, lane)` causal order | SATISFIED | Timing fields supported via `**payload` kwargs (`trace.py:63`); `(run_id, lane)` query via `events_for_lane(load_run(...), lane)`; verified by test_trace_schema.py (causal order, 25-event roundtrip, per-lane turn_index). |
| TRC-02 | 06-03, 06-05, 06-06, 06-08 | `trace_schema_version` on every event + stub no-op migrator | SATISFIED | `trace.py:54` stamps schema_version on every event; `replay.py:migrate_v1` identity for v1.0; v1.0 fixture round-trips through `load_run` (test_replay_stub.py). |
| TRC-03 | 06-04, 06-08 | `fault_injected` + `fault_observed` events with TRC-03 fields | SATISFIED (schema + persist path; runtime fault_observed emission deferred to Phase 7 per D-14) | All 4 fault_injected fields stamped via `inject_fault`; FaultObservedEvent dataclass declares all 7 fields and is constructible. IRON RULE atomicity verified including raise paths. |
| TRC-04 | 06-01, 06-02, 06-07, 06-08 | `/api/race/ws` 8 event types + per-lane turn_index | SATISFIED | Route at web.py:857 on existing app; 8 wire literals locked in WIRE_EVENT_TYPES; turn_index stamped per-lane per D-16 set-union; full lifecycle (handshake/cap/coalesce/heartbeat/reconnect) verified by test_ws_schema.py + test_ws_lifecycle.py. |

**Plan-claimed requirements vs ROADMAP traceability:**
- ROADMAP traceability table maps TRC-01..04 → Phase 6.
- Plans collectively claim TRC-01, TRC-02, TRC-03, TRC-04 across 8 plans.
- No orphaned requirements (no Phase-6-mapped requirements went unclaimed by any plan).
- No surplus requirements (no plan claims a requirement outside Phase 6's mapped TRC set).

**Coverage:** 4/4 SATISFIED.

---

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `race/failure.py` | Soft-mutation kinds (PARTIAL_JSON, SCHEMA_DRIFT, EVENTUAL_CONSISTENCY_READ) return original_response unchanged in Phase 6 | INFO | Documented stub: Phase 7 mock APIs flesh out the soft mutations. Not a runtime defect — `inject_fault` still records the fault_injected event correctly with the right kind. The 2 hard-failure kinds (rate_limit_429, partial_commit_5xx) DO raise as designed and are exercised by atomicity tests. Tracked in plan 06-04 SUMMARY decisions block. |
| `race/replay.py:migrate_v1` | Identity stub migrator (no real migration logic) | INFO | This IS the spec — TRC-02 explicitly asks for a stub no-op migrator. Real migration is TODO-04, deferred indefinitely. Not unintended placeholder code. |
| `MANAGER.publish` | No production call site in Phase 6 source | INFO | Documented Phase 7 boundary per D-14/D-06. Plan 06-07 must_haves explicitly states "MANAGER.publish is callable in Phase 6 but no production call site exists; Phase 7 race harness wires the producer". Tests exercise the path directly. Not a gap; this is the agreed wave structure. |

No BLOCKER or WARNING anti-patterns found. All TODOs/stubs are explicitly documented and bounded to deferred phases or roadmap TODOs.

---

### Human Verification Required

None. All Phase 6 deliverables are headless backend (trace schema, ndjson durability, websocket wire format) with no UI surfaces. The full lifecycle is exercised by automated tests (37 race tests + 109 pre-existing tests = 146 passing). UI verification will be needed in Phase 8 when the Race page lands.

---

### Gaps Summary

No gaps. The phase goal — landing the trace + websocket schema upgrades that unblock v2.0 — is achieved:

- All 4 ROADMAP success criteria are satisfied with code + tests.
- All 4 TRC requirements (TRC-01..04) are implemented and exercised.
- Backwards-compat invariant D-03 is intact: legacy v1 callers continue producing v1-shape events (plus the additive `trace_schema_version` field) and the entire pre-Phase-6 test suite remains green.
- Pre-design gate D-01..D-18 architectural decisions are all materialized in code:
  - D-01 ndjson per run, D-04 batch+forced flush, D-05 single-writer arbiter, D-06 ws lifecycle, D-07 disk-backed reconnect, D-08 coalesce semantics, D-09 asyncio.Queue pubsub, D-11 IRON RULE, D-12 FaultKind enum + Pydantic, D-13 CI grep, D-15/D-16/D-17 turn-index ownership, D-18 dual-mode TraceRecorder.
- Security threats (V12 path traversal, MEDIUM 5/IP cap, MEDIUM slowloris, LOW coalesce DoS) are mitigated AND tested.
- D-14 deferred work (runtime emission of `fault_observed` by recovery state machine) is explicit in plan 06-04 must_haves and ROADMAP Phase 7 success criteria — not a Phase 6 gap.

Phase 6 is ready to proceed to Phase 7.

---

_Verified: 2026-04-28_
_Verifier: Claude (gsd-verifier)_
