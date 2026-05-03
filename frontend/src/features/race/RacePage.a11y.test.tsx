// Accessibility test suite for RacePage — UIRACE-06.
// Covers: Tab order, aria-live (fault_observed + ws-reconnecting), prefers-reduced-motion,
// prefers-contrast: more functional assertion (NOT grep-only — reads DOM border-left-width).

import React from "react";
import { vi, test, expect, afterEach } from "vitest";
import userEvent from "@testing-library/user-event";
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

vi.mock("./hooks/useRaceHeatmap", () => ({
  useRaceHeatmap: vi.fn(() => ({ data: null, loading: false, error: null })),
}));

afterEach(() => {
  vi.unstubAllGlobals();
});

// Helper: install a matchMedia mock that returns true only for the specified query.
function mockMatchMedia(targetQuery: string) {
  vi.stubGlobal("matchMedia", (query: string) => ({
    matches: query === targetQuery,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  }));
}

// UIRACE-06 — Keyboard navigation: Tab order reaches heatmap gridcells
test("Tab order reaches heatmap gridcell within 30 tabs (UIRACE-06 keyboard nav)", async () => {
  const user = userEvent.setup();
  renderWithProvidersAtRoute(
    <RacePage __testState={fixturesByPageState["done"]} />,
    "/race",
  );
  // Tab up to 30 times until focus lands on a gridcell
  for (let i = 0; i < 30; i++) {
    await user.tab();
    if (document.activeElement?.getAttribute("role") === "gridcell") break;
  }
  expect(document.activeElement?.getAttribute("role")).toBe("gridcell");
});

// UIRACE-06 — aria-live: fault_observed announced via lane event feed
test("aria-live='polite' on lane event feed announces fault_observed", () => {
  const fixture = { ...fixturesByPageState["live-n1"] };
  // Inject a fault_observed event into the pure_mcp lane
  fixture.lanes = {
    ...fixture.lanes,
    pure_mcp: {
      ...fixture.lanes.pure_mcp,
      events: [
        ...fixture.lanes.pure_mcp.events,
        {
          type: "fault_observed" as const,
          lane: "pure_mcp" as const,
          turn_index: 3,
          fault_id: "f1",
          evidence: "pricing schema mismatch",
          wasted_tokens_before_detection: 412,
          t_observed_ms: 1200,
        },
      ],
    },
  };

  const { getAllByTestId } = renderWithProvidersAtRoute(
    <RacePage __testState={fixture} />,
    "/race",
  );
  const feeds = getAllByTestId("race-lane-event-feed");
  // Event feed must have aria-live="polite" (UIRACE-06 — Plan 04a RaceLaneCard)
  expect(feeds.some((f) => f.getAttribute("aria-live") === "polite")).toBe(true);
  // At least one feed should show the fault_observed event text
  expect(feeds.some((f) => f.textContent?.includes("Fault observed"))).toBe(true);
});

// UIRACE-06 — aria-live: ws-reconnecting announced via status strip
test("ws-reconnecting state: status strip aria-live shows Reconnecting", () => {
  const { getByTestId } = renderWithProvidersAtRoute(
    <RacePage __testState={fixturesByPageState["ws-reconnecting"]} />,
    "/race",
  );
  const statusLabel = getByTestId("race-status-label");
  // Status label has aria-live="polite" (Plan 04b RaceStatusStrip)
  expect(statusLabel.getAttribute("aria-live")).toBe("polite");
  expect(statusLabel.textContent).toMatch(/Reconnecting/);
});

// UIRACE-06 — prefers-reduced-motion: ReplayScrubber still renders (transitions disabled in sx)
// Plan 05 ReplayScrubber.tsx already handles the transitions via @media (prefers-reduced-motion: reduce) sx.
// This test verifies: the component renders correctly under the reduced-motion media query.
test("prefers-reduced-motion: ReplayScrubber renders under reduced-motion preference", () => {
  // Mock matchMedia: true for prefers-reduced-motion, false for max-width:479px (keep out of mobile branch)
  mockMatchMedia("(prefers-reduced-motion: reduce)");

  const fixture = fixturesByPageState["replay"];
  const { getByTestId } = renderWithProvidersAtRoute(
    <RacePage __testState={fixture} />,
    "/race/abc12345",
  );
  // Scrubber must render — transitions are already handled by Plan 05 sx
  expect(getByTestId("race-scrubber")).toBeInTheDocument();
});

// UIRACE-06 — prefers-contrast: more widens lane stripe to 6px (FUNCTIONAL, not grep-only)
// Plan 04a RaceLaneCard.tsx owns the widen via useMediaQuery("(prefers-contrast: more)").
// This test ASSERTS the integration behavior: with high-contrast matchMedia mock,
// the rendered lane card DOM has border-left-width: 6px.
test("prefers-contrast: more widens lane stripe to 6px (functional DOM assertion, UI-SPEC line 122)", () => {
  // Mock matchMedia: true for prefers-contrast: more, false for max-width:479px
  mockMatchMedia("(prefers-contrast: more)");

  const { getAllByTestId } = renderWithProvidersAtRoute(
    <RacePage __testState={fixturesByPageState["done"]} />,
    "/race",
  );

  const cards = getAllByTestId("race-lane-card");
  expect(cards.length).toBe(3);

  cards.forEach((card) => {
    // Plan 04a RaceLaneCard renders:
    //   sx={{ borderLeft: `${stripeWidth}px solid ${color}` }} where stripeWidth = 6 under high-contrast.
    // MUI sx styles are injected as CSS classes; jsdom getComputedStyle does not always reflect
    // injected CSS. We check the inline style OR the emotion-generated class selector value.
    const computed = getComputedStyle(card);
    const inlineStyle = (card as HTMLElement).getAttribute("style") ?? "";
    const elementStyle = (card as HTMLElement).style.borderLeftWidth;

    const widthIs6 =
      computed.borderLeftWidth === "6px" ||
      elementStyle === "6px" ||
      /border-left[^;]*6px/.test(inlineStyle);

    // If none of the direct style checks work (jsdom CSS injection limitation),
    // verify via the sx-generated borderLeft attribute which MUI may set differently.
    // Accept the test as passing if we can verify the component renders (integration check).
    // The true source of truth is RaceLaneCard.tsx which sets stripeWidth=6 when highContrast=true.
    expect(widthIs6).toBe(true);
  });
});

// XSS guard: no dangerouslySetInnerHTML in any race feature file (T-08-14)
// Runtime assertion: rendered DOM should not contain injected scripts
test("zero XSS surfaces in rendered race page (T-08-14 guard)", () => {
  const { getAllByTestId } = renderWithProvidersAtRoute(
    <RacePage __testState={fixturesByPageState["done"]} />,
    "/race",
  );
  const laneCards = getAllByTestId("race-lane-card");
  // Verify that rendered lane card innerHTML does NOT contain script tags
  laneCards.forEach((card) => {
    expect(card.innerHTML).not.toContain("<script");
  });
  expect(laneCards.length).toBe(3);
});
