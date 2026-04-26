import CompareArrowsOutlinedIcon from "@mui/icons-material/CompareArrowsOutlined";
import HubOutlinedIcon from "@mui/icons-material/HubOutlined";
import PrecisionManufacturingOutlinedIcon from "@mui/icons-material/PrecisionManufacturingOutlined";
import RouteOutlinedIcon from "@mui/icons-material/RouteOutlined";
import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { ProtocolEnvelopeDrawer } from "../../components/traces/ProtocolEnvelopeDrawer";
import { ContentCardSkeleton, FilterCardSkeleton } from "../../components/loading/LoadingSkeletons";
import { fetchReportDetail, fetchReports } from "../../lib/api/client";
import { getProtocolColor, eventBorderColor } from "../../lib/trace/eventColors";
import { isA2AEvent, isTraceFailureEvent, traceEventProtocol, traceEventTone, traceLabel } from "../../lib/trace/utils";
import type { ReportSummary, RunResult, TraceEvent } from "../../lib/types/api";

const MODE_ORDER = ["baseline", "mcp", "a2a", "hybrid"] as const;

const BASELINE_ICON = { icon: <RouteOutlinedIcon fontSize="small" />, protocol: "No protocol" };

const MODE_ICONS: Record<string, { icon: React.ReactNode; protocol: string }> = {
  baseline: BASELINE_ICON,
  mcp: { icon: <PrecisionManufacturingOutlinedIcon fontSize="small" />, protocol: "MCP" },
  a2a: { icon: <HubOutlinedIcon fontSize="small" />, protocol: "A2A" },
  hybrid: { icon: <AccountTreeOutlinedIcon fontSize="small" />, protocol: "A2A + MCP" },
};

function getModeIcon(mode: string) {
  return MODE_ICONS[mode] ?? BASELINE_ICON;
}

function MiniEventRow({
  event,
  onSelect,
}: {
  event: TraceEvent;
  onSelect: (event: TraceEvent) => void;
}) {
  const tone = traceEventTone(event);
  const proto = traceEventProtocol(event);
  const borderColor = eventBorderColor(event);

  return (
    <Tooltip
      title={`${traceLabel(event)} · ${proto} · click to inspect envelope`}
      placement="left"
      arrow
    >
      <Box
        onClick={() => onSelect(event)}
        sx={{
          borderLeft: `3px solid ${borderColor}`,
          pl: 1,
          py: 0.4,
          cursor: "pointer",
          borderRadius: "0 4px 4px 0",
          "&:hover": { background: "rgba(0,0,0,0.04)" },
        }}
      >
        <Stack direction="row" spacing={0.75} alignItems="center" flexWrap="wrap" useFlexGap>
          <Chip
            label={traceLabel(event)}
            size="small"
            color={
              tone === "error"
                ? "error"
                : tone === "warning"
                  ? "warning"
                  : tone === "success"
                    ? "success"
                    : "default"
            }
            sx={{ fontSize: "0.65rem", height: 18 }}
          />
          <Chip
            label={proto}
            size="small"
            variant="outlined"
            sx={{ fontSize: "0.65rem", height: 18 }}
          />
          {isTraceFailureEvent(event) && (
            <Typography variant="caption" sx={{ color: "error.main", fontSize: "0.65rem" }}>
              {String(event.error ?? "failure")}
            </Typography>
          )}
        </Stack>
      </Box>
    </Tooltip>
  );
}

function ModeColumn({
  result,
  onSelectEvent,
}: {
  result: RunResult;
  onSelectEvent: (event: TraceEvent) => void;
}) {
  const modeIcon = getModeIcon(result.mode);
  const modeColor = getProtocolColor(result.mode);
  const toolCalls = result.trace.filter((e) => e.event_type === "tool_call").length;
  const a2aMessages = result.trace.filter(isA2AEvent).length;
  const failures = result.trace.filter(isTraceFailureEvent).length;

  return (
    <Card sx={{ height: "100%", display: "flex", flexDirection: "column" }}>
      <CardContent sx={{ pb: 1 }}>
        <Stack spacing={1}>
          <Stack direction="row" spacing={0.75} alignItems="center">
            <Box sx={{ color: modeColor }}>{modeIcon.icon}</Box>
            <Typography variant="h6" sx={{ color: modeColor, textTransform: "uppercase", fontSize: "0.85rem" }}>
              {result.mode}
            </Typography>
          </Stack>
          <Typography variant="caption" sx={{ color: "text.secondary" }}>
            {modeIcon.protocol}
          </Typography>
          <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
            <Chip label={`${result.trace.length} events`} size="small" />
            {toolCalls > 0 && <Chip label={`${toolCalls} tool calls`} size="small" variant="outlined" />}
            {a2aMessages > 0 && <Chip label={`${a2aMessages} A2A msgs`} size="small" variant="outlined" />}
            {failures > 0 && <Chip label={`${failures} failures`} size="small" color="error" variant="outlined" />}
          </Stack>
        </Stack>
      </CardContent>

      <Box sx={{ borderTop: `2px solid ${modeColor}`, mx: 2 }} />

      <CardContent sx={{ flex: 1, overflowY: "auto", maxHeight: 600, pt: 1.5 }}>
        <Stack spacing={0.5}>
          {result.trace.map((event) => (
            <MiniEventRow
              key={`${event.index}-${event.event_type}`}
              event={event}
              onSelect={onSelectEvent}
            />
          ))}
          {result.trace.length === 0 && (
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              No trace events.
            </Typography>
          )}
        </Stack>
      </CardContent>
    </Card>
  );
}

export function ComparePage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [results, setResults] = useState<RunResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [envelopeEvent, setEnvelopeEvent] = useState<TraceEvent | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const selectedReport = searchParams.get("report") ?? "";

  function setReport(name: string) {
    const next = new URLSearchParams(searchParams);
    next.set("report", name);
    setSearchParams(next, { replace: true });
  }

  useEffect(() => {
    let active = true;
    setLoading(true);
    fetchReports()
      .then((payload) => {
        if (!active) return;
        setReports(payload.reports);
        if (!selectedReport && payload.reports[0]) {
          setReport(payload.reports[0].report_name);
        }
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : "Failed to load reports.");
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => { active = false; };
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedReport) return;
    let active = true;
    setLoadingDetail(true);
    fetchReportDetail(selectedReport)
      .then((payload) => {
        if (active) setResults(payload.results);
      })
      .catch((err: unknown) => {
        if (active) setError(err instanceof Error ? err.message : "Failed to load report.");
      })
      .finally(() => {
        if (active) setLoadingDetail(false);
      });
    return () => { active = false; };
  }, [selectedReport]);

  const orderedResults = useMemo(() => {
    return MODE_ORDER.map((mode) => results.find((r) => r.mode === mode)).filter(
      (r): r is RunResult => r !== undefined,
    );
  }, [results]);

  const cols = orderedResults.length || 4;

  return (
    <Stack spacing={3}>
      <Stack spacing={1}>
        <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
          Protocol Comparison
        </Typography>
        <Typography variant="h2" sx={{ color: "primary.main" }}>
          Side-by-side trace diff — all four modes on one screen.
        </Typography>
        <Typography variant="body1" sx={{ maxWidth: 800, color: "text.secondary" }}>
          Each column shows the same ticket processed by a different execution mode. Click any event
          row to open the protocol envelope and see the raw A2A or MCP shapes that flow across the
          boundary.
        </Typography>
      </Stack>

      {error ? <Alert severity="error">{error}</Alert> : null}

      {loading ? (
        <FilterCardSkeleton fields={1} />
      ) : (
        <Card>
          <CardContent>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2} alignItems="flex-end">
              <Stack spacing={1} sx={{ minWidth: 260 }}>
                <Typography variant="h6">Report</Typography>
                <FormControl fullWidth>
                  <InputLabel id="compare-report-label">Saved Report</InputLabel>
                  <Select
                    labelId="compare-report-label"
                    label="Saved Report"
                    value={selectedReport}
                    onChange={(e) => setReport(e.target.value)}
                  >
                    {reports.map((r) => (
                      <MenuItem key={r.report_name} value={r.report_name}>
                        {r.title} ({r.report_name})
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Stack>
              <Stack direction="row" spacing={1} alignItems="center">
                <CompareArrowsOutlinedIcon color="secondary" />
                <Typography variant="body2" sx={{ color: "text.secondary" }}>
                  {orderedResults.length > 0
                    ? `Comparing ${orderedResults.map((r) => r.mode.toUpperCase()).join(" · ")}`
                    : "Select a report that was run with multiple modes."}
                </Typography>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      )}

      {loadingDetail ? (
        <Grid container spacing={2}>
          {[0, 1, 2, 3].map((i) => (
            <Grid key={i} size={{ xs: 12, sm: 6, xl: 3 }}>
              <ContentCardSkeleton rows={8} height={300} />
            </Grid>
          ))}
        </Grid>
      ) : orderedResults.length > 0 ? (
        <Grid container spacing={2} alignItems="flex-start">
          {orderedResults.map((result) => (
            <Grid key={result.mode} size={{ xs: 12, sm: cols <= 2 ? 6 : 6, xl: cols <= 2 ? 6 : 3 }}>
              <ModeColumn result={result} onSelectEvent={setEnvelopeEvent} />
            </Grid>
          ))}
        </Grid>
      ) : selectedReport ? (
        <Alert severity="info">
          This report has no trace data yet, or was run with a single mode. Run the scenario with{" "}
          <strong>all</strong> modes to see the four-column comparison.
        </Alert>
      ) : null}

      <ProtocolEnvelopeDrawer event={envelopeEvent} onClose={() => setEnvelopeEvent(null)} />
    </Stack>
  );
}
