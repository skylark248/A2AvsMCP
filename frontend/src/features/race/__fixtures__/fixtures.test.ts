// Invariant test: derivePageState(fixture) === fixture.pageState for each of 12 fixtures.
// This locks the fixture-vs-derivation agreement contract for all UIRACE-02 page states.

import { describe, test, expect } from "vitest";
import { fixturesByPageState } from "./raceStateFixtures";
import { derivePageState } from "../pageState";
import type { PageState } from "../../../lib/types/race";

const ALL: PageState[] = [
  "pre-race", "countdown", "live-n1", "live-n5", "done", "replay",
  "sparse-heatmap", "ws-disconnected", "ws-reconnecting", "indeterminate",
  "lane-failed", "heatmap-empty",
];

describe("fixture/derivePageState invariant", () => {
  test.each(ALL)("fixture %s round-trips through derivePageState", (key) => {
    const fixture = fixturesByPageState[key];
    // For "done" / "replay" / "sparse-heatmap" / "heatmap-empty" the derivation depends on heatmap_has_data;
    // pass the value that produces the expected key per UI-SPEC Page State Matrix.
    const heatmap_has_data = key === "sparse-heatmap" || key === "done";
    const derived = derivePageState({
      ws_status: fixture.ws_status,
      lanes: fixture.lanes,
      run_id: fixture.run_id,
      expected_n: key === "live-n5" ? 5 : 1,
      heatmap_has_data,
      countdown_seconds: key === "countdown" ? 5 : null,
    });
    expect(derived).toBe(key);
  });
});
