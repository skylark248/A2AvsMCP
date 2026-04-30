/**
 * Plan 09-04 Task 2 RED: Tests for HardnessFailureHeatmap wrapper component.
 *
 * Coverage:
 *   1. Renders directional pill — "directional · n=3 tasks · v1" in MUI secondary.
 *   2. Delegates grid rendering to HeatmapScaffold (D-46 preserved).
 *   3. Renames backend "multi_source" → frontend "multi_source_synthesis" (LANDMINE 1).
 *   4. 5-pill legend strip ALWAYS visible — even when data is null (HEAT-02).
 *   5. Footer reads from API baseline payload (data-driven, HEAT-02 contract).
 *   6. Footer absent when data is null (no hardcoded fallback).
 *   7. recovery_rate fraction format ("12/15" from {num: 12, den: 15}).
 *   8. Empty cells {} pass-through preserves D-47 (scaffold's empty-state overlay).
 */
import { render, screen, within } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import { HardnessFailureHeatmap } from "./HardnessFailureHeatmap";
import type { HeatmapPayload } from "../../../lib/types/race";
import type { UseRaceHeatmapResult } from "../hooks/useRaceHeatmap";

// ---- Mock the data hook ----------------------------------------------------

let mockResult: UseRaceHeatmapResult;
vi.mock("../hooks/useRaceHeatmap", () => ({
  useRaceHeatmap: () => mockResult,
}));

const SAMPLE_PAYLOAD: HeatmapPayload = {
  cells: [
    {
      hardness_type: "long_chain",
      lane: "pure_mcp",
      dominant_tag: "recovered",
      recovery_rate: { num: 12, den: 15 },
      sample_run_id: "pure_mcp-summarize_repo-0-abc123",
    },
    {
      hardness_type: "multi_source", // backend short form — LANDMINE 1
      lane: "hybrid",
      dominant_tag: "gave_up",
      recovery_rate: { num: 3, den: 5 },
      sample_run_id: "hybrid-book_travel-0-def456",
    },
  ],
  baseline: {
    model: "claude-sonnet-4-6",
    seed: 42,
    task_ids: ["summarize_repo", "negotiate_meeting", "book_travel"],
  },
};

beforeEach(() => {
  mockResult = { data: null, loading: true, error: null };
});

// ---- Tests -----------------------------------------------------------------

describe("HardnessFailureHeatmap — directional pill (HEAT-01)", () => {
  it("renders the 'directional · n=3 tasks · v1' pill", () => {
    render(<HardnessFailureHeatmap />);
    expect(screen.getByText(/directional · n=3 tasks · v1/)).toBeInTheDocument();
  });
});

describe("HardnessFailureHeatmap — delegates grid to HeatmapScaffold (D-46)", () => {
  it("renders the scaffold's role=grid + role=gridcell DOM", () => {
    mockResult = { data: SAMPLE_PAYLOAD, loading: false, error: null };
    render(<HardnessFailureHeatmap />);

    // D-46: HeatmapScaffold rendering primitive must be reachable
    expect(screen.getByRole("grid")).toBeInTheDocument();
    expect(screen.getAllByRole("gridcell").length).toBeGreaterThan(0);
    // data-testid on the scaffold root (set by HeatmapScaffold)
    expect(screen.getByTestId("heatmap-scaffold")).toBeInTheDocument();
  });
});

describe("HardnessFailureHeatmap — multi_source rename (LANDMINE 1)", () => {
  it("maps backend 'multi_source' to frontend 'multi_source_synthesis' row", () => {
    mockResult = { data: SAMPLE_PAYLOAD, loading: false, error: null };
    render(<HardnessFailureHeatmap />);

    // The backend cell { hardness_type: "multi_source", lane: "hybrid", ... }
    // must render in the multi_source_synthesis × hybrid grid cell.
    // HeatmapScaffold tags cells with data-testid="heatmap-cell-{row}-{lane}".
    const cell = screen.getByTestId("heatmap-cell-multi_source_synthesis-hybrid");
    expect(cell).toBeInTheDocument();
    // The cell should have content (icon + recovery fraction)
    expect(within(cell).getByTestId("heatmap-cell-icon")).toBeInTheDocument();
    expect(within(cell).getByText("3/5")).toBeInTheDocument();
  });
});

describe("HardnessFailureHeatmap — 5-pill legend strip always visible (HEAT-02)", () => {
  it("renders 5 legend pills even when data is null (loading state)", () => {
    mockResult = { data: null, loading: true, error: null };
    render(<HardnessFailureHeatmap />);

    // failureTagColor has 5 entries; each must render as a Chip with its label.
    expect(screen.getByText("Recovered")).toBeInTheDocument();
    expect(screen.getByText("Gave Up")).toBeInTheDocument();
    expect(screen.getByText("Kept Going (Unaware)")).toBeInTheDocument();
    expect(screen.getByText("Kept Going to Failure")).toBeInTheDocument();
    expect(screen.getByText("Indeterminate")).toBeInTheDocument();
  });

  it("renders 5 legend pills when data is loaded", () => {
    mockResult = { data: SAMPLE_PAYLOAD, loading: false, error: null };
    render(<HardnessFailureHeatmap />);

    expect(screen.getByText("Recovered")).toBeInTheDocument();
    expect(screen.getByText("Gave Up")).toBeInTheDocument();
    expect(screen.getByText("Kept Going (Unaware)")).toBeInTheDocument();
    expect(screen.getByText("Kept Going to Failure")).toBeInTheDocument();
    expect(screen.getByText("Indeterminate")).toBeInTheDocument();
  });
});

describe("HardnessFailureHeatmap — footer (HEAT-02 data-driven contract)", () => {
  it("renders model · seed · task_ids from API baseline payload", () => {
    mockResult = { data: SAMPLE_PAYLOAD, loading: false, error: null };
    render(<HardnessFailureHeatmap />);

    const footer = screen.getByText(
      /claude-sonnet-4-6.*42.*summarize_repo.*negotiate_meeting.*book_travel/,
    );
    expect(footer).toBeInTheDocument();
  });

  it("does NOT render footer when data is null (no hardcoded fallback)", () => {
    mockResult = { data: null, loading: true, error: null };
    render(<HardnessFailureHeatmap />);

    // Footer reads data.baseline.model — should be absent during loading.
    expect(screen.queryByText(/claude-sonnet-4-6/)).not.toBeInTheDocument();
  });
});

describe("HardnessFailureHeatmap — recovery_rate fraction format", () => {
  it("formats {num: 12, den: 15} as '12/15' in the cell", () => {
    mockResult = { data: SAMPLE_PAYLOAD, loading: false, error: null };
    render(<HardnessFailureHeatmap />);

    const cell = screen.getByTestId("heatmap-cell-long_chain-pure_mcp");
    expect(within(cell).getByText("12/15")).toBeInTheDocument();
  });
});

describe("HardnessFailureHeatmap — empty-state passthrough (D-47 preserved)", () => {
  it("with cells: [] payload, scaffold renders empty-state overlay (scaffold stays mounted)", () => {
    mockResult = {
      data: {
        cells: [],
        baseline: {
          model: "claude-sonnet-4-6",
          seed: 42,
          task_ids: ["summarize_repo", "negotiate_meeting", "book_travel"],
        },
      },
      loading: false,
      error: null,
    };
    render(<HardnessFailureHeatmap />);

    // D-47: scaffold MUST stay mounted — grid still in DOM
    expect(screen.getByRole("grid")).toBeInTheDocument();
    expect(screen.getByTestId("heatmap-scaffold")).toBeInTheDocument();
    // Empty-state overlay surfaces (scaffold renders it when no cells populated)
    expect(screen.getByTestId("heatmap-empty-overlay")).toBeInTheDocument();
  });
});
