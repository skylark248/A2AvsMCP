---
phase: "02-backend-trace-enrichment"
plan: "02"
subsystem: "frontend-types"
tags: [typescript, trace, types, tdd]
dependency_graph:
  requires: []
  provides:
    - "TraceEvent with 5 Phase 2 enrichment fields (api.ts)"
    - "TraceEventResponse with same 5 enrichment fields (api.generated.ts)"
    - "groupA2AEventsByTaskId() export in utils.ts"
  affects:
    - "frontend/src/components/traces/TraceExplorer.tsx (consumes TraceEvent)"
    - "Plan 03 accordion (imports groupA2AEventsByTaskId)"
tech_stack:
  added: []
  patterns:
    - "Manual patch of generated file with comment documenting regeneration path"
    - "TDD RED/GREEN for new utility function"
key_files:
  created:
    - "frontend/src/lib/trace/utils.groupA2AEventsByTaskId.test.ts"
  modified:
    - "frontend/src/lib/types/api.ts"
    - "frontend/src/lib/types/api.generated.ts"
    - "frontend/src/lib/trace/utils.ts"
decisions:
  - "Cast event.task_id via (event as { task_id?: unknown }).task_id — keeps task_id out of TraceEvent interface since it is A2A-internal, accessed through index signature"
  - "api.generated.ts manually patched with | null pattern matching existing generated fields; comment documents that generator re-run will include same fields after api_schemas.py update"
metrics:
  duration: "152s"
  completed: "2026-04-22"
  tasks_completed: 3
  files_modified: 4
---

# Phase 2 Plan 02: TypeScript Type Layer for Enriched Trace Fields Summary

TypeScript type coverage for 5 Phase 2 enrichment fields in both api.ts and api.generated.ts, plus a TDD-verified `groupA2AEventsByTaskId()` helper that Plan 03's protocol-tier accordion depends on.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add 5 Phase 2 fields to TraceEvent in api.ts | a19bcb0 | frontend/src/lib/types/api.ts |
| 2 | Add same 5 fields to TraceEventResponse in api.generated.ts | 281c47c | frontend/src/lib/types/api.generated.ts |
| 3 (RED) | Failing tests for groupA2AEventsByTaskId | d6dfc25 | frontend/src/lib/trace/utils.groupA2AEventsByTaskId.test.ts |
| 3 (GREEN) | Implement groupA2AEventsByTaskId() | ede8f10 | frontend/src/lib/trace/utils.ts |

## What Was Built

### Task 1 — TraceEvent enrichment (api.ts)

Added 5 optional fields to the hand-maintained `TraceEvent` interface:

```typescript
// Phase 2 enrichment fields
step_index?: number;
phase?: "discovery" | "execution";
parallel_batch_id?: string;
started_at?: number;
completed_at?: number;
```

### Task 2 — TraceEventResponse enrichment (api.generated.ts)

Added same 5 fields to the generated `TraceEventResponse` interface using the `| null` pattern consistent with FastAPI/Pydantic output:

```typescript
// Phase 2 enrichment fields (manually patched — re-running generator will also include these after api_schemas.py is updated)
step_index?: number | null;
phase?: "discovery" | "execution" | null;
parallel_batch_id?: string | null;
started_at?: number | null;
completed_at?: number | null;
```

### Task 3 — groupA2AEventsByTaskId() helper (utils.ts, TDD)

New export added to `frontend/src/lib/trace/utils.ts`. Groups A2A-related events by `task_id` for the Plan 03 protocol-tier accordion. Covers `a2a_message`, `a2a_remote_*`, `a2a_task_artifact`, `task_status`, `task_submit`, `task_complete` event types. Falls back to key `"unknown"` when `task_id` is absent. Non-A2A events are excluded entirely.

6 vitest tests cover: empty input, same-key grouping, multi-key separation, task_status inclusion, tool_call exclusion, unknown fallback.

## TDD Gate Compliance

- RED commit: `d6dfc25` — `test(02-02): add failing tests for groupA2AEventsByTaskId helper`
- GREEN commit: `ede8f10` — `feat(02-02): implement groupA2AEventsByTaskId() helper in utils.ts`
- All 6 tests pass. `npx tsc --noEmit` exits clean.

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None.

## Threat Flags

| Flag | File | Description |
|------|------|-------------|
| threat_flag: manual-patch | frontend/src/lib/types/api.generated.ts | File has "do not edit" warning; manual patch is intentional per T-02-04; comment in file documents regeneration path |

## Self-Check

## Self-Check: PASSED

| Item | Status |
|------|--------|
| frontend/src/lib/types/api.ts | FOUND |
| frontend/src/lib/types/api.generated.ts | FOUND |
| frontend/src/lib/trace/utils.ts | FOUND |
| frontend/src/lib/trace/utils.groupA2AEventsByTaskId.test.ts | FOUND |
| .planning/phases/02-backend-trace-enrichment/02-02-SUMMARY.md | FOUND |
| commit a19bcb0 (Task 1) | FOUND |
| commit 281c47c (Task 2) | FOUND |
| commit d6dfc25 (Task 3 RED) | FOUND |
| commit ede8f10 (Task 3 GREEN) | FOUND |
