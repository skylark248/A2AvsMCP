---
phase: 05-presentation-polish
plan: 03
subsystem: frontend-presenter-pages
tags: [glossary, role-first-phrasing, runtime-chip, failure-summary, compare-page]
dependency_graph:
  requires: [05-01, 05-02]
  provides: [role-first-labels, runtime-indicator, failure-visibility]
  affects: [RunWorkspacePage, ComparePage]
tech_stack:
  added: []
  patterns: [GlossaryTerm-wrapping, ROLE_FIRST_LABELS-record, failure-gated-rendering]
key_files:
  created: []
  modified:
    - frontend/src/features/run-workspace/RunWorkspacePage.tsx
    - frontend/src/features/compare/ComparePage.tsx
decisions:
  - "Duplicated ROLE_FIRST_LABELS in both files -- keeps pages self-contained, avoids shared util for 4 lines"
  - "Runtime Chip placed in header Stack alongside transport Chip for visual grouping"
  - "Failure summary uses item.failures.length > 0 guard (not truthy check) since empty arrays are truthy"
  - "ComparePage header replaced template string with JSX map for per-mode GlossaryTerm wrapping"
metrics:
  duration: 1m 29s
  completed: "2026-04-27"
  tasks_completed: 2
  tasks_total: 2
  files_modified: 2
---

# Phase 5 Plan 3: Presenter Page Polish Summary

Role-first phrasing with GlossaryTerm tooltips on Run and Compare pages, runtime indicator Chip per result card, and failure summary chips gated on non-empty failures array.

## What Was Done

### Task 1: RunWorkspacePage Enhancements (4 additions)

1. **GlossaryTerm import** -- Added import from `../../components/glossary/GlossaryTerm`
2. **ROLE_FIRST_LABELS + roleFirstLabel** -- Module-level Record mapping mode keys to audience-friendly labels (e.g., "mcp" -> "Tool Access Protocol (MCP)"). Fallback to `mode.toUpperCase()` for unknown modes.
3. **Mode header replacement** -- Replaced `{item.mode.toUpperCase()}` with `<GlossaryTerm term={item.mode}>{roleFirstLabel(item.mode)}</GlossaryTerm>` for first-mention dotted underline + tooltip per D-05/D-06/D-07.
4. **Runtime Chip** -- Added `<Chip label={item.runtime === "llm" ? "OpenAI Runtime" : "Mock Runtime"} color={item.runtime === "llm" ? "warning" : "default"} variant="outlined" />` in header Stack per D-09.
5. **Failure summary** -- After TalkingPointCard, gated on `item.failures.length > 0`, renders error-colored Chips for each failure string per D-12.

### Task 2: ComparePage Enhancements (2 additions)

1. **GlossaryTerm import** -- Added import from `../../components/glossary/GlossaryTerm`
2. **ROLE_FIRST_LABELS + roleFirstLabel** -- Same module-level helper as RunWorkspacePage.
3. **Comparison header** -- Replaced template string `Comparing ${orderedResults.map(r => r.mode.toUpperCase()).join(" . ")}` with JSX that maps each mode to a `<GlossaryTerm>` wrapped `roleFirstLabel` span, separated by middle dots.

## Verification Results

- TypeScript compiles clean (`npx tsc --noEmit` -- zero errors)
- GlossaryTerm appears 3 times in RunWorkspacePage (import + 1 usage + closing tag)
- GlossaryTerm appears 3 times in ComparePage (import + 1 usage + closing tag)
- roleFirstLabel appears 2 times in each file (definition + usage)
- "Mock Runtime" and "OpenAI Runtime" each appear once in RunWorkspacePage
- `item.failures.length > 0` guard present in RunWorkspacePage
- Existing `item.ticket?.talking_point` render path preserved intact

## Deviations from Plan

None -- plan executed exactly as written.

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1+2 | cc03e9a | feat(05-03): role-first phrasing, GlossaryTerm wrappers, runtime Chip, failure summary |

## Self-Check: PASSED
