import { Box, Typography } from "@mui/material";
import { useMemo } from "react";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getProtocolColor } from "../../lib/trace/eventColors";
import { traceEventActor } from "../../lib/trace/utils";
import type { TraceEvent } from "../../lib/types/api";

interface TimelineBar {
  agent: string;
  offset: number;
  duration: number;
  color: string;
}

interface ParallelAgentTimelineProps {
  events: TraceEvent[];
  mode: string;
}

const MIN_DURATION_MS = 20;

function buildTimelineBars(events: TraceEvent[], mode: string): TimelineBar[] {
  const color = getProtocolColor(mode);

  // Try parallel events first: events with parallel_batch_id + started_at + completed_at
  const parallelEvents = events.filter(
    (e) =>
      e.parallel_batch_id != null &&
      e.started_at != null &&
      e.completed_at != null,
  );

  if (parallelEvents.length > 0) {
    const starts = parallelEvents.map((e) => e.started_at as number);
    const minStart = Math.min(...starts);

    return parallelEvents.map((e) => ({
      agent: traceEventActor(e),
      offset: (e.started_at as number) - minStart,
      duration: Math.max((e.completed_at as number) - (e.started_at as number), MIN_DURATION_MS),
      color,
    }));
  }

  // Sequential fallback: events with step_index, sorted by step_index
  const stepEvents = events
    .filter((e) => e.step_index != null)
    .sort((a, b) => (a.step_index as number) - (b.step_index as number));

  if (stepEvents.length > 0) {
    const firstEvent = stepEvents[0]!;
    const minTs = firstEvent.timestamp_ms;

    return stepEvents.map((e, i) => {
      const offset = e.timestamp_ms - minTs;
      const nextEvent = stepEvents[i + 1];
      const nextTs = nextEvent != null ? nextEvent.timestamp_ms : null;
      const duration = nextTs != null ? Math.max(nextTs - e.timestamp_ms, MIN_DURATION_MS) : 50;

      return {
        agent: traceEventActor(e),
        offset,
        duration,
        color,
      };
    });
  }

  return [];
}

export function ParallelAgentTimeline({ events, mode }: ParallelAgentTimelineProps) {
  const bars = useMemo(() => buildTimelineBars(events, mode), [events, mode]);

  if (bars.length === 0) return null;

  const barHeight = 28;
  const chartHeight = bars.length * (barHeight + 12) + 40;

  return (
    <Box>
      <Typography variant="caption" sx={{ color: "text.secondary", mb: 0.5, display: "block" }}>
        Agent Timeline
      </Typography>
      <ResponsiveContainer width="100%" height={chartHeight}>
        <BarChart layout="vertical" data={bars} barSize={barHeight} margin={{ top: 5, right: 20, bottom: 5, left: 10 }}>
          <XAxis type="number" domain={[0, "dataMax"]} tickFormatter={(v: number) => `${v}ms`} />
          <YAxis type="category" dataKey="agent" width={100} tick={{ fontSize: 12 }} />
          <Tooltip
            formatter={(value, name) =>
              name === "offset" ? ["", ""] : [`${Number(value)}ms`, "Duration"]
            }
            labelFormatter={(label) => `Agent: ${String(label)}`}
          />
          {/* Invisible offset bar — Gantt spacer */}
          <Bar dataKey="offset" stackId="timeline" fill="transparent" isAnimationActive={false} />
          {/* Visible duration bar */}
          <Bar dataKey="duration" stackId="timeline" isAnimationActive={false}>
            {bars.map((bar, i) => (
              <Cell key={i} fill={bar.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </Box>
  );
}
