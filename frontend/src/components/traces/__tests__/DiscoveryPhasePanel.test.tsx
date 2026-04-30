import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { appTheme } from "../../../app/theme";
import { DiscoveryPhasePanel } from "../DiscoveryPhasePanel";
import type { DiscoveryPhasePanelProps } from "../DiscoveryPhasePanel";
import type { TraceEvent } from "../../../lib/types/api";

function renderPanel(props: DiscoveryPhasePanelProps) {
  return render(
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <DiscoveryPhasePanel {...props} />
    </ThemeProvider>,
  );
}

const mcpDiscoveryEvent: TraceEvent = {
  index: 1,
  event_type: "tool_discovery",
  timestamp_ms: 0,
  // Open-ended fields per TraceEvent index signature:
  server: "a2a_vs_mcp.mcp_servers.db_server",
  tools: ["get_order_history", "get_warranty"],
  protocol: "official_mcp_sdk",
  transport: "in_process",
  requested_transport: "in_process",
} as unknown as TraceEvent;

const a2aDiscoveryEvent: TraceEvent = {
  index: 2,
  event_type: "tool_discovery",
  timestamp_ms: 5,
  server: "remote://documentation",
  tools: ["search_docs"],
  protocol: "official_mcp_sdk",
  transport: "in_process",
  requested_transport: "in_process",
  remote_agent: "documentation",
  remote_trace: true,
} as unknown as TraceEvent;

describe("DiscoveryPhasePanel", () => {
  it("renders panel chrome and both column headers when MCP events are present", () => {
    renderPanel({
      mcpEvents: [mcpDiscoveryEvent],
      a2aEvents: [],
      scenario: "tool_discovery",
    });
    expect(screen.getByText("Discovery Phase")).toBeInTheDocument();
    expect(screen.getByText("MCP — Tool Catalog")).toBeInTheDocument();
    expect(screen.getByText("A2A — Agent Cards")).toBeInTheDocument();
    expect(screen.getByText("Run on A2A to populate")).toBeInTheDocument();
  });

  it("renders 'Run on A2A to populate' placeholder when only MCP events present (D-71)", () => {
    renderPanel({
      mcpEvents: [mcpDiscoveryEvent],
      a2aEvents: [],
      scenario: "tool_discovery",
    });
    expect(screen.getByText("Run on A2A to populate")).toBeInTheDocument();
    expect(screen.queryByText("Run on MCP to populate")).toBeNull();
  });

  it("renders 'Run on MCP to populate' placeholder when only A2A events present (D-71)", () => {
    renderPanel({
      mcpEvents: [],
      a2aEvents: [a2aDiscoveryEvent],
      scenario: "tool_discovery",
    });
    expect(screen.getByText("Run on MCP to populate")).toBeInTheDocument();
    expect(screen.queryByText("Run on A2A to populate")).toBeNull();
  });

  it("highlights stale-cache fallback when requested_transport !== transport (RESEARCH Pitfall #3)", () => {
    const fallbackEvent: TraceEvent = {
      ...mcpDiscoveryEvent,
      requested_transport: "stdio",
      transport: "in_process",
    } as unknown as TraceEvent;
    renderPanel({
      mcpEvents: [fallbackEvent],
      a2aEvents: [],
      scenario: "tool_discovery",
    });
    // The WarningAmberRoundedIcon carries aria-label="Stale capability cache" per the
    // component contract; the surrounding Tooltip's title is the long-form copy. The
    // fixture event has two tools — both cards render the warning icon (one per tool),
    // so we assert at least one matching node via getAllByLabelText.
    const warnings = screen.getAllByLabelText(/Stale capability cache/i);
    expect(warnings.length).toBeGreaterThanOrEqual(1);
    expect(warnings[0]).toBeInTheDocument();
  });

  it("renders A2A agent-card skill chips when a2a_remote_discovery event is present (RESEARCH Open Question #1 RESOLVED)", () => {
    const a2aRemoteDiscoveryEvent: TraceEvent = {
      index: 3,
      event_type: "a2a_remote_discovery",
      timestamp_ms: 7,
      remote_agent: "documentation",
      a2a_agent_card: {
        agent_id: "documentation",
        skills: ["lookup_warranty", "check_order"],
      },
    } as unknown as TraceEvent;
    renderPanel({
      mcpEvents: [],
      // Caller (Plan 11-04) passes BOTH event types in a2aEvents — the panel joins
      // them by remote_agent === a2a_agent_card.agent_id and renders skills as Chips.
      a2aEvents: [a2aDiscoveryEvent, a2aRemoteDiscoveryEvent],
      scenario: "tool_discovery",
    });
    expect(screen.getByText("lookup_warranty")).toBeInTheDocument();
    expect(screen.getByText("check_order")).toBeInTheDocument();
  });
});
