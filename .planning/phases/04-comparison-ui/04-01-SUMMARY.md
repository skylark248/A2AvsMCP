---
phase: 04-comparison-ui
plan: 01
subsystem: frontend/trace-colors
tags: [colors, dependencies, refactor, foundation]
dependency_graph:
  requires: []
  provides: [eventColors.ts, recharts, xyflow, react-syntax-highlighter, motion]
  affects: [04-02, 04-03, 04-04]
tech_stack:
  added: [recharts@3, @xyflow/react@12, react-syntax-highlighter@16, motion@12]
  patterns: [centralized-color-module, named-exports]
key_files:
  created:
    - frontend/src/lib/trace/eventColors.ts
  modified:
    - frontend/package.json
    - frontend/package-lock.json
    - frontend/src/components/traces/TraceExplorer.tsx
    - frontend/src/features/compare/ComparePage.tsx
    - frontend/src/features/run-workspace/RunWorkspacePage.tsx
decisions:
  - "Used BASELINE constant instead of protocolColor.baseline for TS strict indexing safety"
  - "Extracted BASELINE_ICON constant in ComparePage for TS Record fallback type safety"
metrics:
  duration: 3m 46s
  completed: 2026-04-26T19:25:28Z
  tasks_completed: 2
  tasks_total: 2
  files_changed: 6
---

# Phase 4 Plan 1: UI-05 Dependencies and eventColors.ts Foundation Summary

Installed four UI-05 frontend dependencies (recharts, @xyflow/react, react-syntax-highlighter, motion) and created the centralized eventColors.ts color system with canonical protocol/tone palettes, then migrated all hardcoded hex colors out of TraceExplorer, ComparePage, and RunWorkspacePage.

## What Was Done

### Task 1: Install UI-05 dependencies and create eventColors.ts
- Installed `recharts@^3.8.1`, `@xyflow/react@^12.10.2`, `react-syntax-highlighter@^16.1.1`, `motion@^12.38.0` as dependencies
- Installed `@types/react-syntax-highlighter` as devDependency
- Created `frontend/src/lib/trace/eventColors.ts` exporting:
  - `protocolColor` — canonical palette (mcp=#1976d2, a2a=#7b1fa2, hybrid=#2e7d32, baseline=#757575)
  - `toneColor` — severity palette (error=#c62828, warning=#ed6c02, success=#2e7d32, info=#757575)
  - `getProtocolColor(mode)` — lookup with baseline fallback
  - `eventBorderColor(event)` — tone-priority border color for trace rows
- **Commit:** 2a54932

### Task 2: Migrate hardcoded colors in three components
- **TraceExplorer.tsx:** Replaced 4-way ternary in ProtocolEventRow with `eventBorderColor(event)`; replaced `#17475f` in FullTraceTier with `getProtocolColor("mcp")`
- **ComparePage.tsx:** Removed `MODE_META` constant and local `eventBorderColor` function; replaced with `MODE_ICONS` (no color field) + imported `getProtocolColor` and `eventBorderColor`
- **RunWorkspacePage.tsx:** Removed local `protocolColor` const; replaced with imported `getProtocolColor(item.mode)`
- **Commit:** ed8e78a

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed TypeScript strict indexing errors in eventColors.ts**
- **Found during:** Task 2 (build verification)
- **Issue:** `Record<string, string>` indexing returns `string | undefined` under strict mode; `protocolColor[mode] ?? protocolColor.baseline` produced TS2322 because both sides could be undefined
- **Fix:** Extracted `const BASELINE = "#757575"` as a string literal fallback instead of re-indexing the Record
- **Files modified:** frontend/src/lib/trace/eventColors.ts

**2. [Rule 1 - Bug] Fixed TypeScript strict type error in ComparePage getModeIcon**
- **Found during:** Task 2 (build verification)
- **Issue:** `MODE_ICONS[mode]` returns `{ icon; protocol } | undefined` — the `?? MODE_ICONS.baseline` fallback also has the same undefined possibility
- **Fix:** Extracted `const BASELINE_ICON` as a typed constant for the fallback
- **Files modified:** frontend/src/features/compare/ComparePage.tsx

## Verification Results

| Check | Result |
|-------|--------|
| `npx tsc --noEmit` | PASS (exit 0) |
| `npm run build` | PASS (built in 1.52s) |
| grep for hardcoded hex in 3 files | CLEAN: zero matches |
| grep for eventColors import in 3 files | Each file has >= 1 match |

## Self-Check: PASSED

- [x] frontend/src/lib/trace/eventColors.ts exists
- [x] Commit 2a54932 exists in git log
- [x] Commit ed8e78a exists in git log
- [x] All 6 files accounted for in commits
