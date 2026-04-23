import DescriptionOutlinedIcon from "@mui/icons-material/DescriptionOutlined";
import {
  Alert,
  Button,
  Card,
  CardContent,
  Chip,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useMemo, useState } from "react";
import { Link as RouterLink, useSearchParams } from "react-router-dom";

import { CardGridSkeleton, FilterCardSkeleton, PageIntroSkeleton } from "../../components/loading/LoadingSkeletons";
import { fetchReports } from "../../lib/api/client";
import type { ReportSummary } from "../../lib/types/api";

export function ReportsPage() {
  const [reports, setReports] = useState<ReportSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchParams, setSearchParams] = useSearchParams();

  const query = searchParams.get("q") ?? "";
  const runtimeFilter = searchParams.get("runtime") ?? "all";
  const recommendedFilter = searchParams.get("recommended") ?? "all";
  const sortBy = searchParams.get("sort") ?? "recent";

  function updateParam(key: string, value: string) {
    const next = new URLSearchParams(searchParams);
    if (!value || value === "all") {
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
        if (active) {
          setReports(payload.reports);
        }
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load reports.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadReports();
    return () => {
      active = false;
    };
  }, []);

  const runtimes = useMemo(() => Array.from(new Set(reports.map((report) => report.runtime))).sort(), [reports]);
  const recommendedModes = useMemo(
    () => Array.from(new Set(reports.map((report) => report.scorecard.recommended_demo_mode))).sort(),
    [reports],
  );

  const filteredReports = useMemo(() => {
    const lowered = query.trim().toLowerCase();
    const filtered = reports.filter((report) => {
      if (runtimeFilter !== "all" && report.runtime !== runtimeFilter) {
        return false;
      }
      if (recommendedFilter !== "all" && report.scorecard.recommended_demo_mode !== recommendedFilter) {
        return false;
      }
      if (!lowered) {
        return true;
      }
      return [report.title, report.scenario, report.report_name, report.runtime]
        .join(" ")
        .toLowerCase()
        .includes(lowered);
    });

    return filtered.sort((left, right) => {
      if (sortBy === "scenario") {
        return left.scenario.localeCompare(right.scenario);
      }
      if (sortBy === "runtime") {
        return left.runtime.localeCompare(right.runtime);
      }
      if (sortBy === "tools") {
        return right.total_tool_calls - left.total_tool_calls;
      }
      if (sortBy === "failures") {
        return right.total_failures - left.total_failures;
      }
      if (sortBy === "recommended") {
        return left.scorecard.recommended_demo_mode.localeCompare(right.scorecard.recommended_demo_mode);
      }
      return right.generated_at.localeCompare(left.generated_at);
    });
  }, [query, recommendedFilter, reports, runtimeFilter, sortBy]);

  return (
    <Stack spacing={3}>
      {loading ? (
        <PageIntroSkeleton />
      ) : (
        <Stack spacing={1}>
          <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
            Report Library
          </Typography>
          <Typography variant="h2" sx={{ color: "primary.main" }}>
            Saved runs are now a first-class workflow.
          </Typography>
          <Typography variant="body1" sx={{ maxWidth: 760, color: "text.secondary" }}>
            Search, filter, and sort saved runs before drilling into report detail, exports, traces, and
            recommendations. The current library state now stays in the URL so it can be shared or revisited.
          </Typography>
        </Stack>
      )}

      {error ? <Alert severity="error">{error}</Alert> : null}

      {loading ? (
        <FilterCardSkeleton />
      ) : (
        <Card>
          <CardContent>
            <Grid container spacing={2}>
              <Grid size={{ xs: 12, md: 4 }}>
                <TextField
                  fullWidth
                  label="Search reports"
                  value={query}
                  onChange={(event) => updateParam("q", event.target.value)}
                />
              </Grid>
              <Grid size={{ xs: 12, md: 2.5 }}>
                <FormControl fullWidth>
                  <InputLabel id="runtime-filter-label">Runtime</InputLabel>
                  <Select
                    labelId="runtime-filter-label"
                    label="Runtime"
                    value={runtimeFilter}
                    onChange={(event) => updateParam("runtime", event.target.value)}
                  >
                    <MenuItem value="all">All runtimes</MenuItem>
                    {runtimes.map((runtime) => (
                      <MenuItem key={runtime} value={runtime}>
                        {runtime}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 2.5 }}>
                <FormControl fullWidth>
                  <InputLabel id="recommended-filter-label">Recommended</InputLabel>
                  <Select
                    labelId="recommended-filter-label"
                    label="Recommended"
                    value={recommendedFilter}
                    onChange={(event) => updateParam("recommended", event.target.value)}
                  >
                    <MenuItem value="all">All modes</MenuItem>
                    {recommendedModes.map((mode) => (
                      <MenuItem key={mode} value={mode}>
                        {mode.toUpperCase()}
                      </MenuItem>
                    ))}
                  </Select>
                </FormControl>
              </Grid>
              <Grid size={{ xs: 12, md: 3 }}>
                <FormControl fullWidth>
                  <InputLabel id="sort-by-label">Sort by</InputLabel>
                  <Select
                    labelId="sort-by-label"
                    label="Sort by"
                    value={sortBy}
                    onChange={(event) => updateParam("sort", event.target.value)}
                  >
                    <MenuItem value="recent">Most recent</MenuItem>
                    <MenuItem value="scenario">Scenario</MenuItem>
                    <MenuItem value="runtime">Runtime</MenuItem>
                    <MenuItem value="recommended">Recommended mode</MenuItem>
                    <MenuItem value="tools">Tool calls</MenuItem>
                    <MenuItem value="failures">Failures</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {loading ? null : (
        <Typography variant="body2" sx={{ color: "text.secondary" }}>
          Showing {filteredReports.length} of {reports.length} saved reports.
        </Typography>
      )}

      {loading ? (
        <CardGridSkeleton />
      ) : (
        <Grid container spacing={2}>
          {filteredReports.map((report) => (
            <Grid key={report.report_name} size={{ xs: 12, md: 6, xl: 4 }}>
              <Card>
                <CardContent>
                  <Stack spacing={1.25}>
                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                      <Typography variant="h6">{report.title}</Typography>
                      <DescriptionOutlinedIcon color="action" />
                    </Stack>
                    <Typography variant="body2" sx={{ color: "text.secondary" }}>
                      Scenario: {report.scenario} | Runtime: {report.runtime}
                    </Typography>
                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                      <Chip label={`${report.total_tool_calls} tool calls`} size="small" />
                      <Chip label={`${report.total_a2a_messages} A2A messages`} size="small" />
                      <Chip label={`${report.total_failures} failures`} size="small" />
                    </Stack>
                    <Typography variant="body2">
                      Recommended: {report.scorecard.recommended_demo_mode.toUpperCase()}
                    </Typography>
                    <Button
                      component={RouterLink}
                      to={`/reports/${encodeURIComponent(report.report_name)}`}
                      variant="text"
                      sx={{ alignSelf: "flex-start", px: 0 }}
                    >
                      Open report detail
                    </Button>
                  </Stack>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Stack>
  );
}
