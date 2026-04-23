import QueryStatsOutlinedIcon from "@mui/icons-material/QueryStatsOutlined";
import { Alert, Card, CardContent, Chip, Grid, Stack, Typography } from "@mui/material";
import { useEffect, useMemo, useState } from "react";

import { MetricBarsCard } from "../../components/charts/MetricBarsCard";
import { ContentCardSkeleton, MetricGridSkeleton, PageIntroSkeleton } from "../../components/loading/LoadingSkeletons";
import { fetchTelemetry } from "../../lib/api/client";
import type { TelemetrySnapshot } from "../../lib/types/api";

export function TelemetryPage() {
  const [telemetry, setTelemetry] = useState<TelemetrySnapshot | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function loadTelemetry() {
      try {
        const payload = await fetchTelemetry(true);
        if (active) {
          setTelemetry(payload);
        }
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load telemetry.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadTelemetry();
    return () => {
      active = false;
    };
  }, []);

  const modeItems = useMemo(() => {
    return Object.entries(telemetry?.mode_counts ?? {}).map(([mode, count]) => ({
      label: mode.toUpperCase(),
      value: count,
      displayValue: String(count),
      subtitle: "completed runs",
      color: "linear-gradient(90deg, #2d6f7d, #17475f)",
    }));
  }, [telemetry]);

  const a2aTransportItems = useMemo(() => {
    return Object.entries(telemetry?.a2a_transport_counts ?? {}).map(([transport, count]) => ({
      label: transport.toUpperCase(),
      value: count,
      displayValue: String(count),
      subtitle: "completed runs",
      color:
        transport === "remote"
          ? "linear-gradient(90deg, #c2571a, #17475f)"
          : "linear-gradient(90deg, #2d6f7d, #17475f)",
    }));
  }, [telemetry]);
  return (
    <Stack spacing={3}>
      {loading ? (
        <PageIntroSkeleton />
      ) : (
        <Stack spacing={1}>
          <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
            Telemetry
          </Typography>
          <Typography variant="h2" sx={{ color: "primary.main" }}>
            Platform activity is visible across runs, users, and modes.
          </Typography>
          <Typography variant="body1" sx={{ maxWidth: 760, color: "text.secondary" }}>
            Use this view to check durable Phase 5 state before or after a demo: run volume, report persistence,
            protocol activity, failures, and active user scopes.
          </Typography>
        </Stack>
      )}

      {error ? <Alert severity="error">{error}</Alert> : null}

      {loading ? (
        <Stack spacing={2}>
          <MetricGridSkeleton />
          <ContentCardSkeleton rows={5} height={220} />
        </Stack>
      ) : null}

      {telemetry ? (
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}>
            <TelemetryCard label="Runs" value={String(telemetry.total_runs)} />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TelemetryCard label="Reports" value={String(telemetry.total_reports)} />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TelemetryCard label="Failures" value={String(telemetry.total_failures)} />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TelemetryCard label="Avg Latency" value={`${telemetry.avg_latency_ms} ms`} />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TelemetryCard label="Tool Calls" value={String(telemetry.tool_calls)} />
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <TelemetryCard label="A2A Messages" value={String(telemetry.a2a_messages)} />
          </Grid>

          <Grid size={{ xs: 12, lg: 7 }}>
            <MetricBarsCard
              title="Runs By Mode"
              subtitle="Completed run events recorded in the durable platform state store."
              items={modeItems}
            />
          </Grid>

          <Grid size={{ xs: 12, lg: 5 }}>
            <MetricBarsCard
              title="Runs By A2A Transport"
              subtitle="Local broker versus hosted remote A2A usage across completed run events."
              items={a2aTransportItems}
            />
          </Grid>

          <Grid size={{ xs: 12, lg: 5 }}>
            <Card sx={{ height: "100%" }}>
              <CardContent>
                <Stack spacing={1.5}>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    <QueryStatsOutlinedIcon color="action" />
                    <Typography variant="h6">User Scopes</Typography>
                  </Stack>
                  <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                    {telemetry.users.length ? (
                      telemetry.users.map((user) => <Chip key={user} label={user} size="small" />)
                    ) : (
                      <Chip label="none" size="small" />
                    )}
                  </Stack>
                  <Typography variant="body2" sx={{ color: "text.secondary" }}>
                    Non-default users store reports, traces, logs, and export bundles under isolated artifact
                    directories.
                  </Typography>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      ) : null}
    </Stack>
  );
}

function TelemetryCard(props: { label: string; value: string }) {
  return (
    <Card>
      <CardContent>
        <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.12em" }}>
          {props.label}
        </Typography>
        <Typography variant="h5" sx={{ color: "primary.main", wordBreak: "break-word" }}>
          {props.value}
        </Typography>
      </CardContent>
    </Card>
  );
}
