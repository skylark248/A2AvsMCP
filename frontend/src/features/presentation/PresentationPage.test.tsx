import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { appTheme } from "../../app/theme";
import { AppUiProvider } from "../../app/ui/AppUiProvider";
import { PresentationPage } from "./PresentationPage";

describe("PresentationPage", () => {
  it("supports presenter keyboard shortcuts for focus, navigation, copying, and demo layout", async () => {
    const user = userEvent.setup();
    const requestFullscreen = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(document.documentElement, "requestFullscreen", {
      value: requestFullscreen,
      configurable: true,
    });

    const writeText = vi.spyOn(navigator.clipboard, "writeText").mockResolvedValue(undefined);

    const router = createMemoryRouter(
      [
        { path: "/presentation", element: <PresentationPage /> },
        { path: "/trends", element: <div>Trends Destination</div> },
        { path: "/traces", element: <div>Traces Destination</div> },
        { path: "/reports", element: <div>Reports Destination</div> },
      ],
      { initialEntries: ["/presentation"] },
    );

    render(
      <ThemeProvider theme={appTheme}>
        <CssBaseline />
        <AppUiProvider>
          <RouterProvider router={router} />
        </AppUiProvider>
      </ThemeProvider>,
    );

    expect(screen.getByText("Focused preset: 1")).toBeInTheDocument();

    await user.keyboard("{ArrowRight}");
    expect(screen.getByText("Focused preset: 2")).toBeInTheDocument();

    await user.keyboard("c");
    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("/traces?mode=all"));
    expect(await screen.findByText("Copied preset link for Failure Resilience Demo.")).toBeInTheDocument();

    await user.keyboard("f");
    expect(requestFullscreen).toHaveBeenCalled();
    expect(await screen.findByRole("button", { name: "Exit live demo layout" })).toBeInTheDocument();

    await user.keyboard("{Enter}");
    expect(await screen.findByText("Traces Destination")).toBeInTheDocument();
  });
});
