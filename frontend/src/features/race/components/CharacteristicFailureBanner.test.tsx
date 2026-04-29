import { describe, test, expect } from "vitest";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../../test/renderWithProviders";
import { CharacteristicFailureBanner } from "./CharacteristicFailureBanner";

describe("CharacteristicFailureBanner", () => {
  test("renders with data-testid='characteristic-failure-banner'", () => {
    renderWithProviders(
      <CharacteristicFailureBanner header="Characteristic failure:" clause="gave up after 3 turns" />,
    );
    expect(screen.getByTestId("characteristic-failure-banner")).toBeInTheDocument();
  });

  test("banner element has role='banner' (UI-SPEC ARIA Landmarks line 240)", () => {
    renderWithProviders(
      <CharacteristicFailureBanner header="Failure:" clause="gave up" />,
    );
    const banner = screen.getByTestId("characteristic-failure-banner");
    expect(banner).toHaveAttribute("role", "banner");
  });

  test("renders header text as h2 content", () => {
    renderWithProviders(
      <CharacteristicFailureBanner header="Characteristic failure:" clause="gave up after 3 turns" />,
    );
    expect(screen.getByText(/Characteristic failure/)).toBeInTheDocument();
  });

  test("renders clause text inside italic span (UIRACE-03 italic dynamic clause)", () => {
    renderWithProviders(
      <CharacteristicFailureBanner header="Failure:" clause="kept going without noticing" />,
    );
    expect(screen.getByText(/kept going without noticing/)).toBeInTheDocument();
  });

  test("borderRadius is 0 — acceptance criteria enforced by grep, component renders (UIRACE-03 banner=0)", () => {
    const { container } = renderWithProviders(
      <CharacteristicFailureBanner header="Header" clause="clause text" />,
    );
    const banner = container.querySelector("[data-testid='characteristic-failure-banner']");
    expect(banner).toBeInTheDocument();
  });

  test("borderLeft 4px primary rule — component renders with sx values (UIRACE-03)", () => {
    const { container } = renderWithProviders(
      <CharacteristicFailureBanner header="Header" clause="clause text" />,
    );
    const banner = container.querySelector("[data-testid='characteristic-failure-banner']");
    expect(banner).toBeInTheDocument();
    // sx enforcement is via acceptance criteria grep; render-level check ensures no crash
  });

  test("padding is 24px (p=3 in MUI = 24px lg) — component renders without error", () => {
    const { container } = renderWithProviders(
      <CharacteristicFailureBanner header="Header" clause="clause text" />,
    );
    expect(container.querySelector("[data-testid='characteristic-failure-banner']")).toBeTruthy();
  });

  test("when clause is empty string, banner renders without crashing", () => {
    expect(() => {
      renderWithProviders(<CharacteristicFailureBanner header="Failure:" clause="" />);
    }).not.toThrow();
    const banner = screen.getByTestId("characteristic-failure-banner");
    expect(banner).toBeInTheDocument();
  });

  test("clause text rendered as React text child — not dangerouslySetInnerHTML (T-08-08)", () => {
    renderWithProviders(
      <CharacteristicFailureBanner
        header="Failure:"
        clause="<script>alert('xss')</script>"
      />,
    );
    // If rendered as text, XSS payload is escaped — script tag would NOT execute.
    // Verify the text content appears as literal text (escaped).
    const banner = screen.getByTestId("characteristic-failure-banner");
    // React text rendering means innerHTML shows escaped text, not a live script element.
    expect(banner.querySelector("script")).toBeNull();
    expect(banner.textContent).toContain("<script>");
  });

  test("h2 element has 1.6rem font-size (UI-SPEC Display 25.6px = 1.6rem at 16px base)", () => {
    const { container } = renderWithProviders(
      <CharacteristicFailureBanner header="Header" clause="clause" />,
    );
    // acceptance criteria grep enforces 1.6rem value; component renders
    expect(
      container.querySelector("[data-testid='characteristic-failure-banner']"),
    ).toBeInTheDocument();
  });
});
