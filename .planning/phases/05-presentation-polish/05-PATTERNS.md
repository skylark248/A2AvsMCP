# Phase 5: Presentation Polish - Pattern Map

**Mapped:** 2026-04-27
**Files analyzed:** 5 (2 new, 3 modified)
**Analogs found:** 5 / 5

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `frontend/src/lib/glossary/glossaryTerms.ts` | static data / utility | transform (lookup) | `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` (FIELD_ANNOTATIONS map) | role-match |
| `frontend/src/components/glossary/GlossaryTerm.tsx` | component | request-response (hover) | `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` (JsonTree key tooltip pattern) | role-match |
| `frontend/src/features/run-workspace/RunWorkspacePage.tsx` | component (page) | CRUD + request-response | self (existing file, targeted additions) | exact |
| `frontend/src/features/compare/ComparePage.tsx` | component (page) | request-response | self (existing file, targeted additions) | exact |
| `frontend/src/components/traces/TraceExplorer.tsx` | component | request-response | self (existing file, targeted additions) | exact |

---

## Pattern Assignments

### `frontend/src/lib/glossary/glossaryTerms.ts` (static data, lookup)

**Analog:** `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` — `FIELD_ANNOTATIONS` and `PROTO_NOTES` module-level `Record<string, string>` constants

**Data map pattern** (ProtocolEnvelopeDrawer.tsx lines 26-45 and 157-164):
```typescript
// Module-level constant — static Record keyed by string slug, values are one-sentence strings
// FIELD_ANNOTATIONS pattern (lines 26-45):
const FIELD_ANNOTATIONS: Record<string, string> = {
  protocolVersion: "A2A spec version — must be '1.0' for interoperability.",
  messageId: "Unique message ID for idempotency and tracing.",
  taskId: "Links this message to the task lifecycle (submitted → working → completed).",
  // ... more entries
};

// PROTO_NOTES pattern (lines 157-164):
const PROTO_NOTES: Record<string, string> = {
  a2a: "A2A 1.0 protocol shapes: Agent Cards advertise skills ...",
  mcp: "MCP protocol shapes: tools/list discovers capabilities ...",
  runtime: "Internal runtime event — not part of MCP or A2A wire format ...",
};
```

**Copy this pattern for `glossaryTerms.ts`:**
- Exported constant (not `const`, but `export const`) so consumers can import it
- `Record<string, string>` type — key is term slug, value is one-sentence definition
- Module-level static — no function, no factory, no async
- File lives in `lib/glossary/` — mirrors the `lib/trace/` and `lib/demo/` pattern

**Import pattern** (ProtocolEnvelopeDrawer.tsx line 17-18):
```typescript
import type { TraceEvent } from "../../lib/types/api";
import { isA2AEvent, traceEventProtocol, traceLabel } from "../../lib/trace/utils";
```
For `glossaryTerms.ts`, no imports are needed — pure static export.

---

### `frontend/src/components/glossary/GlossaryTerm.tsx` (component, hover tooltip)

**Analog:** `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` — the `JsonTree` component's per-key MUI Tooltip pattern with dotted underline styling

**Imports pattern** (ProtocolEnvelopeDrawer.tsx lines 1-18):
```typescript
import {
  Alert,
  Box,
  Chip,
  Divider,
  Drawer,
  IconButton,
  Stack,
  Tooltip,       // <-- The MUI Tooltip already used for hover annotations
  Typography,
} from "@mui/material";
import type { TraceEvent } from "../../lib/types/api";
```

For `GlossaryTerm.tsx`, the relevant imports are:
```typescript
import Tooltip from "@mui/material/Tooltip";
import type { ReactNode } from "react";
import { glossaryTerms } from "../../lib/glossary/glossaryTerms";
```

**Core MUI Tooltip + dotted underline pattern** (ProtocolEnvelopeDrawer.tsx lines 129-142):
```tsx
// JsonTree key rendering — exact pattern to replicate in GlossaryTerm
<Tooltip title={note ?? ""} placement="left" arrow disableHoverListener={!note}>
  <Box
    component="span"
    sx={{
      color: note ? "secondary.main" : "primary.main",
      fontWeight: note ? 600 : 400,
      cursor: note ? "help" : "default",
      textDecoration: note ? "underline dotted" : "none",   // dotted underline for known terms
      whiteSpace: "nowrap",
    }}
  >
    &quot;{key}&quot;
  </Box>
</Tooltip>
```

**GlossaryTerm adaptation** — simplify the JsonTree pattern to a standalone component:
- Remove color/fontWeight overrides (GlossaryTerm is inline in body text, not monospace JSON)
- Use `borderBottom: "1px dashed currentColor"` (D-04) instead of `textDecoration: "underline dotted"` — same visual effect, more cross-browser consistent for inline text
- Use `cursor: "help"` (from JsonTree pattern, D-04)
- Keep `arrow` on Tooltip (from JsonTree pattern)
- Guard: if term not in glossaryTerms map, render children unwrapped (same as JsonTree's `disableHoverListener={!note}` guard — but use early return for clarity)

**Component props interface pattern** (ProtocolEnvelopeDrawer.tsx lines 20-23):
```typescript
interface ProtocolEnvelopeDrawerProps {
  event: TraceEvent | null;
  onClose: () => void;
}
```
Copy this interface pattern for GlossaryTerm — named interface in same file, above the function.

---

### `frontend/src/features/run-workspace/RunWorkspacePage.tsx` (MODIFIED — runtime Chip, GlossaryTerm wrappers, failure summary)

**Analog:** Self — existing file. Additions follow patterns already established within the file.

**Existing imports block** (RunWorkspacePage.tsx lines 1-49):
```typescript
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,          // <-- already imported, runtime Chip uses same import
  Divider,
  FormControl,
  FormControlLabel,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
// ...
import { getProtocolColor } from "../../lib/trace/eventColors";
import type {
  // ... RunResult, RunResponse already imported
} from "../../lib/types/api";
```

**New imports to add:**
```typescript
import { GlossaryTerm } from "../../components/glossary/GlossaryTerm";
// Tooltip already available from MUI — no new MUI import needed for GlossaryTerm usage
// (GlossaryTerm wraps Tooltip internally)
```

**Runtime Chip pattern** — copy from existing transport Chip (RunWorkspacePage.tsx lines 864-867):
```tsx
// Existing transport Chip (lines 865-867):
{item.mcp_transport ? (
  <Chip label={item.mcp_transport} size="small" variant="outlined" color="default" />
) : null}

// New runtime Chip follows identical structure — add to same Stack direction="row":
<Chip
  label={item.runtime === "llm" ? "OpenAI Runtime" : "Mock Runtime"}
  size="small"
  color={item.runtime === "llm" ? "warning" : "default"}
  variant="outlined"
/>
```

The containing Stack (lines 862-868):
```tsx
<Stack direction="row" justifyContent="space-between" alignItems="center">
  <Typography variant="h6">{item.mode.toUpperCase()}</Typography>
  <Stack direction="row" spacing={0.5} alignItems="center">
    {item.mcp_transport ? (
      <Chip label={item.mcp_transport} size="small" variant="outlined" color="default" />
    ) : null}
    {/* ADD runtime Chip here, after transport Chip */}
  </Stack>
</Stack>
```

**GlossaryTerm first-mention pattern** — wrap the mode header text. The `item.mode.toUpperCase()` at line 863 is the target for role-first phrasing. Replace with a mode-label helper that returns the role-first string and wraps first mention:
```tsx
// Current (line 863):
<Typography variant="h6">{item.mode.toUpperCase()}</Typography>

// After (role-first phrasing via GlossaryTerm):
<Typography variant="h6">
  <GlossaryTerm term={item.mode}>
    {roleFirstLabel(item.mode)}
  </GlossaryTerm>
</Typography>

// Helper function (module-level, above component):
function roleFirstLabel(mode: string): string {
  const labels: Record<string, string> = {
    mcp: "Tool Access Protocol (MCP)",
    a2a: "Agent Coordination Protocol (A2A)",
    baseline: "Direct Agent (Baseline)",
    hybrid: "Combined Protocol (Hybrid)",
  };
  return labels[mode] ?? mode.toUpperCase();
}
```

**Failure summary pattern** — insert after the TalkingPointCard block (lines 894-916), following the same Stack+Chip pattern already used in the file (lines 819-831 for scenario tags):
```tsx
// Existing scenario tags chips pattern (lines 819-831) — copy for failure chips:
<Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
  {selectedScenario.tags.map((tag) => (
    <Chip key={tag} label={tag} size="small" />
  ))}
</Stack>

// New failure summary (add after TalkingPointCard, line 916):
{item.failures.length > 0 && (
  <Stack spacing={0.5}>
    <Typography variant="caption" sx={{ color: "error.main", fontWeight: 600 }}>
      Failure Events ({item.failures.length})
    </Typography>
    <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
      {item.failures.map((f, i) => (
        <Chip key={i} label={f} size="small" color="error" variant="outlined" />
      ))}
    </Stack>
  </Stack>
)}
```

**TalkingPointCard existing pattern** (RunWorkspacePage.tsx lines 894-916 — do not change, copy for reference):
```tsx
{item.ticket?.talking_point ? (
  <Paper
    elevation={0}
    sx={{
      borderLeft: `4px solid ${getProtocolColor(item.mode)}`,
      bgcolor: "action.hover",
      p: 1.5,
    }}
  >
    <Typography variant="subtitle2" fontWeight="bold">
      {item.ticket.talking_point.headline}
    </Typography>
    <Typography variant="body2" sx={{ mt: 0.5 }}>
      {item.ticket.talking_point.sentence}
    </Typography>
    <Typography variant="body2" sx={{ mt: 0.5, fontStyle: "italic", color: "text.secondary" }}>
      {item.ticket.talking_point.callout}
    </Typography>
  </Paper>
) : null}
```

---

### `frontend/src/features/compare/ComparePage.tsx` (MODIFIED — GlossaryTerm wrappers, role-first phrasing)

**Analog:** Self — existing file. Additions follow the same patterns as RunWorkspacePage.tsx.

**Existing imports block** (ComparePage.tsx lines 1-21):
```typescript
import {
  Alert,
  Card,
  CardContent,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";
import { CompareTracesPanel } from "./CompareTracesPanel";
```

**New imports to add:**
```typescript
import { GlossaryTerm } from "../../components/glossary/GlossaryTerm";
```

**Comparison header text** (ComparePage.tsx lines 92-93) — role-first phrasing target:
```tsx
// Current (line 131-133):
`Comparing ${orderedResults.map((r) => r.mode.toUpperCase()).join(" · ")}`

// After — map each mode through roleFirstLabel before joining:
`Comparing ${orderedResults.map((r) => roleFirstLabel(r.mode)).join(" · ")}`
```

The `roleFirstLabel` helper is the same module-level function as in RunWorkspacePage (can be shared via a utility or defined per-file for simplicity — planner decides, but pattern is identical).

**GlossaryTerm on mode labels in compare panel** — the `orderedResults.map()` at lines 80-84 feeds into `CompareTracesPanel`. The mode display labels in the compare header text are the first-mention location. Apply `<GlossaryTerm term={r.mode}>` there.

**Error/empty-state Alert pattern** (ComparePage.tsx lines 102-103 — already in file, reference for any new Alert additions):
```tsx
{error ? <Alert severity="error">{error}</Alert> : null}
```

---

### `frontend/src/components/traces/TraceExplorer.tsx` (MODIFIED — runtime prop, latency badge, LLM banner)

**Analog:** Self — existing file. Additions follow patterns already used within TraceExplorer.

**Existing imports block** (TraceExplorer.tsx lines 1-36):
```typescript
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRoundedIcon";  // line 5 — already imported
import {
  Card,
  CardContent,
  Chip,    // line 13 — already imported, latency badge uses this
  Divider,
  // ...
} from "@mui/material";
// Alert is NOT currently imported — must add for LLM banner
```

**New imports to add:**
```typescript
import Alert from "@mui/material/Alert";
// WarningAmberRoundedIcon is already imported (line 5) — no new icon import needed
// Chip already imported (line 13) — no new import needed
```

**Existing props interface** (TraceExplorer.tsx lines 38-42):
```typescript
interface TraceExplorerProps {
  events: TraceEvent[];
  title?: string;
  subtitle?: string;
}
```

**Extended props interface — add `runtime` prop:**
```typescript
interface TraceExplorerProps {
  events: TraceEvent[];
  title?: string;
  subtitle?: string;
  runtime?: string;  // "mock" | "llm" — optional so existing call sites without it still work
}
```

**Existing stats strip pattern** (TraceExplorer.tsx lines 154-169 — summary strip "Tier 0"):
```tsx
<Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap
  sx={{ px: 1, py: 0.75, bgcolor: "action.hover", borderRadius: 1 }}>
  <Typography variant="caption" sx={{ color: "text.secondary" }}>
    <strong>{events.length}</strong> total
  </Typography>
  {/* ... more caption items */}
</Stack>
```

**Latency badge pattern** — add to the title/subtitle header Stack (lines 93-98) alongside the existing title Typography. Follows existing WarningAmberRoundedIcon usage in `TraceStat` (line 112):
```tsx
// Existing header Stack (lines 93-98):
<Stack spacing={0.5}>
  <Typography variant="h6">{title}</Typography>
  <Typography variant="body2" sx={{ color: "text.secondary" }}>
    {subtitle ?? "Filter the protocol timeline by event type, actor, tool, and failure state."}
  </Typography>
</Stack>

// After — extend header Stack to include latency badge:
<Stack direction="row" justifyContent="space-between" alignItems="flex-start">
  <Stack spacing={0.5}>
    <Typography variant="h6">{title}</Typography>
    <Typography variant="body2" sx={{ color: "text.secondary" }}>
      {subtitle ?? "Filter the protocol timeline by event type, actor, tool, and failure state."}
    </Typography>
  </Stack>
  {runtime === "llm" && (
    <Chip
      label="Expect 2-5s per LLM call"
      size="small"
      color="warning"
      icon={<WarningAmberRoundedIcon fontSize="small" />}
    />
  )}
</Stack>
```

**LLM Alert banner pattern** — insert after the filter Divider (line 152) and before the summary strip (line 155). Follows existing Alert usage pattern at RunWorkspacePage.tsx line 364:
```tsx
// Existing Alert pattern in codebase (RunWorkspacePage.tsx line 403):
{selectedPreset ? <Alert severity="info">{selectedPreset.description}</Alert> : null}

// New LLM alert banner — same conditional pattern:
{runtime !== undefined && runtime !== "mock" && (
  <Alert severity="warning" sx={{ mb: 1 }}>
    This run used OpenAI GPT-4o-mini — latency reflects real API calls.
  </Alert>
)}
```

**WarningAmberRoundedIcon existing usage** (TraceExplorer.tsx line 112 — already used in TraceStat, pattern confirmed):
```tsx
<TraceStat
  label="Failures"
  value={stats.failures}
  icon={<WarningAmberRoundedIcon fontSize="small" />}
/>
```

**Failure highlighting** — `ProtocolEventRow` (lines 262-282) already applies `eventBorderColor(event)` which returns `toneColor.error` (`#c62828`) for error-tone events. The `isTraceFailureEvent` function is already called in the filter and stats calculations. No additional failure highlighting needed in `ProtocolEventRow` — the color system already works.

**`runtime` prop threading** — after adding `runtime` to `TraceExplorerProps`, search all usages of `<TraceExplorer` in the codebase and pass the runtime value from the parent `RunResult.runtime`. Both `RunWorkspacePage` (if/when TraceExplorer is added there) and `CompareTracesPanel` are call sites.

---

## Shared Patterns

### MUI Tooltip for hover definitions
**Source:** `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` lines 129-142
**Apply to:** `GlossaryTerm.tsx` (new component)
```tsx
// The JsonTree key tooltip pattern — extract and simplify:
<Tooltip title={note ?? ""} placement="left" arrow disableHoverListener={!note}>
  <Box
    component="span"
    sx={{
      cursor: note ? "help" : "default",
      textDecoration: note ? "underline dotted" : "none",
    }}
  >
    {children}
  </Box>
</Tooltip>
```

### Chip for status/badge indicators
**Source:** `frontend/src/features/run-workspace/RunWorkspacePage.tsx` lines 864-867 (transport Chip), lines 872-887 (metrics Chips)
**Apply to:** Runtime indicator Chip in RunWorkspacePage, latency badge Chip in TraceExplorer
```tsx
// Consistent Chip usage pattern across the app:
<Chip
  label="..."
  size="small"
  color="warning" | "default" | "success" | "error"
  variant="outlined"
/>
// icon prop: <SomeIcon fontSize="small" /> when icon needed
```

### Alert for contextual banners
**Source:** `frontend/src/features/run-workspace/RunWorkspacePage.tsx` lines 364, 403, 554-558
**Apply to:** LLM run banner in TraceExplorer
```tsx
// Conditional Alert pattern (line 403):
{condition ? <Alert severity="info">{message}</Alert> : null}
// For TraceExplorer LLM banner: severity="warning"
```

### Module-level static Record<string, string> map
**Source:** `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` lines 26-45 (FIELD_ANNOTATIONS), lines 157-164 (PROTO_NOTES)
**Apply to:** `glossaryTerms.ts` (new static data file)
```typescript
// Export the map so consumers can import it:
export const glossaryTerms: Record<string, string> = {
  slug: "One-sentence definition.",
  // ... 15-20 entries
};
// No function wrappers, no async, no factory — plain exported constant
```

### Stack + Chip for failure/tag lists
**Source:** `frontend/src/features/run-workspace/RunWorkspacePage.tsx` lines 819-831
**Apply to:** Failure summary chips in RunWorkspacePage result card
```tsx
<Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
  {items.map((item, i) => (
    <Chip key={i} label={item} size="small" color="error" variant="outlined" />
  ))}
</Stack>
```

### Protocol color lookup
**Source:** `frontend/src/lib/trace/eventColors.ts` — `getProtocolColor(mode)` and `toneColor`
**Apply to:** Any new component that needs protocol-keyed colors (GlossaryTerm can optionally use `protocolColor[term]` to color the dotted underline by protocol)
```typescript
import { getProtocolColor, toneColor } from "../../lib/trace/eventColors";
// getProtocolColor("mcp") → "#1976d2"
// toneColor.error → "#c62828"
// toneColor.warning → "#ed6c02"
```

---

## No Analog Found

All files have close matches. No files in Phase 5 require novel patterns without a codebase analog.

---

## Metadata

**Analog search scope:** `frontend/src/` — components, features, lib directories
**Key files scanned:**
- `frontend/src/features/run-workspace/RunWorkspacePage.tsx` (949 lines — full read)
- `frontend/src/components/traces/TraceExplorer.tsx` (348 lines — full read)
- `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` (250 lines — full read)
- `frontend/src/features/compare/ComparePage.tsx` (162 lines — full read)
- `frontend/src/lib/trace/eventColors.ts` (36 lines — full read)
- `frontend/src/lib/demo/presets.ts` (83 lines — full read)
- `frontend/src/lib/types/api.ts` (lines 1-120 — key type definitions)

**Files scanned:** 7
**Pattern extraction date:** 2026-04-27

---

## Key Observations for Planner

1. **`ProtocolEnvelopeDrawer.tsx` is the closest analog for both new files** — it already implements the exact pattern of (a) a static `Record<string, string>` map keyed by slug, and (b) a Tooltip with dotted underline + `cursor: "help"` on a `<Box component="span">`. `GlossaryTerm.tsx` is a simplified extraction of that pattern.

2. **`TraceExplorer.tsx` already imports `WarningAmberRoundedIcon` and `Chip`** — the latency badge adds no new imports beyond `Alert`. The `runtime` prop is the only interface change needed.

3. **`RunResult.runtime` is a required `string` field** (api.ts line 79, not optional) — LLM detection is `item.runtime === "llm"` or equivalently `item.runtime !== "mock"`. No null-check needed.

4. **Failure highlighting in `ProtocolEventRow` is already complete** — `eventBorderColor()` already returns `toneColor.error` (`#c62828`) for error-tone events via `traceEventTone()`. The only gap is the failure summary list in the result card (item.failures[] not rendered anywhere).

5. **`GlossaryTerm` usage rule** — per D-05, each protocol term gets exactly one `<GlossaryTerm>` wrapper per page showing the role-first full form. Subsequent mentions use plain text. The result card mode header (`item.mode.toUpperCase()` at RunWorkspacePage line 863) is the primary target.
