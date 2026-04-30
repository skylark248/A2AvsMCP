---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Race Demo + Discovery + Visualization
status: in_progress
stopped_at: Phase 9 Plan 03 complete — HEAT-03 replay symmetry + HEAT-04 K-calibration sweep landed; 09-04 (frontend wrapper) remains
last_updated: "2026-04-30T06:10:41Z"
last_activity: 2026-04-30 11:40 — Phase 9 Plan 03 complete (2 commits, 45 new tests, 326/326 pytest)
progress:
  total_phases: 8
  completed_phases: 3
  total_plans: 30
  completed_plans: 29
  percent: 96
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-28)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** Phase 09 — heatmap-replay-k3-calibration

## Current Position

Phase: 09 (heatmap-replay-k3-calibration) — IN PROGRESS (3/4 plans complete)
Plan: 3 of 4 complete (09-01, 09-02, 09-03 SHIPPED 2026-04-30); 09-04 (frontend wrapper) remains
Next action: `/gsd-execute-phase 9` continues with Wave 2 (09-04 HardnessFailureHeatmap.tsx wrapper + useRaceHeatmap hook + fetchRaceHeatmap client + RacePage wiring). 09-04 depends on 09-01's heatmap payload contract (already landed). 09-03 shipped: tests/race/_replay_helpers.py (single-source-of-truth replay_with_k(events, K, score_pass) reusing production Detector class verbatim per D-33); tests/conftest.py registers --update-snapshots flag (hand-rolled snapshot, no external deps); tests/race/test_replay_symmetry.py (HEAT-03 two-layer fixture sweep, 18 cases); tests/test_recovery_calibration.py at the ROADMAP-named path (HEAT-04 K=3 lock + K∈{2,4,5} drift sweep, 27 cases). Authored 9 near-K3-boundary fixtures (3 per task at evidence distances {3,4,5}) per RESEARCH LANDMINE 9 — without these the K-drift assertion has no positive evidence; expected_terminal_tag computed via replay_with_k(K=3) per T-09-11 mitigation, never hand-authored.
Status: Plan 09-03 complete with 2 atomic commits (98b861e helper+flag, a048cc5 tests+fixtures). 3 auto-fixed deviations: (Rule 1) helper missed race_done-without-done finalization branch — fixed to call finalize_at_race_done_no_done(); (Rule 3) missing tests/__init__.py blocked imports — created package marker; (Rule 3) preexisting test_all_nine_fixtures_present asserted exactly 9 fixtures — scoped to non-boundary glob to preserve §The Assignment count assertion. Full pytest 326/326 green (281 prior + 45 new). --update-snapshots smoke confirmed zero expected_terminal_tag value drift — D-33 symmetry-by-construction verified end-to-end.
Last activity: 2026-04-30 11:40 — Phase 09 Plan 03 complete

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

Last session: 2026-04-30T06:10:41Z
Stopped at: Phase 9 Plan 03 (replay symmetry + K=3 calibration) complete — 09-04 (frontend wrapper) pending
Resume file: .planning/phases/09-heatmap-replay-k3-calibration/09-03-SUMMARY.md
Next action: Spawn executor agent for Plan 09-04 (HardnessFailureHeatmap.tsx wrapper + useRaceHeatmap hook + fetchRaceHeatmap client + RacePage wiring). 09-04 is the only remaining plan; depends on 09-01's locked heatmap payload contract (already landed). After 09-04 lands, Phase 9 closes — proceed to /gsd-verify-phase 9.
