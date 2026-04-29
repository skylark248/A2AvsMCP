/**
 * Task 2 RED: Tests for useRaceReplay hook.
 * run_id validation (T-08-05), fetch lifecycle, cleanup-on-unmount discipline.
 * Uses vi.spyOn(global, 'fetch') to intercept fetchRaceReplay.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";

// These imports will fail until Task 2 GREEN — expected (RED phase).
import { useRaceReplay } from "./useRaceReplay";

// ---- Helpers ---------------------------------------------------------------

function makeMockFetch(payload: unknown, ok = true, status = 200) {
  return vi.fn().mockResolvedValue({
    ok,
    status,
    json: () => Promise.resolve(payload),
    text: () => Promise.resolve(JSON.stringify(payload)),
  });
}

const VALID_PAYLOAD = {
  run_id: "abc-123_def",
  events: [],
  schema_version: "1.0",
};

// ---- Setup / Teardown ------------------------------------------------------

beforeEach(() => {
  vi.restoreAllMocks();
});

afterEach(() => {
  vi.restoreAllMocks();
});

// ---- Tests -----------------------------------------------------------------

describe("useRaceReplay — run_id validation (T-08-05)", () => {
  it("valid run_id triggers a fetch", async () => {
    vi.stubGlobal("fetch", makeMockFetch(VALID_PAYLOAD));
    const { result } = renderHook(() => useRaceReplay("abc-123_def"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/race/runs/abc-123_def/trace"));
  });

  it("invalid run_id with slash does NOT fetch and returns error", () => {
    vi.stubGlobal("fetch", makeMockFetch(VALID_PAYLOAD));
    const { result } = renderHook(() => useRaceReplay("../../etc/passwd"));

    expect(result.current.trace).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe("Invalid run_id");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("invalid run_id with double-dot does NOT fetch and returns error", () => {
    vi.stubGlobal("fetch", makeMockFetch(VALID_PAYLOAD));
    const { result } = renderHook(() => useRaceReplay("run..id"));

    expect(result.current.trace).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe("Invalid run_id");
    expect(fetch).not.toHaveBeenCalled();
  });

  it("invalid run_id over 64 chars does NOT fetch and returns error", () => {
    vi.stubGlobal("fetch", makeMockFetch(VALID_PAYLOAD));
    const longId = "a".repeat(65);
    const { result } = renderHook(() => useRaceReplay(longId));

    expect(result.current.trace).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe("Invalid run_id");
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe("useRaceReplay — fetch lifecycle", () => {
  it("starts in loading=true when a valid run_id is provided", () => {
    // Make fetch never resolve during this test
    vi.stubGlobal("fetch", vi.fn().mockReturnValue(new Promise(() => {})));
    const { result } = renderHook(() => useRaceReplay("abc123"));

    expect(result.current.trace).toBeNull();
    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBeNull();
  });

  it("on fetch success: trace populated, loading false, error null", async () => {
    vi.stubGlobal("fetch", makeMockFetch(VALID_PAYLOAD));
    const { result } = renderHook(() => useRaceReplay("abc-123_def"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.trace).toEqual(VALID_PAYLOAD);
    expect(result.current.error).toBeNull();
  });

  it("on fetch error: trace null, loading false, error message set", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockRejectedValue(new Error("Network error")),
    );
    const { result } = renderHook(() => useRaceReplay("abc123"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.trace).toBeNull();
    expect(result.current.error).toBeTruthy();
  });

  it("on fetch non-ok response: trace null, loading false, error message set", async () => {
    vi.stubGlobal("fetch", makeMockFetch({}, false, 404));
    const { result } = renderHook(() => useRaceReplay("abc123"));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.trace).toBeNull();
    expect(result.current.error).toBeTruthy();
  });
});

describe("useRaceReplay — undefined run_id", () => {
  it("does not fetch when run_id is undefined", () => {
    vi.stubGlobal("fetch", makeMockFetch(VALID_PAYLOAD));
    const { result } = renderHook(() => useRaceReplay(undefined));

    expect(result.current.trace).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });
});

describe("useRaceReplay — cleanup on unmount (stale state prevention)", () => {
  it("does not update state after unmount (active flag discipline)", async () => {
    let resolveFetch!: (value: unknown) => void;
    vi.stubGlobal(
      "fetch",
      vi.fn().mockReturnValue(
        new Promise((resolve) => {
          resolveFetch = resolve;
        }),
      ),
    );

    const { result, unmount } = renderHook(() => useRaceReplay("abc123"));
    expect(result.current.loading).toBe(true);

    // Unmount before fetch resolves
    unmount();

    // Resolve the fetch after unmount — should NOT trigger setState (no crash, no warning)
    resolveFetch({
      ok: true,
      status: 200,
      json: () => Promise.resolve(VALID_PAYLOAD),
    });

    // No assertion on result.current (component unmounted) — test passes if no error thrown
    await new Promise((r) => setTimeout(r, 50));
  });
});
