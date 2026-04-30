// Responsive test suite for RacePage — UIRACE-05 (4 breakpoints).
// Tests the viewport branching behavior: three-lane row vs mobile placeholder.

import React from "react";
import { vi, beforeAll, afterAll, test, expect } from "vitest";
import { fixturesByPageState } from "./__fixtures__/raceStateFixtures";
import { RacePage } from "./RacePage";
import { renderWithProvidersAtRoute } from "../../test/renderWithProviders";

// Mock hooks to prevent WebSocket connections in tests
vi.mock("./hooks/useRaceStream", () => ({
  useRaceStream: vi.fn(() => ({
    pageState: "pre-race" as const,
    ws_status: "open" as const,
    run_id: null,
    lanes: {
      pure_mcp: { lane: "pure_mcp" as const, last_turn_index: -1, ttff_ms: null, recovered_count: 0, total_count: 0, faults: [], events: [], terminal_tag: null, headline: null },
      pure_a2a: { lane: "pure_a2a" as const, last_turn_index: -1, ttff_ms: null, recovered_count: 0, total_count: 0, faults: [], events: [], terminal_tag: null, headline: null },
      hybrid:   { lane: "hybrid" as const,   last_turn_index: -1, ttff_ms: null, recovered_count: 0, total_count: 0, faults: [], events: [], terminal_tag: null, headline: null },
    },
  })),
}));

vi.mock("./hooks/useRaceReplay", () => ({
  useRaceReplay: vi.fn(() => ({ trace: null, loading: false, error: null })),
}));

// UIRACE-05 desktop, tablet, small-tablet: three-lane row visible
// __testState bypasses the isMobile branch (isMobile=false from jsdom default matchMedia).
test.each([
  { width: 1280, label: "desktop >=1200" },
  { width: 1024, label: "tablet 768-1199" },
  { width: 600, label: "small-tablet 480-767" },
])("$label viewport ($width) renders three-lane row (UIRACE-05)", ({ width }) => {
  vi.stubGlobal("innerWidth", width);
  window.dispatchEvent(new Event("resize"));
  // __testState provided: isMobile branch bypassed regardless of matchMedia result.
  // Lane row must always be present at non-mobile viewports.
  const { getByTestId } = renderWithProvidersAtRoute(
    <RacePage __testState={fixturesByPageState["done"]} />,
    "/race",
  );
  expect(getByTestId("race-lane-row")).toBeInTheDocument();
  vi.unstubAllGlobals();
});

// UIRACE-05 mobile <480: summary placeholder emitted when isMobile=true AND no __testState.
// Approach: mock window.matchMedia so useMediaQuery("(max-width:479px)") returns true.
// jsdom does not implement matchMedia; we install a deterministic mock.
test("mobile <480 renders summary placeholder marker (UIRACE-05 fallback shape)", () => {
  vi.stubGlobal("innerWidth", 400);

  // Install matchMedia mock: returns true for max-width:479px, false for all others.
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: query === "(max-width:479px)",
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));

  const { queryByTestId } = renderWithProvidersAtRoute(
    // No __testState — let the isMobile branch activate
    <RacePage />,
    "/race",
  );
  expect(queryByTestId("race-mobile-summary-placeholder")).toBeInTheDocument();
  expect(queryByTestId("race-lane-row")).toBeNull();

  vi.unstubAllGlobals();
});

// Phase 10 UIRACE-05 closure: live-mode (no run_id) on mobile suggests desktop;
// replay-mode (run_id present) renders <img src=/race/<run_id>/og.png>.
test("mobile live-mode (no run_id) shows desktop suggestion", () => {
  vi.stubGlobal("innerWidth", 400);
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: query === "(max-width:479px)",
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));

  const { getByTestId } = renderWithProvidersAtRoute(<RacePage />, "/race");
  const placeholder = getByTestId("race-mobile-summary-placeholder");
  expect(placeholder.textContent).toMatch(/Open on desktop/);

  vi.unstubAllGlobals();
});
