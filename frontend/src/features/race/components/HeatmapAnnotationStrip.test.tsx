/**
 * Plan 10-03 Task 1 RED: Tests for HeatmapAnnotationStrip (OG-02).
 *
 * Coverage:
 *   1. Renders the literal string `{runId} · {model} · seed={seed} · n={n} · {task_ids}`.
 *   2. Carries data-testid="heatmap-annotation-strip" for OG-02 selector.
 *   3. task_ids are joined with ", ".
 */
import { render, screen } from "@testing-library/react";
import { describe, it, expect } from "vitest";

import { HeatmapAnnotationStrip } from "./HeatmapAnnotationStrip";
import type { HeatmapPayload } from "../../../lib/types/race";

const SAMPLE_BASELINE: HeatmapPayload["baseline"] = {
  model: "claude-sonnet-4-6",
  seed: 42,
  task_ids: ["summarize_repo", "negotiate_meeting", "book_travel"],
};

describe("HeatmapAnnotationStrip — OG-02 annotation contract", () => {
  it("renders {runId} · {model} · seed={seed} · n={n} · {task_ids}", () => {
    render(
      <HeatmapAnnotationStrip
        runId="run_abc123"
        baseline={SAMPLE_BASELINE}
        n={5}
      />,
    );

    const strip = screen.getByTestId("heatmap-annotation-strip");
    expect(strip).toBeInTheDocument();
    expect(strip.textContent).toContain("run_abc123");
    expect(strip.textContent).toContain("claude-sonnet-4-6");
    expect(strip.textContent).toContain("seed=42");
    expect(strip.textContent).toContain("n=5");
    expect(strip.textContent).toContain(
      "summarize_repo, negotiate_meeting, book_travel",
    );
    // Single-pass shape — middle dot separators
    expect(strip.textContent).toMatch(/run_abc123.*·.*claude-sonnet-4-6.*·.*seed=42.*·.*n=5.*·.*summarize_repo/);
  });

  it("renders with single task_id correctly", () => {
    render(
      <HeatmapAnnotationStrip
        runId="run_x"
        baseline={{ model: "gpt-4o", seed: 7, task_ids: ["task_a"] }}
        n={3}
      />,
    );
    const strip = screen.getByTestId("heatmap-annotation-strip");
    expect(strip.textContent).toContain("task_a");
    expect(strip.textContent).toContain("seed=7");
    expect(strip.textContent).toContain("n=3");
  });
});
