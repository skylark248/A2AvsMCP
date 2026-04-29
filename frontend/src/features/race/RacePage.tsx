// RacePage — Wave 4 integration (Plan 06).
// Composes all Plan 01-05 outputs: live/replay dispatch, 12 page-state branches,
// mobile-summary placeholder, all section components.
//
// Live mode  (/race):          useRaceStream(!isMobile) — T-08-16 WS gate
// Replay mode (/race/:run_id): useRaceReplay(run_id) + local reducer replay
//
// Design decisions:
//   D-44: useReducer over closed RaceEvent union (no global store)
//   D-48: run_id route param flips data source
//   D-49: ReplayScrubber visible only in replay mode
//   T-08-16: useRaceStream(enabled=!isMobile) gates WS without violating rules-of-hooks

import { Box, Container, Stack, Typography } from "@mui/material";
import useMediaQuery from "@mui/material/useMediaQuery";
import { useEffect, useReducer } from "react";
import { useParams } from "react-router-dom";
import { CharacteristicFailureBanner } from "./components/CharacteristicFailureBanner";
import { HeatmapScaffold } from "./components/HeatmapScaffold";
import { MethodologySection } from "./components/MethodologySection";
import { RaceLaneCard } from "./components/RaceLaneCard";
import { RaceStatusStrip } from "./components/RaceStatusStrip";
import { ReplayScrubber } from "./components/ReplayScrubber";
import { useRaceReplay } from "./hooks/useRaceReplay";
import { useRaceStream } from "./hooks/useRaceStream";
import { initialRaceState, raceReducer } from "./raceReducer";
import { derivePageState } from "./pageState";
import type { PageState, RaceState } from "../../lib/types/race";

// States where the CharacteristicFailureBanner is visible (UI-SPEC Page State Matrix lines 295-302).
const BANNER_VISIBLE_STATES: PageState[] = [
  "done",
  "replay",
  "sparse-heatmap",
  "indeterminate",
  "lane-failed",
  "heatmap-empty",
];

interface RacePageProps {
  /**
   * Test seam: inject a known RaceState to bypass live hooks in tests.
   * When provided, isMobile check is still performed but the baseState is overridden.
   */
  __testState?: RaceState;
}

export function RacePage({ __testState }: RacePageProps = {}) {
  const { run_id: routeRunId } = useParams<{ run_id?: string }>();
  // In test mode, use the fixture's run_id to determine replay mode.
  // In production, use the route param (D-48: /race/:run_id flips data source).
  const run_id = __testState ? (__testState.run_id ?? routeRunId) : routeRunId;
  const isReplay = Boolean(run_id);

  // UIRACE-05 mobile fallback (viewport check).
  // Full ?mode=summary redirect ships in Phase 10. Plan 06 only emits the placeholder branch.
  const isMobile = useMediaQuery("(max-width:479px)");

  // Live mode: useRaceStream owns ws + reducer internally.
  // Pass enabled=!isMobile: gates the WebSocket on mobile without violating rules-of-hooks (T-08-16).
  // Hook is always called (rules-of-hooks compliant); only the side effect is gated by enabled.
  const liveState = useRaceStream(!isMobile && !isReplay);

  // Replay mode: fetch trace, fold through reducer locally (D-48).
  const replay = useRaceReplay(isReplay && !isMobile ? run_id : undefined);
  const [replayState, dispatch] = useReducer(
    raceReducer,
    { ...initialRaceState, run_id: run_id ?? null },
  );

  useEffect(() => {
    if (replay.trace) {
      replay.trace.events.forEach((ev) => dispatch(ev));
    }
  }, [replay.trace]);

  // Mobile branch — Phase 8 emits a placeholder; Phase 10 OG Image ships the cropped anchor PNG.
  // __testState bypasses this branch in tests so all 12 states can be exercised.
  if (isMobile && !__testState) {
    return (
      <Box data-testid="race-mobile-summary-placeholder" sx={{ p: 4, textAlign: "center" }}>
        <Typography variant="body1">Loading summary…</Typography>
      </Box>
    );
  }

  // Determine the effective base state: injected (test) > replay > live
  const baseState: RaceState = __testState ?? (isReplay ? { ...replayState, run_id: run_id ?? null } : liveState);

  // Derive the 12-state page state from observable runtime signals (Plan 02).
  // expected_n: demo default n=5 per RACE-03; Phase 8 ships live-n1 fixture via state shape directly.
  // heatmap_has_data: Phase 8 ships empty path ({}); Phase 9 wires actual cells.
  const expected_n = 5;
  const heatmap_has_data = false;
  const pageState: PageState = derivePageState({
    ws_status: baseState.ws_status,
    lanes: baseState.lanes,
    run_id: baseState.run_id,
    expected_n,
    heatmap_has_data,
  });

  // Banner clause — derived from terminal lane tags per headline templates.
  // T-08-15: banner clause sourced from lane.headline (Phase 7 deterministic templates, not user input).
  const bannerHeader = "Characteristic failure mode:";
  const bannerClause = derivedBannerClause(baseState);

  // Heatmap cells — empty in Phase 8; HeatmapScaffold renders heatmap-empty overlay (D-47).
  // Phase 9 wires actual cells from the heatmap data API.
  const heatmapCells = {};

  // Current turn index for scrubber (max across all lanes).
  const maxTurnIndex = Math.max(
    0,
    ...Object.values(baseState.lanes).map((l) => l.last_turn_index),
  );

  return (
    <Box data-testid={isReplay ? "race-replay-mode" : "race-live-mode"}>
      {/* Information hierarchy slot 1: status strip (UIRACE-01) */}
      <RaceStatusStrip
        state={pageState}
        runId={baseState.run_id}
        timestampLabel={null}
      />

      {/* Information hierarchy slot 2: scrubber (replay only, D-49) */}
      {isReplay ? (
        <ReplayScrubber
          value={maxTurnIndex}
          max={maxTurnIndex}
          onScrub={() => {
            // Phase 9 wires actual scrub-to-turn-index navigation.
          }}
        />
      ) : null}

      {/* Information hierarchy slot 3+: central column (UIRACE-01 1200px max) */}
      <Container component="main" sx={{ maxWidth: 1200, py: 6 }}>
        <Stack spacing={6}>
          {/* Page title block */}
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

          {/* Three-lane row — UIRACE-05 responsive breakpoints via MUI sx flexDirection */}
          <Box
            data-testid="race-lane-row"
            sx={{
              display: "flex",
              flexDirection: { xs: "column", md: "row" },
              gap: { xs: 2, md: 4 },
            }}
          >
            <RaceLaneCard lane={baseState.lanes.pure_mcp} />
            <RaceLaneCard lane={baseState.lanes.pure_a2a} />
            <RaceLaneCard lane={baseState.lanes.hybrid} />
          </Box>

          {/* Banner — visible only for terminal + error states (UI-SPEC Page State Matrix) */}
          {BANNER_VISIBLE_STATES.includes(pageState) ? (
            <CharacteristicFailureBanner header={bannerHeader} clause={bannerClause} />
          ) : null}

          {/* Methodology section — flat aside, static prose, GlossaryTerm wraps (UIRACE-07) */}
          <MethodologySection />

          {/* Heatmap — Phase 8 ships empty scaffold; Phase 9 wires data (D-47) */}
          <HeatmapScaffold cells={heatmapCells} />
        </Stack>
      </Container>
    </Box>
  );
}

/**
 * Pick a representative banner clause from terminal lanes.
 * T-08-15: clause sourced from lane.headline (Phase 7 deterministic templates).
 * No user-controlled input reaches here.
 */
function derivedBannerClause(state: RaceState): string {
  const tagged = Object.values(state.lanes).find((l) => l.terminal_tag !== null);
  if (tagged?.headline) return tagged.headline;
  return "indeterminate — not enough signal to classify.";
}
