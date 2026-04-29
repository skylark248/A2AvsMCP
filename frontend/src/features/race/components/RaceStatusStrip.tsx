import { Box, Stack, Typography } from "@mui/material";
import { ReplayPill } from "./ReplayPill";
import type { PageState } from "../../../lib/types/race";

// UI-SPEC Copywriting Contract (lines 263-278) — verbatim labels for all 12 PageState values.
// "done", "replay", "sparse-heatmap", "indeterminate", "lane-failed", "heatmap-empty" all use
// "Completed" as the base label (timestampLabel prop appended at runtime by Plan 06).
const STATUS_LABEL: Record<PageState, string> = {
  "pre-race": "Ready",
  "countdown": "Starting in…",          // {N} interpolated by parent (Plan 06 wires)
  "live-n1": "Live · 1 run",
  "live-n5": "Live · 5 runs",
  "done": "Completed",                   // {timestamp} interpolated by parent
  "replay": "Completed",                 // replay pill carries replay context (D-49)
  "sparse-heatmap": "Completed",
  "ws-disconnected": "Disconnected",
  "ws-reconnecting": "Reconnecting…",
  "indeterminate": "Completed",
  "lane-failed": "Completed",
  "heatmap-empty": "Completed",
};

// States that should NOT show the timestamp suffix even when provided.
const NO_TIMESTAMP_STATES: ReadonlySet<PageState> = new Set([
  "ws-disconnected",
  "ws-reconnecting",
  "pre-race",
  "live-n1",
  "live-n5",
  "countdown",
]);

interface RaceStatusStripProps {
  /** Current page state from derivePageState (Plan 02). */
  state: PageState;
  /** Present in replay mode (D-49): renders right-aligned ReplayPill. */
  runId?: string | null;
  /** Optional suffix appended to "Completed" label (e.g. "12:34 PM"). Plan 06 passes. */
  timestampLabel?: string | null;
}

/**
 * 48px sticky status strip (UI-SPEC line 51, Information Hierarchy top slot).
 *
 * Layout: state label left-aligned | ReplayPill right-aligned when in replay mode (D-49).
 * aria-live="polite" on label container surfaces ws-reconnecting transitions
 * to screen readers (UI-SPEC ARIA Landmarks aria-live table, line 233).
 *
 * Copywriting contract: 12-state labels from UI-SPEC Copywriting Contract lines 263-278.
 * Visual contract: height=48, borderBottom="1px solid rgba(16, 32, 51, 0.08)" per AppShell analog.
 */
export function RaceStatusStrip({ state, runId, timestampLabel }: RaceStatusStripProps) {
  const baseLabel = STATUS_LABEL[state];
  const label =
    timestampLabel && !NO_TIMESTAMP_STATES.has(state)
      ? `${baseLabel} · ${timestampLabel}`
      : baseLabel;

  return (
    <Box
      data-testid="race-status-strip"
      sx={{
        height: 48,                                              // UI-SPEC: status strip 48px fixed (line 51)
        bgcolor: "background.paper",
        borderBottom: "1px solid rgba(16, 32, 51, 0.08)",      // AppShell analog (PATTERNS.md line 519)
        px: 2,
      }}
    >
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        sx={{ height: "100%" }}
      >
        {/* aria-live="polite": WS reconnect status announcements (UI-SPEC line 233) */}
        <Box aria-live="polite" data-testid="race-status-label">
          <Typography variant="body2">{label}</Typography>
        </Box>

        {/* Right-aligned ReplayPill rendered only when runId present (D-49) */}
        {runId ? <ReplayPill runId={runId} /> : null}
      </Stack>
    </Box>
  );
}
