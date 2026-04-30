/**
 * Plan 09-04 Task 1 RED: Tests for useRaceHeatmap hook.
 *
 * Mirrors useRaceReplay.test.ts patterns: vi.stubGlobal('fetch', mockFetch) +
 * renderHook + waitFor. The hook follows the let-active-true cleanup pattern
 * from useRaceReplay verbatim (Pattern 4).
 *
 * Behavior pinned:
 *   1. Initial loading state — {data: null, loading: true, error: null} before fetch resolves.
 *   2. Happy fetch — {data: payload, loading: false, error: null} after fetch resolves.
 *   3. Error path — {data: null, loading: false, error: message} on fetch reject.
 *   4. Cleanup on unmount — unmounting before fetch resolves does not warn.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";

import { useRaceHeatmap } from "./useRaceHeatmap";
import type { HeatmapPayload } from "../../../lib/types/race";

// ---- Helpers ---------------------------------------------------------------

function makeMockFetch(payload: unknown, ok = true, status = 200) {
  return vi.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(payload),
    text: () => Promise.resolve(JSON.stringify(payload)),
  });
}

const SAMPLE_PAYLOAD: HeatmapPayload = {
  cells: [
    {
      hardness_type: "long_chain",
      lane: "pure_mcp",
      dominant_tag: "recovered",
      recovery_rate: { num: 12, den: 15 },
      sample_run_id: "pure_mcp-summarize_repo-0-abc123",
    },
  ],
  baseline: {
    model: "claude-sonnet-4-6",
    seed: 42,
    task_ids: ["summarize_repo", "negotiate_meeting", "book_travel"],
  },
};

// ---- Setup / Teardown ------------------------------------------------------

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---- Tests -----------------------------------------------------------------

describe("useRaceHeatmap — fetch lifecycle", () => {
  it("starts in loading=true (initial state) before fetch resolves", () => {
    // Make fetch never resolve during this test
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));
    const { result } = renderHook(() => useRaceHeatmap());

    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it("on fetch success: data populated, loading false, error null", async () => {
    vi.stubGlobal("fetch", makeMockFetch(SAMPLE_PAYLOAD));
    const { result } = renderHook(() => useRaceHeatmap());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toEqual(SAMPLE_PAYLOAD);
    expect(result.current.error).toBeNull();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/race/heatmap"));
  });

  it("on fetch error: data null, loading false, error message set", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("Network error")),
    );
    const { result } = renderHook(() => useRaceHeatmap());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.data).toBeNull();
    expect(result.current.error).toBeTruthy();
    expect(result.current.error).toContain("Network error");
  });
});

describe("useRaceHeatmap — cleanup discipline (Pattern 4: let active = true)", () => {
  it("unmounting before fetch resolves does not warn about setState on unmounted component", async () => {
    // fetch resolves AFTER we unmount — guard prevents stale setState writes
    let resolveFetch: ((value: unknown) => void) | null = null;
    const pending = new Promise((resolve) => {
      resolveFetch = resolve;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn().mockReturnValue(
        pending.then(() => ({
          ok: true,
          status: 200,
          json: () => Promise.resolve(SAMPLE_PAYLOAD),
        })),
      ),
    );

    const warnSpy = vi.spyOn(console, "error").mockImplementation(() => {});
    const { unmount } = renderHook(() => useRaceHeatmap());
    unmount();

    // Now resolve the fetch — guards should swallow the setState writes
    if (resolveFetch) {
      (resolveFetch as (v: unknown) => void)(undefined);
    }
    // Let microtasks flush
    await new Promise((r) => setTimeout(r, 0));

    expect(warnSpy).not.toHaveBeenCalledWith(
      expect.stringContaining("unmounted component"),
    );
    warnSpy.mockRestore();
  });
});
