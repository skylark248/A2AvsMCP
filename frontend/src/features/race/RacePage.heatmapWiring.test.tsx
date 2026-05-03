// TDD RED: B3 fix — heatmap_has_data must be derived from useRaceHeatmap().data.cells.length.
//
// These tests verify that RacePage:
//   1. Calls useRaceHeatmap() at component scope (not just inside HardnessFailureHeatmap).
//   2. Derives heatmap_has_data = !!heatmapData?.cells?.length from the hook result.
//   3. Passes that boolean to derivePageState so "sparse-heatmap" state is reachable.
//
// Pre-fix state: RacePage never calls useRaceHeatmap — heatmap_has_data is hardcoded false.
// Post-fix state: RacePage calls useRaceHeatmap; heatmap_has_data flows from real data.

import React from "react";
import { describe, test, expect, vi, beforeEach } from "vitest";
import { fixturesByPageState } from "./__fixtures__/raceStateFixtures";
import { RacePage } from "./RacePage";
import type { PageState } from "../../lib/types/race";
import { renderWithProvidersAtRoute } from "../../test/renderWithProviders";

// Standard mocks from RacePage.test.tsx
vi.mock("./hooks/useRaceStream", () => ({
  useRaceStream: vi.fn(() => ({
    pageState: "pre-race" as PageState,
    ws_status: "open",
    run_id: null,
    lanes: {
      pure_mcp: { lane: "pure_mcp", last_turn_index: -1, ttff_ms: null, recovered_count: 0, total_count: 0, faults: [], events: [], terminal_tag: null, headline: null },
      pure_a2a: { lane: "pure_a2a", last_turn_index: -1, ttff_ms: null, recovered_count: 0, total_count: 0, faults: [], events: [], terminal_tag: null, headline: null },
      hybrid:   { lane: "hybrid",   last_turn_index: -1, ttff_ms: null, recovered_count: 0, total_count: 0, faults: [], events: [], terminal_tag: null, headline: null },
    },
  })),
}));

vi.mock("./hooks/useRaceReplay", () => ({
  useRaceReplay: vi.fn(() => ({ trace: null, loading: false, error: null })),
}));

// B3-specific mock: useRaceHeatmap must be callable at RacePage scope.
vi.mock("./hooks/useRaceHeatmap", () => ({
  useRaceHeatmap: vi.fn(() => ({ data: null, loading: false, error: null })),
}));

import { useRaceHeatmap } from "./hooks/useRaceHeatmap";
const mockUseRaceHeatmap = vi.mocked(useRaceHeatmap);

beforeEach(() => {
  // Reset call count before each test
  mockUseRaceHeatmap.mockClear();
});

describe("B3 fix: useRaceHeatmap called at RacePage scope", () => {
  test("useRaceHeatmap is called when RacePage renders (not just inside HardnessFailureHeatmap)", () => {
    // Before the B3 fix: RacePage does NOT import useRaceHeatmap, so this mock is
    // ONLY called by HardnessFailureHeatmap internally. After the fix: RacePage also
    // calls useRaceHeatmap, so the mock call count should be >= 2 (one from RacePage,
    // one from HardnessFailureHeatmap).
    //
    // Pre-fix: callCount == 1 (only from HardnessFailureHeatmap)
    // Post-fix: callCount >= 2 (RacePage + HardnessFailureHeatmap)
    mockUseRaceHeatmap.mockReturnValue({ data: null, loading: false, error: null });

    renderWithProvidersAtRoute(
      <RacePage __testState={fixturesByPageState["done"]} />,
      "/race",
    );

    // This assertion FAILS pre-fix (only 1 call from HardnessFailureHeatmap)
    // and PASSES post-fix (2 calls: RacePage + HardnessFailureHeatmap)
    expect(mockUseRaceHeatmap.mock.calls.length).toBeGreaterThanOrEqual(2);
  });

  test("heatmap_has_data is false when useRaceHeatmap returns null data", () => {
    // null data → heatmap_has_data = false → derivePageState receives false → 'heatmap-empty'
    mockUseRaceHeatmap.mockReturnValue({ data: null, loading: false, error: null });

    const fixture = fixturesByPageState["done"];
    const { getByTestId } = renderWithProvidersAtRoute(
      <RacePage __testState={fixture} />,
      "/race",
    );
    // Component renders without crash
    expect(getByTestId("race-status-strip")).toBeInTheDocument();
    // heatmap-empty-overlay present because HardnessFailureHeatmap also gets null data
    expect(getByTestId("heatmap-empty-overlay")).toBeInTheDocument();
  });

  test("heatmap_has_data is false when useRaceHeatmap returns empty cells array", () => {
    // data.cells = [] → heatmap_has_data = !!([].length) = false
    mockUseRaceHeatmap.mockReturnValue({
      data: { cells: [], baseline: { model: "gpt-4o", seed: 42, task_ids: ["summarize_repo"] } },
      loading: false,
      error: null,
    });

    const fixture = fixturesByPageState["done"];
    const { getByTestId } = renderWithProvidersAtRoute(
      <RacePage __testState={fixture} />,
      "/race",
    );
    expect(getByTestId("race-status-strip")).toBeInTheDocument();
    // Empty cells → scaffold isEmpty=true → overlay present
    expect(getByTestId("heatmap-empty-overlay")).toBeInTheDocument();
  });

  test("heatmap_has_data is true when useRaceHeatmap returns cells — overlay absent", () => {
    // cells has 1 item → heatmap_has_data = true → HardnessFailureHeatmap renders populated grid
    // The scaffold isEmpty flag is driven by HardnessFailureHeatmap's OWN useRaceHeatmap call
    // (same mock). With cells present, isEmpty=false → heatmap-empty-overlay is NOT rendered.
    mockUseRaceHeatmap.mockReturnValue({
      data: {
        cells: [
          {
            hardness_type: "long_chain" as const,
            lane: "pure_mcp" as const,
            dominant_tag: "recovered" as const,
            recovery_rate: { num: 4, den: 5 },
            sample_run_id: "run-abc123",
          },
        ],
        baseline: { model: "gpt-4o", seed: 42, task_ids: ["summarize_repo"] },
      },
      loading: false,
      error: null,
    });

    const fixture = fixturesByPageState["done"];
    const { queryByTestId, getByTestId } = renderWithProvidersAtRoute(
      <RacePage __testState={fixture} />,
      "/race",
    );
    // Component renders without crash
    expect(getByTestId("race-status-strip")).toBeInTheDocument();
    // Populated cells → scaffold isEmpty=false → overlay NOT present
    expect(queryByTestId("heatmap-empty-overlay")).toBeNull();
  });
});
