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
import { useEffect, useMemo, useReducer, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { CharacteristicFailureBanner } from "./components/CharacteristicFailureBanner";
import { CopyHeadlineImageButton } from "./components/CopyHeadlineImageButton";
import { HardnessFailureHeatmap } from "./components/HardnessFailureHeatmap";
import { MethodologySection } from "./components/MethodologySection";
import { RaceLaneCard } from "./components/RaceLaneCard";
import { RaceStatusStrip } from "./components/RaceStatusStrip";
import { ReplayScrubber } from "./components/ReplayScrubber";
import { useRaceHeatmap } from "./hooks/useRaceHeatmap";
import { useRaceReplay } from "./hooks/useRaceReplay";
import { useRaceStream } from "./hooks/useRaceStream";
import { initialRaceState, raceReducer } from "./raceReducer";
import { derivePageState } from "./pageState";
import { startRace } from "../../lib/api/client";
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

  // Phase 10 OG-01/OG-02: ?og=1 mode renders only the screenshot region; ?surface=heatmap
  // swaps the heatmap card in for the title/lanes/banner anchor.
  const [searchParams] = useSearchParams();
  const isOg = searchParams.get("og") === "1";
  const ogSurface = searchParams.get("surface");

  // UIRACE-05 mobile fallback (viewport check).
  // Full ?mode=summary redirect ships in Phase 10. Plan 06 only emits the placeholder branch.
  const isMobile = useMediaQuery("(max-width:479px)");

  // B2 fix: run_id returned from POST /api/race/run; passed to useRaceStream.
  const [wsRunId, setWsRunId] = useState<string>("");

  // Live mode: useRaceStream owns ws + reducer internally.
  // wsRunId gates enabled: WS does not open until startRace() returns a run_id (B2 fix).
  // Additional gates: mobile (T-08-16), replay mode, OG screenshot mode (Phase 10 Risk-4).
  const liveState = useRaceStream(wsRunId, !!wsRunId && !isMobile && !isReplay && !isOg);

  // Replay mode: fetch trace, fold through reducer locally (D-48).
  const replay = useRaceReplay(isReplay && !isMobile ? run_id : undefined);

  // B3 fix: read heatmap data at RacePage scope to drive derivePageState.
  // HardnessFailureHeatmap manages its own fetch separately — this call is independent.
  const { data: heatmapData } = useRaceHeatmap();

  const [replayState, dispatch] = useReducer(
    raceReducer,
    { ...initialRaceState, run_id: run_id ?? null },
  );

  useEffect(() => {
    if (replay.trace) {
      replay.trace.events.forEach((ev) => dispatch(ev));
    }
  }, [replay.trace]);

  // W2 fix: seek position for ReplayScrubber. null = show full replay (all events).
  const [seekPosition, setSeekPosition] = useState<number | null>(null);

  // Derive partial replay state by folding only the first (seekPosition+1) events.
  // When seekPosition is null, full replayState is used.
  const seekedReplayState = useMemo<RaceState | null>(() => {
    if (seekPosition === null || !replay.trace) return null;
    const slice = replay.trace.events.slice(0, seekPosition + 1);
    return slice.reduce<RaceState>(
      raceReducer,
      { ...initialRaceState, run_id: run_id ?? null },
    );
  }, [seekPosition, replay.trace, run_id]);

  const handleStartRace = async () => {
    try {
      const { run_id } = await startRace({
        task_ids: ["summarize_repo"],
        lanes: ["pure_mcp", "pure_a2a", "hybrid"],
        n: 5,
      });
      setWsRunId(run_id);
    } catch (err) {
      // eslint-disable-next-line no-console
      console.error("Failed to start race:", err);
    }
  };

  // Mobile branch — Phase 8 emitted a placeholder; Phase 10 closes UIRACE-05 by
  // consuming /race/<run_id>/og.png via <img>. Phase 8 mobile-viewport gate (D-48)
  // preserved verbatim — only the inner JSX is changed.
  // __testState bypasses this branch in tests so all 12 states can be exercised.
  if (isMobile && !__testState) {
    const ogImageUrl = run_id ? `/race/${run_id}/og.png` : null;
    return (
      <Box data-testid="race-mobile-summary-placeholder" sx={{ p: 2, textAlign: "center" }}>
        {ogImageUrl ? (
          <Box
            component="img"
            src={ogImageUrl}
            alt={`Race summary for ${run_id}`}
            loading="lazy"
            data-testid="race-mobile-summary-image"
            sx={{
              width: "100%",
              maxWidth: 1200,
              height: "auto",
              borderRadius: 2,
            }}
            onError={(e) => {
              (e.currentTarget as HTMLImageElement).style.display = "none";
            }}
          />
        ) : (
          <Typography variant="body1">
            Open on desktop for the live race UI.
          </Typography>
        )}
      </Box>
    );
  }

  // Determine the effective base state: injected (test) > seeked replay > full replay > live
  const baseState: RaceState = __testState ?? (isReplay
    ? { ...(seekedReplayState ?? replayState), run_id: run_id ?? null }
    : liveState);

  // Derive the 12-state page state from observable runtime signals (Plan 02).
  // expected_n: demo default n=5 per RACE-03; Phase 8 ships live-n1 fixture via state shape directly.
  const expected_n = 5;
  const heatmap_has_data = !!heatmapData?.cells?.length;
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

  // Current turn index for scrubber (max across all lanes).
  const maxTurnIndex = Math.max(
    0,
    ...Object.values(baseState.lanes).map((l) => l.last_turn_index),
  );

  // Phase 10 Risk-10: data-og-ready fires only after replay fold completes, otherwise
  // Playwright captures blank lane cards. Live + non-OG branches always pass true.
  const isOgReady = !isOg
    ? true
    : ogSurface === "heatmap"
      ? true // heatmap-anchor uses [data-testid="heatmap-annotation-strip"] as its own ready signal
      : isReplay
        ? replay.trace !== null
        : true;

  return (
    <Box data-testid={isReplay ? "race-replay-mode" : "race-live-mode"}>
      {/* Information hierarchy slot 1: status strip (UIRACE-01). Hidden in OG mode. */}
      {!isOg ? (
        <RaceStatusStrip
          state={pageState}
          runId={baseState.run_id}
          timestampLabel={null}
        />
      ) : null}

      {/* Start Race trigger — visible only in pre-race state (B2 fix: sets wsRunId). */}
      {pageState === "pre-race" && !isReplay && !isOg ? (
        <Box sx={{ px: 2, pb: 1 }}>
          <button
            type="button"
            onClick={() => { void handleStartRace(); }}
            data-testid="race-start-button"
          >
            Start Race
          </button>
        </Box>
      ) : null}

      {/* Information hierarchy slot 2: scrubber (replay only, D-49). Hidden in OG mode. */}
      {isReplay && !isOg ? (
        <ReplayScrubber
          value={seekPosition ?? Math.max(0, (replay.trace?.events.length ?? 1) - 1)}
          max={Math.max(0, (replay.trace?.events.length ?? 1) - 1)}
          onScrub={setSeekPosition}
        />
      ) : null}

      {/* Information hierarchy slot 3+: central column (UIRACE-01 1200px max) */}
      <Container component="main" sx={{ maxWidth: 1200, py: isOg ? 2 : 6 }}>
        {/* OG anchor: title + lanes + banner. Skipped when surface=heatmap. */}
        {ogSurface !== "heatmap" ? (
          <Box
            data-og-anchor
            data-og-ready={isOgReady ? "true" : undefined}
            sx={{ width: isOg ? 1200 : "auto" }}
          >
            <Stack spacing={isOg ? 3 : 6}>
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

              {/* Banner — visible only for terminal + error states (UI-SPEC Page State Matrix).
                  OG-03: actionSlot mounts CopyHeadlineImageButton in live UI only (never inside the OG screenshot itself). */}
              {BANNER_VISIBLE_STATES.includes(pageState) ? (
                <CharacteristicFailureBanner
                  header={bannerHeader}
                  clause={bannerClause}
                  actionSlot={!isOg && run_id ? <CopyHeadlineImageButton runId={run_id} /> : undefined}
                />
              ) : null}
            </Stack>
          </Box>
        ) : null}

        {/* Methodology section — flat aside, static prose, GlossaryTerm wraps (UIRACE-07).
            Hidden in OG mode (Risk-7). */}
        {!isOg ? (
          <Box sx={{ mt: 6 }}>
            <MethodologySection />
          </Box>
        ) : null}

        {/* Heatmap — Phase 9 data-wired wrapper owns its own fetch + transform.
            D-46 + D-47 preserved. In OG mode: hidden when ogSurface != "heatmap";
            wrapped in data-heatmap-anchor + receives ogAnnotation prop when ogSurface == "heatmap". */}
        {!isOg ? (
          <Box sx={{ mt: 6 }}>
            <HardnessFailureHeatmap />
          </Box>
        ) : ogSurface === "heatmap" ? (
          <Box data-heatmap-anchor sx={{ width: 1200 }}>
            <HardnessFailureHeatmap ogAnnotation={true} runId={run_id ?? null} />
          </Box>
        ) : null}
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
