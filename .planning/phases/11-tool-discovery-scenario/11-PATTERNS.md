# Phase 11: Tool Discovery Scenario - Pattern Map

**Mapped:** 2026-04-30
**Files analyzed:** 9 (3 NEW, 4 MODIFY, 2 NEW tests)
**Analogs found:** 9 / 9 (100% match coverage)

## File Classification

| New/Modified File | Type | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|------|-----------|----------------|---------------|
| `frontend/src/lib/trace/JsonTree.tsx` | NEW (refactor) | utility / lib component | recursive transform | extracted from `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx:25-50, 80-155` | exact (extract-in-place) |
| `frontend/src/components/traces/DiscoveryPhasePanel.tsx` | NEW | component (presentational) | request-response (filter + render) | `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` (chrome) + `frontend/src/components/traces/TraceExplorer.tsx` (Accordion + Grid + Card stats) | role-match (combined analog) |
| `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` | MODIFY | component refactor | unchanged | self (delete inline JsonTree, import from `../../lib/trace/JsonTree`) | self |
| `frontend/src/features/traces/TraceWorkspacePage.tsx` | MODIFY | mount-site wiring | request-response | self (insert `<Grid size={{ xs:12 }}>` block immediately above line 391's existing `<Grid>`) | self |
| `frontend/src/features/compare/CompareTracesPanel.tsx` | MODIFY | mount-site wiring | request-response | self (insert above line 97 dual-column `<Grid container>`) | self |
| `src/a2a_vs_mcp/data/seeds/scenarios.json` | MODIFY | scenario seed | data-only append | existing TICKET-1011 / TICKET-1012 rows (lines 142-169) | exact |
| `src/a2a_vs_mcp/data/seeds/customers.json` | MODIFY | customer seed | data-only append | existing CUST-001..CUST-004 rows (lines 1-26) | exact |
| `tests/test_tool_discovery_scenario.py` | NEW | test (pytest) | request-response | `tests/test_demo_modes.py` (`DemoModeTests.test_mcp_mode_uses_tool_calls`, lines 38-71) | exact |
| `frontend/src/components/traces/__tests__/DiscoveryPhasePanel.test.tsx` | NEW | test (vitest) | request-response | `frontend/src/features/run-workspace/RunWorkspacePage.test.tsx` (lines 1-80) | role-match |

---

## Pattern Assignments

### `frontend/src/lib/trace/JsonTree.tsx` (NEW — extract from ProtocolEnvelopeDrawer)

**Analog:** `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx`

**Move out (verbatim, then export named):** `FIELD_ANNOTATIONS` (lines 26-45), `annotate()` (lines 47-50), and `JsonTree` (lines 80-155).

**Imports needed in the new file:**
```typescript
import { Box, Tooltip } from "@mui/material";
```

**Public surface to export:**
```typescript
export const FIELD_ANNOTATIONS: Record<string, string> = { /* lines 26-45 verbatim */ };
export function annotate(key: string, parentKey?: string): string | undefined { /* lines 47-50 */ }
export function JsonTree(props: { data: unknown; depth?: number; parentKey?: string }) { /* lines 80-155 */ }
```

**Why:** UI-SPEC line 145 mandates "extract, do not duplicate." Both `ProtocolEnvelopeDrawer` and `DiscoveryPhasePanel` need the same renderer. Pitfall #5 (RESEARCH.md) flags that the drawer's import path must be updated in the same plan.

---

### `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` (MODIFY — consume extracted JsonTree)

**Action:** Remove lines 25-50 (FIELD_ANNOTATIONS + annotate) and 80-155 (JsonTree). Add named import:

```typescript
import { JsonTree } from "../../lib/trace/JsonTree";
```

The existing usage site at line 241 (`<JsonTree data={data} />`) requires no other change. The `Tooltip` import at line 13 of the original file may be removed if no longer used after the extraction.

---

### `frontend/src/components/traces/DiscoveryPhasePanel.tsx` (NEW — component)

**Analog (chrome):** `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` lines 217-247
**Analog (Accordion + Grid + Card stat strip):** `frontend/src/components/traces/TraceExplorer.tsx` lines 1-120

**Imports pattern** (model on `TraceExplorer.tsx:1-37`):
```typescript
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import { Box, Card, CardContent, Chip, Grid, Stack, Tooltip, Typography } from "@mui/material";
import { useMemo } from "react";

import { protocolColor, toneColor } from "../../lib/trace/eventColors";
import { JsonTree } from "../../lib/trace/JsonTree";
import type { TraceEvent } from "../../lib/types/api";
```

**Props interface** (verbatim from UI-SPEC lines 96-103):
```typescript
interface DiscoveryPhasePanelProps {
  mcpEvents: TraceEvent[];   // event_type === "tool_discovery" && !remote_agent
  a2aEvents: TraceEvent[];   // event_type === "tool_discovery" && Boolean(remote_agent)
  scenario: string;          // gate check (caller pre-gates on TraceWorkspacePage)
  defaultExpanded?: boolean; // default: true (per Open Question #2)
}
```

**Top-level Accordion structure** (mirror `TraceExplorer.tsx:91-112` Card+CardContent+Stack header pattern, but wrapped in MUI Accordion):
```typescript
<Accordion defaultExpanded={defaultExpanded ?? true}>
  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
    <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
      <Typography variant="h6">Discovery Phase</Typography>
      <Chip label={`${mcpEvents.length} tools discovered`} size="small"
            sx={{ color: protocolColor.mcp, borderColor: protocolColor.mcp }}
            variant="outlined" />
      <Chip label={`${a2aEvents.length} agents found`} size="small"
            sx={{ color: protocolColor.a2a, borderColor: protocolColor.a2a }}
            variant="outlined" />
    </Stack>
  </AccordionSummary>
  <AccordionDetails>
    <Grid container spacing={3}>
      <Grid size={{ xs: 12, md: 6 }}>{/* MCP column */}</Grid>
      <Grid size={{ xs: 12, md: 6 }}>{/* A2A column */}</Grid>
    </Grid>
  </AccordionDetails>
</Accordion>
```

**MCP column header pattern** (overline + 4px left-edge stripe):
```typescript
<Box sx={{ borderLeft: `4px solid ${protocolColor.mcp}`, pl: 2 }}>
  <Typography component="h3" variant="overline"
    sx={{ color: protocolColor.mcp, letterSpacing: "0.14em", display: "block" }}>
    MCP — Tool Catalog
  </Typography>
</Box>
```
> Pattern source: `ProtocolEnvelopeDrawer.tsx:221-225` for the overline+letterSpacing styling; UI-SPEC line 110 for the 4px stripe.

**Per-tool Card** (model on UI-SPEC lines 110-112; chrome from MUI theme `MuiCard` override per UI-SPEC line 121):
```typescript
<Card variant="outlined" sx={{ borderRadius: 2, mb: 1 }}>
  <CardContent sx={{ py: 1.5 }}>
    <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
      <Stack spacing={0.5}>
        <Typography variant="body2" fontWeight={600}>{toolName}</Typography>
        <Typography variant="body2" color="text.secondary">{toolDescription}</Typography>
      </Stack>
      <Typography variant="caption" color="text.secondary">+{relativeMs}ms</Typography>
    </Stack>
    {/* nested Accordion if inputSchema present */}
    {inputSchema ? (
      <Accordion disableGutters elevation={0} sx={{ mt: 1 }}>
        <AccordionSummary expandIcon={<ExpandMoreIcon fontSize="small" />}>
          <Typography variant="caption">Input Schema</Typography>
        </AccordionSummary>
        <AccordionDetails>
          <Box sx={{ background: "#1a2332", borderRadius: 1, p: 1.5,
                     fontFamily: "monospace", fontSize: "0.72rem",
                     color: "#e8e8e8", overflowX: "auto" }}>
            <JsonTree data={inputSchema} />
          </Box>
        </AccordionDetails>
      </Accordion>
    ) : null}
  </CardContent>
</Card>
```
> Code surface (`#1a2332`, monospace, 0.72rem) lifted verbatim from `ProtocolEnvelopeDrawer.tsx:228-240`.

**Failure-row highlight** (UI-SPEC line 122-123 — when `requested_transport !== transport`):
```typescript
const isFallback = event.requested_transport && event.requested_transport !== event.transport;
// apply to Card sx:
sx={{
  borderLeft: isFallback ? `2px solid ${toneColor.warning}` : undefined,
  borderRadius: 2, mb: 1,
}}
// and beside timestamp:
{isFallback ? (
  <Tooltip title="Stale capability cache — tool list returned no match for this query">
    <WarningAmberRoundedIcon fontSize="small" sx={{ color: toneColor.warning }} />
  </Tooltip>
) : null}
```

**Empty / placeholder column** (UI-SPEC lines 112-117, copy from D-71):
```typescript
{mcpEvents.length === 0 ? (
  <Box sx={{ py: 3, textAlign: "center" }}>
    <Typography variant="body2" color="text.disabled">Run on MCP to populate</Typography>
  </Box>
) : null}
```

**Relative-timestamp helper** (UI-SPEC line 119: `+{ms}ms` relative to first discovery event):
```typescript
const baseMs = useMemo(() => {
  const all = [...mcpEvents, ...a2aEvents];
  if (all.length === 0) return 0;
  return Math.min(...all.map((e) => e.timestamp_ms));
}, [mcpEvents, a2aEvents]);
const rel = (e: TraceEvent) => e.timestamp_ms - baseMs;
```

---

### `frontend/src/features/traces/TraceWorkspacePage.tsx` (MODIFY — mount #1)

**Analog:** self, lines 391-406.

**Read-first context** (lines 391-406):
```typescript
<Grid size={{ xs: 12 }}>
  <Stack spacing={2}>
    {visibleResults.map((result) => (
      <TraceExplorer
        key={`workspace-trace-${result.mode}`}
        events={result.trace}
        ...
      />
    ))}
  </Stack>
</Grid>
```

**Action** — insert ABOVE the line 391 Grid, gated on scenario (D-73):
```typescript
{detail?.summary?.scenario === "tool_discovery" ? (
  <Grid size={{ xs: 12 }}>
    <DiscoveryPhasePanel
      mcpEvents={visibleResults.flatMap((r) => r.trace).filter(
        (e) => e.event_type === "tool_discovery" && !e.remote_agent
      )}
      a2aEvents={visibleResults.flatMap((r) => r.trace).filter(
        (e) => e.event_type === "tool_discovery" && Boolean(e.remote_agent)
      )}
      scenario={detail.summary.scenario}
    />
  </Grid>
) : null}
```
> The `detail?.summary?.scenario` accessor is null-safe (Pitfall #6, RESEARCH.md). Same pattern already used at TraceWorkspacePage line 401 (`detail?.summary.title ?? "saved report"`).

---

### `frontend/src/features/compare/CompareTracesPanel.tsx` (MODIFY — mount #2)

**Analog:** self, lines 97-138 (dual-column Grid).

**Read-first context** (lines 97-99):
```typescript
{/* D-08: Two synchronized TraceExplorer columns */}
<Grid container spacing={2} alignItems="flex-start">
  <Grid size={{ xs: 12, md: 6 }}>
```

**Action** — insert ABOVE line 97 (single full-width panel above both columns per D-72):
```typescript
{(() => {
  const allEvents = [...(resultA?.trace ?? []), ...(resultB?.trace ?? [])];
  const mcpEvents = allEvents.filter((e) => e.event_type === "tool_discovery" && !e.remote_agent);
  const a2aEvents = allEvents.filter((e) => e.event_type === "tool_discovery" && Boolean(e.remote_agent));
  if (mcpEvents.length === 0 && a2aEvents.length === 0) return null; // presence-gated per A4
  return (
    <Grid container spacing={2}>
      <Grid size={{ xs: 12 }}>
        <DiscoveryPhasePanel
          mcpEvents={mcpEvents}
          a2aEvents={a2aEvents}
          scenario="tool_discovery"
        />
      </Grid>
    </Grid>
  );
})()}
```
> Presence-gating (RESEARCH A4) keeps non-discovery compare flows clean. UI-SPEC line 130 explicitly says "no scenario string gate needed" on this surface.

---

### `src/a2a_vs_mcp/data/seeds/scenarios.json` (MODIFY — append row)

**Analog:** `scenarios.json` lines 142-169 (TICKET-1011, TICKET-1012 — both `advanced` rows with multi-tag arrays + nested `talking_point`).

**Read-first context** (line 156-169 verbatim — TICKET-1012, the immediate-prior row):
```json
{
  "scenario": "vip_parallel_escalation",
  "ticket_id": "TICKET-1012",
  "customer_id": "CUST-003",
  "title": "VIP Parallel Escalation",
  "difficulty": "advanced",
  "tags": ["enterprise", "parallel_investigation", "escalation"],
  "query": "...",
  "talking_point": {
    "headline": "Three specialists, one simultaneous dispatch",
    "sentence": "...",
    "callout": "..."
  }
}
```

**Action** — append new row inside the top-level array (after current TICKET-1012 closing `}` at line 169, before the array's closing `]` at line 170):
```json
,
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
> Field names are CONTEXT-locked (D-67/D-68/D-69). `DemoRepository.load_scenarios()` (`dataset.py:105-119`) consumes these keys verbatim.

---

### `src/a2a_vs_mcp/data/seeds/customers.json` (MODIFY — append row)

**Analog:** `customers.json` lines 1-26 (CUST-001..CUST-004, all 4 fields: `customer_id`, `name`, `email`, `segment`).

**Read-first context** (lines 20-25 verbatim — CUST-004, the immediate-prior consumer-segment row):
```json
{
  "customer_id": "CUST-004",
  "name": "Dana Lee",
  "email": "dana@example.com",
  "segment": "consumer"
}
```

**Action** — append after the CUST-004 closing `}` at line 25, before the closing `]` at line 26:
```json
,
{
  "customer_id": "CUST-005",
  "name": "Casey Rivera",
  "email": "casey@example.com",
  "segment": "consumer"
}
```
> Verify `CUST-005` is not used elsewhere (RESEARCH A1) via `grep -r CUST-005 src/a2a_vs_mcp/data/seeds/` before appending.

---

### `tests/test_tool_discovery_scenario.py` (NEW — pytest)

**Analog:** `tests/test_demo_modes.py` lines 1-80.

**Imports + bootstrap pattern** (verbatim from `test_demo_modes.py:1-25`):
```python
import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("A2A_VS_MCP_ARTIFACT_ROOT", str(PROJECT_ROOT / ".tmp" / "test_artifacts"))
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a2a_vs_mcp.dataset import DemoRepository
from a2a_vs_mcp.platform import DemoPlatform
```

**Setup pattern** (mirror `test_demo_modes.py:39-40`):
```python
class ToolDiscoveryScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.platform = DemoPlatform(PROJECT_ROOT, runtime="mock")
```

**Core assertions** — combine RESEARCH.md Code Example 6 with `test_demo_modes.py:65-80` discovery-event lookup pattern:
```python
def test_tool_discovery_scenario_loads(self) -> None:
    repo = DemoRepository(PROJECT_ROOT)
    scenarios = repo.load_scenarios()
    self.assertIn("tool_discovery", scenarios)
    ticket = scenarios["tool_discovery"]
    self.assertEqual(ticket.ticket_id, "TICKET-1013")
    self.assertEqual(ticket.customer_id, "CUST-005")
    self.assertEqual(ticket.difficulty, "advanced")
    self.assertIn("discovery", ticket.tags)
    self.assertIn("fallback", ticket.tags)

def test_tool_discovery_scenario_emits_discovery_event_in_mcp_mode(self) -> None:
    ticket = self.platform.get_ticket("tool_discovery", None, None)
    result = self.platform.run("mcp", ticket)
    discovery_events = [e for e in result.trace if e["event_type"] == "tool_discovery"]
    self.assertGreater(len(discovery_events), 0)

def test_tool_discovery_scenario_falls_back_for_unknown_sku(self) -> None:
    # NebulaSync Hub is NOT in warranties/orders seeds → forces search_docs fallback
    ticket = self.platform.get_ticket("tool_discovery", None, None)
    result = self.platform.run("mcp", ticket)
    self.assertIn("search_docs", result.tools_used)
```
> The `result.trace[i]["event_type"] == "tool_discovery"` lookup pattern is verified in `test_demo_modes.py:70-71`.

---

### `frontend/src/components/traces/__tests__/DiscoveryPhasePanel.test.tsx` (NEW — vitest)

**Analog:** `frontend/src/features/run-workspace/RunWorkspacePage.test.tsx` lines 1-80.

**Imports pattern** (verbatim model from `RunWorkspacePage.test.tsx:1-10`):
```typescript
import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { appTheme } from "../../../app/theme";
import { DiscoveryPhasePanel } from "../DiscoveryPhasePanel";
import type { TraceEvent } from "../../../lib/types/api";
```

**Render harness** (model on `RunWorkspacePage.test.tsx:77-80` — wraps in ThemeProvider + CssBaseline; no router/provider needed for a presentational component):
```typescript
function renderPanel(props: Parameters<typeof DiscoveryPhasePanel>[0]) {
  return render(
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <DiscoveryPhasePanel {...props} />
    </ThemeProvider>
  );
}
```

**Test cases** (RESEARCH Code Example 6, expanded for all D-decisions):
```typescript
const mcpDiscoveryEvent: TraceEvent = {
  index: 1,
  event_type: "tool_discovery",
  timestamp_ms: 0,
  server: "a2a_vs_mcp.mcp_servers.db_server",
  tools: ["get_order_history", "get_warranty"],
  protocol: "official_mcp_sdk",
  transport: "in_process",
  requested_transport: "in_process",
};

it("renders MCP tools side-by-side with A2A placeholder when only MCP events present", () => {
  renderPanel({ mcpEvents: [mcpDiscoveryEvent], a2aEvents: [], scenario: "tool_discovery" });
  expect(screen.getByText("Discovery Phase")).toBeInTheDocument();
  expect(screen.getByText("MCP — Tool Catalog")).toBeInTheDocument();
  expect(screen.getByText("Run on A2A to populate")).toBeInTheDocument();
});

it("renders A2A placeholder copy 'Run on MCP to populate' when only A2A events present", () => {
  renderPanel({
    mcpEvents: [],
    a2aEvents: [{ ...mcpDiscoveryEvent, remote_agent: "documentation" }],
    scenario: "tool_discovery",
  });
  expect(screen.getByText("Run on MCP to populate")).toBeInTheDocument();
});

it("highlights stale-cache failure when requested_transport !== transport", () => {
  const fallbackEvent: TraceEvent = { ...mcpDiscoveryEvent, requested_transport: "stdio", transport: "in_process" };
  renderPanel({ mcpEvents: [fallbackEvent], a2aEvents: [], scenario: "tool_discovery" });
  // Failure tooltip is keyboard-accessible via aria-label
  expect(screen.getByLabelText(/Stale capability cache/i)).toBeInTheDocument();
});
```

---

## Shared Patterns

### Color tokens (apply to ALL new frontend files)
**Source:** `frontend/src/lib/trace/eventColors.ts:11-25`
**Rule:** Never hardcode protocol or tone hex values. Use the maps.
```typescript
import { protocolColor, toneColor } from "../../lib/trace/eventColors";
// protocolColor.mcp === "#1976d2"
// protocolColor.a2a === "#7b1fa2"
// toneColor.warning === "#ed6c02"
// toneColor.error   === "#c62828"
```

### `TraceEvent` typing (apply to all frontend files)
**Source:** `frontend/src/lib/types/api.ts:34-56`
**Rule:** Always import `TraceEvent` from `lib/types/api`. The interface is open-ended (`[key: string]: unknown`) — fields like `remote_agent`, `tools`, `a2a_agent_card` are accessed by string key without type errors.
```typescript
import type { TraceEvent } from "../../lib/types/api";
```

### Overline section header (apply to MCP/A2A column headers)
**Source:** `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx:221-225`
```typescript
<Typography variant="overline"
  sx={{ color: "secondary.main", letterSpacing: "0.14em", display: "block", mb: 1 }}>
  {label}
</Typography>
```
Override `color` to `protocolColor.mcp` or `protocolColor.a2a` for column-specific headers per UI-SPEC §Color.

### Code-surface block (apply to JSON schema/agent-card payload rendering)
**Source:** `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx:227-240`
```typescript
<Box sx={{
  background: "#1a2332",
  borderRadius: 1,
  p: 2,
  fontFamily: "monospace",
  fontSize: "0.72rem",
  lineHeight: 1.6,
  color: "#e8e8e8",
  overflowX: "auto",
  whiteSpace: "pre-wrap",
  wordBreak: "break-word",
}}>
  <JsonTree data={data} />
</Box>
```

### MUI Grid responsive split (apply to side-by-side MCP/A2A layout)
**Source:** `frontend/src/features/compare/CompareTracesPanel.tsx:98-138`
```typescript
<Grid container spacing={3}>
  <Grid size={{ xs: 12, md: 6 }}>{/* MCP */}</Grid>
  <Grid size={{ xs: 12, md: 6 }}>{/* A2A */}</Grid>
</Grid>
```

### pytest sys.path bootstrap (apply to ALL new pytest files)
**Source:** `tests/test_demo_modes.py:1-25`
**Rule:** Every backend test file inserts `src/` on `sys.path` and sets `A2A_VS_MCP_ARTIFACT_ROOT` BEFORE any `a2a_vs_mcp` import. Skipping this causes module-not-found OR pollutes the developer's real artifact root.

### Vitest theme harness (apply to ALL new vitest component tests)
**Source:** `frontend/src/features/run-workspace/RunWorkspacePage.test.tsx:77-80`
**Rule:** Wrap the component under test in `<ThemeProvider theme={appTheme}><CssBaseline />…</ThemeProvider>`. Without ThemeProvider, MUI `sx` props that reference `secondary.main` / `text.disabled` resolve to `undefined` and tests can fail on color assertions.

### Failure-mode payload contract (already on the wire — DO NOT add new event types)
**Source:** `src/a2a_vs_mcp/mcp/client.py:62-84` and `src/a2a_vs_mcp/a2a/remote_broker.py:234-244`
**Rule:** Stale-cache + unknown-tool-fallback are already encoded as:
- `tool_transport_fallback` event (when transport falls back) — `mcp/client.py:69-75`
- `requested_transport !== transport` divergence on the next `tool_discovery` event — `mcp/client.py:77-84`
- A2A re-emit copies these verbatim with `remote_agent` + `remote_trace=true` tags — `a2a/remote_broker.py:237-243`

The panel's failure-row highlight must read `event.requested_transport !== event.transport` — no new field, no schema change. RESEARCH.md anti-pattern #2 forbids adding a new event_type.

---

## No Analog Found

None. Every new file in Phase 11 has a strong existing analog in the codebase. This is consistent with RESEARCH.md's "stitch existing primitives together" assessment (line 245).

---

## Metadata

**Analog search scope:**
- `frontend/src/components/traces/` (drawer, explorer)
- `frontend/src/features/traces/`, `frontend/src/features/compare/` (mount sites)
- `frontend/src/lib/trace/` (color + utility modules)
- `frontend/src/features/run-workspace/` (vitest reference)
- `src/a2a_vs_mcp/data/seeds/` (scenarios + customers)
- `src/a2a_vs_mcp/dataset.py`, `schemas.py`, `mcp/client.py`, `a2a/remote_broker.py`
- `tests/` (pytest reference)

**Files scanned:** 12 source + 2 test analogs + 2 seed files = 16 files inspected.

**Pattern extraction date:** 2026-04-30
