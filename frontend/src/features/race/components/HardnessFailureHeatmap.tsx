/**
 * HardnessFailureHeatmap — HEAT-01 + HEAT-02 data-wired wrapper around the
 * Phase 8 HeatmapScaffold (D-46 + D-47).
 *
 * Owns:
 *   - API fetch via useRaceHeatmap()
 *   - backend → frontend hardness_type rename (LANDMINE 1)
 *   - "directional · n=3 tasks · v1" pill (UI-SPEC + ROADMAP success criterion 1)
 *   - 5-pill legend strip — always visible (HEAT-02)
 *   - data-driven footer reading model · seed · task_ids from API baseline (HEAT-02 contract)
 *
 * Grid rendering delegates to HeatmapScaffold — D-46 (CSS Grid + role=gridcell +
 * failureTagColor lookup) and D-47 (empty-state never-unmount) preserved by
 * passing `{}` to the scaffold when cells are empty.
 */

import type { ComponentType } from "react";
import { Box, Chip, Stack, Typography } from "@mui/material";

import { HeatmapScaffold, type HeatmapCells, type HardnessType } from "./HeatmapScaffold";
import { useRaceHeatmap } from "../hooks/useRaceHeatmap";
import { failureTagColor } from "../../../lib/trace/eventColors";
import type {
  FailureTag,
  HeatmapPayload,
  HardnessTypeBackend,
} from "../../../lib/types/race";

// LANDMINE 1: backend HardnessType.MULTI_SOURCE_SYNTHESIS = "multi_source"
// (race/types.py:26) but HeatmapScaffold types row keys as "multi_source_synthesis".
// Rename at the transform boundary so the scaffold never sees the backend short form.
const HARDNESS_BACKEND_TO_FRONTEND: Record<HardnessTypeBackend, HardnessType> = {
  long_chain: "long_chain",
  rate_pressure: "rate_pressure",
  schema_variance: "schema_variance",
  multi_source: "multi_source_synthesis",
};

function toHeatmapCells(payload: HeatmapPayload): HeatmapCells {
  const cells: HeatmapCells = {};
  for (const c of payload.cells) {
    const row = HARDNESS_BACKEND_TO_FRONTEND[c.hardness_type];
    if (!row) continue; // T-09-13: graceful degradation on unknown enum values
    cells[row] ??= {};
    cells[row]![c.lane] = {
      tag: c.dominant_tag,
      recoveryFraction: `${c.recovery_rate.num}/${c.recovery_rate.den}`,
    };
  }
  return cells;
}

export function HardnessFailureHeatmap() {
  const { data } = useRaceHeatmap();
  const cells = data ? toHeatmapCells(data) : {};

  return (
    <Box>
      {/* Directional pill — UI-SPEC + ROADMAP success criterion 1 */}
      <Chip
        color="secondary"
        label="directional · n=3 tasks · v1"
        sx={{ mb: 2 }}
      />

      {/* Phase 8 scaffold — D-46 + D-47 preserved (CSS Grid + role=gridcell) */}
      <HeatmapScaffold cells={cells} />

      {/* 5-pill legend strip — always visible (HEAT-02) */}
      <Stack direction="row" spacing={1} sx={{ mt: 2 }} flexWrap="wrap" useFlexGap>
        {(Object.keys(failureTagColor) as FailureTag[]).map((tag) => {
          const cfg = failureTagColor[tag];
          const Icon = cfg.Icon as ComponentType;
          return (
            <Chip
              key={tag}
              icon={<Icon />}
              label={cfg.label}
              sx={{ bgcolor: cfg.bg, color: cfg.text }}
            />
          );
        })}
      </Stack>

      {/* Footer — data-driven from API baseline payload (HEAT-02 contract).
          T-09-15: text-node interpolation; React escapes any HTML in task_ids.
          T-09-16: reads data.baseline on every render — no client-side caching. */}
      {data ? (
        <Typography
          variant="caption"
          sx={{ color: "text.secondary", display: "block", mt: 1 }}
        >
          {data.baseline.model} · {data.baseline.seed} · {data.baseline.task_ids.join(", ")}
        </Typography>
      ) : null}
    </Box>
  );
}
