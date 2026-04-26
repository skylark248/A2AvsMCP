# Phase 4: Comparison UI - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-04-27
**Phase:** 04-comparison-ui
**Areas discussed:** Outcome metrics card, Swimlane timeline, Side-by-side panel, Color system

---

## Outcome Metrics Card

### Q1: Metrics layout on result card

| Option | Description | Selected |
|--------|-------------|----------|
| Inline chip row | Row of MUI Chips below mode header; minimal layout change | Y |
| Mini-dashboard grid | 3-column Grid with stat boxes like TraceStat; more prominent | |
| You decide | Let Claude choose | |

**User's choice:** Inline chip row
**Notes:** Consistent with existing Chip usage throughout the app.

### Q2: Which metrics to show

| Option | Description | Selected |
|--------|-------------|----------|
| Core three | Elapsed time, round-trip count, agent count | Y |
| Core three + failures | Add red failure chip when > 0 | |
| All six | All ComparisonMetrics values | |

**User's choice:** Core three
**Notes:** Matches UI-01 spec exactly.

### Q3: Round-trip count format

| Option | Description | Selected |
|--------|-------------|----------|
| Combined total | Single chip like '7 round-trips' | Y |
| Separate chips | Two chips: tool calls and A2A messages | |

**User's choice:** Combined total
**Notes:** Protocol-neutral metric; trace explorer has the breakdown.

---

## Swimlane Timeline

### Q1: Rendering approach

| Option | Description | Selected |
|--------|-------------|----------|
| Recharts horizontal bars | BarChart with horizontal bars per agent | Y |
| Custom SVG | Hand-built SVG rects; full layout control | |
| @xyflow/react flow | Node-based flow diagram; heavy for Gantt-like view | |

**User's choice:** Recharts horizontal bars
**Notes:** Already in UI-05 dependency list; simple and responsive.

### Q2: Non-parallel modes

| Option | Description | Selected |
|--------|-------------|----------|
| Sequential bars | Non-overlapping bars showing sequential execution | Y |
| Hide entirely | Only show when parallel_batch_id events exist | |
| Placeholder message | 'No parallel execution' with muted icon | |

**User's choice:** Sequential bars
**Notes:** The contrast with A2A overlapping bars IS the demo point.

### Q3: Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Inside result card, above trace | Per-mode, only for parallel scenarios | Y |
| Standalone comparison section | Dedicated section below all cards | |
| You decide | Let Claude place based on layout space | |

**User's choice:** Inside result card, above trace
**Notes:** Directly above the trace explorer.

---

## Side-by-side Panel

### Q1: Panel location

| Option | Description | Selected |
|--------|-------------|----------|
| ComparePage only | Dedicated Compare page; RunWorkspacePage shows individual cards | Y |
| Both pages | Compact panel on RunWorkspacePage + full on ComparePage | |
| RunWorkspacePage only | Replace ComparePage with inline panel | |

**User's choice:** ComparePage only
**Notes:** Separation of concerns -- no layout bloat on RunWorkspacePage.

### Q2: Number of modes

| Option | Description | Selected |
|--------|-------------|----------|
| Two modes at a time | Mode A/B selectors; two TraceExplorer columns | Y |
| All available modes | 2-4 columns depending on run | |
| You decide | Let Claude choose based on screen width | |

**User's choice:** Two modes at a time
**Notes:** Typical demo compares MCP vs A2A; focused and clean.

### Q3: Synchronized scrolling

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, sync scroll | Both columns scroll together | Y |
| No, independent scroll | Each column scrolls independently | |

**User's choice:** Yes, sync scroll
**Notes:** Lets viewer see what each protocol does at the same step.

---

## Color System

### Q1: Scope of eventColors.ts

| Option | Description | Selected |
|--------|-------------|----------|
| Protocol + event tones | Both protocol colors and error/warning/success tones | Y |
| Protocol colors only | Only centralize the 4 protocol colors | |
| You decide | Let Claude scope based on hardcoded color count | |

**User's choice:** Protocol + event tones
**Notes:** Single source of truth replacing all hardcoded values.

### Q2: Canonical palette

| Option | Description | Selected |
|--------|-------------|----------|
| RunWorkspacePage palette | MUI blue/purple/green/grey | Y |
| ComparePage palette | Darker muted variants | |
| You decide | Let Claude pick by contrast ratio | |

**User's choice:** RunWorkspacePage palette (MUI-based)
**Notes:** ComparePage's darker MODE_META colors get replaced.

### Q3: File location

| Option | Description | Selected |
|--------|-------------|----------|
| frontend/src/lib/trace/ | Next to utils.ts in trace utilities | Y |
| frontend/src/lib/theme/ | New theme subdirectory | |
| You decide | Let Claude choose by import simplicity | |

**User's choice:** frontend/src/lib/trace/
**Notes:** Co-located with trace helpers.

---

## Claude's Discretion

- Recharts BarChart configuration details (bar height, axis labels, responsive breakpoints)
- Whether to extract ParallelAgentTimeline as separate component file
- Synchronized scroll implementation approach
- Sequential bar derivation from step_index + timestamp_ms for non-parallel modes
- Whether eventBorderColor() helper moves to eventColors.ts or stays in utils.ts
- UI-05 dependency versions and installation order

## Deferred Ideas

- @xyflow/react for interactive flow diagrams (v2 VIZ-02)
- react-syntax-highlighter usage (Phase 5 or v2)
- motion/framer-motion animations (Phase 5)
- Four-column all-modes-at-once comparison (deferred for cleaner layout)
