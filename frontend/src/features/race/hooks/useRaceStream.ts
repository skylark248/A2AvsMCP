// useRaceStream — owns the WebSocket connection + reducer state for live race mode.
//
// Design decisions:
//   D-44: useReducer over closed RaceEvent union; no global store/provider.
//   D-45: Reconnect resume via per-lane last_turn_index in WS URL query params.
//   T-08-16: `enabled` flag (default true) gates the WebSocket open.
//            Consumer passes `enabled=false` to skip ws bring-up (e.g. Plan 06 mobile branch)
//            without violating React rules-of-hooks — hook must always be called.
//
// WebSocket URL format on (re)connect (Phase 14 B2 fix):
//   ws://<host>/api/race/ws?run_id=<runId>&pure_mcp=<N>&pure_a2a=<N>&hybrid=<N>
//   where N = last_turn_index per lane (-1 on fresh connect, ≥0 after cursor advance).
//   run_id is mandatory per backend; encodeURIComponent applied (T-14-02-01).

import { useEffect, useReducer, useRef } from "react";
import { initialRaceState, raceReducer } from "../raceReducer";
import type { RaceLane, RaceState } from "../../../lib/types/race";

const WS_PATH = "/api/race/ws";
const LANES: RaceLane[] = ["pure_mcp", "pure_a2a", "hybrid"];

function buildWsUrl(runId: string, state: RaceState): string {
  // Encode per-lane cursors as query string (D-45 reconnect resume).
  const qs = LANES.map((l) => `${l}=${state.lanes[l].last_turn_index}`).join("&");
  // Derive ws/wss from current page protocol (T-08-10: same-origin).
  const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
  // B2 fix: run_id is the first query param (T-14-02-01: encodeURIComponent as belt-and-suspenders).
  return `${proto}//${window.location.host}${WS_PATH}?run_id=${encodeURIComponent(runId)}&${qs}`;
}

/**
 * Subscribes to the live race WebSocket and reduces incoming events into RaceState.
 *
 * @param runId - The run_id returned from POST /api/race/run. Injected into the WS URL
 *   as run_id=<runId>. When runId changes, the current socket is closed and a new one
 *   is opened. Phase 14 B2 gap closure — backend requires run_id as a mandatory query param.
 * @param enabled - When false, the WebSocket is NOT opened and the effect returns early.
 *   Defaults to true. Pass `enabled=false` in the mobile-summary branch (Plan 06) to gate
 *   the WS connection without violating React rules-of-hooks (T-08-16).
 */
export function useRaceStream(runId: string = "", enabled: boolean = true): RaceState {
  const [state, dispatch] = useReducer(raceReducer, initialRaceState);

  // Stable ref to latest state — used inside the effect to capture current cursors
  // when building the reconnect URL without making the effect depend on `state`.
  const stateRef = useRef(state);
  stateRef.current = state;

  useEffect(() => {
    if (!enabled) return; // T-08-16 gate — no WS when explicitly disabled

    let active = true;
    const url = buildWsUrl(runId, stateRef.current);
    const socket = new WebSocket(url);

    socket.onmessage = (ev) => {
      if (!active) return;
      try {
        // eslint-disable-next-line @typescript-eslint/no-unsafe-argument
        dispatch(JSON.parse(ev.data as string));
      } catch {
        // Drop malformed payloads silently (T-08-07: untrusted ws input)
      }
    };

    socket.onerror = () => {
      if (active) dispatch({ type: "ws_error" });
    };

    socket.onclose = () => {
      if (active) dispatch({ type: "ws_closed" });
    };

    return () => {
      active = false;
      socket.close();
    };
  }, [enabled, runId]); // Re-run when enabled toggles or runId changes; reducer holds cursor state

  return state;
}
