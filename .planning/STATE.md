---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Race Demo + Discovery + Visualization
status: in_progress
stopped_at: Phase 9 ALL PLANS COMPLETE (09-01..09-04) — ready for /gsd-verify-phase 9
last_updated: "2026-04-30T06:20:22Z"
last_activity: 2026-04-30 11:50 — Phase 9 Plan 04 complete (4 commits, 13 new frontend tests, 280/280 vitest, 326/326 pytest)
progress:
  total_phases: 8
  completed_phases: 3
  total_plans: 30
  completed_plans: 30
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-28)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** Phase 09 — heatmap-replay-k3-calibration

## Current Position

Phase: 09 (heatmap-replay-k3-calibration) — ALL PLANS COMPLETE (4/4)
Plan: 4 of 4 complete (09-01, 09-02, 09-03, 09-04 SHIPPED 2026-04-30)
Next action: `/gsd-verify-phase 9` — all 4 ROADMAP success criteria are now testable in CI. After PASS verdict, advance to Phase 10 (OG Image & Sharing) which is unblocked: heatmap card now renders populated cells under `/race/<run_id>?og=1` mode for Playwright PNG capture.
Status: Plan 09-04 complete with 4 atomic commits (1a77308 RED hook, 2ea9f4d GREEN hook+types+client, cfa20e3 RED component, 864fa2d GREEN component+RacePage wiring). 2 auto-fixed deviations: (Rule 1) hook initial loading state had to be true (not false) for synchronous test assertion to pass before useEffect flushes — one-line fix; (Rule 1) component test getByText('Recovered') matched both legend chip + sr-only label inside populated cell (UIRACE-04 channel 4) — switched to getAllByText >= 1 for the two collision-prone tags. HEAT-01 + HEAT-02 satisfied: HardnessFailureHeatmap renders rows × cols via HeatmapScaffold with directional pill in MUI secondary, 5-pill always-visible legend strip, and data-driven model · seed · task_ids footer. LANDMINE 1 (backend "multi_source" → frontend "multi_source_synthesis") resolved at the wrapper transform boundary via HARDNESS_BACKEND_TO_FRONTEND closed Record. D-46 (HeatmapScaffold rendering primitive) and D-47 (empty-state never-unmount) preserved. Frontend suite 280/280 (+13), backend pytest 326/326 (no regression).
Last activity: 2026-04-30 11:50 — Phase 09 Plan 04 complete; Phase 9 fully shipped

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

Last session: 2026-04-30T06:20:22Z
Stopped at: Phase 9 ALL PLANS COMPLETE (09-01..09-04) — ready for /gsd-verify-phase 9
Resume file: .planning/phases/09-heatmap-replay-k3-calibration/09-04-SUMMARY.md
Next action: Run `/gsd-verify-phase 9` to validate the 4 ROADMAP success criteria against shipped code (heatmap visual contract, 5-pill legend + footer, replay-symmetric tags, K=3 calibration sweep). After PASS, advance to Phase 10 (OG Image & Sharing) which now has populated heatmap cells available for Playwright PNG capture.
