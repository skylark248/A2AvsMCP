// Twelve fully-specified RaceState fixtures — one per PageState.
// Each fixture's pageState key MUST round-trip through derivePageState (locked by fixtures.test.ts).
// Used by: RacePage.test.tsx (integration), fixtures.test.ts (invariant), responsive + a11y tests.

import type { RaceState, PageState, LaneState, RaceLane } from "../../../lib/types/race";

function lane(overrides: Partial<LaneState>): LaneState {
  return {
    lane: "pure_mcp",
    last_turn_index: -1,
    ttff_ms: null,
    recovered_count: 0,
    total_count: 0,
    faults: [],
    events: [],
    terminal_tag: null,
    headline: null,
    ...overrides,
  };
}

const emptyLanes: Record<RaceLane, LaneState> = {
  pure_mcp: lane({ lane: "pure_mcp" }),
  pure_a2a: lane({ lane: "pure_a2a" }),
  hybrid: lane({ lane: "hybrid" }),
};

export const fixturesByPageState: Record<PageState, RaceState> = {
  "pre-race": {
    pageState: "pre-race",
    ws_status: "open",
    run_id: null,
    lanes: { ...emptyLanes },
  },

  "countdown": {
    pageState: "countdown",
    ws_status: "open",
    run_id: null,
    lanes: { ...emptyLanes },
  },

  "live-n1": {
    pageState: "live-n1",
    ws_status: "open",
    run_id: null,
    lanes: {
      pure_mcp: lane({ lane: "pure_mcp", last_turn_index: 2, events: [{ type: "tick", lane: "pure_mcp", turn_index: 2, t_ms: 100 }] }),
      pure_a2a: lane({ lane: "pure_a2a" }),
      hybrid: lane({ lane: "hybrid" }),
    },
  },

  "live-n5": {
    pageState: "live-n5",
    ws_status: "open",
    run_id: null,
    lanes: {
      pure_mcp: lane({ lane: "pure_mcp", last_turn_index: 4, events: [{ type: "tick", lane: "pure_mcp", turn_index: 4, t_ms: 400 }] }),
      pure_a2a: lane({ lane: "pure_a2a", last_turn_index: 3, events: [{ type: "tick", lane: "pure_a2a", turn_index: 3, t_ms: 300 }] }),
      hybrid:   lane({ lane: "hybrid",   last_turn_index: 5, events: [{ type: "tick", lane: "hybrid",   turn_index: 5, t_ms: 500 }] }),
    },
  },

  "done": {
    pageState: "done",
    ws_status: "open",
    run_id: null,
    lanes: {
      pure_mcp: lane({ lane: "pure_mcp", terminal_tag: "recovered",              headline: "Recovered cleanly",         ttff_ms: 1200, recovered_count: 5, total_count: 5, last_turn_index: 12, events: [{ type: "done", lane: "pure_mcp", turn_index: 12, tag: "recovered",              headline: "Recovered cleanly" }] }),
      pure_a2a: lane({ lane: "pure_a2a", terminal_tag: "gave_up",                headline: "Gave up after 4 turns",     ttff_ms: 800,  recovered_count: 0, total_count: 5, last_turn_index: 8,  events: [{ type: "done", lane: "pure_a2a", turn_index: 8,  tag: "gave_up",                headline: "Gave up after 4 turns" }] }),
      hybrid:   lane({ lane: "hybrid",   terminal_tag: "kept_going_to_failure",  headline: "Kept going to failure",     ttff_ms: 1500, recovered_count: 1, total_count: 5, last_turn_index: 14, events: [{ type: "done", lane: "hybrid",   turn_index: 14, tag: "kept_going_to_failure",  headline: "Kept going to failure" }] }),
    },
  },

  "replay": {
    pageState: "replay",
    ws_status: "open",
    run_id: "abc12345",
    lanes: {
      pure_mcp: lane({ lane: "pure_mcp", terminal_tag: "recovered",              headline: "Recovered cleanly",         ttff_ms: 1200, recovered_count: 5, total_count: 5, last_turn_index: 12 }),
      pure_a2a: lane({ lane: "pure_a2a", terminal_tag: "gave_up",                headline: "Gave up after 4 turns",     ttff_ms: 800,  recovered_count: 0, total_count: 5, last_turn_index: 8 }),
      hybrid:   lane({ lane: "hybrid",   terminal_tag: "kept_going_to_failure",  headline: "Kept going to failure",     ttff_ms: 1500, recovered_count: 1, total_count: 5, last_turn_index: 14 }),
    },
  },

  "sparse-heatmap": {
    pageState: "sparse-heatmap",
    ws_status: "open",
    run_id: null,
    lanes: {
      pure_mcp: lane({ lane: "pure_mcp", terminal_tag: "recovered", headline: "Recovered (sparse)", ttff_ms: 1100, recovered_count: 1, total_count: 1, last_turn_index: 6 }),
      pure_a2a: lane({ lane: "pure_a2a", terminal_tag: "gave_up",   headline: "Gave up (sparse)",   ttff_ms: 900,  recovered_count: 0, total_count: 1, last_turn_index: 4 }),
      hybrid:   lane({ lane: "hybrid",   terminal_tag: "recovered", headline: "Recovered (sparse)", ttff_ms: 1300, recovered_count: 1, total_count: 1, last_turn_index: 7 }),
    },
  },

  "ws-disconnected": {
    pageState: "ws-disconnected",
    ws_status: "closed",
    run_id: null,
    lanes: { ...emptyLanes },
  },

  "ws-reconnecting": {
    pageState: "ws-reconnecting",
    ws_status: "reconnecting",
    run_id: null,
    lanes: { ...emptyLanes },
  },

  "indeterminate": {
    pageState: "indeterminate",
    ws_status: "open",
    run_id: null,
    lanes: {
      pure_mcp: lane({ lane: "pure_mcp", terminal_tag: "indeterminate", headline: "Indeterminate — insufficient signal", ttff_ms: 1000, recovered_count: 0, total_count: 1, last_turn_index: 5 }),
      pure_a2a: lane({ lane: "pure_a2a", terminal_tag: "recovered",     headline: "Recovered cleanly",                    ttff_ms: 900,  recovered_count: 1, total_count: 1, last_turn_index: 4 }),
      hybrid:   lane({ lane: "hybrid",   terminal_tag: "gave_up",       headline: "Gave up after 3 turns",                ttff_ms: 800,  recovered_count: 0, total_count: 1, last_turn_index: 3 }),
    },
  },

  "lane-failed": {
    pageState: "lane-failed",
    ws_status: "open",
    run_id: null,
    lanes: {
      pure_mcp: lane({ lane: "pure_mcp", last_turn_index: 3, events: [{ type: "error", lane: "pure_mcp", turn_index: 3, message: "Lane failed: tool error" }] }),
      pure_a2a: lane({ lane: "pure_a2a", last_turn_index: 4, events: [{ type: "tick",  lane: "pure_a2a", turn_index: 4, t_ms: 400 }] }),
      hybrid:   lane({ lane: "hybrid",   last_turn_index: 4, events: [{ type: "tick",  lane: "hybrid",   turn_index: 4, t_ms: 410 }] }),
    },
  },

  "heatmap-empty": {
    pageState: "heatmap-empty",
    ws_status: "open",
    run_id: null,
    lanes: {
      pure_mcp: lane({ lane: "pure_mcp", terminal_tag: "recovered", headline: "Recovered cleanly", ttff_ms: 1200, recovered_count: 1, total_count: 1, last_turn_index: 6 }),
      pure_a2a: lane({ lane: "pure_a2a", terminal_tag: "gave_up",   headline: "Gave up",           ttff_ms: 900,  recovered_count: 0, total_count: 1, last_turn_index: 4 }),
      hybrid:   lane({ lane: "hybrid",   terminal_tag: "recovered", headline: "Recovered cleanly", ttff_ms: 1100, recovered_count: 1, total_count: 1, last_turn_index: 5 }),
    },
  },
};
