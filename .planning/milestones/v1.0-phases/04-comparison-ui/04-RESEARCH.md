# Phase 4: Comparison UI - Research

**Researched:** 2026-04-27
**Domain:** React frontend — MUI components, recharts data visualization, trace color system
**Confidence:** HIGH

## Summary

Phase 4 transforms raw trace data into visual comparison tools: inline metric chips on result cards, a recharts-based swimlane timeline for parallel agent execution, synchronized side-by-side trace panels on the Compare page, and a centralized color system replacing all hardcoded hex values. The existing codebase already has `ComparisonMetrics` on every `RunResult` (computed by the backend), a three-tier `TraceExplorer` component, and a `ComparePage` with `ModeColumn` that will be replaced by `CompareTracesPanel`.

The frontend stack is React 19 + MUI 7 + Vite 7 with TypeScript. recharts is the only new runtime dependency needed for this phase; `@xyflow/react`, `react-syntax-highlighter`, and `motion` are installed per UI-05 but explicitly deferred to later phases per CONTEXT.md.

**Primary recommendation:** Build `eventColors.ts` first (UI-04) as foundation, then metrics chips (UI-01), then swimlane timeline (UI-02), then compare panel (UI-03), and install all UI-05 deps last. The color file unblocks all other components.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- D-01: Metrics as inline MUI Chips (elapsed time, round-trips, agent count) below mode header in result cards
- D-02: Round-trip count is combined (`tool_calls + a2a_messages`)
- D-03: Only core three metrics shown: elapsed time, round-trip count, agent count
- D-04: ParallelAgentTimeline uses recharts BarChart horizontal bars per agent
- D-05: Non-parallel modes get sequential non-overlapping bars from step_index + timestamp_ms
- D-06: Timeline embedded inside result card, above trace explorer
- D-07: CompareTracesPanel on ComparePage only
- D-08: Two modes at a time with Mode A/B selectors
- D-09: Synchronized scrolling via shared scroll ref
- D-10: eventColors.ts exports protocol + event tone colors
- D-11: Canonical palette: mcp=#1976d2, a2a=#7b1fa2, hybrid=#2e7d32, baseline=#757575
- D-12: File at frontend/src/lib/trace/eventColors.ts

### Claude's Discretion
- Exact recharts BarChart configuration (bar height, axis labels, responsive breakpoints)
- Whether to extract ParallelAgentTimeline as a separate component file or keep inline
- Synchronized scroll implementation detail (shared ref, scroll event listener, or IntersectionObserver)
- How to derive sequential bars for non-parallel modes from step_index + timestamp_ms
- Whether eventColors.ts also exports eventBorderColor() helper or keeps it in utils.ts
- Installation order and exact versions for UI-05 dependencies

### Deferred Ideas (OUT OF SCOPE)
- @xyflow/react for interactive flow diagrams -- installed but not used this phase
- react-syntax-highlighter -- installed but not used this phase
- motion (framer-motion) -- installed but not used this phase
- Four-column comparison -- two-at-a-time is sufficient
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | Result card displays outcome metrics (elapsed time, round-trip count, agent count) | Metrics chips pattern documented; ComparisonMetrics data shape verified on RunResult |
| UI-02 | ParallelAgentTimeline component -- swimlane timeline showing parallel A2A agent execution | Recharts BarChart layout="vertical" pattern documented; TraceEvent timing fields verified |
| UI-03 | CompareTracesPanel -- two synchronized trace explorer instances side-by-side | ComparePage current structure mapped; synchronized scroll approach documented |
| UI-04 | eventColors.ts as single source of truth for event-type color constants | Full hardcoded color audit completed; migration surface documented |
| UI-05 | Frontend dependencies added -- @xyflow/react, recharts, react-syntax-highlighter, motion | All versions verified against npm registry |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Outcome metrics chips | Frontend Client | -- | Read-only display of backend-computed ComparisonMetrics already on RunResult |
| Swimlane timeline | Frontend Client | -- | Client-side recharts rendering from trace event timing fields |
| Synchronized trace panel | Frontend Client | -- | Two TraceExplorer instances with shared scroll ref; no backend work |
| Color system (eventColors.ts) | Frontend Client | -- | Pure constant/utility module replacing hardcoded hex across components |
| Dependency installation | Build / Dev | -- | npm install; no runtime API changes |

## Standard Stack

### Core (already installed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| react | ^19.2.0 | UI framework | Already in project [VERIFIED: frontend/package.json] |
| @mui/material | ^7.3.1 | Component library (Chip, Grid, Card, Select) | Already in project [VERIFIED: frontend/package.json] |
| react-router-dom | ^7.9.4 | Routing (ComparePage) | Already in project [VERIFIED: frontend/package.json] |
| vite | ^7.1.10 | Build tool | Already in project [VERIFIED: frontend/package.json] |
| typescript | ^5.9.3 | Type safety | Already in project [VERIFIED: frontend/package.json] |

### New Dependencies (UI-05)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| recharts | 3.8.1 | Swimlane BarChart for ParallelAgentTimeline | UI-02 timeline rendering [VERIFIED: npm registry 2026-04-27] |
| @xyflow/react | 12.10.2 | Flow diagrams (deferred to v2 VIZ-02) | Installed now, used later [VERIFIED: npm registry 2026-04-27] |
| react-syntax-highlighter | 16.1.1 | Code highlighting (deferred to Phase 5+) | Installed now, used later [VERIFIED: npm registry 2026-04-27] |
| motion | 12.38.0 | Animations (deferred to Phase 5+) | Installed now, used later [VERIFIED: npm registry 2026-04-27] |

**Installation:**
```bash
cd frontend && npm install recharts@^3.8.1 @xyflow/react@^12.10.2 react-syntax-highlighter@^16.1.1 motion@^12.38.0
```

Note: `react-syntax-highlighter` needs `@types/react-syntax-highlighter` as a devDependency for TypeScript support. [ASSUMED]

```bash
npm install -D @types/react-syntax-highlighter
```

## Architecture Patterns

### System Architecture Diagram

```
RunWorkspacePage.tsx                          ComparePage.tsx
  |                                            |
  v                                            v
[Result Card] -----> per mode               [Report Selector]
  |                                            |
  +-- [MetricsChipRow]                         v
  |     reads: item.metrics.*             [Mode A/B Selectors]
  |                                            |
  +-- [ParallelAgentTimeline]                  v
  |     reads: item.trace[]               [CompareTracesPanel]
  |     (parallel_batch_id,                    |
  |      started_at, completed_at,         +---+---+
  |      step_index, timestamp_ms)         |       |
  |                                   [TraceExplorer A] [TraceExplorer B]
  +-- [TraceExplorer]                      (synced scroll via shared ref)
        reads: item.trace[]
                                    All components import from:
                                    eventColors.ts (protocol + tone colors)
```

### Recommended Project Structure
```
frontend/src/
├── lib/trace/
│   ├── eventColors.ts          # NEW: canonical color constants + helpers (UI-04)
│   └── utils.ts                # existing trace helpers
├── components/
│   ├── traces/
│   │   ├── TraceExplorer.tsx    # MODIFY: import colors from eventColors.ts
│   │   └── ProtocolEnvelopeDrawer.tsx  # MODIFY: import colors from eventColors.ts
│   └── timeline/
│       └── ParallelAgentTimeline.tsx   # NEW: recharts swimlane (UI-02)
├── features/
│   ├── run-workspace/
│   │   └── RunWorkspacePage.tsx # MODIFY: add metrics chips + timeline (UI-01, UI-06 embed)
│   └── compare/
│       ├── ComparePage.tsx      # MODIFY: replace ModeColumn with CompareTracesPanel (UI-03)
│       └── CompareTracesPanel.tsx  # NEW: two-mode synced trace panel (UI-03)
```

### Pattern 1: Recharts Horizontal BarChart (Swimlane)
**What:** Use `layout="vertical"` on `BarChart` to render horizontal bars. YAxis becomes the category axis (agent names), XAxis becomes the value axis (time in ms).
**When to use:** ParallelAgentTimeline for both parallel and sequential modes.
**Example:**
```typescript
// Source: Context7 recharts docs + recharts API
import { BarChart, Bar, XAxis, YAxis, Cell, ResponsiveContainer, Tooltip } from "recharts";

interface TimelineBar {
  agent: string;
  start: number;  // ms offset from earliest event
  duration: number; // ms
  color: string;
}

// For recharts horizontal bars, we need layout="vertical"
// YAxis type="category" for agent names, XAxis type="number" for time
<ResponsiveContainer width="100%" height={barCount * 40 + 40}>
  <BarChart layout="vertical" data={bars} barSize={20}>
    <XAxis type="number" domain={[0, "dataMax"]} tickFormatter={(v) => `${v}ms`} />
    <YAxis type="category" dataKey="agent" width={100} />
    <Tooltip />
    <Bar dataKey="duration" fill="#1976d2">
      {bars.map((bar, i) => (
        <Cell key={i} fill={bar.color} />
      ))}
    </Bar>
  </BarChart>
</ResponsiveContainer>
```

**Important note on Gantt-style rendering:** recharts `BarChart` does not natively support offset start positions (Gantt bars). The standard approach is to use a stacked bar technique: render an invisible "offset" bar followed by the visible "duration" bar. [VERIFIED: Context7 recharts docs show no native offset support]

```typescript
// Gantt-style: invisible offset bar + visible duration bar
interface GanttBar {
  agent: string;
  offset: number;   // invisible spacer
  duration: number;  // visible bar
}

<Bar dataKey="offset" stackId="timeline" fill="transparent" />
<Bar dataKey="duration" stackId="timeline">
  {bars.map((bar, i) => (
    <Cell key={i} fill={bar.color} />
  ))}
</Bar>
```

### Pattern 2: MUI Chip Metrics Row
**What:** Inline row of MUI Chips below the mode header in result cards.
**When to use:** UI-01 metrics display.
**Example:**
```typescript
// Source: Existing pattern in RunWorkspacePage.tsx lines 880-893
// Current code already uses Chip rows for tool/a2a/failures — new row replaces with D-01 spec

const roundTrips = item.metrics.tool_calls + item.metrics.a2a_messages; // D-02

<Stack direction="row" spacing={0.5} alignItems="center">
  <Chip
    label={`${item.metrics.latency_ms}ms`}
    size="small"
    sx={{ bgcolor: protocolColor(item.mode), color: "#fff" }}
  />
  <Chip label={`${roundTrips} round-trips`} size="small" variant="outlined" />
  <Chip label={`${item.metrics.agents_involved.length} agents`} size="small" variant="outlined" />
</Stack>
```

### Pattern 3: Synchronized Scroll
**What:** Two scrollable containers that stay in sync.
**When to use:** CompareTracesPanel with two TraceExplorer instances.
**Example:**
```typescript
// Source: Standard React ref-based scroll sync pattern [ASSUMED]
import { useRef, useCallback } from "react";

function CompareTracesPanel() {
  const scrollRefA = useRef<HTMLDivElement>(null);
  const scrollRefB = useRef<HTMLDivElement>(null);
  const syncing = useRef(false);

  const handleScroll = useCallback((source: "a" | "b") => {
    if (syncing.current) return;
    syncing.current = true;
    const from = source === "a" ? scrollRefA.current : scrollRefB.current;
    const to = source === "a" ? scrollRefB.current : scrollRefA.current;
    if (from && to) {
      to.scrollTop = from.scrollTop;
    }
    // Use requestAnimationFrame to prevent scroll event loops
    requestAnimationFrame(() => { syncing.current = false; });
  }, []);

  return (
    <Grid container spacing={2}>
      <Grid size={6}>
        <Box ref={scrollRefA} onScroll={() => handleScroll("a")}
             sx={{ overflowY: "auto", maxHeight: 600 }}>
          <TraceExplorer events={modeAEvents} />
        </Box>
      </Grid>
      <Grid size={6}>
        <Box ref={scrollRefB} onScroll={() => handleScroll("b")}
             sx={{ overflowY: "auto", maxHeight: 600 }}>
          <TraceExplorer events={modeBEvents} />
        </Box>
      </Grid>
    </Grid>
  );
}
```

### Anti-Patterns to Avoid
- **Scroll event infinite loops:** Without the `syncing` guard, setting `scrollTop` on B triggers B's scroll handler which sets A's `scrollTop`, creating an infinite loop. Always use a mutex ref.
- **Direct DOM color overrides in sx props:** After UI-04, no component should hardcode hex colors for protocol or tone styling. Always import from `eventColors.ts`.
- **Over-engineering the timeline:** Do not use `@xyflow/react` for the swimlane. recharts BarChart is the decided approach (D-04). xyflow is for interactive sequence diagrams in v2.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Horizontal bar chart | Custom SVG/Canvas timeline | recharts `BarChart layout="vertical"` | Handles responsive sizing, tooltips, axis labels; stacked bar technique for Gantt offsets |
| Responsive chart container | Manual resize observer | recharts `ResponsiveContainer` | Built-in debounced resize handling |
| Color constants | Inline hex strings | `eventColors.ts` module | Single source of truth; eliminates 30+ hardcoded hex values across 5+ files |
| Scroll synchronization | ScrollSpy library or IntersectionObserver | Shared ref + onScroll handler | Simpler, no dependency, < 20 lines of code |

**Key insight:** The synchronized scroll is simple enough that a library would add overhead without benefit. The recharts timeline, however, saves significant work on axis rendering, tooltips, and responsive behavior.

## Common Pitfalls

### Pitfall 1: Recharts Gantt-Style Offset Bars
**What goes wrong:** Developer uses a single `<Bar>` and expects to set a start offset. Recharts bars always start at 0.
**Why it happens:** BarChart is designed for magnitude comparison, not Gantt timelines.
**How to avoid:** Use the stacked bar pattern: invisible `offset` bar + visible `duration` bar with `stackId`.
**Warning signs:** All bars start from the left edge despite different `started_at` values.

### Pitfall 2: Scroll Sync Infinite Loop
**What goes wrong:** Setting `scrollTop` on panel B triggers B's `onScroll`, which sets A's `scrollTop`, creating an infinite recursive scroll event.
**Why it happens:** The browser fires a scroll event whenever `scrollTop` is programmatically changed.
**How to avoid:** Use a `syncing` ref guard and `requestAnimationFrame` to break the cycle.
**Warning signs:** Page freezes or jitters when scrolling either trace panel.

### Pitfall 3: Missing Color Migration Spots
**What goes wrong:** After creating `eventColors.ts`, some hardcoded hex values remain in non-obvious locations (e.g., inline styles in `ProtocolEnvelopeDrawer.tsx` JSON tree, `FullTraceTier` border).
**Why it happens:** Grep for hex values catches the obvious ones, but some are in template literals or deeply nested sx props.
**How to avoid:** Run the full color audit (documented below) and verify with `grep -r '#[0-9a-fA-F]\{6\}'` after migration.
**Warning signs:** Inconsistent colors between components after the color system migration.

### Pitfall 4: TraceExplorer Inside ScrollSync Container
**What goes wrong:** `TraceExplorer` is a `<Card>` component with its own internal overflow. Wrapping it in another scrollable container creates nested scroll areas.
**Why it happens:** The existing `ModeColumn` in `ComparePage.tsx` has `maxHeight: 600, overflowY: "auto"` on its content area.
**How to avoid:** When embedding `TraceExplorer` in `CompareTracesPanel`, either remove the Card wrapper's internal scroll or make the outer container the sole scroll target.
**Warning signs:** Two scrollbars appear, or scroll sync only affects one level.

## Code Examples

### Current Result Card Structure (insertion points for UI-01 and UI-02)
```typescript
// Source: RunWorkspacePage.tsx lines 862-921
// Each result card in the .map() currently shows:
//   1. Mode header + transport badge + latency chip   (line 867-875)
//   2. Final answer text                               (line 876-878)
//   3. Divider                                         (line 879)
//   4. Metrics chip row (tool_calls, a2a, failures)   (line 880-893)
//   5. Talking point paper (if exists)                 (line 894-916)
//
// INSERT metrics chips (UI-01) at position 1 (below header, replace existing latency chip)
// INSERT ParallelAgentTimeline (UI-02) between positions 4 and 5
// TraceExplorer is NOT currently in result cards — it lives on a separate page
```

### Current ComparePage Structure (replacement points for UI-03)
```typescript
// Source: ComparePage.tsx lines 170-314
// Current layout:
//   1. Report selector card                    (line 254-286)
//   2. Grid of ModeColumn cards (up to 4)      (line 296-303)
//   3. ProtocolEnvelopeDrawer                  (line 311)
//
// REPLACE: ModeColumn grid with CompareTracesPanel (two-mode, synced)
// KEEP: Report selector card, ProtocolEnvelopeDrawer
// ADD: Mode A / Mode B selectors
```

### ComparisonMetrics Data Flow
```typescript
// Source: api.ts lines 58-69
// ComparisonMetrics is on RunResult.metrics — already computed by backend
// No new API endpoint needed.

interface ComparisonMetrics {
  mode: string;
  latency_ms: number;        // D-01: elapsed time chip
  tool_calls: number;        // D-02: combined with a2a_messages for round-trip count
  a2a_messages: number;      // D-02: combined with tool_calls
  agents_involved: string[]; // D-03: .length for agent count chip
  complexity: string;
  strengths: string[];
  weaknesses: string[];
  retries: number;
  failures: number;
}

// TraceEvent timing fields for swimlane (from Phase 2 enrichment):
interface TraceEvent {
  step_index?: number;           // sequential ordering
  parallel_batch_id?: string;    // groups concurrent agent tasks
  started_at?: number;           // ms timestamp for bar start
  completed_at?: number;         // ms timestamp for bar end
  // ... other fields
}
```

### Hardcoded Color Audit (complete migration surface for UI-04)

**Files that MUST import from eventColors.ts after migration:**

| File | Line(s) | Current Value | Meaning | Action |
|------|---------|---------------|---------|--------|
| `RunWorkspacePage.tsx` | 49-54 | `protocolColor` map (#1976d2, #7b1fa2, #2e7d32, #757575) | Protocol colors | Replace with `eventColors.protocolColor` |
| `RunWorkspacePage.tsx` | 898 | `protocolColor[item.mode] ?? "#757575"` | Talking point border | Replace with import |
| `ComparePage.tsx` | 32-37 | `MODE_META` colors (#546e7a, #17475f, #8d4e2a, #4a235a) | Protocol colors (darker set) | **Delete entirely** — use D-11 canonical palette |
| `ComparePage.tsx` | 43-51 | `eventBorderColor()` function | Tone + protocol border colors | Move to `eventColors.ts` |
| `TraceExplorer.tsx` | 263-266 | `ProtocolEventRow` border colors (#c62828, #ed6c02, #2e7d32, #17475f) | Tone-based borders | Replace with `eventColors.eventBorderColor()` |
| `TraceExplorer.tsx` | 298 | `#17475f` | FullTraceTier card border | Replace with import |
| `ProtocolEnvelopeDrawer.tsx` | 93, 96, 99 | `#c0392b`, `#2980b9`, `#27ae60` | JSON tree syntax colors | **Keep as-is** — these are syntax highlighting, not protocol/tone colors |
| `ProtocolEnvelopeDrawer.tsx` | 229, 235 | `#1a2332`, `#e8e8e8` | Dark code block background | **Keep as-is** — UI chrome, not semantic colors |

**Files NOT in scope for eventColors.ts migration** (non-trace decorative colors):
- `theme.ts` — app-wide theme (primary/secondary/background)
- `MetricBarsCard.tsx` — SVG export chart colors (separate concern)
- `AppShell.tsx` — background gradients
- `ReportDetailPage.tsx` — gradient decorations
- `TrendsPage.tsx` — gradient decorations
- `TelemetryPage.tsx` — gradient decorations
- `TraceWorkspacePage.tsx` — gradient decoration (line 175)

### eventColors.ts Recommended Shape
```typescript
// Source: Synthesized from D-10, D-11, D-12 decisions + color audit above

export const protocolColor: Record<string, string> = {
  mcp: "#1976d2",
  a2a: "#7b1fa2",
  hybrid: "#2e7d32",
  baseline: "#757575",
};

export const toneColor = {
  error: "#c62828",
  warning: "#ed6c02",
  success: "#2e7d32",
  info: "#757575",
} as const;

/** Border color for trace event rows — tone takes priority, then protocol */
export function eventBorderColor(event: TraceEvent): string {
  const tone = traceEventTone(event);
  if (tone === "error") return toneColor.error;
  if (tone === "warning") return toneColor.warning;
  if (tone === "success") return toneColor.success;
  const proto = traceEventProtocol(event);
  return protocolColor[proto] ?? protocolColor.baseline;
}

/** Get protocol color by mode string, with fallback */
export function getProtocolColor(mode: string): string {
  return protocolColor[mode] ?? protocolColor.baseline;
}
```

### Swimlane Data Transformation
```typescript
// Transform TraceEvent[] into recharts-compatible bar data

interface TimelineBar {
  agent: string;
  offset: number;    // ms from earliest start — invisible spacer bar
  duration: number;  // ms — visible colored bar
  color: string;     // from eventColors.protocolColor
  batchId?: string;  // parallel_batch_id for grouping
}

function buildTimelineBars(events: TraceEvent[], mode: string): TimelineBar[] {
  // For parallel modes: filter events with parallel_batch_id + started_at + completed_at
  const parallelEvents = events.filter(
    (e) => e.parallel_batch_id && e.started_at != null && e.completed_at != null
  );

  if (parallelEvents.length > 0) {
    const minStart = Math.min(...parallelEvents.map((e) => e.started_at!));
    return parallelEvents.map((e) => ({
      agent: traceEventActor(e),
      offset: e.started_at! - minStart,
      duration: e.completed_at! - e.started_at!,
      color: getProtocolColor(mode),
      batchId: e.parallel_batch_id,
    }));
  }

  // For sequential modes: derive from step_index + timestamp_ms
  const stepped = events
    .filter((e) => e.step_index != null)
    .sort((a, b) => a.step_index! - b.step_index!);

  if (stepped.length === 0) return [];

  const minTs = stepped[0].timestamp_ms;
  // Each step gets a fixed-width bar positioned at its relative timestamp
  return stepped.map((e, i) => {
    const nextTs = stepped[i + 1]?.timestamp_ms ?? e.timestamp_ms + 50;
    return {
      agent: traceEventActor(e),
      offset: e.timestamp_ms - minTs,
      duration: nextTs - e.timestamp_ms,
      color: getProtocolColor(mode),
    };
  });
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| recharts 2.x API | recharts 3.x (current) | 2024 | New tree-shaking, some prop changes; use 3.x imports [VERIFIED: npm registry shows 3.8.1] |
| framer-motion package | motion package (renamed) | 2024 | `framer-motion` is now `motion`; import from `motion/react` [VERIFIED: npm registry] |
| @xyflow/react (was reactflow) | @xyflow/react 12.x | 2024 | Package renamed from `reactflow`; use `@xyflow/react` [VERIFIED: npm registry] |

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `@types/react-syntax-highlighter` needed as devDependency | Standard Stack | TypeScript build fails if types are bundled differently in v16 |
| A2 | requestAnimationFrame sufficient to break scroll sync loop | Pattern 3 / Pitfall 2 | May need setTimeout(0) fallback on some browsers; low risk |
| A3 | ProtocolEnvelopeDrawer JSON syntax colors (#c0392b etc.) should NOT migrate to eventColors.ts | Color Audit | If user expects total color unification, these would need inclusion too |

## Open Questions

1. **TraceExplorer scroll container nesting**
   - What we know: `TraceExplorer` renders inside a `<Card>` with no explicit maxHeight. `ComparePage`'s `ModeColumn` adds `maxHeight: 600` externally.
   - What's unclear: Should `CompareTracesPanel` set maxHeight on the wrapper Box or pass it as a prop to `TraceExplorer`?
   - Recommendation: Set maxHeight on the outer scroll sync Box (the one with the ref). TraceExplorer remains unaware of scroll constraints.

2. **Sequential bar duration for non-parallel modes**
   - What we know: Events have `timestamp_ms` and `step_index` but no explicit duration for sequential steps.
   - What's unclear: Whether the gap between consecutive timestamps accurately represents step duration, or if some events are instantaneous.
   - Recommendation: Use gap between consecutive timestamps. If gap is 0, use a minimum visual width (e.g., 20ms) to keep bars visible.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Node.js | Build/dev | Assumed | -- | -- |
| npm | Package install | Assumed | -- | -- |
| recharts | UI-02 | Not yet installed | Will be 3.8.1 | -- |
| @xyflow/react | UI-05 (deferred) | Not yet installed | Will be 12.10.2 | -- |
| react-syntax-highlighter | UI-05 (deferred) | Not yet installed | Will be 16.1.1 | -- |
| motion | UI-05 (deferred) | Not yet installed | Will be 12.38.0 | -- |

**Missing dependencies with no fallback:** None -- all are installable via npm.

## Sources

### Primary (HIGH confidence)
- Context7 `/recharts/recharts` -- BarChart, ResponsiveContainer, Cell, layout="vertical" patterns
- npm registry (2026-04-27) -- recharts@3.8.1, @xyflow/react@12.10.2, react-syntax-highlighter@16.1.1, motion@12.38.0
- Codebase grep -- complete hardcoded hex color audit across frontend/src/

### Secondary (MEDIUM confidence)
- Existing codebase patterns -- RunWorkspacePage.tsx, ComparePage.tsx, TraceExplorer.tsx, api.ts type definitions

### Tertiary (LOW confidence)
- None

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- all packages verified against npm, existing codebase fully audited
- Architecture: HIGH -- insertion points, data shapes, and component boundaries verified from source code
- Pitfalls: HIGH -- recharts Gantt limitation verified via Context7 docs; scroll sync pattern is well-known
- Color audit: HIGH -- exhaustive grep of all hex values in frontend/src/ completed

**Research date:** 2026-04-27
**Valid until:** 2026-05-27 (stable MUI/recharts ecosystem; 30 days)
