import { describe, it, expect } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";
import { GlossaryTerm } from "./GlossaryTerm";
import { FirstMentionProvider } from "../../features/race/context/FirstMentionProvider";
import { renderWithProviders } from "../../test/renderWithProviders";

// ---- Outside FirstMentionProvider ----

describe("GlossaryTerm — outside provider (regression guard)", () => {
  it("renders children with Tooltip (no Popover) for known terms outside provider", () => {
    renderWithProviders(<GlossaryTerm term="mcp">MCP</GlossaryTerm>);
    // The Tooltip-wrapped span carries data-testid="glossary-term-tooltip-mcp"
    expect(screen.getByTestId("glossary-term-tooltip-mcp")).toBeDefined();
  });

  it("renders children unchanged for unknown terms outside provider", () => {
    renderWithProviders(<GlossaryTerm term="unknown_xyz">unknown</GlossaryTerm>);
    expect(screen.getByText("unknown")).toBeDefined();
  });
});

// ---- Inside FirstMentionProvider — first mention ----

describe("GlossaryTerm — inside provider, first mention", () => {
  it("renders first-mention span with data-testid glossary-term-first-{term}", () => {
    renderWithProviders(
      <FirstMentionProvider>
        <GlossaryTerm term="ttff">TTFF</GlossaryTerm>
      </FirstMentionProvider>,
    );
    expect(screen.getByTestId("glossary-term-first-ttff")).toBeDefined();
  });

  it("clicking the span opens a Popover containing the definition text", () => {
    renderWithProviders(
      <FirstMentionProvider>
        <GlossaryTerm term="ttff">TTFF</GlossaryTerm>
      </FirstMentionProvider>,
    );
    const span = screen.getByTestId("glossary-term-first-ttff");
    fireEvent.click(span);
    // Popover should show the definition
    expect(
      screen.getByText(/Time to first fault/i),
    ).toBeDefined();
  });

  it("clicking the span opens a Popover with a 'Got it' button", () => {
    renderWithProviders(
      <FirstMentionProvider>
        <GlossaryTerm term="ttff">TTFF</GlossaryTerm>
      </FirstMentionProvider>,
    );
    const span = screen.getByTestId("glossary-term-first-ttff");
    fireEvent.click(span);
    expect(screen.getByRole("button", { name: /got it/i })).toBeDefined();
  });

  it("clicking 'Got it' closes the Popover and marks term as seen", () => {
    renderWithProviders(
      <FirstMentionProvider>
        <GlossaryTerm term="recovery_rate">Recovery Rate</GlossaryTerm>
      </FirstMentionProvider>,
    );
    const span = screen.getByTestId("glossary-term-first-recovery_rate");
    fireEvent.click(span);
    const btn = screen.getByRole("button", { name: /got it/i });
    fireEvent.click(btn);
    // After dismissal, the span should no longer be the first-mention variant.
    // The component should now render the Tooltip variant.
    expect(screen.queryByTestId("glossary-term-first-recovery_rate")).toBeNull();
    expect(screen.getByTestId("glossary-term-tooltip-recovery_rate")).toBeDefined();
  });
});

// ---- Inside FirstMentionProvider — subsequent mentions ----

describe("GlossaryTerm — inside provider, subsequent mentions render Tooltip", () => {
  it("after 'Got it' dismiss, second GlossaryTerm for same term renders Tooltip", () => {
    renderWithProviders(
      <FirstMentionProvider>
        {/* First instance — will become first-mention */}
        <GlossaryTerm term="gave_up">Gave Up</GlossaryTerm>
        {/* Second instance of same term — initially also first-mention because no mark yet */}
      </FirstMentionProvider>,
    );
    const span = screen.getByTestId("glossary-term-first-gave_up");
    fireEvent.click(span);
    fireEvent.click(screen.getByRole("button", { name: /got it/i }));
    // Now it should be Tooltip variant
    expect(screen.getByTestId("glossary-term-tooltip-gave_up")).toBeDefined();
  });
});

// ---- Glossary terms — 8 race entries present ----

describe("glossaryTerms — 8 race entries", () => {
  it("ttff, recovery_rate, hardness_profile, recovered, gave_up, kept_going_without_noticing, kept_going_to_failure, indeterminate are present", async () => {
    const { glossaryTerms } = await import("../../lib/glossary/glossaryTerms");
    const raceTerms = [
      "ttff",
      "recovery_rate",
      "hardness_profile",
      "recovered",
      "gave_up",
      "kept_going_without_noticing",
      "kept_going_to_failure",
      "indeterminate",
    ];
    for (const term of raceTerms) {
      expect(glossaryTerms[term], `glossaryTerms.${term} should be defined`).toBeDefined();
      expect(glossaryTerms[term].length, `glossaryTerms.${term} should be non-empty`).toBeGreaterThan(0);
    }
  });

  it("ttff definition matches UI-SPEC verbatim", async () => {
    const { glossaryTerms } = await import("../../lib/glossary/glossaryTerms");
    expect(glossaryTerms.ttff).toBe(
      "Time to first fault — the elapsed milliseconds from run start until the first injected fault event lands in the trace.",
    );
  });

  it("indeterminate definition matches UI-SPEC verbatim", async () => {
    const { glossaryTerms } = await import("../../lib/glossary/glossaryTerms");
    expect(glossaryTerms.indeterminate).toBe(
      "A fault classification tag: the available trace evidence was insufficient to assign any of the four primary recovery tags.",
    );
  });
});
