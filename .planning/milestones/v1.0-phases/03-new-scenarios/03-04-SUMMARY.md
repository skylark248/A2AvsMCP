---
phase: 03-new-scenarios
plan: "04"
subsystem: ui
tags: [react, typescript, mui, vite]

# Dependency graph
requires:
  - phase: 03-new-scenarios
    plan: "01"
    provides: "TalkingPointResponse Pydantic model + talking_point field in TicketResponse backend; seed JSON with headline/sentence/callout for new scenarios"
provides:
  - TalkingPointCard TypeScript interface in api.generated.ts (headline, sentence, callout as required string fields)
  - talking_point optional field on TicketResponse and RunResult.ticket in TypeScript types
  - Paper import + protocolColor module-level map in RunWorkspacePage.tsx
  - Conditional TalkingPointCard JSX inline in result map with colored left border per protocol
affects:
  - 04-comparison-ui
  - 05-presentation-polish

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "protocolColor map: module-level Record<string, string> constant mapping mode keys to MUI color hex values; Phase 4 will promote this to eventColors.ts token file"
    - "api.ts dual-type pattern: inline ticket type in RunResult must mirror TicketResponse fields from api.generated.ts — both must be kept in sync"

key-files:
  created: []
  modified:
    - frontend/src/lib/types/api.generated.ts
    - frontend/src/lib/types/api.ts
    - frontend/src/features/run-workspace/RunWorkspacePage.tsx

key-decisions:
  - "D-14: TalkingPointCard rendered as inline JSX inside result map — not extracted to a separate component file (per plan decision)"
  - "D-15: protocolColor hardcoded at module level — Phase 4 will introduce eventColors.ts as the single token source; noted in comment"
  - "api.ts RunResult.ticket inline type must be patched alongside api.generated.ts TicketResponse — the two type definitions are independent and both feed RunWorkspacePage"

patterns-established:
  - "Phase 3 type patch comment: '// Phase 3: per-scenario talking point for presenter card (manually patched ...)' — follow this style for any future manual patches to api.ts or api.generated.ts"
  - "Optional chaining guard on ticket: item.ticket?.talking_point — protects against null ticket in result map; all talking_point access goes through this guard"

requirements-completed:
  - SCEN-03

# Metrics
duration: 15min
completed: 2026-04-23
---

# Phase 3 Plan 04: Frontend Talking-Point Card Summary

**TalkingPointCard TypeScript interface wired end-to-end from api.generated.ts through RunWorkspacePage.tsx with colored-border Paper renders per protocol mode**

## Performance

- **Duration:** 15 min
- **Started:** 2026-04-23T16:17:00Z
- **Completed:** 2026-04-23T16:32:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- Added `TalkingPointCard` interface (headline/sentence/callout) to `api.generated.ts` immediately before `TicketResponse`, plus `talking_point?: TalkingPointCard | null` field on `TicketResponse`
- Added `Paper` to MUI import block and `protocolColor` module-level const in `RunWorkspacePage.tsx`; conditional TalkingPointCard JSX renders below metric chips with protocol-colored left border
- Vite build and `npx tsc --noEmit` both exit 0 — full TypeScript type coverage maintained

## Task Commits

Each task was committed atomically:

1. **Task 1: TypeScript types — TalkingPointCard interface + TicketResponse.talking_point field** - `6f2f7d0` (feat)
2. **Task 2: RunWorkspacePage — Paper import, protocolColor map, TalkingPointCard JSX render** - `67638e1` (feat)

**Plan metadata:** (docs commit — see below)

## Files Created/Modified
- `frontend/src/lib/types/api.generated.ts` - Added TalkingPointCard interface before TicketResponse; added talking_point field to TicketResponse
- `frontend/src/lib/types/api.ts` - Added TalkingPointCard interface + talking_point field to RunResult inline ticket type (Rule 1 fix)
- `frontend/src/features/run-workspace/RunWorkspacePage.tsx` - Paper import, protocolColor const, conditional TalkingPointCard JSX in result map

## Decisions Made
- Kept TalkingPointCard JSX inline in the result map rather than extracting to a component file (D-14, per plan)
- Hardcoded protocolColor at module level with a comment pointing to Phase 4 eventColors.ts migration (D-15)
- Patched both `api.generated.ts` and `api.ts` — the two files maintain independent type definitions for the same data; both must be kept in sync

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added TalkingPointCard + talking_point to api.ts RunResult inline ticket type**
- **Found during:** Task 2 (RunWorkspacePage JSX — npm run build)
- **Issue:** `RunWorkspacePage.tsx` imports from `../../lib/types/api` (not `api.generated`), which has its own independent inline `ticket` type inside `RunResult`. That inline type had no `talking_point` field, causing 4 TypeScript errors: `Property 'talking_point' does not exist on type '{ ticket_id: string; ... }'`
- **Fix:** Added `TalkingPointCard` interface and `talking_point?: TalkingPointCard | null` field to the `RunResult.ticket` inline type in `api.ts` with a Phase 3 patch comment
- **Files modified:** `frontend/src/lib/types/api.ts`
- **Verification:** `npm run build` exits 0, `✓ built in 4.43s`
- **Committed in:** `67638e1` (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug: missing field in parallel type definition)
**Impact on plan:** Necessary correctness fix. The plan only mentioned `api.generated.ts` but the component's actual import path is `api.ts`. No scope creep — same interface, same field, different file.

## Issues Encountered
- `api.ts` maintains an independent hand-written `RunResult` interface with an inline `ticket` shape that is separate from `api.generated.ts` — these two type definitions must be kept in sync manually. Documented in `api.ts` with a Phase 3 patch comment.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 3 complete: all 4 plans done (seed data, parallel dispatch, pytest validation, frontend UI)
- Running `device_failure_warranty_refund` or `parallel_investigation` scenario will now display talking-point cards below each mode's metric chips
- Phase 4 (Comparison UI) can begin: `eventColors.ts` token file should subsume the `protocolColor` map added here

---
*Phase: 03-new-scenarios*
*Completed: 2026-04-23*
