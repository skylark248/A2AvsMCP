/**
 * Task 2: TDD RED phase — RacePage shell mounts with section slot placeholders.
 * Tests: data-testid markers, live vs replay mode dispatch, scrubber slot gating.
 */
import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen } from "@testing-library/react";
import { MemoryRouter, Routes, Route } from "react-router-dom";

import { appTheme } from "../../app/theme";
import { AppUiProvider } from "../../app/ui/AppUiProvider";
import { RacePage } from "./RacePage";

function renderRacePage(initialEntry: string) {
  return render(
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <AppUiProvider>
        <MemoryRouter initialEntries={[initialEntry]}>
          <Routes>
            <Route path="/race" element={<RacePage />} />
            <Route path="/race/:run_id" element={<RacePage />} />
          </Routes>
        </MemoryRouter>
      </AppUiProvider>
    </ThemeProvider>,
  );
}

describe("RacePage shell — UIRACE-01 section hierarchy", () => {
  describe("live mode at /race (no run_id)", () => {
    it('renders data-testid="race-live-mode" at /race', () => {
      renderRacePage("/race");
      expect(screen.getByTestId("race-live-mode")).toBeInTheDocument();
    });

    it("renders status strip slot (race-status-strip)", () => {
      renderRacePage("/race");
      expect(screen.getByTestId("race-status-strip")).toBeInTheDocument();
    });

    it("renders lane row slot (race-lane-row)", () => {
      renderRacePage("/race");
      expect(screen.getByTestId("race-lane-row")).toBeInTheDocument();
    });

    it("renders banner slot (race-banner-slot)", () => {
      renderRacePage("/race");
      expect(screen.getByTestId("race-banner-slot")).toBeInTheDocument();
    });

    it("renders methodology slot (race-methodology-slot) as aside[role=complementary]", () => {
      renderRacePage("/race");
      const methodology = screen.getByTestId("race-methodology-slot");
      expect(methodology).toBeInTheDocument();
      expect(methodology.tagName.toLowerCase()).toBe("aside");
      expect(methodology).toHaveAttribute("role", "complementary");
    });

    it("renders heatmap slot (race-heatmap-slot)", () => {
      renderRacePage("/race");
      expect(screen.getByTestId("race-heatmap-slot")).toBeInTheDocument();
    });

    it("does NOT render scrubber slot in live mode (D-49)", () => {
      renderRacePage("/race");
      expect(screen.queryByTestId("race-scrubber-slot")).not.toBeInTheDocument();
    });
  });

  describe("replay mode at /race/:run_id", () => {
    it('renders data-testid="race-replay-mode" at /race/abc123', () => {
      renderRacePage("/race/abc123");
      expect(screen.getByTestId("race-replay-mode")).toBeInTheDocument();
    });

    it("renders scrubber slot in replay mode (D-49)", () => {
      renderRacePage("/race/abc123");
      expect(screen.getByTestId("race-scrubber-slot")).toBeInTheDocument();
    });

    it("renders all standard section slots in replay mode too", () => {
      renderRacePage("/race/abc123");
      expect(screen.getByTestId("race-status-strip")).toBeInTheDocument();
      expect(screen.getByTestId("race-lane-row")).toBeInTheDocument();
      expect(screen.getByTestId("race-banner-slot")).toBeInTheDocument();
      expect(screen.getByTestId("race-methodology-slot")).toBeInTheDocument();
      expect(screen.getByTestId("race-heatmap-slot")).toBeInTheDocument();
    });
  });
});
