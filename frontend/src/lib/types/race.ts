// Shared race types. Closed-set unions consumed by useRaceStream reducer (Plan 03),
// RaceLaneCard / FailureStateBadge / HeatmapScaffold (Plans 04-05), and RacePage (Plan 06).
// Source-of-truth: 08-CONTEXT.md D-44, 08-UI-SPEC.md Page State Matrix.

export type FailureTag =
  | "recovered"
  | "gave_up"
  | "kept_going_without_noticing"
  | "kept_going_to_failure"
  | "indeterminate";

export type RaceLane = "pure_mcp" | "pure_a2a" | "hybrid";

// 12 page states from UIRACE-02 / 08-UI-SPEC.md Page State Matrix.
export type PageState =
  | "pre-race"
  | "countdown"
  | "live-n1"
  | "live-n5"
  | "done"
  | "replay"
  | "sparse-heatmap"
  | "ws-disconnected"
  | "ws-reconnecting"
  | "indeterminate"
  | "lane-failed"
  | "heatmap-empty";

// Closed event union from Phase 6/7 ws contract (TRC-04, RACE-03).
// Each event carries per-lane turn_index (TRC-04). Plan 03 reducer dispatches on `type`.
export type RaceEvent =
  | { type: "tick"; lane: RaceLane; turn_index: number; t_ms: number }
  | { type: "tool_call"; lane: RaceLane; turn_index: number; tool_name: string; status: string; t_call_ms: number; error_kind?: string }
  | { type: "agent_msg"; lane: RaceLane; turn_index: number; sender: string; recipient: string; content: string; t_ms: number }
  | { type: "fault_injected"; lane: RaceLane; turn_index: number; fault_id: string; fault_kind: string; target: string; t_inject_ms: number }
  | { type: "fault_observed"; lane: RaceLane; turn_index: number; fault_id: string; evidence: string; wasted_tokens_before_detection: number; t_observed_ms: number }
  | { type: "done"; lane: RaceLane; turn_index: number; tag: FailureTag; headline: string }
  | { type: "error"; lane: RaceLane; turn_index: number; message: string }
  | { type: "race_done"; turn_index: number }
  | { type: "ws_closed" }
  | { type: "ws_error" };

export interface LaneState {
  lane: RaceLane;
  last_turn_index: number;
  ttff_ms: number | null;
  recovered_count: number;
  total_count: number;
  faults: Array<{ fault_id: string; fault_kind: string; target: string; observed: boolean }>;
  events: RaceEvent[]; // capped feed (last N)
  terminal_tag: FailureTag | null;
  headline: string | null;
}

export interface RaceState {
  pageState: PageState;
  lanes: Record<RaceLane, LaneState>;
  ws_status: "connecting" | "open" | "reconnecting" | "closed";
  run_id: string | null; // null in live mode, set in replay mode
}
