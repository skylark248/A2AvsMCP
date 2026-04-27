import CompareArrowsOutlinedIcon from "@mui/icons-material/CompareArrowsOutlined";
import {
  Alert,
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

import { GlossaryTerm } from "../../components/glossary/GlossaryTerm";
import { ProtocolEnvelopeDrawer } from "../../components/traces/ProtocolEnvelopeDrawer";
import { ContentCardSkeleton, FilterCardSkeleton } from "../../components/loading/LoadingSkeletons";
import { fetchReportDetail, fetchReports } from "../../lib/api/client";
import type { ReportSummary, RunResult, TraceEvent } from "../../lib/types/api";
import { CompareTracesPanel } from "./CompareTracesPanel";

const ROLE_FIRST_LABELS: Record<string, string> = {
  mcp: "Tool Access Protocol (MCP)",
  a2a: "Agent Coordination Protocol (A2A)",
  baseline: "Direct Agent (Baseline)",
  hybrid: "Combined Protocol (Hybrid)",
};

function roleFirstLabel(mode: string): string {
  return ROLE_FIRST_LABELS[mode] ?? mode.toUpperCase();
}

const MODE_ORDER = ["baseline", "mcp", "a2a", "hybrid"] as const;

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
                  {orderedResults.length > 0 ? (
                    <>
                      Comparing{" "}
                      {orderedResults.map((r, i) => (
                        <span key={r.mode}>
                          {i > 0 && " \u00b7 "}
                          <GlossaryTerm term={r.mode}>
                            {roleFirstLabel(r.mode)}
                          </GlossaryTerm>
                        </span>
                      ))}
                    </>
                  ) : (
                    "Select a report that was run with multiple modes."
                  )}
                </Typography>
              </Stack>
            </Stack>
          </CardContent>
        </Card>
      )}

      {loadingDetail ? (
        <Grid container spacing={2}>
          {[0, 1].map((i) => (
            <Grid key={i} size={{ xs: 12, md: 6 }}>
              <ContentCardSkeleton rows={8} height={300} />
            </Grid>
          ))}
        </Grid>
      ) : orderedResults.length > 0 ? (
        <CompareTracesPanel results={orderedResults} />
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
