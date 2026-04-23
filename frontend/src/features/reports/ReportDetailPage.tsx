import OpenInNewOutlinedIcon from "@mui/icons-material/OpenInNewOutlined";
import { Alert, Button, Card, CardContent, Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { Link as RouterLink, useParams } from "react-router-dom";

import { MetricBarsCard } from "../../components/charts/MetricBarsCard";
import {
  CardGridSkeleton,
  ContentCardSkeleton,
  MetricGridSkeleton,
  PageIntroSkeleton,
} from "../../components/loading/LoadingSkeletons";
import { TraceExplorer } from "../../components/traces/TraceExplorer";
import { fetchReportDetail } from "../../lib/api/client";
import type { ReportDetailResponse } from "../../lib/types/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

export function ReportDetailPage() {
  const { reportName = "" } = useParams();
  const [report, setReport] = useState<ReportDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadReport() {
      try {
        const payload = await fetchReportDetail(reportName);
        if (active) {
          setReport(payload);
        }
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load the report.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    if (reportName) {
      void loadReport();
    } else {
      setLoading(false);
      setError("Missing report name.");
    }

    return () => {
      active = false;
    };
  }, [reportName]);

  const comparisonItems = useMemo(() => {
    return (report?.results ?? []).map((result) => ({
      label: result.mode.toUpperCase(),
      latency: result.metrics.latency_ms,
      tools: result.metrics.tool_calls,
      a2a: result.metrics.a2a_messages,
      failures: result.metrics.failures,
    }));
  }, [report]);

  return (
    <Stack spacing={3}>
      {loading ? (
        <PageIntroSkeleton />
      ) : (
        <Stack direction={{ xs: "column", md: "row" }} justifyContent="space-between" spacing={2}>
          <Stack spacing={1}>
            <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
              Report Detail
            </Typography>
            <Typography variant="h2" sx={{ color: "primary.main" }}>
              {report?.summary.title ?? "Report detail"}
            </Typography>
            <Typography variant="body1" sx={{ color: "text.secondary", maxWidth: 760 }}>
              Deep-dive view for a saved run, including scorecards, per-mode results, export links, and visual
              analytics.
            </Typography>
          </Stack>
          <Stack direction={{ xs: "column", sm: "row" }} spacing={1}>
            <Button component={RouterLink} to="/reports" variant="text">
              Back to reports
            </Button>
            {report ? (
              <>
                <Button
                  component="a"
                  href={`${API_BASE_URL}${report.export_url}`}
                  target="_blank"
                  rel="noreferrer"
                  endIcon={<OpenInNewOutlinedIcon fontSize="small" />}
                >
                  Open HTML Export
                </Button>
                <Button
                  component="a"
                  href={`${API_BASE_URL}${report.pdf_export_url}`}
                  target="_blank"
                  rel="noreferrer"
                  endIcon={<OpenInNewOutlinedIcon fontSize="small" />}
                >
                  Open PDF Export
                </Button>
                <Button component="a" href={`${API_BASE_URL}${report.evidence_export_url}`} rel="noreferrer">
                  Download Evidence Bundle
                </Button>
              </>
            ) : null}
          </Stack>
        </Stack>
      )}

      {error ? <Alert severity="error">{error}</Alert> : null}

      {loading ? (
        <Stack spacing={2}>
          <MetricGridSkeleton />
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, lg: 5 }}>
              <ContentCardSkeleton rows={4} height={150} />
            </Grid>
            <Grid size={{ xs: 12, lg: 7 }}>
              <ContentCardSkeleton rows={5} height={190} />
            </Grid>
            <Grid size={{ xs: 12, lg: 6 }}>
              <ContentCardSkeleton rows={4} height={160} />
            </Grid>
            <Grid size={{ xs: 12, lg: 6 }}>
              <ContentCardSkeleton rows={4} height={160} />
            </Grid>
          </Grid>
          <CardGridSkeleton cards={2} />
          <ContentCardSkeleton rows={6} height={180} />
        </Stack>
      ) : null}

      {report ? (
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}>
            <MetricCard label="Scenario" value={report.summary.scenario} />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <MetricCard label="Runtime" value={report.summary.runtime} />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <MetricCard label="Recommended" value={report.summary.scorecard.recommended_demo_mode.toUpperCase()} />
          </Grid>

          <Grid size={{ xs: 12, lg: 5 }}>
            <Card>
              <CardContent>
                <Stack spacing={1.5}>
                  <Typography variant="h6">Talking Points</Typography>
                  {report.summary.talking_points.map((point) => (
                    <Typography key={point} variant="body2" sx={{ color: "text.secondary" }}>
                      - {point}
                    </Typography>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, lg: 7 }}>
            <Card>
              <CardContent>
                <Stack spacing={1.5}>
                  <Typography variant="h6">Mode Scorecards</Typography>
                  {report.summary.scorecard.mode_scorecards.map((card) => (
                    <Stack
                      key={card.mode}
                      direction={{ xs: "column", md: "row" }}
                      justifyContent="space-between"
                      spacing={1}
                      sx={{ py: 1, borderBottom: "1px solid rgba(16, 32, 51, 0.08)" }}
                    >
                      <Stack spacing={0.5}>
                        <Typography variant="subtitle1">{card.mode.toUpperCase()}</Typography>
                        <Typography variant="body2" sx={{ color: "text.secondary" }}>
                          {card.headline}
                        </Typography>
                      </Stack>
                      <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                        <Chip label={`Overall ${card.overall_score}`} size="small" />
                        <Chip label={`Tooling ${card.tooling_score}`} size="small" />
                        <Chip label={`Collab ${card.collaboration_score}`} size="small" />
                        <Chip label={`Resilience ${card.resilience_score}`} size="small" />
                      </Stack>
                    </Stack>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, lg: 6 }}>
            <MetricBarsCard
              title="Latency Comparison"
              subtitle="Lower is better, so this chart inverses the metric to highlight the fastest mode visually."
              inverse
              items={comparisonItems.map((item) => ({
                label: item.label,
                value: item.latency,
                displayValue: `${item.latency} ms`,
                subtitle: `Tools ${item.tools} | A2A ${item.a2a}`,
                color: "linear-gradient(90deg, #2d6f7d, #17475f)",
              }))}
            />
          </Grid>

          <Grid size={{ xs: 12, lg: 6 }}>
            <MetricBarsCard
              title="Tool And Collaboration Load"
              subtitle="Shows how much protocol activity each mode generated during the saved run."
              items={comparisonItems.map((item) => ({
                label: item.label,
                value: item.tools + item.a2a,
                displayValue: `${item.tools + item.a2a} combined`,
                subtitle: `Tools ${item.tools} | A2A ${item.a2a} | Failures ${item.failures}`,
                color: "linear-gradient(90deg, #b85c38, #d78958)",
              }))}
            />
          </Grid>

          <Grid size={{ xs: 12 }}>
            <Grid container spacing={2}>
              {report.results.map((result) => (
                <Grid key={result.mode} size={{ xs: 12, md: 6 }}>
                  <Card>
                    <CardContent>
                      <Stack spacing={1.25}>
                        <Stack direction="row" justifyContent="space-between" alignItems="center">
                          <Typography variant="h6">{result.mode.toUpperCase()}</Typography>
                          <Chip label={`${result.metrics.latency_ms} ms`} size="small" />
                        </Stack>
                        <Typography variant="body2" sx={{ color: "text.secondary" }}>
                          {result.final_answer}
                        </Typography>
                        <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                          <Chip label={`${result.metrics.tool_calls} tools`} size="small" />
                          <Chip label={`${result.metrics.a2a_messages} A2A`} size="small" />
                          <Chip label={`${result.metrics.failures} failures`} size="small" />
                        </Stack>
                      </Stack>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>
          </Grid>

          <Grid size={{ xs: 12 }}>
            <Stack spacing={2}>
              {report.results.map((result) => (
                <TraceExplorer
                  key={`report-trace-${result.mode}`}
                  events={result.trace}
                  title={`${result.mode.toUpperCase()} Trace`}
                  subtitle={`Explore saved ${result.mode.toUpperCase()} protocol events, transports, and failure signals.`}
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
