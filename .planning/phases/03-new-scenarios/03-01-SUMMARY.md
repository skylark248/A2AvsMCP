---
phase: "03-new-scenarios"
plan: "01"
subsystem: "backend-data-schema"
tags: ["schema", "seed-data", "pydantic", "tdd", "scenarios"]
dependency_graph:
  requires: []
  provides:
    - "SupportTicket.talking_point field"
    - "TalkingPointResponse Pydantic model"
    - "TicketResponse.talking_point field"
    - "scenarios.json 12 entries with talking_point objects"
    - "warranties.json WAR-7004 for CUST-001"
    - "SCEN-03 pytest assertions (2 tests)"
  affects:
    - "03-02-PLAN.md — parallel dispatch reads new scenario tags"
    - "03-03-PLAN.md — SCEN-01 tests run new scenario tickets"
    - "03-04-PLAN.md — frontend types consume TalkingPointResponse"
tech_stack:
  added: []
  patterns:
    - "Pydantic BaseModel for typed API surface (TalkingPointResponse)"
    - "dataclass optional field with plain None default (talking_point: dict | None = None)"
    - "item.get() passthrough in load_scenarios() — no transformation, None if absent"
key_files:
  created:
    - "src/a2a_vs_mcp/data/seeds/scenarios.json (12 entries)"
    - "src/a2a_vs_mcp/data/seeds/warranties.json (4 entries)"
  modified:
    - "src/a2a_vs_mcp/schemas.py — SupportTicket.talking_point field"
    - "src/a2a_vs_mcp/api_schemas.py — TalkingPointResponse model + TicketResponse.talking_point field"
    - "src/a2a_vs_mcp/dataset.py — load_scenarios() talking_point passthrough"
    - "tests/test_demo_modes.py — 2 SCEN-03 test methods added"
decisions:
  - "03-01-D1: TalkingPointResponse uses required str fields (not Optional) — seed data always provides all three keys; None is handled at the TicketResponse level"
  - "03-01-D2: TICKET-1011 has no parallel_investigation tag — multi-step chained scenario, not parallel; parallel_investigation tag reserved for TICKET-1012 to trigger 03-02 dispatch branch"
metrics:
  duration: "3 minutes"
  completed: "2026-04-23"
  tasks_completed: 2
  files_modified: 6
---

# Phase 3 Plan 01: Seed Data and Schema Layer Summary

Schema and data contract layer establishing `SupportTicket.talking_point`, `TalkingPointResponse` Pydantic model, `TicketResponse.talking_point`, 12-entry scenarios.json with talking_point objects on all entries, WAR-7004 warranty seed, and 2 SCEN-03 pytest assertions — all passing.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| RED | SCEN-03 failing tests | d57ad47 | tests/test_demo_modes.py |
| GREEN | Schema + data layer implementation | 7160f83 | schemas.py, api_schemas.py, dataset.py, scenarios.json, warranties.json |

## What Was Built

### SupportTicket.talking_point (schemas.py)
Added `talking_point: dict | None = None` as the last field on the `SupportTicket` dataclass, after `tags`. Uses plain `None` default (not `field(default_factory=...)`), correct for an optional mutable type where None signals absence.

### TalkingPointResponse + TicketResponse.talking_point (api_schemas.py)
Inserted `TalkingPointResponse(BaseModel)` with three required `str` fields (`headline`, `sentence`, `callout`) immediately before `TicketResponse`. Added `talking_point: TalkingPointResponse | None = None` as the last field on `TicketResponse`. This creates a typed API surface: Pydantic validates structure at serialization, `None` is accepted, malformed dicts raise `ValidationError` before response is sent (T-03-01-03 mitigation).

### dataset.py passthrough
Added `talking_point=item.get("talking_point")` to the `SupportTicket(...)` constructor in `load_scenarios()`. No transformation — `item.get()` returns `None` when key is absent, matching the field default.

### scenarios.json (12 entries)
All 10 existing entries enriched with `talking_point` objects. Two new entries appended:
- **TICKET-1011** (`device_failure_warranty_refund`): advanced, tags `["warranty", "troubleshooting", "policy", "multi-step"]` — chained multi-step scenario
- **TICKET-1012** (`vip_parallel_escalation`): advanced, tags `["enterprise", "parallel_investigation", "escalation"]` — `parallel_investigation` tag triggers 03-02 dispatch branch

### warranties.json (4 entries)
WAR-7004 added: CUST-001 / SmartHub Mini / expires 2027-04-01 / premium coverage. Covers CUST-001 (Aisha Verma) for the TICKET-1011 device failure scenario.

### SCEN-03 pytest (test_demo_modes.py)
Two new methods in `DemoModeTests`:
- `test_scen03_talking_point_on_ticket` — asserts `device_failure_warranty_refund` ticket has non-None `talking_point` with all three keys
- `test_scen03_talking_point_on_vip_ticket` — same for `vip_parallel_escalation`

Both pass. Full suite: **43 passed in 16.33s**.

## TDD Gate Compliance

- RED gate: `test(03-01)` commit `d57ad47` — two failing tests before any implementation
- GREEN gate: `feat(03-01)` commit `7160f83` — all tests pass after implementation
- REFACTOR gate: not needed (schema additions, no logic to clean up)

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — `talking_point` data is fully wired from seed JSON through `SupportTicket` to `TicketResponse`. The frontend UI consumer (03-04) does not yet render the card, but that is the intended split across plans, not a stub in this plan's scope.

## Threat Flags

No new security-relevant surface beyond plan's threat model. `TalkingPointResponse` Pydantic validation covers T-03-01-03 (malformed talking_point dict raises `ValidationError` before API response is sent).

## Self-Check: PASSED

Files confirmed present:
- src/a2a_vs_mcp/schemas.py — `talking_point: dict | None = None` present
- src/a2a_vs_mcp/api_schemas.py — `class TalkingPointResponse` present
- src/a2a_vs_mcp/dataset.py — `talking_point=item.get` present
- src/a2a_vs_mcp/data/seeds/scenarios.json — 12 entries confirmed
- src/a2a_vs_mcp/data/seeds/warranties.json — 4 entries including WAR-7004 confirmed
- tests/test_demo_modes.py — `test_scen03_talking_point_on_ticket` present

Commits confirmed:
- d57ad47 (RED): test(03-01) commit exists
- 7160f83 (GREEN): feat(03-01) commit exists
