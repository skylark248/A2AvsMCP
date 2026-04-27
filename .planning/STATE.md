---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: "Race Demo + Discovery + Visualization"
status: planning
last_updated: "2026-04-28T00:00:00Z"
last_activity: "2026-04-28 -- Roadmap created (Phases 6-13)"
progress:
  total_phases: 8
  completed_phases: 0
  total_plans: 25
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-28)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** Awaiting Phase 6 kickoff (TraceRecorder Schema Gate & Race Foundation)

## Current Position

Phase: Not started — Phase 6 next (TraceRecorder Schema Gate & Race Foundation)
Plan: —
Status: Roadmap locked; ready for `/gsd-discuss-phase 6`
Last activity: 2026-04-28 — Roadmap created, 31/31 v2.0 requirements mapped across Phases 6-13

## Accumulated Context

### Decisions

Decisions logged in PROJECT.md Key Decisions table. v1.0 per-plan decision history retained in `.planning/milestones/v1.0-phases/*/`.

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

None — roadmap locked, ready for phase planning.

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

Last session: 2026-04-28
Stopped at: Roadmap created — 8 phases (6-13), 31/31 requirements mapped, ~25 plans estimated
Next action: `/gsd-discuss-phase 6` to begin TraceRecorder Schema Gate & Race Foundation
