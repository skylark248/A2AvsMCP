---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Race Demo + Discovery + Visualization
status: ready_to_execute
stopped_at: Phase 9 planned — 4 plans across 2 waves (D-52..D-60); ready for /gsd-execute-phase 9
last_updated: "2026-04-29T17:25:00.000Z"
last_activity: 2026-04-29 23:14 — Phase 9 plan-phase complete; 4 PLAN.md files + RESEARCH.md + PATTERNS.md written
progress:
  total_phases: 8
  completed_phases: 3
  total_plans: 30
  completed_plans: 26
  percent: 87
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-28)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** Phase 09 — heatmap-replay-k3-calibration

## Current Position

Phase: 09 (heatmap-replay-k3-calibration) — READY TO EXECUTE (4 plans, 2 waves)
Plan: 0 of 4
Next action: `/gsd-execute-phase 9` — 9 decisions locked (D-52..D-60). Wave 1 (parallel): 09-01 heatmap backend (HEATMAP_BASELINE constant + race/heatmap.py aggregator + cache invalidator + GET /api/race/heatmap + harness run_meta emit) [HEAT-01, HEAT-02], 09-02 replay route GET /api/race/runs/{run_id}/trace [HEAT-03], 09-03 pytest --update-snapshots + replay symmetry fixture + K∈{2,3,4,5} calibration sweep [HEAT-03, HEAT-04]. Wave 2: 09-04 HardnessFailureHeatmap.tsx data-wired wrapper + useRaceHeatmap + fetchRaceHeatmap + RacePage wiring [HEAT-01, HEAT-02]. New decisions added during plan-phase: D-58 run_meta event (first event of every run), D-59 defer event_type/type normalization to later phase, D-60 skip /gsd-ui-phase 9 (Phase 8 UI-SPEC + ROADMAP cover heatmap visual contract). Note: 09-01 + 09-02 both append routes to web.py — non-conflicting, executor handles via worktree merge per Phase 8 pattern.
Status: Phase 09 plan-phase complete (research + pattern map + 4 plans + manual verify). Plan-checker subagent hit quota wall; manual fallback per workflow Step 11a confirmed all checker focus areas (D-58 run_meta first event, no-LLM replay test, --update-snapshots hand-rolled, multi_source→multi_source_synthesis transform). Coverage gates: 4/4 REQs (HEAT-01..04), 9/9 decisions (D-52..D-60).
Last activity: 2026-04-29 23:14 — Phase 09 plan-phase complete

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

Last session: 2026-04-29T06:21:06.559Z
Stopped at: Phase 8 UI-SPEC approved
Resume file: .planning/phases/08-race-page-ui-visual-contract/08-UI-SPEC.md
Next action: Execute Wave 5/6 — Plan 07-10 (harness Semaphore(8) parallel scheduler + Haiku judge integration), Plan 07-11 (chokepoint + integration tests)
