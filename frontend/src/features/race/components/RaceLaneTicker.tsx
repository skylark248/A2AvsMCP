import Box from "@mui/material/Box";
import Typography from "@mui/material/Typography";
import type { ReactNode } from "react";
import { GlossaryTerm } from "../../../components/glossary/GlossaryTerm";
import type { LaneState } from "../../../lib/types/race";

interface MetricCellProps {
  label: ReactNode;
  value: ReactNode;
}

// Label-above-value metric pair per UI-SPEC Typography:
// label: 14px (0.875rem) / 400 / 0.12em letter-spacing / secondary.main
// value: 18.4px (1.15rem) / 700 / primary.main
function MetricCell({ label, value }: MetricCellProps) {
  return (
    <Box>
      <Typography
        variant="caption"
        sx={{
          display: "block",
          color: "secondary.main",
          letterSpacing: "0.12em", // UI-SPEC Typography label
          fontSize: "0.875rem", // 14px label per UI-SPEC
          fontWeight: 400,
          textTransform: "uppercase",
        }}
      >
        {label}
      </Typography>
      <Typography
        sx={{
          color: "primary.main",
          fontSize: "1.15rem", // 18.4px value per UI-SPEC Typography
          fontWeight: 700,
        }}
      >
        {value}
      </Typography>
    </Box>
  );
}

// RaceLaneTicker: label-above-value pattern for 4 race metrics (UIRACE-03)
// GlossaryTerm wraps ttff and recovery_rate for first-mention popover (UIRACE-07)
export function RaceLaneTicker({ lane }: { lane: LaneState }) {
  const ttff = lane.ttff_ms === null ? "—" : `${lane.ttff_ms}ms`;
  const recovery = `${lane.recovered_count}/${lane.total_count}`;
  const turns = lane.last_turn_index < 0 ? "—" : lane.last_turn_index + 1;
  const score = lane.terminal_tag ? lane.terminal_tag.replace(/_/g, " ") : "—";

  return (
    <Box
      data-testid="race-lane-ticker"
      sx={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 2 }}
    >
      <MetricCell
        label={<GlossaryTerm term="ttff">TTFF</GlossaryTerm>}
        value={ttff}
      />
      <MetricCell
        label={<GlossaryTerm term="recovery_rate">Recovery Rate</GlossaryTerm>}
        value={recovery}
      />
      <MetricCell label="Turns" value={turns} />
      <MetricCell label="Score" value={score} />
    </Box>
  );
}
