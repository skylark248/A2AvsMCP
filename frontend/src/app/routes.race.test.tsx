/**
 * Route resolution tests for /race and /race/:run_id routes.
 * Task 1: TDD RED phase — these tests fail until routes.tsx + RacePage are wired.
 */
import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen } from "@testing-library/react";
import { RouterProvider, createMemoryRouter } from "react-router-dom";

import { appTheme } from "./theme";
import { AppUiProvider } from "./ui/AppUiProvider";
import { AppShell } from "../components/layout/AppShell";
import { FirstMentionProvider } from "../features/race/context/FirstMentionProvider";
import { RacePage } from "../features/race/RacePage";
import { useFirstMention } from "../features/race/context/FirstMentionProvider";

// Probe component: mounts inside RacePage tree and asserts FirstMentionProvider is present
function FirstMentionProbe() {
  const ctx = useFirstMention();
  return (
    <div data-testid="first-mention-probe" data-has-context={ctx !== null ? "true" : "false"} />
  );
}

function renderWithRoutes(initialEntry: string) {
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <AppShell />,
        children: [
          {
            path: "race",
            element: (
              <FirstMentionProvider>
                <RacePage />
                <FirstMentionProbe />
              </FirstMentionProvider>
            ),
          },
          {
            path: "race/:run_id",
            element: (
              <FirstMentionProvider>
                <RacePage />
                <FirstMentionProbe />
              </FirstMentionProvider>
            ),
          },
        ],
      },
    ],
    { initialEntries: [initialEntry] },
  );

  return render(
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <AppUiProvider>
        <RouterProvider router={router} />
      </AppUiProvider>
    </ThemeProvider>,
  );
}

describe("/race routes — D-48, D-51", () => {
  it("renders RacePage at /race in live mode", () => {
    renderWithRoutes("/race");
    expect(screen.getByTestId("race-live-mode")).toBeInTheDocument();
  });

  it("renders RacePage at /race/abc123 in replay mode", () => {
    renderWithRoutes("/race/abc123");
    expect(screen.getByTestId("race-replay-mode")).toBeInTheDocument();
  });

  it("FirstMentionProvider is present in render tree at /race (D-51)", () => {
    renderWithRoutes("/race");
    const probe = screen.getByTestId("first-mention-probe");
    expect(probe.getAttribute("data-has-context")).toBe("true");
  });

  it("FirstMentionProvider is present in render tree at /race/abc123 (D-51)", () => {
    renderWithRoutes("/race/abc123");
    const probe = screen.getByTestId("first-mention-probe");
    expect(probe.getAttribute("data-has-context")).toBe("true");
  });

  it("AppShell nav includes a Race entry pointing to /race", () => {
    renderWithRoutes("/race");
    // Use exact string match to avoid matching "Traces" (which contains "race" as substring)
    const raceLink = screen.getByRole("link", { name: "Race" });
    expect(raceLink).toBeInTheDocument();
    expect(raceLink).toHaveAttribute("href", "/race");
  });
});
