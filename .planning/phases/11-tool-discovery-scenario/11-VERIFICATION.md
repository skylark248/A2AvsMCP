---
phase: 11-tool-discovery-scenario
verified: 2026-05-04T16:14:00Z
status: passed
score: 16/16 must-haves verified
overrides_applied: 0
human_verification_evidence:
  - test: "Run tool_discovery on A2A protocol via live UI"
    result: "✓ Passed — agent cards populated with agents and skill chips, relative timestamps rendered, MCP column showed placeholder text, panel rendered above TraceExplorer"
  - test: "Run tool_discovery on MCP protocol via live UI"
    result: "✓ Passed — tool catalog populated with names and timestamps, search_docs fallback visible for NebulaSync Hub unknown SKU, panel rendered above TraceExplorer"
  - test: "Run tool_discovery in compare mode (D-72 layout)"
    result: "✓ Passed — single full-width DiscoveryPhasePanel above dual-column TraceExplorer grid, both MCP and A2A columns populated"
  - test: "Verify visual ordering (panel before execution events)"
    result: "✓ Passed — panel renders ABOVE TraceExplorer on all three modes (single MCP, single A2A, compare)"
human_verification:
  - test: "Run the tool_discovery scenario on the A2A protocol via the live UI"
    expected: "TraceWorkspacePage renders DiscoveryPhasePanel above the TraceExplorer; A2A column populates with at least one agent card and skill chips; A2A — Agent Cards header shown; per-agent timestamps render"
    why_human: "Backend pytest only asserts mcp mode emission and search_docs fallback. ROADMAP success criterion #1 explicitly says 'both MCP and A2A protocols' — the A2A code path shares the same tool_discovery event but is not exercised by an automated test. Visual confirmation needed that a2a_remote_discovery events flow through the agent-card column in a real run."
  - test: "Run the tool_discovery scenario in mcp mode via the live UI and observe stale-capability-cache + unknown-tool-fallback rendering"
    expected: "DiscoveryPhasePanel shows MCP tool catalog cards; the unknown 'NebulaSync Hub' SKU triggers fallback such that search_docs is rendered as an executed tool below; if requested_transport differs from transport, a warning icon (aria-label 'Stale capability cache') appears on the tool card"
    why_human: "Vitest verifies the warning icon renders given a fixture; pytest verifies search_docs is in tools_used. End-to-end visual confirmation that the operator-facing failure-mode story reads correctly is a UX judgment."
  - test: "Run the tool_discovery scenario in compare mode (both modes selected) and confirm a single full-width DiscoveryPhasePanel renders above the dual-column TraceExplorer (D-72)"
    expected: "Exactly ONE DiscoveryPhasePanel above the dual-column Grid — not one per column. Panel disappears when comparing two non-discovery runs (presence-gate per RESEARCH A4)."
    why_human: "Grep gates confirm the wiring shape; live verification confirms the visual layout matches D-72 contract."
  - test: "Confirm DiscoveryPhasePanel renders strictly BEFORE any execution-phase events in the visual flow"
    expected: "Panel appears ABOVE TraceExplorer; tool_discovery events render in the panel and DO NOT also clutter the explorer's execution timeline at the top"
    why_human: "ROADMAP success criterion #2 explicit phrasing: 'before any execution-phase events'. Programmatic check confirmed the panel mounts above the explorer Grid block; visual ordering at runtime needs human eye."
---

# Phase 11: Tool Discovery Scenario Verification Report

**Phase Goal:** Surface MCP tool discovery and A2A agent-card discovery as a first-class UI section above the trace explorer, on a dedicated scenario.
**Verified:** 2026-05-01T10:57:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| T-01 | DemoRepository.load_scenarios() returns SupportTicket keyed by 'tool_discovery' | VERIFIED | `tests/test_tool_discovery_scenario.py:31-40` asserts; row exists at `src/a2a_vs_mcp/data/seeds/scenarios.json` line 171; orchestrator-reported pytest 345/345 |
| T-02 | tool_discovery scenario emits tool_discovery trace events in mcp mode | VERIFIED | `tests/test_tool_discovery_scenario.py:42-55` asserts at least one event; emit site in `src/a2a_vs_mcp/mcp/client.py:78` |
| T-03 | Unknown SKU 'NebulaSync Hub' forces search_docs fallback | VERIFIED | `tests/test_tool_discovery_scenario.py:57-69` asserts search_docs in result.tools_used; SKU absent from warranties/orders seeds (D-68 data-driven) |
| T-04 | SQLite cache rebuilds via _seed_signature() hash mismatch | VERIFIED | Tests run successfully against fresh fixture cache; `dataset.py` rebuild path unchanged |
| T-05 | ProtocolEnvelopeDrawer continues rendering tool_discovery payloads identically | VERIFIED | `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx:16` imports JsonTree from new path; usage at line 136 unchanged; full vitest suite 291/291 (no drawer regression) |
| T-06 | JsonTree, FIELD_ANNOTATIONS, annotate are named exports of shared module | VERIFIED | `frontend/src/lib/trace/JsonTree.tsx:4,25,31` — three `export` keywords; no `export default` |
| T-07 | DiscoveryPhasePanel renders Accordion (defaultExpanded=true) with two-column Grid | VERIFIED | `DiscoveryPhasePanel.tsx:224` Accordion, lines 243-288 Grid with `xs:12, md:6` columns |
| T-08 | MCP column renders tool catalog cards with name + relative timestamp | VERIFIED | `DiscoveryPhasePanel.tsx:44-119` `renderMcpToolCards`; `+{relMs}ms` at line 88; vitest baseline case |
| T-09 | A2A column shows agent-card chips joined to tool list by remote_agent ↔ a2a_agent_card.agent_id | VERIFIED | `DiscoveryPhasePanel.tsx:126-207` `renderA2aAgentCards` with Map join; vitest case 5 asserts `lookup_warranty` + `check_order` chips render |
| T-10 | Empty MCP column renders 'Run on MCP to populate' (D-71 verbatim) | VERIFIED | `DiscoveryPhasePanel.tsx:258`; vitest case 3 |
| T-11 | Empty A2A column renders 'Run on A2A to populate' (D-71 verbatim) | VERIFIED | `DiscoveryPhasePanel.tsx:281`; vitest case 2 |
| T-12 | Stale-cache fallback highlight uses requested_transport != transport (no new event_type) | VERIFIED | `DiscoveryPhasePanel.tsx:46-49` divergence check; lines 78-86 Tooltip + WarningAmberRoundedIcon with aria-label="Stale capability cache"; vitest case 4 |
| T-13 | TraceWorkspacePage mounts DiscoveryPhasePanel ABOVE TraceExplorer gated on scenario === 'tool_discovery' | VERIFIED | `frontend/src/features/traces/TraceWorkspacePage.tsx:392` gate; line 405 panel mounted; line 415 TraceExplorer below |
| T-14 | CompareTracesPanel mounts SINGLE full-width DiscoveryPhasePanel above dual-column Grid (D-72) | VERIFIED | `frontend/src/features/compare/CompareTracesPanel.tsx:111-118` single panel; line 121 dual-column Grid below |
| T-15 | CompareTracesPanel mount is presence-gated on tool_discovery / a2a_remote_discovery presence | VERIFIED | `CompareTracesPanel.tsx:57` `showDiscoveryPanel` derived from `discoveryMcpEvents.length > 0 || discoveryA2aEvents.length > 0`; line 112 conditional render |
| T-16 | Both mount sites filter on event_type === 'tool_discovery' (NOT phase) and union A2A with a2a_remote_discovery | VERIFIED | `TraceWorkspacePage.tsx:397,401-402` and `CompareTracesPanel.tsx:50,54-55` both have event_type filters; `grep -c 'phase === "discovery"'` returns 0 in all three component files (Pitfall #1 honored) |

**Score:** 16/16 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `frontend/src/lib/trace/JsonTree.tsx` | Shared JsonTree, FIELD_ANNOTATIONS, annotate (named exports) | VERIFIED | 107 lines; 3 `export` declarations; imports `Box, Tooltip` from MUI; no default export |
| `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` | Imports JsonTree from new shared module | VERIFIED | Line 16 `import { JsonTree } from "../../lib/trace/JsonTree"`; usage at line 136 |
| `src/a2a_vs_mcp/data/seeds/scenarios.json` | TICKET-1013 with scenario='tool_discovery', advanced, tags=[discovery,fallback] | VERIFIED | Valid JSON (13 rows); contains TICKET-1013, scenario:tool_discovery, NebulaSync Hub query |
| `src/a2a_vs_mcp/data/seeds/customers.json` | CUST-005 (Casey Rivera) | VERIFIED | Valid JSON (5 rows); contains CUST-005 |
| `tests/test_tool_discovery_scenario.py` | 3 pytest cases: load, emit, fallback | VERIFIED | unittest.TestCase with 3 test methods asserting TICKET-1013/CUST-005/event_type/search_docs |
| `frontend/src/components/traces/DiscoveryPhasePanel.tsx` | Component with DiscoveryPhasePanelProps, two columns, fallback highlight, JsonTree consumer | VERIFIED | 293 lines; exports `DiscoveryPhasePanel`, `DiscoveryPhasePanelProps`; imports JsonTree, protocolColor, toneColor; zero dangerouslySetInnerHTML; zero `event.phase` references |
| `frontend/src/components/traces/__tests__/DiscoveryPhasePanel.test.tsx` | 5 vitest cases | VERIFIED | All 5 cases present: baseline, MCP-only placeholder, A2A-only placeholder, stale-cache highlight, a2a_remote_discovery skill-chip render |
| `frontend/src/features/traces/TraceWorkspacePage.tsx` | Mount with scenario gate above TraceExplorer | VERIFIED | Import at line 26; mount block at lines 392-413 ABOVE TraceExplorer Grid at line 415 |
| `frontend/src/features/compare/CompareTracesPanel.tsx` | Single full-width mount above dual-column Grid, presence-gated | VERIFIED | Import at line 13; presence gate + mount at lines 49-118; dual-column Grid below at line 121 |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|----|--------|---------|
| ProtocolEnvelopeDrawer.tsx | lib/trace/JsonTree.tsx | named import | WIRED | Line 16 import; line 136 usage `<JsonTree data={data} />` |
| DiscoveryPhasePanel.tsx | lib/trace/JsonTree.tsx | named import | WIRED | Line 10 import; line 109 usage in inputSchema render |
| DiscoveryPhasePanel.tsx | lib/trace/eventColors.ts | named import (protocolColor, toneColor) | WIRED | Line 9 import; protocolColor.mcp/a2a used at lines 232,238,246,250,269,273; toneColor.warning at lines 62,83 |
| DiscoveryPhasePanel.test.tsx | DiscoveryPhasePanel.tsx | named import | WIRED | Lines 6-7 named import for component + props type |
| TraceWorkspacePage.tsx | DiscoveryPhasePanel.tsx | named import + JSX usage | WIRED | Line 26 import; line 405 JSX |
| CompareTracesPanel.tsx | DiscoveryPhasePanel.tsx | named import + JSX usage | WIRED | Line 13 import; line 113 JSX |
| TraceWorkspacePage.tsx mount gate | seeds/scenarios.json scenario string | scenario === "tool_discovery" string match | WIRED | Line 392 — value flows from `detail.summary.scenario` populated server-side from Plan 11-02's seed |
| MCP client emit | tool_discovery event_type | TraceRecorder | WIRED | `src/a2a_vs_mcp/mcp/client.py:78` emits `tool_discovery` event_type |
| A2A remote broker emit | a2a_remote_discovery event_type | TraceRecorder | WIRED | `src/a2a_vs_mcp/a2a/remote_broker.py:91` emits `a2a_remote_discovery` |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|--------------------|--------|
| DiscoveryPhasePanel | mcpEvents prop | TraceWorkspacePage filters `visibleResults.flatMap(r => r.trace ?? [])` from API `detail.results[].trace` | Yes — events emitted by `mcp/client.py:78` | FLOWING |
| DiscoveryPhasePanel | a2aEvents prop | TraceWorkspacePage / CompareTracesPanel filter unions of tool_discovery+remote_agent and a2a_remote_discovery from same trace arrays | Yes — events emitted by `a2a/remote_broker.py:91` and `mcp/client.py:78` | FLOWING |
| DiscoveryPhasePanel | scenario prop | `detail.summary.scenario` (TraceWorkspacePage) / `resultA?.ticket?.scenario` (CompareTracesPanel) — both originate from seeds/scenarios.json TICKET-1013 row | Yes — value 'tool_discovery' flows from seed JSON through DemoRepository → API | FLOWING |
| DiscoveryPhasePanel inputSchema rendering | tool.inputSchema | event.tools[i].inputSchema from MCP server tools/list response | Yes when MCP server returns inputSchema; component handles missing inputSchema (line 92 conditional) | FLOWING |
| renderA2aAgentCards skills | a2a_agent_card.skills | event.a2a_agent_card.skills from a2a_remote_discovery emit site | Yes — `remote_broker.py:91` emits this payload | FLOWING |

All Level 4 traces resolve to FLOWING — no HOLLOW or DISCONNECTED artifacts.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Backend test suite (orchestrator-reported) | `pytest` | 345/345 passing | PASS |
| Frontend test suite (orchestrator-reported) | `npm test -- --run` | 291/291 passing | PASS |
| New backend tests pass | (orchestrator-reported subset) | 3/3 in tests/test_tool_discovery_scenario.py | PASS |
| New frontend tests pass | (orchestrator-reported subset) | 5/5 in DiscoveryPhasePanel.test.tsx | PASS |
| Seed JSON validity | `python -m json.tool ...` | exit 0 for both files (13 + 5 rows) | PASS |
| Pitfall #1 honored — no `phase === "discovery"` gate | grep across 3 files | 0 hits | PASS |
| No XSS via dangerouslySetInnerHTML | grep across new files | 0 hits | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| DISC-01 | 11-02 | New `tool_discovery` scenario in DemoRepository exercising MCP+A2A discovery; failure modes stale-capability-cache + unknown-tool-fallback | SATISFIED | TICKET-1013 seeded; pytest cases assert load + mcp emission + search_docs fallback; D-68 data-driven design for stale cache via requested_transport divergence (existing wire signal) |
| DISC-02 | 11-01, 11-03, 11-04 | DiscoveryPhasePanel renders discovery phase as first-class section above trace explorer; tool catalog (MCP) + agent cards (A2A) side-by-side with timestamps | SATISFIED | Component built (11-03), JsonTree extracted (11-01), mounted on both TraceWorkspacePage and CompareTracesPanel ABOVE TraceExplorer (11-04); vitest baseline + 4 case-specific tests pass; orchestrator-reported full vitest suite 291/291 |

No orphaned requirements: REQUIREMENTS.md maps DISC-01 + DISC-02 to Phase 11; both appear in plan frontmatter `requirements:` fields (11-02 → DISC-01; 11-01/11-03/11-04 → DISC-02).

### Anti-Patterns Found

None. Spot-checked categories:

| Category | Result |
|----------|--------|
| TODO/FIXME/PLACEHOLDER comments in modified files | 0 hits |
| `phase === "discovery"` gating (Pitfall #1) | 0 hits across all 3 frontend files |
| `dangerouslySetInnerHTML` | 0 hits |
| Hardcoded empty props at mount sites | None — both mount sites compute filters from real trace arrays |
| Empty handlers / stub returns in DiscoveryPhasePanel | None — component does substantive rendering work |

### Critical Pitfall Re-Verification

| Pitfall | Location | Status |
|---------|----------|--------|
| #1 Filter on event_type, not event.phase | TraceWorkspacePage.tsx:397, CompareTracesPanel.tsx:50, DiscoveryPhasePanel.tsx:128 | HONORED — 0 phase-gating hits |
| #2 A2A partition unions tool_discovery+remote_agent with a2a_remote_discovery | TraceWorkspacePage.tsx:401-402, CompareTracesPanel.tsx:54-55 | HONORED — both clauses present |
| #5 Drawer import path updated when JsonTree extracted | ProtocolEnvelopeDrawer.tsx:16 | HONORED — drawer imports from new location; vitest 291/291 |
| #6 Null-safe accessors at mount sites | TraceWorkspacePage.tsx:392 `detail?.summary?.scenario`, CompareTracesPanel.tsx:48 `resultA?.trace ?? []`, line 49 same for resultB | HONORED |
| D-72 single full-width panel above both columns on Compare | CompareTracesPanel.tsx:111-118 | HONORED — single `<DiscoveryPhasePanel ...>` element, no per-column duplication |
| D-73 TraceWorkspacePage gates on scenario string | TraceWorkspacePage.tsx:392 `scenario === "tool_discovery"` | HONORED |

### Gaps Summary

No blocking gaps. All 16 must-haves verified against the codebase. All 9 artifacts present and substantive. All 9 key links wired. All 5 data-flow traces flow real backend data through to user-visible rendering. All 6 critical pitfalls (#1, #2, #5, #6, D-72, D-73) honored. Backend pytest 345/345 and frontend vitest 291/291 reported by orchestrator.

The `human_needed` status is driven by the four human-verification items in the frontmatter:

1. ROADMAP success criterion #1 explicitly demands the scenario run on **both** MCP and A2A protocols. Backend pytest covers mcp mode emission + search_docs fallback. The A2A protocol path (a2a_remote_discovery emit, agent-card join to skills) shares the same wire-level event types and is exercised by component-level vitest fixtures, but no end-to-end pytest case asserts a real run in `a2a` mode produces an `a2a_remote_discovery` event with populated agent_card.skills. A live UI run on the A2A protocol is the smallest extra check that closes this concern.
2. ROADMAP success criterion #2 requires the panel render "before any execution-phase events" — programmatic checks confirm DOM ordering (panel above explorer Grid block) but visual confirmation that the timeline reads correctly is a UX judgment.
3. The compare-mode D-72 contract (single full-width panel above dual-column Grid) is grep-confirmed but the live visual layout is best confirmed by eye.
4. The stale-cache fallback warning highlight is unit-tested but its end-to-end UX (does the operator see the divergence story clearly?) needs human review.

These are surface-area confirmations, not implementation gaps. The phase is functionally complete and the goal is achieved in code; the human items are the standard visual/UX confirmations that cannot be reduced to grep or unit tests.

---

_Verified: 2026-05-04T16:14:00Z (human UAT completed)_
_Verifier: Claude (gsd-verifier) + human UAT (Shivansh Choudhary)_
