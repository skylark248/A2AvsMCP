---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Race Demo + Discovery + Visualization
status: in_progress
stopped_at: Phase 9 Plan 02 complete — replay route GET /api/race/runs/{run_id}/trace mounted (HEAT-03); 09-03/09-04 still pending
last_updated: "2026-04-30T06:01:48.000Z"
last_activity: 2026-04-30 11:31 — Phase 9 Plan 02 complete (2 commits, 5 new tests, 281/281 pytest, 172/172 race regression)
progress:
  total_phases: 8
  completed_phases: 3
  total_plans: 30
  completed_plans: 28
  percent: 93
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-28)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** Phase 09 — heatmap-replay-k3-calibration

## Current Position

Phase: 09 (heatmap-replay-k3-calibration) — IN PROGRESS (2/4 plans complete)
Plan: 2 of 4 complete (09-01, 09-02 SHIPPED 2026-04-30); 09-03 / 09-04 pending
Next action: `/gsd-execute-phase 9` continues with Wave 1 remaining plan (09-03 replay symmetry + K=3 calibration tests) and Wave 2 (09-04 frontend heatmap wrapper, depends on 09-01 contract — now landed). 09-02 shipped: GET /api/race/runs/{run_id}/trace mounted in web.py at lines 869-887 (sync def, validate-then-load prologue mirroring race_ws); returns {run_id, events, schema_version: "1.0"} matching frontend RaceReplayPayload (client.ts:136-140); 400 on malformed run_id (path-traversal guard via _validate_run_id); 404 on missing file; events shipped verbatim (D-59 deferral); 5 new tests + 281/281 pytest green.
Status: Plan 09-02 complete with 2 atomic commits (RED 9dc03ec + GREEN 51ecc91). Zero deviations — plan executed exactly as written. Frontend `useRaceReplay` Phase-8 typed stub now satisfied by live backend; the existing hook is a drop-in consumer with no client changes needed.
Last activity: 2026-04-30 11:31 — Phase 09 Plan 02 complete

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

Last session: 2026-04-30T06:01:48.000Z
Stopped at: Phase 9 Plan 02 (replay route) complete — 09-03 / 09-04 pending
Resume file: .planning/phases/09-heatmap-replay-k3-calibration/09-02-SUMMARY.md
Next action: Spawn executor agents for Plan 09-03 (replay symmetry + K=3 calibration tests) and Plan 09-04 (HardnessFailureHeatmap.tsx wrapper). 09-03 is independent (uses load_run directly + existing fixtures); 09-04 depends only on 09-01's locked payload contract (already landed). Both can run in parallel.
