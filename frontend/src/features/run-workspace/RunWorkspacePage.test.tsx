import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { appTheme } from "../../app/theme";
import { AppUiProvider } from "../../app/ui/AppUiProvider";
import { fetchRemoteA2aHealth, runDemo } from "../../lib/api/client";
import { RunWorkspacePage } from "./RunWorkspacePage";

const defaultRunResponse = vi.hoisted(() => ({
  results: [],
  report_name: null,
  summary: {
    report_name: "unsaved",
    scenario: "setup_error",
    title: "Setup Error Triage",
    runtime: "mock",
    generated_at: "2026-04-07T00:00:00Z",
    mode_count: 0,
    total_tool_calls: 0,
    total_a2a_messages: 0,
    total_failures: 0,
    talking_points: [],
    scorecard: {
      fastest_mode: "baseline",
      most_tool_heavy_mode: "mcp",
      most_collaborative_mode: "a2a",
      most_resilient_mode: "hybrid",
      recommended_demo_mode: "mcp",
      mode_scorecards: [],
      notes: [],
    },
  },
}));

vi.mock("../../lib/api/client", () => ({
  fetchRemoteMcpRegistry: vi.fn().mockResolvedValue({
    servers: [
      {
        id: "local_example",
        label: "Local example endpoints",
        db_url: "http://127.0.0.1:9001/mcp",
        docs_url: "http://127.0.0.1:9002/mcp",
        enabled: true,
      },
    ],
  }),
  fetchRemoteA2aRegistry: vi.fn().mockResolvedValue({
    agents: [
      { role: "customer_data", url: "http://127.0.0.1:9101", enabled: true },
      { role: "documentation", url: "http://127.0.0.1:9102", enabled: true },
      { role: "policy_billing", url: "http://127.0.0.1:9103", enabled: true },
    ],
  }),
  fetchRemoteA2aHealth: vi.fn().mockResolvedValue({ agents: [] }),
  fetchScenarios: vi.fn().mockResolvedValue([
    {
      key: "order_status",
      label: "Shipment Status Check",
      query: "Where is my order?",
      difficulty: "starter",
      tags: ["order"],
    },
    {
      key: "setup_error",
      label: "Setup Error Triage",
      query: "Setup is failing with error code X123.",
      difficulty: "starter",
      tags: ["docs"],
    },
  ]),
  runDemo: vi.fn().mockResolvedValue(defaultRunResponse),
}));

function renderRunWorkspace() {
  return render(
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <AppUiProvider>
        <MemoryRouter>
          <RunWorkspacePage />
        </MemoryRouter>
      </AppUiProvider>
    </ThemeProvider>,
  );
}

describe("RunWorkspacePage controls", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(runDemo).mockResolvedValue(defaultRunResponse);
    vi.mocked(fetchRemoteA2aHealth).mockResolvedValue({ agents: [] });
  });

  it("loads saved demo presets into the run payload", async () => {
    const user = userEvent.setup();
    renderRunWorkspace();

    await screen.findByText("Run Controls");
    await user.click(screen.getByLabelText("Demo Preset"));
    await user.click(screen.getByRole("option", { name: "MCP Transport Boundary" }));
    expect(await screen.findByText("A docs-heavy case through the MCP tool boundary.")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Run Demo" }));

    await waitFor(() => {
      expect(runDemo).toHaveBeenCalledWith(
        expect.objectContaining({
          profile: "demo",
          scenario: "setup_error",
          mode: "mcp",
          runtime: "mock",
          mcp_transport: "http",
          export_logs: true,
        }),
      );
    });
  });

  it("sets the run mode from the guided story controls", async () => {
    const user = userEvent.setup();
    renderRunWorkspace();

    await screen.findByText("Guided Story");
    await user.click(screen.getByRole("button", { name: "A2A" }));
    await user.click(screen.getByRole("button", { name: "Run Demo" }));

    await waitFor(() => {
      expect(runDemo).toHaveBeenCalledWith(expect.objectContaining({ mode: "a2a" }));
    });
  });

  it("fills remote A2A registry defaults and checks the configured endpoints", async () => {
    const user = userEvent.setup();
    renderRunWorkspace();

    await screen.findByText("Run Controls");
    await user.click(screen.getByLabelText("A2A Transport"));
    await user.click(screen.getByRole("option", { name: "Remote HTTP" }));

    expect(screen.getByLabelText("Remote Customer A2A URL")).toHaveValue("http://127.0.0.1:9101");
    expect(screen.getByLabelText("Remote Setup A2A URL")).toHaveValue("http://127.0.0.1:9102");
    expect(screen.getByLabelText("Remote Policy A2A URL")).toHaveValue("http://127.0.0.1:9103");

    await user.click(screen.getByRole("button", { name: "Check" }));

    await waitFor(() => {
      expect(fetchRemoteA2aHealth).toHaveBeenCalledWith({
        customer_url: "http://127.0.0.1:9101",
        documentation_url: "http://127.0.0.1:9102",
        policy_url: "http://127.0.0.1:9103",
      });
    });
  });

  it("shows backend error details from failed runs", async () => {
    const user = userEvent.setup();
    vi.mocked(runDemo).mockRejectedValueOnce(new Error("remote_a2a_customer_url points to an external host."));
    renderRunWorkspace();

    await screen.findByText("Run Controls");
    await user.click(screen.getByRole("button", { name: "Run Demo" }));

    expect(await screen.findByText("remote_a2a_customer_url points to an external host.")).toBeInTheDocument();
  });

  it("remote A2A failure toggles force the remote transport", async () => {
    const user = userEvent.setup();
    renderRunWorkspace();

    await screen.findByText("Run Controls");
    await user.click(screen.getByLabelText("Remote A2A bad auth"));
    await user.click(screen.getByRole("button", { name: "Run Demo" }));

    await waitFor(() => {
      expect(runDemo).toHaveBeenCalledWith(
        expect.objectContaining({ a2a_transport: "remote", remote_a2a_bad_auth: true }),
      );
    });
  });
});
