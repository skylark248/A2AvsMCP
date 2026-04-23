import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RouterProvider, createMemoryRouter, useLocation } from "react-router-dom";
import { vi } from "vitest";

import { appTheme } from "../../app/theme";
import { AppUiProvider } from "../../app/ui/AppUiProvider";
import { ReportsPage } from "./ReportsPage";

vi.mock("../../lib/api/client", () => ({
  fetchReports: vi.fn().mockResolvedValue({
    reports: [
      {
        report_name: "report-1",
        scenario: "order_status",
        title: "Order Status Review",
        runtime: "mock",
        generated_at: "2026-04-06T00:00:00Z",
        mode_count: 4,
        total_tool_calls: 3,
        total_a2a_messages: 1,
        total_failures: 0,
        talking_points: [],
        scorecard: {
          fastest_mode: "baseline",
          most_tool_heavy_mode: "mcp",
          most_collaborative_mode: "a2a",
          most_resilient_mode: "hybrid",
          recommended_demo_mode: "hybrid",
          mode_scorecards: [],
          notes: [],
        },
      },
    ],
  }),
}));

function LocationProbe() {
  const location = useLocation();
  return <div data-testid="location-search">{location.search}</div>;
}

function renderReports(route: string) {
  const router = createMemoryRouter(
    [
      {
        path: "/reports",
        element: (
          <>
            <ReportsPage />
            <LocationProbe />
          </>
        ),
      },
    ],
    { initialEntries: [route] },
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

describe("ReportsPage", () => {
  it("hydrates filters from URL state and keeps them visible", async () => {
    renderReports("/reports?q=order&runtime=mock&recommended=hybrid&sort=tools");

    await waitFor(() => {
      expect(screen.getByText("Order Status Review")).toBeInTheDocument();
    });

    expect(screen.getByLabelText("Search reports")).toHaveValue("order");
    expect(screen.getByRole("combobox", { name: "Runtime" })).toHaveTextContent("mock");
    expect(screen.getByRole("combobox", { name: "Recommended" })).toHaveTextContent("HYBRID");
    expect(screen.getByRole("combobox", { name: "Sort by" })).toHaveTextContent("Tool calls");
  });

  it("updates the route search when filters change", async () => {
    const user = userEvent.setup();
    renderReports("/reports");

    await waitFor(() => {
      expect(screen.getByText("Order Status Review")).toBeInTheDocument();
    });

    const search = screen.getByLabelText("Search reports");
    await user.type(search, "hybrid");

    await waitFor(() => {
      expect(screen.getByTestId("location-search")).toHaveTextContent("q=hybrid");
    });
  });
});
