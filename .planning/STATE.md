---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: "Race Demo + Discovery + Visualization"
status: in_progress
last_updated: "2026-04-29T03:01:00+05:30"
last_activity: "2026-04-29 -- Phase 7 Plan 09 (Wave 4) shipped: 3 race lane runners (pure_mcp + pure_a2a + hybrid) each consuming task_config.yaml and returning a RaceResult of identical shape; Detector(K=3) instantiated inline per fault_injected event in all 3 runners (D-32 + D-33 replay-symmetric); fault_observed events emitted with compute_wasted_tokens (D-40); D-21 IRON RULE enforced via grep gate (no LLM call in hybrid v1); D-24 send_task method (NOT send_message); 4 atomic commits including 1 follow-up Rule-1 fix for FastMCP ToolError unwrap + A2A worker-thread ContextVar re-arm; 146 pre-existing tests still green"
progress:
  total_phases: 8
  completed_phases: 1
  total_plans: 41
  completed_plans: 17
  percent: 41
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-28)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** Phase 7 (Race Backend — Lanes, Harness, Recovery State Machine) — in progress, Wave 3 complete (8/11 plans)

## Current Position

Phase: 7 — Race Backend — Lanes, Harness, Recovery State Machine — IN PROGRESS (9/11 plans)
Next: Wave 5/6 — Plan 10 (harness Semaphore(8) parallel scheduler + Haiku judge integration), Plan 11 (chokepoint tests + integration)
Status: Waves 0-3 complete + Wave 4 fully shipped (3 race lane runners). New (07-09): race/runners/{__init__,pure_mcp,pure_a2a,hybrid}.py — module-level async coroutines with locked RESEARCH §4 signature. Detector(K=3) wiring inline per fault_injected event in all 3 runners (replay-symmetric with classifier.py by construction). pure_mcp uses real MCPClient(transport='in_process'); pure_a2a uses real A2ABroker.send_task (D-24 confirmed at broker.py:61, NOT send_message). hybrid is pre-scripted plan executor (D-21 IRON RULE — no LLM call) with full D-29 on_fault enum dispatch (retry_once/delegate/abort/continue). FixtureBackedAgentHandler routes A2A handlers through race.mocks chokepoint (T-07-09-04 mitigation). Two Rule-1 deviations auto-fixed: (1) FastMCP wraps InjectedFaultError as ToolError — runner now catches Exception when fault armed for target; (2) A2ABroker uses stdlib ThreadPoolExecutor which doesn't propagate ContextVars — handler captures armed_faults at registration and re-arms in worker thread.
Last activity: 2026-04-29 03:01 — Plan 07-09 shipped 4 atomic commits (734455c, 3644805, f09a135, 7cc4be2); 146 pre-existing tests still green; all 9 (lane × task) clean-runs return well-formed RaceResults; all 3 runners produce fault_injected + fault_observed pairs when faults armed

## Accumulated Context

### Decisions

Decisions logged in PROJECT.md Key Decisions table. v1.0 per-plan decision history retained in `.planning/milestones/v1.0-phases/*/`.

Phase 7 implementation decisions (D-19..D-43) locked in `07-CONTEXT.md`. Notable:
- D-19: Fresh race runners; v1 agents NOT subclassed/touched.
- D-22..D-25: Real MCP + A2A transport reused; mocks chokepointed in `race/mocks/`; `inject_fault()` is single mutation point.
- D-26..D-30: task_config.yaml inside `src/.../race/tasks/<id>/`; per-task callable registries (TARGETS + BINDS); Pydantic startup validation.
- D-31..D-34: Classifier owns `Detector(K=3)`; runners invoke inline; replay-symmetric by construction.
- D-38, D-42: harness concurrency + Haiku judge integration deferred to research/planner.

Carried into v2.0:
- Race Demo design: 2-lane Pure-MCP vs Pure-A2A + Hybrid restored to v1 scope (CEO+eng+design-cleared, iter 3, 8.5/10)
- Recovery state machine K=3 confirmed; multi-task calibration (TODO 8) promoted into v2 scope (lands in Phase 9)
- OG image generation via Playwright headless (TODO 3) promoted into v2 scope (Phase 10)
- DESIGN.md lock via /design-consultation (TODO 5) promoted into v2 scope (Phase 13, late by design — benefits from race-demo rules already shipped)
- SDK migrations (SDK-01/02) deferred to v2.1+ — too risky alongside Race Demo

Roadmap-shaping decisions (2026-04-28):
- Phase 6 opens v2.0 because the design doc's PRE-DESIGN GATE (TraceRecorder fault-injection schema audit) blocks all downstream race work. Front-loaded by design.
- Hybrid runner (highest-risk seam per design doc) lives in Phase 7 alongside the recovery state machine — risk consolidated, not spread across phases.
- DISC (Phase 11) and VIZ (Phase 12) sit after race demo lands; both depend only on the Phase 6 trace schema, so could parallelize with later race phases if scheduling allows.
- DSGN-01 (Phase 13) deliberately last — `/design-consultation` is interactive and benefits from having race-demo design rules (failureTagColor, methodology-as-flat, secondary-as-replay-pill) already concrete in code.

Phase 6 implementation decisions (D-01..D-18) locked in `06-CONTEXT.md`. Notable:
- D-03: TraceRecorder additive extension preserves v1 backwards-compat (all legacy tests stay green).
- D-05: threading.Lock (not asyncio.Lock) for RunWriter single-writer arbiter.
- D-08 + D-16: NEVER_COALESCE has exactly 7 members; only TickEvent eligible for coalescing.
- D-11/D-13: IRON RULE atomicity — record fault_injected BEFORE mutation, even on raise paths.
- D-14: `fault_observed` runtime emission deferred to Phase 7 (recovery state machine owns emission); Phase 6 ships schema + persistence path only.

### Pending Todos

7 deferred items in `TODOS.md` (project root) post-v2-promotion:
- TODO 1 (real plan-emitter hybrid)
- TODO 2 (multi-seed benchmark)
- TODO 4 (trace schema migrator)
- TODO 6 (display typeface)
- TODO 7 (heatmap rows from enum)
- TODO 9 (HMAC PNG URLs)
- TODO 10 (LLM-judge recovery)

### Blockers/Concerns

None — Phase 7 context gathered; ready to plan.

## Deferred Items (carried from v1.0)

Items acknowledged at v1.0 close that remain deferred into v2.0+:

| Category | Item | Status | Source |
|----------|------|--------|--------|
| Verification | Phase 5 missing VERIFICATION.md | Wired per integration check; bookkeeping gap | v1.0 audit |
| Verification | Phase 4 — 3 visual verification items | Code-level verified; visual checks deferred to demo-day rehearsal | v1.0 audit |
| SDK | SDK-01: A2A SDK 1.0.0 migration | v2.1+ backlog | Init |
| SDK | SDK-02: MCP SDK v2 migration (`FastMCP` → `McpServer`) | v2.1+ backlog | Init |
| Plan Review | TODOs 1, 2, 4, 6, 7, 9, 10 in TODOS.md | v2.1+ candidates per promote conditions | Plan reviews |

## Session Continuity

Last session: 2026-04-29
Stopped at: Phase 7 Plan 09 complete — Wave 4 fully shipped (3 race lane runners with end-to-end Detector wiring)
Resume file: .planning/phases/07-race-backend-lanes-harness-recovery/07-09-SUMMARY.md
Next action: Execute Wave 5/6 — Plan 07-10 (harness Semaphore(8) parallel scheduler + Haiku judge integration), Plan 07-11 (chokepoint + integration tests)
