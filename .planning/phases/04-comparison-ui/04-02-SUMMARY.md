---
phase: 04-comparison-ui
plan: 02
subsystem: frontend/run-workspace
tags: [metrics, chips, outcome-display, UI-01]
dependency_graph:
  requires: [04-01]
  provides: [outcome-metrics-chips]
  affects: [04-03, 04-04]
tech_stack:
  added: []
  patterns: [protocol-colored-chip, combined-round-trips, inline-metrics-row]
key_files:
  created: []
  modified:
    - frontend/src/features/run-workspace/RunWorkspacePage.tsx
decisions:
  - "Combined tool_calls + a2a_messages into single round-trips chip per D-02"
  - "Latency chip moved from header row to metrics row with protocol color per D-01"
  - "Removed old detailed chips (tools, A2A, failures, complexity, a2a_transport) per D-03"
metrics:
  duration: 0m 56s
  completed: 2026-04-26T19:28:29Z
  tasks_completed: 1
  tasks_total: 1
  files_changed: 1
---

# Phase 4 Plan 2: Outcome Metrics Chips Summary

Added three concise outcome metrics chips (elapsed time with protocol color, combined round-trip count, agent count) to each result card in RunWorkspacePage, replacing the old detailed metrics row with five granular chips.

## What Was Done

### Task 1: Add outcome metrics chip row to result cards
- Removed the old latency chip from the mode header row (it was a plain `Chip` showing `{latency_ms} ms`)
- Added new D-01 metrics chip row between the mode header and final answer text:
  - **Elapsed time**: `Chip` with `bgcolor: getProtocolColor(item.mode)` and white text showing `{latency_ms}ms`
  - **Round-trips**: Outlined `Chip` showing `{tool_calls + a2a_messages} round-trips` (combined per D-02)
  - **Agent count**: Outlined `Chip` showing `{agents_involved.length} agents`
- Removed old detailed metrics row containing: tool_calls, a2a_messages, failures, complexity, a2a_transport chips
- Preserved mcp_transport badge in header row
- Preserved talking point Paper section
- **Commit:** cd47327

## Deviations from Plan

None - plan executed exactly as written.

## Verification Results

| Check | Result |
|-------|--------|
| `npx tsc --noEmit` | PASS (exit 0) |
| `npm run build` | PASS (built in 1.54s) |
| grep `round-trips` | FOUND (line 877) |
| grep `agents_involved.length` | FOUND (line 882) |
| grep `bgcolor: getProtocolColor` | FOUND (line 874) |
| grep old chips (tools, A2A, failures) | NOT FOUND (removed) |
| grep `talking_point` | FOUND (preserved) |
| grep `mcp_transport` | FOUND (10 occurrences, preserved) |

## Known Stubs

None.

## Self-Check: PASSED

- [x] frontend/src/features/run-workspace/RunWorkspacePage.tsx exists and modified
- [x] Commit cd47327 exists in git log
- [x] All acceptance criteria verified
