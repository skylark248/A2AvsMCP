import Chip from "@mui/material/Chip";

interface ReplayPillProps {
  runId: string;
}

// D-49: Replay state shows right-aligned pill in status strip — "REPLAY · run abc123"
// UIRACE-03: pill border-radius = 999 (full pill shape)
// UI-SPEC Typography line 69: 14px/700, uppercase, letter-spacing 0.08em
// T-08-04 mitigation: runId rendered as React text child — auto-escaped, never innerHTML
export function ReplayPill({ runId }: ReplayPillProps) {
  // Truncate to first 8 chars (D-49). React text-child rendering auto-escapes (T-08-04 mitigation).
  const truncated = runId.slice(0, 8);
  return (
    <Chip
      label={`REPLAY · ${truncated}`}
      data-testid="replay-pill"
      sx={{
        bgcolor: "secondary.main", // #b85c38 warm accent (D-49)
        color: "common.white",
        borderRadius: "999px", // UIRACE-03 pill=999
        fontSize: "0.875rem", // UI-SPEC Typography label size (14px)
        fontWeight: 700,
        textTransform: "uppercase",
        letterSpacing: "0.08em", // UI-SPEC Typography line 69
        height: 32,
      }}
    />
  );
}
