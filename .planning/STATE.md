---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Race Demo + Discovery + Visualization
status: in_progress
stopped_at: Phase 11 plan 11-01 complete (Wave 0 refactor; vitest 286/286 green)
last_updated: "2026-05-01T03:24:00.000Z"
last_activity: 2026-05-01 03:24 — Plan 11-01 executed: JsonTree extracted to lib/trace/JsonTree.tsx; drawer imports updated; vitest 286/286 green; ROADMAP + STATE updated.
progress:
  total_phases: 8
  completed_phases: 5
  total_plans: 39
  completed_plans: 36
  percent: 92.3
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-28)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** Phase 11 — Tool Discovery Scenario (1/4 plans complete; Wave 0 shipped 2026-05-01; Wave 1 next: 11-02 + 11-03)

## Current Position

Phase: 11 (tool-discovery-scenario) — Wave 0 complete (11-01 shipped 2026-05-01, vitest 286/286 green). Next: 11-02 (Wave 1 backend seed) + 11-03 (Wave 1 frontend panel) can run in parallel; 11-04 gated on both.

Wave structure:
- Wave 0 / 11-01: ✅ Extract JsonTree+FIELD_ANNOTATIONS+annotate from ProtocolEnvelopeDrawer → frontend/src/lib/trace/JsonTree.tsx (commits 3b5aff9, f5dd49a) [DISC-02 partial]
- Wave 1 / 11-02: tool_discovery scenario seed (TICKET-1013) + customer (CUST-005) + pytest (3 tests covering load + emit + fallback) [DISC-01]
- Wave 1 / 11-03: DiscoveryPhasePanel.tsx (MUI Accordion + Grid 2-col + protocol stripes) + 5-case vitest (incl. a2a_remote_discovery skill chips) [DISC-02]; depends_on [11-01]
- Wave 2 / 11-04: Mount-site wiring — TraceWorkspacePage gate (D-73) + CompareTracesPanel single panel above dual-column (D-72) + integration verification [DISC-02]; depends_on [11-02, 11-03]

Pitfalls baked into plans:
- Filter on event.event_type === "tool_discovery" (NOT event.phase) — _PHASE_MAP does not tag discovery
- A2A column unions tool_discovery (with remote_agent) AND a2a_remote_discovery (joins by agent_id)
- JsonTree-only import (FIELD_ANNOTATIONS/annotate not used by panel)
- Failure modes reuse existing tool_transport_fallback event — no new event_type
- Vitest renders wrapped in ThemeProvider+CssBaseline

Decisions locked (D-67..D-73):
Decisions locked (D-67..D-73):

- D-67: Net-new TICKET-1013 + net-new customer in seeds/scenarios.json (researcher fills profile)
- D-68: Unknown product/SKU in query forces discovery — naturally exercises stale-cache + unknown-tool-fallback
- D-69: difficulty=advanced, tags=[discovery, fallback]
- D-70: TraceWorkspacePage — active protocol column populated; sibling column dimmed with placeholder
- D-71: Sibling placeholder = static hint text only ("Run on {A2A|MCP} to populate"); no inline run button
- D-72: CompareTracesPanel — single DiscoveryPhasePanel above both columns, full-width, internal MCP|A2A split
- D-73: Panel mounts only when scenario === "tool_discovery" on TraceWorkspacePage

Discretion resolved during research/planning:
- Failure-mode injection: reuse tool_transport_fallback + requested_transport divergence (no new event_type)
- ReportDetailPage/RacePage: NOT mounted (deferred to potential Phase 12)
- Accordion default: defaultExpanded={true}
- talking_point + CUST-005 profile: drafted in 11-02 plan

Next action: continue Phase 11 execution (Wave 1: plans 11-02 + 11-03).
Status: Phase 10 implementation decisions D-61..D-66 honoured (Playwright singleton + asyncio.Lock, 503 + canvas fallback, mock render in CI, html2canvas lazy, ClipboardItem + download fallback, manual OG_LAYOUT_VERSION). Backend pytest 342/342 (336 baseline + 6 og_cache + 10 og_routes); frontend vitest 286/286 across 31 files (280 baseline + 2 HeatmapAnnotationStrip + 4 CopyHeadlineImageButton; Phase 8 RacePage.responsive copy assertion updated for UIRACE-05 closure). Wave 2 quota recovery: 10-02 + 10-03 each had Task 1 committed pre-quota; Task 2 salvaged from main tree; remaining tasks (test_og_routes.py, RacePage `?og=1` wiring, both SUMMARYs) executed inline.
Last activity: 2026-04-30 21:58 — Phase 10 verified PASS; ROADMAP + STATE advanced

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

Last session: 2026-05-01T03:24:00.000Z
Stopped at: Plan 11-01 complete (Wave 0 refactor; commits 3b5aff9 + f5dd49a; vitest 286/286)
Resume file: .planning/phases/11-tool-discovery-scenario/11-01-SUMMARY.md
Next action: Run `/gsd-verify-phase 9` to validate the 4 ROADMAP success criteria against shipped code (heatmap visual contract, 5-pill legend + footer, replay-symmetric tags, K=3 calibration sweep). After PASS, advance to Phase 10 (OG Image & Sharing) which now has populated heatmap cells available for Playwright PNG capture.
