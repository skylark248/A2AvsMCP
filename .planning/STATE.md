---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: "Race Demo + Discovery + Visualization"
status: in_progress
last_updated: "2026-04-29T03:10:00+05:30"
last_activity: "2026-04-29 -- Phase 7 Plan 10 (Wave 5) shipped: race/harness.py — concurrency harness with asyncio.Semaphore(8) cap (env override RACE_HARNESS_CONCURRENCY), closed-tuple TRANSIENT_RETRY_TYPES (only 4 anthropic transient types; InjectedFaultError NEVER caught — IRON RULE enforced), 120s per-run asyncio.wait_for, race_done event emission per D-39 with t_end_ms + total_runs + lane_failed_reasons + 6-template per-(lane,task) headlines from failure_mode_classifier (RACE-06 closed); CLI dry-run path runs end-to-end against mock chokepoint, no Anthropic key required; 4 atomic commits (ad5cd77, e9878ef, 9fba337, f914fd9); 146 pre-existing tests still green"
progress:
  total_phases: 8
  completed_phases: 1
  total_plans: 41
  completed_plans: 18
  percent: 44
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-28)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** Phase 7 (Race Backend — Lanes, Harness, Recovery State Machine) — in progress, Wave 5 complete (10/11 plans)

## Current Position

Phase: 7 — Race Backend — Lanes, Harness, Recovery State Machine — IN PROGRESS (10/11 plans)
Next: Wave 6 — Plan 11 (chokepoint tests + integration: test_harness.py, test_iron_rule_grep.py, test_mocks_chokepoint.py, integration suite)
Status: Waves 0-3 + Wave 4 (lane runners) + Wave 5 (harness) all shipped. New (07-10): race/harness.py — async run_race fan-out across (lane × task × run_idx) tuples under shared module-level asyncio.Semaphore(8) (env override RACE_HARNESS_CONCURRENCY); closed-tuple TRANSIENT_RETRY_TYPES = (anthropic.APIConnectionError, APITimeoutError, InternalServerError, RateLimitError) — InjectedFaultError DELIBERATELY absent so injected faults bubble through retry classifier untouched (IRON RULE); 3-attempt exponential backoff (2**attempt + uniform(0,1)); per-run asyncio.wait_for(120s) — TimeoutError -> ScoreCard(failure_mode='lane_failed', lane_failed_reason='timeout'); transient exhaustion -> lane_failed_reason=type(exc).__name__; race_done event emitted exactly once per run_race call carrying t_end_ms + total_runs + lane_failed_reasons + headlines (tuple keys flattened to 'lane|task_id' for JSON compat); per (lane, task) cell aggregate_for_classifier (Plan 05) -> failure_mode_classifier (Plan 04) -> 6-template headline sentence (RACE-06 closed); fault_observed forwarded by recorders unfiltered (D-41 + Phase 6 D-08 NEVER_COALESCE preserved end-to-end); CLI smoke-test entry point (--dry-run path runs full fan-out against mock chokepoint, no Anthropic key needed). Two Rule-1 deviations auto-fixed during execution: (1) `^MODEL = ` grep gate required removing PEP 526 type annotation from module constants; (2) inline-comment `InjectedFaultError` references survived `grep -v '^#'` filter — moved to full-line comments using "the injected-fault exception type" rephrasing.
Last activity: 2026-04-29 03:10 — Plan 07-10 shipped 4 atomic commits (ad5cd77, e9878ef, 9fba337, f914fd9); 146 pre-existing tests still green; CLI `python -m a2a_vs_mcp.race.harness --task summarize_repo --lane pure_mcp --n 1 --dry-run` exits 0 and emits race_done + headline lines

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
