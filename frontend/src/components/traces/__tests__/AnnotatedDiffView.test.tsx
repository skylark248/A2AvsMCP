import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { appTheme } from "../../../app/theme";
import { AnnotatedDiffView } from "../AnnotatedDiffView";
import type { TraceEvent } from "../../../lib/types/api";

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

function renderView(props: React.ComponentProps<typeof AnnotatedDiffView>) {
  return render(
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <AnnotatedDiffView {...props} />
    </ThemeProvider>,
  );
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("AnnotatedDiffView", () => {
  it("renders empty-state copy when both sides empty", () => {
    renderView({ leftEvents: [], rightEvents: [] });
    expect(screen.getByText("No events to compare")).toBeInTheDocument();
    expect(screen.getByText("Run both protocols to compare traces.")).toBeInTheDocument();
  });

  it("renders one row per DiffRow across all 4 statuses (D-76)", () => {
    // Build fixtures so alignTraces yields at minimum one of each status.
    // matched-equal: same turn_index + event_type + same non-trivial fields
    const matchedEqualL = evt({ turn_index: 0, event_type: "tool_call", tool: "search", protocol: "mcp" });
    const matchedEqualR = evt({ turn_index: 0, event_type: "tool_call", tool: "search", protocol: "mcp" });
    // matched-divergent (field): same turn_index + event_type, different tool
    const divergentL = evt({ turn_index: 1, event_type: "agent_msg", tool: "db_tool" });
    const divergentR = evt({ turn_index: 1, event_type: "agent_msg", tool: "docs_tool" });
    // removed: left-only event
    const removedL = evt({ turn_index: 2, event_type: "llm_call" });
    // added: right-only event
    const addedR = evt({ turn_index: 3, event_type: "a2a_message" });

    renderView({
      leftEvents: [matchedEqualL, divergentL, removedL],
      rightEvents: [matchedEqualR, divergentR, addedR],
    });

    const rowEls = document.querySelectorAll("[data-row-status]");
    const statuses = Array.from(rowEls).map((el) => el.getAttribute("data-row-status"));

    // Each DiffRow produces 2 data-row-status elements (left + right), so we check the set
    const statusSet = new Set(statuses);
    expect(statusSet.has("matched-equal")).toBe(true);
    expect(statusSet.has("matched-divergent")).toBe(true);
    expect(statusSet.has("removed")).toBe(true);
    expect(statusSet.has("added")).toBe(true);
  });

  it("shows '+' glyph on added rows", () => {
    // Right-only event → alignTraces produces 'added' DiffRow
    const addedR = evt({ turn_index: 0, event_type: "a2a_message" });
    renderView({ leftEvents: [], rightEvents: [addedR] });

    // The '+' chip should be in the DOM
    const plusChips = screen.getAllByText("+");
    expect(plusChips.length).toBeGreaterThanOrEqual(1);

    // AND a row container with data-row-status="added" should exist
    const addedRows = document.querySelectorAll("[data-row-status='added']");
    expect(addedRows.length).toBeGreaterThanOrEqual(1);
  });

  it("shows '−' glyph on removed rows", () => {
    // Left-only event → alignTraces produces 'removed' DiffRow
    const removedL = evt({ turn_index: 0, event_type: "tool_call", tool: "db" });
    renderView({ leftEvents: [removedL], rightEvents: [] });

    // The '−' minus-sign chip should be in the DOM
    const minusChips = screen.getAllByText("−");
    expect(minusChips.length).toBeGreaterThanOrEqual(1);

    const removedRows = document.querySelectorAll("[data-row-status='removed']");
    expect(removedRows.length).toBeGreaterThanOrEqual(1);
  });

  it("shows '≠' glyph and field tooltip on matched-divergent (cause=field) rows", () => {
    // Pair of events that differ only on tool → divergenceCause='field'
    const leftE = evt({ turn_index: 0, event_type: "tool_call", tool: "db_tool" });
    const rightE = evt({ turn_index: 0, event_type: "tool_call", tool: "docs_tool" });
    renderView({ leftEvents: [leftE], rightEvents: [rightE] });

    // '≠' glyph chip should be in the DOM
    const neqChips = screen.getAllByText("≠");
    expect(neqChips.length).toBeGreaterThanOrEqual(1);

    // Row container should have data-divergence-cause="field"
    const fieldRows = document.querySelectorAll("[data-divergence-cause='field']");
    expect(fieldRows.length).toBeGreaterThanOrEqual(1);

    // MUI Tooltip renders the title as aria-label on the child element (the Chip clone).
    // Use getByLabelText to find the element with this tooltip copy.
    const tooltipEl = screen.getByLabelText(
      "Same step, different details — fields differ between traces.",
    );
    expect(tooltipEl).toBeInTheDocument();
  });

  it("uses fault override copy on matched-divergent (cause=fault) rows", () => {
    // fault divergence via fault_ field prefix (alignTraces checks diffs.some(d => d.startsWith("fault_")))
    // Both have same (turn_index, event_type) so they match, but left has fault_observed=true
    // while right doesn't — divergenceCause='fault' per alignTraces contract
    const leftE = evt({ turn_index: 0, event_type: "tool_call", tool: "db_tool", fault_observed: true });
    const rightE = evt({ turn_index: 0, event_type: "tool_call", tool: "db_tool" });
    renderView({ leftEvents: [leftE], rightEvents: [rightE] });

    // Row should have data-divergence-cause="fault"
    const faultRows = document.querySelectorAll("[data-divergence-cause='fault']");
    expect(faultRows.length).toBeGreaterThanOrEqual(1);

    // MUI Tooltip renders the title as aria-label on the child element (the Chip clone).
    const tooltipEl = screen.getByLabelText(
      "Fault observed on one side only — one protocol noticed a failure the other didn't.",
    );
    expect(tooltipEl).toBeInTheDocument();
  });

  it("renders default protocol headers with chips showing event counts", () => {
    // Use distinct protocols so left=1 event, right=2 events (unique turn_index
    // to avoid alignment merging them into a single matched row)
    const leftEvt = evt({ turn_index: 99, event_type: "llm_call", protocol: "mcp" });
    const rightEvt1 = evt({ turn_index: 100, event_type: "a2a_message", protocol: "a2a" });
    const rightEvt2 = evt({ turn_index: 101, event_type: "agent_msg", protocol: "a2a" });

    renderView({ leftEvents: [leftEvt], rightEvents: [rightEvt1, rightEvt2] });

    // Column header labels (locked Copywriting Contract)
    expect(screen.getByText("MCP — Trace A")).toBeInTheDocument();
    expect(screen.getByText("A2A — Trace B")).toBeInTheDocument();

    // MUI Chip renders event counts as text spans.
    // Left side has 1 event, right side has 2. The header Chips show these counts.
    // Note: other "1" texts may appear in the row (turn indices etc) — use getAllByText
    // and assert the count is at least 1.
    expect(screen.getAllByText("1").length).toBeGreaterThanOrEqual(1);
    expect(screen.getAllByText("2").length).toBeGreaterThanOrEqual(1);
  });

  it("uses role-first label via traceLabel for row text", () => {
    // traceLabel returns `${event_type}:${message_type}` when message_type present,
    // else event_type. We use a predictable fixture.
    const leftE = evt({ turn_index: 0, event_type: "tool_call", message_type: "request" });
    const rightE = evt({ turn_index: 0, event_type: "tool_call", message_type: "request" });

    renderView({ leftEvents: [leftE], rightEvents: [rightE] });

    // traceLabel returns "tool_call:request" for this fixture
    const labelEls = screen.getAllByText((content) => content.includes("tool_call:request"));
    expect(labelEls.length).toBeGreaterThanOrEqual(1);
  });

  it("overrides column header labels when leftProtocolLabel and rightProtocolLabel are provided", () => {
    const leftE = evt({ turn_index: 0, event_type: "tool_call" });
    const rightE = evt({ turn_index: 0, event_type: "tool_call" });

    renderView({
      leftEvents: [leftE],
      rightEvents: [rightE],
      leftProtocolLabel: "Custom Left Label",
      rightProtocolLabel: "Custom Right Label",
    });

    expect(screen.getByText("Custom Left Label")).toBeInTheDocument();
    expect(screen.getByText("Custom Right Label")).toBeInTheDocument();
    // Default labels should NOT appear when overrides provided
    expect(screen.queryByText("MCP — Trace A")).toBeNull();
    expect(screen.queryByText("A2A — Trace B")).toBeNull();
  });
});
