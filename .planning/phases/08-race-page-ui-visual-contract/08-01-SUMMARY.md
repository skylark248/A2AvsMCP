---
phase: 08-race-page-ui-visual-contract
plan: "01"
subsystem: frontend/race-foundation
tags: [frontend, mui, design-tokens, glossary, accessibility, context]
dependency_graph:
  requires: []
  provides:
    - frontend/src/lib/types/race.ts (FailureTag, RaceLane, PageState, RaceEvent, LaneState, RaceState)
    - frontend/src/lib/trace/eventColors.ts (failureTagColor map — 5 entries)
    - frontend/src/features/race/context/FirstMentionProvider.tsx (FirstMentionProvider, useFirstMention)
    - frontend/src/components/glossary/GlossaryTerm.tsx (Popover+Tooltip branch)
    - frontend/src/lib/glossary/glossaryTerms.ts (8 new race terms)
  affects:
    - Plans 02-06 (all import from race.ts and/or consume failureTagColor)
    - Run/Compare pages (GlossaryTerm backward-compat via Tooltip branch preserved)
tech_stack:
  added: []
  patterns:
    - MUI Popover + Button (Got it dismiss) for first-mention educational UX
    - React Context + useCallback/useMemo for route-scoped Set tracking
    - Record<ClosedUnion, StyleShape> static lookup map (failureTagColor)
key_files:
  created:
    - frontend/src/lib/types/race.ts
    - frontend/src/lib/trace/eventColors.test.ts
    - frontend/src/features/race/context/FirstMentionProvider.tsx
    - frontend/src/features/race/context/FirstMentionProvider.test.tsx
    - frontend/src/components/glossary/GlossaryTerm.test.tsx
  modified:
    - frontend/src/lib/trace/eventColors.ts
    - frontend/src/lib/glossary/glossaryTerms.ts
    - frontend/src/components/glossary/GlossaryTerm.tsx
decisions:
  - "useFirstMention returns null (not throw) outside provider — GlossaryTerm is used on Run/Compare pages; backward-compat per D-51"
  - "MUI icon typeof is 'object' (forwardRef wrapper) not 'function'; test updated to accept both types"
  - "sessionStorage/localStorage grep returns 1 (comment only, no functional access) — D-51 compliant"
metrics:
  duration_minutes: 25
  completed_date: "2026-04-29"
  tasks_completed: 2
  files_changed: 8
---

# Phase 8 Plan 01: Race Foundation — Types, Colors, Glossary, First-Mention UX Summary

Wave 1 foundation: failureTagColor map (5 entries), 8 race glossary terms, FirstMentionProvider route-scoped context, and GlossaryTerm Popover-on-first-mention branch.

## Files Created

| File | Purpose |
|------|---------|
| `frontend/src/lib/types/race.ts` | Closed-set type contracts: FailureTag, RaceLane, PageState, RaceEvent, LaneState, RaceState — all downstream Plans 02-06 import from here |
| `frontend/src/features/race/context/FirstMentionProvider.tsx` | Route-scoped React Context tracking seen glossary terms via Set<string>; exports FirstMentionProvider + useFirstMention |
| `frontend/src/features/race/context/FirstMentionProvider.test.tsx` | 7 tests covering null-outside-provider, hasSeen/markSeen lifecycle, independent Set isolation, reset-on-remount |
| `frontend/src/components/glossary/GlossaryTerm.test.tsx` | 10 tests covering outside-provider Tooltip regression, inside-provider first-mention Popover, Got-it dismiss, subsequent Tooltip, 8 glossary term presence |
| `frontend/src/lib/trace/eventColors.test.ts` | 10 tests covering 5-entry count, exact bg/label values per UI-SPEC, Icon presence, regression guard for protocolColor/toneColor |

## Files Modified

| File | Change |
|------|--------|
| `frontend/src/lib/trace/eventColors.ts` | Added imports for 5 MUI icons + FailureTag type; added `failureTagColor: Record<FailureTag, FailureTagStyle>` with 5 entries; preserved all existing exports |
| `frontend/src/lib/glossary/glossaryTerms.ts` | Appended 8 race terms (ttff, recovery_rate, hardness_profile, recovered, gave_up, kept_going_without_noticing, kept_going_to_failure, indeterminate) with verbatim UI-SPEC definitions |
| `frontend/src/components/glossary/GlossaryTerm.tsx` | Added useFirstMention import; added Popover-on-first-mention branch with Got it dismiss; preserved existing Tooltip branch for subsequent mentions and outside-provider usage |

## failureTagColor Map (UIRACE-04, D-46)

5-entry `Record<FailureTag, {bg, text, Icon, label}>` — single source of truth, color always paired with icon + label:

| Key | bg | text | Icon | Label |
|-----|----|------|------|-------|
| `recovered` | `#e8f5e9` | `#1b5e20` | CheckCircleOutlineIcon | "Recovered" |
| `gave_up` | `#fce4ec` | `#880e4f` | CancelOutlinedIcon | "Gave Up" |
| `kept_going_without_noticing` | `#fff3e0` | `#e65100` | VisibilityOffOutlinedIcon | "Kept Going (Unaware)" |
| `kept_going_to_failure` | `#fbe9e7` | `#bf360c` | ErrorOutlineIcon | "Kept Going to Failure" |
| `indeterminate` | `#f5f5f5` | `#424242` | HelpOutlineIcon | "Indeterminate" |

## 8 Glossary Terms Appended (UIRACE-07)

All definitions verbatim from UI-SPEC Glossary Extension table (lines 311-319):

- `ttff` — Time to first fault elapsed ms from run start
- `recovery_rate` — Fraction of runs agent fully recovered from injected fault
- `hardness_profile` — Structured description of task difficulty characteristics
- `recovered` — Fault tag: detected + returned to correct path within K=3 turns
- `gave_up` — Fault tag: detected + abandoned task
- `kept_going_without_noticing` — Fault tag: did not acknowledge fault, continued
- `kept_going_to_failure` — Fault tag: continued past fault, produced incorrect result
- `indeterminate` — Fault tag: insufficient evidence to assign primary tag

## FirstMentionProvider Behavior (D-51)

- `FirstMentionProvider`: mounts a fresh `Set<string>()` on every mount — route exit (unmount) resets Set
- `useFirstMention()`: returns `null` outside provider (NOT throw) for backward-compat with Run/Compare pages
- Inside provider: returns `{ hasSeen(term): boolean, markSeen(term): void }`
- No sessionStorage / localStorage access — D-51 explicit forbid; every viewer gets educational moment fresh

## GlossaryTerm Branch Logic (D-50)

1. **First mention inside provider** (`firstMention !== null && !firstMention.hasSeen(term)`): renders dashed-underline clickable span + MUI Popover with definition + "Got it" Button; clicking "Got it" calls `markSeen(term)` and closes Popover
2. **Subsequent mention inside provider** (after Got-it dismissal): renders existing Tooltip branch
3. **Outside provider** (`firstMention === null`): renders existing Tooltip branch — Run/Compare pages unaffected

`data-testid` attributes: `glossary-term-first-{term}` (first-mention span) and `glossary-term-tooltip-{term}` (Tooltip span).

## Plans 02-06 Import Surface from frontend/src/lib/types/race.ts

```typescript
import type { FailureTag, RaceLane, PageState, RaceEvent, LaneState, RaceState } from "../lib/types/race";
```

All 6 type exports are stable for Plans 02-06:
- `FailureTag` — consumed by failureTagColor (Plan 04 FailureStateBadge, Plan 05 HeatmapScaffold)
- `RaceLane` — consumed by lane cards (Plan 04)
- `PageState` — consumed by status strip (Plan 02) and page-state machine (Plan 06)
- `RaceEvent` — consumed by useRaceStream reducer (Plan 03)
- `LaneState` — consumed by RaceLaneCard (Plan 04)
- `RaceState` — consumed by RacePage (Plan 06)

## Test Results

- `eventColors.test.ts`: 10/10 passed
- `FirstMentionProvider.test.tsx`: 7/7 passed
- `GlossaryTerm.test.tsx`: 10/10 passed
- TypeScript: `npx tsc --noEmit` exits 0
- Build: `npm run build` exits 0 in 2.88s

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 | `954d80f` | feat(08-01): race types + failureTagColor map (UIRACE-04, D-46) |
| Task 2 | `9415196` | feat(08-01): FirstMentionProvider, GlossaryTerm Popover branch, 8 race glossary terms |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] MUI icon typeof is "object" not "function"**
- **Found during:** Task 1, GREEN phase test run
- **Issue:** Test asserted `typeof value.Icon === "function"` but MUI SvgIcon components are `React.forwardRef` wrappers with `typeof === "object"`
- **Fix:** Updated test to accept both `"function"` and `"object"` with an explanatory comment; the implementation is correct (Icons are valid ComponentType values)
- **Files modified:** `frontend/src/lib/trace/eventColors.test.ts`
- **Commit:** `954d80f`

**2. [Rule N/A - Note] sessionStorage/localStorage grep count = 1**
- **Context:** The acceptance criterion says `grep -c "sessionStorage\|localStorage" ... equals 0`; actual count is 1 because the implementation includes a comment `// D-51: Set reset on mount. No sessionStorage / localStorage.` — the grep finds the comment line, not functional code. D-51 is fully compliant; no actual storage API is called.

## Known Stubs

None — all exports are fully implemented with real values. No placeholder data, no TODO comments in implementation files.

## Threat Flags

None — no new network endpoints, auth paths, or file access patterns introduced. All additions are static frontend modules (React components, static Records). Threat model in plan frontmatter covers all surfaces.

## Self-Check: PASSED
