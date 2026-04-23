import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { RouterProvider, createMemoryRouter } from "react-router-dom";
import { vi } from "vitest";

import { appTheme } from "./theme";
import { AppUiProvider } from "./ui/AppUiProvider";
import { AppShell } from "../components/layout/AppShell";
import { LearningPage } from "../features/learn/LearningPage";
import { PresentationPage } from "../features/presentation/PresentationPage";
import { ReportDetailPage } from "../features/reports/ReportDetailPage";
import { ReportsPage } from "../features/reports/ReportsPage";
import { RunWorkspacePage } from "../features/run-workspace/RunWorkspacePage";
import { TraceWorkspacePage } from "../features/traces/TraceWorkspacePage";
import { TelemetryPage } from "../features/telemetry/TelemetryPage";
import { TrendsPage } from "../features/trends/TrendsPage";
import { runDemo } from "../lib/api/client";

const fixtures = vi.hoisted(() => {
  const scorecard = {
    fastest_mode: "baseline",
    most_tool_heavy_mode: "mcp",
    most_collaborative_mode: "a2a",
    most_resilient_mode: "hybrid",
    recommended_demo_mode: "hybrid",
    mode_scorecards: [
      {
        mode: "hybrid",
        overall_score: 91,
        responsiveness_score: 76,
        tooling_score: 88,
        collaboration_score: 94,
        resilience_score: 90,
        presentation_score: 92,
        headline: "Best all-around demo mode.",
      },
    ],
    notes: ["Hybrid is the clearest combined protocol story."],
  };

  const summary = {
    report_name: "TICKET-1001_report.json",
    scenario: "order_status",
    title: "Shipment Status Check",
    runtime: "mock",
    generated_at: "2026-04-06T00:00:00Z",
    mode_count: 1,
    total_tool_calls: 2,
    total_a2a_messages: 4,
    total_failures: 0,
    talking_points: ["HYBRID is the recommended presentation mode."],
    scorecard,
  };

  const runResult = {
    mode: "hybrid",
    runtime: "mock",
    ticket: {
      ticket_id: "TICKET-1001",
      customer_id: "CUST-001",
      query: "Where is my order?",
      scenario: "order_status",
      title: "Shipment Status Check",
      difficulty: "standard",
      tags: ["shipping"],
    },
    final_answer: "Order ORD-1001 is in transit.",
    metrics: {
      mode: "hybrid",
      latency_ms: 42,
      tool_calls: 2,
      a2a_messages: 4,
      agents_involved: ["triage_agent", "documentation_agent"],
      complexity: "high",
      strengths: ["Clear separation"],
      weaknesses: ["More moving parts"],
      retries: 0,
      failures: 0,
    },
    tools_used: ["search_docs"],
    agents_used: ["triage_agent", "documentation_agent"],
    failures: [],
    external_log_path: null,
    trace: [
      { index: 1, event_type: "a2a_message", timestamp_ms: 1, message_type: "task_request" },
      { index: 2, event_type: "tool_call", timestamp_ms: 2, tool: "search_docs", transport: "http" },
    ],
  };

  return { scorecard, summary, runResult };
});

vi.mock("../lib/api/client", () => ({
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
  fetchScenarios: vi.fn().mockResolvedValue([
    {
      key: "order_status",
      label: "Shipment Status Check",
      query: "Where is my order?",
      difficulty: "standard",
      tags: ["shipping"],
    },
  ]),
  runDemo: vi.fn().mockResolvedValue({
    results: [fixtures.runResult],
    report_name: "TICKET-1001_report.json",
    summary: fixtures.summary,
  }),
  fetchReports: vi.fn().mockResolvedValue({ reports: [fixtures.summary] }),
  fetchReportDetail: vi.fn().mockResolvedValue({
    report_name: "TICKET-1001_report.json",
    summary: fixtures.summary,
    results: [fixtures.runResult],
    export_url: "/reports/TICKET-1001_report.json/export",
    pdf_export_url: "/reports/TICKET-1001_report.json/export.pdf",
    evidence_export_url: "/reports/TICKET-1001_report.json/evidence.zip",
    sorting: {
      score_sort: "overall",
      score_dir: "desc",
      result_sort: "latency",
      result_dir: "asc",
    },
  }),
  fetchTelemetry: vi.fn().mockResolvedValue({
    total_runs: 12,
    total_reports: 4,
    total_failures: 1,
    avg_latency_ms: 19.5,
    tool_calls: 33,
    a2a_messages: 44,
    users: ["default", "alice"],
    mode_counts: { baseline: 3, mcp: 3, a2a: 3, hybrid: 3 },
  }),
  fetchTrends: vi.fn().mockResolvedValue({
    trends: {
      total_reports: 1,
      scenario_counts: [{ scenario: "order_status", count: 1 }],
      runtime_counts: { mock: 1 },
      recommended_mode_counts: [{ mode: "hybrid", count: 1 }],
      average_totals: { tool_calls: 2, a2a_messages: 4, failures: 0 },
      mode_trends: [
        {
          mode: "hybrid",
          appearances: 1,
          recommended_count: 1,
          avg_overall_score: 91,
          avg_presentation_score: 92,
          avg_resilience_score: 90,
          avg_latency_ms: 42,
          avg_tool_calls: 2,
          avg_a2a_messages: 4,
        },
      ],
      recent_reports: [fixtures.summary],
      narrative: ["HYBRID has been strongest across saved reports."],
      available_filters: { scenarios: ["order_status"], runtimes: ["mock"], recommended_modes: ["hybrid"] },
      applied_filters: { scenario: "", runtime: "", recommended_mode: "" },
    },
  }),
}));

function renderApp(initialEntry = "/") {
  const router = createMemoryRouter(
    [
      {
        path: "/",
        element: <AppShell />,
        children: [
          { index: true, element: <RunWorkspacePage /> },
          { path: "learn", element: <LearningPage /> },
          { path: "reports", element: <ReportsPage /> },
          { path: "reports/:reportName", element: <ReportDetailPage /> },
          { path: "traces", element: <TraceWorkspacePage /> },
          { path: "trends", element: <TrendsPage /> },
          { path: "presentation", element: <PresentationPage /> },
          { path: "telemetry", element: <TelemetryPage /> },
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

describe("primary React app routes", () => {
  it("runs a demo and navigates from reports to report detail", async () => {
    const user = userEvent.setup();
    renderApp("/");

    expect(await screen.findByText(/Compare baseline, MCP, A2A, and hybrid flows/i)).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /Run Demo/i }));

    expect(await screen.findByText(/HYBRID is currently the recommended presentation mode/i)).toBeInTheDocument();
    expect(runDemo).toHaveBeenCalledWith(expect.objectContaining({ scenario: "order_status", mode: "all" }));

    await user.click(screen.getByRole("link", { name: /Reports/i }));
    expect(await screen.findByText("Saved runs are now a first-class workflow.")).toBeInTheDocument();
    expect(screen.getByText("Shipment Status Check")).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /Open report detail/i }));
    expect(await screen.findByText("Report Detail")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Open HTML Export/i })).toHaveAttribute(
      "href",
      "/reports/TICKET-1001_report.json/export",
    );
    expect(screen.getByRole("link", { name: /Download Evidence Bundle/i })).toHaveAttribute(
      "href",
      "/reports/TICKET-1001_report.json/evidence.zip",
    );
  });

  it("teaches the protocol difference in the learning workspace", async () => {
    const user = userEvent.setup();
    vi.mocked(runDemo).mockClear();
    renderApp("/learn");

    expect(await screen.findByText(/MCP answers tool access\. A2A answers agent collaboration\./i)).toBeInTheDocument();
    expect(screen.getAllByText(/official MCP SDK servers and clients/i).length).toBeGreaterThan(0);
    expect(screen.getAllByText(/educational A2A-style broker/i).length).toBeGreaterThan(0);

    await user.click(screen.getByRole("button", { name: /Study MCP/i }));
    await user.click(screen.getByRole("button", { name: /Run MCP lesson/i }));

    expect(runDemo).toHaveBeenCalledWith(
      expect.objectContaining({ mode: "mcp", mcp_transport: "http", save_report: false }),
    );
    expect(await screen.findByText(/Order ORD-1001 is in transit/i)).toBeInTheDocument();
  });

  it("loads trend and trace workspaces from saved report data", async () => {
    const user = userEvent.setup();
    renderApp("/trends");

    expect(await screen.findByText(/Cross-run analytics/i)).toBeInTheDocument();
    expect(screen.getByText("Saved Reports")).toBeInTheDocument();
    expect(screen.getByText(/HYBRID has been strongest/i)).toBeInTheDocument();

    await user.click(screen.getByRole("link", { name: /Traces/i }));
    expect(await screen.findByText(/Compare protocol behavior across modes/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/HYBRID: 2 total events, 1 tool calls, 1 A2A messages/i)).toBeInTheDocument();
    });

    await user.click(screen.getByRole("link", { name: /Telemetry/i }));
    expect(await screen.findByText(/Platform activity is visible/i)).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
    expect(screen.getByText("default")).toBeInTheDocument();
  });
});
