---
phase: 11-tool-discovery-scenario
plan: 01
subsystem: frontend
tags: [refactor, frontend, mui, trace]
requirements: [DISC-02]
dependency_graph:
  requires: []
  provides:
    - "frontend/src/lib/trace/JsonTree.tsx (named exports JsonTree, FIELD_ANNOTATIONS, annotate)"
  affects:
    - "frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx (now imports JsonTree from shared module)"
tech_stack:
  added: []
  patterns:
    - "Shared rendering primitive lifted into lib/trace/ alongside existing eventColors.ts and utils.ts"
key_files:
  created:
    - frontend/src/lib/trace/JsonTree.tsx
  modified:
    - frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx
decisions: []
metrics:
  duration_minutes: 2
  completed_date: "2026-05-01"
  tasks_total: 2
  tasks_completed: 2
  files_changed: 2
  tests_pass: "286/286 (vitest, 31 files)"
---

# Phase 11 Plan 01: Extract JsonTree to Shared Module — Summary

**One-liner:** Lift `JsonTree`, `FIELD_ANNOTATIONS`, and `annotate()` out of `ProtocolEnvelopeDrawer.tsx` into `frontend/src/lib/trace/JsonTree.tsx` as three named exports, so Wave 1's `DiscoveryPhasePanel` can consume the same renderer without duplicating it.

## What Shipped

- **New module** `frontend/src/lib/trace/JsonTree.tsx` (106 lines) with three named exports moved verbatim from the drawer:
  - `FIELD_ANNOTATIONS: Record<string, string>` — 18-entry field-tooltip map
  - `annotate(key, parentKey?)` — annotation lookup helper
  - `JsonTree({data, depth?, parentKey?})` — recursive React component with per-key MUI Tooltip
- **Drawer updated** (`ProtocolEnvelopeDrawer.tsx` now 144 lines, was 250): inline definitions deleted, replaced by `import { JsonTree } from "../../lib/trace/JsonTree"`. Unused `Tooltip` removed from `@mui/material` named import (only the inline JsonTree referenced it). The `<JsonTree data={data} />` JSX usage at the bottom of the drawer is preserved unchanged — zero behavioral change.
- **Threat T-11-01-01 (Tampering)** mitigation verified: `grep -c "dangerouslySetInnerHTML" frontend/src/lib/trace/JsonTree.tsx` returns 0. Extraction is byte-for-byte; React's default text-escaping is preserved.

## Tasks Completed

| Task | Name                                                       | Commit  | Files                                              |
| ---- | ---------------------------------------------------------- | ------- | -------------------------------------------------- |
| 1    | Create `lib/trace/JsonTree.tsx` with three named exports   | 3b5aff9 | `frontend/src/lib/trace/JsonTree.tsx` (new, +106)  |
| 2    | Update drawer to import JsonTree; delete inline copies     | f5dd49a | `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` (-106 / +1) |

## Verification

- **Acceptance criteria — Task 1:** all 5 grep checks pass (file exists, 3 `^export ` lines, MUI import present, no `export default`, contains `FIELD_ANNOTATIONS` + `function JsonTree` literals).
- **Acceptance criteria — Task 2:** all 5 grep checks pass (no `^function JsonTree`, no `^const FIELD_ANNOTATIONS`, exactly 1 import from `../../lib/trace/JsonTree`, ≥1 `<JsonTree` usage, `Tooltip` reduced to 0 remaining occurrences in drawer).
- **Full vitest suite:** `cd frontend && npm test -- --run` → **286/286 tests passing across 31 files** (matches the documented baseline). Plan ships green.

## Deviations from Plan

None — plan executed exactly as written. The plan's optional Tooltip-removal branch ("if Tooltip becomes unused, drop it") triggered: the drawer body has zero remaining `Tooltip` references after JsonTree extraction, so `Tooltip` was removed from the MUI named import per the plan's explicit instruction.

### Notable Test-Run Observation (not a deviation, not a regression)

On the first full vitest run, `src/app/routes.test.tsx > "runs a demo and navigates from reports to report detail"` exceeded its 5000ms `testTimeout` once under suite-wide load. Re-running the file in isolation: 3/3 pass in 2.86s. Re-running the full suite: 286/286 pass in 16.32s. The refactor does not touch routes, demo wiring, or report-detail navigation; this is a known timing-sensitive test under cold-import load, not a regression introduced by the extraction.

## Threat Model Compliance

- **T-11-01-01 (Tampering on JsonTree rendering):** verified. No `dangerouslySetInnerHTML` introduced (`grep -c` = 0). React JSX text-node escaping preserved by byte-for-byte extraction.
- **T-11-01-02 (Information Disclosure):** verified. No new event types consumed; identical fields rendered with identical logic.

## DISC-02 Coverage Status

Partial. This plan delivers the **shared rendering primitive** that Wave 1's `DiscoveryPhasePanel` (Plan 11-03) is required to import (UI-SPEC line 145: "extract, do not duplicate"). DISC-02 closes when 11-03 + 11-04 ship; this plan unblocks both.

## Graphify

Ran `graphify update .` — AST re-extraction across 206 files produced 1565 nodes, 4135 edges, 111 communities. `graph.json`, `graph.html`, and `GRAPH_REPORT.md` regenerated in `graphify-out/`.

## Self-Check: PASSED

- [x] `frontend/src/lib/trace/JsonTree.tsx` exists.
- [x] Commit `3b5aff9` exists in `git log`.
- [x] `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx` modified.
- [x] Commit `f5dd49a` exists in `git log`.
- [x] Full vitest suite green (286/286).
