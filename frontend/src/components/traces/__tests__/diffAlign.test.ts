import { describe, it, expect } from "vitest";
import { alignTraces, type DiffRow } from "../diffAlign";
import type { TraceEvent } from "../../../lib/types/api";

// ---------------------------------------------------------------------------
// Fixture helper
// ---------------------------------------------------------------------------

function evt(
  overrides: Partial<TraceEvent> & { turn_index?: number; [k: string]: unknown },
): TraceEvent {
  return {
    index: 0,
    event_type: "tool_call",
    timestamp_ms: 1,
    ...overrides,
  } as TraceEvent;
}

// ---------------------------------------------------------------------------
// Tests
// ---------------------------------------------------------------------------

describe("alignTraces", () => {
  it("returns empty array for empty inputs", () => {
    expect(alignTraces([], [])).toEqual([]);
  });

  it("classifies same (turn_index, event_type) with identical non-trivial fields as matched-equal", () => {
    // timestamp_ms and index are IGNORE_FIELDS — differ here but should NOT trigger divergence
    const left = [evt({ event_type: "tool_call", turn_index: 0, tool: "db_server", timestamp_ms: 1, index: 0 })];
    const right = [evt({ event_type: "tool_call", turn_index: 0, tool: "db_server", timestamp_ms: 999, index: 5 })];
    const rows = alignTraces(left, right);
    expect(rows).toHaveLength(1);
    expect(rows[0].status).toBe("matched-equal");
    expect(rows[0].divergenceCause).toBeUndefined();
    expect(rows[0].left).toBe(left[0]);
    expect(rows[0].right).toBe(right[0]);
    expect(rows[0].turnIndex).toBe(0);
  });

  it("classifies field-only difference as matched-divergent with cause=field", () => {
    const left = [evt({ event_type: "tool_call", turn_index: 0, tool: "db_server" })];
    const right = [evt({ event_type: "tool_call", turn_index: 0, tool: "docs_server" })];
    const rows = alignTraces(left, right);
    expect(rows).toHaveLength(1);
    expect(rows[0].status).toBe("matched-divergent");
    expect(rows[0].divergenceCause).toBe("field");
    expect(rows[0].differingFields).toContain("tool");
  });

  it("classifies fault-only-on-one-side as matched-divergent with cause=fault (fault_ field differs)", () => {
    // Left has fault_observed=true and fault_kind; right does not.
    // The fault_ field names start with "fault_" so divergenceCause must be "fault".
    const left = [
      evt({ event_type: "tool_call", turn_index: 0, fault_observed: true, fault_kind: "timeout" }),
    ];
    const right = [evt({ event_type: "tool_call", turn_index: 0 })];
    const rows = alignTraces(left, right);
    expect(rows).toHaveLength(1);
    expect(rows[0].status).toBe("matched-divergent");
    expect(rows[0].divergenceCause).toBe("fault");
    // At least fault_observed should appear in differingFields
    expect(rows[0].differingFields?.some((f) => f.startsWith("fault_"))).toBe(true);
  });

  it("classifies left-only event as removed and right-only event as added", () => {
    // Different turn_indices so they don't pair.
    const leftOnly = evt({ event_type: "tool_call", turn_index: 0, tool: "db_server" });
    const rightOnly = evt({ event_type: "agent_msg", turn_index: 1 });
    const rows = alignTraces([leftOnly], [rightOnly]);
    expect(rows).toHaveLength(2);

    const removed = rows.find((r) => r.status === "removed");
    const added = rows.find((r) => r.status === "added");

    expect(removed).toBeDefined();
    expect(removed!.left).toBe(leftOnly);
    expect(removed!.right).toBeUndefined();

    expect(added).toBeDefined();
    expect(added!.right).toBe(rightOnly);
    expect(added!.left).toBeUndefined();
  });

  it("includes every event_type in output (D-76 — no pre-filter)", () => {
    // Build a fixture with one event each of 6 event_types on different turn_indices.
    // Identical left and right means all should be matched-equal — none silently dropped.
    const eventTypes = [
      "tool_discovery",
      "a2a_remote_discovery",
      "agent_msg",
      "fault_observed",
      "llm_request",
      "tool_call",
    ];
    const leftEvents = eventTypes.map((et, i) => evt({ event_type: et, turn_index: i }));
    const rightEvents = eventTypes.map((et, i) => evt({ event_type: et, turn_index: i }));

    const rows = alignTraces(leftEvents, rightEvents);

    // All 6 pairs must appear — none filtered out (D-76)
    expect(rows.length).toBeGreaterThanOrEqual(6);
    expect(rows.every((r) => r.status === "matched-equal")).toBe(true);

    // Each event_type appears at least once in left side of output
    const outputEventTypes = rows.map((r) => r.left?.event_type ?? r.right?.event_type);
    for (const et of eventTypes) {
      expect(outputEventTypes).toContain(et);
    }
  });

  it("sorts within a turn bucket as matched-equal, matched-divergent, removed, added", () => {
    // Build 4 events under turn_index=0 with DIFFERENT event_types so they don't collide.
    // 1. matched-equal pair: event_type="tool_call"
    // 2. matched-divergent pair: event_type="agent_msg" (tool differs)
    // 3. removed-only: event_type="llm_request" (only on left)
    // 4. added-only: event_type="tool_discovery" (only on right)
    const leftEvents = [
      evt({ event_type: "tool_call", turn_index: 0, tool: "db_server" }),
      evt({ event_type: "agent_msg", turn_index: 0, tool: "db_server" }),
      evt({ event_type: "llm_request", turn_index: 0 }),
    ];
    const rightEvents = [
      evt({ event_type: "tool_call", turn_index: 0, tool: "db_server" }),
      evt({ event_type: "agent_msg", turn_index: 0, tool: "docs_server" }),
      evt({ event_type: "tool_discovery", turn_index: 0 }),
    ];

    const rows = alignTraces(leftEvents, rightEvents);
    // Should have 4 rows: matched-equal, matched-divergent, removed, added
    expect(rows).toHaveLength(4);

    const statuses = rows.map((r: DiffRow) => r.status);
    expect(statuses).toEqual(["matched-equal", "matched-divergent", "removed", "added"]);
  });

  it("orders rows ascending by turnIndex across buckets", () => {
    // Mix turn_indices 2, 0, 1 — output must be in ascending order.
    const leftEvents = [
      evt({ event_type: "tool_call", turn_index: 2 }),
      evt({ event_type: "tool_call", turn_index: 0 }),
      evt({ event_type: "tool_call", turn_index: 1 }),
    ];
    const rightEvents = [
      evt({ event_type: "tool_call", turn_index: 2 }),
      evt({ event_type: "tool_call", turn_index: 0 }),
      evt({ event_type: "tool_call", turn_index: 1 }),
    ];

    const rows = alignTraces(leftEvents, rightEvents);
    const indices = rows.map((r: DiffRow) => r.turnIndex);
    // Must be non-decreasing
    for (let i = 1; i < indices.length; i++) {
      expect(indices[i]).toBeGreaterThanOrEqual(indices[i - 1]);
    }
    // Specifically [0, 1, 2]
    expect(indices).toEqual([0, 1, 2]);
  });

  it("handles multiple events of the same (turn_index, event_type) by pairing in arrival order", () => {
    // Two tool_call events in turn_index=0 on each side. Paired by index:
    //   left[0] + right[0] → matched-equal (same tool)
    //   left[1] + right[1] → matched-divergent (different tool)
    const leftEvents = [
      evt({ event_type: "tool_call", turn_index: 0, tool: "db_server" }),
      evt({ event_type: "tool_call", turn_index: 0, tool: "docs_server" }),
    ];
    const rightEvents = [
      evt({ event_type: "tool_call", turn_index: 0, tool: "db_server" }),
      evt({ event_type: "tool_call", turn_index: 0, tool: "cache_server" }),
    ];

    const rows = alignTraces(leftEvents, rightEvents);
    expect(rows).toHaveLength(2);
    // First pair: db_server vs db_server → matched-equal
    expect(rows[0].status).toBe("matched-equal");
    // Second pair: docs_server vs cache_server → matched-divergent
    expect(rows[1].status).toBe("matched-divergent");
    expect(rows[1].divergenceCause).toBe("field");
    expect(rows[1].differingFields).toContain("tool");
  });

  it("classifies matched-divergent with cause=fault when isTraceFailureEvent disagrees", () => {
    // error field makes isTraceFailureEvent return true for left but false for right.
    const leftWithError = evt({ event_type: "tool_call", turn_index: 0, error: "timeout" });
    const rightOk = evt({ event_type: "tool_call", turn_index: 0 });
    const rows = alignTraces([leftWithError], [rightOk]);
    expect(rows).toHaveLength(1);
    expect(rows[0].status).toBe("matched-divergent");
    expect(rows[0].divergenceCause).toBe("fault");
  });

  it("treats all IGNORE_FIELDS differences as matched-equal (run_id, parallel_batch_id, etc.)", () => {
    const left = [
      evt({
        event_type: "tool_call",
        turn_index: 0,
        run_id: "run-aaa",
        parallel_batch_id: "batch-aaa",
        task_id: "task-aaa",
        messageId: "msg-aaa",
        contextId: "ctx-aaa",
        artifactId: "art-aaa",
        lane: "mcp",
      }),
    ];
    const right = [
      evt({
        event_type: "tool_call",
        turn_index: 0,
        run_id: "run-bbb",
        parallel_batch_id: "batch-bbb",
        task_id: "task-bbb",
        messageId: "msg-bbb",
        contextId: "ctx-bbb",
        artifactId: "art-bbb",
        lane: "a2a",
      }),
    ];
    const rows = alignTraces(left, right);
    expect(rows).toHaveLength(1);
    expect(rows[0].status).toBe("matched-equal");
  });
});
