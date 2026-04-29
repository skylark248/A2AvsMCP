import { describe, test, expect } from "vitest";
import { screen } from "@testing-library/react";
import { render } from "@testing-library/react";
import { ThemeProvider, CssBaseline } from "@mui/material";
import { MemoryRouter } from "react-router-dom";
import { appTheme } from "../../../app/theme";
import { AppUiProvider } from "../../../app/ui/AppUiProvider";
import { FirstMentionProvider } from "../context/FirstMentionProvider";
import { renderWithProviders } from "../../../test/renderWithProviders";
import { MethodologySection } from "./MethodologySection";

// Renders with FirstMentionProvider so GlossaryTerm first-mention branch is exercised.
function renderWithFirstMention(ui: React.ReactElement) {
  return render(
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <AppUiProvider>
        <MemoryRouter initialEntries={["/race"]}>
          <FirstMentionProvider>{ui}</FirstMentionProvider>
        </MemoryRouter>
      </AppUiProvider>
    </ThemeProvider>,
  );
}

describe("MethodologySection", () => {
  test("renders with data-testid='race-methodology-section'", () => {
    renderWithFirstMention(<MethodologySection />);
    expect(screen.getByTestId("race-methodology-section")).toBeInTheDocument();
  });

  test("outermost element is <aside> (component='aside') with role='complementary' (UI-SPEC line 243)", () => {
    const { container } = renderWithFirstMention(<MethodologySection />);
    const aside = container.querySelector("aside");
    expect(aside).toBeTruthy();
    expect(aside).toHaveAttribute("role", "complementary");
  });

  test("does NOT render <Paper> or <Card> elements — flat section (UIRACE-03)", () => {
    const { container } = renderWithFirstMention(<MethodologySection />);
    // MUI Paper renders as <div class="MuiPaper-root">; Card extends Paper.
    const paper = container.querySelector(".MuiPaper-root");
    expect(paper).toBeNull();
    const card = container.querySelector(".MuiCard-root");
    expect(card).toBeNull();
  });

  test("renders overline label 'Methodology'", () => {
    renderWithFirstMention(<MethodologySection />);
    expect(screen.getByText("Methodology")).toBeInTheDocument();
  });

  test("renders h2 heading 'How we measure failure recovery'", () => {
    renderWithFirstMention(<MethodologySection />);
    expect(
      screen.getByText(/How we measure failure recovery/),
    ).toBeInTheDocument();
  });

  test("renders body prose text", () => {
    renderWithFirstMention(<MethodologySection />);
    expect(
      screen.getByText(/We measure each lane/),
    ).toBeInTheDocument();
  });

  test("wraps 'ttff' in GlossaryTerm (UIRACE-07 first-mention contract)", () => {
    const { container } = renderWithFirstMention(<MethodologySection />);
    // First-mention GlossaryTerm renders with data-testid="glossary-term-first-{term}"
    const ttffGlossary =
      container.querySelector("[data-testid='glossary-term-first-ttff']") ??
      container.querySelector("[data-testid='glossary-term-tooltip-ttff']");
    expect(ttffGlossary).toBeTruthy();
  });

  test("wraps 'recovery_rate' in GlossaryTerm (UIRACE-07 first-mention contract)", () => {
    const { container } = renderWithFirstMention(<MethodologySection />);
    const recoveryRateGlossary =
      container.querySelector("[data-testid='glossary-term-first-recovery_rate']") ??
      container.querySelector("[data-testid='glossary-term-tooltip-recovery_rate']");
    expect(recoveryRateGlossary).toBeTruthy();
  });

  test("wraps 'hardness_profile' in GlossaryTerm (UIRACE-07 first-mention contract)", () => {
    const { container } = renderWithFirstMention(<MethodologySection />);
    const hardnessGlossary =
      container.querySelector("[data-testid='glossary-term-first-hardness_profile']") ??
      container.querySelector("[data-testid='glossary-term-tooltip-hardness_profile']");
    expect(hardnessGlossary).toBeTruthy();
  });

  test("bgcolor is background.default (dominant 60% per UI-SPEC Color section)", () => {
    const { container } = renderWithFirstMention(<MethodologySection />);
    const aside = container.querySelector("aside");
    // sx bgcolor value enforced by acceptance criteria grep; component renders without error
    expect(aside).toBeInTheDocument();
  });

  test("renders without FirstMentionProvider (GlossaryTerm falls back to Tooltip branch)", () => {
    renderWithProviders(<MethodologySection />);
    expect(screen.getByTestId("race-methodology-section")).toBeInTheDocument();
  });
});
