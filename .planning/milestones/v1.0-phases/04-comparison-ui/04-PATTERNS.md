# Phase 4: Comparison UI - Pattern Map

**Mapped:** 2026-04-27
**Files analyzed:** 8 (3 new, 5 modified)
**Analogs found:** 8 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `frontend/src/lib/trace/eventColors.ts` (NEW) | utility | transform | `frontend/src/lib/trace/utils.ts` | exact |
| `ParallelAgentTimeline` component (NEW) | component | transform | `frontend/src/components/charts/MetricBarsCard.tsx` | role-match |
| `CompareTracesPanel` component (NEW) | component | request-response | `frontend/src/features/compare/ComparePage.tsx` (ModeColumn) | exact |
| `frontend/src/features/run-workspace/RunWorkspacePage.tsx` (MODIFY) | component | request-response | self (result card section lines 862-921) | exact |
| `frontend/src/features/compare/ComparePage.tsx` (MODIFY) | component | request-response | self (ModeColumn lines 114-168) | exact |
| `frontend/src/components/traces/TraceExplorer.tsx` (MODIFY) | component | transform | self (ProtocolEventRow lines 261-284) | exact |
| `frontend/src/lib/trace/utils.ts` (MODIFY) | utility | transform | self | exact |
| `frontend/package.json` (MODIFY) | config | N/A | self | exact |

## Pattern Assignments

### `frontend/src/lib/trace/eventColors.ts` (NEW - utility, transform)

**Analog:** `frontend/src/lib/trace/utils.ts`

**Imports pattern** (utils.ts lines 1):
```typescript
import type { TraceEvent } from "../types/api";
```

**Core pattern -- pure functions with typed returns, no side effects** (utils.ts lines 7-12, 34-50):
```typescript
// Each function is a named export, takes a TraceEvent, returns a typed primitive
export function traceLabel(event: TraceEvent): string {
  if (event.message_type) {
    return `${event.event_type}:${event.message_type}`;
  }
  return event.event_type;
}

export function traceEventTone(event: TraceEvent): "error" | "warning" | "success" | "info" {
  // ... cascading if checks returning literal union members
}
```

**Color values to consolidate into this file:**

Protocol colors (from RunWorkspacePage.tsx lines 49-54 -- these are the CANONICAL values per D-11):
```typescript
const protocolColor: Record<string, string> = {
  mcp: "#1976d2",      // MUI blue
  a2a: "#7b1fa2",      // MUI purple
  hybrid: "#2e7d32",   // MUI green
  baseline: "#757575", // MUI grey
};
```

Tone colors (from ComparePage.tsx lines 43-52 and TraceExplorer.tsx lines 263-266):
```typescript
// These are duplicated in two places -- both use the same values
// error: "#c62828", warning: "#ed6c02", success: "#2e7d32"
function eventBorderColor(event: TraceEvent): string {
  const tone = traceEventTone(event);
  if (tone === "error") return "#c62828";
  if (tone === "warning") return "#ed6c02";
  if (tone === "success") return "#2e7d32";
  const proto = traceEventProtocol(event);
  if (proto === "a2a") return "#8d4e2a";
  if (proto === "mcp") return "#17475f";
  return "#546e7a";
}
```

ComparePage MODE_META colors to REPLACE (lines 32-37 -- these CONFLICT with canonical palette and must be replaced):
```typescript
// WRONG -- darker brand colors, not the canonical MUI protocol colors
const MODE_META = {
  baseline: { icon: ..., color: "#546e7a", protocol: "No protocol" },
  mcp:      { icon: ..., color: "#17475f", protocol: "MCP" },
  a2a:      { icon: ..., color: "#8d4e2a", protocol: "A2A" },
  hybrid:   { icon: ..., color: "#4a235a", protocol: "A2A + MCP" },
};
```

TraceExplorer FullTraceTier hardcoded color (line 298):
```typescript
sx={{ borderLeft: `4px solid #17475f` }}
```

---

### `ParallelAgentTimeline` component (NEW - component, transform)

**Analog:** `frontend/src/components/charts/MetricBarsCard.tsx`

**Component file structure** (MetricBarsCard.tsx lines 1-23):
```typescript
// Imports: MUI first, then React hooks, then internal utilities
import DownloadOutlinedIcon from "@mui/icons-material/DownloadOutlined";
import LinkOutlinedIcon from "@mui/icons-material/LinkOutlined";
import { Box, Button, Card, CardContent, Stack, Typography } from "@mui/material";
import { useMemo } from "react";

import { useAppUi } from "../../app/ui/AppUiProvider";

// Interface defined above component, named Props suffix convention
interface MetricBarItem {
  label: string;
  value: number;
  displayValue?: string;
  color?: string;
  subtitle?: string;
}

interface MetricBarsCardProps {
  title: string;
  subtitle?: string;
  items: MetricBarItem[];
  inverse?: boolean;
  minBarPercent?: number;
  snapshotKey?: string;
}
```

**Export pattern** (MetricBarsCard.tsx line 41):
```typescript
// Named export, not default export
export function MetricBarsCard({ title, subtitle, items, ... }: MetricBarsCardProps) {
```

**Card wrapper pattern** (MetricBarsCard.tsx lines 116-177):
```typescript
return (
  <Card id={anchorId} sx={{ height: "100%", scrollMarginTop: 112 }}>
    <CardContent>
      <Stack spacing={1.5}>
        {/* header row */}
        <Stack direction={{ xs: "column", sm: "row" }} justifyContent="space-between" spacing={1.5}>
          ...
        </Stack>
        {/* content rows */}
        <Stack spacing={1.25}>
          {items.map((item) => (
            ...
          ))}
        </Stack>
      </Stack>
    </CardContent>
  </Card>
);
```

**Note:** This is a recharts BarChart component (new dependency). No recharts analog exists in the codebase. The planner should reference recharts horizontal BarChart docs. The component will receive `TraceEvent[]` and compute bar data from `started_at`/`completed_at` fields or derive sequential bars from `step_index`/`timestamp_ms`.

**Props pattern to follow** (inferred from TraceExplorer lines 37-41):
```typescript
interface ParallelAgentTimelineProps {
  events: TraceEvent[];
  mode: string;  // for protocol color lookup from eventColors
}
```

---

### `CompareTracesPanel` component (NEW - component, request-response)

**Analog:** `frontend/src/features/compare/ComparePage.tsx` (ModeColumn + page layout)

**Component structure with internal sub-components** (ComparePage.tsx lines 54-168):
```typescript
// Pattern: private sub-components defined above the exported component
// Each sub-component has its own typed props interface
function MiniEventRow({
  event,
  onSelect,
}: {
  event: TraceEvent;
  onSelect: (event: TraceEvent) => void;
}) { ... }

function ModeColumn({
  result,
  onSelectEvent,
}: {
  result: RunResult;
  onSelectEvent: (event: TraceEvent) => void;
}) { ... }
```

**Data loading pattern** (ComparePage.tsx lines 170-229):
```typescript
export function ComparePage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [results, setResults] = useState<RunResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  // URL-driven state
  const selectedReport = searchParams.get("report") ?? "";

  // Fetch with cleanup pattern
  useEffect(() => {
    let active = true;
    fetchReportDetail(selectedReport)
      .then((payload) => { if (active) setResults(payload.results); })
      .catch((err: unknown) => { if (active) setError(err instanceof Error ? err.message : "..."); })
      .finally(() => { if (active) setLoadingDetail(false); });
    return () => { active = false; };
  }, [selectedReport]);
```

**Two-column Grid layout** (ComparePage.tsx lines 297-303):
```typescript
<Grid container spacing={2} alignItems="flex-start">
  {orderedResults.map((result) => (
    <Grid key={result.mode} size={{ xs: 12, sm: cols <= 2 ? 6 : 6, xl: cols <= 2 ? 6 : 3 }}>
      <ModeColumn result={result} onSelectEvent={setEnvelopeEvent} />
    </Grid>
  ))}
</Grid>
```

**TraceExplorer integration** (TraceExplorer.tsx lines 37-43):
```typescript
// CompareTracesPanel will embed two TraceExplorer instances
// Props already support customization via title/subtitle
interface TraceExplorerProps {
  events: TraceEvent[];
  title?: string;
  subtitle?: string;
}
export function TraceExplorer({ events, title = "Trace Explorer", subtitle }: TraceExplorerProps) {
```

**Synchronized scroll pattern:** No analog exists in the codebase. Use shared `useRef<HTMLDivElement>` with `onScroll` event handler to sync two scrollable containers. The ModeColumn scrollable container pattern (line 150) shows the scroll target:
```typescript
<CardContent sx={{ flex: 1, overflowY: "auto", maxHeight: 600, pt: 1.5 }}>
```

---

### `RunWorkspacePage.tsx` (MODIFY - add metrics chips + swimlane)

**Analog:** Self -- result card section

**Existing Chip pattern in result cards** (lines 880-893):
```typescript
<Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
  <Chip label={`${item.metrics.tool_calls} tools`} size="small" />
  <Chip label={`${item.metrics.a2a_messages} A2A`} size="small" />
  <Chip label={`${item.metrics.failures} failures`} size="small" />
  <Chip
    label={item.metrics.complexity}
    size="small"
    color="secondary"
    variant="outlined"
  />
  {item.a2a_transport ? (
    <Chip label={`A2A ${item.a2a_transport}`} size="small" variant="outlined" />
  ) : null}
</Stack>
```

**Existing latency chip** (lines 873-874):
```typescript
<Chip label={`${item.metrics.latency_ms} ms`} size="small" />
```

**Result card iteration pattern** (lines 862-921):
```typescript
{result.results.map((item) => (
  <Grid key={item.mode} size={{ xs: 12, md: 6 }}>
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Stack spacing={1.25}>
          {/* header row with mode name + chips */}
          {/* final answer text */}
          <Divider />
          {/* metrics chips row */}
          {/* talking point paper -- INSERT swimlane ABOVE this */}
        </Stack>
      </CardContent>
    </Card>
  </Grid>
))}
```

**Data available on RunResult** (api.ts lines 77-100):
```typescript
// item.metrics has: latency_ms, tool_calls, a2a_messages, agents_involved, failures
// item.trace has: TraceEvent[] with step_index, started_at, completed_at, parallel_batch_id
```

**protocolColor usage to replace** (line 898):
```typescript
borderLeft: `4px solid ${protocolColor[item.mode] ?? "#757575"}`,
```

---

### `ComparePage.tsx` (MODIFY - replace with CompareTracesPanel)

**Existing structure to replace** (lines 296-311):
```typescript
// Current: Grid of ModeColumn components with MiniEventRow
// Target: Mode A / Mode B selectors + CompareTracesPanel with two TraceExplorer instances

// The ProtocolEnvelopeDrawer integration stays (line 311):
<ProtocolEnvelopeDrawer event={envelopeEvent} onClose={() => setEnvelopeEvent(null)} />
```

**Report selector pattern to KEEP** (lines 254-286):
```typescript
<Card>
  <CardContent>
    <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems="flex-end">
      <Stack spacing={1} sx={{ minWidth: 260 }}>
        <Typography variant="h6">Report</Typography>
        <FormControl fullWidth>
          <InputLabel id="compare-report-label">Saved Report</InputLabel>
          <Select ...>
            {reports.map((r) => (
              <MenuItem key={r.report_name} value={r.report_name}>
                {r.title} ({r.report_name})
              </MenuItem>
            ))}
          </Select>
        </FormControl>
      </Stack>
    </Stack>
  </CardContent>
</Card>
```

**MODE_META to remove** (lines 30-37) -- replaced by eventColors.ts imports

---

### `TraceExplorer.tsx` (MODIFY - use eventColors.ts)

**Hardcoded colors to replace** (lines 263-266):
```typescript
const borderColor =
  tone === "error" ? "#c62828" :
  tone === "warning" ? "#ed6c02" :
  tone === "success" ? "#2e7d32" : "#17475f";
```

**FullTraceTier hardcoded color** (line 298):
```typescript
sx={{ borderLeft: `4px solid #17475f` }}
```

**New import to add** (at the existing internal import block, after line 34):
```typescript
import { eventBorderColor } from "../../lib/trace/eventColors";
```

---

### `frontend/src/lib/trace/utils.ts` (MODIFY - potential eventBorderColor move)

**Current state:** No `eventBorderColor` function exists here. The function is duplicated in `ComparePage.tsx` (line 43) and inline in `TraceExplorer.tsx` (lines 263-266). Per D-12, the canonical version moves to `eventColors.ts`. No changes needed in `utils.ts` unless the planner decides to re-export from here for backward compatibility.

---

## Shared Patterns

### MUI Import Convention
**Source:** All component files
**Apply to:** All new component files
```typescript
// Order: 1) MUI icons (individual imports), 2) MUI material (destructured), 3) React, 4) react-router-dom, 5) internal imports
import SomeIcon from "@mui/icons-material/SomeIcon";
import { Box, Card, CardContent, Chip, Grid, Stack, Typography } from "@mui/material";
import { useMemo, useState } from "react";

import { someUtil } from "../../lib/trace/utils";
import type { SomeType } from "../../lib/types/api";
```

### Chip Usage Pattern
**Source:** `RunWorkspacePage.tsx` lines 580-589, 827-836, 880-893
**Apply to:** Metrics chips in RunWorkspacePage, stats in CompareTracesPanel
```typescript
// Small chips for data display, variant="outlined" for secondary info
<Chip label={`${value} ms`} size="small" />
<Chip label={tagLabel} size="small" variant="outlined" />
<Chip label={statusLabel} size="small" color="success" variant="outlined" />
```

### Card Layout Pattern
**Source:** `RunWorkspacePage.tsx` lines 864-919, `ComparePage.tsx` lines 127-167
**Apply to:** All new card components
```typescript
<Card variant="outlined" sx={{ height: "100%" }}>
  <CardContent>
    <Stack spacing={1.25}>
      {/* content */}
    </Stack>
  </CardContent>
</Card>
```

### Fetch + Cleanup Pattern
**Source:** `ComparePage.tsx` lines 208-223, `RunWorkspacePage.tsx` lines 204-237
**Apply to:** Any component that fetches data
```typescript
useEffect(() => {
  let active = true;
  fetchSomething(param)
    .then((payload) => { if (active) setData(payload); })
    .catch((err: unknown) => { if (active) setError(err instanceof Error ? err.message : "Failed."); })
    .finally(() => { if (active) setLoading(false); });
  return () => { active = false; };
}, [param]);
```

### Test File Pattern
**Source:** `RunWorkspacePage.test.tsx`, `MetricBarsCard.test.tsx`
**Apply to:** Tests for new components
```typescript
// Framework: vitest + @testing-library/react + userEvent
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";
import { renderWithProviders } from "../../test/renderWithProviders";

describe("ComponentName", () => {
  it("does something", async () => {
    const user = userEvent.setup();
    renderWithProviders(<Component props={...} />, "/route");
    // assertions with screen.getByRole, screen.findByText, expect(...)
  });
});
```

### Named Export Convention
**Source:** All components
**Apply to:** All new files
```typescript
// Always named exports, never default exports
export function ComponentName(...) { }
export function utilFunction(...) { }
```

## Hardcoded Color Inventory

All hex colors that `eventColors.ts` must consolidate (per D-10, D-11, D-12):

| Color | Current Location | Purpose | Canonical Value |
|-------|-----------------|---------|-----------------|
| `#1976d2` | RunWorkspacePage:50 | MCP protocol | `#1976d2` (D-11 canonical) |
| `#7b1fa2` | RunWorkspacePage:51 | A2A protocol | `#7b1fa2` (D-11 canonical) |
| `#2e7d32` | RunWorkspacePage:52 | Hybrid protocol | `#2e7d32` (D-11 canonical) |
| `#757575` | RunWorkspacePage:53,898 | Baseline protocol | `#757575` (D-11 canonical) |
| `#546e7a` | ComparePage:33,51 | Baseline (WRONG -- replace) | Replace with `#757575` |
| `#17475f` | ComparePage:34,50; TraceExplorer:266,298 | MCP (WRONG -- brand color) | Replace with `#1976d2` |
| `#8d4e2a` | ComparePage:35,49 | A2A (WRONG -- brand color) | Replace with `#7b1fa2` |
| `#4a235a` | ComparePage:36 | Hybrid (WRONG -- brand color) | Replace with `#2e7d32` |
| `#c62828` | ComparePage:45; TraceExplorer:264 | Error tone | `#c62828` |
| `#ed6c02` | ComparePage:46; TraceExplorer:265 | Warning tone | `#ed6c02` |
| `#2e7d32` | ComparePage:47; TraceExplorer:266 | Success tone | `#2e7d32` |

**Out of scope for eventColors.ts** (app theme / SVG snapshot / JSON tree syntax colors):
- `#17475f`, `#b85c38` in theme.ts (MUI theme primary/secondary)
- `#17475f`, `#b85c38`, `#fffaf4`, etc. in MetricBarsCard SVG builder
- `#c0392b`, `#2980b9`, `#27ae60`, `#1a2332`, `#e8e8e8` in ProtocolEnvelopeDrawer JsonTree
- Gradient colors in TrendsPage, TelemetryPage, ReportDetailPage, TraceWorkspacePage

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `ParallelAgentTimeline` (recharts) | component | transform | No recharts components exist -- `recharts` is a new dependency. Use `MetricBarsCard` for Card/Stack wrapper pattern and recharts BarChart docs for the chart internals. |

## Metadata

**Analog search scope:** `frontend/src/` (all subdirectories)
**Files scanned:** 32 TypeScript/TSX files
**Pattern extraction date:** 2026-04-27
