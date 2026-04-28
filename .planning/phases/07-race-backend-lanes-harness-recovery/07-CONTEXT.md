# Phase 7: Race Backend — Lanes, Harness, Recovery State Machine - Context

**Gathered:** 2026-04-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Stand up the three runner lanes, the harness that drives parallel runs, the locked recovery state machine, the three v1 tasks with mock APIs, and the deterministic per-lane headline classifier — all on top of the Phase 6 trace + ws schema gate.

In scope (RACE-01..07):
- `race/types.py` — `HardnessType` StrEnum (4 v1 values), `HardnessProfile` dataclass, `TaskSpec`, `RaceResult`, `ScoreCard`.
- `race/runners/{pure_mcp,pure_a2a,hybrid}.py` — fresh race-native runners (NOT subclasses of v1 BaseAgent).
- `race/harness.py` — drives N parallel runs per (lane, task); demo `n=5`, dev `n=1`; deterministic `model=claude-sonnet-4-6, seed=42, temperature=0, per_run_timeout_s=120`; emits live ws events; only retries transient infra errors (never injected faults).
- `race/classifier.py` — stateful `Detector(K=3)` per-fault state machine + `failure_mode_classifier(lane, task_id, per_run_tags, agg) → headline_sentence` (6 deterministic templates).
- `race/tasks/<id>/task_config.yaml` (3 tasks: `summarize_repo`, `negotiate_meeting`, `book_travel`) + per-task `__init__.py` registering `(target → callable)` and `(bind_key → callable)` tables.
- `race/mocks/{github,calendar,travel}.py` — single fault chokepoint; called from MCP server tool dispatch + A2A handler dispatch.
- `mcp_servers/race_{github,calendar,travel}.py` — three new MCP servers wrapping race/mocks; pure_mcp + hybrid lanes call them via real `MCPClient`.
- A2A fixture-backed agents registered via existing `A2ABroker` so pure_a2a + hybrid lanes exercise real broker traffic.
- Per-task scorers: Haiku-judge for `summarize_repo` + `book_travel`, structural for `negotiate_meeting`, composite for `book_travel` total.
- `fault_observed` emission live, runner-driven via classifier's `Detector`.
- Wasted-tokens computation server-side from authoritative trace at `fault_observed` time (master design §Cost computation).

Out of scope (deferred to later phases):
- UI for race page / heatmap / banner — Phases 8-9.
- Replay route `/race/<run_id>` deterministic test — Phase 9 (HEAT-03 two-layer fixture).
- K∈{2,3,4,5} sweep test — Phase 9 (HEAT-04).
- OG / heatmap PNG — Phase 10.
- Real plan-emitter hybrid — TODO 1 stays deferred (v1 hybrid is pre-scripted per task).
- Multi-seed benchmark — TODO 2 deferred.
- LLM-judge recovery (paraphrase-resilient) — TODO 10 deferred (regex with negation guard is v1).

</domain>

<decisions>
## Implementation Decisions

### Runner architecture
- **D-19:** **Fresh race runners**. New `race/runners/{pure_mcp,pure_a2a,hybrid}.py` files. v1 agents (`agents/single_agent.py`, `specialists.py`, `hybrid_specialists.py`, `triage.py`) are NOT subclassed and NOT touched. Race lanes are independent of v1 demo evolution; SupportTicket/AgentResult abstractions do not leak into race.
- **D-20:** Runner contract: `run(task_spec: TaskSpec, run_id: str, recorder: TraceRecorder, failure_script: list[FaultEntry]) → RaceResult`. Each runner constructs its own `TraceRecorder` via the Phase 6 `(run_id, lane)` constructor. The harness threads `run_id` in.
- **D-21:** Hybrid runner is the **pre-scripted plan executor** (v1 contract). It interprets `task_config.hybrid_plan.steps` linearly, branching on `on_fault` enum (`retry_once | delegate | abort | continue`). Agent-driven decision policy is v2+.

### Mock API delivery surface
- **D-22:** **Mocks live behind real MCP + A2A transport**. `race/mocks/{github,calendar,travel}.py` are pure Python adapter modules (single fault chokepoint via `inject_fault()`).
- **D-23:** Three new MCP servers `mcp_servers/race_{github,calendar,travel}.py` wrap the mocks, exposing tool calls. `pure_mcp` and `hybrid` lanes call them via the existing `MCPClient` from `src/a2a_vs_mcp/mcp/client.py`. **Reuse, do not duplicate, MCP transport.**
- **D-24:** A2A side: register fixture-backed agent handlers on the existing `A2ABroker` (`src/a2a_vs_mcp/a2a/broker.py`). `pure_a2a` and `hybrid` lanes route via real `broker.send_message`. **Reuse, do not duplicate, A2A transport.**
- **D-25:** `inject_fault()` (Phase 6, `race/failure.py`) is the **only** mutation point for mock responses. MCP servers + A2A handlers both call into the mock module, which calls `inject_fault()`. Single chokepoint = single IRON RULE enforcement point. CI grep from Phase 6 D-13 still applies.

### task_config.yaml location + bind/target semantics
- **D-26:** YAMLs live at `src/a2a_vs_mcp/race/tasks/<task_id>/task_config.yaml` — inside the package, importable via `pkg_resources` / `importlib.resources`. No path discovery, no out-of-package data dir for v1.
- **D-27:** Each task ships `src/a2a_vs_mcp/race/tasks/<task_id>/__init__.py` that registers two **callable registries**:
  - `TARGETS: dict[str, Callable]` — `failure_script[].target` strings (e.g., `"github_api.get_repo_metadata"`) → mock callables.
  - `BINDS: dict[str, Callable[[ExecutionContext], Any]]` — `hybrid_plan.steps[].bind` keys (e.g., `"from_subagent_output"`, `"lowest_cost_combo"`) → resolution functions reading the in-flight `ExecutionContext`.
- **D-28:** **Pydantic validators reject unknown `target` and `bind` identifiers at startup**, not at first run. Typo = startup `ValidationError`, not silent mid-run failure. Same pattern as Phase 6 D-12 (`FaultKind` validator).
- **D-29:** `failure_script[].kind` enum is the Phase 6 `FaultKind` (5 values, locked). `hybrid_plan.steps[].on_fault` enum locked at 4 values: `retry_once | delegate | abort | continue` (master design §task_config.yaml).
- **D-30:** Hardness coverage check (locked from master design): LONG_CHAIN ∈ {summarize_repo, book_travel}, RATE_PRESSURE ∈ {summarize_repo, book_travel}, SCHEMA_VARIANCE ∈ {summarize_repo, negotiate_meeting}, MULTI_SOURCE_SYNTHESIS ∈ {negotiate_meeting, book_travel}. All 4 v1 types appear in ≥2 tasks. Test verifies via `HardnessProfile` inspection.

### fault_observed emission ownership
- **D-31:** **`race/classifier.py` owns the K=3 detection algorithm; runners invoke it inline.** Classifier exposes `Detector(K: int = 3)` — stateful per-fault, accepts events as they happen, transitions states per the master design pseudocode (`WAITING → AWAITING_OBSERVATION → OBSERVED`), and reports when fault is OBSERVED.
- **D-32:** Each runner instantiates one `Detector` per `fault_injected` event it observes (faults are scripted, so runner sees them as the harness applies them). Runner feeds subsequent events (`tool_error`, `agent_msg`, `retry`) into all live detectors. When a detector flips to OBSERVED, runner calls `recorder.record('fault_observed', fault_id=..., turn_index=..., t_observed_ms=..., evidence_kind=...)`.
- **D-33:** **Replay symmetry guaranteed by construction**: replay re-instantiates the same `Detector` class over the recorded event stream from `data/runs/<run_id>.json`. Same algorithm = same tags, no rule drift. Verified in Phase 9 HEAT-03 two-layer fixture test.
- **D-34:** Recovery tag emission (final `tag(fault_id) := recovered | gave_up | kept_going_without_noticing | kept_going_to_failure | indeterminate`) happens at `done` event arrival via the classifier's terminal-state rules (master design §Per-fault state machine). `indeterminate` = `race_done` arrives with no `done` and detector still in `WAITING | AWAITING_OBSERVATION`.

### Recovery + headline classifier shape
- **D-35:** `failure_mode_classifier(lane, task_id, per_run_tags, agg) → str` lives in `race/classifier.py` alongside `Detector`. Same module = single concept (recovery analysis). 6 templates locked verbatim from master design §failure_mode_classifier — `recovered | gave_up | kept_going_without_noticing | kept_going_to_failure | indeterminate | lane_failed`.
- **D-36:** `agent_msg_acknowledging_fault` regex with negation guard locked verbatim from master design §Recovery detection. Compiled once at module load. Negation guard sentence-split by `[.!?]` or end-of-message. False-positive target <10% on `summarize_repo` traces (test asserts via fixture).
- **D-37:** `characteristic_event` lookup table per lane (master design §failure_mode_classifier):
  - `pure_mcp` → `"retried {tool_name} {median_retries} times"`
  - `pure_a2a` → `"delegated {median_delegations} times"`
  - `hybrid` → `"switched protocol path {median_switches} times"`
  Computed from trace counts; fallback to `"continued for {median_turns_after_fault} turns"` if counts absent.

### Harness concurrency + retry
- **D-38 (planner note):** Harness runs `(lane, task, run_idx)` tuples. With `n=5` × 3 lanes × 1 task = 15 concurrent Anthropic Sonnet calls — likely rate-limit risk. Research must surface concrete options: bounded `asyncio.Semaphore` (e.g., 5), full sequential, or `asyncio.gather` with retry-backoff. Planner picks based on Anthropic rate limits at `claude-sonnet-4-6`. Retry **only** on transient infra errors (HTTP 5xx, connection-reset); injected faults are NEVER retried.
- **D-39:** `race_done` event emitted by harness when all (lane, task) tuples complete or per-run `120s` timeout fires. Drives `indeterminate` detection in classifier.

### Wasted-tokens computation
- **D-40:** Computed server-side from `data/runs/<run_id>.json` at `fault_observed` time (master design §Cost computation, locked). Sum `tokens_in + tokens_out` across all LLM calls in the trace where `t_call_start_ms ∈ [t_inject_ms, t_observed_ms]` for the same lane. Lives in `race/metrics.py` (small helper, not a separate module unless research surfaces a reason).
- **D-41:** Emitted as a field on the `fault_observed` event payload for UI display — UI does not recompute. Event-stream coalescing (Phase 6 D-08) cannot drop this because `fault_observed` is in `NEVER_COALESCE`.

### Judge / scorer integration
- **D-42 (planner note):** Haiku judge for `summarize_repo` + `book_travel`. Reuse-vs-new is research's call: existing `reasoning.py` Anthropic client wired via model override is one option; new `race/judges/` module with prompt-cache strategy is another. Determinism MUST hold (`temperature=0, seed=42`). Planner picks. Composite for `book_travel` = structural (cost ≤ budget AND legs connect) AND Haiku (purpose match) — both must pass.
- **D-43:** `negotiate_meeting` is **structural-only** (proposed time within all 3 free windows AND respects hard constraints). No LLM judge.

### Claude's Discretion
- Layout of `race/runners/` package (single file per lane, or `runners/__init__.py` + per-lane modules) — research/planner picks.
- Where `ExecutionContext` (binding-resolution dict) is defined — could live in `race/runners/hybrid.py` or `race/types.py`. Whichever keeps imports clean.
- Whether `mcp_servers/race_*.py` files share a common base or are three independent modules.
- Exact mock fixture data — 5 GitHub repos, 3 calendars, travel search/booking — needs design but is not gray (master design §Tasks specifies shape; fixtures are content choices).
- Whether classifier `Detector` and `failure_mode_classifier` share a module-level state pool or are independent — implementation detail.

### Folded Todos
None. All Phase 7-adjacent TODOs (1, 2, 10) explicitly stay deferred.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project + milestone state
- `.planning/PROJECT.md` — v2.0 milestone scope, core value, key decisions table.
- `.planning/REQUIREMENTS.md` §RACE — RACE-01..07 verbatim (the locked requirement text Phase 7 implements).
- `.planning/ROADMAP.md` §Phase 7 — goal, dependencies (Phase 6), 5 success criteria.
- `.planning/STATE.md` — current milestone position; Phase 6 closed, Phase 7 next.

### Master design doc (authoritative for all of v2.0)
- `~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-design-20260427-193227.md` — 918-line approved master design. Sections directly relevant to Phase 7:
  - §Hardness vector — `HardnessType` StrEnum with 4 v1 values; `HardnessProfile` dataclass.
  - §Runners — pure_mcp / pure_a2a / hybrid contracts; hybrid v1 = pre-scripted plan.
  - §Harness — n=5/n=1, model=claude-sonnet-4-6, seed=42, temperature=0, per_run_timeout_s=120; retry only on infra errors.
  - §Recovery detection — full state machine pseudocode; `agent_msg_acknowledging_fault` regex with negation guard; K=3 turn window; tag enum.
  - §task_config.yaml — 3 verbatim YAMLs (summarize_repo, negotiate_meeting, book_travel) + closed `kind:` enum + `on_fault:` enum.
  - §failure_mode_classifier — 6 templates, characteristic_event phrases, fault_summary computation.
  - §Cost computation — wasted-tokens server-side rule.
  - §Tasks — judge/scorer per task (Haiku for summarize_repo + book_travel structural piece; structural for negotiate_meeting; composite for book_travel total).

### Test plan (eng-review iter 2 supplement)
- `~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-eng-review-test-plan-20260427-224635.md` — Phase 7 must satisfy: recovery state-machine fixtures, K=3 false-positive target test, hardness coverage assertion, harness deterministic-seed test, hybrid_plan executor on_fault branching tests.

### Phase 6 inheritance (read in full)
- `.planning/phases/06-tracerecorder-schema-gate-race-foundation/06-CONTEXT.md` — D-01..D-18 locked decisions.
- `.planning/phases/06-tracerecorder-schema-gate-race-foundation/06-VERIFICATION.md` — what Phase 6 actually shipped.
- `src/a2a_vs_mcp/race/{__init__,schemas,turn,failure,runs,replay,ws}.py` — Phase 6 modules; Phase 7 depends on all of them.
- `tests/race/` — 37 existing race tests (TRC-01..04). Phase 7 must not regress these.

### Codebase intel (read before research)
- `.planning/codebase/ARCHITECTURE.md` — current backend layout.
- `.planning/codebase/STRUCTURE.md` — directory map.
- `.planning/codebase/TESTING.md` — pytest layout + existing fixture patterns.
- `.planning/codebase/CONVENTIONS.md` — coding conventions to honor.
- `.planning/codebase/INTEGRATIONS.md` — MCP client + A2A broker integration patterns.

### Existing code that Phase 7 reuses verbatim (transport)
- `src/a2a_vs_mcp/mcp/client.py` — `MCPClient` used by pure_mcp + hybrid lanes against new `mcp_servers/race_*.py`. **Do not modify.**
- `src/a2a_vs_mcp/mcp_servers/db_server.py`, `docs_server.py` — reference shape for new race MCP servers.
- `src/a2a_vs_mcp/a2a/broker.py` — `A2ABroker.register` + `send_message` used by pure_a2a + hybrid lanes for fixture-backed agents. **Do not modify.**
- `src/a2a_vs_mcp/a2a/protocol.py` — A2A protocol constants; race agents use the same.
- `src/a2a_vs_mcp/trace.py` — Phase 6-extended TraceRecorder; race runners construct with `(mode, runtime, task_id, run_id, lane)` per D-18.
- `src/a2a_vs_mcp/race/failure.py` (Phase 6) — `inject_fault()` IRON RULE; race mocks call into this exclusively.
- `src/a2a_vs_mcp/race/turn.py` (Phase 6) — `TURN_DEFINING_EVENTS`; classifier `Detector` consults this.

### Existing code that Phase 7 deliberately does NOT touch
- `src/a2a_vs_mcp/agents/{single_agent,specialists,hybrid_specialists,triage}.py` — v1 demo agents. Race uses **fresh** runners (D-19).
- `src/a2a_vs_mcp/schemas.py` — v1 `FailureConfig` + `SupportTicket` schemas. Untouched.
- `src/a2a_vs_mcp/reasoning.py`, `persistence.py`, `reporting.py` — v1 demo code paths.

### Deferred-context backlog
- `TODOS.md` §TODO 1 — real plan-emitter hybrid (v1 is pre-scripted, this is v2+).
- `TODOS.md` §TODO 2 — multi-seed benchmark (Phase 7 ships seed=42 only).
- `TODOS.md` §TODO 4 — production trace migrator (still deferred; Phase 6 stub still suffices).
- `TODOS.md` §TODO 10 — paraphrase-resilient recovery detection (regex+negation is v1).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets (transport reuse, agent code NOT reused)
- **MCP transport** (`mcp/client.py`, `mcp_servers/db_server.py` shape): proven pattern. Race adds `mcp_servers/race_{github,calendar,travel}.py` mirroring `db_server.py` shape; lanes call via `MCPClient`.
- **A2A broker** (`a2a/broker.py`): `register(card, handler)` + `send_message` proven. Race registers fixture-backed agents on a per-(run_id, lane) broker instance.
- **Phase 6 `inject_fault()`** (`race/failure.py`): IRON RULE chokepoint. Race mocks call this; nothing else mutates mock responses.
- **Phase 6 `TURN_DEFINING_EVENTS`** (`race/turn.py`): classifier `Detector` reads to count turns since `fault_injected`.
- **Phase 6 ndjson dispatcher** (`race/runs.py` RunWriter): all 3 lanes append via the threading.Lock arbiter (D-05). No new writer.

### Established Patterns
- **Per-task module with `__init__.py`-registered tables** mirrors `config.py:default_profile_name()` profile-registry pattern (Phase 6 noted this in D-12 vicinity).
- **Pydantic validator at startup** for unknown identifiers — Phase 6 D-12 (`FaultKind` validator) sets the pattern; Phase 7 D-28 reuses for `target` + `bind`.
- **MCP server module shape** — `mcp_servers/db_server.py` and `docs_server.py` are the shape templates. Each new race server follows the same `tools = [...]` + `dispatch(name, args)` shape.
- **Dataclass-first schemas** with `to_dict()` (per Phase 6 `<code_context>`). Race types follow.

### Integration Points
- `serve_ui.py` mount: harness needs to be invokable from a route eventually (Phase 8 wires the actual `POST /api/race/start`); Phase 7 ships harness as a Python-callable + CLI entry. Confirm no new mount needed.
- `data/runs/<run_id>.json` — Phase 6 ndjson path; harness mints `run_id` and threads to all 3 recorders (D-02 from Phase 6). Phase 7 finalizes the call site.
- `data/race/fixtures/` (new): mock fixture data — 5 GitHub repos, 3 calendars, travel inventory. Lives outside `src/` because it's data, not code.

</code_context>

<specifics>
## Specific Ideas

- **Real-shaped transport is a v2.0 design commitment, not an aesthetic choice.** Pure_MCP must demonstrate "real MCP" — that means MCPClient → MCP server → mock. Pure_A2A must demonstrate "real A2A" — that means broker.send_message → registered handler → mock. Anything less weakens the comparison.
- **Single fault chokepoint at the mock layer** (D-25) means `inject_fault()` is called from exactly one place per task target. CI grep from Phase 6 D-13 still applies and now extends to `mcp_servers/race_*.py` and the A2A handlers.
- **Replay symmetry is non-negotiable** (D-33). The classifier `Detector` class is the single source of truth for K=3 detection — used live in runners AND in replay over recorded events. Phase 9 HEAT-03 fixture test asserts identical tags.
- **Hybrid runner v1 = pre-scripted plan executor.** Do not let "real plan-emitter" sneak in via TODO 1. The hybrid_plan.steps interpreter is the v1 contract; agent-driven planning is v2+.
- **`negotiate_meeting` has no LLM judge** (D-43). Pure structural check. Don't let composite-judge logic drift onto it.
- **Wasted-tokens NEVER coalesces** (D-41). Even under backpressure, `fault_observed` and its payload pass through.

</specifics>

<deferred>
## Deferred Ideas

- **Real plan-emitter hybrid** — TODO 1. Promote when leaderboard 10x scopes agent-driven hybrid policy.
- **Multi-seed benchmark** — TODO 2. v1 ships seed=42 only.
- **Paraphrase-resilient recovery (LLM-judge)** — TODO 10. Regex + negation guard is v1.
- **Cross-run aggregate analytics beyond per-(lane, task) headline** — heatmap aggregation is Phase 9 scope.
- **Real (non-stub) trace migrator** — TODO 4 stays deferred from Phase 6.
- **Per-tool retry budget config** — v1 hybrid_plan.on_fault.retry_once is exactly one retry; configurable budget is v2+.
- **AST-based lint plugin for inject_fault IRON RULE** — module docstring + CI grep is sufficient.

### Reviewed Todos (not folded)
None. TODOS.md entries adjacent to Phase 7 (1, 2, 10) explicitly remain deferred per master design v1 contract.

</deferred>

---

*Phase: 7-Race Backend — Lanes, Harness, Recovery State Machine*
*Context gathered: 2026-04-28*
