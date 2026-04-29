---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Race Demo + Discovery + Visualization
status: ready_to_plan
stopped_at: Phase 9 context gathered — 6 decisions (D-52..D-57); ready for /gsd-plan-phase 9
last_updated: "2026-04-29T16:52:00.000Z"
last_activity: 2026-04-29 22:22 — Phase 9 discuss-phase complete; CONTEXT.md + DISCUSSION-LOG.md written
progress:
  total_phases: 8
  completed_phases: 3
  total_plans: 26
  completed_plans: 26
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-28)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** Phase 09 — heatmap-replay-k3-calibration

## Current Position

Phase: 09 (heatmap-replay-k3-calibration) — READY TO PLAN (CONTEXT.md gathered, 0/4 plans)
Plan: 0 of TBD
Next action: `/gsd-plan-phase 9` — 6 decisions locked (D-52..D-57): GET /api/race/heatmap aggregate endpoint, minimal cell shape, in-memory cache invalidated on race_done, pinned (model=claude-sonnet-4-6, seed=42, 3 v1 task_ids) baseline filter, HEATMAP_BASELINE module constant in race/config.py, off-baseline runs silently excluded. Researcher picks: replay tag computation (HEAT-03), K=3 calibration fixture format (HEAT-04), two-layer fixture plugin, cache invalidation transport, HardnessFailureHeatmap vs HeatmapScaffold replacement strategy.
Status: Phase 08 complete; ready for Phase 09 planning. Wave breakdown: W1 08-01 (tokens/glossary/types), W2 08-02 (routes+shell+derivePageState), W3a 08-03+04a+05 (parallel: hooks/lane components/heatmap+scrubber), W3b 08-04b (status strip+banner+methodology), W4 08-06 (RacePage integration + 12 fixtures + a11y + responsive). UIRACE-01..07 all verified; D-44..D-51 all honored. 24 commits across waves. Deferred: heatmap data backend → P9, replay endpoint → P9, OG/mobile PNG → P10.
Last activity: 2026-04-29 21:41 — Phase 08 verified PASS

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
