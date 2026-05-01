import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { appTheme } from "../../../app/theme";
import { SequenceDiagramView } from "../SequenceDiagramView";
import type { TraceEvent } from "../../../lib/types/api";

// D-83 test pattern (from RaceLaneCard.test.tsx lines 8, 187)
vi.mock("@mui/material/useMediaQuery", () => ({ default: vi.fn() }));

async function setReducedMotion(value: boolean) {
  const mod = await import("@mui/material/useMediaQuery");
  (mod.default as ReturnType<typeof vi.fn>).mockReturnValue(value);
}

function renderView(props: Parameters<typeof SequenceDiagramView>[0]) {
  return render(
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <SequenceDiagramView {...props} />
    </ThemeProvider>,
  );
}

// Fixture events covering different lane types (D-80)
const sample: TraceEvent[] = [
  {
    index: 0,
    event_type: "user_input",
    timestamp_ms: 1,
    turn_index: 0,
  } as TraceEvent,
  {
    index: 1,
    event_type: "tool_call",
    timestamp_ms: 2,
    turn_index: 0,
    tool: "db_server",
  } as TraceEvent,
  {
    index: 2,
    event_type: "llm_request",
    timestamp_ms: 3,
    turn_index: 1,
  } as TraceEvent,
];

beforeEach(async () => {
  await setReducedMotion(false);
});

describe("SequenceDiagramView", () => {
  it("renders all 5 lifeline labels (D-80)", () => {
    renderView({ events: sample });
    ["User", "Orchestrator", "LLM", "Tool", "Remote Agent"].forEach((L) => {
      expect(screen.getAllByText(L).length).toBeGreaterThan(0);
    });
  });

  it("calls onPinEvent with String(event.index) when arrow clicked (D-82)", async () => {
    const onPin = vi.fn();
    renderView({ events: sample, onPinEvent: onPin });
    const arrows = screen.getAllByRole("button");
    await userEvent.click(arrows[0]);
    expect(onPin).toHaveBeenCalled();
    expect(typeof onPin.mock.calls[0][0]).toBe("string");
  });

  it("toggles pin off when the already-pinned arrow is clicked again (D-82)", async () => {
    const onPin = vi.fn();
    const { rerender } = renderView({
      events: sample,
      onPinEvent: onPin,
      pinnedEventId: null,
    });
    const firstArrow = screen.getAllByRole("button")[0];
    await userEvent.click(firstArrow);
    const pinnedId = onPin.mock.calls[0][0] as string;
    rerender(
      <ThemeProvider theme={appTheme}>
        <CssBaseline />
        <SequenceDiagramView
          events={sample}
          onPinEvent={onPin}
          pinnedEventId={pinnedId}
        />
      </ThemeProvider>,
    );
    await userEvent.click(screen.getAllByRole("button")[0]);
    expect(onPin).toHaveBeenLastCalledWith(null);
  });

  it("warns when an event has no mappable lane", () => {
    const warn = vi.spyOn(console, "warn").mockImplementation(() => {});
    // An event with event_type that doesn't start with any known prefix
    // and no tool/server/remote_agent — triggers the fallback null path
    const unmappable: TraceEvent[] = [
      {
        index: 0,
        event_type: "weird_unmapped_event_xyz",
        timestamp_ms: 1,
        turn_index: 0,
        // No tool, server, remote_agent, sender — actor will be "system"
        // system → "Orchestrator" so we need actor to be something not in any bucket
      } as TraceEvent,
    ];
    // Override agent to something unmapped so laneOf returns null
    const unmappableWithAgent: TraceEvent[] = [
      {
        index: 0,
        event_type: "weird_unmapped_event_xyz",
        timestamp_ms: 1,
        turn_index: 0,
        agent: "unknown_agent_xyz_not_mapped",
      } as TraceEvent,
    ];
    renderView({ events: unmappableWithAgent });
    // laneOf returns null for this event → console.warn should be called
    expect(warn).toHaveBeenCalled();
    warn.mockRestore();
  });

  it("renders no draw-in animation class under prefers-reduced-motion (D-83)", async () => {
    await setReducedMotion(true);
    const { container } = renderView({ events: sample });
    // When reduced motion is active, no element should have the seqdiag-draw-in class
    expect(container.querySelectorAll(".seqdiag-draw-in").length).toBe(0);
  });

  it("renders the empty-state copy when events is empty", () => {
    renderView({ events: [] });
    expect(screen.getByText("No events to diagram")).toBeInTheDocument();
    expect(
      screen.getByText("Run the scenario to populate the sequence diagram."),
    ).toBeInTheDocument();
  });
});
