---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: "Phase 4 planned — 4 plans in 3 waves, verification passed. Ready for /gsd-execute-phase 4."
last_updated: "2026-04-27T13:00:00Z"
last_activity: 2026-04-27
progress:
  total_phases: 5
  completed_phases: 3
  total_plans: 4
  completed_plans: 0
  percent: 60
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-22)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** Phase 4 — Comparison UI

## Current Position

Phase: 3 of 5 (New Scenarios)
Plan: 4 of 4 in current phase (03-04 complete, Phase 3 done)
Status: Phase 3 complete — ready for Phase 4 (Comparison UI)
Last activity: 2026-04-23

Progress: [████████░░] 80%

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: —
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Init: Lock demo day to `runtime=mock, transport=in_process` — only fully-tested, crash-safe transport path
- Init: Pin `mcp>=1.27,<2` and `a2a-sdk==0.3.26` for this milestone; defer SDK major migrations to v2
- Init: Add new scenarios as `DemoRepository` entries — fits existing dispatch pattern without infrastructure changes
- 02-02: Cast event.task_id via `(event as { task_id?: unknown }).task_id` — keeps task_id out of TraceEvent interface since it is A2A-internal, accessed through index signature
- 02-02: api.generated.ts manually patched with `| null` pattern; comment documents regeneration path after api_schemas.py is updated
- 02-03: Tests pass at RED commit — Plan 01 pre-implemented enrichment fields; test methods serve as regression guards for TRACE-01/02/03/04
- 02-03: handler.handle_task() (not handle()) is the broker handler protocol — matched FlakyHandler in existing test suite
- 03-01: TalkingPointResponse uses required str fields (not Optional) — seed data always provides all three keys; None handled at TicketResponse level
- 03-01: TICKET-1011 has no parallel_investigation tag — multi-step chained scenario; parallel_investigation reserved for TICKET-1012 to trigger 03-02 dispatch branch
- 03-02: Tag check inserted as first line of resolve_with_broker() before intent classification — deterministic, crash-safe (D-06); _merge() used with issue_type='parallel_investigation'
- 03-03: a2a sequential dispatch emits a2a_message(task_request) not task_submit — task_submit is parallel-only (D-07); assertion corrected from task_submit to a2a_message filter
- 03-03: MockReasoner classifies 'failed after 6 months — warranty refund' as warranty_return with needs_docs=False (no failing/error/setup match) — 2 specialists fire; assertion adjusted to >= 2 with comment (D-08)
- 03-04: api.ts maintains an independent inline RunResult.ticket type separate from api.generated.ts TicketResponse — both must be patched when adding fields; TalkingPointCard added to both (Rule 1 fix)
- 03-04: protocolColor hardcoded at module level in RunWorkspacePage.tsx — Phase 4 eventColors.ts will subsume this (D-15)
- 03-04: TalkingPointCard JSX inline in result map, not extracted to a component file (D-14)

### Pending Todos

None yet.

### Blockers/Concerns

None — Phase 2 complete. TRACE-05 delivered; timeout_ms=5000 in A2ABroker confirmed.

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Scenarios | DISC-01/02: Tool discovery scenario + DiscoveryPhasePanel | v2 backlog | Init |
| SDK | SDK-01: A2A SDK 1.0.0 migration | v2 backlog | Init |
| SDK | SDK-02: MCP SDK v2 migration | v2 backlog | Init |
| Visualization | VIZ-01: Annotated diff view | v2 backlog | Init |
| Visualization | VIZ-02: Interactive sequence diagram | v2 backlog | Init |

## Session Continuity

Last session: 2026-04-27
Stopped at: Phase 4 planned — 4 plans in 3 waves (eventColors foundation → metrics+swimlane parallel → compare panel). Verification passed, all 12 decisions covered.
Resume file: .planning/phases/04-comparison-ui/04-01-PLAN.md
