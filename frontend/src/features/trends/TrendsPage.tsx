import TimelineOutlinedIcon from "@mui/icons-material/TimelineOutlined";
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

import { MetricBarsCard } from "../../components/charts/MetricBarsCard";
import {
  ContentCardSkeleton,
  FilterCardSkeleton,
  MetricGridSkeleton,
  PageIntroSkeleton,
} from "../../components/loading/LoadingSkeletons";
import { fetchTrends } from "../../lib/api/client";
import type { ReportTrendSummary } from "../../lib/types/api";

export function TrendsPage() {
  const [trends, setTrends] = useState<ReportTrendSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const scenario = searchParams.get("scenario") ?? "";
  const runtime = searchParams.get("runtime") ?? "";
  const recommendedMode = searchParams.get("recommended_mode") ?? "";
  const modeSort = searchParams.get("mode_sort") ?? "overall";

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (!value) {
      next.delete(key);
    } else {
      next.set(key, value);
    }
    setSearchParams(next, { replace: true });
  }

  useEffect(() => {
    let active = true;

    async function loadTrends() {
      try {
        const payload = await fetchTrends({
          scenario: scenario || undefined,
          runtime: runtime || undefined,
          recommended_mode: recommendedMode || undefined,
          mode_sort: modeSort || undefined,
        });
        if (active) {
          setTrends(payload.trends);
        }
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load trends.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadTrends();
    return () => {
      active = false;
    };
  }, [modeSort, recommendedMode, runtime, scenario]);

  const modeScoreItems = useMemo(() => {
    return (trends?.mode_trends ?? []).map((mode) => ({
      label: mode.mode.toUpperCase(),
      value: mode.avg_overall_score,
      displayValue: String(mode.avg_overall_score),
      subtitle: `${mode.appearances} appearances | ${mode.recommended_count} recommendations`,
    }));
  }, [trends]);

  const latencyItems = useMemo(() => {
    return (trends?.mode_trends ?? []).map((mode) => ({
      label: mode.mode.toUpperCase(),
      value: mode.avg_latency_ms,
      displayValue: `${mode.avg_latency_ms} ms`,
      subtitle: `Avg tool calls ${mode.avg_tool_calls} | Avg A2A ${mode.avg_a2a_messages}`,
      color: "linear-gradient(90deg, #2d6f7d, #17475f)",
    }));
  }, [trends]);

  const a2aTransportItems = useMemo(() => {
    return Object.entries(trends?.a2a_transport_counts ?? {}).map(([transport, count]) => ({
      label: transport.toUpperCase(),
      value: count,
      displayValue: `${count} runs`,
      color:
        transport === "remote"
          ? "linear-gradient(90deg, #c2571a, #17475f)"
          : "linear-gradient(90deg, #2d6f7d, #17475f)",
    }));
  }, [trends]);
  const scenarioItems = useMemo(() => {
    return (trends?.scenario_counts ?? []).slice(0, 6).map((entry) => ({
      label: entry.scenario.replaceAll("_", " ").toUpperCase(),
      value: entry.count,
      displayValue: `${entry.count} saved`,
      color: "linear-gradient(90deg, #b85c38, #d78958)",
    }));
  }, [trends]);

  return (
    <Stack spacing={3}>
      {loading ? (
        <PageIntroSkeleton />
      ) : (
        <Stack spacing={1}>
          <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
            Trend Workspace
          </Typography>
          <Typography variant="h2" sx={{ color: "primary.main" }}>
            Cross-run analytics are ready for richer visual storytelling.
          </Typography>
          <Typography variant="body1" sx={{ maxWidth: 760, color: "text.secondary" }}>
            This React view now uses lightweight chart cards to show mode performance, latency posture, and scenario
            concentration without depending on an external charting library. Active filters and sorting now live in the
            URL for shareable trend views.
          </Typography>
        </Stack>
      )}

      {error ? <Alert severity="error">{error}</Alert> : null}

      {loading ? (
        <Stack spacing={2}>
          <FilterCardSkeleton />
          <MetricGridSkeleton />
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, lg: 7 }}>
              <ContentCardSkeleton rows={4} height={180} />
            </Grid>
            <Grid size={{ xs: 12, lg: 5 }}>
              <ContentCardSkeleton rows={5} height={180} />
            </Grid>
            <Grid size={{ xs: 12, lg: 6 }}>
              <ContentCardSkeleton rows={4} height={160} />
            </Grid>
            <Grid size={{ xs: 12, lg: 6 }}>
              <ContentCardSkeleton rows={4} height={160} />
            </Grid>
            <Grid size={{ xs: 12 }}>
              <ContentCardSkeleton rows={4} height={120} />
            </Grid>
          </Grid>
        </Stack>
      ) : null}

      {trends ? (
        <Grid container spacing={2}>
          <Grid size={{ xs: 12 }}>
            <Card>
              <CardContent>
                <Grid container spacing={2}>
                  <Grid size={{ xs: 12, md: 3 }}>
                    <FormControl fullWidth>
                      <InputLabel id="trend-scenario-label">Scenario</InputLabel>
                      <Select
                        labelId="trend-scenario-label"
                        label="Scenario"
                        value={scenario}
                        onChange={(event) => updateParam("scenario", event.target.value)}
                      >
                        <MenuItem value="">All scenarios</MenuItem>
                        {trends.available_filters.scenarios.map((item) => (
                          <MenuItem key={item} value={item}>
                            {item}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid size={{ xs: 12, md: 3 }}>
                    <FormControl fullWidth>
                      <InputLabel id="trend-runtime-label">Runtime</InputLabel>
                      <Select
                        labelId="trend-runtime-label"
                        label="Runtime"
                        value={runtime}
                        onChange={(event) => updateParam("runtime", event.target.value)}
                      >
                        <MenuItem value="">All runtimes</MenuItem>
                        {trends.available_filters.runtimes.map((item) => (
                          <MenuItem key={item} value={item}>
                            {item}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid size={{ xs: 12, md: 3 }}>
                    <FormControl fullWidth>
                      <InputLabel id="trend-rec-label">Recommended</InputLabel>
                      <Select
                        labelId="trend-rec-label"
                        label="Recommended"
                        value={recommendedMode}
                        onChange={(event) => updateParam("recommended_mode", event.target.value)}
                      >
                        <MenuItem value="">All modes</MenuItem>
                        {trends.available_filters.recommended_modes.map((item) => (
                          <MenuItem key={item} value={item}>
                            {item.toUpperCase()}
                          </MenuItem>
                        ))}
                      </Select>
                    </FormControl>
                  </Grid>
                  <Grid size={{ xs: 12, md: 3 }}>
                    <FormControl fullWidth>
                      <InputLabel id="trend-sort-label">Mode Sort</InputLabel>
                      <Select
                        labelId="trend-sort-label"
                        label="Mode Sort"
                        value={modeSort}
                        onChange={(event) => updateParam("mode_sort", event.target.value)}
                      >
                        <MenuItem value="overall">Overall score</MenuItem>
                        <MenuItem value="latency">Latency</MenuItem>
                        <MenuItem value="recommended">Recommended count</MenuItem>
                        <MenuItem value="tools">Tool calls</MenuItem>
                        <MenuItem value="a2a">A2A messages</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                </Grid>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, md: 4 }}>
            <SummaryCard label="Saved Reports" value={String(trends.total_reports)} />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <SummaryCard label="Avg Tool Calls" value={String(trends.average_totals.tool_calls)} />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <SummaryCard label="Avg A2A Messages" value={String(trends.average_totals.a2a_messages)} />
          </Grid>

          <Grid size={{ xs: 12, lg: 7 }}>
            <MetricBarsCard
              title="Average Overall Mode Score"
              subtitle="Higher is better for demo recommendation and all-around presentation quality."
              items={modeScoreItems}
            />
          </Grid>
          <Grid size={{ xs: 12, lg: 5 }}>
            <Card sx={{ height: "100%" }}>
              <CardContent>
                <Stack spacing={1.5}>
                  <Typography variant="h6">Narrative Summary</Typography>
                  {trends.narrative.map((item) => (
                    <Typography key={item} variant="body2" sx={{ color: "text.secondary" }}>
                      - {item}
                    </Typography>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>

          <Grid size={{ xs: 12, lg: 6 }}>
            <MetricBarsCard
              title="Latency Advantage"
              subtitle="Shorter bars are worse here, so this chart inverses the metric to highlight the fastest modes."
              items={latencyItems}
              inverse
            />
          </Grid>
          <Grid size={{ xs: 12, lg: 6 }}>
            <MetricBarsCard
              title="A2A Transport Mix"
              subtitle="Local broker versus hosted remote A2A runs across saved reports."
              items={a2aTransportItems}
            />
          </Grid>
          <Grid size={{ xs: 12, lg: 6 }}>
            <MetricBarsCard
              title="Most Frequent Scenarios"
              subtitle="Which saved scenarios are showing up most often in the report corpus."
              items={scenarioItems}
            />
          </Grid>

          <Grid size={{ xs: 12 }}>
            <Card>
              <CardContent>
                <Stack spacing={1.5}>
                  <Typography variant="h6">Mode Leaders</Typography>
                  {trends.mode_trends.slice(0, 4).map((mode) => (
                    <Stack key={mode.mode} direction="row" justifyContent="space-between" alignItems="center">
                      <Stack direction="row" spacing={1} alignItems="center">
                        <TimelineOutlinedIcon fontSize="small" color="action" />
                        <Typography variant="body2">{mode.mode.toUpperCase()}</Typography>
                      </Stack>
                      <Typography variant="body2" sx={{ color: "text.secondary" }}>
                        Score {mode.avg_overall_score} | Latency {mode.avg_latency_ms} ms | Recommended{" "}
                        {mode.recommended_count}x
                      </Typography>
                    </Stack>
                  ))}
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      ) : null}
    </Stack>
  );
}

function SummaryCard(props: { label: string; value: string }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.12em" }}>
          {props.label}
        </Typography>
        <Typography variant="h3" sx={{ color: "primary.main" }}>
          {props.value}
        </Typography>
      </CardContent>
    </Card>
  );
}
