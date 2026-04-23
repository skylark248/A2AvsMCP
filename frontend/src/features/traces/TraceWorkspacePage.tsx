import CompareArrowsOutlinedIcon from "@mui/icons-material/CompareArrowsOutlined";
import UploadFileOutlinedIcon from "@mui/icons-material/UploadFileOutlined";
import {
  Alert,
  Button,
  Card,
  CardContent,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { MetricBarsCard } from "../../components/charts/MetricBarsCard";
import {
  ContentCardSkeleton,
  FilterCardSkeleton,
  MetricGridSkeleton,
  PageIntroSkeleton,
} from "../../components/loading/LoadingSkeletons";
import { TraceExplorer } from "../../components/traces/TraceExplorer";
import { fetchReportDetail, fetchReports } from "../../lib/api/client";
import { isA2AEvent, isTraceFailureEvent } from "../../lib/trace/utils";
import type { ReportDetailResponse, ReportSummary, TraceEvent } from "../../lib/types/api";

interface ImportedLogRun {
  task_id?: string;
  mode?: string;
  runtime?: string;
  profile?: string;
  requested_transport?: string;
  trace_file?: string;
}

interface ImportedLogLine {
  run?: ImportedLogRun;
  event?: TraceEvent;
}

export function TraceWorkspacePage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [detail, setDetail] = useState<ReportDetailResponse | null>(null);
  const [loadingReports, setLoadingReports] = useState(true);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const [importedEvents, setImportedEvents] = useState<TraceEvent[]>([]);
  const [importedRun, setImportedRun] = useState<ImportedLogRun | null>(null);
  const [importedFileName, setImportedFileName] = useState<string>("");

  const selectedReport = searchParams.get("report") ?? "";
  const modeFilter = searchParams.get("mode") ?? "all";
  const source = searchParams.get("source") ?? "saved";

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (!value || value === "all" || (key === "source" && value === "saved")) {
      next.delete(key);
    } else {
      next.set(key, value);
    }
    setSearchParams(next, { replace: true });
  }

  useEffect(() => {
    let active = true;

    async function loadReports() {
      try {
        const payload = await fetchReports();
        if (!active) {
          return;
        }
        setReports(payload.reports);
        if (!selectedReport && payload.reports[0] && source === "saved") {
          const next = new URLSearchParams(searchParams);
          next.set("report", payload.reports[0].report_name);
          setSearchParams(next, { replace: true });
        }
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load reports.");
        }
      } finally {
        if (active) {
          setLoadingReports(false);
        }
      }
    }

    void loadReports();
    return () => {
      active = false;
    };
  }, [searchParams, selectedReport, setSearchParams, source]);

  useEffect(() => {
    let active = true;

    async function loadDetail() {
      if (!selectedReport || source !== "saved") {
        return;
      }
      setLoadingDetail(true);
      try {
        const payload = await fetchReportDetail(selectedReport);
        if (active) {
          setDetail(payload);
        }
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load report detail.");
        }
      } finally {
        if (active) {
          setLoadingDetail(false);
        }
      }
    }

    void loadDetail();
    return () => {
      active = false;
    };
  }, [selectedReport, source]);

  const visibleResults = useMemo(() => {
    if (source === "imported") {
      const importedMode = importedRun?.mode ?? "imported";
      const result = {
        mode: importedMode,
        trace: importedEvents,
      };
      if (modeFilter !== "all" && modeFilter !== importedMode) {
        return [];
      }
      return [result];
    }

    const items = detail?.results ?? [];
    if (modeFilter === "all") {
      return items.map((result) => ({ mode: result.mode, trace: result.trace }));
    }
    return items
      .filter((result) => result.mode === modeFilter)
      .map((result) => ({ mode: result.mode, trace: result.trace }));
  }, [detail, importedEvents, importedRun, modeFilter, source]);

  const protocolItems = useMemo(() => {
    return visibleResults.map((result) => {
      const toolCalls = result.trace.filter((event) => event.event_type === "tool_call").length;
      const a2aMessages = result.trace.filter(isA2AEvent).length;
      return {
        label: result.mode.toUpperCase(),
        value: toolCalls + a2aMessages,
        displayValue: `${toolCalls + a2aMessages} events`,
        subtitle: `Tools ${toolCalls} | A2A ${a2aMessages}`,
      };
    });
  }, [visibleResults]);

  const failureItems = useMemo(() => {
    return visibleResults.map((result) => {
      const failureCount = result.trace.filter(isFailureEvent).length;
      return {
        label: result.mode.toUpperCase(),
        value: failureCount,
        displayValue: `${failureCount} failure signals`,
        subtitle: `${result.trace.length} total events`,
        color: "linear-gradient(90deg, #a63d40, #ed6c02)",
      };
    });
  }, [visibleResults]);

  async function handleImport(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    try {
      const text = await file.text();
      const lines = text
        .split(/\r?\n/)
        .map((line) => line.trim())
        .filter(Boolean)
        .map((line) => JSON.parse(line) as ImportedLogLine);
      const events = lines.map((line) => line.event).filter((item): item is TraceEvent => Boolean(item));
      setImportedEvents(events);
      setImportedRun(lines[0]?.run ?? null);
      setImportedFileName(file.name);
      updateParam("source", "imported");
      if ((lines[0]?.run?.mode ?? "") !== "") {
        updateParam("mode", lines[0]?.run?.mode ?? "all");
      }
      setError(null);
    } catch {
      setError("Failed to parse the NDJSON log. Make sure it matches the exported structured log format.");
    }
  }

  const sourceTitle =
    source === "imported"
      ? `Imported log${importedFileName ? `: ${importedFileName}` : ""}`
      : (detail?.summary.title ?? "Saved report trace view");

  return (
    <Stack spacing={3}>
      {loadingReports && source === "saved" ? (
        <PageIntroSkeleton />
      ) : (
        <Stack spacing={1}>
          <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
            Trace Workspace
          </Typography>
          <Typography variant="h2" sx={{ color: "primary.main" }}>
            Compare protocol behavior across modes from saved reports or imported logs.
          </Typography>
          <Typography variant="body1" sx={{ maxWidth: 800, color: "text.secondary" }}>
            This workspace is built for cross-mode trace narration: pick a saved report, compare event volume and
            failure signals, or import an NDJSON log for replay. The current source and filters live in the URL for
            shareable trace views.
          </Typography>
        </Stack>
      )}

      {error ? <Alert severity="error">{error}</Alert> : null}

      {loadingReports && source === "saved" ? (
        <FilterCardSkeleton fields={3} />
      ) : (
        <Card>
          <CardContent>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 4 }}>
                <Stack spacing={2}>
                  <Typography variant="h6">Trace Source</Typography>
                  <FormControl fullWidth>
                    <InputLabel id="trace-source-label">Source Type</InputLabel>
                    <Select
                      labelId="trace-source-label"
                      label="Source Type"
                      value={source}
                      onChange={(event) => updateParam("source", event.target.value)}
                    >
                      <MenuItem value="saved">Saved report</MenuItem>
                      <MenuItem value="imported">Imported NDJSON</MenuItem>
                    </Select>
                  </FormControl>
                </Stack>
              </Grid>
              <Grid size={{ xs: 12, md: 5 }}>
                <Stack spacing={2}>
                  <Typography variant="h6">Selection</Typography>
                  {source === "saved" ? (
                    <FormControl fullWidth>
                      <InputLabel id="trace-report-label">Saved Report</InputLabel>
                      <Select
                        labelId="trace-report-label"
                        label="Saved Report"
                        value={selectedReport}
                        onChange={(event) => updateParam("report", event.target.value)}
                      >
                        {reports.map((report) => (
                          <MenuItem key={report.report_name} value={report.report_name}>
                            {report.title} ({report.report_name})
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  ) : (
                    <Button component="label" startIcon={<UploadFileOutlinedIcon fontSize="small" />}>
                      Import NDJSON Log
                      <input
                        hidden
                        type="file"
                        accept=".ndjson,.jsonl,.txt"
                        onChange={(event) => void handleImport(event)}
                      />
                    </Button>
                  )}
                </Stack>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <Stack spacing={2}>
                  <Typography variant="h6">Mode Focus</Typography>
                  <FormControl fullWidth>
                    <InputLabel id="trace-mode-label">Visible Mode</InputLabel>
                    <Select
                      labelId="trace-mode-label"
                      label="Visible Mode"
                      value={modeFilter}
                      onChange={(event) => updateParam("mode", event.target.value)}
                    >
                      <MenuItem value="all">All modes</MenuItem>
                      {source === "saved" ? (
                        (detail?.results ?? []).map((result) => (
                          <MenuItem key={result.mode} value={result.mode}>
                            {result.mode.toUpperCase()}
                          </MenuItem>
                        ))
                      ) : importedRun?.mode ? (
                        <MenuItem value={importedRun.mode}>{importedRun.mode.toUpperCase()}</MenuItem>
                      ) : null}
                    </Select>
                  </FormControl>
                </Stack>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {loadingDetail ? (
        <Stack spacing={2}>
          <MetricGridSkeleton />
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, lg: 6 }}>
              <ContentCardSkeleton rows={4} height={160} />
            </Grid>
            <Grid size={{ xs: 12, lg: 6 }}>
              <ContentCardSkeleton rows={4} height={160} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <ContentCardSkeleton rows={4} height={120} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <ContentCardSkeleton rows={6} height={220} />
            </Grid>
          </Grid>
        </Stack>
      ) : null}

      {(source === "imported" ? importedEvents.length > 0 : Boolean(detail)) ? (
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}>
            <MetricCard label="Source" value={source === "imported" ? "NDJSON replay" : "Saved report"} />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <MetricCard label="Context" value={sourceTitle} />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <MetricCard
              label="Runtime"
              value={
                source === "imported" ? (importedRun?.runtime ?? "unknown") : (detail?.summary.runtime ?? "unknown")
              }
            />
          </Grid>

          <Grid size={{ xs: 12, lg: 6 }}>
            <MetricBarsCard
              title="Protocol Activity By Mode"
              subtitle="Combined tool calls and A2A messages from the selected trace source."
              items={protocolItems}
            />
          </Grid>
          <Grid size={{ xs: 12, lg: 6 }}>
            <MetricBarsCard
              title="Failure Signals By Mode"
              subtitle="Warnings, retries, and trace-level errors surfaced during execution."
              items={failureItems}
            />
          </Grid>

          <Grid size={{ xs: 12 }}>
            <Card>
              <CardContent>
                <Stack spacing={1.25}>
                  <Stack direction="row" spacing={1} alignItems="center">
                    <CompareArrowsOutlinedIcon color="secondary" />
                    <Typography variant="h6">Cross-Mode Comparison</Typography>
                  </Stack>
                  {visibleResults.map((result) => (
                    <Typography key={`compare-${result.mode}`} variant="body2" sx={{ color: "text.secondary" }}>
                      {result.mode.toUpperCase()}: {result.trace.length} total events,{" "}
                      {result.trace.filter((event) => event.event_type === "tool_call").length} tool calls,{" "}
                      {result.trace.filter(isA2AEvent).length} A2A messages,{" "}
                      {result.trace.filter(isFailureEvent).length} failure signals.
                    </Typography>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12 }}>
            <Stack spacing={2}>
              {visibleResults.map((result) => (
                <TraceExplorer
                  key={`workspace-trace-${result.mode}`}
                  events={result.trace}
                  title={`${result.mode.toUpperCase()} Trace`}
                  subtitle={
                    source === "imported"
                      ? `Replayed from imported NDJSON log${importedFileName ? ` (${importedFileName})` : ""}.`
                      : `Inspect ${result.mode.toUpperCase()} protocol flow for ${detail?.summary.title ?? "saved report"}.`
                  }
                />
              ))}
            </Stack>
          </Grid>
        </Grid>
      ) : null}
    </Stack>
  );
}

function MetricCard(props: { label: string; value: string }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.12em" }}>
          {props.label}
        </Typography>
        <Typography variant="h6" sx={{ color: "primary.main", wordBreak: "break-word" }}>
          {props.value}
        </Typography>
      </CardContent>
    </Card>
  );
}

function isFailureEvent(event: TraceEvent) {
  return isTraceFailureEvent(event);
}
