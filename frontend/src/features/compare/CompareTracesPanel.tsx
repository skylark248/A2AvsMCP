import {
  Box,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import { useCallback, useRef, useState } from "react";

import { AnnotatedDiffView } from "../../components/traces/AnnotatedDiffView";
import { DiscoveryPhasePanel } from "../../components/traces/DiscoveryPhasePanel";
import { TraceExplorer } from "../../components/traces/TraceExplorer";
import { getProtocolColor } from "../../lib/trace/eventColors";
import type { RunResult, TraceEvent } from "../../lib/types/api";

// W-6 mitigation: stable empty-array reference prevents useMemo invalidation
// in AnnotatedDiffView when resultA/resultB are undefined.
const EMPTY_EVENTS: TraceEvent[] = [];

// View mode type — 'side-by-side' is the non-regressing default (D-75)
type CompareViewMode = "side-by-side" | "diff";

interface CompareTracesPanelProps {
  results: RunResult[];
}

export function CompareTracesPanel({ results }: CompareTracesPanelProps) {
  const modes = results.map((r) => r.mode);
  const [modeA, setModeA] = useState<string>(modes[0] ?? "");
  const [modeB, setModeB] = useState<string>(modes[1] ?? modes[0] ?? "");

  // D-75: in-place viewMode toggle — defaults to Side-by-side (no regression)
  const [viewMode, setViewMode] = useState<CompareViewMode>("side-by-side");

  const scrollRefA = useRef<HTMLDivElement>(null);
  const scrollRefB = useRef<HTMLDivElement>(null);
  const syncing = useRef(false);

  // D-09: Synchronized scrolling with mutex guard (RESEARCH.md Pitfall 2)
  // Refs are simply inert when viewMode === 'diff' because the dual-column
  // Boxes are not in the rendered tree. Refs reattach automatically on toggle
  // round-trip (RESEARCH §2 — acceptable behavior).
  const handleScroll = useCallback((source: "a" | "b") => {
    if (syncing.current) return;
    syncing.current = true;
    const from = source === "a" ? scrollRefA.current : scrollRefB.current;
    const to = source === "a" ? scrollRefB.current : scrollRefA.current;
    if (from && to) {
      to.scrollTop = from.scrollTop;
    }
    requestAnimationFrame(() => {
      syncing.current = false;
    });
  }, []);

  const resultA = results.find((r) => r.mode === modeA);
  const resultB = results.find((r) => r.mode === modeB);

  const allEvents = [...(resultA?.trace ?? []), ...(resultB?.trace ?? [])];
  const discoveryMcpEvents = allEvents.filter(
    (e) => e.event_type === "tool_discovery" && !(e as { remote_agent?: unknown }).remote_agent,
  );
  const discoveryA2aEvents = allEvents.filter(
    (e) =>
      (e.event_type === "tool_discovery" && Boolean((e as { remote_agent?: unknown }).remote_agent)) ||
      e.event_type === "a2a_remote_discovery",
  );
  const showDiscoveryPanel = discoveryMcpEvents.length > 0 || discoveryA2aEvents.length > 0;
  const discoveryScenario =
    resultA?.ticket?.scenario ?? resultB?.ticket?.scenario ?? "tool_discovery";

  return (
    <Stack spacing={2}>
      {/* D-08: Mode A / Mode B selectors */}
      <Grid container spacing={2}>
        <Grid size={{ xs: 12, sm: 6 }}>
          <FormControl fullWidth size="small">
            <InputLabel id="mode-a-label">Mode A</InputLabel>
            <Select
              labelId="mode-a-label"
              label="Mode A"
              value={modeA}
              onChange={(e) => setModeA(e.target.value)}
            >
              {modes.map((m) => (
                <MenuItem key={m} value={m}>
                  <Typography
                    component="span"
                    sx={{ color: getProtocolColor(m), fontWeight: 600, textTransform: "uppercase" }}
                  >
                    {m}
                  </Typography>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid size={{ xs: 12, sm: 6 }}>
          <FormControl fullWidth size="small">
            <InputLabel id="mode-b-label">Mode B</InputLabel>
            <Select
              labelId="mode-b-label"
              label="Mode B"
              value={modeB}
              onChange={(e) => setModeB(e.target.value)}
            >
              {modes.map((m) => (
                <MenuItem key={m} value={m}>
                  <Typography
                    component="span"
                    sx={{ color: getProtocolColor(m), fontWeight: 600, textTransform: "uppercase" }}
                  >
                    {m}
                  </Typography>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
      </Grid>

      {/* D-75: View mode toggle — right-aligned, between Mode A/B Grid and discovery panel.
          Per UI-SPEC lines 200-207: size="small", exclusive, aria-label="View mode".
          B-3 mitigation: do NOT pass leftProtocolLabel/rightProtocolLabel — let AnnotatedDiffView
          defaults apply ("MCP — Trace A", "A2A — Trace B") to preserve Copywriting Contract. */}
      <Stack direction="row" justifyContent="flex-end">
        <ToggleButtonGroup
          value={viewMode}
          exclusive
          size="small"
          aria-label="View mode"
          onChange={(_e, next) => {
            if (next === "side-by-side" || next === "diff") setViewMode(next);
          }}
        >
          <ToggleButton value="side-by-side">Side-by-side</ToggleButton>
          <ToggleButton value="diff">Annotated diff</ToggleButton>
        </ToggleButtonGroup>
      </Stack>

      {/* D-72: Single full-width DiscoveryPhasePanel above dual-column Grid (presence-gated).
          This block is ABOVE the viewMode conditional — it remains visible in BOTH view modes. */}
      {showDiscoveryPanel ? (
        <DiscoveryPhasePanel
          mcpEvents={discoveryMcpEvents}
          a2aEvents={discoveryA2aEvents}
          scenario={discoveryScenario}
        />
      ) : null}

      {/* D-75: Conditional body — swap dual-column for AnnotatedDiffView when viewMode==='diff' */}
      {viewMode === "side-by-side" ? (
        /* D-08: Two synchronized TraceExplorer columns */
        <Grid container spacing={2} alignItems="flex-start">
          <Grid size={{ xs: 12, md: 6 }}>
            <Box
              ref={scrollRefA}
              onScroll={() => handleScroll("a")}
              sx={{ overflowY: "auto", maxHeight: 600 }}
            >
              {resultA ? (
                <TraceExplorer
                  events={resultA.trace}
                  title={`${resultA.mode.toUpperCase()} Trace`}
                  subtitle={`${resultA.trace.length} events`}
                  runtime={resultA.runtime}
                />
              ) : (
                <Typography variant="body2" sx={{ color: "text.secondary" }}>
                  Select Mode A above.
                </Typography>
              )}
            </Box>
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            <Box
              ref={scrollRefB}
              onScroll={() => handleScroll("b")}
              sx={{ overflowY: "auto", maxHeight: 600 }}
            >
              {resultB ? (
                <TraceExplorer
                  events={resultB.trace}
                  title={`${resultB.mode.toUpperCase()} Trace`}
                  subtitle={`${resultB.trace.length} events`}
                  runtime={resultB.runtime}
                />
              ) : (
                <Typography variant="body2" sx={{ color: "text.secondary" }}>
                  Select Mode B above.
                </Typography>
              )}
            </Box>
          </Grid>
        </Grid>
      ) : (
        /* W-6: Use EMPTY_EVENTS (not inline []) to keep useMemo in AnnotatedDiffView stable */
        <AnnotatedDiffView
          leftEvents={resultA?.trace ?? EMPTY_EVENTS}
          rightEvents={resultB?.trace ?? EMPTY_EVENTS}
        />
      )}
    </Stack>
  );
}
