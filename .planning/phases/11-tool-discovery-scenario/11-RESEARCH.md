# Phase 11: Tool Discovery Scenario - Research

**Researched:** 2026-04-30
**Domain:** Frontend MUI panel + backend seed-data scenario + trace-event filtering for MCP/A2A discovery surfacing
**Confidence:** HIGH

## Summary

Phase 11 ships two requirements (DISC-01, DISC-02) by combining (1) a JSON-row addition to `src/a2a_vs_mcp/data/seeds/scenarios.json` (`TICKET-1013`, `tool_discovery` scenario, advanced) plus a new customer in `customers.json`, and (2) a new `DiscoveryPhasePanel.tsx` MUI Accordion mounted above `TraceExplorer` on `TraceWorkspacePage` (gated on `scenario === "tool_discovery"`) and full-width above the dual columns on `CompareTracesPanel`. Both `tool_discovery` events (MCP via `mcp/client.py:78`, A2A re-emit via `a2a/remote_broker.py:237-243`) are already emitted today — Phase 11 is **purely a consumer**, no schema change.

The two failure modes (stale-capability-cache + unknown-tool-fallback) are exercised **naturally** by D-68's design: an unknown product/SKU in the seeded query forces the agent to discover tools, find no match, and fall back to `search_docs`. The existing `tool_transport_fallback` event already provides the wire signal for the panel's failure-row highlight (UI-SPEC line 122-123). No new event_type, no `FailureConfig` extension required for the locked scope.

The single non-trivial frontend refactor is extracting `JsonTree` from `ProtocolEnvelopeDrawer.tsx` (lines 80-155) into `frontend/src/lib/trace/JsonTree.tsx` so both the drawer AND the new panel can import it. UI-SPEC mandates "extract, do not duplicate" (line 145).

**Primary recommendation:** Land 5 plans in 3 waves: Wave 0 = JsonTree extraction (refactor-only, safe), Wave 1 = backend scenario seed + customer + tests in parallel with frontend `DiscoveryPhasePanel.tsx` + types, Wave 2 = mount-site wiring (TraceWorkspacePage gate + CompareTracesPanel) + tests.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Seed `tool_discovery` scenario row | Backend / Storage (JSON) | — | `DemoRepository` reads `seeds/scenarios.json` verbatim — pure data add (PROJECT.md line 117 confirms: "TICKET-1011 + TICKET-1012 added with no infra change") |
| Net-new customer | Backend / Storage (JSON) | — | `customers.json` seed; SQLite rebuild auto-triggers via `_seed_signature()` hash mismatch (`dataset.py:30-43`) |
| Failure-mode emission | Backend / Runtime | — | `MCPClient.__init__` already records `tool_transport_fallback` on transport failure (`mcp/client.py:69-75`); no new emission needed when the SKU is genuinely unknown to the seeds |
| Trace-event filtering for discovery | Frontend / Client | — | Panel filters `events: TraceEvent[]` already passed from API into `TraceExplorer` — zero backend coupling |
| Side-by-side MCP/A2A render | Frontend / Client | — | Pure presentational; MUI `Grid` + `Accordion` |
| Scenario-gating mount | Frontend / Client | — | `searchParams.get("report")` → `detail.summary.scenario` already on `TraceWorkspacePage` |
| JsonTree shared helper | Frontend / Lib | — | Move from `components/traces/ProtocolEnvelopeDrawer.tsx` to `lib/trace/JsonTree.tsx`; both consumers import |

## Standard Stack

### Core (already in repo — no new deps)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@mui/material` | v5 | Accordion, Card, Grid, Chip, Typography for the panel | Project-wide standard (CLAUDE.md states "no Tailwind/shadcn"); UI-SPEC line 24 confirms |
| `@mui/icons-material` | v5 (Outlined variant) | `ExpandMoreIcon`, `WarningAmberRoundedIcon` for failure-signal | Convention matches `ProtocolEnvelopeDrawer` + `TraceExplorer` (UI-SPEC line 25) |
| `react-router-dom` | v6 | `useSearchParams` for `?scenario=` gating already in place | TraceWorkspacePage already uses it (line 17, 51) |
| Pydantic / dataclasses | stdlib | `SupportTicket` dataclass already accepts new row verbatim | `schemas.py:18-26` shows existing shape |
| `pytest` | (project default) | Backend tests for new scenario | CLAUDE.md command: `pytest` |
| `vitest` | (project default) | Frontend component tests | CLAUDE.md command: `cd frontend && npm test`; existing `RunWorkspacePage.test.tsx` is a model |

### Supporting (existing helpers — reuse, do not rebuild)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `protocolColor`, `toneColor` | local | Color tokens for MCP (#1976d2), A2A (#7b1fa2), warning stripe | Imported from `frontend/src/lib/trace/eventColors.ts` (verified — file exists, exports both maps) |
| `traceEventProtocol`, `isA2AEvent` | local | Filter helpers already used in `TraceExplorer.tsx:69, 81` | Reuse in panel for symmetric protocol detection |
| `JsonTree` | local (after extraction) | Render tool `inputSchema` and agent `skills` payloads | Currently inside `ProtocolEnvelopeDrawer.tsx:80-155` — extract to `lib/trace/JsonTree.tsx` |
| `FIELD_ANNOTATIONS` | local | Spec-field tooltips in JsonTree | `ProtocolEnvelopeDrawer.tsx:26-45` — extract alongside JsonTree |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Reusing `tool_transport_fallback` for failure highlight | New `tool_discovery_failure` event_type | New event = backend schema bump + migrator entry + Phase 6 audit. Reuse keeps blast radius zero. |
| MUI Accordion for collapsible | Custom `<details>` element | Accordion already in use across codebase (`TraceExplorer.tsx`); consistent UX + a11y baked in |
| Extending `FailureConfig` for cache-staleness toggle | Always-on for `tool_discovery` scenario only | UI-SPEC + CONTEXT.md note "scenario-bound" path is preferred; FailureConfig touch would ripple into race tests |

**Installation:** No new packages required.

**Version verification:** No new dependencies — verification N/A. Existing MUI v5 + react-router v6 + vitest are already pinned in `frontend/package.json` (assumed verified by Phase 8 + 10 frontend work which used same stack).

## Architecture Patterns

### System Architecture Diagram

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          USER (operator)                                  │
└──────────────────────────────────────────────────────────────────────────┘
                                   │
                ┌──────────────────┴──────────────────┐
                │ /run RunWorkspacePage selects        │
                │ scenario="tool_discovery"            │
                ▼                                      │
   ┌──────────────────────┐                           │
   │  POST /api/run        │                          │
   │  (existing endpoint)  │                          │
   └──────────┬────────────┘                          │
              │                                        │
              ▼                                        │
   ┌──────────────────────────────────┐                │
   │  DemoPlatform.run(mode, ticket)  │                │
   │   ─ TICKET-1013, unknown SKU     │                │
   └──────────┬───────────────────────┘                │
              │                                        │
       ┌──────┴──────┐                                 │
       │             │                                 │
       ▼             ▼                                 │
   ┌────────┐   ┌─────────────┐                        │
   │MCPClient│   │RemoteA2ABroker│                     │
   │ __init__│   │  .discover()  │                     │
   └───┬────┘   └────┬─────────┘                       │
       │             │                                  │
       │ records     │ records                          │
       ▼             ▼                                  │
   ┌─────────────────────────────────┐                 │
   │ TraceRecorder (events list)      │                │
   │   ─ tool_discovery (MCP)         │                │
   │   ─ a2a_remote_discovery         │                │
   │   ─ tool_discovery (re-emit,     │                │
   │     remote_agent=...)            │                │
   │   ─ tool_transport_fallback      │                │
   │     (when triggered)             │                │
   │   ─ tool_call (search_docs       │                │
   │     fallback for unknown SKU)    │                │
   └────────────┬────────────────────┘                 │
                │ trace.save() → JSON                  │
                ▼                                       │
   ┌──────────────────────────┐                        │
   │ data/<user>/traces/      │                        │
   │   <ticket_id>_<mode>.json│                        │
   └──────────┬───────────────┘                        │
              │                                         │
              │ GET /api/reports/<name>                 │
              ▼                                         │
   ┌─────────────────────────────────────┐             │
   │ TraceWorkspacePage.tsx               │            │
   │  ─ detail.summary.scenario           │◄───────────┘
   │  ─ detail.results[i].trace[]         │
   └────────────┬────────────────────────┘
                │
                │ if scenario === "tool_discovery"
                ▼
   ┌──────────────────────────────────────────┐
   │ DiscoveryPhasePanel.tsx                   │
   │   filter events:                           │
   │     mcpEvents = e.event_type ===           │
   │       "tool_discovery" && !e.remote_agent  │
   │     a2aEvents = e.event_type ===           │
   │       "tool_discovery" && e.remote_agent   │
   │   render two-column Grid (MUI)             │
   │   ─ MCP: Card per tool from event.tools[]  │
   │   ─ A2A: Card per agent from               │
   │     event.a2a_agent_card                   │
   │   ─ failure-row: tool_transport_fallback   │
   │     OR requested_transport !== transport   │
   └──────────────────────────────────────────┘
                │
                ▼
   ┌──────────────────────────────────────────┐
   │ <TraceExplorer events={result.trace} />   │
   │ (unchanged — execution-phase events)      │
   └──────────────────────────────────────────┘
```

### Recommended Project Structure

```
src/a2a_vs_mcp/data/seeds/
├── scenarios.json          # APPEND: TICKET-1013 row
├── customers.json          # APPEND: net-new customer (CUST-005 or similar)

frontend/src/lib/trace/
├── JsonTree.tsx            # NEW: extracted from ProtocolEnvelopeDrawer
├── eventColors.ts          # unchanged
└── utils.ts                # unchanged

frontend/src/features/traces/components/
└── DiscoveryPhasePanel.tsx # NEW: MUI Accordion + 2-col Grid

frontend/src/features/traces/__tests__/
└── DiscoveryPhasePanel.test.tsx  # NEW: vitest

tests/
└── test_tool_discovery_scenario.py  # NEW: pytest
```

### Pattern 1: JSON-Row Scenario Add (no infra change)

**What:** New scenarios are added by appending one object to `seeds/scenarios.json`. `DemoRepository._seed_signature()` SHA-256s the file, sees mismatch, rebuilds SQLite. `load_scenarios()` returns it as a `SupportTicket`.
**When to use:** Whenever a scenario is data-only (no new tool, no new agent). Phase 11 fits this pattern verbatim per CONTEXT.md and PROJECT.md line 117.
**Example:**
```json
// Source: src/a2a_vs_mcp/data/seeds/scenarios.json (existing row TICKET-1012, lines 156-169)
{
  "scenario": "tool_discovery",
  "ticket_id": "TICKET-1013",
  "customer_id": "CUST-005",
  "title": "Discovery: Unknown Product Triage",
  "difficulty": "advanced",
  "tags": ["discovery", "fallback"],
  "query": "I bought a NebulaSync Hub last month and it won't pair. What should I try?",
  "talking_point": {
    "headline": "Discovery before answer",
    "sentence": "MCP lists tools then falls back to search_docs; A2A lists agent skills then escalates to documentation specialist.",
    "callout": "Watch the discovery phase fire BEFORE any execution-phase tool_call."
  }
}
```

### Pattern 2: Trace-Event Mirror in A2A Path

**What:** When `RemoteA2ABroker` receives results from a remote A2A specialist, it copies that specialist's MCP-side `tool_discovery` events back into the local trace, tagging them with `remote_agent=<agent_id>` and `remote_trace=true`.
**When to use:** Already happens automatically. The panel's A2A column simply filters for `event.remote_agent` truthy.
**Example:**
```python
# Source: src/a2a_vs_mcp/a2a/remote_broker.py:234-244
def _record_remote_server_events(self, agent_id: str, events: list[dict[str, Any]]) -> None:
    for event in events:
        event_type = event.get("event_type")
        if event_type in {"tool_discovery", "tool_call", "tool_error", "tool_transport_fallback"}:
            copied = {key: value for key, value in event.items() if key not in {"index", "timestamp_ms", "event_type"}}
            self.trace.record(
                event_type,
                **copied,
                remote_agent=agent_id,
                remote_trace=True,
            )
```

### Pattern 3: MUI Accordion + Grid Two-Column (matches UI-SPEC)

**What:** Top-level `Accordion` with `defaultExpanded`, header `AccordionSummary`, body `AccordionDetails > Grid container > 2× Grid size={{xs:12, md:6}}`.
**When to use:** Per UI-SPEC line 105-117 — exactly this layout for `DiscoveryPhasePanel`. Already used by `TraceExplorer.tsx` and `ProtocolEnvelopeDrawer` for nested layouts.
**Example:** UI-SPEC §Component Inventory lines 92-123 specifies the exact structure. Inputs:
```ts
interface DiscoveryPhasePanelProps {
  mcpEvents: TraceEvent[];   // pre-filtered by mount site
  a2aEvents: TraceEvent[];   // pre-filtered by mount site
  scenario: string;          // gate (TraceWorkspacePage caller checks; CompareTracesPanel always-on)
  defaultExpanded?: boolean; // default: true (researcher discretion)
}
```

### Anti-Patterns to Avoid

- **Duplicating JsonTree inside DiscoveryPhasePanel** — UI-SPEC line 145 explicitly forbids this. Extract once to `lib/trace/JsonTree.tsx`.
- **Adding a new event_type for cache-stale signal** — `tool_transport_fallback` already exists and `requested_transport !== transport` already encodes the divergence on every `tool_discovery` event. Reuse.
- **Adding a `FailureConfig` toggle for the discovery scenario** — D-68 deliberately makes the failure modes data-driven (unknown SKU forces them organically). A FailureConfig switch would be redundant + couples Phase 11 to race semantics.
- **Mounting DiscoveryPhasePanel always-on TraceWorkspacePage** — D-73 locked: gate on `scenario === "tool_discovery"`. Other scenarios' UX must not change.
- **Coupling A2A panel column to MCP run** — D-71 locked: sibling placeholder is static hint text only ("Run on {A2A|MCP} to populate").

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON pretty-print with field tooltips | Custom JSON renderer | Extract `JsonTree` from `ProtocolEnvelopeDrawer.tsx:80-155` to `lib/trace/JsonTree.tsx` | Already battle-tested with `FIELD_ANNOTATIONS`, recursive Object/Array handling, MUI tooltips |
| Protocol color mapping | Hardcoded hex | `protocolColor.mcp` / `protocolColor.a2a` from `eventColors.ts` | Single source of truth used by 5+ existing components |
| Tone color (warning stripe) | Hardcoded `#ed6c02` | `toneColor.warning` from `eventColors.ts` | Same map; consistency with race-demo failure tags |
| Scenario data shape validation | Bespoke check | `SupportTicket` dataclass in `schemas.py:18-26` | `load_scenarios()` already constructs it from JSON row verbatim |
| SQLite rebuild on seed change | Manual rebuild step | `DemoRepository._needs_rebuild()` SHA-256 hash check (`dataset.py:36-43`) | Auto-triggered on next instantiation — zero ceremony |
| Collapsible UI | Custom `<details>` + state | MUI `Accordion` | A11y, keyboard, animation, `prefers-reduced-motion` baked in |

**Key insight:** This phase is overwhelmingly a "stitch existing primitives together" job. The single net-new component (`DiscoveryPhasePanel`) is a thin presentational shell over already-emitted data and already-defined visual tokens.

## Runtime State Inventory

This phase is **mostly greenfield (additive seed row + new component)** with **one runtime-state concern: the SQLite cache.**

| Category | Items Found | Action Required |
|----------|-------------|------------------|
| Stored data | `data/<user>/support_demo.db` (per-user SQLite cache) and `data/<user>/seed_manifest.json` (SHA-256 manifest) — both keyed off `seeds/*.json` content hash. Adding a row to `scenarios.json` and `customers.json` will cause a hash mismatch. | **None — auto-handled.** `DemoRepository._needs_rebuild()` (`dataset.py:36-43`) sees mismatch, re-runs `_rebuild_sqlite()` on next platform instantiation. No data migration required. |
| Live service config | None. Demo is fully local; no remote services hold scenario state. | None — verified by inspecting `DemoPlatform.__init__` (`platform.py:23-63`) which only reads local files + env vars. |
| OS-registered state | None. No Task Scheduler, launchd, systemd, pm2 entries reference scenario IDs. | None. |
| Secrets/env vars | None. New scenario uses no new credentials. `REMOTE_A2A_TOKEN` etc. unaffected. | None. |
| Build artifacts / installed packages | None. No compiled or generated artifacts reference `TICKET-1013` or the new customer. | None. |

**Edge case worth a 30-second check:** if a developer's local `data/<user>/support_demo.db` was built on the OLD seed manifest, the **first** post-merge platform instantiation will rebuild SQLite. This is normal behavior — no documentation needed unless a reviewer flags it. (Verified: `_ensure_sqlite()` runs unconditionally on `__init__`.)

## Common Pitfalls

### Pitfall 1: `_PHASE_MAP` does NOT tag `tool_discovery` events as `phase: "discovery"`

**What goes wrong:** A planner reading `TraceEvent.phase` from `frontend/src/lib/types/api.ts:51` (`phase?: "discovery" | "execution"`) might assume `tool_discovery` events arrive with `phase === "discovery"` — they do not.
**Why it happens:** `TraceRecorder._PHASE_MAP` (`trace.py:24-27`) only maps `agent_register` and `capability_advertise` to `"discovery"`. `tool_discovery` falls through to the default `"execution"` (`trace.py:48`).
**How to avoid:** **DO NOT filter on `event.phase === "discovery"`** for the panel. Filter on `event.event_type === "tool_discovery"` instead. The panel name "Discovery Phase" is a UX label, not a `phase` field match.
**Warning signs:** If panel renders empty when MCP run clearly emitted tool_discovery, this is the bug.

### Pitfall 2: A2A re-emit shape is a copy, not a reshape

**What goes wrong:** Assuming the A2A column needs a different event_type or specially-shaped agent-card payload.
**Why it happens:** The remote_broker copies the specialist's MCP `tool_discovery` event verbatim and just adds `remote_agent` + `remote_trace` tags (`remote_broker.py:237-243`).
**How to avoid:** Filter A2A events as `event.event_type === "tool_discovery" && event.remote_agent`. The agent-card payload comes from a SEPARATE event (`a2a_remote_discovery` at `remote_broker.py:90-99`, which carries `a2a_agent_card`).
**Warning signs:** If the A2A column shows tool lists but no agent-card metadata, you're filtering only `tool_discovery` and missing `a2a_remote_discovery`. The panel needs **both**: `tool_discovery` (with `remote_agent`) for the per-agent tool list, and `a2a_remote_discovery` for the agent-card skills/capabilities. **Recommend adjusting filter contract before plan-time** (see Open Question #1).

### Pitfall 3: `MCPClient.__init__` swallows fallback errors silently for non-`in_process` transports

**What goes wrong:** When a transport other than `in_process` fails discovery, `MCPClient` records `tool_transport_fallback` and silently retries with `in_process` (`mcp/client.py:62-76`). The `tool_discovery` event that DOES land has `transport: "in_process"` and `requested_transport: "<original>"`. Reviewers may not realize the fallback happened.
**Why it happens:** Designed-in resilience. UI-SPEC line 122-123 already accounts for this — failure-row highlights when `requested_transport !== transport`.
**How to avoid:** The panel must inspect both `event.requested_transport` and `event.transport` and highlight when they diverge. Tooltip copy already drafted in UI-SPEC line 175.
**Warning signs:** None — this is feature, not bug. Just don't filter it out.

### Pitfall 4: `mcp_capability_discovery` is a separate, additional event

**What goes wrong:** Building the panel from the assumption that all MCP discovery info is in one event — it isn't. After `tool_discovery`, MCPClient also records `mcp_capability_discovery` with `resources` and `prompts` lists (`mcp/client.py:91-102`).
**Why it happens:** MCP exposes three primitives (tools, resources, prompts) and the platform records each separately.
**How to avoid:** **Phase 11 scope per UI-SPEC line 100 says "Tool Catalog"** — research recommends panel filters ONLY `tool_discovery` (not `mcp_capability_discovery`). Resources/prompts are out of scope. Document this so a future enhancement doesn't think it's a regression.
**Warning signs:** If a reviewer asks "where are the MCP resources?", the answer is "deferred — Phase 11 surfaces tools only".

### Pitfall 5: `JsonTree` extraction must not break `ProtocolEnvelopeDrawer` import path

**What goes wrong:** Moving `JsonTree` to `lib/trace/JsonTree.tsx` and forgetting to update the drawer's import causes a build failure across all trace pages.
**Why it happens:** `JsonTree` is currently a local function declaration inside the same file (`ProtocolEnvelopeDrawer.tsx:80-155`).
**How to avoid:** Extraction plan must (1) move `JsonTree` AND `FIELD_ANNOTATIONS` AND `annotate()` helper, (2) export named, (3) update drawer import, (4) run `cd frontend && npm test` to confirm no regression. Suggest a Wave 0 plan that ONLY does the refactor and ships green tests before any panel work begins.
**Warning signs:** vitest fails on `ProtocolEnvelopeDrawer.test.tsx` (if exists) or any test that mounts the drawer.

### Pitfall 6: TraceWorkspacePage's `detail` may be null on first render

**What goes wrong:** Mounting `DiscoveryPhasePanel` based on `detail.summary.scenario` while `detail` is still loading throws.
**Why it happens:** `TraceWorkspacePage.tsx:47` initializes `detail` as `null` and populates it via async fetch.
**How to avoid:** Gate at mount site with `detail?.summary?.scenario === "tool_discovery"` — same null-safe accessor pattern used at `TraceWorkspacePage.tsx:401`.
**Warning signs:** Console TypeError "Cannot read property 'summary' of null".

## Code Examples

Verified patterns from existing source:

### Example 1: Adding a Scenario Row (CONTEXT-locked shape)

```json
// Source: src/a2a_vs_mcp/data/seeds/scenarios.json (TICKET-1011 verified pattern, lines 142-155)
// New row to append:
{
  "scenario": "tool_discovery",
  "ticket_id": "TICKET-1013",
  "customer_id": "CUST-005",
  "title": "Discovery: Unknown Product Triage",
  "difficulty": "advanced",
  "tags": ["discovery", "fallback"],
  "query": "I just bought a NebulaSync Hub. It won't pair with my devices. Where do I start?",
  "talking_point": {
    "headline": "Discovery before answer",
    "sentence": "MCP enumerates tools and falls back to search_docs when no warranty/order matches; A2A enumerates agent skills and escalates to documentation specialist.",
    "callout": "Discovery-phase events fire BEFORE any execution-phase tool_call."
  }
}
```

### Example 2: New Customer Row

```json
// Source: src/a2a_vs_mcp/data/seeds/customers.json (verified pattern, lines 1-26)
// New row to append:
{
  "customer_id": "CUST-005",
  "name": "Casey Rivera",
  "email": "casey@example.com",
  "segment": "consumer"
}
```
> Note: NebulaSync Hub is intentionally NOT in `warranties.json` or `orders.json` — that's what forces the discovery + fallback path.

### Example 3: Frontend Filter for MCP/A2A Discovery Events

```tsx
// Source: derived from frontend/src/components/traces/TraceExplorer.tsx:80-89
//        and src/a2a_vs_mcp/a2a/remote_broker.py:237-243
import { useMemo } from "react";
import type { TraceEvent } from "../../lib/types/api";

function partitionDiscoveryEvents(events: TraceEvent[]) {
  return useMemo(() => {
    const mcpEvents = events.filter(
      (e) => e.event_type === "tool_discovery" && !e.remote_agent
    );
    const a2aEvents = events.filter(
      (e) => e.event_type === "tool_discovery" && Boolean(e.remote_agent)
    );
    // OPTIONAL (see Open Question #1): also collect a2a_remote_discovery
    const agentCards = events.filter(
      (e) => e.event_type === "a2a_remote_discovery"
    );
    return { mcpEvents, a2aEvents, agentCards };
  }, [events]);
}
```

### Example 4: Mount-Site Gate (TraceWorkspacePage)

```tsx
// Source: frontend/src/features/traces/TraceWorkspacePage.tsx:391-406 (mount point)
// Insert ABOVE the existing <Grid size={{ xs: 12 }}><Stack> at line 391:
{detail?.summary?.scenario === "tool_discovery" ? (
  <Grid size={{ xs: 12 }}>
    <DiscoveryPhasePanel
      mcpEvents={mcpEvents}
      a2aEvents={a2aEvents}
      scenario={detail.summary.scenario}
    />
  </Grid>
) : null}
```

### Example 5: Mount-Site (CompareTracesPanel — always-on per D-72)

```tsx
// Source: frontend/src/features/compare/CompareTracesPanel.tsx:97 (insert ABOVE the dual-column Grid)
// One panel above, full-width:
<Grid size={{ xs: 12 }}>
  <DiscoveryPhasePanel
    mcpEvents={[...resultA?.trace ?? [], ...resultB?.trace ?? []].filter(
      (e) => e.event_type === "tool_discovery" && !e.remote_agent
    )}
    a2aEvents={[...resultA?.trace ?? [], ...resultB?.trace ?? []].filter(
      (e) => e.event_type === "tool_discovery" && Boolean(e.remote_agent)
    )}
    scenario="tool_discovery"  /* CompareTracesPanel doesn't track scenario string; UI-SPEC line 130 says "no gate" here */
  />
</Grid>
```

### Example 6: Test Pattern (pytest scenario load + frontend vitest)

```python
# Source: tests/test_demo_modes.py existing pattern (assumed — file present)
# New test:
def test_tool_discovery_scenario_loads():
    repo = DemoRepository(project_root=Path("."))
    scenarios = repo.load_scenarios()
    assert "tool_discovery" in scenarios
    ticket = scenarios["tool_discovery"]
    assert ticket.ticket_id == "TICKET-1013"
    assert ticket.difficulty == "advanced"
    assert "discovery" in ticket.tags and "fallback" in ticket.tags
    assert ticket.customer_id == "CUST-005"
```

```tsx
// Source: frontend/src/features/run-workspace/RunWorkspacePage.test.tsx pattern
// New test for DiscoveryPhasePanel:
import { render, screen } from "@testing-library/react";
import { DiscoveryPhasePanel } from "../components/DiscoveryPhasePanel";

it("renders MCP tools side-by-side with A2A placeholder when only MCP events present", () => {
  render(
    <DiscoveryPhasePanel
      mcpEvents={[{ index: 1, event_type: "tool_discovery", timestamp_ms: 0,
                    server: "...db_server", tools: ["get_order"], protocol: "official_mcp_sdk",
                    transport: "in_process", requested_transport: "in_process" }]}
      a2aEvents={[]}
      scenario="tool_discovery"
    />
  );
  expect(screen.getByText("Discovery Phase")).toBeInTheDocument();
  expect(screen.getByText("MCP — Tool Catalog")).toBeInTheDocument();
  expect(screen.getByText("Run on A2A to populate")).toBeInTheDocument();
});
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Trace events as flat list, no phase tagging | `phase: "discovery" \| "execution"` field on every event | Phase 2 (v1.0) | But `_PHASE_MAP` only covers 2 event types — see Pitfall #1 |
| `FailureConfig` for race-only fault injection | Same `FailureConfig` reused for v1 scenarios | Phases 6-7 | Phase 11 deliberately does NOT extend this (CONTEXT.md `<specifics>`) |
| Inline JSON pretty-print | Shared `JsonTree` with field tooltips | Phase 4-5 (Comparison UI) | Phase 11 finalizes by extracting to `lib/trace/` |
| Single panel above trace explorer | Same pattern, gated by scenario string | Phase 11 (this) | New convention: scenario-bound rich panels |

**Deprecated/outdated:**
- None for this phase. All target patterns are current as of 2026-04-30.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | New customer ID `CUST-005` is unused. | Code Examples | LOW — can be verified by `grep CUST-005 src/a2a_vs_mcp/data/seeds/`. Planner should confirm. |
| A2 | `NebulaSync Hub` is not in any seed. | Code Examples | LOW — same grep verification. Choose any unmapped product if collision found. |
| A3 | `cd frontend && npm test` is `vitest` (not jest). | Standard Stack | LOW — CLAUDE.md says `cd frontend && npm test`; existing test files use vitest-style imports based on Phase 8 patterns. Planner should verify by reading `frontend/package.json` `scripts.test`. |
| A4 | `DiscoveryPhasePanel` mount on `CompareTracesPanel` should be always-on (UI-SPEC line 130 says "no scenario string gate needed"). | Mount-site code | MEDIUM — D-72 says "single panel above both columns." UI-SPEC says "always shown when results contain tool_discovery events." If both runs are non-discovery scenarios, panel renders empty (which is fine per UI-SPEC empty-state copy line 177). Planner can choose: render-empty vs. presence-gated. **Recommend: presence-gated** (`if any mcp/a2a tool_discovery event present`) to keep other compare flows clean. |
| A5 | Extraction of `JsonTree` won't break unrelated tests because no other component imports `JsonTree` directly. | Pitfalls | LOW — `JsonTree` is currently a local function inside `ProtocolEnvelopeDrawer.tsx`, not exported. Verified by grep on the codebase (`JsonTree` only appears in that one file). Wave 0 refactor + run-tests guard mitigates. |

## Open Questions

1. **Should `DiscoveryPhasePanel` consume `a2a_remote_discovery` events too (for agent-card skills/capabilities), or rely entirely on `tool_discovery` re-emit + `remote_agent` tag?**
   - What we know: `tool_discovery` re-emit (`remote_broker.py:237`) carries the **tool list** the remote agent exposes via MCP. The agent-card metadata (skills, name, capabilities) lives in a separate event `a2a_remote_discovery` (`remote_broker.py:90-99`) with `a2a_agent_card` payload.
   - What's unclear: UI-SPEC line 116 says "agent name (`body2`, weight 600), skills list as `Chip` row" — this requires `a2a_agent_card.skills`. That data is on `a2a_remote_discovery`, not on `tool_discovery`.
   - Recommendation: **Panel should accept BOTH event types**. Treat `a2a_remote_discovery` as the agent-card source, and `tool_discovery` (with `remote_agent`) as the per-agent tool list. Document the props contract as `mcpEvents`, `a2aEvents` (= union of both for the A2A column), or split into `a2aAgentCards` + `a2aTools`. **Prefer**: `a2aEvents` accepts both, and the panel internally joins by `remote_agent === a2a_agent_card.agent_id`.

2. **Default state of the Accordion: expanded or collapsed?**
   - What we know: UI-SPEC says `defaultExpanded={true}` (researcher discretion). CONTEXT.md `<decisions>.Claude's Discretion` flags this as open.
   - What's unclear: User feedback may prefer collapsed for "discovery is supplementary" framing.
   - Recommendation: **Default expanded (`true`)** — the whole point of Phase 11 is to surface discovery as a first-class UI element. Hiding it by default contradicts the goal. Expose `defaultExpanded` prop for future override.

3. **Should the panel mount on `ReportDetailPage` (third TraceExplorer site at line 260)?**
   - What we know: CONTEXT.md `<decisions>.Claude's Discretion` says "default = do not mount unless researcher finds compelling reason."
   - What's unclear: Will demo viewers click into a saved report's detail view and expect the panel to be there?
   - Recommendation: **Do NOT mount on ReportDetailPage in Phase 11.** TraceWorkspacePage already opens by default and is the primary review surface. Saved-report detail can defer to Phase 12 (annotated diff) which has different rendering needs anyway. Documenting "out of scope" is cheaper than building it. If user requests in review, plan-checker can revisit.

4. **Talking-point copy for the new scenario.**
   - What we know: CONTEXT.md says researcher drafts; user did not pin verbatim text.
   - Recommendation drafted in Code Examples §1 above. Planner can refine; does not block the plan.

## Environment Availability

This phase is **purely code/config** — no external runtime, no new tools. SKIPPED per Step 2.6 fallback.

For completeness, all needed tooling is already used by Phases 6-10:
- Python 3.11+ ✓ (existing project)
- pytest ✓ (existing)
- node + npm + vitest ✓ (frontend already shipped)

## Validation Architecture

> Skipped per phase context: "Validation Architecture (Nyquist): Disabled for this project — skip the Validation Architecture section."

## Project Constraints (from CLAUDE.md)

The following CLAUDE.md directives constrain Phase 11 implementation:

- **Frontend stack:** React + Material UI (NOT Tailwind/shadcn). UI-SPEC + this research align.
- **Backend stack:** Python/FastAPI; tests via `pytest`.
- **Frontend tests:** `cd frontend && npm test`.
- **Browsing tool:** `/browse` from gstack — NOT `mcp__claude-in-chrome__*`. Not needed for this phase (no live browsing required).
- **Memory + graphify:** project has `claude mem` and `graphify-out/`. Plan-time agents may consult these; not strictly required.
- **Skill routing:** product/architecture/QA/review skills are available — planner is free to invoke `/plan-eng-review` after producing PLAN.md.

## Sources

### Primary (HIGH confidence) — verified in-repo

- `src/a2a_vs_mcp/dataset.py:17-120` — `DemoRepository`, `_seed_signature`, `load_scenarios`, `SupportTicket` construction
- `src/a2a_vs_mcp/schemas.py:18-26` — `SupportTicket` dataclass shape
- `src/a2a_vs_mcp/mcp/client.py:62-104` — `tool_discovery`, `tool_transport_fallback`, `mcp_capability_discovery` emission paths
- `src/a2a_vs_mcp/a2a/remote_broker.py:56-117, 234-244` — A2A discovery + remote-event mirroring (`remote_agent` tag)
- `src/a2a_vs_mcp/trace.py:1-80` — `TraceRecorder`, `_PHASE_MAP` (Pitfall #1 source)
- `src/a2a_vs_mcp/data/seeds/scenarios.json` — 12 existing scenarios (TICKET-1001..1012); shape verified
- `src/a2a_vs_mcp/data/seeds/customers.json` — 4 existing customers; shape verified
- `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx:26-155, 65-68` — JsonTree, FIELD_ANNOTATIONS, tool_discovery payload handling
- `frontend/src/components/traces/TraceExplorer.tsx:1-100` — events filter pattern, MUI Accordion convention
- `frontend/src/lib/trace/eventColors.ts` — `protocolColor`, `toneColor`, `failureTagColor`
- `frontend/src/lib/types/api.ts:34-56` — `TraceEvent` interface (`phase` field, open-ended `[key: string]: unknown`)
- `frontend/src/features/traces/TraceWorkspacePage.tsx:391-406` — mount-point #1
- `frontend/src/features/compare/CompareTracesPanel.tsx:97-139` — mount-point #2
- `frontend/src/features/run-workspace/RunWorkspacePage.tsx:434-447` — scenario picker pattern (`Select` with MenuItems from scenarios list)
- `.planning/phases/11-tool-discovery-scenario/11-CONTEXT.md` — D-67..D-73 locked decisions
- `.planning/phases/11-tool-discovery-scenario/11-UI-SPEC.md` — design contract (4 PASS / 2 FLAG)
- `.planning/REQUIREMENTS.md:67-70` — DISC-01, DISC-02 acceptance text
- `.planning/ROADMAP.md:124-132` — Phase 11 goal + success criteria

### Secondary (MEDIUM confidence)

- None required — all claims verified in-repo.

### Tertiary (LOW confidence)

- None — research is fully grounded in the codebase.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| DISC-01 | New `tool_discovery` scenario in `DemoRepository` exercising MCP tool discovery + A2A agent-card discovery; failure modes = stale capability cache + unknown-tool fallback | Pattern 1 (JSON-row scenario add); Code Examples 1 + 2; D-68 design (unknown SKU forces both modes naturally — no `FailureConfig` extension needed); existing `tool_transport_fallback` event provides the wire signal (`mcp/client.py:69-75`) |
| DISC-02 | `DiscoveryPhasePanel.tsx` renders discovery phase as first-class section above trace explorer; tool catalog (MCP) + agent cards (A2A) side-by-side with timestamps | Pattern 3 (MUI Accordion + 2-col Grid); Code Examples 3-5 (filtering + mount-site gates per D-70..D-73); UI-SPEC §Component Inventory lines 92-132 specifies layout verbatim |

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already in repo, all helpers verified by grep
- Architecture: HIGH — both mount sites read directly from existing files; data flow traced end-to-end
- Pitfalls: HIGH — Pitfalls #1, #2, #4 are derived from reading current source; Pitfall #3 is feature-not-bug per UI-SPEC; Pitfall #5/6 are standard refactor/null-safety hygiene
- Open Questions: MEDIUM — Q1 (`a2a_remote_discovery` inclusion) is the most consequential; recommend planner addresses explicitly in PLAN.md before Wave 1 starts

**Research date:** 2026-04-30
**Valid until:** 2026-05-30 (estimate — code-and-data only; no fast-moving externals)

## RESEARCH COMPLETE
