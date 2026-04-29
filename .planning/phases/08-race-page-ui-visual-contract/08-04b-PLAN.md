---
phase: 08-race-page-ui-visual-contract
plan: 04b
type: execute
wave: 3
depends_on: [08-01, 08-02, 08-04a]
files_modified:
  - frontend/src/features/race/components/RaceStatusStrip.tsx
  - frontend/src/features/race/components/CharacteristicFailureBanner.tsx
  - frontend/src/features/race/components/MethodologySection.tsx
  - frontend/src/features/race/components/RaceStatusStrip.test.tsx
  - frontend/src/features/race/components/CharacteristicFailureBanner.test.tsx
  - frontend/src/features/race/components/MethodologySection.test.tsx
autonomous: true
requirements: [UIRACE-01, UIRACE-03, UIRACE-06, UIRACE-07]
tags: [frontend, mui, components, visual-contract, accessibility]

must_haves:
  truths:
    - "Status strip: 48px fixed height with right-aligned ReplayPill in replay mode (D-49)"
    - "Status strip exposes labels for all 12 PageState values per UI-SPEC Copywriting Contract (UIRACE-02 surface)"
    - "Banner h1 left-aligned, 4px primary rule, italic dynamic clause; radius=0 (UIRACE-03)"
    - "Banner ARIA landmark role='banner' (UI-SPEC Interaction Contract)"
    - "Methodology renders flat — no Paper/Card — with role='complementary' (UIRACE-03)"
    - "Methodology body wraps ttff, recovery_rate, hardness_profile in <GlossaryTerm> (UIRACE-07)"
  artifacts:
    - path: "frontend/src/features/race/components/RaceStatusStrip.tsx"
      provides: "48px sticky strip: left state label + right replay pill"
      exports: ["RaceStatusStrip"]
    - path: "frontend/src/features/race/components/CharacteristicFailureBanner.tsx"
      provides: "Full-bleed banner: 4px primary left rule + h2 + italic clause + role=banner"
      exports: ["CharacteristicFailureBanner"]
    - path: "frontend/src/features/race/components/MethodologySection.tsx"
      provides: "Flat aside (no Paper/Card) with overline + h2 + body prose wrapping GlossaryTerm"
      exports: ["MethodologySection"]
  key_links:
    - from: "frontend/src/features/race/components/RaceStatusStrip.tsx"
      to: "frontend/src/features/race/components/ReplayPill.tsx"
      via: "ReplayPill rendered inline when runId present"
      pattern: "ReplayPill"
    - from: "frontend/src/features/race/components/MethodologySection.tsx"
      to: "frontend/src/components/glossary/GlossaryTerm.tsx"
      via: "<GlossaryTerm term='ttff'> wrapping prose"
      pattern: "GlossaryTerm"
---

<objective>
Build the page chrome family: RaceStatusStrip (48px strip with all 12 page-state labels and right-aligned ReplayPill), CharacteristicFailureBanner (4px primary rule + italic clause + role=banner), MethodologySection (flat aside with GlossaryTerm prose).

Purpose: Wave 3 — runs in parallel with Plan 04a (lane/badge family) and Plan 05 (heatmap + scrubber). Splits Plan 04 keep each plan in the ~50% context budget. Depends on Plan 04a only because RaceStatusStrip imports ReplayPill — same wave but earlier-finishing artifact.

Output: 3 new component files + 3 test files.
</objective>

<execution_context>
@$HOME/.claude/get-shit-done/workflows/execute-plan.md
@$HOME/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/REQUIREMENTS.md
@.planning/phases/08-race-page-ui-visual-contract/08-CONTEXT.md
@.planning/phases/08-race-page-ui-visual-contract/08-PATTERNS.md
@.planning/phases/08-race-page-ui-visual-contract/08-UI-SPEC.md

<interfaces>
<!-- Existing patterns + Plan 01 + Plan 04a outputs. -->

From Plan 01 (frontend/src/lib/types/race.ts):
```typescript
export type PageState = "pre-race" | "countdown" | "live-n1" | "live-n5" | "done" | "replay" | "sparse-heatmap" | "ws-disconnected" | "ws-reconnecting" | "indeterminate" | "lane-failed" | "heatmap-empty";
```

From Plan 04a (frontend/src/features/race/components/ReplayPill.tsx):
```typescript
export function ReplayPill({ runId }: { runId: string }): JSX.Element;
```

From frontend/src/components/layout/AppShell.tsx lines 47-78 (Toolbar strip pattern).
From frontend/src/features/run-workspace/RunWorkspacePage.tsx lines 916-938 (talking-point Paper analog for banner).
From frontend/src/features/learn/LearningPage.tsx (flat section pattern for methodology).
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Build RaceStatusStrip — 48px strip with 12-state labels and right-aligned ReplayPill</name>
  <files>frontend/src/features/race/components/RaceStatusStrip.tsx, frontend/src/features/race/components/RaceStatusStrip.test.tsx</files>
  <read_first>
    - frontend/src/components/layout/AppShell.tsx lines 47-78 (Toolbar strip pattern)
    - frontend/src/features/race/components/ReplayPill.tsx (Plan 04a output)
    - .planning/phases/08-race-page-ui-visual-contract/08-UI-SPEC.md lines 184-208 (Information Hierarchy), 220-238 (ARIA Landmarks + aria-live), 261-281 (Copywriting Contract)
    - .planning/phases/08-race-page-ui-visual-contract/08-PATTERNS.md lines 483-519 (Status strip pattern)
  </read_first>
  <behavior>
    - Test: rendering with `state="pre-race"` shows "Ready" left-aligned, no replay pill.
    - Test: `state="live-n5"` shows "Live · 5 runs".
    - Test: `state="ws-disconnected"` shows "Disconnected".
    - Test: `state="ws-reconnecting"` shows "Reconnecting…" with `aria-live="polite"` on the label container (UI-SPEC line 233).
    - Test: when `runId` prop is non-null, ReplayPill renders right-aligned in the strip (D-49).
    - Test: strip height is 48px fixed (UI-SPEC line 51).
    - Test: borderBottom is `1px solid rgba(16, 32, 51, 0.08)` (UI-SPEC + AppShell analog).
    - Test: covers all 12 PageState values via parametrized test (each state → expected status label per UI-SPEC Copywriting Contract lines 263-278).
  </behavior>
  <action>
Create `frontend/src/features/race/components/RaceStatusStrip.tsx` per UI-SPEC Copywriting Contract verbatim:

```tsx
import { Box, Stack, Typography } from "@mui/material";
import { ReplayPill } from "./ReplayPill";
import type { PageState } from "../../../lib/types/race";

const STATUS_LABEL: Record<PageState, string> = {
  "pre-race": "Ready",
  "countdown": "Starting in…",                 // {N} interpolated by parent (Plan 06 wires)
  "live-n1": "Live · 1 run",
  "live-n5": "Live · 5 runs",
  "done": "Completed",                          // {timestamp} interpolated by parent
  "replay": "Completed",                        // replay pill carries replay context
  "sparse-heatmap": "Completed",
  "ws-disconnected": "Disconnected",
  "ws-reconnecting": "Reconnecting…",
  "indeterminate": "Completed",
  "lane-failed": "Completed",
  "heatmap-empty": "Completed",
};

export function RaceStatusStrip({ state, runId, timestampLabel }: { state: PageState; runId?: string | null; timestampLabel?: string | null }) {
  const baseLabel = STATUS_LABEL[state];
  const label = timestampLabel && state !== "ws-disconnected" && state !== "ws-reconnecting" && state !== "pre-race" && state !== "live-n1" && state !== "live-n5" && state !== "countdown"
    ? `${baseLabel} · ${timestampLabel}`
    : baseLabel;
  return (
    <Box
      data-testid="race-status-strip"
      sx={{
        height: 48,
        bgcolor: "background.paper",
        borderBottom: "1px solid rgba(16, 32, 51, 0.08)",
        px: 2,
      }}
    >
      <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ height: "100%" }}>
        <Box aria-live="polite" data-testid="race-status-label">
          <Typography variant="body2">{label}</Typography>
        </Box>
        {runId ? <ReplayPill runId={runId} /> : null}
      </Stack>
    </Box>
  );
}
```

vitest tests cover all 12 page states + replay-pill visibility.
  </action>
  <verify>
    <automated>cd frontend && npm test -- RaceStatusStrip 2>&1 | tail -20</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c "height: 48" frontend/src/features/race/components/RaceStatusStrip.tsx` >= 1 (UI-SPEC line 51)
    - `grep -c "borderBottom.*1px solid" frontend/src/features/race/components/RaceStatusStrip.tsx` >= 1
    - `grep -c "ReplayPill" frontend/src/features/race/components/RaceStatusStrip.tsx` >= 2 (import + usage)
    - `grep -c "aria-live=\"polite\"" frontend/src/features/race/components/RaceStatusStrip.tsx` >= 1 (UI-SPEC line 233)
    - `grep -E "Ready|Live|Disconnected|Reconnecting|Completed" frontend/src/features/race/components/RaceStatusStrip.tsx | wc -l` >= 5 (Copywriting Contract verbatim labels)
    - `cd frontend && npm test -- RaceStatusStrip` exits 0
  </acceptance_criteria>
  <done>RaceStatusStrip covers all 12 page-state labels per UI-SPEC Copywriting Contract verbatim; 48px height; ReplayPill rendered right-aligned when runId present.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Build CharacteristicFailureBanner + MethodologySection</name>
  <files>frontend/src/features/race/components/CharacteristicFailureBanner.tsx, frontend/src/features/race/components/MethodologySection.tsx, frontend/src/features/race/components/CharacteristicFailureBanner.test.tsx, frontend/src/features/race/components/MethodologySection.test.tsx</files>
  <read_first>
    - frontend/src/features/run-workspace/RunWorkspacePage.tsx lines 916-938 (talking-point Paper analog for banner)
    - frontend/src/features/learn/LearningPage.tsx (flat section pattern for methodology)
    - .planning/phases/08-race-page-ui-visual-contract/08-UI-SPEC.md lines 184-208 (Information Hierarchy), 220-244 (ARIA Landmarks)
    - .planning/phases/08-race-page-ui-visual-contract/08-PATTERNS.md lines 213-247 (Banner pattern), 252-271 (Methodology pattern)
  </read_first>
  <behavior>
    CharacteristicFailureBanner:
    - Test: renders with `role="banner"` (UI-SPEC ARIA Landmarks line 240).
    - Test: borderLeft is `4px solid` with `borderColor: primary.main` (UIRACE-03).
    - Test: borderRadius is 0 (UIRACE-03 banner=0).
    - Test: h2 element rendered with display size 25.6px / 1.6rem / 700 weight (UI-SPEC Typography Display).
    - Test: dynamic clause inside h2 has `font-style: italic` (UIRACE-03).
    - Test: padding is 24px (lg per spacing scale).
    - Test: when `clause` prop empty/undefined, banner renders with empty italic span (does not crash).
    - Test: clause text rendered as React text — never innerHTML (T-08-08 mitigation).

    MethodologySection:
    - Test: outermost element is `<aside>` with `role="complementary"` (UI-SPEC ARIA Landmarks line 243).
    - Test: NO `<Paper>` and NO `<Card>` in the rendered tree (UIRACE-03 — flat section).
    - Test: renders an overline label "Methodology" + h2 heading + body prose.
    - Test: prose wraps at least `ttff`, `recovery_rate`, and `hardness_profile` in `<GlossaryTerm>` (UIRACE-07 first-mention contract).
    - Test: bgcolor is `background.default` (dominant 60% per UI-SPEC Color section).
  </behavior>
  <action>
Step 1 — `frontend/src/features/race/components/CharacteristicFailureBanner.tsx`:

```tsx
import { Box, Typography } from "@mui/material";

export function CharacteristicFailureBanner({ header, clause }: { header: string; clause: string }) {
  return (
    <Box
      role="banner"                              // UI-SPEC line 240
      data-testid="characteristic-failure-banner"
      sx={{
        borderLeft: "4px solid",                  // UIRACE-03 banner 4px primary rule
        borderColor: "primary.main",
        bgcolor: "background.paper",
        p: 3,                                     // 24px (lg)
        borderRadius: 0,                          // UIRACE-03 banner=0
      }}
    >
      <Typography
        variant="h2"
        component="h1"
        sx={{ fontSize: "1.6rem", fontWeight: 700, lineHeight: 1.2 }}    // Display 25.6px/700 per UI-SPEC
      >
        {header}{" "}
        <Typography
          component="span"
          sx={{ fontStyle: "italic", fontSize: "1.6rem", fontWeight: 700 }} // UIRACE-03 italic dynamic clause
        >
          {clause}
        </Typography>
      </Typography>
    </Box>
  );
}
```

Step 2 — `frontend/src/features/race/components/MethodologySection.tsx`:

```tsx
import { Box, Container, Typography } from "@mui/material";
import { GlossaryTerm } from "../../../components/glossary/GlossaryTerm";

export function MethodologySection() {
  return (
    <Box
      component="aside"
      role="complementary"                          // UI-SPEC line 243
      data-testid="race-methodology-section"
      sx={{ bgcolor: "background.default", py: 6 }}  // 60% dominant + 2xl spacing
    >
      <Container maxWidth="lg" disableGutters>
        <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
          Methodology
        </Typography>
        <Typography variant="h2" sx={{ color: "primary.main", mb: 2 }}>
          How we measure failure recovery
        </Typography>
        <Typography variant="body1" sx={{ maxWidth: 760, color: "text.secondary" }}>
          We measure each lane by{" "}
          <GlossaryTerm term="ttff">TTFF</GlossaryTerm>,{" "}
          <GlossaryTerm term="recovery_rate">recovery rate</GlossaryTerm>, and the{" "}
          <GlossaryTerm term="hardness_profile">hardness profile</GlossaryTerm>{" "}
          of each task. Faults are injected deterministically; the recovery state machine classifies each run as recovered, gave_up, kept_going_without_noticing, kept_going_to_failure, or indeterminate within a K=3 turn window.
        </Typography>
      </Container>
    </Box>
  );
}
```

Step 3 — vitest tests covering all behavior bullets above. Use `renderWithProviders` + FirstMentionProvider for tests that exercise GlossaryTerm. Banner test asserts `getByTestId("characteristic-failure-banner")` returns the banner with role=banner attribute (avoid getByRole because AppShell may also have a role=banner header).
  </action>
  <verify>
    <automated>cd frontend && npm test -- CharacteristicFailureBanner MethodologySection 2>&1 | tail -20</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c 'role="banner"' frontend/src/features/race/components/CharacteristicFailureBanner.tsx` equals 1 (UI-SPEC line 240)
    - `grep -c "borderRadius: 0" frontend/src/features/race/components/CharacteristicFailureBanner.tsx` >= 1 (UIRACE-03 banner=0)
    - `grep -c "borderLeft.*4px" frontend/src/features/race/components/CharacteristicFailureBanner.tsx` >= 1 (UIRACE-03 4px primary rule)
    - `grep -c "primary.main" frontend/src/features/race/components/CharacteristicFailureBanner.tsx` >= 1
    - `grep -c "fontStyle.*italic\|fontStyle: \"italic\"" frontend/src/features/race/components/CharacteristicFailureBanner.tsx` >= 1 (UIRACE-03 italic clause)
    - `grep -c "1.6rem" frontend/src/features/race/components/CharacteristicFailureBanner.tsx` >= 1 (UI-SPEC Display 25.6px)
    - `grep -c 'role="complementary"' frontend/src/features/race/components/MethodologySection.tsx` equals 1 (UI-SPEC line 243)
    - `grep -c "component=\"aside\"" frontend/src/features/race/components/MethodologySection.tsx` equals 1
    - `grep -v '^[[:space:]]*//' frontend/src/features/race/components/MethodologySection.tsx | grep -cE "Paper|Card[^C]"` equals 0 (UIRACE-03 — flat section, NO Paper/Card; comment-stripped count guards against the self-invalidating grep gate)
    - `grep -c "GlossaryTerm" frontend/src/features/race/components/MethodologySection.tsx` >= 3 (ttff + recovery_rate + hardness_profile per UIRACE-07)
    - `grep -c "dangerouslySetInnerHTML" frontend/src/features/race/components/CharacteristicFailureBanner.tsx` equals 0 (T-08-08)
    - `cd frontend && npm test -- CharacteristicFailureBanner MethodologySection` exits 0
  </acceptance_criteria>
  <done>CharacteristicFailureBanner has role=banner + 4px primary rule + radius=0 + italic clause; MethodologySection is flat aside with no Paper/Card and 3+ GlossaryTerm wraps.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| `clause` prop → Banner italic span | Author-controlled (Plan 06 wires from headline templates); rendered as React text. |
| `runId` → RaceStatusStrip → ReplayPill text | Validated upstream (Plan 03 useRaceReplay regex); rendered as text-child only. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-08-08 | Injection (XSS via clause / event content) | CharacteristicFailureBanner | mitigate | Clause + header rendered exclusively as React text children (auto-escaped). NO `dangerouslySetInnerHTML`. Acceptance criteria grep enforces zero usage. |
| T-08-11 | Spoofing (banner role conflict with AppShell header) | CharacteristicFailureBanner | accept | UI-SPEC explicitly accepts dual role="banner" (page-level + section-level). a11y-checker pass logged in UI-SPEC review. |
</threat_model>

<verification>
- TypeScript compiles: `cd frontend && npx tsc --noEmit`
- All 3 component tests pass: `cd frontend && npm test -- RaceStatusStrip CharacteristicFailureBanner MethodologySection`
- Build succeeds: `cd frontend && npm run build`
- No XSS surfaces: `grep -r "dangerouslySetInnerHTML"` returns nothing for the 3 files in this plan.
</verification>

<success_criteria>
- 3 chrome components (RaceStatusStrip, Banner, Methodology) ship with UI-SPEC verbatim values for radii, colors, spacing, typography.
- ARIA contract surfaces: aria-live="polite" on status label + reconnect status; role="banner" on banner; role="complementary" on methodology (UIRACE-06).
- Methodology contains zero Paper/Card components (UIRACE-03 flat section enforced via comment-stripped grep).
- Methodology wraps ttff + recovery_rate + hardness_profile in GlossaryTerm (UIRACE-07).
</success_criteria>

<output>
After completion, create `.planning/phases/08-race-page-ui-visual-contract/08-04b-SUMMARY.md` with:
- 3 component files created
- Visual contract checklist mapped to each component (radii, colors, ARIA roles)
- Inputs each component expects (PageState, runId, header+clause)
- Plan 06 will compose these into RacePage chrome slots
</output>
