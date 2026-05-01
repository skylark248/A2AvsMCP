import type { TraceEvent } from "../../lib/types/api";
import { isTraceFailureEvent } from "../../lib/trace/utils";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export type DiffStatus = "added" | "removed" | "matched-equal" | "matched-divergent";

export interface DiffRow {
  status: DiffStatus;
  left?: TraceEvent;
  right?: TraceEvent;
  turnIndex: number;
  divergenceCause?: "fault" | "field";
  differingFields?: string[];
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/**
 * Fields that always differ between two protocol runs but carry no signal of
 * behavioral divergence. Excluded from the field-by-field comparison.
 * Do NOT mutate this set at runtime.
 */
const IGNORE_FIELDS = new Set<string>([
  "timestamp_ms",
  "started_at",
  "completed_at",
  "index",
  "parallel_batch_id",
  "task_id",
  "messageId",
  "contextId",
  "artifactId",
  "run_id",
  "lane",
]);

// Within-turn sort order: matched-equal first, matched-divergent next, then removed, added.
const STATUS_ORDER: Record<DiffStatus, number> = {
  "matched-equal": 0,
  "matched-divergent": 1,
  removed: 2,
  added: 3,
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Coerce turn_index from the open-ended index signature on TraceEvent.
 * turn_index is emitted by the backend (trace.py) but not statically declared
 * on the TypeScript interface — it arrives as `unknown` via `[key: string]: unknown`.
 */
function turnIndexOf(e: TraceEvent): number {
  return Number((e as { turn_index?: unknown }).turn_index ?? 0);
}

/**
 * Compare two events field-by-field, ignoring IGNORE_FIELDS.
 * Returns the set of field names that differ (non-empty → events diverge).
 */
function compareFields(
  l: TraceEvent,
  r: TraceEvent,
): { equal: boolean; diffs: string[] } {
  const keys = new Set([...Object.keys(l), ...Object.keys(r)]);
  const diffs: string[] = [];
  for (const k of keys) {
    if (IGNORE_FIELDS.has(k)) continue;
    if (
      JSON.stringify((l as Record<string, unknown>)[k]) !==
      JSON.stringify((r as Record<string, unknown>)[k])
    ) {
      diffs.push(k);
    }
  }
  return { equal: diffs.length === 0, diffs };
}

// ---------------------------------------------------------------------------
// Public API
// ---------------------------------------------------------------------------

/**
 * Align two protocol traces into a flat list of `DiffRow` entries.
 *
 * ## Alignment contract (D-74)
 * Two events match iff `a.turn_index === b.turn_index && a.event_type === b.event_type`.
 * Unmatched on either side = added/removed. Matched events are compared field-by-field
 * for "matched-divergent" status (e.g., one has `fault_observed`, the other doesn't).
 *
 * ## Scope (D-76)
 * No event_type pre-filter. Every event — including tool_discovery, a2a_remote_discovery,
 * agent_msg, fault_*, llm_* — appears in the output. Discovery divergence is a feature.
 *
 * ## Within-turn pairing (Pitfall 8)
 * Within a `(turn_index, event_type)` bucket events pair by arrival order. If a turn
 * emits the same event_type multiple times in different orders across protocols, divergence
 * may surface as matched-divergent rows even when both sides did the same work — by design
 * for v1.
 *
 * ## Sort order
 * Output is sorted by `turnIndex` ascending, then within a turn bucket:
 * matched-equal → matched-divergent → removed → added (UI-SPEC line 211).
 *
 * @param left  Events from Trace A (typically MCP protocol run).
 * @param right Events from Trace B (typically A2A protocol run).
 * @returns     Flat sorted array of DiffRow, one entry per (paired or unpaired) event.
 */
export function alignTraces(left: TraceEvent[], right: TraceEvent[]): DiffRow[] {
  // Step 1: bucket each side by `${turnIndex}::${event_type}` → ordered list of events.
  const makeKey = (e: TraceEvent): string => `${turnIndexOf(e)}::${e.event_type}`;

  const bucket = (events: TraceEvent[]): Map<string, TraceEvent[]> => {
    const m = new Map<string, TraceEvent[]>();
    for (const e of events) {
      const k = makeKey(e);
      if (!m.has(k)) m.set(k, []);
      m.get(k)!.push(e);
    }
    return m;
  };

  const lb = bucket(left);
  const rb = bucket(right);

  // Step 2: iterate all unique keys from union of both bucket maps.
  const allKeys = new Set([...lb.keys(), ...rb.keys()]);
  const rows: DiffRow[] = [];

  for (const k of allKeys) {
    const ls = lb.get(k) ?? [];
    const rs = rb.get(k) ?? [];
    const max = Math.max(ls.length, rs.length);

    for (let i = 0; i < max; i++) {
      const l = ls[i];
      const r = rs[i];

      if (l !== undefined && r !== undefined) {
        // Step 3a: paired — compare fields to determine status.
        const { equal, diffs } = compareFields(l, r);
        if (equal) {
          rows.push({
            status: "matched-equal",
            left: l,
            right: r,
            turnIndex: turnIndexOf(l),
          });
        } else {
          // Divergence cause = "fault" if one side is a failure event and the other isn't,
          // OR if any differing field name starts with "fault_".
          const faulty =
            isTraceFailureEvent(l) !== isTraceFailureEvent(r) ||
            diffs.some((d) => d.startsWith("fault_"));
          rows.push({
            status: "matched-divergent",
            left: l,
            right: r,
            turnIndex: turnIndexOf(l),
            divergenceCause: faulty ? "fault" : "field",
            differingFields: diffs,
          });
        }
      } else if (l !== undefined) {
        // Step 3b: surplus on left side → removed.
        rows.push({ status: "removed", left: l, turnIndex: turnIndexOf(l) });
      } else if (r !== undefined) {
        // Step 3c: surplus on right side → added.
        rows.push({ status: "added", right: r, turnIndex: turnIndexOf(r) });
      }
    }
  }

  // Step 4: sort by turnIndex asc, then by within-turn status order.
  rows.sort(
    (a, b) => a.turnIndex - b.turnIndex || STATUS_ORDER[a.status] - STATUS_ORDER[b.status],
  );

  return rows;
}
