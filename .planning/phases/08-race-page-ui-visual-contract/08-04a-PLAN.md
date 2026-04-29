---
phase: 08-race-page-ui-visual-contract
plan: 04a
type: execute
wave: 3
depends_on: [08-01, 08-02]
files_modified:
  - frontend/src/features/race/components/RaceLaneCard.tsx
  - frontend/src/features/race/components/RaceLaneTicker.tsx
  - frontend/src/features/race/components/FailureStateBadge.tsx
  - frontend/src/features/race/components/ReplayPill.tsx
  - frontend/src/features/race/components/RaceLaneCard.test.tsx
  - frontend/src/features/race/components/RaceLaneTicker.test.tsx
  - frontend/src/features/race/components/FailureStateBadge.test.tsx
  - frontend/src/features/race/components/ReplayPill.test.tsx
autonomous: true
requirements: [UIRACE-03, UIRACE-04, UIRACE-06]
tags: [frontend, mui, components, visual-contract, accessibility]

must_haves:
  truths:
    - "Lane card has 4px left-edge stripe in protocol color (UIRACE-03)"
    - "Lane card stripe widens to 6px under `@media (prefers-contrast: more)` (UI-SPEC line 122 high-contrast widen — encoded inside RaceLaneCard sx, NOT retrofitted in Plan 06)"
    - "Border radius scale: lane=18, badge=4, pills=999 (UIRACE-03)"
    - "FailureStateBadge consumes failureTagColor (Plan 01) — color + Icon + label, never color alone (UIRACE-04)"
    - "Ticker uses label-above-value pattern: 14px/400 label over 18.4px/700 value (UIRACE-03 + UI-SPEC Typography)"
    - "ReplayPill: secondary.main bg, white text, radius=999, uppercase + 0.08em letter-spacing (D-49 + UI-SPEC)"
    - "fault_observed announcements via aria-live='polite' on the lane event feed (UIRACE-06)"
    - "Lane name rendered inside <GlossaryTerm> for first-mention popover (UIRACE-07)"
  artifacts:
    - path: "frontend/src/features/race/components/RaceLaneCard.tsx"
      provides: "Per-lane card with 4px stripe (6px under prefers-contrast: more), header, ticker grid, event feed, terminal badge slot"
      exports: ["RaceLaneCard"]
    - path: "frontend/src/features/race/components/RaceLaneTicker.tsx"
      provides: "Label-above-value metric pair (TTFF / Recovery Rate / Turns / Score)"
      exports: ["RaceLaneTicker"]
    - path: "frontend/src/features/race/components/FailureStateBadge.tsx"
      provides: "Pill (radius=4) carrying tag color + Icon + label from failureTagColor"
      exports: ["FailureStateBadge"]
    - path: "frontend/src/features/race/components/ReplayPill.tsx"
      provides: "Status-strip pill displaying truncated run_id"
      exports: ["ReplayPill"]
  key_links:
    - from: "frontend/src/features/race/components/FailureStateBadge.tsx"
      to: "frontend/src/lib/trace/eventColors.ts"
      via: "import { failureTagColor }"
      pattern: "failureTagColor\\["
    - from: "frontend/src/features/race/components/RaceLaneCard.tsx"
      to: "frontend/src/lib/trace/eventColors.ts"
      via: "getProtocolColor for stripe"
      pattern: "getProtocolColor"
---

<objective>
Build the lane + badge family of visual building blocks: RaceLaneCard (with the prefers-contrast widen baked in), RaceLaneTicker, FailureStateBadge, ReplayPill. Each consumes Plan 01 types/tokens and renders per UI-SPEC verbatim values.

Purpose: Wave 3 — runs in parallel with Plan 04b (chrome family) and Plan 05 (heatmap + scrubber). Splitting Plan 04 into 04a + 04b keeps each plan within the ~50% context budget (4 components / 8 files in a single task was too dense). The prefers-contrast widen is owned here — no cross-wave backflow from Plan 06.

Output: 4 new component files + 4 test files.
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
<!-- Existing patterns + Plan 01 outputs. -->

From frontend/src/lib/trace/eventColors.ts (Plan 01 + existing):
```typescript
export function getProtocolColor(lane: string): string;
export const failureTagColor: Record<FailureTag, { bg: string; text: string; Icon: ComponentType; label: string }>;
```

From frontend/src/lib/types/race.ts (Plan 01):
```typescript
export type RaceLane = "pure_mcp" | "pure_a2a" | "hybrid";
export type FailureTag = "recovered" | "gave_up" | "kept_going_without_noticing" | "kept_going_to_failure" | "indeterminate";
export interface LaneState { lane; last_turn_index; ttff_ms; recovered_count; total_count; faults; events; terminal_tag; headline; }
```

From frontend/src/features/run-workspace/RunWorkspacePage.tsx lines 870-953 (lane card analog with stripe + ticker chips + faults).
From frontend/src/features/telemetry/TelemetryPage.tsx lines 157-169 (label-above-value TelemetryCard analog).
</interfaces>
</context>

<tasks>

<task type="auto" tdd="true">
  <name>Task 1: Build FailureStateBadge + ReplayPill — atomic chip primitives</name>
  <files>frontend/src/features/race/components/FailureStateBadge.tsx, frontend/src/features/race/components/ReplayPill.tsx, frontend/src/features/race/components/FailureStateBadge.test.tsx, frontend/src/features/race/components/ReplayPill.test.tsx</files>
  <read_first>
    - frontend/src/lib/trace/eventColors.ts (Plan 01 — failureTagColor)
    - frontend/src/lib/types/race.ts (Plan 01 — FailureTag)
    - .planning/phases/08-race-page-ui-visual-contract/08-UI-SPEC.md lines 99-118 (Failure Tag Color Map), 138-146 (Border Radius Scale), 56-70 (Typography)
    - .planning/phases/08-race-page-ui-visual-contract/08-CONTEXT.md (D-49 ReplayPill copy + styling)
    - .planning/phases/08-race-page-ui-visual-contract/08-PATTERNS.md lines 183-209 (FailureStateBadge), 522-541 (ReplayPill)
  </read_first>
  <behavior>
    FailureStateBadge:
    - Test: rendering with `tag="gave_up"` produces a Chip with `bgcolor: "#fce4ec"`, `color: "#880e4f"`, `borderRadius: "4px"` (UIRACE-03 badge=4).
    - Test: Chip carries the icon associated with the tag (CancelOutlinedIcon for gave_up).
    - Test: visible label text matches `failureTagColor[tag].label` (e.g., "Gave Up").
    - Test: minimum height 44px (touch target per UIRACE-06 / UI-SPEC line 49).
    - Test: NEVER renders color without icon AND label (UIRACE-04 — color is never sole channel).

    ReplayPill:
    - Test: rendering with `runId="abc12345extra"` shows `"REPLAY · abc12345"` (truncated to first 8 chars per D-49).
    - Test: bgcolor is `secondary.main`, color is white, borderRadius 999.
    - Test: text is uppercase with `letter-spacing: 0.08em` and 0.875rem / 700 (UI-SPEC Typography line 69).
    - Test: run_id rendered as text only — never inserted as `dangerouslySetInnerHTML` (T-08-04 mitigation).
  </behavior>
  <action>
Step 1 — `frontend/src/features/race/components/FailureStateBadge.tsx`:

```tsx
import Chip from "@mui/material/Chip";
import { failureTagColor } from "../../../lib/trace/eventColors";
import type { FailureTag } from "../../../lib/types/race";

export function FailureStateBadge({ tag }: { tag: FailureTag }) {
  const cfg = failureTagColor[tag];
  const Icon = cfg.Icon;
  return (
    <Chip
      icon={<Icon />}
      label={cfg.label}
      data-testid="failure-state-badge"
      data-tag={tag}
      sx={{
        bgcolor: cfg.bg,
        color: cfg.text,
        borderRadius: "4px",   // UIRACE-03 badge=4
        height: 44,            // UI-SPEC line 49 — WCAG 2.5.5 touch target
        fontWeight: 600,
        "& .MuiChip-icon": { color: cfg.text },
      }}
    />
  );
}
```

Step 2 — `frontend/src/features/race/components/ReplayPill.tsx`:

```tsx
import Chip from "@mui/material/Chip";

export function ReplayPill({ runId }: { runId: string }) {
  // Truncate to first 8 chars (D-49). React text-child rendering auto-escapes (T-08-04 mitigation).
  const truncated = runId.slice(0, 8);
  return (
    <Chip
      label={`REPLAY · ${truncated}`}
      data-testid="replay-pill"
      sx={{
        bgcolor: "secondary.main",
        color: "common.white",
        borderRadius: "999px",          // UIRACE-03 pill=999
        fontSize: "0.875rem",           // UI-SPEC Typography label size
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.08em",
        height: 32,
      }}
    />
  );
}
```

Step 3 — vitest tests for both. Use `renderWithProviders`. Assert exact bg colors, border styles, text content per behavior list.
  </action>
  <verify>
    <automated>cd frontend && npm test -- FailureStateBadge ReplayPill 2>&1 | tail -20</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c "failureTagColor" frontend/src/features/race/components/FailureStateBadge.tsx` >= 1
    - `grep -c "borderRadius.*\"4px\"\|borderRadius: 4" frontend/src/features/race/components/FailureStateBadge.tsx` >= 1 (UIRACE-03 badge=4)
    - `grep -c "height: 44" frontend/src/features/race/components/FailureStateBadge.tsx` >= 1 (touch target)
    - `grep -c "borderRadius.*\"999" frontend/src/features/race/components/ReplayPill.tsx` >= 1 (UIRACE-03 pill=999)
    - `grep -c "secondary.main" frontend/src/features/race/components/ReplayPill.tsx` >= 1 (D-49)
    - `grep -c "0.08em" frontend/src/features/race/components/ReplayPill.tsx` >= 1 (UI-SPEC line 69 letter-spacing)
    - `grep -rl "dangerouslySetInnerHTML" frontend/src/features/race/components/FailureStateBadge.tsx frontend/src/features/race/components/ReplayPill.tsx | wc -l` equals 0 (T-08-04)
    - `cd frontend && npm test -- FailureStateBadge ReplayPill` exits 0
  </acceptance_criteria>
  <done>FailureStateBadge consumes failureTagColor with icon+label always paired (UIRACE-04); ReplayPill renders truncated run_id with D-49 styling; no innerHTML usage.</done>
</task>

<task type="auto" tdd="true">
  <name>Task 2: Build RaceLaneCard (with prefers-contrast widen) + RaceLaneTicker</name>
  <files>frontend/src/features/race/components/RaceLaneCard.tsx, frontend/src/features/race/components/RaceLaneTicker.tsx, frontend/src/features/race/components/RaceLaneCard.test.tsx, frontend/src/features/race/components/RaceLaneTicker.test.tsx</files>
  <read_first>
    - frontend/src/features/run-workspace/RunWorkspacePage.tsx lines 870-953 (lane card analog)
    - frontend/src/features/telemetry/TelemetryPage.tsx lines 157-169 (TelemetryCard label-above-value)
    - frontend/src/lib/trace/eventColors.ts (Plan 01 — getProtocolColor)
    - frontend/src/lib/types/race.ts (Plan 01 — types)
    - frontend/src/features/race/components/FailureStateBadge.tsx (Task 1 output)
    - .planning/phases/08-race-page-ui-visual-contract/08-UI-SPEC.md lines 99-104 (Protocol Lane Colors), 120-130 (high-contrast widen), 56-70 (Typography)
    - .planning/phases/08-race-page-ui-visual-contract/08-PATTERNS.md lines 93-153 (RaceLaneCard pattern), 157-180 (Ticker pattern)
  </read_first>
  <behavior>
    RaceLaneCard:
    - Test: rendering with `lane="pure_mcp"` shows `borderLeft: "4px solid #1976d2"` (protocolColor.mcp).
    - Test: card border-radius is 18px (theme default — UIRACE-03 lane card scale).
    - Test: lane header chip background equals protocolColor for that lane.
    - Test: when `terminal_tag` is null, no FailureStateBadge renders (badge slot only fills on terminal state per UI-SPEC Page State Matrix).
    - Test: when `terminal_tag = "recovered"`, FailureStateBadge renders inside the card.
    - Test: event feed div has `aria-live="polite"` (UIRACE-06).
    - Test: lane name is wrapped in `<GlossaryTerm term={lane}>` (first-mention contract — UIRACE-07 + Pattern 4).
    - Test: data-testid="race-lane-card" with `data-lane={lane}` attribute.
    - Test (high-contrast widen — UI-SPEC line 122): mock `useMediaQuery("(prefers-contrast: more)")` to return true; render card; assert the rendered DOM Box for the card has computed `borderLeftWidth: 6px` via the inline `sx` style object — i.e. the sx prop's media query branch evaluates. In jsdom where computed-style for media queries is unreliable, use a snapshot of the rendered sx object: `expect(card.style.borderLeftWidth).toBe("6px")` after `useMediaQuery` is forced true. Implementation MUST use `useMediaQuery` (not raw CSS string) so test can mock it deterministically.

    RaceLaneTicker:
    - Test: renders 4 metric pairs in a 2-column grid: TTFF (ms), Recovery Rate (n/n), Turns (count), Score.
    - Test: label uses 14px/0.875rem with `letter-spacing: 0.12em` and color `secondary.main`.
    - Test: value uses 18.4px/1.15rem with `font-weight: 700` and color `primary.main`.
    - Test: `ttff_ms === null` → renders `"—"` (em dash), not `"null"` or `"NaN"`.
    - Test: each metric label is wrapped in `<GlossaryTerm>` for `ttff` and `recovery_rate` (UIRACE-07).
  </behavior>
  <action>
Step 1 — `frontend/src/features/race/components/RaceLaneTicker.tsx`:

```tsx
import { Box, Typography } from "@mui/material";
import { GlossaryTerm } from "../../../components/glossary/GlossaryTerm";
import type { LaneState } from "../../../lib/types/race";

interface MetricCellProps { label: React.ReactNode; value: React.ReactNode; }

function MetricCell({ label, value }: MetricCellProps) {
  return (
    <Box>
      <Typography variant="caption" sx={{
        display: "block",
        color: "secondary.main",
        letterSpacing: "0.12em",
        fontSize: "0.875rem",        // 14px label per UI-SPEC Typography
        fontWeight: 400,
        textTransform: "uppercase",
      }}>
        {label}
      </Typography>
      <Typography sx={{
        color: "primary.main",
        fontSize: "1.15rem",         // 18.4px value per UI-SPEC Typography
        fontWeight: 700,
      }}>
        {value}
      </Typography>
    </Box>
  );
}

export function RaceLaneTicker({ lane }: { lane: LaneState }) {
  const ttff = lane.ttff_ms === null ? "—" : `${lane.ttff_ms}ms`;
  const recovery = `${lane.recovered_count}/${lane.total_count}`;
  return (
    <Box
      data-testid="race-lane-ticker"
      sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}
    >
      <MetricCell label={<GlossaryTerm term="ttff">TTFF</GlossaryTerm>} value={ttff} />
      <MetricCell label={<GlossaryTerm term="recovery_rate">Recovery Rate</GlossaryTerm>} value={recovery} />
      <MetricCell label="Turns" value={lane.last_turn_index < 0 ? "—" : lane.last_turn_index + 1} />
      <MetricCell label="Score" value={lane.terminal_tag ? failureTagShort(lane.terminal_tag) : "—"} />
    </Box>
  );
}

function failureTagShort(tag: string): string {
  return tag.replace(/_/g, " ");
}
```

Step 2 — `frontend/src/features/race/components/RaceLaneCard.tsx` (uses `useMediaQuery` for prefers-contrast widen so a11y tests can mock it deterministically):

```tsx
import { Box, Card, CardContent, Chip, Stack, Typography } from "@mui/material";
import useMediaQuery from "@mui/material/useMediaQuery";
import { getProtocolColor } from "../../../lib/trace/eventColors";
import { GlossaryTerm } from "../../../components/glossary/GlossaryTerm";
import { FailureStateBadge } from "./FailureStateBadge";
import { RaceLaneTicker } from "./RaceLaneTicker";
import type { LaneState, RaceLane } from "../../../lib/types/race";

const LANE_LABEL: Record<RaceLane, string> = {
  pure_mcp: "Pure MCP",
  pure_a2a: "Pure A2A",
  hybrid: "Hybrid",
};

export function RaceLaneCard({ lane }: { lane: LaneState }) {
  const color = getProtocolColor(lane.lane);
  // UI-SPEC line 122: prefers-contrast: more widens the lane stripe from 4px → 6px.
  // Use useMediaQuery (not raw `@media` in sx) so a11y tests can deterministically mock it.
  const highContrast = useMediaQuery("(prefers-contrast: more)");
  const stripeWidth = highContrast ? 6 : 4;

  return (
    <Card
      variant="outlined"
      data-testid="race-lane-card"
      data-lane={lane.lane}
      sx={{
        height: "100%",
        flex: 1,
        borderLeft: `${stripeWidth}px solid ${color}`,   // UIRACE-03 4px stripe; widened under prefers-contrast (UI-SPEC line 122)
        // borderRadius defaults to theme 18px — UIRACE-03 lane card scale
      }}
    >
      <CardContent>
        <Stack spacing={1.5}>
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="h3">
              <GlossaryTerm term={lane.lane}>{LANE_LABEL[lane.lane]}</GlossaryTerm>
            </Typography>
            <Chip label={lane.lane} size="small" sx={{ bgcolor: color, color: "#fff" }} />
          </Stack>

          <RaceLaneTicker lane={lane} />

          {lane.terminal_tag ? <FailureStateBadge tag={lane.terminal_tag} /> : null}

          {/* Event feed — aria-live for fault_observed (UIRACE-06) */}
          <Box
            aria-live="polite"
            data-testid="race-lane-event-feed"
            sx={{ maxHeight: 240, overflow: "auto", borderTop: "1px solid", borderColor: "divider", pt: 1 }}
          >
            {lane.events.slice(-20).map((ev, i) => (
              <Typography key={`${ev.type}-${i}`} variant="caption" sx={{ display: "block", color: ev.type === "fault_observed" ? "error.main" : "text.secondary" }}>
                {/* Render as plain text — auto-escaped by React (T-08-08 mitigation: never innerHTML) */}
                {ev.type === "fault_observed" ? `Fault observed: ${"evidence" in ev ? ev.evidence : ""}` : `${ev.type} (turn ${ev.turn_index})`}
              </Typography>
            ))}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}
```

Step 3 — vitest tests. The high-contrast test mocks `useMediaQuery` via `vi.mock("@mui/material/useMediaQuery", () => ({ default: vi.fn(() => true) }))` to force the widen branch. Assert:

```typescript
import { vi } from "vitest";
vi.mock("@mui/material/useMediaQuery", () => ({ default: vi.fn(() => true) }));

test("prefers-contrast: more widens lane stripe to 6px", () => {
  const { getByTestId } = renderWithProviders(<RaceLaneCard lane={fixtureLane()} />);
  const card = getByTestId("race-lane-card");
  // MUI sx with template-literal computes inline; assert via getComputedStyle border-left-width.
  expect(getComputedStyle(card).borderLeftWidth).toBe("6px");
});
```

(If jsdom's getComputedStyle does not reflect inline-sx, fall back to snapshotting the rendered Card's sx object via the React tree, OR confirm via the data attribute and inspect the rendered border-left in the style attribute.)
  </action>
  <verify>
    <automated>cd frontend && npm test -- RaceLaneCard RaceLaneTicker 2>&1 | tail -20</automated>
  </verify>
  <acceptance_criteria>
    - `grep -c "borderLeft.*\\\${stripeWidth}\\|borderLeft.*4px\\|borderLeft.*6px" frontend/src/features/race/components/RaceLaneCard.tsx` >= 1 (UIRACE-03 lane stripe — 4px/6px branch)
    - `grep -c "useMediaQuery" frontend/src/features/race/components/RaceLaneCard.tsx` >= 1 (deterministic high-contrast mock)
    - `grep -c "prefers-contrast: more" frontend/src/features/race/components/RaceLaneCard.tsx` >= 1 (UI-SPEC line 122)
    - `grep -c "stripeWidth\|: 6 :" frontend/src/features/race/components/RaceLaneCard.tsx` >= 1 (widen branch present)
    - `grep -c "getProtocolColor" frontend/src/features/race/components/RaceLaneCard.tsx` >= 1
    - `grep -c "aria-live=\"polite\"" frontend/src/features/race/components/RaceLaneCard.tsx` >= 1 (UIRACE-06)
    - `grep -c "GlossaryTerm" frontend/src/features/race/components/RaceLaneCard.tsx` >= 1 (lane name first-mention)
    - `grep -c "GlossaryTerm" frontend/src/features/race/components/RaceLaneTicker.tsx` >= 2 (ttff + recovery_rate)
    - `grep -rl "dangerouslySetInnerHTML" frontend/src/features/race/components/RaceLaneCard.tsx frontend/src/features/race/components/RaceLaneTicker.tsx | wc -l` equals 0
    - `cd frontend && npm test -- RaceLaneCard RaceLaneTicker` exits 0
  </acceptance_criteria>
  <done>RaceLaneCard ships 4px stripe + aria-live event feed + lane GlossaryTerm; prefers-contrast widen to 6px lives in this plan via useMediaQuery (no Plan 06 backflow); RaceLaneTicker label-above-value with ttff + recovery_rate GlossaryTerm wraps.</done>
</task>

</tasks>

<threat_model>
## Trust Boundaries

| Boundary | Description |
|----------|-------------|
| `lane.events[].evidence` / event content → DOM render | Phase 7 ws emits these as strings; React text-child rendering auto-escapes. |
| `runId` → ReplayPill text | Validated upstream (Plan 03 useRaceReplay regex); rendered as text-child only. |

## STRIDE Threat Register

| Threat ID | Category | Component | Disposition | Mitigation Plan |
|-----------|----------|-----------|-------------|-----------------|
| T-08-08 | Injection (XSS via event content) | RaceLaneCard event feed | mitigate | Events rendered exclusively as React text children (auto-escaped). NO `dangerouslySetInnerHTML`. Acceptance criteria grep enforces zero usage. |
| T-08-04 | Injection (XSS via run_id text) | ReplayPill | mitigate | run_id substring(0,8) rendered as React text inside Chip label. No href, no innerHTML. |
</threat_model>

<verification>
- TypeScript compiles: `cd frontend && npx tsc --noEmit`
- All 4 component tests pass: `cd frontend && npm test -- RaceLaneCard RaceLaneTicker FailureStateBadge ReplayPill`
- Build succeeds: `cd frontend && npm run build`
- No XSS surfaces: `grep -r "dangerouslySetInnerHTML" frontend/src/features/race/components/` returns nothing for the 4 files in this plan.
</verification>

<success_criteria>
- 4 lane/badge components ship with UI-SPEC verbatim values for radii, colors, spacing, typography.
- failureTagColor (Plan 01) is the single source of truth — FailureStateBadge consumes it with color + icon + label always paired (UIRACE-04).
- aria-live="polite" on lane event feed (UIRACE-06).
- Lane stripe widens to 6px under `prefers-contrast: more` via useMediaQuery (UI-SPEC line 122) — owned in this plan, no Plan 06 backflow.
- No XSS surfaces.
</success_criteria>

<output>
After completion, create `.planning/phases/08-race-page-ui-visual-contract/08-04a-SUMMARY.md` with:
- 4 component files created
- Visual contract checklist (radii, colors, ARIA roles)
- prefers-contrast widen behavior (4px → 6px via useMediaQuery)
- Inputs each component expects (LaneState, FailureTag, runId)
- Plan 06 will compose these into RacePage lane row
</output>
