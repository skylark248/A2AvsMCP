/**
 * HeatmapScaffold — CSS Grid heatmap with rows=HardnessType, cols=lanes.
 * UIRACE-02, UIRACE-03, UIRACE-04, UIRACE-06 | D-46, D-47
 *
 * 4-channel cell encoding per UIRACE-04:
 *   (1) backgroundColor from failureTagColor[tag].bg
 *   (2) visible Icon rendered inline (data-testid="heatmap-cell-icon")
 *   (3) visible recovery fraction text (e.g. "12/15")
 *   (4) sr-only tag-name label via @mui/utils visuallyHidden (canonical accessible-hide helper)
 *
 * Empty-state (D-47): full grid scaffold stays mounted; absolute-positioned
 * overlay copy appears over muted neutral cells.
 */

import type React from "react";
import { Box, Stack, Typography } from "@mui/material";
import { visuallyHidden } from "@mui/utils"; // canonical accessible-hide helper from @mui/utils
import { failureTagColor } from "../../../lib/trace/eventColors";
import type { FailureTag, RaceLane } from "../../../lib/types/race";

export type HardnessType =
  | "long_chain"
  | "rate_pressure"
  | "schema_variance"
  | "multi_source_synthesis";

const HARDNESS_ORDER: HardnessType[] = [
  "long_chain",
  "rate_pressure",
  "schema_variance",
  "multi_source_synthesis",
];

const HARDNESS_LABEL: Record<HardnessType, string> = {
  long_chain: "Long Chain",
  rate_pressure: "Rate Pressure",
  schema_variance: "Schema Variance",
  multi_source_synthesis: "Multi-Source Synthesis",
};

const LANE_ORDER: RaceLane[] = ["pure_mcp", "pure_a2a", "hybrid"];

const LANE_LABEL: Record<RaceLane, string> = {
  pure_mcp: "Pure MCP",
  pure_a2a: "Pure A2A",
  hybrid: "Hybrid",
};

export interface HeatmapCell {
  tag: FailureTag;
  /** Visible primary text channel, e.g. "12/15" (UIRACE-04 channel 3) */
  recoveryFraction: string;
}

export type HeatmapCells = Partial<
  Record<HardnessType, Partial<Record<RaceLane, HeatmapCell>>>
>;

export function HeatmapScaffold({ cells }: { cells: HeatmapCells }) {
  const isEmpty =
    Object.keys(cells).length === 0 ||
    HARDNESS_ORDER.every(
      (h) => !cells[h] || Object.keys(cells[h]!).length === 0,
    );

  return (
    <Box sx={{ position: "relative" }} data-testid="heatmap-scaffold">
      {/* CSS Grid scaffold — NEVER unmounts in empty-state (D-47) */}
      <Box
        role="grid"
        aria-label="Hardness vs Failure Heatmap"
        sx={{
          display: "grid",
          gridTemplateColumns: `auto repeat(${LANE_ORDER.length}, 1fr)`,
          /* 44px min row height — UIRACE-06 / WCAG 2.5.5 touch target */
          gridTemplateRows: `auto repeat(${HARDNESS_ORDER.length}, minmax(44px, 1fr))`,
          gap: 0, // cells touch edge-to-edge (UIRACE-03)
          border: "1px solid rgba(16, 32, 51, 0.08)",
        }}
      >
        {/* ── Header row: empty corner + 3 lane labels ── */}
        <Box role="columnheader" aria-hidden="true" sx={{ p: 1 }} />
        {LANE_ORDER.map((lane) => (
          <Box
            key={lane}
            role="columnheader"
            sx={{ p: 1, fontWeight: 700, textAlign: "center" }}
          >
            {LANE_LABEL[lane]}
          </Box>
        ))}

        {/* ── Body rows: 4 hardness × 3 lanes ── */}
        {HARDNESS_ORDER.map((row) => (
          <Box key={`row-${row}`} sx={{ display: "contents" }}>
            {/* Row header */}
            <Box role="rowheader" sx={{ p: 1, fontWeight: 700 }}>
              {HARDNESS_LABEL[row]}
            </Box>

            {LANE_ORDER.map((lane) => {
              const cell = cells[row]?.[lane];
              const cfg = cell ? failureTagColor[cell.tag] : null;
              const Icon = cfg?.Icon;

              return (
                <Box
                  key={`cell-${row}-${lane}`}
                  role="gridcell"
                  tabIndex={0}
                  data-testid={`heatmap-cell-${row}-${lane}`}
                  sx={{
                    /* CHANNEL 1 (color): bg from failureTagColor; neutral muted in empty (D-47) */
                    bgcolor: cfg ? cfg.bg : "action.hover",
                    color: cfg ? cfg.text : "text.disabled",
                    /* UIRACE-03 cell radius=0 — cells touch */
                    borderRadius: 0,
                    p: 1,
                    /* UIRACE-06 / WCAG 2.5.5 — 44px touch target */
                    minHeight: 44,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                    /* Focus-visible 3px primary outline (UI-SPEC Interaction Contract) */
                    "&:focus-visible": {
                      outline: "3px solid #17475f",
                      outlineOffset: 2,
                      "@media (prefers-contrast: more)": {
                        /* UI-SPEC high-contrast widen to 4px */
                        outline: "4px solid #17475f",
                      },
                    },
                  }}
                >
                  {cell && Icon ? (
                    <Stack direction="row" spacing={0.5} alignItems="center">
                      {/* CHANNEL 2: visible Icon rendered inline — aria-hidden; sighted channel */}
                      <Box
                        component="span"
                        data-testid="heatmap-cell-icon"
                        aria-hidden="true"
                      >
                        <Icon fontSize="small" />
                      </Box>

                      {/* CHANNEL 3: visible recovery-fraction — primary text for sighted users */}
                      <Typography variant="caption" sx={{ fontWeight: 600 }}>
                        {cell.recoveryFraction}
                      </Typography>

                      {/* CHANNEL 4: sr-only tag-name label via @mui/utils visuallyHidden.
                          Applied as inline style (not sx) so jsdom + AT can inspect
                          position:absolute and width:1px directly on the element. */}
                      <span style={visuallyHidden as React.CSSProperties}>
                        {cfg!.label}
                      </span>
                    </Stack>
                  ) : null}
                </Box>
              );
            })}
          </Box>
        ))}
      </Box>

      {/* heatmap-empty overlay (D-47): grid stays mounted; copy layered absolutely */}
      {isEmpty ? (
        <Box
          data-testid="heatmap-empty-overlay"
          sx={{
            position: "absolute",
            inset: 0,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            pointerEvents: "none",
            bgcolor: "rgba(243, 239, 231, 0.85)",
          }}
        >
          {/* D-47 + UI-SPEC Copywriting — verbatim */}
          <Typography variant="h3" sx={{ color: "primary.main" }}>
            No runs yet
          </Typography>
          <Typography variant="body2" sx={{ color: "text.secondary" }}>
            Launch a race to populate the heatmap.
          </Typography>
        </Box>
      ) : null}
    </Box>
  );
}
