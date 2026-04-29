// Page-state derivation function for RacePage.
// Maps ws_status + lane terminal flags + run_id → one of 12 UIRACE-02 PageState values.
// Truth table: 08-UI-SPEC.md Page State Matrix (lines 286-302).
// Decision: D-48 (run_id → replay), D-44 (derived state from event-tail + ws status).

import type { PageState, RaceLane, LaneState } from "../../lib/types/race";

export interface DerivePageStateInput {
  ws_status: "connecting" | "open" | "reconnecting" | "closed";
  lanes: Record<RaceLane, LaneState>;
  run_id: string | null;
  /** Optional pre-race countdown ticker value (seconds remaining). */
  countdown_seconds?: number | null;
  /** How many parallel runs are in flight: 1 for single-run, 5 for K=5 aggregate. */
  expected_n: number;
  /** True when the heatmap grid has at least one populated cell. */
  heatmap_has_data: boolean;
}

/**
 * Derive the current PageState from observable runtime signals.
 *
 * Priority ordering (highest wins):
 * 1. replay — run_id present overrides all other signals (D-48: bookmarkable replay route)
 * 2. ws-disconnected / ws-reconnecting — WS lifecycle preempts content states
 * 3. lane-failed — any lane has error event (before terminal tag is set)
 * 4. indeterminate / heatmap-empty / done — all lanes terminal (post-race final states)
 * 5. countdown — no events yet, countdown_seconds provided
 * 6. live-n1 / live-n5 — events flowing, lanes streaming
 * 7. pre-race — ws open, no events, no countdown
 */
export function derivePageState(input: DerivePageStateInput): PageState {
  // 1. Replay mode dominates — any run_id forces "replay" (D-48).
  if (input.run_id) return "replay";

  // 2. WS lifecycle states preempt content states.
  if (input.ws_status === "closed") return "ws-disconnected";
  if (input.ws_status === "reconnecting") return "ws-reconnecting";

  const laneStates = Object.values(input.lanes);

  // 3. Lane-failed: a lane has an error event (type="error") and has not been
  //    assigned a terminal_tag yet — indicates connection-level failure mid-race.
  const hasLaneFailed = laneStates.some(
    (l) =>
      l.terminal_tag === null &&
      l.events.some((e) => e.type === "error"),
  );
  if (hasLaneFailed) return "lane-failed";

  // 4. All-terminal states (post-race).
  const allTerminal = laneStates.every((l) => l.terminal_tag !== null);
  if (allTerminal) {
    // indeterminate: at least one lane unable to be classified.
    if (laneStates.some((l) => l.terminal_tag === "indeterminate")) return "indeterminate";
    // heatmap-empty: race complete but no heatmap data yet (D-47).
    if (!input.heatmap_has_data) return "heatmap-empty";
    // sparse-heatmap heuristic is deferred to Plan 05 (requires cell-coverage analysis).
    // Until then, terminal + heatmap_has_data → done.
    return "done";
  }

  // 5. Pre-race / countdown — no events received yet.
  const anyEvents = laneStates.some((l) => l.events.length > 0);
  if (!anyEvents) {
    if (input.countdown_seconds !== null && input.countdown_seconds !== undefined) {
      return "countdown";
    }
    return "pre-race";
  }

  // 6. Live states — events are flowing.
  return input.expected_n >= 5 ? "live-n5" : "live-n1";
}
