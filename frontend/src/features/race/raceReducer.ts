// Pure reducer for the race live-stream state machine.
// Dispatched on every WebSocket event from useRaceStream (Plan 03).
// No React dependencies — testable in isolation (D-44).
// Cursor monotonicity: last_turn_index never regresses (D-45).
// Events feed capped at EVENTS_FEED_CAP to bound memory (T-08-09).

import type { RaceEvent, RaceLane, RaceState, LaneState } from "../../lib/types/race";

const EVENTS_FEED_CAP = 200;

const LANES: RaceLane[] = ["pure_mcp", "pure_a2a", "hybrid"];

function emptyLane(lane: RaceLane): LaneState {
  return {
    lane,
    last_turn_index: -1,
    ttff_ms: null,
    recovered_count: 0,
    total_count: 0,
    faults: [],
    events: [],
    terminal_tag: null,
    headline: null,
  };
}

export const initialRaceState: RaceState = {
  pageState: "pre-race",
  lanes: Object.fromEntries(LANES.map((l) => [l, emptyLane(l)])) as Record<RaceLane, LaneState>,
  ws_status: "connecting",
  run_id: null,
};

function updateLane(
  state: RaceState,
  lane: RaceLane,
  mutator: (l: LaneState) => LaneState,
): RaceState {
  return { ...state, lanes: { ...state.lanes, [lane]: mutator(state.lanes[lane]) } };
}

function appendEvent(lane: LaneState, event: RaceEvent): LaneState {
  const events = [...lane.events, event].slice(-EVENTS_FEED_CAP);
  return { ...lane, events };
}

export function raceReducer(state: RaceState, event: RaceEvent): RaceState {
  switch (event.type) {
    case "tick": {
      return updateLane(state, event.lane, (l) => ({
        ...appendEvent(l, event),
        last_turn_index: Math.max(l.last_turn_index, event.turn_index),
      }));
    }

    case "tool_call": {
      return updateLane(state, event.lane, (l) => ({
        ...appendEvent(l, event),
        last_turn_index: Math.max(l.last_turn_index, event.turn_index),
      }));
    }

    case "agent_msg": {
      return updateLane(state, event.lane, (l) => ({
        ...appendEvent(l, event),
        last_turn_index: Math.max(l.last_turn_index, event.turn_index),
      }));
    }

    case "fault_injected": {
      return updateLane(state, event.lane, (l) => ({
        ...appendEvent(l, event),
        last_turn_index: Math.max(l.last_turn_index, event.turn_index),
        faults: [
          ...l.faults,
          {
            fault_id: event.fault_id,
            fault_kind: event.fault_kind,
            target: event.target,
            observed: false,
          },
        ],
      }));
    }

    case "fault_observed": {
      return updateLane(state, event.lane, (l) => {
        const faults = l.faults.map((f) =>
          f.fault_id === event.fault_id ? { ...f, observed: true } : f,
        );
        // ttff_ms is set exactly once — first fault observation for the lane wins (D-45 semantics)
        const ttff_ms = l.ttff_ms === null ? event.t_observed_ms : l.ttff_ms;
        return {
          ...appendEvent(l, event),
          last_turn_index: Math.max(l.last_turn_index, event.turn_index),
          faults,
          ttff_ms,
        };
      });
    }

    case "done": {
      return updateLane(state, event.lane, (l) => ({
        ...appendEvent(l, event),
        last_turn_index: Math.max(l.last_turn_index, event.turn_index),
        terminal_tag: event.tag,
        headline: event.headline,
      }));
    }

    case "error": {
      // Pre-classification failure signal — append to events feed; terminal_tag stays null.
      // derivePageState (Plan 02) reads the error event presence + terminal_tag===null to derive "lane-failed".
      return updateLane(state, event.lane, (l) => ({
        ...appendEvent(l, event),
        last_turn_index: Math.max(l.last_turn_index, event.turn_index),
      }));
    }

    case "race_done": {
      // Session-level signal — no per-lane mutation.
      // derivePageState (Plan 02) reads this from the event feed when checking "done" state.
      return state;
    }

    case "ws_closed":
    case "ws_error": {
      // Preserve all lane state; only update connection status.
      return { ...state, ws_status: "closed" };
    }

    default: {
      // Exhaustive check — TypeScript ensures all event types are handled.
      const _exhaustive: never = event;
      void _exhaustive;
      return state;
    }
  }
}
