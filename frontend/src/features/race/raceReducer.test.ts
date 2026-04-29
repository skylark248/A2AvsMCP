/**
 * Task 1 RED: Tests for raceReducer pure state machine.
 * All event types from the closed RaceEvent union must be handled.
 * Cursor (last_turn_index) must be monotonically non-decreasing per lane (D-45).
 */
import { describe, it, expect } from "vitest";

// These imports will fail until Task 1 GREEN — that is expected (RED phase).
import { raceReducer, initialRaceState } from "./raceReducer";
import type { RaceEvent } from "../../lib/types/race";

// ---- Helpers ---------------------------------------------------------------

function tick(lane: "pure_mcp" | "pure_a2a" | "hybrid", turn_index: number): RaceEvent {
  return { type: "tick", lane, turn_index, t_ms: turn_index * 10 };
}

function toolCall(lane: "pure_mcp" | "pure_a2a" | "hybrid", turn_index: number): RaceEvent {
  return { type: "tool_call", lane, turn_index, tool_name: "search", status: "ok", t_call_ms: 42 };
}

function agentMsg(lane: "pure_mcp" | "pure_a2a" | "hybrid", turn_index: number): RaceEvent {
  return {
    type: "agent_msg",
    lane,
    turn_index,
    sender: "agent_a",
    recipient: "agent_b",
    content: "hello",
    t_ms: turn_index * 10,
  };
}

function faultInjected(lane: "pure_mcp" | "pure_a2a" | "hybrid", turn_index: number, fault_id: string): RaceEvent {
  return {
    type: "fault_injected",
    lane,
    turn_index,
    fault_id,
    fault_kind: "latency",
    target: "tool_search",
    t_inject_ms: turn_index * 10,
  };
}

function faultObserved(
  lane: "pure_mcp" | "pure_a2a" | "hybrid",
  turn_index: number,
  fault_id: string,
  t_observed_ms: number,
): RaceEvent {
  return {
    type: "fault_observed",
    lane,
    turn_index,
    fault_id,
    evidence: "retry attempt",
    wasted_tokens_before_detection: 50,
    t_observed_ms,
  };
}

function doneEvent(lane: "pure_mcp" | "pure_a2a" | "hybrid", turn_index: number): RaceEvent {
  return { type: "done", lane, turn_index, tag: "recovered", headline: "Agent recovered!" };
}

function errorEvent(lane: "pure_mcp" | "pure_a2a" | "hybrid", turn_index: number): RaceEvent {
  return { type: "error", lane, turn_index, message: "Something went wrong" };
}

// ---- Suite -----------------------------------------------------------------

describe("initialRaceState", () => {
  it("ws_status is connecting", () => {
    expect(initialRaceState.ws_status).toBe("connecting");
  });

  it("all 3 lanes initialised with last_turn_index === -1", () => {
    expect(initialRaceState.lanes.pure_mcp.last_turn_index).toBe(-1);
    expect(initialRaceState.lanes.pure_a2a.last_turn_index).toBe(-1);
    expect(initialRaceState.lanes.hybrid.last_turn_index).toBe(-1);
  });

  it("all 3 lanes are present", () => {
    const keys = Object.keys(initialRaceState.lanes);
    expect(keys).toContain("pure_mcp");
    expect(keys).toContain("pure_a2a");
    expect(keys).toContain("hybrid");
  });
});

describe("tick event", () => {
  it("advances last_turn_index for the correct lane", () => {
    const state = raceReducer(initialRaceState, tick("pure_mcp", 0));
    expect(state.lanes.pure_mcp.last_turn_index).toBe(0);
  });

  it("advances cursor to 5 after receiving turn_index 3 then 5", () => {
    const s1 = raceReducer(initialRaceState, tick("pure_mcp", 3));
    const s2 = raceReducer(s1, tick("pure_mcp", 5));
    expect(s2.lanes.pure_mcp.last_turn_index).toBe(5);
  });

  it("does NOT regress cursor when receiving a stale (out-of-order) turn_index", () => {
    const s1 = raceReducer(initialRaceState, tick("pure_mcp", 5));
    const s2 = raceReducer(s1, tick("pure_mcp", 2)); // stale
    expect(s2.lanes.pure_mcp.last_turn_index).toBe(5);
  });

  it("does not affect other lanes", () => {
    const state = raceReducer(initialRaceState, tick("pure_mcp", 3));
    expect(state.lanes.pure_a2a.last_turn_index).toBe(-1);
    expect(state.lanes.hybrid.last_turn_index).toBe(-1);
  });
});

describe("tool_call event", () => {
  it("appends to lane events and updates last_turn_index", () => {
    const state = raceReducer(initialRaceState, toolCall("pure_a2a", 1));
    expect(state.lanes.pure_a2a.events).toHaveLength(1);
    expect(state.lanes.pure_a2a.events[0].type).toBe("tool_call");
    expect(state.lanes.pure_a2a.last_turn_index).toBe(1);
  });
});

describe("agent_msg event", () => {
  it("appends to lane events", () => {
    const state = raceReducer(initialRaceState, agentMsg("hybrid", 2));
    expect(state.lanes.hybrid.events).toHaveLength(1);
    expect(state.lanes.hybrid.events[0].type).toBe("agent_msg");
  });
});

describe("fault_injected event", () => {
  it("appends a fault with observed: false to lane.faults", () => {
    const state = raceReducer(initialRaceState, faultInjected("pure_mcp", 4, "f1"));
    expect(state.lanes.pure_mcp.faults).toHaveLength(1);
    expect(state.lanes.pure_mcp.faults[0].fault_id).toBe("f1");
    expect(state.lanes.pure_mcp.faults[0].observed).toBe(false);
  });
});

describe("fault_observed event", () => {
  it("marks the matching fault as observed: true", () => {
    const s1 = raceReducer(initialRaceState, faultInjected("pure_mcp", 4, "f1"));
    const s2 = raceReducer(s1, faultObserved("pure_mcp", 6, "f1", 600));
    expect(s2.lanes.pure_mcp.faults[0].observed).toBe(true);
  });

  it("computes ttff_ms on first observation", () => {
    const s1 = raceReducer(initialRaceState, faultInjected("pure_mcp", 4, "f1"));
    const s2 = raceReducer(s1, faultObserved("pure_mcp", 6, "f1", 600));
    expect(s2.lanes.pure_mcp.ttff_ms).toBe(600);
  });

  it("does NOT overwrite ttff_ms on a second observation", () => {
    const s1 = raceReducer(initialRaceState, faultInjected("pure_mcp", 4, "f1"));
    const s2 = raceReducer(s1, faultInjected("pure_mcp", 5, "f2"));
    const s3 = raceReducer(s2, faultObserved("pure_mcp", 6, "f1", 600));
    const s4 = raceReducer(s3, faultObserved("pure_mcp", 7, "f2", 900));
    expect(s4.lanes.pure_mcp.ttff_ms).toBe(600); // first observation wins
  });
});

describe("done event", () => {
  it("sets terminal_tag and headline on the lane", () => {
    const state = raceReducer(initialRaceState, doneEvent("pure_mcp", 10));
    expect(state.lanes.pure_mcp.terminal_tag).toBe("recovered");
    expect(state.lanes.pure_mcp.headline).toBe("Agent recovered!");
  });
});

describe("error event", () => {
  it("appends an error event to the lane events without crashing", () => {
    const state = raceReducer(initialRaceState, errorEvent("hybrid", 3));
    expect(state.lanes.hybrid.events).toHaveLength(1);
    expect(state.lanes.hybrid.events[0].type).toBe("error");
  });

  it("does NOT set terminal_tag on error (pre-classification signal)", () => {
    const state = raceReducer(initialRaceState, errorEvent("hybrid", 3));
    expect(state.lanes.hybrid.terminal_tag).toBeNull();
  });
});

describe("race_done event", () => {
  it("does NOT mutate per-lane state (session-level signal only)", () => {
    const s1 = raceReducer(initialRaceState, tick("pure_mcp", 3));
    const s2 = raceReducer(s1, { type: "race_done", turn_index: 10 });
    // All per-lane state identical to s1
    expect(s2.lanes.pure_mcp.last_turn_index).toBe(s1.lanes.pure_mcp.last_turn_index);
    expect(s2.lanes.pure_a2a.last_turn_index).toBe(s1.lanes.pure_a2a.last_turn_index);
    expect(s2.lanes.hybrid.last_turn_index).toBe(s1.lanes.hybrid.last_turn_index);
  });
});

describe("ws_closed event", () => {
  it("sets ws_status to closed while preserving lane state", () => {
    const s1 = raceReducer(initialRaceState, tick("pure_mcp", 5));
    const s2 = raceReducer(s1, { type: "ws_closed" });
    expect(s2.ws_status).toBe("closed");
    expect(s2.lanes.pure_mcp.last_turn_index).toBe(5); // lane preserved
  });
});

describe("ws_error event", () => {
  it("sets ws_status to closed while preserving lane state", () => {
    const s1 = raceReducer(initialRaceState, tick("hybrid", 7));
    const s2 = raceReducer(s1, { type: "ws_error" });
    expect(s2.ws_status).toBe("closed");
    expect(s2.lanes.hybrid.last_turn_index).toBe(7); // lane preserved
  });
});

describe("reducer purity", () => {
  it("produces structurally-equal output when called twice with same inputs", () => {
    const event = tick("pure_mcp", 2);
    const out1 = raceReducer(initialRaceState, event);
    const out2 = raceReducer(initialRaceState, event);
    expect(out1).toEqual(out2);
  });

  it("does not share mutable references between successive calls (no aliased arrays)", () => {
    const s1 = raceReducer(initialRaceState, tick("pure_mcp", 1));
    const s2 = raceReducer(s1, tick("pure_mcp", 2));
    // events arrays must be distinct objects
    expect(s2.lanes.pure_mcp.events).not.toBe(s1.lanes.pure_mcp.events);
  });
});

describe("events feed cap (T-08-09 memory bound)", () => {
  it("caps events array at last 200 entries", () => {
    let state = initialRaceState;
    for (let i = 0; i < 210; i++) {
      state = raceReducer(state, tick("pure_mcp", i));
    }
    expect(state.lanes.pure_mcp.events.length).toBeLessThanOrEqual(200);
  });
});
