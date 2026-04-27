---
phase: 05-presentation-polish
plan: 01
subsystem: ui
tags: [glossary, mui-tooltip, typescript, react]

requires:
  - phase: 04-compare-visualisation
    provides: "MUI component patterns and FIELD_ANNOTATIONS analog"
provides:
  - "glossaryTerms.ts — 17-term static Record<string, string> for protocol vocabulary"
  - "GlossaryTerm.tsx — reusable Tooltip + dotted-underline span component"
affects: [05-03-PLAN, presentation-polish]

tech-stack:
  added: []
  patterns: ["Module-level static Record for term definitions", "Inline style span with MUI Tooltip for glossary popovers"]

key-files:
  created:
    - frontend/src/lib/glossary/glossaryTerms.ts
    - frontend/src/components/glossary/GlossaryTerm.tsx
  modified: []

key-decisions:
  - "Used inline style on span instead of Box+sx -- simpler, avoids extra MUI wrapper, span provides DOM ref for Tooltip"
  - "Em dashes (--) in definitions matching RESEARCH.md copywriting pattern"

patterns-established:
  - "Glossary data pattern: module-level Record<string, string> keyed by term slug"
  - "Glossary UI pattern: GlossaryTerm component wraps children in Tooltip+dotted-underline span"

requirements-completed: [PRES-02]

duration: 1min
completed: 2026-04-27
---

# Phase 5 Plan 01: Glossary System Summary

**Static 17-term glossary data map (glossaryTerms.ts) and GlossaryTerm component with MUI Tooltip + dotted-underline hover popovers**

## Performance

- **Duration:** 1m 5s
- **Started:** 2026-04-27T04:45:57Z
- **Completed:** 2026-04-27T04:47:02Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Created glossaryTerms.ts with exactly 17 protocol term definitions (mcp, a2a, tool_call, task_submit, agent_card, transport, broker, specialist_agent, parallel_dispatch, step_index, parallel_batch_id, discovery_phase, execution_phase, mock_runtime, llm_runtime, baseline, hybrid)
- Created GlossaryTerm component with MUI Tooltip on hover, dotted underline via borderBottom, cursor: help, and bare-children fallback for unknown terms
- TypeScript compiles cleanly with no errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Create glossaryTerms.ts static data map** - `5128a65` (feat)
2. **Task 2: Create GlossaryTerm component** - `eb1d7e3` (feat)

## Files Created/Modified
- `frontend/src/lib/glossary/glossaryTerms.ts` - Static Record<string, string> with 17 protocol term definitions
- `frontend/src/components/glossary/GlossaryTerm.tsx` - Reusable glossary popover component (Tooltip + dotted underline span)

## Decisions Made
- Used inline `style` on `<span>` instead of MUI `Box component="span" sx={...}` -- simpler, avoids extra MUI wrapper, and plain span provides the DOM ref that MUI Tooltip requires on its direct child
- Kept em dashes (--) in definitions matching the RESEARCH.md copywriting convention

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Glossary infrastructure ready for Plan 03 to wire GlossaryTerm into RunWorkspacePage and ComparePage
- glossaryTerms map can be extended with additional terms as needed

---
*Phase: 05-presentation-polish*
*Completed: 2026-04-27*
