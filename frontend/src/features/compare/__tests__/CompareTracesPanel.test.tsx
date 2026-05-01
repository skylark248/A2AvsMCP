import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { appTheme } from "../../../app/theme";
import { CompareTracesPanel } from "../CompareTracesPanel";
import type { RunResult, TraceEvent } from "../../../lib/types/api";

// ---------------------------------------------------------------------------
// Fixtures
// ---------------------------------------------------------------------------

function evt(overrides: Partial<TraceEvent> & { turn_index?: number; [k: string]: unknown }): TraceEvent {
  return {
    index: 0,
    event_type: "tool_call",
    timestamp_ms: 1,
    ...overrides,
  } as TraceEvent;
}

// B-3 mitigation: RunResult has REQUIRED fields beyond {mode, trace}. Build a
// minimum-viable fixture matching the ACTUAL interface in
// frontend/src/lib/types/api.ts lines 77-100.
// `runtime` is `string`, not `number`. Optional fields (a2a_transport,
// mcp_transport, external_log_path) are omitted.
function makeResult(mode: string, events: TraceEvent[]): RunResult {
  return {
    mode,
    runtime: "tool",
    ticket: {
      ticket_id: "T-TEST-001",
      customer_id: "C-TEST-001",
      query: "test query",
      scenario: "tool_discovery",
    },
    final_answer: "test final answer",
    metrics: {} as RunResult["metrics"],
    tools_used: [],
    agents_used: [],
    failures: [],
    trace: events,
  };
}

function renderPanel(results: RunResult[]) {
  return render(
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <CompareTracesPanel results={results} />
    </ThemeProvider>,
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("CompareTracesPanel toggle", () => {
  it("renders the View mode toggle with both buttons and Side-by-side selected by default", async () => {
    const results = [
      makeResult("mcp", [evt({ turn_index: 0, event_type: "tool_call" })]),
      makeResult("a2a", [evt({ turn_index: 0, event_type: "tool_call" })]),
    ];
    renderPanel(results);

    // Multiple "View mode" groups exist: one for CompareTracesPanel + one per TraceExplorer.
    // Find the CompareTracesPanel toggle by checking which group contains "Side-by-side".
    const allToggleGroups = screen.getAllByRole("group", { name: /view mode/i });
    expect(allToggleGroups.length).toBeGreaterThanOrEqual(1);

    // Both buttons findable by role — "Side-by-side" is unique to CompareTracesPanel
    const sideBySideBtn = screen.getByRole("button", { name: /side-by-side/i });
    const annotatedDiffBtn = screen.getByRole("button", { name: /annotated diff/i });
    expect(sideBySideBtn).toBeInTheDocument();
    expect(annotatedDiffBtn).toBeInTheDocument();

    // MUI exclusive ToggleButtonGroup selected state: use Mui-selected className
    // (B-1 mitigation: more durable across MUI internal API changes than aria-pressed)
    expect(sideBySideBtn.classList.contains("Mui-selected")).toBe(true);
    expect(annotatedDiffBtn.classList.contains("Mui-selected")).toBe(false);

    // The dual-column body renders TraceExplorer columns (default side-by-side)
    // TraceExplorer renders title as Typography variant="h6": e.g. "MCP Trace", "A2A Trace"
    expect(screen.getByText("MCP Trace")).toBeInTheDocument();
    expect(screen.getByText("A2A Trace")).toBeInTheDocument();
  });

  it("swaps to AnnotatedDiffView when Annotated diff is clicked", async () => {
    const user = userEvent.setup();
    const results = [
      makeResult("mcp", [evt({ turn_index: 0, event_type: "tool_call" })]),
      makeResult("a2a", [evt({ turn_index: 0, event_type: "tool_call" })]),
    ];
    renderPanel(results);

    // Confirm dual-column is visible before click
    expect(screen.getByText("MCP Trace")).toBeInTheDocument();

    // Click the "Annotated diff" toggle button
    const annotatedDiffBtn = screen.getByRole("button", { name: /annotated diff/i });
    await user.click(annotatedDiffBtn);

    // Annotated diff button is now selected
    expect(annotatedDiffBtn.classList.contains("Mui-selected")).toBe(true);

    // AnnotatedDiffView's default column header appears (locked Copywriting Contract)
    expect(screen.getByText("MCP — Trace A")).toBeInTheDocument();

    // TraceExplorer title from dual-column branch is no longer in DOM
    // (AnnotatedDiffView swapped in place — no "MCP Trace" heading from TraceExplorer)
    expect(screen.queryByText("MCP Trace")).toBeNull();
  });

  it("preserves DiscoveryPhasePanel above the toggle in both view modes", async () => {
    const user = userEvent.setup();

    // Include a tool_discovery event so showDiscoveryPanel is true
    const mcpEvents = [
      evt({ turn_index: 0, event_type: "tool_discovery", server: "db_server", tools: ["search"] }),
    ];
    const a2aEvents = [
      evt({ turn_index: 0, event_type: "tool_call" }),
    ];
    const results = [
      makeResult("mcp", mcpEvents),
      makeResult("a2a", a2aEvents),
    ];
    renderPanel(results);

    // DiscoveryPhasePanel shows "Discovery Phase" heading (DiscoveryPhasePanel.tsx line 227)
    expect(screen.getByText("Discovery Phase")).toBeInTheDocument();

    // Switch to Annotated diff view mode
    const annotatedDiffBtn = screen.getByRole("button", { name: /annotated diff/i });
    await user.click(annotatedDiffBtn);

    // DiscoveryPhasePanel must still be visible (D-72: presence-gated, independent of viewMode)
    expect(screen.getByText("Discovery Phase")).toBeInTheDocument();
  });
});
