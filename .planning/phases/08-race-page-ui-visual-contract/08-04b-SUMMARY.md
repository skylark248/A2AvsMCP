---
phase: 08-race-page-ui-visual-contract
plan: "04b"
subsystem: frontend/race-chrome-components
tags: [frontend, mui, components, visual-contract, accessibility, tdd]
dependency_graph:
  requires:
    - frontend/src/lib/types/race.ts (Plan 01 — PageState type, 12-value enum)
    - frontend/src/features/race/components/ReplayPill.tsx (Plan 04a — right-aligned pill)
    - frontend/src/components/glossary/GlossaryTerm.tsx (Plan 01 — first-mention popover + Tooltip)
    - frontend/src/features/race/context/FirstMentionProvider.tsx (Plan 01 — route-scoped context)
    - frontend/src/lib/glossary/glossaryTerms.ts (ttff, recovery_rate, hardness_profile entries)
  provides:
    - frontend/src/features/race/components/RaceStatusStrip.tsx (48px strip, all 12 page-state labels, ReplayPill slot)
    - frontend/src/features/race/components/CharacteristicFailureBanner.tsx (4px primary rule, role=banner, italic clause)
    - frontend/src/features/race/components/MethodologySection.tsx (flat aside, GlossaryTerm prose)
  affects:
    - Plan 06 (composes RaceStatusStrip + CharacteristicFailureBanner + MethodologySection into RacePage chrome slots)
tech_stack:
  added: []
  patterns:
    - STATUS_LABEL Record<PageState, string> — verbatim UI-SPEC Copywriting Contract (12 states)
    - aria-live="polite" on status label container for WS reconnect announcements (UI-SPEC line 233)
    - NO_TIMESTAMP_STATES Set to suppress timestamp suffix on transient states
    - Banner borderLeft="4px solid" + borderColor="primary.main" pattern (UIRACE-03)
    - borderRadius=0 for banner (UIRACE-03 explicit zero)
    - GlossaryTerm first-mention wrapping for ttff + recovery_rate + hardness_profile (UIRACE-07)
    - Flat Box component="aside" + role="complementary" (no Paper/Card — UIRACE-03)
key_files:
  created:
    - frontend/src/features/race/components/RaceStatusStrip.tsx
    - frontend/src/features/race/components/RaceStatusStrip.test.tsx
    - frontend/src/features/race/components/CharacteristicFailureBanner.tsx
    - frontend/src/features/race/components/CharacteristicFailureBanner.test.tsx
    - frontend/src/features/race/components/MethodologySection.tsx
    - frontend/src/features/race/components/MethodologySection.test.tsx
  modified: []
decisions:
  - "STATUS_LABEL record has all 12 PageState keys — done/replay/sparse-heatmap/indeterminate/lane-failed/heatmap-empty all share Completed base label; timestampLabel suffix added by Plan 06 at runtime"
  - "NO_TIMESTAMP_STATES Set gates the timestamp suffix — ws-disconnected/ws-reconnecting/pre-race/live states never append a timestamp even if caller passes one"
  - "CharacteristicFailureBanner uses Box (not Paper) to satisfy UIRACE-03 borderRadius=0 — Paper default radius would override sx borderRadius: 0 in some MUI versions"
  - "MethodologySection JSDoc avoids Paper/Card keyword to pass the comment-stripped grep acceptance criterion"
  - "Banner JSDoc avoids dangerouslySetInnerHTML keyword — uses 'no XSS surface' phrasing instead"
metrics:
  duration_minutes: 20
  completed_date: "2026-04-29"
  tasks_completed: 2
  files_changed: 6
---

# Phase 8 Plan 04b: Page Chrome Component Family Summary

3 page chrome components — RaceStatusStrip, CharacteristicFailureBanner, MethodologySection — with verbatim UI-SPEC values for heights, radii, colors, typography, ARIA roles, and the first-mention GlossaryTerm contract.

## Files Created

| File | Purpose |
|------|---------|
| `frontend/src/features/race/components/RaceStatusStrip.tsx` | 48px sticky strip — `STATUS_LABEL` Record with all 12 `PageState` values per UI-SPEC Copywriting Contract; `aria-live="polite"` on label container; right-aligned `ReplayPill` when `runId` present (D-49); `height:48`, `borderBottom:1px solid rgba(16,32,51,0.08)` |
| `frontend/src/features/race/components/RaceStatusStrip.test.tsx` | 23 tests covering 12-state parametrized labels, replay-pill visibility, aria-live, height/border assertions |
| `frontend/src/features/race/components/CharacteristicFailureBanner.tsx` | Full-bleed banner — `role="banner"`, `borderLeft:"4px solid"` + `borderColor:"primary.main"`, `borderRadius:0`, `p:3`, h2 `fontSize:"1.6rem"/fontWeight:700`, italic `clause` span; T-08-08: no innerHTML |
| `frontend/src/features/race/components/CharacteristicFailureBanner.test.tsx` | 10 tests covering role=banner, borderRadius=0, borderLeft 4px, italic clause, empty clause safety, XSS text-node safety |
| `frontend/src/features/race/components/MethodologySection.tsx` | Flat `<aside>` with `role="complementary"`, no Paper/Card, overline + h2 + body prose; 3x `<GlossaryTerm>` for `ttff`, `recovery_rate`, `hardness_profile` (UIRACE-07); `bgcolor:"background.default"` |
| `frontend/src/features/race/components/MethodologySection.test.tsx` | 11 tests covering aside role, no Paper/Card, overline/h2 text, 3x GlossaryTerm presence, FirstMentionProvider integration, bgcolor |

## Visual Contract Checklist

| Requirement | Component | Value | Status |
|-------------|-----------|-------|--------|
| Status strip height 48px (UI-SPEC line 51) | RaceStatusStrip | `height: 48` | PASS |
| Status strip borderBottom separator | RaceStatusStrip | `borderBottom: "1px solid rgba(16, 32, 51, 0.08)"` | PASS |
| All 12 PageState labels (Copywriting Contract) | RaceStatusStrip | `STATUS_LABEL` Record verbatim | PASS |
| aria-live="polite" on label container (UI-SPEC line 233) | RaceStatusStrip | `aria-live="polite"` on `data-testid="race-status-label"` | PASS |
| ReplayPill right-aligned in replay mode (D-49) | RaceStatusStrip | `{runId ? <ReplayPill runId={runId} /> : null}` | PASS |
| Banner borderLeft 4px primary (UIRACE-03) | CharacteristicFailureBanner | `borderLeft: "4px solid"` + `borderColor: "primary.main"` | PASS |
| Banner borderRadius 0 (UIRACE-03 banner=0) | CharacteristicFailureBanner | `borderRadius: 0` | PASS |
| Banner padding 24px lg (spacing scale) | CharacteristicFailureBanner | `p: 3` | PASS |
| Banner h2 Display 25.6px/700 (UI-SPEC Typography) | CharacteristicFailureBanner | `fontSize: "1.6rem", fontWeight: 700` | PASS |
| Banner italic dynamic clause (UIRACE-03) | CharacteristicFailureBanner | `fontStyle: "italic"` on span | PASS |
| Banner role=banner (UI-SPEC line 240) | CharacteristicFailureBanner | `role="banner"` | PASS |
| Methodology flat aside (UIRACE-03 no Paper/Card) | MethodologySection | `Box component="aside"` — zero MUI elevation components | PASS |
| Methodology role=complementary (UI-SPEC line 243) | MethodologySection | `role="complementary"` | PASS |
| Methodology bgcolor=background.default (60% dominant) | MethodologySection | `bgcolor: "background.default"` | PASS |
| GlossaryTerm wraps ttff (UIRACE-07) | MethodologySection | `<GlossaryTerm term="ttff">` | PASS |
| GlossaryTerm wraps recovery_rate (UIRACE-07) | MethodologySection | `<GlossaryTerm term="recovery_rate">` | PASS |
| GlossaryTerm wraps hardness_profile (UIRACE-07) | MethodologySection | `<GlossaryTerm term="hardness_profile">` | PASS |
| No XSS surface in banner (T-08-08) | CharacteristicFailureBanner | Zero `dangerouslySetInnerHTML` usage | PASS |

## Component Inputs

| Component | Props | Notes |
|-----------|-------|-------|
| `RaceStatusStrip` | `state: PageState; runId?: string \| null; timestampLabel?: string \| null` | `timestampLabel` suppressed for transient states (disconnected/reconnecting/live/pre-race/countdown) |
| `CharacteristicFailureBanner` | `header: string; clause: string` | Both rendered as React text — auto-escaped; empty `clause` renders empty italic span (does not crash) |
| `MethodologySection` | None (static content) | Safe outside `FirstMentionProvider` — GlossaryTerm falls back to Tooltip branch |

## TDD Gate Compliance

Both tasks followed RED/GREEN cycle:

| Gate | Task 1 (RaceStatusStrip) | Task 2 (Banner + Methodology) |
|------|--------------------------|-------------------------------|
| RED (test commit) | `ddece01` test(08-04b): add failing tests for RaceStatusStrip (TDD RED) | `70aa947` test(08-04b): add failing tests for CharacteristicFailureBanner and MethodologySection (TDD RED) |
| GREEN (feat commit) | `6c1ace8` feat(08-04b): RaceStatusStrip — 48px strip with 12-state labels and ReplayPill | `b88ce72` feat(08-04b): CharacteristicFailureBanner + MethodologySection |
| REFACTOR | Not needed — implementations were clean on first pass | Not needed |

## Test Results

| File | Tests | Status |
|------|-------|--------|
| `RaceStatusStrip.test.tsx` | 23 | PASS |
| `CharacteristicFailureBanner.test.tsx` | 10 | PASS |
| `MethodologySection.test.tsx` | 11 | PASS |
| TypeScript `npx tsc --noEmit` | — | PASS |
| `npm run build` | — | PASS (2.49s) |

**Total: 44 tests pass.**

## Plan 06 Handoff

Plan 06 (RacePage wiring) will:
1. Import `RaceStatusStrip` and render in the page chrome slot, passing `state`, `runId` (from `useRaceReplay`), and `timestampLabel` (from `race_done` event)
2. Import `CharacteristicFailureBanner` and render below the lane row when `state` is `done`/`replay`/`sparse-heatmap`/`indeterminate`/`lane-failed` — passing `header` + `clause` from the headline template
3. Import `MethodologySection` and render below the banner slot — it is static and needs no props
4. Wrap the race route in `<FirstMentionProvider>` (D-51) so `MethodologySection`'s GlossaryTerms trigger the first-mention popover on first visit

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| Task 1 RED | `ddece01` | test(08-04b): add failing tests for RaceStatusStrip (TDD RED) |
| Task 1 GREEN | `6c1ace8` | feat(08-04b): RaceStatusStrip — 48px strip with 12-state labels and ReplayPill |
| Task 2 RED | `70aa947` | test(08-04b): add failing tests for CharacteristicFailureBanner and MethodologySection (TDD RED) |
| Task 2 GREEN | `b88ce72` | feat(08-04b): CharacteristicFailureBanner + MethodologySection |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Banner JSDoc contained `dangerouslySetInnerHTML` keyword — triggered acceptance criteria grep**
- **Found during:** Task 2, GREEN phase — grep acceptance criterion `equals 0` failed because the JSDoc comment mentioned the keyword
- **Fix:** Replaced phrasing "Zero `dangerouslySetInnerHTML`" with "No XSS surface" in JSDoc
- **Files modified:** `CharacteristicFailureBanner.tsx`
- **Commit:** Incorporated into `b88ce72`

**2. [Rule 1 - Bug] MethodologySection JSDoc mentioned `Paper`/`Card` — triggered comment-stripped grep**
- **Found during:** Task 2, GREEN phase — `grep -v '^[[:space:]]*//'` does not strip block-comment lines starting with ` *`
- **Fix:** Replaced "No Paper, no Card" with "Flat Box component='aside' — no MUI elevation components" in JSDoc
- **Files modified:** `MethodologySection.tsx`
- **Commit:** Incorporated into `b88ce72`

**3. [Rule 2 - Missing] CharacteristicFailureBanner uses Box (not Paper) for root element**
- **Found during:** Task 2, implementation — plan template code showed `<Paper elevation={0} ...>` as the pattern analog
- **Issue:** `Paper` default `borderRadius` would compete with the `sx={{ borderRadius: 0 }}` override and could vary across MUI versions; using `Box` is unambiguous
- **Fix:** Root element is `<Box>` — the 4px border, bgcolor, padding, and radius are all explicit `sx` values
- **Files modified:** `CharacteristicFailureBanner.tsx`

### Out-of-scope items

None discovered.

## Known Stubs

None — all 3 components are fully implemented with real values matching UI-SPEC. MethodologySection has static prose content; Plan 06 wires the dynamic data into RaceStatusStrip and CharacteristicFailureBanner via props.

## Threat Flags

None — no new network endpoints, auth paths, or file access patterns introduced.

**T-08-08 (XSS via clause content):** CharacteristicFailureBanner renders `clause` and `header` as React text children exclusively. Zero `dangerouslySetInnerHTML` usage (grep-enforced, confirmed 0). Test `"clause rendered as React text — XSS payload"` verifies script tags appear as escaped literal text in `textContent`.

**T-08-11 (banner role conflict):** UI-SPEC explicitly accepts dual `role="banner"` (AppShell header + CharacteristicFailureBanner section). a11y-checker pass logged in UI-SPEC review. Tests use `getByTestId` not `getByRole("banner")` to avoid selector ambiguity in the test environment.

## Self-Check: PASSED
