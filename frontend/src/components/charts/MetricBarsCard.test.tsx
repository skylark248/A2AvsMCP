import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { vi } from "vitest";

import { MetricBarsCard } from "./MetricBarsCard";
import { renderWithProviders } from "../../test/renderWithProviders";

describe("MetricBarsCard", () => {
  it("copies a chart link and shows a shared toast", async () => {
    const user = userEvent.setup();
    const writeText = vi.spyOn(navigator.clipboard, "writeText").mockResolvedValue(undefined);

    renderWithProviders(
      <MetricBarsCard
        title="Average Overall Mode Score"
        items={[{ label: "HYBRID", value: 92, displayValue: "92/100" }]}
      />,
      "/trends",
    );

    await user.click(screen.getByRole("button", { name: "Share" }));

    expect(writeText).toHaveBeenCalledWith(expect.stringContaining("#average-overall-mode-score"));
    expect(await screen.findByText("Chart link copied to clipboard.")).toBeInTheDocument();
  });

  it("downloads an SVG snapshot and shows a toast", async () => {
    const user = userEvent.setup();
    const createObjectUrl = vi.spyOn(URL, "createObjectURL");
    const revokeObjectUrl = vi.spyOn(URL, "revokeObjectURL");
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {});

    renderWithProviders(
      <MetricBarsCard title="Latency Advantage" items={[{ label: "MCP", value: 120, displayValue: "120 ms" }]} />,
      "/trends",
    );

    await user.click(screen.getByRole("button", { name: "Snapshot" }));

    expect(createObjectUrl).toHaveBeenCalled();
    expect(clickSpy).toHaveBeenCalled();
    expect(revokeObjectUrl).toHaveBeenCalled();
    expect(await screen.findByText("SVG snapshot downloaded.")).toBeInTheDocument();
  });
});
