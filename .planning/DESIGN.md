# Design System Reference — Race Demo Surfaces

This document formalizes the design tokens and rules established during Phases 8–12 of the A2A vs MCP Demo Platform. It covers exactly 5 items: the failure-tag color map, the methodology-as-flat layout rule, the `secondary.main` replay-pill semantic, the role-first first-mention contract, and the primary/secondary palette intent. It is a reference document — a single source of truth for contributors building on or extending the race-demo surfaces. It contains no change-management procedures and no self-assessment section.

---

## 1. Failure Tag Color Map

**Intent:** Each failure tag has a unique `bg`/`text` pair that communicates recovery outcome at a glance. Color is always paired with an Icon and a Label so it is never the sole information channel — this satisfies the UIRACE-04 accessibility requirement.

**Source:** `frontend/src/lib/trace/eventColors.ts` — single source of truth for all 5 entries. Consumed by `FailureStateBadge` and `HardnessFailureHeatmap` cells.

**Token table:**

| Tag | bg | text | Icon | Label | Intent |
|-----|----|------|------|-------|--------|
| `recovered` | `#e8f5e9` | `#1b5e20` | `CheckCircleOutlineIcon` | Recovered | Agent detected fault and recovered within K=3 turns |
| `gave_up` | `#fce4ec` | `#880e4f` | `CancelOutlinedIcon` | Gave Up | Agent stopped after fault; task incomplete |
| `kept_going_without_noticing` | `#fff3e0` | `#e65100` | `VisibilityOffOutlinedIcon` | Kept Going (Unaware) | Agent continued without acknowledging the fault |
| `kept_going_to_failure` | `#fbe9e7` | `#bf360c` | `ErrorOutlineIcon` | Kept Going to Failure | Agent continued past fault and task ultimately failed |
| `indeterminate` | `#f5f5f5` | `#424242` | `HelpOutlineIcon` | Indeterminate | Insufficient evidence to classify recovery outcome |

**Code snippet:**

```typescript
// frontend/src/lib/trace/eventColors.ts
export const failureTagColor: Record<FailureTag, FailureTagStyle> = {
  recovered:                   { bg: "#e8f5e9", text: "#1b5e20", Icon: CheckCircleOutlineIcon,   label: "Recovered" },
  gave_up:                     { bg: "#fce4ec", text: "#880e4f", Icon: CancelOutlinedIcon,        label: "Gave Up" },
  kept_going_without_noticing: { bg: "#fff3e0", text: "#e65100", Icon: VisibilityOffOutlinedIcon, label: "Kept Going (Unaware)" },
  kept_going_to_failure:       { bg: "#fbe9e7", text: "#bf360c", Icon: ErrorOutlineIcon,          label: "Kept Going to Failure" },
  indeterminate:               { bg: "#f5f5f5", text: "#424242", Icon: HelpOutlineIcon,           label: "Indeterminate" },
};
```

**Rules — do NOT:**
- do NOT add a 6th failure tag without pairing it with a unique Icon — color alone violates UIRACE-04. Every new entry must supply `Icon` and `label` alongside `bg`/`text`.
- do NOT reference `failureTagColor` from outside `FailureStateBadge` and `HardnessFailureHeatmap` without first confirming the new consumer also renders an Icon and Label alongside the color.

---

## 2. Methodology-as-Flat Rule

**Intent:** Methodology and contextual-prose sections live as flat `Box` aside elements at `background.default` — they are not content cards. Using MUI `Card` or `Paper` elevation on these sections implies user-actionable content, which is wrong for read-only context prose. The visual weight must stay below the interactive data panels on the same page.

**Source:** `frontend/src/features/race/components/MethodologySection.tsx`

**Code snippet:**

```tsx
// frontend/src/features/race/components/MethodologySection.tsx
<Box
  component="aside"
  role="complementary"
  data-testid="race-methodology-section"
  sx={{ bgcolor: "background.default", py: 6 }}
>
  {/* prose content — no Paper, no Card, no elevation */}
</Box>
```

**Rules — do NOT:**
- do NOT wrap the methodology section in a MUI `Card` or `Paper` — it must remain a flat `Box` aside with `bgcolor: "background.default"`.
- do NOT apply `elevation` or `variant="outlined"` to contextual prose sections. If content needs a border or raised surface, it is a data card, not a methodology section; treat it as such and place it in a `Paper` variant.

---

## 3. secondary.main as Replay-Pill Semantic

**Intent:** `secondary.main` (`#b85c38`) is a warm terracotta accent reserved for non-primary emphasis signals: replay-state indicators (the `ReplayPill` chip) and role-first overline labels (section-heading preambles). Its dual use is intentional — both are "warm annotation" contexts where the goal is to draw the eye without anchoring structure. A third use would dilute the semantic and make the warm accent meaningless.

**Sources:** `frontend/src/features/race/components/ReplayPill.tsx` (replay-pill implementation), `frontend/src/features/run-workspace/RunWorkspacePage.tsx` line 363 (role-first overline).

**Code snippets:**

```tsx
// frontend/src/features/race/components/ReplayPill.tsx
<Chip
  label={`REPLAY · ${truncated}`}
  sx={{
    bgcolor: "secondary.main",   // #b85c38 warm accent (D-49)
    color: "common.white",
    borderRadius: "999px",
    fontSize: "0.875rem",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.08em",
    height: 32,
  }}
/>

// frontend/src/features/run-workspace/RunWorkspacePage.tsx (line 363)
<Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
  Interactive Workspace
</Typography>
```

**Rules — do NOT:**
- do NOT use `secondary.main` (`#b85c38`) for any purpose other than replay-pill background and role-first overline labels. For other accent needs, use `primary.main` or a `toneColor` entry from `eventColors.ts`.
- do NOT use `secondary.main` as a border color, icon fill, or hover state — these contexts belong to `primary.main` or `toneColor` severity values.

---

## 4. Role-First First-Mention Contract

**Intent:** On the Run, Compare, and Race pages, every section that introduces a protocol role (MCP, A2A, Hybrid, Baseline, or a named workspace concept) must label it with an overline in `secondary.main` before the section heading. This makes protocol identity legible at a glance without relying on color, position, or memory of page structure.

**Scope:** Run + Compare + Race pages only. Trends and Learn pages may apply the same pattern incidentally, but those incidental uses are not governed by this rule and do not extend its scope.

**Visual rule** (document the rule; do not document the `roleFirstLabel()` implementation detail):
- Typography variant: `"overline"`
- Color: `"secondary.main"` (`#b85c38`)
- Letter spacing: `letterSpacing: "0.16em"`

**Source:** `frontend/src/features/run-workspace/RunWorkspacePage.tsx` line 363

**Code snippet:**

```tsx
// frontend/src/features/run-workspace/RunWorkspacePage.tsx (line 363)
<Typography
  variant="overline"
  sx={{ color: "secondary.main", letterSpacing: "0.16em" }}
>
  Interactive Workspace
</Typography>
```

**Rules — do NOT:**
- do NOT use `variant="subtitle2"` or `variant="caption"` as a substitute for the role-first overline — only `variant="overline"` + `color="secondary.main"` + `letterSpacing: "0.16em"` satisfies the contract.
- do NOT apply the role-first pattern outside the Run, Compare, and Race pages without a new explicit design decision. Incidental matching on other pages does not extend the contract.

---

## 5. Primary/Secondary Palette Intent

**Intent:** `primary.main` (`#17475f`) is a deep teal used for structural emphasis — headings, active states, and the 4px left-border accent rule. `secondary.main` (`#b85c38`) is a warm terracotta used for non-primary annotation signals (replay state, role-first labels). They are not interchangeable: primary anchors structure, secondary annotates. The warm/cool split is deliberate and should be preserved across any new surfaces.

**Source:** `frontend/src/app/theme.ts`

**Code snippet:**

```typescript
// frontend/src/app/theme.ts
export const appTheme = createTheme({
  palette: {
    mode: "light",
    primary:    { main: "#17475f" },  // deep teal — structural emphasis
    secondary:  { main: "#b85c38" },  // warm terracotta — annotation signals
    background: { default: "#f3efe7", paper: "#fffdfa" },
  },
  shape: { borderRadius: 18 },
});
```

**Rules — do NOT:**
- do NOT swap `primary` and `secondary` for aesthetic variety — the teal/terracotta pairing is a deliberate warm/cool split and the split carries meaning throughout the race-demo surfaces.
- do NOT introduce a third "accent" color outside this palette for race-demo surfaces. Use `toneColor` entries (`error`/`warning`/`success`/`info` in `eventColors.ts`) for severity signals; use `failureTagColor` entries for recovery-outcome signals.
