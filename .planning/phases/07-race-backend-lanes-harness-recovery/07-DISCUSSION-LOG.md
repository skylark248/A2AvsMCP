# Phase 7 Discussion Log

**Date:** 2026-04-28
**Phase:** 7 — Race Backend — Lanes, Harness, Recovery State Machine
**Mode:** default (single-question turns)

## Gray Areas Selected

User selected all 4 presented:
1. Runner architecture
2. Mock API delivery surface
3. task_config + bind semantics
4. fault_observed emission ownership

Master design already locked: HardnessType enum (4 values), failure_script.kind enum (5 values), hybrid_plan.on_fault enum (4 values), recovery state-machine pseudocode, agent_msg_acknowledging_fault regex with negation guard, K=3, task_config.yaml verbatim (3 tasks), 6 headline templates, scorers per task, harness defaults. Not re-asked.

---

## Q1: Runner architecture

**Question:** How should race runners (pure_mcp / pure_a2a / hybrid) relate to the v1 agent stack?

**Options presented:**
- Reuse + adapter shim — subclass v1 BaseAgent / A2ABroker / MCPEnabledMixin; add TaskAdapter mapping.
- Fresh race runners — new `race/runners/{pure_mcp,pure_a2a,hybrid}.py` with race-native interfaces; v1 agents untouched.
- Hybrid: shared transport, fresh agent bodies — reuse `a2a/broker.py` + `mcp/client.py` + `mcp_servers/`; new race agent classes use these transports.

**User selection:** Fresh race runners.

**Decision:** D-19. v1 agents NOT subclassed, NOT touched. Race lanes independent of v1 demo evolution. SupportTicket/AgentResult abstractions do not leak into race.

**Follow-on D-20, D-21:** Runner contract `run(task_spec, run_id, recorder, failure_script) → RaceResult`. Hybrid runner is pre-scripted plan executor (v1 contract; agent-driven is v2+).

---

## Q2: Mock API delivery surface

**Question:** How do runners reach the mock APIs?

**Options presented:**
- Through real MCP + A2A transport — 3 new MCP servers + A2A fixture-backed agents; inject_fault wraps server tool dispatch.
- Direct Python mock adapters — `race/mocks/*.py` called directly; trace events recorded manually.
- Hybrid: real MCP, A2A via broker; mocks behind both — mocks at chokepoint, MCP servers + A2A handlers both call the mock layer.

**User selection:** Hybrid: real MCP, A2A via broker; mocks behind both.

**Decision:** D-22, D-23, D-24, D-25. `race/mocks/{github,calendar,travel}.py` are the single fault chokepoint. `mcp_servers/race_{github,calendar,travel}.py` wrap mocks for MCPClient. A2A fixture-backed agents register on existing `A2ABroker`. `inject_fault()` is the only mutation point for mock responses.

**Follow-on:** Reconciles with Q1 — fresh agent bodies but transport is reused verbatim. No duplication of MCP client / A2A broker.

---

## Q3: task_config.yaml location + bind semantics

**Question:** Where do task_config.yaml files live, and how are 'target' / 'bind' identifiers resolved?

**Options presented:**
- `src/.../race/tasks/<id>/task_config.yaml` + per-task callable registry — strict, validated at startup.
- `tasks/<id>/task_config.yaml` at repo root + reflective context lookup — discoverable, runtime-typo-prone.
- `data/race/tasks/<id>/task_config.yaml` + hybrid registry+context — strict targets, flexible binds.

**User selection:** `src/.../race/tasks/<id>/task_config.yaml` + per-task callable registry.

**Decision:** D-26, D-27, D-28, D-29, D-30. YAMLs ship inside the package via `importlib.resources`. Per-task `__init__.py` registers `TARGETS` + `BINDS` callable tables. Pydantic validator rejects unknown identifiers at startup (typo = startup ValidationError). `kind` enum and `on_fault` enum locked.

---

## Q4: fault_observed emission ownership

**Question:** Who emits the fault_observed event into the trace?

**Options presented:**
- Runner emits live — runner runs per-fault watcher; classifier is pure post-hoc tagging.
- Classifier owns detection + emission, post-hoc — runners emit raw events only; classifier reads at race_done.
- Classifier owns logic, runners invoke it inline (Recommended) — `Detector(K=3)` class owned by classifier, instantiated per fault by runners, fed events live, emits fault_observed when OBSERVED.

**User selection:** Classifier owns logic, runners invoke it inline.

**Decision:** D-31, D-32, D-33, D-34. `race/classifier.py` exposes stateful `Detector(K)`. Runners instantiate per `fault_injected`, feed live events, call `recorder.record('fault_observed', ...)` on transition. Replay re-runs same `Detector` over recorded events — symmetric by construction. Phase 9 HEAT-03 verifies.

---

## Claude's Discretion (deferred to research/planner)

- D-38 harness concurrency model (asyncio.gather vs bounded semaphore vs sequential) — Anthropic rate-limit constraints inform choice.
- D-42 Haiku judge integration (reuse `reasoning.py` client vs new `race/judges/`).
- Layout of `race/runners/` package, ExecutionContext location, `mcp_servers/race_*.py` shared base or independent.
- Mock fixture content (5 GitHub repos, 3 calendars, travel inventory).

## Deferred Ideas

Captured in CONTEXT.md `<deferred>`. No new scope-creep deferrals from this session.

## Folded / Reviewed Todos

None. TODOs 1, 2, 4, 10 explicitly remain deferred per master design v1 contract.
