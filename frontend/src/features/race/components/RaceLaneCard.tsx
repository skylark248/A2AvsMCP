import Box from "@mui/material/Box";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import Chip from "@mui/material/Chip";
import Stack from "@mui/material/Stack";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import { getProtocolColor } from "../../../lib/trace/eventColors";
import { GlossaryTerm } from "../../../components/glossary/GlossaryTerm";
import { FailureStateBadge } from "./FailureStateBadge";
import { RaceLaneTicker } from "./RaceLaneTicker";
import type { LaneState, RaceLane, RaceEvent } from "../../../lib/types/race";

const LANE_LABEL: Record<RaceLane, string> = {
  pure_mcp: "Pure MCP",
  pure_a2a: "Pure A2A",
  hybrid: "Hybrid",
};

function formatEvent(ev: RaceEvent): string {
  // T-08-08 mitigation: events rendered as plain React text children — no innerHTML
  if (ev.type === "fault_observed") {
    const evidence = "evidence" in ev ? ev.evidence : "";
    return `Fault observed: ${evidence}`;
  }
  if ("turn_index" in ev) {
    return `${ev.type} (turn ${ev.turn_index})`;
  }
  return ev.type;
}

// RaceLaneCard: Per-lane card with protocol color stripe (UIRACE-03)
// Lane stripe: 4px left border in protocol color; widens to 6px under prefers-contrast: more
// (UI-SPEC line 122 high-contrast widen — encoded here via useMediaQuery, NOT retrofitted later)
// aria-live="polite" on event feed for fault_observed accessibility (UIRACE-06)
// Lane name wrapped in <GlossaryTerm> for first-mention popover (UIRACE-07)
export function RaceLaneCard({ lane }: { lane: LaneState }) {
  const color = getProtocolColor(lane.lane);

  // UI-SPEC line 122: prefers-contrast: more widens lane stripe from 4px → 6px.
  // Use useMediaQuery (not raw @media in sx string) so a11y tests can mock it deterministically.
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
        // UIRACE-03: 4px left-edge stripe in protocol color; widened to 6px under prefers-contrast (UI-SPEC line 122)
        borderLeft: `${stripeWidth}px solid ${color}`,
        // Border radius defaults to theme 18px — UIRACE-03 lane card scale
      }}
    >
      <CardContent>
        <Stack spacing={1.5}>
          {/* Lane header: name + protocol chip */}
          <Stack direction="row" justifyContent="space-between" alignItems="center">
            <Typography variant="h3">
              <GlossaryTerm term={lane.lane}>
                {LANE_LABEL[lane.lane]}
              </GlossaryTerm>
            </Typography>
            <Chip
              label={lane.lane}
              size="small"
              sx={{ bgcolor: color, color: "#fff" }}
            />
          </Stack>

          {/* Ticker grid: TTFF, Recovery Rate, Turns, Score */}
          <RaceLaneTicker lane={lane} />

          {/* Terminal failure badge — only rendered when lane reaches terminal state */}
          {lane.terminal_tag ? <FailureStateBadge tag={lane.terminal_tag} /> : null}

          {/* Event feed — aria-live for fault_observed announcements (UIRACE-06) */}
          <Box
            aria-live="polite"
            data-testid="race-lane-event-feed"
            sx={{
              maxHeight: 240,
              overflow: "auto",
              borderTop: "1px solid",
              borderColor: "divider",
              pt: 1,
            }}
          >
            {lane.events.slice(-20).map((ev, i) => (
              <Typography
                key={`${ev.type}-${i}`}
                variant="caption"
                sx={{
                  display: "block",
                  color: ev.type === "fault_observed" ? "error.main" : "text.secondary",
                }}
              >
                {/* Render as plain text — auto-escaped by React (T-08-08 mitigation: never innerHTML) */}
                {formatEvent(ev)}
              </Typography>
            ))}
          </Box>
        </Stack>
      </CardContent>
    </Card>
  );
}
