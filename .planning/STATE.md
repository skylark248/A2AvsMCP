---
gsd_state_version: 1.0
milestone: v2.0
milestone_name: Race Demo + Discovery + Visualization
status: "v2.0 COMPLETE — All 8 phases (6-13) shipped. Phase 13 DSGN-01 delivered: .planning/DESIGN.md formalizes 5 race-demo design tokens (failureTagColor map, methodology-as-flat, secondary.main, role-first, palette intent). Backend 345/345 pytest; frontend 326/326 vitest. Milestone complete 2026-05-01."
stopped_at: Phase 13 complete — DSGN-01 VERIFIED PASS 2026-05-01. v2.0 milestone complete.
last_updated: "2026-05-01T18:27:00.000Z"
last_activity: "2026-05-01 23:57 — Phase 13 verified PASS; v2.0 milestone complete (8/8 phases, 43/43 plans)"
progress:
  total_phases: 8
  completed_phases: 8
  total_plans: 43
  completed_plans: 43
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-28)

**Core value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.
**Current focus:** v2.0 milestone COMPLETE — all 8 phases (6-13) shipped. See `.planning/DESIGN.md` for DSGN-01 deliverable.

## Current Position

Phase: 13 ✅ VERIFIED PASS (2026-05-01). v2.0 milestone COMPLETE — all 8 phases (Phases 6-13), 43/43 plans. DSGN-01 delivered: `.planning/DESIGN.md`.

Phase 12 wave structure:

- Wave 1 / 12-01: alignTraces pure function + vitest (`frontend/src/components/traces/diffAlign.ts` + `__tests__/diffAlign.test.ts`) — VIZ-01 algorithm foundation [D-74, D-76, D-77, D-78]
- Wave 1 / 12-02: SequenceDiagramView (hand-rolled SVG, 5 fixed lifelines) + TraceExplorer toggle (List|Sequence) + pinned-event lift + vitest covering reduced-motion + click-to-pin + cross-view scroll — closes VIZ-02 [D-78, D-79, D-80, D-81, D-82, D-83, D-85]
- Wave 2 / 12-03 (depends_on 12-01): AnnotatedDiffView component + CompareTracesPanel toggle (Side-by-side|Annotated diff) + vitest (≥7 + ≥3) — closes VIZ-01 [D-75, D-77, D-78, D-84, D-85]

Plan-checker subagent skipped (quota exhausted; resets May 4). Plans written inline against locked CONTEXT.md + UI-SPEC.md + verified RESEARCH.md line numbers; verify integrity before/during execute.

Quota recovery: planner subagent crashed mid-write after 12-01 + 12-02 landed. 12-03 authored inline by primary session per `feedback_subagent_quota_recovery` rule.

Wave structure:

- Wave 0 / 11-01: ✅ Extract JsonTree+FIELD_ANNOTATIONS+annotate from ProtocolEnvelopeDrawer → frontend/src/lib/trace/JsonTree.tsx (commits 3b5aff9, f5dd49a) [DISC-02 partial]
- Wave 1 / 11-02: ✅ tool_discovery scenario seed (TICKET-1013) + customer (CUST-005) + pytest (3 tests: load + emit + fallback) (commits f413311, 866fbb3) [DISC-01]
- Wave 1 / 11-03: ✅ DiscoveryPhasePanel.tsx (MUI Accordion + Grid 2-col + protocol stripes + stale-cache highlight + a2a_remote_discovery skill-chip join) + 5-case vitest (commits a84c511, b84acd3) [DISC-02]
- Wave 2 / 11-04: ✅ Mount-site wiring — TraceWorkspacePage D-73 gate + CompareTracesPanel D-72 single panel above dual-column + integration verification (commits e1b6e31, 1357a2f) [DISC-02]

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

Next action: continue Phase 11 execution (Wave 2: plan 11-04 mount-site wiring — TraceWorkspacePage gate D-73 + CompareTracesPanel single-panel-above-dual D-72 + integration verification).
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

Last session: 2026-05-01T06:10:40.245Z
Stopped at: Phase 12 UI-SPEC approved
Resume file: .planning/phases/12-comparison-visualization-upgrades/12-UI-SPEC.md
Next action: Execute plan 11-04 (Wave 2 mount-site wiring) — gated on 11-02 + 11-03, both now complete. Wires DiscoveryPhasePanel into TraceWorkspacePage (gated on scenario === "tool_discovery" per D-73) and CompareTracesPanel (single panel above dual-column per D-72), with integration verification via vitest.
