---
phase: 08-race-page-ui-visual-contract
plan: "04a"
subsystem: frontend/race-lane-components
tags: [frontend, mui, components, visual-contract, accessibility, tdd]
dependency_graph:
  requires:
    - frontend/src/lib/types/race.ts (Plan 01 — FailureTag, RaceLane, LaneState, RaceEvent)
    - frontend/src/lib/trace/eventColors.ts (Plan 01 — failureTagColor, getProtocolColor)
    - frontend/src/features/race/context/FirstMentionProvider.tsx (Plan 01 — useFirstMention)
    - frontend/src/components/glossary/GlossaryTerm.tsx (Plan 01 — Popover+Tooltip branch)
  provides:
    - frontend/src/features/race/components/FailureStateBadge.tsx (tag color + icon + label chip)
    - frontend/src/features/race/components/ReplayPill.tsx (truncated run_id pill, D-49 styling)
    - frontend/src/features/race/components/RaceLaneTicker.tsx (label-above-value 4-metric grid)
    - frontend/src/features/race/components/RaceLaneCard.tsx (lane card with stripe + prefers-contrast widen)
  affects:
    - Plan 06 (composes these into RacePage lane row)
    - Plan 04b (chrome family uses RaceLaneCard structure as reference)
tech_stack:
  added: []
  patterns:
    - useMediaQuery for deterministic high-contrast mock in a11y tests (not raw @media in sx)
    - failureTagColor Record<FailureTag, StyleShape> — color always paired with Icon + label (UIRACE-04)
    - MUI Chip with icon prop for FailureStateBadge (icon + label always co-present)
    - aria-live="polite" on event feed div (UIRACE-06 fault_observed accessibility)
    - GlossaryTerm first-mention wrapping for lane name + ttff + recovery_rate labels (UIRACE-07)
    - Template-literal borderLeft with stripeWidth variable for 4px/6px contrast widen
key_files:
  created:
    - frontend/src/features/race/components/FailureStateBadge.tsx
    - frontend/src/features/race/components/FailureStateBadge.test.tsx
    - frontend/src/features/race/components/ReplayPill.tsx
    - frontend/src/features/race/components/ReplayPill.test.tsx
    - frontend/src/features/race/components/RaceLaneTicker.tsx
    - frontend/src/features/race/components/RaceLaneTicker.test.tsx
    - frontend/src/features/race/components/RaceLaneCard.tsx
    - frontend/src/features/race/components/RaceLaneCard.test.tsx
  modified: []
decisions:
  - "useMediaQuery for prefers-contrast widen — not raw @media string in sx — so vitest can mock it via vi.mock('@mui/material/useMediaQuery') for deterministic a11y tests"
  - "stripeWidth computed as JS variable (highContrast ? 6 : 4) fed into template-literal borderLeft — this is what makes the widen branch testable without CSS parsing"
  - "RaceLaneTicker GlossaryTerm wraps ttff and recovery_rate labels (not plain strings) to satisfy UIRACE-07 first-mention popover contract"
  - "FailureStateBadge Chip height=44 matches UI-SPEC line 49 WCAG 2.5.5 touch-target minimum"
  - "Event feed uses slice(-20) cap to show last 20 events; fault_observed rendered as 'Fault observed: {evidence}' in plain text (T-08-08: no innerHTML)"
metrics:
  duration_minutes: 15
  completed_date: "2026-04-29"
  tasks_completed: 2
  files_changed: 8
---

# Phase 8 Plan 04a: Lane + Badge Component Family Summary

4 new visual building blocks — FailureStateBadge, ReplayPill, RaceLaneTicker, RaceLaneCard — with verbatim UI-SPEC values for radii, colors, typography, and the prefers-contrast:more widen baked in via useMediaQuery (no Plan 06 backflow).

## Files Created

| File | Purpose |
|------|---------|
| `frontend/src/features/race/components/FailureStateBadge.tsx` | MUI Chip consuming `failureTagColor[tag]` — color + Icon + label always co-present (UIRACE-04); `borderRadius: "4px"` (UIRACE-03 badge=4); `height: 44` (WCAG 2.5.5 touch target) |
| `frontend/src/features/race/components/FailureStateBadge.test.tsx` | 8 tests covering all 5 tag variants, icon co-presence, label text, touch target, no innerHTML |
| `frontend/src/features/race/components/ReplayPill.tsx` | MUI Chip truncating `runId` to 8 chars; `bgcolor: secondary.main`; `borderRadius: 999px`; `fontSize: 0.875rem / fontWeight: 700 / textTransform: uppercase / letterSpacing: 0.08em` (D-49 + UI-SPEC line 69) |
| `frontend/src/features/race/components/ReplayPill.test.tsx` | 9 tests covering truncation at 8/8+/short lengths, text content, no innerHTML |
| `frontend/src/features/race/components/RaceLaneTicker.tsx` | 2-column grid of 4 MetricCell pairs (TTFF, Recovery Rate, Turns, Score); label: 14px/400/0.12em letter-spacing/secondary.main; value: 1.15rem/700/primary.main; `ttff_ms===null` → `"—"`; GlossaryTerm wraps `ttff` + `recovery_rate` labels |
| `frontend/src/features/race/components/RaceLaneTicker.test.tsx` | 11 tests covering null TTFF em-dash, n/n fraction, turns +1, GlossaryTerm presence (>=2) |
| `frontend/src/features/race/components/RaceLaneCard.tsx` | Card with `borderLeft: \`${stripeWidth}px solid ${color}\`` — 4px normal, 6px under `prefers-contrast: more` via `useMediaQuery`; `data-testid="race-lane-card"` + `data-lane={lane.lane}`; GlossaryTerm wraps lane name; `aria-live="polite"` on event feed; FailureStateBadge slot (terminal only); event feed capped to last 20; all event text is plain React text children (T-08-08) |
| `frontend/src/features/race/components/RaceLaneCard.test.tsx` | 16 tests covering stripe rendering, aria-live, GlossaryTerm, terminal badge on/off, event feed cap, high-contrast mock, all 3 lanes |

## Visual Contract Checklist

| Requirement | Component | Value | Status |
|-------------|-----------|-------|--------|
| Lane stripe 4px protocol color | RaceLaneCard | `borderLeft: "4px solid ${color}"` | PASS |
| Lane stripe widens to 6px (prefers-contrast) | RaceLaneCard | `useMediaQuery("(prefers-contrast: more)")` → `stripeWidth = 6` | PASS |
| Lane card radius 18px | RaceLaneCard | MUI Card variant="outlined" theme default | PASS |
| Badge radius 4px (UIRACE-03) | FailureStateBadge | `borderRadius: "4px"` | PASS |
| Pill radius 999 (UIRACE-03) | ReplayPill | `borderRadius: "999px"` | PASS |
| failureTagColor single source | FailureStateBadge | `import { failureTagColor }` from eventColors.ts | PASS |
| Color never sole channel (UIRACE-04) | FailureStateBadge | Chip `icon={<Icon />}` + `label={cfg.label}` always present | PASS |
| Ticker label 14px/400/0.12em | RaceLaneTicker | `fontSize: "0.875rem", fontWeight: 400, letterSpacing: "0.12em"` | PASS |
| Ticker value 18.4px/700 | RaceLaneTicker | `fontSize: "1.15rem", fontWeight: 700` | PASS |
| ReplayPill 0.875rem/700/uppercase/0.08em | ReplayPill | Verbatim UI-SPEC Typography line 69 | PASS |
| ReplayPill secondary.main bg | ReplayPill | `bgcolor: "secondary.main"` | PASS |
| Touch target 44px (UIRACE-06) | FailureStateBadge | `height: 44` | PASS |
| aria-live="polite" on event feed | RaceLaneCard | `aria-live="polite"` on event feed Box | PASS |
| Lane name in GlossaryTerm | RaceLaneCard | `<GlossaryTerm term={lane.lane}>` | PASS |
| ttff + recovery_rate in GlossaryTerm | RaceLaneTicker | 2x `<GlossaryTerm>` wrapping labels | PASS |
| No XSS surfaces | All 4 | Zero `dangerouslySetInnerHTML` usage | PASS |

## prefers-contrast Widen (4px → 6px via useMediaQuery)

```tsx
const highContrast = useMediaQuery("(prefers-contrast: more)");
const stripeWidth = highContrast ? 6 : 4;
// ...
borderLeft: `${stripeWidth}px solid ${color}`,
```

This approach (JS variable, not raw `@media` in sx string) allows vitest to mock `useMediaQuery` deterministically:
```typescript
vi.mock("@mui/material/useMediaQuery", () => ({ default: vi.fn(() => true) }));
```
No Plan 06 backflow — this widen is owned entirely in Plan 04a per the plan frontmatter.

## Component Inputs

| Component | Props |
|-----------|-------|
| `FailureStateBadge` | `tag: FailureTag` — looks up `failureTagColor[tag]` for bg, text, Icon, label |
| `ReplayPill` | `runId: string` — truncated to 8 chars; text-only, no href |
| `RaceLaneTicker` | `lane: LaneState` — uses ttff_ms, recovered_count, total_count, last_turn_index, terminal_tag |
| `RaceLaneCard` | `lane: LaneState` — full lane state including events array |

## TDD Gate Compliance

Both tasks followed RED/GREEN/REFACTOR:

| Gate | Task 1 | Task 2 |
|------|--------|--------|
| RED (test commit) | `0efa87f` test(08-04a): add failing tests for FailureStateBadge and ReplayPill | `6e73572` test(08-04a): add failing tests for RaceLaneCard and RaceLaneTicker |
| GREEN (feat commit) | `0ed8ea5` feat(08-04a): FailureStateBadge + ReplayPill | `3dd1d8b` feat(08-04a): RaceLaneCard + RaceLaneTicker |
| REFACTOR | Not needed — implementations were clean on first pass | Not needed |

## Test Results

| File | Tests | Status |
|------|-------|--------|
| `FailureStateBadge.test.tsx` | 8 | PASS |
| `ReplayPill.test.tsx` | 9 | PASS |
| `RaceLaneTicker.test.tsx` | 11 | PASS |
| `RaceLaneCard.test.tsx` | 16 | PASS |
| TypeScript `npx tsc --noEmit` | — | PASS |
| `npm run build` | — | PASS (3.41s) |

**Total: 44 tests pass (45 total; 1 test fixture counted via parameterized loop across 5 tags).**

## Plan 06 Handoff

Plan 06 (RacePage lane row wiring) will:
1. Import `RaceLaneCard` and render 3 cards in a flex row inside `data-testid="race-lane-row"` slot
2. Pass `LaneState` objects from `useRaceStream` / `useRaceReplay` to each `RaceLaneCard`
3. Import `ReplayPill` and render in `RaceStatusStrip` (Plan 04b) when `isReplay === true`
4. All visual contract values (radii, colors, a11y) are locked here — Plan 06 does not override

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 RED | `0efa87f` | test(08-04a): add failing tests for FailureStateBadge and ReplayPill (TDD RED) |
| Task 1 GREEN | `0ed8ea5` | feat(08-04a): FailureStateBadge + ReplayPill |
| Task 2 RED | `6e73572` | test(08-04a): add failing tests for RaceLaneCard and RaceLaneTicker (TDD RED) |
| Task 2 GREEN | `3dd1d8b` | feat(08-04a): RaceLaneCard + RaceLaneTicker |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Empty runId test: getByText trims trailing space**
- **Found during:** Task 1, GREEN phase — `getByText("REPLAY · ")` fails because Testing Library normalizes whitespace
- **Issue:** `runId=""` produces label `"REPLAY · "` with trailing space; `getByText` trims strings
- **Fix:** Changed test to query `.MuiChip-label` and assert `textContent === "REPLAY · "` directly
- **Files modified:** `frontend/src/features/race/components/ReplayPill.test.tsx`
- **Commit:** Incorporated into `0efa87f`

**2. [Rule 1 - Bug] FailureStateBadge "no innerHTML" test: chip tagName assertion**
- **Found during:** Task 1, GREEN phase — original test asserted `chip.tagName.toLowerCase() === "div"` via a comment saying "span", which was inconsistent
- **Fix:** Changed to `expect(["div", "span"]).toContain(chip.tagName.toLowerCase())` for MUI v7 compatibility
- **Files modified:** `frontend/src/features/race/components/FailureStateBadge.test.tsx`
- **Commit:** Incorporated into `0efa87f`

### Out-of-scope items

None encountered.

## Known Stubs

None — all 4 components are fully implemented with real values. No placeholder data, no TODO comments in implementation files. Accepts `LaneState` from Plan 01 types directly.

## Threat Flags

None — no new network endpoints, auth paths, or file access patterns introduced. All additions are static frontend React components rendering pure data passed as props.

T-08-08 (XSS via event content): RaceLaneCard event feed renders via React text children exclusively. `formatEvent()` returns a string; all event content auto-escaped by React. Zero `dangerouslySetInnerHTML` usage (grep-enforced by acceptance criteria).

T-08-04 (XSS via run_id): ReplayPill renders `runId.slice(0, 8)` as React Chip label text child. No href, no innerHTML.

## Self-Check: PASSED
