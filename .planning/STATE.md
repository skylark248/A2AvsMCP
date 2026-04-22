# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-22)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** Phase 2 — Backend Trace Enrichment

## Current Position

Phase: 2 of 5 (Backend Trace Enrichment)
Plan: 0 of TBD in current phase
Status: Context captured — ready for planning
Last activity: 2026-04-22 — Phase 2 context gathered (step_index, phase tagging, trace tier UI decisions locked)

Progress: [██░░░░░░░░] 20%

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

### Pending Todos

None yet.

### Blockers/Concerns

- TRACE-05 (trace view tiers) must be complete before Phase 3 scenarios are built — new scenarios will produce 60-120+ events
- `timeout_ms=1500` in `A2ABroker` is too low for parallel dispatch (TRACE-04 addresses this in Phase 2)

## Deferred Items

| Category | Item | Status | Deferred At |
|----------|------|--------|-------------|
| Scenarios | DISC-01/02: Tool discovery scenario + DiscoveryPhasePanel | v2 backlog | Init |
| SDK | SDK-01: A2A SDK 1.0.0 migration | v2 backlog | Init |
| SDK | SDK-02: MCP SDK v2 migration | v2 backlog | Init |
| Visualization | VIZ-01: Annotated diff view | v2 backlog | Init |
| Visualization | VIZ-02: Interactive sequence diagram | v2 backlog | Init |

## Session Continuity

Last session: 2026-04-22
Stopped at: Phase 2 context captured — ready for /gsd-plan-phase 2
Resume file: .planning/phases/02-backend-trace-enrichment/02-CONTEXT.md
