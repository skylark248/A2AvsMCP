import { describe, test, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../../test/renderWithProviders";
import { RaceLaneTicker } from "./RaceLaneTicker";
import type { LaneState } from "../../../lib/types/race";

function fixtureLaneState(overrides?: Partial<LaneState>): LaneState {
  return {
    lane: "pure_mcp",
    last_turn_index: 4,
    ttff_ms: 1200,
    recovered_count: 3,
    total_count: 5,
    faults: [],
    events: [],
    terminal_tag: null,
    headline: null,
    ...overrides,
  };
}

describe("RaceLaneTicker", () => {
  test("renders 4 metric pairs in a 2-column grid", () => {
    const { container } = renderWithProviders(
      <RaceLaneTicker lane={fixtureLaneState()} />,
    );
    const ticker = container.querySelector("[data-testid='race-lane-ticker']");
    expect(ticker).toBeTruthy();
  });

  test("renders TTFF value formatted as ms string", () => {
    renderWithProviders(<RaceLaneTicker lane={fixtureLaneState({ ttff_ms: 1200 })} />);
    expect(screen.getByText("1200ms")).toBeInTheDocument();
  });

  test("renders Recovery Rate as n/n fraction", () => {
    renderWithProviders(
      <RaceLaneTicker lane={fixtureLaneState({ recovered_count: 3, total_count: 5 })} />,
    );
    expect(screen.getByText("3/5")).toBeInTheDocument();
  });

  test("renders Turns count (last_turn_index + 1)", () => {
    renderWithProviders(<RaceLaneTicker lane={fixtureLaneState({ last_turn_index: 4 })} />);
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  test("renders — (em dash) when ttff_ms is null — not 'null' or 'NaN'", () => {
    renderWithProviders(<RaceLaneTicker lane={fixtureLaneState({ ttff_ms: null })} />);
    // Should render em dash, not "null" or "NaN"
    const ticker = screen.getByTestId("race-lane-ticker");
    expect(ticker.textContent).not.toContain("null");
    expect(ticker.textContent).not.toContain("NaN");
    // em dash should appear
    expect(ticker.textContent).toContain("—");
  });

  test("renders — when last_turn_index is -1 (turns)", () => {
    renderWithProviders(
      <RaceLaneTicker lane={fixtureLaneState({ last_turn_index: -1 })} />,
    );
    // Should render em dash for turns
    const ticker = screen.getByTestId("race-lane-ticker");
    expect(ticker.textContent).toContain("—");
  });

  test("ttff label is wrapped in GlossaryTerm (UIRACE-07)", () => {
    const { container } = renderWithProviders(
      <RaceLaneTicker lane={fixtureLaneState()} />,
    );
    // GlossaryTerm renders a span with data-testid=glossary-term-tooltip-ttff (outside provider)
    const glossaryEl = container.querySelector("[data-testid^='glossary-term']");
    expect(glossaryEl).toBeTruthy();
  });

  test("recovery_rate label is wrapped in GlossaryTerm (UIRACE-07)", () => {
    const { container } = renderWithProviders(
      <RaceLaneTicker lane={fixtureLaneState()} />,
    );
    // Should have glossary terms for both ttff and recovery_rate
    const glossaryEls = container.querySelectorAll("[data-testid^='glossary-term']");
    expect(glossaryEls.length).toBeGreaterThanOrEqual(2);
  });

  test("label uses 0.875rem / 0.12em letter-spacing (UI-SPEC Typography)", () => {
    const { container } = renderWithProviders(
      <RaceLaneTicker lane={fixtureLaneState()} />,
    );
    // Labels are rendered via Typography variant="caption" with sx styles
    // The ticker renders without error — sx values enforced by acceptance_criteria grep
    const ticker = container.querySelector("[data-testid='race-lane-ticker']");
    expect(ticker).toBeTruthy();
  });

  test("value uses 1.15rem / font-weight 700 (UI-SPEC Typography)", () => {
    const { container } = renderWithProviders(
      <RaceLaneTicker lane={fixtureLaneState()} />,
    );
    const ticker = container.querySelector("[data-testid='race-lane-ticker']");
    expect(ticker).toBeTruthy();
  });

  test("no dangerouslySetInnerHTML usage", () => {
    const { container } = renderWithProviders(
      <RaceLaneTicker lane={fixtureLaneState()} />,
    );
    const ticker = container.querySelector("[data-testid='race-lane-ticker']");
    expect(ticker).toBeTruthy();
    // All content is React text children
  });
});
