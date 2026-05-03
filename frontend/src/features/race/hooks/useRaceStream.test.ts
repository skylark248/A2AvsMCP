/**
 * Tests for useRaceStream hook.
 * WebSocket lifecycle, per-lane reconnect cursor (D-45), enabled gate (T-08-16, D-44).
 * B2 fix: runId param injected into WS URL as run_id= query param (Phase 14 plan 02).
 * Uses vi.stubGlobal('WebSocket', MockWebSocket) — no codebase precedent (08-PATTERNS line 780).
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";
import { renderHook, act } from "@testing-library/react";

import { useRaceStream } from "./useRaceStream";

// ---- MockWebSocket ---------------------------------------------------------

type WsEventHandler = ((ev: MessageEvent) => void) | null;
type CloseHandler = ((ev: CloseEvent) => void) | null;
type ErrorHandler = ((ev: Event) => void) | null;
type OpenHandler = (() => void) | null;

class MockWebSocket {
  static instances: MockWebSocket[] = [];

  url: string;
  onmessage: WsEventHandler = null;
  onclose: CloseHandler = null;
  onerror: ErrorHandler = null;
  onopen: OpenHandler = null;
  readyState: number = WebSocket.CONNECTING;
  closed = false;

  constructor(url: string) {
    this.url = url;
    MockWebSocket.instances.push(this);
  }

  close() {
    this.closed = true;
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent("close"));
    }
  }

  // Test helper: simulate an incoming message
  simulateMessage(data: unknown) {
    if (this.onmessage) {
      this.onmessage(new MessageEvent("message", { data: JSON.stringify(data) }));
    }
  }

  // Test helper: simulate a socket error
  simulateError() {
    if (this.onerror) {
      this.onerror(new Event("error"));
    }
  }

  // Test helper: simulate socket close without calling our close()
  simulateClose() {
    this.readyState = WebSocket.CLOSED;
    if (this.onclose) {
      this.onclose(new CloseEvent("close"));
    }
  }
}

// ---- Setup / Teardown ------------------------------------------------------

beforeEach(() => {
  MockWebSocket.instances = [];
  vi.stubGlobal("WebSocket", MockWebSocket);
});

afterEach(() => {
  vi.unstubAllGlobals();
});

// ---- Tests -----------------------------------------------------------------

describe("useRaceStream — hook signature", () => {
  it("exports useRaceStream as a function", () => {
    expect(typeof useRaceStream).toBe("function");
  });

  it("returns RaceState shape (lanes, ws_status, run_id)", () => {
    const { result } = renderHook(() => useRaceStream("", true));
    const state = result.current;
    expect(state).toHaveProperty("lanes");
    expect(state).toHaveProperty("ws_status");
    expect(state).toHaveProperty("run_id");
    expect(state.run_id).toBeNull(); // live mode
  });
});

describe("useRaceStream — WebSocket lifecycle (enabled=true)", () => {
  it("opens a WebSocket to /api/race/ws on mount when enabled is true", () => {
    renderHook(() => useRaceStream("test-run-id", true));
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toContain("/api/race/ws");
  });

  it("opens a WebSocket with default enabled (only runId arg)", () => {
    renderHook(() => useRaceStream("test-run-id"));
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toContain("/api/race/ws");
  });

  it("closes WebSocket on unmount", () => {
    const { unmount } = renderHook(() => useRaceStream("test-run-id", true));
    const socket = MockWebSocket.instances[0];
    unmount();
    expect(socket.closed).toBe(true);
  });
});

describe("useRaceStream — enabled=false gate (T-08-16)", () => {
  it("does NOT open a WebSocket when enabled=false", () => {
    renderHook(() => useRaceStream("test-run-id", false));
    expect(MockWebSocket.instances).toHaveLength(0);
  });

  it("still returns initial RaceState when enabled=false", () => {
    const { result } = renderHook(() => useRaceStream("test-run-id", false));
    expect(result.current.ws_status).toBe("connecting");
    expect(result.current.lanes.pure_mcp.last_turn_index).toBe(-1);
  });

  it("opens WebSocket when enabled toggles from false to true", () => {
    const { rerender } = renderHook(
      ({ enabled }: { enabled: boolean }) => useRaceStream("run-abc", enabled),
      { initialProps: { enabled: false } },
    );
    expect(MockWebSocket.instances).toHaveLength(0);

    rerender({ enabled: true });
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toContain("/api/race/ws");
  });

  it("closes WebSocket when enabled toggles from true to false", () => {
    const { rerender } = renderHook(
      ({ enabled }: { enabled: boolean }) => useRaceStream("run-abc", enabled),
      { initialProps: { enabled: true } },
    );
    const socket = MockWebSocket.instances[0];
    expect(socket.closed).toBe(false);

    rerender({ enabled: false });
    expect(socket.closed).toBe(true);
  });
});

describe("useRaceStream — message dispatch", () => {
  it("dispatches incoming ws message into reducer; state reflects the change", () => {
    const { result } = renderHook(() => useRaceStream("run-123", true));
    const socket = MockWebSocket.instances[0];

    act(() => {
      socket.simulateMessage({ type: "tick", lane: "pure_mcp", turn_index: 5, t_ms: 50 });
    });

    expect(result.current.lanes.pure_mcp.last_turn_index).toBe(5);
  });

  it("dispatches ws_error on socket error → ws_status becomes closed", () => {
    const { result } = renderHook(() => useRaceStream("run-123", true));
    const socket = MockWebSocket.instances[0];

    act(() => {
      socket.simulateError();
    });

    expect(result.current.ws_status).toBe("closed");
  });

  it("dispatches ws_closed on socket close → ws_status becomes closed", () => {
    const { result } = renderHook(() => useRaceStream("run-123", true));
    const socket = MockWebSocket.instances[0];

    act(() => {
      socket.simulateClose();
    });

    expect(result.current.ws_status).toBe("closed");
  });
});

describe("useRaceStream — per-lane reconnect cursor (D-45)", () => {
  it("initial WS URL contains per-lane cursors with default -1 values", () => {
    renderHook(() => useRaceStream("run-xyz", true));
    const url = MockWebSocket.instances[0].url;
    expect(url).toContain("pure_mcp=-1");
    expect(url).toContain("pure_a2a=-1");
    expect(url).toContain("hybrid=-1");
  });
});

describe("useRaceStream — run_id in WS URL (B2 fix, Phase 14 plan 02)", () => {
  it("includes run_id as first query param in WS URL when runId is provided", () => {
    renderHook(() => useRaceStream("my-run-id-123", true));
    const url = MockWebSocket.instances[0].url;
    expect(url).toContain("run_id=my-run-id-123");
    // run_id should appear before lane cursors
    const runIdIdx = url.indexOf("run_id=");
    const pureMcpIdx = url.indexOf("pure_mcp=");
    expect(runIdIdx).toBeLessThan(pureMcpIdx);
  });

  it("encodes run_id with encodeURIComponent in WS URL (T-14-02-01)", () => {
    renderHook(() => useRaceStream("run id with spaces", true));
    const url = MockWebSocket.instances[0].url;
    expect(url).toContain("run_id=run%20id%20with%20spaces");
  });

  it("opens a new WebSocket when runId changes", () => {
    const { rerender } = renderHook(
      ({ runId }: { runId: string }) => useRaceStream(runId, true),
      { initialProps: { runId: "run-first" } },
    );
    expect(MockWebSocket.instances).toHaveLength(1);
    expect(MockWebSocket.instances[0].url).toContain("run_id=run-first");

    rerender({ runId: "run-second" });
    // Old socket closed, new socket opened
    expect(MockWebSocket.instances).toHaveLength(2);
    expect(MockWebSocket.instances[1].url).toContain("run_id=run-second");
  });

  it("WS URL format: ws(s)://host/api/race/ws?run_id=X&pure_mcp=N&pure_a2a=N&hybrid=N", () => {
    renderHook(() => useRaceStream("abc123", true));
    const url = MockWebSocket.instances[0].url;
    // Should match pattern: ws(s)://host/api/race/ws?run_id=abc123&pure_mcp=-1&pure_a2a=-1&hybrid=-1
    expect(url).toMatch(/^wss?:\/\/.+\/api\/race\/ws\?run_id=abc123&pure_mcp=-1&pure_a2a=-1&hybrid=-1$/);
  });

  it("still gates WS on enabled=false even with non-empty runId (T-08-16 preserved)", () => {
    renderHook(() => useRaceStream("valid-run-id", false));
    expect(MockWebSocket.instances).toHaveLength(0);
  });
});
