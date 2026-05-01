import { CssBaseline, ThemeProvider } from "@mui/material";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { appTheme } from "../../../app/theme";
import { TraceExplorer } from "../TraceExplorer";
import type { TraceEvent } from "../../../lib/types/api";

// D-83 test pattern (from RaceLaneCard.test.tsx lines 8, 187)
vi.mock("@mui/material/useMediaQuery", () => ({ default: vi.fn() }));

async function setReducedMotion(value: boolean) {
  const mod = await import("@mui/material/useMediaQuery");
  (mod.default as ReturnType<typeof vi.fn>).mockReturnValue(value);
}

function renderExplorer(props: { events: TraceEvent[]; title?: string }) {
  return render(
    <ThemeProvider theme={appTheme}>
      <CssBaseline />
      <TraceExplorer {...props} />
    </ThemeProvider>,
  );
}

const events: TraceEvent[] = [
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
];

beforeEach(async () => {
  await setReducedMotion(false);
  // Mock scrollIntoView — jsdom does not implement it
  (
    Element.prototype as unknown as { scrollIntoView: () => void }
  ).scrollIntoView = vi.fn();
});

describe("TraceExplorer", () => {
  it("renders both List and Sequence ToggleButtons with List as default (D-81)", () => {
    renderExplorer({ events });
    // B-1 mitigation: MUI v5 ToggleButton uses role="button" + Mui-selected class
    const listBtn = screen.getByRole("button", { name: /^list$/i });
    const seqBtn = screen.getByRole("button", { name: /^sequence$/i });
    expect(listBtn.classList.contains("Mui-selected")).toBe(true);
    expect(seqBtn.classList.contains("Mui-selected")).toBe(false);
  });

  it("swaps to SequenceDiagramView when the Sequence toggle is clicked (D-81)", async () => {
    renderExplorer({ events });
    await userEvent.click(screen.getByRole("button", { name: /^sequence$/i }));
    // SequenceDiagramView renders 5 lane labels
    ["User", "Orchestrator", "LLM", "Tool", "Remote Agent"].forEach((L) => {
      expect(screen.getAllByText(L).length).toBeGreaterThan(0);
    });
  });

  it("calls scrollIntoView on the pinned row when toggled back to List (D-82)", async () => {
    renderExplorer({ events });
    // Switch to sequence view
    await userEvent.click(screen.getByRole("button", { name: /^sequence$/i }));
    // Click the first arrow in the SVG (aria-label contains "→")
    const arrows = screen
      .getAllByRole("button")
      .filter((b) => b.getAttribute("aria-label")?.includes("→"));
    await userEvent.click(arrows[0]);
    // Toggle back to list
    await userEvent.click(screen.getByRole("button", { name: /^list$/i }));
    await waitFor(() => {
      expect(
        (Element.prototype.scrollIntoView as ReturnType<typeof vi.fn>),
      ).toHaveBeenCalled();
    });
  });

  it("resets pin when events identity changes", async () => {
    const { rerender } = renderExplorer({ events });
    // Go to sequence and pin an event
    await userEvent.click(screen.getByRole("button", { name: /^sequence$/i }));
    const arrows = screen
      .getAllByRole("button")
      .filter((b) => b.getAttribute("aria-label")?.includes("→"));
    await userEvent.click(arrows[0]);
    // Re-render with a NEW events array reference (simulates new trace loaded)
    const newEvents: TraceEvent[] = [
      {
        index: 99,
        event_type: "user_input",
        timestamp_ms: 9,
        turn_index: 0,
      } as TraceEvent,
    ];
    (Element.prototype.scrollIntoView as ReturnType<typeof vi.fn>).mockClear?.();
    rerender(
      <ThemeProvider theme={appTheme}>
        <CssBaseline />
        <TraceExplorer events={newEvents} />
      </ThemeProvider>,
    );
    // Switch back to list — pin was cleared so scrollIntoView should NOT be called
    await userEvent.click(screen.getByRole("button", { name: /^list$/i }));
    // Give any RAF time to run
    await new Promise((resolve) => setTimeout(resolve, 50));
    expect(
      (Element.prototype.scrollIntoView as ReturnType<typeof vi.fn>),
    ).not.toHaveBeenCalled();
  });
});
