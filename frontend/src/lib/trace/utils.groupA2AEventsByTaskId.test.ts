import { describe, it, expect } from "vitest";
import { groupA2AEventsByTaskId } from "./utils";
import type { TraceEvent } from "../types/api";

function makeEvent(overrides: Partial<TraceEvent> & { event_type: string }): TraceEvent {
  return {
    index: 0,
    timestamp_ms: 0,
    ...overrides,
  };
}

describe("groupA2AEventsByTaskId", () => {
  it("Test 1: returns empty Map for empty input", () => {
    const result = groupA2AEventsByTaskId([]);
    expect(result).toBeInstanceOf(Map);
    expect(result.size).toBe(0);
  });

  it("Test 2: two a2a_message events with same task_id are grouped together", () => {
    const events: TraceEvent[] = [
      makeEvent({ event_type: "a2a_message", task_id: "t1" } as TraceEvent & { task_id: string }),
      makeEvent({ event_type: "a2a_message", task_id: "t1" } as TraceEvent & { task_id: string }),
    ];
    const result = groupA2AEventsByTaskId(events);
    expect(result.size).toBe(1);
    expect(result.get("t1")).toHaveLength(2);
  });

  it("Test 3: a2a_message with task_id=t1 and a2a_task_artifact with task_id=t2 produce two groups", () => {
    const events: TraceEvent[] = [
      makeEvent({ event_type: "a2a_message", task_id: "t1" } as TraceEvent & { task_id: string }),
      makeEvent({ event_type: "a2a_task_artifact", task_id: "t2" } as TraceEvent & { task_id: string }),
    ];
    const result = groupA2AEventsByTaskId(events);
    expect(result.size).toBe(2);
    expect(result.get("t1")).toHaveLength(1);
    expect(result.get("t2")).toHaveLength(1);
  });

  it("Test 4: task_status event with task_id is included in the group", () => {
    const events: TraceEvent[] = [
      makeEvent({ event_type: "task_status", task_id: "t1" } as TraceEvent & { task_id: string }),
    ];
    const result = groupA2AEventsByTaskId(events);
    expect(result.size).toBe(1);
    expect(result.get("t1")).toHaveLength(1);
  });

  it("Test 5: tool_call event (not A2A) is NOT included in any group", () => {
    const events: TraceEvent[] = [
      makeEvent({ event_type: "tool_call", task_id: "t1" } as TraceEvent & { task_id: string }),
    ];
    const result = groupA2AEventsByTaskId(events);
    expect(result.size).toBe(0);
  });

  it("Test 6: A2A event with no task_id is grouped under 'unknown'", () => {
    const events: TraceEvent[] = [
      makeEvent({ event_type: "a2a_message" }),
    ];
    const result = groupA2AEventsByTaskId(events);
    expect(result.size).toBe(1);
    expect(result.get("unknown")).toHaveLength(1);
  });
});
