# Phase 8: Race Page UI & Visual Contract — Pattern Map

**Mapped:** 2026-04-29
**Files analyzed:** 17 (13 new + 4 modified)
**Analogs found:** 13 / 17 (4 files have NO close analog — flagged for blank-slate per UI-SPEC + RESEARCH-equivalent)

---

## File Classification

### New files (13)

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `frontend/src/features/race/RacePage.tsx` | page component | request-response (fetch) + streaming (ws) | `frontend/src/features/run-workspace/RunWorkspacePage.tsx` | role-match (page) + replay-fetch piece role-matches `ReportDetailPage` |
| `frontend/src/features/race/components/RaceStatusStrip.tsx` | component | derived-state | `frontend/src/components/layout/AppShell.tsx` (strip layout pattern) | role-match (sticky strip + Chip) |
| `frontend/src/features/race/components/RaceLaneCard.tsx` | component | derived-state | `RunWorkspacePage.tsx` lane card block (lines 870-953) | exact (lane card with stripe + chips) |
| `frontend/src/features/race/components/RaceLaneTicker.tsx` | component | derived-state | `TelemetryCard` (TelemetryPage.tsx lines 157-169) | role-match (label-above-value Card) |
| `frontend/src/features/race/components/FailureStateBadge.tsx` | component | derived-state | `RunWorkspacePage.tsx` failure chips (lines 939-950) | role-match (Chip with color/icon/label) |
| `frontend/src/features/race/components/CharacteristicFailureBanner.tsx` | component | derived-state | `RunWorkspacePage.tsx` Paper talking-point block (lines 916-938) | role-match (left-border accent + headline + italic) |
| `frontend/src/features/race/components/MethodologySection.tsx` | component | static | `LearningPage` body sections (flat Box+Typography) | role-match (flat section, no Paper/Card) |
| `frontend/src/features/race/components/HeatmapScaffold.tsx` | component | grid render | NONE (no CSS-Grid heatmap precedent in codebase) | NO ANALOG |
| `frontend/src/features/race/components/ReplayPill.tsx` | component | static | Chip usage in `RunWorkspacePage.tsx` lines 884-890 | role-match (Chip variant) |
| `frontend/src/features/race/components/ReplayScrubber.tsx` | component | event-driven (drag) | NONE (no MUI Slider usage anywhere in frontend) | NO ANALOG |
| `frontend/src/features/race/context/FirstMentionProvider.tsx` | provider | event-driven (set ops) | `frontend/src/app/ui/AppUiProvider.tsx` | exact (Context + Provider pattern) |
| `frontend/src/features/race/hooks/useRaceStream.ts` | hook | streaming (WebSocket) | NONE (no useReducer or WebSocket precedent) | NO ANALOG |
| `frontend/src/features/race/hooks/useRaceReplay.ts` | hook | request-response (fetch) | `ReportDetailPage.tsx` `useEffect` fetch (lines 25-55) | role-match (fetch-by-route-param into state) |

### Modified files (4)

| Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---------------|------|-----------|----------------|---------------|
| `frontend/src/components/glossary/GlossaryTerm.tsx` | component | branch on context | self (existing Tooltip body) + Popover via MUI docs | extension only |
| `frontend/src/lib/trace/eventColors.ts` | utility | static lookup | self (existing `protocolColor` Record pattern) | exact (extend the same module-level Record convention) |
| `frontend/src/lib/glossary/glossaryTerms.ts` | utility | static lookup | self (existing Record<string,string>) | exact (append 8 entries) |
| `frontend/src/app/routes.tsx` | config | route registration | self (existing lazy import + withSuspense) | exact (extend with `/race` and `/race/:run_id`) |

---

## Pattern Assignments

### `frontend/src/features/race/RacePage.tsx` (page, request-response + streaming)

**Analog:** `frontend/src/features/run-workspace/RunWorkspacePage.tsx` (page-shell pattern)
**Secondary analog:** `frontend/src/features/reports/ReportDetailPage.tsx` (route-param fetch pattern)

**Imports pattern** (RunWorkspacePage.tsx lines 1-50):
```typescript
import { Alert, Box, Card, CardContent, Chip, Container, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";

import { GlossaryTerm } from "../../components/glossary/GlossaryTerm";
import { useAppUi } from "../../app/ui/AppUiProvider";
import { ContentCardSkeleton, PageIntroSkeleton } from "../../components/loading/LoadingSkeletons";
import { getProtocolColor } from "../../lib/trace/eventColors";
import type { /* race types */ } from "../../lib/types/api";
```
Path-alias style: `../../` relative imports. No barrel files. Named exports only.

**Route-param fetch branch** (ReportDetailPage.tsx lines 19-55) — use as analog for replay mode dispatch:
```typescript
const { run_id } = useParams();           // undefined on /race; defined on /race/:run_id
const [state, dispatch] = useReducer(...)  // for live mode (D-44)
const replay = useRaceReplay(run_id);      // for replay mode
const isReplay = Boolean(run_id);
```

**Outer page shell** (RunWorkspacePage.tsx lines 358-378):
```tsx
return (
  <Stack spacing={3}>
    {loading ? <PageIntroSkeleton /> : (
      <Box>
        <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
          Three-Lane Failure Race
        </Typography>
        <Typography variant="h1" sx={{ maxWidth: 900, color: "primary.main", mb: 1 }}>
          {/* page-state-driven headline */}
        </Typography>
      </Box>
    )}
    {error ? <Alert severity="error">{error}</Alert> : null}
    {/* status strip, scrubber, lanes, banner, methodology, heatmap */}
  </Stack>
);
```

**Page-state-driven loading** uses the `loading ? <Skeleton /> : <Real />` pattern from RunWorkspacePage.tsx 359-374 — apply to each section based on `RaceState.pageState`.

---

### `frontend/src/features/race/components/RaceLaneCard.tsx` (component, derived-state)

**Analog:** `RunWorkspacePage.tsx` lines 870-953 — the per-mode result Card with mode header + chips + final answer + ParallelAgentTimeline + talking-point Paper + failure chips.

**Lane stripe pattern** (adapted from RunWorkspacePage.tsx lines 916-924 talking-point Paper, which uses `borderLeft: 4px solid`):
```tsx
<Card variant="outlined" sx={{
  height: "100%",
  borderLeft: `4px solid ${getProtocolColor(lane)}`,  // 4px lane stripe per UIRACE-03
}}>
  <CardContent>
    <Stack spacing={1.25}>
      <Stack direction="row" justifyContent="space-between" alignItems="center">
        <Typography variant="h3">
          <GlossaryTerm term={lane}>{laneLabel(lane)}</GlossaryTerm>
        </Typography>
        <Chip label={lane} size="small" sx={{ bgcolor: getProtocolColor(lane), color: "#fff" }} />
      </Stack>
      {/* ticker grid */}
      {/* event feed (scrollable) with aria-live="polite" for fault_observed */}
      {/* FailureStateBadge — only when terminal */}
    </Stack>
  </CardContent>
</Card>
```

**Mode header + chip pattern** (RunWorkspacePage.tsx lines 874-891):
```tsx
<Stack direction="row" justifyContent="space-between" alignItems="center">
  <Typography variant="h6">
    <GlossaryTerm term={item.mode}>{roleFirstLabel(item.mode)}</GlossaryTerm>
  </Typography>
  <Stack direction="row" spacing={0.5} alignItems="center">
    <Chip label={item.runtime} size="small" variant="outlined" />
  </Stack>
</Stack>
```

**Metrics chips pattern** (RunWorkspacePage.tsx lines 893-909) — for ticker:
```tsx
<Stack direction="row" spacing={0.5} alignItems="center">
  <Chip label={`${ttff}ms`} size="small" sx={{ bgcolor: getProtocolColor(lane), color: "#fff" }} />
  <Chip label={`${recovered}/${total}`} size="small" variant="outlined" />
</Stack>
```

**Failure event chips** (RunWorkspacePage.tsx lines 939-950) — for fault list per lane:
```tsx
{failures.length > 0 && (
  <Stack spacing={0.5}>
    <Typography variant="caption" sx={{ color: "error.main", fontWeight: 600 }}>
      Faults ({failures.length})
    </Typography>
    <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
      {failures.map((f, i) => (
        <Chip key={i} label={f} size="small" color="error" variant="outlined" />
      ))}
    </Stack>
  </Stack>
)}
```

---

### `frontend/src/features/race/components/RaceLaneTicker.tsx` (component, derived-state)

**Analog:** `TelemetryPage.tsx` `TelemetryCard` (lines 157-169) — the label-above-value pattern.

**Pattern** (TelemetryPage.tsx 157-169):
```tsx
function TelemetryCard(props: { label: string; value: string }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.12em" }}>
          {props.label}
        </Typography>
        <Typography variant="h5" sx={{ color: "primary.main", wordBreak: "break-word" }}>
          {props.value}
        </Typography>
      </CardContent>
    </Card>
  );
}
```

For race ticker: drop the outer `<Card>`, use `<Box>` since the ticker lives inside the lane Card. Keep the Typography pair (overline label + heading-size value). Per UI-SPEC: label uses 14px/400 (`variant="caption"` or `body2`), value uses 18.4px/700 (`variant="h3"`).

---

### `frontend/src/features/race/components/FailureStateBadge.tsx` (component, derived-state)

**Analog:** `RunWorkspacePage.tsx` failure chip pattern (lines 939-950) + scenario chips (831-844).

**Pattern** (combined chip + icon + label per UIRACE-04):
```tsx
import { Chip } from "@mui/material";
import { failureTagColor } from "../../../lib/trace/eventColors";

export function FailureStateBadge({ tag }: { tag: FailureTag }) {
  const cfg = failureTagColor[tag];
  return (
    <Chip
      icon={<cfg.Icon />}
      label={cfg.label}
      sx={{
        bgcolor: cfg.bg,
        color: cfg.text,
        borderRadius: "4px",   // UIRACE-03 pill radius=4 (compact)
        height: 44,            // touch target min per UI-SPEC
      }}
    />
  );
}
```

`Chip` with `icon` prop is established in `RunWorkspacePage.tsx` line 391 (`startIcon={<ShareOutlinedIcon fontSize="small" />}` on Button — same MUI primitive shape).

---

### `frontend/src/features/race/components/CharacteristicFailureBanner.tsx` (component, derived-state)

**Analog:** `RunWorkspacePage.tsx` talking-point Paper (lines 916-938).

**Pattern** (left-border accent + headline + italic clause):
```tsx
<Paper
  elevation={0}
  sx={{
    borderLeft: `4px solid`,
    borderColor: "primary.main",
    bgcolor: "background.paper",
    p: 3,                    // 24px lg per spacing scale
    borderRadius: 0,         // UIRACE-03 banner=0
  }}
  role="banner"              // ARIA landmark per UI-SPEC
>
  <Typography variant="h2" component="h1">
    {staticHeader} <Typography component="span" variant="h2" sx={{ fontStyle: "italic" }}>{dynamicClause}</Typography>
  </Typography>
</Paper>
```
Reference excerpt (RunWorkspacePage.tsx 916-938):
```tsx
<Paper elevation={0} sx={{
  borderLeft: `4px solid ${getProtocolColor(item.mode)}`,
  bgcolor: "action.hover",
  p: 1.5,
}}>
  <Typography variant="subtitle2" fontWeight="bold">{item.ticket.talking_point.headline}</Typography>
  <Typography variant="body2" sx={{ mt: 0.5 }}>{item.ticket.talking_point.sentence}</Typography>
  <Typography variant="body2" sx={{ mt: 0.5, fontStyle: "italic", color: "text.secondary" }}>
    {item.ticket.talking_point.callout}
  </Typography>
</Paper>
```

---

### `frontend/src/features/race/components/MethodologySection.tsx` (component, static)

**Analog:** Inferred from UI-SPEC explicit "flat section, no Paper/Card" rule — the page-intro `<Box>` block in `RunWorkspacePage.tsx` lines 362-373 is the closest pattern (flat Box + Typography).

**Pattern**:
```tsx
<Box component="aside" role="complementary" sx={{ bgcolor: "background.default", py: 6 }}>
  <Container maxWidth="lg">
    <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
      Methodology
    </Typography>
    <Typography variant="h2" sx={{ color: "primary.main", mb: 2 }}>
      How we measure failure recovery
    </Typography>
    <Typography variant="body1" sx={{ maxWidth: 760, color: "text.secondary" }}>
      {/* methodology prose with GlossaryTerm wraps for ttff, recovery_rate, hardness_profile */}
    </Typography>
  </Container>
</Box>
```

---

### `frontend/src/features/race/context/FirstMentionProvider.tsx` (provider, event-driven)

**Analog:** `frontend/src/app/ui/AppUiProvider.tsx` — exact match for Context + Provider + custom hook trio.

**Full pattern excerpt** (AppUiProvider.tsx 14-58):
```tsx
const AppUiContext = createContext<AppUiContextValue | null>(null);

export function AppUiProvider(props: { children: React.ReactNode }) {
  const [isPresentationChromeHidden, setPresentationChromeHidden] = useState(false);
  const [toast, setToast] = useState<AppToast | null>(null);

  const showToast = useCallback((nextToast: AppToast) => {
    setToast(nextToast);
  }, []);

  const value = useMemo(
    () => ({ isPresentationChromeHidden, setPresentationChromeHidden, showToast }),
    [isPresentationChromeHidden, showToast],
  );

  return <AppUiContext.Provider value={value}>{props.children}</AppUiContext.Provider>;
}

export function useAppUi() {
  const context = useContext(AppUiContext);
  if (!context) {
    throw new Error("useAppUi must be used within AppUiProvider.");
  }
  return context;
}
```

**Apply for FirstMentionProvider:**
```tsx
interface FirstMentionContextValue {
  hasSeen: (term: string) => boolean;
  markSeen: (term: string) => void;
}
// state = useState(() => new Set<string>())
// markSeen = useCallback((term) => setSeen(prev => new Set(prev).add(term)), [])
// useFirstMention() throws if used outside provider
```

Per D-51: NO sessionStorage / localStorage. Set is reset by mount/unmount of the provider (route-scoped wrap). Provider mounts inside the `/race` and `/race/:run_id` route elements only.

---

### `frontend/src/features/race/hooks/useRaceReplay.ts` (hook, request-response)

**Analog:** `ReportDetailPage.tsx` lines 19-55 — fetch-by-route-param into state with cleanup-on-unmount.

**Pattern excerpt** (ReportDetailPage.tsx 25-55):
```typescript
useEffect(() => {
  let active = true;

  async function loadReport() {
    try {
      const payload = await fetchReportDetail(reportName);
      if (active) {
        setReport(payload);
      }
    } catch (loadError) {
      if (active) {
        setError(loadError instanceof Error ? loadError.message : "Failed to load the report.");
      }
    } finally {
      if (active) {
        setLoading(false);
      }
    }
  }

  if (reportName) {
    void loadReport();
  } else {
    setLoading(false);
    setError("Missing report name.");
  }

  return () => {
    active = false;
  };
}, [reportName]);
```

**Adapt for `useRaceReplay(run_id)`:**
- Wrap as a custom hook returning `{ trace, loading, error }`.
- Stub the fetch endpoint per CONTEXT deferred: `/api/race/runs/:run_id/trace` (Phase 9 HEAT-03 ships the backend; Phase 8 ships the typed call signature).
- Add the call to `frontend/src/lib/api/client.ts` mirroring `fetchReportDetail` (lines 82-84).

---

### `frontend/src/features/race/hooks/useRaceStream.ts` (hook, streaming WebSocket)

**Analog:** NONE. No `useReducer` or `WebSocket` usage exists in `frontend/src/`. **Planner: use UI-SPEC D-44 as authoritative pattern source.**

**Required shape per CONTEXT D-44 + D-45:**
- `useReducer<RaceState, RaceEvent>` over the closed Phase 7 ws event union.
- WebSocket connection in `useEffect`; cleanup closes socket.
- Reconnect carries per-lane `last_turn_index` cursor as ws URL query params (D-45).
- Endpoint: `/api/race/ws` (CONTEXT canonical_refs).
- Closest neighbour-pattern: existing `useEffect`+cleanup style from ReportDetailPage 25-55 — adopt the `let active = true; ... return () => { active = false; }` cleanup discipline, replacing `fetch` with `new WebSocket(url)` and `socket.close()`.

**Skeleton:**
```typescript
export function useRaceStream(run_id?: string) {
  const [state, dispatch] = useReducer(raceReducer, initialRaceState);

  useEffect(() => {
    const cursors = perLaneLastTurnIndex(state); // for resume
    const url = `${WS_BASE}/api/race/ws?${qs(cursors)}`;
    const socket = new WebSocket(url);
    socket.onmessage = (ev) => dispatch(JSON.parse(ev.data));
    socket.onerror = () => dispatch({ type: "ws_error" });
    socket.onclose = () => dispatch({ type: "ws_closed" });
    return () => socket.close();
  }, [run_id]);

  return state;
}
```
Type the event union from existing `frontend/src/lib/types/api.ts` `TraceEvent` extended with Phase 6/7 events (CONTEXT integration_points).

---

### `frontend/src/features/race/components/HeatmapScaffold.tsx` (component, grid render)

**Analog:** NONE. No CSS-Grid heatmap precedent in codebase (recharts ParallelAgentTimeline is the closest data-viz, but uses BarChart not Grid).

**Authoritative pattern source: UI-SPEC + D-46 + D-47.**

**Skeleton per UI-SPEC:**
```tsx
<Box
  role="grid"
  aria-label="Hardness vs Failure Heatmap"
  sx={{
    display: "grid",
    gridTemplateColumns: `auto repeat(${lanes.length}, 1fr)`,
    gridTemplateRows: `auto repeat(${rows.length}, minmax(44px, 1fr))`,  // 44px touch target
    gap: 0,                                                                // touching cells
    border: "1px solid rgba(16, 32, 51, 0.08)",
  }}
>
  {/* row + col headers */}
  {rows.map((row) => lanes.map((lane) => (
    <Box
      key={`${row}-${lane}`}
      role="gridcell"
      tabIndex={0}
      sx={{
        bgcolor: cell ? failureTagColor[cell.tag].bg : "action.hover",
        borderRadius: 0,                  // UIRACE-03 cell=0
        p: 1,
        minHeight: 44,                    // touch target
        "&:focus-visible": {
          outline: "3px solid",
          outlineColor: "primary.main",
          outlineOffset: 2,
        },
      }}
    >
      {cell ? (
        <Stack direction="row" spacing={0.5}>
          <cell.Icon fontSize="small" />
          <Typography variant="caption">{cell.recoveryFraction}</Typography>
        </Stack>
      ) : null}
    </Box>
  )))}
  {/* heatmap-empty overlay (D-47): full grid stays mounted; absolute-positioned center overlay */}
</Box>
```

**Empty-state overlay rule (D-47):** Grid never unmounts; muted neutral cells render in place; centered overlay copy ("No runs yet — Launch a race to populate the heatmap.") layered with `position: absolute`.

Adopt focus outline color (`primary.main` = `#17475f`) and 3px width from UI-SPEC Interaction Contract. `prefers-contrast: more` widens to 4px (UI-SPEC color section).

---

### `frontend/src/features/race/components/ReplayScrubber.tsx` (component, event-driven)

**Analog:** NONE. No `MUI Slider` usage exists in the frontend. **Planner: use MUI 7 `<Slider>` defaults plus UI-SPEC interaction contract.**

**Skeleton per D-49 + UI-SPEC:**
```tsx
<Stack spacing={1}>
  <Slider
    value={turnIndex}
    onChange={(_, v) => onScrub(v as number)}
    min={0}
    max={maxTurn}
    step={1}
    sx={{ height: 40 }}                 // UI-SPEC scrubber min hit area
    aria-label="Replay turn scrubber"
  />
  <Box aria-live="polite" sx={{ /* throttled to 200ms during drag */ }}>
    Turn {turnIndex} of {maxTurn}
  </Box>
</Stack>
```

Throttle aria-live announcements to one per 200ms during drag, full announcement on release (CONTEXT specifics + UI-SPEC Interaction Contract).

---

### `frontend/src/features/race/components/RaceStatusStrip.tsx` (component, derived-state)

**Analog:** `AppShell.tsx` Toolbar pattern (lines 47-78) — sticky strip with left-aligned label + right-aligned controls.

**Pattern excerpt** (AppShell.tsx 47-77):
```tsx
<Toolbar sx={{ gap: 2, flexWrap: "wrap", py: 1 }}>
  <Box sx={{ flexGrow: 1 }}>
    <Typography variant="overline" sx={{ letterSpacing: "0.16em", color: "secondary.main" }}>
      Protocol Learning Lab
    </Typography>
    <Typography variant="h6" sx={{ color: "primary.main" }}>A2A vs MCP Demo Platform</Typography>
  </Box>
  <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
    {/* nav buttons */}
  </Stack>
</Toolbar>
```

**For RaceStatusStrip:**
```tsx
<Box sx={{
  height: 48,                    // UI-SPEC: status strip 48px fixed
  bgcolor: "background.paper",
  borderBottom: "1px solid rgba(16, 32, 51, 0.08)",
  px: 2,
}}>
  <Stack direction="row" alignItems="center" justifyContent="space-between" sx={{ height: "100%" }}>
    <Box aria-live="polite">                       {/* page-state label, ws reconnect status */}
      <Typography variant="body2">{stateLabel}</Typography>
    </Box>
    {isReplay ? <ReplayPill runId={runId} /> : null}    {/* right-aligned per D-49 */}
  </Stack>
</Box>
```

Adopt the `borderBottom: "1px solid rgba(16, 32, 51, 0.08)"` divider rule from AppShell.tsx line 45.

---

### `frontend/src/features/race/components/ReplayPill.tsx` (component, static)

**Analog:** `RunWorkspacePage.tsx` Chip patterns (lines 884-890, 944-948).

**Pattern per UI-SPEC + D-49:**
```tsx
<Chip
  label={`REPLAY · ${runId.slice(0, 8)}`}
  sx={{
    bgcolor: "secondary.main",            // #b85c38 warm accent
    color: "common.white",
    borderRadius: 999,                    // UIRACE-03 pill=999
    fontSize: "0.875rem",
    fontWeight: 700,
    textTransform: "uppercase",
    letterSpacing: "0.08em",
  }}
/>
```

---

### `frontend/src/components/glossary/GlossaryTerm.tsx` (modified, branch on context)

**Existing body** (full file, 26 lines) — keep `Tooltip` branch for subsequent mentions.

**Extend** with `useFirstMention()` from new `FirstMentionProvider`:
```tsx
import Popover from "@mui/material/Popover";
import Button from "@mui/material/Button";
import Tooltip from "@mui/material/Tooltip";
import { useState, type ReactNode } from "react";
import { glossaryTerms } from "../../lib/glossary/glossaryTerms";
import { useFirstMention } from "../../features/race/context/FirstMentionProvider";

export function GlossaryTerm({ term, children }: { term: string; children: ReactNode }) {
  const definition = glossaryTerms[term];
  const firstMention = useFirstMention();      // safe: returns null outside Provider
  const isFirstMention = firstMention && !firstMention.hasSeen(term);
  const [anchorEl, setAnchorEl] = useState<HTMLElement | null>(null);

  if (!definition) return <>{children}</>;

  if (isFirstMention) {
    return (
      <>
        <span
          onClick={(e) => setAnchorEl(e.currentTarget)}
          tabIndex={0}                                       // keyboard target per UI-SPEC tab order
          style={{ borderBottom: "1px dashed currentColor", cursor: "help" }}
        >
          {children}
        </span>
        <Popover
          open={Boolean(anchorEl)}
          anchorEl={anchorEl}
          onClose={() => setAnchorEl(null)}
          anchorOrigin={{ vertical: "bottom", horizontal: "left" }}
          transformOrigin={{ vertical: "top", horizontal: "left" }}
        >
          <Stack spacing={1.5} sx={{ p: 2, maxWidth: 360 }}>
            <Typography variant="h6">{term}</Typography>
            <Typography variant="body2">{definition}</Typography>
            <Button
              size="small"
              variant="contained"
              onClick={() => { firstMention.markSeen(term); setAnchorEl(null); }}
            >
              Got it
            </Button>
          </Stack>
        </Popover>
      </>
    );
  }

  // Existing Tooltip branch (preserve)
  return (
    <Tooltip title={definition} arrow>
      <span style={{ borderBottom: "1px dashed currentColor", cursor: "help" }}>{children}</span>
    </Tooltip>
  );
}
```

**Backward-compat note:** Outside the FirstMentionProvider, `useFirstMention()` must return `null` (NOT throw) — diverges from `useAppUi`'s strict throw pattern, because `GlossaryTerm` is used on Run/Compare pages too. Document this in the hook.

---

### `frontend/src/lib/trace/eventColors.ts` (modified, static lookup)

**Analog:** Self — the existing `protocolColor` and `toneColor` Records (lines 5-18) are the exact pattern.

**Existing pattern excerpt** (eventColors.ts 5-18):
```typescript
export const protocolColor: Record<string, string> = {
  mcp: "#1976d2",
  a2a: "#7b1fa2",
  hybrid: "#2e7d32",
  baseline: "#757575",
};

export const toneColor = {
  error: "#c62828",
  warning: "#ed6c02",
  success: "#2e7d32",
  info: "#757575",
} as const;
```

**Extend per UIRACE-04 + UI-SPEC failureTagColor table** — append:
```typescript
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import CancelOutlinedIcon from "@mui/icons-material/CancelOutlined";
import VisibilityOffOutlinedIcon from "@mui/icons-material/VisibilityOffOutlined";
import ErrorOutlineIcon from "@mui/icons-material/ErrorOutline";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import type { ComponentType } from "react";

export type FailureTag = "recovered" | "gave_up" | "kept_going_without_noticing" | "kept_going_to_failure" | "indeterminate";

export const failureTagColor: Record<FailureTag, { bg: string; text: string; Icon: ComponentType; label: string }> = {
  recovered:                    { bg: "#e8f5e9", text: "#1b5e20", Icon: CheckCircleOutlineIcon,   label: "Recovered" },
  gave_up:                      { bg: "#fce4ec", text: "#880e4f", Icon: CancelOutlinedIcon,        label: "Gave Up" },
  kept_going_without_noticing:  { bg: "#fff3e0", text: "#e65100", Icon: VisibilityOffOutlinedIcon, label: "Kept Going (Unaware)" },
  kept_going_to_failure:        { bg: "#fbe9e7", text: "#bf360c", Icon: ErrorOutlineIcon,          label: "Kept Going to Failure" },
  indeterminate:                { bg: "#f5f5f5", text: "#424242", Icon: HelpOutlineIcon,           label: "Indeterminate" },
};
```

Same export style as `protocolColor` (named export, module-level Record). Existing convention: no function wrapper unless needed (e.g., `getProtocolColor` exists for fallback handling — `failureTagColor` is closed-set so direct lookup is fine).

---

### `frontend/src/lib/glossary/glossaryTerms.ts` (modified, static lookup)

**Analog:** Self — the existing `glossaryTerms: Record<string, string>` (full file 1-39).

**Pattern:** Append the 8 race terms (UIRACE-07 + UI-SPEC Glossary Extension table) directly to the existing Record. Keep the file-level docstring at top (lines 1-5). No new file, no map merge — just append entries.

**Append block:**
```typescript
ttff: "Time to first fault — the elapsed milliseconds from run start until the first injected fault event lands in the trace.",
recovery_rate: "The fraction of runs in which the agent fully recovered from an injected fault, expressed as a count (e.g. 12/15).",
hardness_profile: "A structured description of the difficulty characteristics of a task — which hardness types apply and at what intensity.",
recovered: "A fault classification tag: the agent detected the fault and returned to a correct execution path within K=3 turns.",
gave_up: "A fault classification tag: the agent detected the fault and abandoned the task rather than attempting recovery.",
kept_going_without_noticing: "A fault classification tag: the agent did not acknowledge the fault and continued executing as if nothing had changed.",
kept_going_to_failure: "A fault classification tag: the agent continued past the fault point and ultimately produced an incorrect or failed result.",
indeterminate: "A fault classification tag: the available trace evidence was insufficient to assign any of the four primary recovery tags.",
```

---

### `frontend/src/app/routes.tsx` (modified, route registration)

**Analog:** Self — existing lazy + `withSuspense` pattern (full file 1-110).

**Existing lazy import pattern** (routes.tsx 7-10, repeated 8x):
```typescript
const LearningPage = lazy(() =>
  import("../features/learn/LearningPage").then((module) => ({
    default: module.LearningPage,
  })),
);
```

**Existing route registration** (routes.tsx 66-108):
```typescript
export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: withSuspense(<RunWorkspacePage />) },
      { path: "learn", element: withSuspense(<LearningPage />) },
      // ...
    ],
  },
]);
```

**Extend:**
```typescript
const RacePage = lazy(() =>
  import("../features/race/RacePage").then((module) => ({
    default: module.RacePage,
  })),
);

// In children array, add (must wrap in FirstMentionProvider):
{ path: "race", element: withSuspense(<FirstMentionProvider><RacePage /></FirstMentionProvider>) },
{ path: "race/:run_id", element: withSuspense(<FirstMentionProvider><RacePage /></FirstMentionProvider>) },
```

Per D-51, FirstMentionProvider wraps both `/race` and `/race/:run_id` so the seen-set resets on route exit (unmount). Both routes render the same `RacePage`; the route param `run_id` selects live vs replay data source inside the component.

Add a "Race" nav item to `AppShell.tsx` `navItems` (lines 14-23) following the existing icon + label shape.

---

## Shared Patterns

### 1. Page Section Loading Gate

**Source:** `RunWorkspacePage.tsx` lines 359-374, `ReportDetailPage.tsx` lines 67-117, `TelemetryPage.tsx` lines 64-89
**Apply to:** `RacePage.tsx` for each major section (status strip, lanes, banner, methodology, heatmap)
**Pattern:**
```tsx
{loading ? <PageIntroSkeleton /> : <RealHeader />}
{error ? <Alert severity="error">{error}</Alert> : null}
```

### 2. Cleanup-on-Unmount in useEffect

**Source:** `RunWorkspacePage.tsx` 211-244, `ReportDetailPage.tsx` 25-55, `TelemetryPage.tsx` 15-39
**Apply to:** `useRaceStream` (close ws on unmount), `useRaceReplay` (cancel fetch on unmount)
**Pattern:**
```typescript
useEffect(() => {
  let active = true;
  async function load() {
    try {
      const payload = await fetchX();
      if (active) setX(payload);
    } catch (err) {
      if (active) setError(err instanceof Error ? err.message : "Failed.");
    } finally {
      if (active) setLoading(false);
    }
  }
  void load();
  return () => { active = false; };
}, [/* deps */]);
```

### 3. Module-Level Record for Static Lookup Tables

**Source:** `eventColors.ts` 5-10, `glossaryTerms.ts` 6-39
**Apply to:** `failureTagColor` (extension), 8 new glossary terms (extension), any race page-state -> label map.
**Convention:** Named export, no function wrapper unless fallback needed, frozen-shape `Record<K, V>`.

### 4. GlossaryTerm Wrap Around First Mention

**Source:** `RunWorkspacePage.tsx` lines 876-878
**Apply to:** All race-specific terminology in RacePage, MethodologySection, FailureStateBadge labels.
**Pattern:**
```tsx
<Typography variant="h3">
  <GlossaryTerm term="recovery_rate">Recovery Rate</GlossaryTerm>
</Typography>
```
Inside `<FirstMentionProvider>` the first wrap renders the Popover variant; subsequent wraps render the existing Tooltip.

### 5. Test Setup with Providers + MemoryRouter

**Source:** `frontend/src/test/renderWithProviders.tsx` (full file 1-18), `RunWorkspacePage.test.tsx` lines 77-88, `routes.test.tsx` lines 173-202
**Apply to:** Race page tests must wrap in `ThemeProvider + CssBaseline + AppUiProvider + MemoryRouter` and ALSO `FirstMentionProvider` for any test that exercises glossary popover. Race tests likely need a `MockWebSocket` shim (no precedent in codebase — planner: use `vi.stubGlobal('WebSocket', MockWebSocketClass)`).

### 6. Color via getProtocolColor

**Source:** `eventColors.ts` 23-25, used in `RunWorkspacePage.tsx` 897, `ParallelAgentTimeline.tsx` 24
**Apply to:** Lane stripe color, lane chip background, lane ticker accent.
**Pattern:** `getProtocolColor(lane)` — handles `mcp`/`a2a`/`hybrid` and the rare `baseline` fallback.

### 7. ARIA Landmarks via component prop

**Source:** `AppShell.tsx` (implicit `<header>` via `<AppBar>`); UI-SPEC Interaction Contract.
**Apply to:** `RaceStatusStrip` no role (sub-region), `CharacteristicFailureBanner` `role="banner"` (note: collides with AppBar — UI-SPEC explicitly accepts this for "ARIA landmark `role=\"banner\"`" on the failure banner; planner verify with a11y check), `MethodologySection` `<Box component="aside" role="complementary">`, `HeatmapScaffold` `role="grid"` + `role="gridcell"`. Lane row + race content under `role="main"` (provided by AppShell `<main>` semantics — verify AppShell uses `<main>` or add explicit wrapper).

---

## No Analog Found

These files have no close codebase precedent. Planner must use UI-SPEC + CONTEXT decisions as the authoritative source:

| File | Role | Data Flow | Why no analog |
|------|------|-----------|---------------|
| `frontend/src/features/race/hooks/useRaceStream.ts` | hook | streaming WebSocket | **No `useReducer` precedent.** **No `WebSocket` precedent.** All existing data flow is fetch-based. |
| `frontend/src/features/race/components/HeatmapScaffold.tsx` | component | grid render | **No CSS-Grid heatmap precedent.** Existing data viz uses recharts BarChart only. |
| `frontend/src/features/race/components/ReplayScrubber.tsx` | component | event-driven (drag) | **No MUI Slider usage anywhere in frontend.** |
| `frontend/src/features/race/RacePage.tsx` page-state machine | derived state | event-driven | The 12-state page-state enum has no precedent (RunWorkspacePage has only `loading`/`running`/`result` flags). Use D-44 reducer + Claude's-Discretion choice (FSM enum vs derived). |

For these files, the planner should reference:
- **WebSocket**: MDN `WebSocket` API + D-44/D-45 reducer contract. Use existing `let active = true` cleanup discipline as the unmount pattern.
- **CSS Grid heatmap**: UI-SPEC HeatmapScaffold spec + D-46/D-47.
- **Slider**: MUI 7 `<Slider>` defaults + UI-SPEC scrubber contract + D-49.
- **Page-state enum**: UI-SPEC Page State Matrix (12 states) is authoritative.

---

## Metadata

**Analog search scope:** `frontend/src/features/`, `frontend/src/components/`, `frontend/src/lib/`, `frontend/src/app/`
**Files scanned:** 38 (.ts/.tsx in `frontend/src/`)
**Searches:** `useReducer`, `WebSocket`, `Popover`, `Slider`, page-component patterns, hook patterns, Card/Chip patterns, ARIA landmark usage
**Reads:** 13 (RunWorkspacePage, RunWorkspacePage.test, ReportDetailPage, TelemetryPage, AppShell, AppUiProvider, theme.ts, routes.tsx, routes.test.tsx, GlossaryTerm, glossaryTerms, eventColors, ParallelAgentTimeline, TraceExplorer head, LoadingSkeletons, renderWithProviders, api/client.ts)
**Pattern extraction date:** 2026-04-29

---

*Phase: 8-race-page-ui-visual-contract*
*PATTERNS.md created: 2026-04-29*
