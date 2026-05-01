---
phase: 12-comparison-visualization-upgrades
plan: "01"
subsystem: frontend/traces
tags: [viz-01, diff-alignment, pure-function, vitest, typescript]
dependency_graph:
  requires:
    - frontend/src/lib/types/api.ts (TraceEvent shape, [key: string]: unknown index sig)
    - frontend/src/lib/trace/utils.ts (isTraceFailureEvent)
  provides:
    - frontend/src/components/traces/diffAlign.ts (alignTraces, DiffRow, DiffStatus)
    - frontend/src/components/traces/__tests__/diffAlign.test.ts (11 unit test cases)
  affects:
    - Plan 12-03 (AnnotatedDiffView imports alignTraces directly — alignment contract now locked)
tech_stack:
  added: []
  patterns:
    - Pure TypeScript function (no React, no DOM) in a .ts file co-located with components
    - IGNORE_FIELDS Set-based field exclusion for structural diff
    - Bucket-by-key Map<string, TraceEvent[]> for O(n+m) alignment
    - isTraceFailureEvent() + fault_ prefix check for divergenceCause="fault" classification
key_files:
  created:
    - frontend/src/components/traces/diffAlign.ts
    - frontend/src/components/traces/__tests__/diffAlign.test.ts
  modified: []
decisions:
  - "turn_index coerced via (e as { turn_index?: unknown }).turn_index ?? 0 — not statically declared on TraceEvent"
  - "divergenceCause='fault' when isTraceFailureEvent(l)!==isTraceFailureEvent(r) OR any differing field starts with fault_"
  - "All 11 IGNORE_FIELDS excluded: timestamp_ms, started_at, completed_at, index, parallel_batch_id, task_id, messageId, contextId, artifactId, run_id, lane"
  - "node_modules symlinked (not committed) from main project into worktree for vitest execution"
metrics:
  duration: "~20 minutes"
  completed_date: "2026-05-01"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 0
---

# Phase 12 Plan 01: alignTraces Pure Function + Vitest — Summary

VIZ-01 alignment foundation: pure `alignTraces(left, right): DiffRow[]` function with O(n+m)
bucket-by-(turn_index, event_type) algorithm, full field comparison with IGNORE_FIELDS exclusion,
fault/field divergenceCause classification, and 11 vitest cases locking the contract for Plan 12-03.

## Function Signature Shipped

```typescript
export type DiffStatus = "added" | "removed" | "matched-equal" | "matched-divergent";

export interface DiffRow {
  status: DiffStatus;
  left?: TraceEvent;
  right?: TraceEvent;
  turnIndex: number;
  divergenceCause?: "fault" | "field";
  differingFields?: string[];
}

export function alignTraces(left: TraceEvent[], right: TraceEvent[]): DiffRow[];
```

Exports: `alignTraces`, `DiffRow`, `DiffStatus` — exactly the surface required by the plan and consumed by Plan 12-03's `AnnotatedDiffView`.

## IGNORE_FIELDS Set

```typescript
const IGNORE_FIELDS = new Set<string>([
  "timestamp_ms", "started_at", "completed_at", "index",
  "parallel_batch_id", "task_id", "messageId", "contextId",
  "artifactId", "run_id", "lane",
]);
```

These 11 fields always differ between protocol runs without signaling behavioral divergence (wall-clock timestamps, per-run UUIDs, protocol lane labels).

## Algorithm

1. **Bucket pass:** Group each side into `Map<"${turnIndex}::${event_type}", TraceEvent[]>`.
2. **Pairing pass:** For each unique key, pair `left[i]` with `right[i]` by arrival order. Surplus on left → `removed`. Surplus on right → `added`.
3. **Field comparison:** For matched pairs, iterate union of own keys minus IGNORE_FIELDS. Stringify-compare values. If any differ → `matched-divergent`.
4. **Cause classification:** `divergenceCause="fault"` iff `isTraceFailureEvent(l) !== isTraceFailureEvent(r)` OR any differing field name starts with `"fault_"`. Otherwise `"field"`.
5. **Sort:** By `turnIndex` ascending, then `matched-equal < matched-divergent < removed < added` within a turn.

## Vitest Case Names and Counts

File: `frontend/src/components/traces/__tests__/diffAlign.test.ts`
Total: **11 passing test cases** (pure TypeScript, no React, no ThemeProvider)

| # | Test name | Status/cause covered |
|---|-----------|----------------------|
| 1 | returns empty array for empty inputs | edge case |
| 2 | classifies same (turn_index, event_type) with identical non-trivial fields as matched-equal | matched-equal |
| 3 | classifies field-only difference as matched-divergent with cause=field | matched-divergent/field |
| 4 | classifies fault-only-on-one-side as matched-divergent with cause=fault (fault_ field differs) | matched-divergent/fault (fault_ prefix) |
| 5 | classifies left-only event as removed and right-only event as added | removed + added |
| 6 | includes every event_type in output (D-76 — no pre-filter) | D-76 scope guarantee |
| 7 | sorts within a turn bucket as matched-equal, matched-divergent, removed, added | within-turn sort order |
| 8 | orders rows ascending by turnIndex across buckets | cross-turn sort order |
| 9 | handles multiple events of same (turn_index, event_type) by pairing in arrival order | Pitfall 8 |
| 10 | classifies matched-divergent with cause=fault when isTraceFailureEvent disagrees | matched-divergent/fault (isTraceFailureEvent) |
| 11 | treats all IGNORE_FIELDS differences as matched-equal | IGNORE_FIELDS exhaustive |

Full suite result: **302/302 passing** (291 baseline + 11 new).

## Forbidden Import Check (D-85)

| Import | Status |
|--------|--------|
| `@xyflow/react` | 0 matches — PASS |
| `from "motion` | 0 matches — PASS |
| Any diff library | Not imported — PASS |

## Worktree Execution Note

The worktree's `frontend/` directory had no `node_modules`. A symlink was created from the worktree's `frontend/node_modules` → main project's `frontend/node_modules` to enable vitest execution. The symlink is untracked (not committed). TypeScript check was run against the main project's `tsc` binary for the same reason.

## Deviations from Plan

None — plan executed exactly as written. The algorithm skeleton in 12-RESEARCH.md §1 (lines 568-655) was used as the spine with no structural changes. Two additional test cases beyond the required 6 were added (tests 9 and 11) to cover Pitfall 8 (arrival-order pairing) and the full IGNORE_FIELDS set exhaustively.

## Self-Check

### Files exist:
- `frontend/src/components/traces/diffAlign.ts`: EXISTS
- `frontend/src/components/traces/__tests__/diffAlign.test.ts`: EXISTS

### Commits exist:
- `97ec400`: feat(12-01): implement alignTraces pure function
- `d6c8561`: test(12-01): vitest coverage for alignTraces

## Self-Check: PASSED

Both files exist. Both commits verified. All 302 vitest cases pass. TypeScript clean. Forbidden imports absent. No stubs. No threat surface introduced.
