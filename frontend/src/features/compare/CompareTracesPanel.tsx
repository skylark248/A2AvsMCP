import {
  Box,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useCallback, useRef, useState } from "react";

import { TraceExplorer } from "../../components/traces/TraceExplorer";
import { getProtocolColor } from "../../lib/trace/eventColors";
import type { RunResult } from "../../lib/types/api";

interface CompareTracesPanelProps {
  results: RunResult[];
}

export function CompareTracesPanel({ results }: CompareTracesPanelProps) {
  const modes = results.map((r) => r.mode);
  const [modeA, setModeA] = useState<string>(modes[0] ?? "");
  const [modeB, setModeB] = useState<string>(modes[1] ?? modes[0] ?? "");

  const scrollRefA = useRef<HTMLDivElement>(null);
  const scrollRefB = useRef<HTMLDivElement>(null);
  const syncing = useRef(false);

  // D-09: Synchronized scrolling with mutex guard (RESEARCH.md Pitfall 2)
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

      {/* D-08: Two synchronized TraceExplorer columns */}
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
    </Stack>
  );
}
