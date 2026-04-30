/**
 * Phase 10 OG-02: annotation strip rendered ONLY when ?og=1&surface=heatmap.
 *
 * Renders the literal annotation contract:
 *   {runId} · {baseline.model} · seed={baseline.seed} · n={n} · {baseline.task_ids.join(", ")}
 *
 * The strip is mounted from HardnessFailureHeatmap when ogAnnotation && runId && data
 * (additive — preserves Phase 9 D-46 HeatmapScaffold + D-47 empty-state never-unmount).
 */

import { Box, Typography } from "@mui/material";
import type { HeatmapPayload } from "../../../lib/types/race";

interface HeatmapAnnotationStripProps {
  runId: string;
  baseline: HeatmapPayload["baseline"];
  n: number;
}

export function HeatmapAnnotationStrip({ runId, baseline, n }: HeatmapAnnotationStripProps) {
  const taskIds = baseline.task_ids.join(", ");
  return (
    <Box
      data-testid="heatmap-annotation-strip"
      sx={{
        bgcolor: "background.paper",
        borderTop: "2px solid",
        borderColor: "primary.main",
        p: 2,
        mt: 2,
      }}
    >
      <Typography
        variant="caption"
        sx={{ color: "text.primary", fontFamily: "monospace", whiteSpace: "nowrap" }}
      >
        {runId} · {baseline.model} · seed={baseline.seed} · n={n} · {taskIds}
      </Typography>
    </Box>
  );
}
