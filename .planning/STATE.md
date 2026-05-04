---
gsd_state_version: 1.0
milestone: null
milestone_name: "v2.0 closed — awaiting next milestone"
status: "v2.0 milestone shipped 2026-05-04. All 31 requirements complete. Run /gsd-new-milestone to start v2.1."
stopped_at: "v2.0 milestone close — archived 2026-05-05"
last_updated: "2026-05-05T01:00:00+05:30"
last_activity: "2026-05-05 01:00 — v2.0 milestone archived (11 phases, 52 plans, 261 commits, +63,141 LOC)"
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-05-04)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** Planning next milestone (v2.1) — see `TODOS.md` for top backlog candidates (SDK-01/02, TODO 1/2/4/6/7/9/10).

## Current Position

v2.0 shipped 2026-05-04. All v2.0 phases (6-16) complete with SUMMARY + VERIFICATION artifacts. Backend 352/352 pytest, frontend 335/335 vitest. Three-Lane Failure-Shape Race Demo functionally end-to-end (POST /api/race/run + WS streaming). Phase 11 human UAT passed (4/4) closing DISC-01/02. DESIGN.md formalized.

Next action: run `/gsd-new-milestone` to start v2.1 (questioning → research → requirements → roadmap). Fresh `REQUIREMENTS.md` will be created by that workflow.

## Accumulated Context

### Decisions

Decisions logged in PROJECT.md Key Decisions table. Per-plan decision history retained in `.planning/milestones/v1.0-phases/` (v1.0) and per-phase directories `.planning/phases/06-*..16-*/` (v2.0, until archived via `/gsd-cleanup`).

### Carried into v2.1+

- SDK-01: A2A SDK 0.3.26 → 1.0.0 migration
- SDK-02: MCP SDK v2 (`FastMCP` → `McpServer`) migration
- TODO-01: Real plan-emitter hybrid (`propose_plan` agent step generation)
- TODO-02: Multi-seed n=20+ benchmark mode with bootstrap CIs
- TODO-04: Production trace schema migrator
- TODO-06: Real display typeface
- TODO-07: HardnessFailureHeatmap auto-renders rows from `HardnessType` enum
- TODO-09: HMAC-signed PNG URLs (production hardening)
- TODO-10: LLM-judge replacement for `agent_msg_acknowledging_fault` regex

### Pending Todos

10 deferred items in `TODOS.md` (project root). Promote conditions per item.

### Blockers/Concerns

None — v2.0 closed clean.

## Deferred Items (carried from v1.0 + v2.0)

| Category | Item | Status | Source |
|----------|------|--------|--------|
| Verification | Phase 5 missing VERIFICATION.md | Wired per integration check; bookkeeping gap | v1.0 audit |
| Verification | Phase 4 — 3 visual verification items | Code-level verified; visual checks deferred to demo-day rehearsal | v1.0 audit |
| SDK | SDK-01: A2A SDK 1.0.0 migration | v2.1+ backlog | Init |
| SDK | SDK-02: MCP SDK v2 migration (`FastMCP` → `McpServer`) | v2.1+ backlog | Init |
| Tech Debt | `api.ts` + `api.generated.ts` dual-patching | Manual edits in both required for new fields | v1.0+ |
| Tech Debt | `tool_transport_fallback` event type doubles as discovery-failure signal | Pragmatic but coupled | Phase 11 |
| Plan Review | TODOs 1, 2, 4, 6, 7, 9, 10 in TODOS.md | v2.1+ candidates per promote conditions | Plan reviews |

## Session Continuity

Last session: 2026-05-05T01:00:00+05:30
Stopped at: v2.0 milestone close — archived
Resume file: N/A (milestone closed; run `/gsd-new-milestone` to start v2.1)
Next action: `/gsd-new-milestone` to define v2.1 scope and produce fresh `REQUIREMENTS.md` + `ROADMAP.md` entries.
