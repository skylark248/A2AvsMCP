// useRaceHeatmap — fetches the closing-artifact heatmap aggregate (HEAT-01 / HEAT-02).
//
// Mirrors useRaceReplay's let-active-true cleanup pattern verbatim (Pattern 4).
// Singleton endpoint (no params), so the effect runs once on mount.

import { useEffect, useState } from "react";

import { fetchRaceHeatmap } from "../../../lib/api/client";
import type { HeatmapPayload } from "../../../lib/types/race";

export interface UseRaceHeatmapResult {
  data: HeatmapPayload | null;
  loading: boolean;
  error: string | null;
}

export function useRaceHeatmap(): UseRaceHeatmapResult {
  const [data, setData] = useState<HeatmapPayload | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);

    void fetchRaceHeatmap()
      .then((payload) => {
        if (active) {
          setData(payload);
          setError(null);
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setData(null);
          setError(err instanceof Error ? err.message : "Failed to load heatmap.");
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });

    return () => {
      active = false; // Cancel stale state writes on unmount
    };
  }, []);

  return { data, loading, error };
}
