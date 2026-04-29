// useRaceReplay — fetches a completed race trace by run_id.
//
// Design decisions:
//   D-48: Replay is a separate route /race/:run_id (not a toggle).
//         Phase 9 HEAT-03 ships the backend; Phase 8 ships the typed call signature only.
//   T-08-05: run_id is validated by isValidRunId (regex ^[a-zA-Z0-9_-]{1,64}$) before fetch.
//            Invalid run_id returns { trace: null, loading: false, error: "Invalid run_id" }.
//
// Cleanup pattern: `let active = true` guards all setState calls after unmount,
// mirroring the ReportDetailPage pattern (frontend/src/features/reports/ReportDetailPage.tsx:25-55).

import { useEffect, useState } from "react";
import { fetchRaceReplay, isValidRunId, type RaceReplayPayload } from "../../../lib/api/client";

export interface UseRaceReplayResult {
  trace: RaceReplayPayload | null;
  loading: boolean;
  error: string | null;
}

export function useRaceReplay(run_id: string | undefined): UseRaceReplayResult {
  const [trace, setTrace] = useState<RaceReplayPayload | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // No run_id — reset to idle state
    if (!run_id) {
      setLoading(false);
      setTrace(null);
      setError(null);
      return;
    }

    // T-08-05: Validate before fetch — reject path traversal / oversized IDs
    if (!isValidRunId(run_id)) {
      setLoading(false);
      setTrace(null);
      setError("Invalid run_id");
      return;
    }

    let active = true;
    setLoading(true);
    setError(null);

    void fetchRaceReplay(run_id)
      .then((payload) => {
        if (active) {
          setTrace(payload);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setTrace(null);
          setError(err instanceof Error ? err.message : "Failed to load replay.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false; // Cancel stale state writes on unmount / run_id change
    };
  }, [run_id]);

  return { trace, loading, error };
}
