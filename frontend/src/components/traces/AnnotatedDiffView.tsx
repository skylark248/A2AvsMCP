import { Box, Chip, Grid, Paper, Stack, Tooltip, Typography } from "@mui/material";
import { useMemo, useState } from "react";

import { JsonTree } from "../../lib/trace/JsonTree";
import { failureTagColor, getProtocolColor, toneColor } from "../../lib/trace/eventColors";
import { traceEventProtocol, traceLabel } from "../../lib/trace/utils";
import type { TraceEvent } from "../../lib/types/api";
import { alignTraces, type DiffRow, type DiffStatus } from "./diffAlign";

// ---------------------------------------------------------------------------
// W-6 mitigation: stable empty-array reference.
// Callers should pass `resultA?.trace ?? EMPTY_EVENTS` (not inline `?? []`) to
// keep useMemo memoization stable across renders.
// ---------------------------------------------------------------------------
export const EMPTY_EVENTS: readonly TraceEvent[] = [];

// ---------------------------------------------------------------------------
// Public interface
// ---------------------------------------------------------------------------

/**
 * Props for AnnotatedDiffView.
 *
 * @param leftEvents  Trace A events (typically MCP). Pass `resultA?.trace ?? EMPTY_EVENTS`
 *                    (not inline `?? []`) to keep useMemo stable across renders (W-6).
 * @param rightEvents Trace B events (typically A2A). Same stability recommendation.
 * @param pinnedEventId   reserved for cross-view parity with TraceExplorer (D-82);
 *                        diff view does not pin per UI-SPEC line 216
 * @param onPinEvent      reserved for cross-view parity with TraceExplorer (D-82);
 *                        diff view does not pin per UI-SPEC line 216
 */
export interface AnnotatedDiffViewProps {
  leftEvents: TraceEvent[];
  rightEvents: TraceEvent[];
  leftProtocolLabel?: string;
  rightProtocolLabel?: string;
  /** reserved for cross-view parity with TraceExplorer (D-82); diff view does not pin per UI-SPEC line 216 */
  pinnedEventId?: string | null;
  /** reserved for cross-view parity with TraceExplorer (D-82); diff view does not pin per UI-SPEC line 216 */
  onPinEvent?: (eventId: string | null) => void;
}

// ---------------------------------------------------------------------------
// Module-level helpers
// ---------------------------------------------------------------------------

/** Returns the gutter glyph character for a given DiffStatus. */
function getStatusGlyph(status: DiffStatus): string {
  switch (status) {
    case "added":
      return "+";
    case "removed":
      return "−"; // "−" minus sign
    case "matched-divergent":
      return "≠"; // "≠" not-equal
    case "matched-equal":
      return "";
  }
}

/** Returns the locked Copywriting Contract tooltip copy for a DiffRow (UI-SPEC lines 247-253). */
function getStatusTooltip(row: DiffRow): string | null {
  switch (row.status) {
    case "added":
      return "Only in Trace B — this step did not occur in Trace A.";
    case "removed":
      return "Only in Trace A — Trace B skipped this step.";
    case "matched-divergent":
      if (row.divergenceCause === "fault") {
        return "Fault observed on one side only — one protocol noticed a failure the other didn't.";
      }
      return "Same step, different details — fields differ between traces.";
    case "matched-equal":
      return null;
  }
}

/**
 * Returns the sx decoration object for a diff row based on its status and divergenceCause.
 * Sources colors strictly from failureTagColor / toneColor (D-84 / Phase 8 single-source contract).
 */
function getRowSx(row: DiffRow): Record<string, unknown> {
  switch (row.status) {
    case "added":
      return { backgroundColor: failureTagColor.recovered.bg };
    case "removed":
      return { backgroundColor: failureTagColor.gave_up.bg };
    case "matched-divergent":
      if (row.divergenceCause === "fault") {
        return {
          borderLeft: "2px solid",
          borderLeftColor: failureTagColor.kept_going_to_failure.text,
        };
      }
      return {
        borderLeft: "2px solid",
        borderLeftColor: toneColor.warning,
      };
    case "matched-equal":
      return {};
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export function AnnotatedDiffView({
  leftEvents,
  rightEvents,
  leftProtocolLabel = "MCP — Trace A",
  rightProtocolLabel = "A2A — Trace B",
  pinnedEventId: _pinnedEventId,
  onPinEvent: _onPinEvent,
}: AnnotatedDiffViewProps) {
  const rows = useMemo(
    () => alignTraces(leftEvents, rightEvents),
    [leftEvents, rightEvents],
  );
  const [expandedRowKey, setExpandedRowKey] = useState<string | null>(null);

  // ---------------------------------------------------------------------------
  // Empty state
  // ---------------------------------------------------------------------------
  if (leftEvents.length === 0 && rightEvents.length === 0) {
    return (
      <Paper
        elevation={0}
        sx={{
          borderRadius: 2,
          border: "1px solid rgba(16,32,51,0.08)",
          backgroundColor: "background.paper",
          p: 4,
          textAlign: "center",
        }}
      >
        <Typography variant="body2" color="text.disabled">
          No events to compare
        </Typography>
        <Typography variant="body2" color="text.disabled">
          Run both protocols to compare traces.
        </Typography>
      </Paper>
    );
  }

  // ---------------------------------------------------------------------------
  // Determine column header protocol colors.
  // getProtocolColor accepts any string; fall back to 'mcp'/'a2a' defaults when
  // the respective side is empty (only one side has events).
  // ---------------------------------------------------------------------------
  const leftProto = leftEvents.length > 0
    ? traceEventProtocol(leftEvents[0])
    : "mcp";
  const rightProto = rightEvents.length > 0
    ? traceEventProtocol(rightEvents[0])
    : "a2a";

  // ---------------------------------------------------------------------------
  // Main render
  // ---------------------------------------------------------------------------
  return (
    <Paper
      elevation={0}
      role="table"
      aria-label="Annotated trace diff"
      sx={{
        borderRadius: 2,
        border: "1px solid rgba(16,32,51,0.08)",
        backgroundColor: "background.paper",
        overflow: "hidden",
      }}
    >
      {/* Header strip — 40px tall, two columns (UI-SPEC line 132-135) */}
      <Grid container sx={{ px: 2, py: 1, alignItems: "center" }}>
        <Grid size={6}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography
              variant="overline"
              sx={{ color: getProtocolColor(leftProto), fontWeight: 600 }}
            >
              {leftProtocolLabel}
            </Typography>
            <Chip size="small" label={leftEvents.length} />
          </Stack>
        </Grid>
        <Grid size={6}>
          <Stack direction="row" spacing={1} alignItems="center">
            <Typography
              variant="overline"
              sx={{ color: getProtocolColor(rightProto), fontWeight: 600 }}
            >
              {rightProtocolLabel}
            </Typography>
            <Chip size="small" label={rightEvents.length} />
          </Stack>
        </Grid>
      </Grid>

      {/* Body — CSS grid: gutter | left | gutter | right (UI-SPEC line 134) */}
      <Box
        role="rowgroup"
        sx={{
          display: "grid",
          gridTemplateColumns: "28px 1fr 28px 1fr",
          rowGap: 0.5,
          px: 0,
        }}
      >
        {rows.map((row, idx) => {
          const rowKey = `${row.turnIndex}-${row.status}-${idx}`;
          const isExpanded = expandedRowKey === rowKey;
          const glyph = getStatusGlyph(row.status);
          const tooltip = getStatusTooltip(row);
          const rowSx = getRowSx(row);
          // Role-first label sourced from whichever side is present (D-78)
          const labelSource = row.left ?? row.right;
          const label = labelSource ? traceLabel(labelSource) : "";

          return (
            <Box key={rowKey} sx={{ display: "contents" }}>
              {/*
                W-3 mitigation: render the gutter chip in EXACTLY ONE gutter per row to
                avoid duplicate glyphs on matched-divergent rows. Layout rule:
                  - "removed" → Gutter A (left) only.
                  - "added"   → Gutter B (right) only.
                  - "matched-divergent" → Gutter A only (stable layout choice).
                  - "matched-equal"     → no glyph (both gutters empty).
              */}

              {/* Gutter A — removed and matched-divergent show here */}
              <Box sx={{ ...rowSx, p: 0.5, textAlign: "center" }}>
                {(row.status === "removed" || row.status === "matched-divergent") && glyph !== "" ? (
                  <Tooltip title={tooltip ?? ""}>
                    <Chip
                      size="small"
                      label={glyph}
                      data-status={row.status}
                      sx={{
                        minWidth: 20,
                        height: 20,
                        ...(row.status === "removed"
                          ? {
                              backgroundColor: failureTagColor.gave_up.bg,
                              color: failureTagColor.gave_up.text,
                            }
                          : { backgroundColor: "transparent" }),
                      }}
                    />
                  </Tooltip>
                ) : null}
              </Box>

              {/* Left row body */}
              <Box
                role="row"
                tabIndex={0}
                data-row-status={row.status}
                data-divergence-cause={row.divergenceCause ?? ""}
                onClick={() => setExpandedRowKey(isExpanded ? null : rowKey)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setExpandedRowKey(isExpanded ? null : rowKey);
                  }
                }}
                sx={{ ...rowSx, p: 1, cursor: row.left ? "pointer" : "default" }}
              >
                {row.left ? (
                  <Stack spacing={0.5}>
                    <Typography variant="body2">{label}</Typography>
                    {isExpanded ? <JsonTree data={row.left} /> : null}
                  </Stack>
                ) : null}
              </Box>

              {/* Gutter B — only "added" rows render their chip here per W-3 */}
              <Box sx={{ ...rowSx, p: 0.5, textAlign: "center" }}>
                {row.status === "added" && glyph !== "" ? (
                  <Tooltip title={tooltip ?? ""}>
                    <Chip
                      size="small"
                      label={glyph}
                      data-status={row.status}
                      sx={{
                        minWidth: 20,
                        height: 20,
                        backgroundColor: failureTagColor.recovered.bg,
                        color: failureTagColor.recovered.text,
                      }}
                    />
                  </Tooltip>
                ) : null}
              </Box>

              {/* Right row body */}
              <Box
                role="row"
                tabIndex={0}
                data-row-status={row.status}
                data-divergence-cause={row.divergenceCause ?? ""}
                onClick={() => setExpandedRowKey(isExpanded ? null : rowKey)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    setExpandedRowKey(isExpanded ? null : rowKey);
                  }
                }}
                sx={{ ...rowSx, p: 1, cursor: row.right ? "pointer" : "default" }}
              >
                {row.right ? (
                  <Stack spacing={0.5}>
                    <Typography variant="body2">{label}</Typography>
                    {isExpanded ? <JsonTree data={row.right} /> : null}
                  </Stack>
                ) : null}
              </Box>
            </Box>
          );
        })}
      </Box>
    </Paper>
  );
}
