import { Box, Container, Stack, Typography } from "@mui/material";
import { useParams } from "react-router-dom";

// RacePage shell — section slots stubbed for Plans 04-06 to fill in.
// Both live mode (/race) and replay mode (/race/:run_id) render this component.
// The route param run_id flips data source from useRaceStream → useRaceReplay (D-48).
export function RacePage() {
  const { run_id } = useParams<{ run_id?: string }>();
  const isReplay = Boolean(run_id);

  return (
    <Box data-testid={isReplay ? "race-replay-mode" : "race-live-mode"}>
      {/* Status strip slot — Plan 04 fills (48px, session-level metadata per UIRACE-01) */}
      <Box
        data-testid="race-status-strip"
        sx={{ height: 48, borderBottom: "1px solid rgba(16, 32, 51, 0.08)" }}
      />

      {/* Scrubber slot — replay-only per D-49; Plan 05 fills */}
      {isReplay ? <Box data-testid="race-scrubber-slot" /> : null}

      <Container maxWidth="lg" sx={{ maxWidth: 1200, py: 6 }}>
        <Stack spacing={6}>
          <Box>
            <Typography
              variant="overline"
              sx={{ color: "secondary.main", letterSpacing: "0.16em" }}
            >
              Three-Lane Failure Race
            </Typography>
            <Typography variant="h1" sx={{ color: "primary.main", maxWidth: 900 }}>
              How three protocol lanes recover (or don&apos;t) from injected faults
            </Typography>
          </Box>

          {/* Three-lane row — Plan 04 fills with RaceLaneCard ×3, gap=xl(32px) per UIRACE-01 */}
          <Box
            data-testid="race-lane-row"
            sx={{
              display: "flex",
              flexDirection: { xs: "column", md: "row" },
              gap: { xs: 2, md: 4 },
            }}
          />

          {/* Banner slot — Plan 04 fills (CharacteristicFailureBanner, 0px radius, 4px primary rule) */}
          <Box data-testid="race-banner-slot" />

          {/* Methodology section slot — flat, no Paper/Card per UIRACE-03 */}
          <Box
            data-testid="race-methodology-slot"
            component="aside"
            role="complementary"
          />

          {/* Heatmap slot — Plan 05 fills (CSS Grid, role=grid per D-46) */}
          <Box data-testid="race-heatmap-slot" />
        </Stack>
      </Container>
    </Box>
  );
}
