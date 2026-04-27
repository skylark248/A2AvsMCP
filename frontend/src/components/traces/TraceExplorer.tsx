import FilterAltOutlinedIcon from "@mui/icons-material/FilterAltOutlined";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import HubOutlinedIcon from "@mui/icons-material/HubOutlined";
import PrecisionManufacturingOutlinedIcon from "@mui/icons-material/PrecisionManufacturingOutlined";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import {
  Alert,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Typography,
} from "@mui/material";
import { useMemo, useState } from "react";

import { eventBorderColor, getProtocolColor } from "../../lib/trace/eventColors";
import {
  groupA2AEventsByTaskId,
  isA2AEvent,
  isTraceFailureEvent,
  traceEventActor,
  traceEventProtocol,
  traceEventSummary,
  traceEventTone,
  traceLabel,
  uniqueTraceValues,
} from "../../lib/trace/utils";
import type { TraceEvent } from "../../lib/types/api";

interface TraceExplorerProps {
  events: TraceEvent[];
  title?: string;
  subtitle?: string;
  runtime?: string;
}

export function TraceExplorer({ events, title = "Trace Explorer", subtitle, runtime }: TraceExplorerProps) {
  const [eventFilter, setEventFilter] = useState<string>("all");
  const [actorFilter, setActorFilter] = useState<string>("all");
  const [toolFilter, setToolFilter] = useState<string>("all");
  const [protocolFilter, setProtocolFilter] = useState<string>("all");
  const [failureFilter, setFailureFilter] = useState<string>("all");

  const eventTypes = useMemo(() => uniqueTraceValues(events, (event) => traceLabel(event)), [events]);
  const actors = useMemo(() => uniqueTraceValues(events, (event) => traceEventActor(event)), [events]);
  const tools = useMemo(() => uniqueTraceValues(events, (event) => event.tool), [events]);
  const protocols = useMemo(() => uniqueTraceValues(events, (event) => traceEventProtocol(event)), [events]);

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      if (eventFilter !== "all" && traceLabel(event) !== eventFilter) {
        return false;
      }
      if (actorFilter !== "all" && traceEventActor(event) !== actorFilter) {
        return false;
      }
      if (toolFilter !== "all" && (event.tool ?? "") !== toolFilter) {
        return false;
      }
      if (protocolFilter !== "all" && traceEventProtocol(event) !== protocolFilter) {
        return false;
      }
      if (failureFilter === "only_failures" && !isTraceFailureEvent(event)) {
        return false;
      }
      return true;
    });
  }, [actorFilter, eventFilter, events, failureFilter, protocolFilter, toolFilter]);

  const stats = useMemo(() => {
    const toolCalls = events.filter((e) => e.event_type === "tool_call").length;
    const a2aMessages = events.filter(isA2AEvent).length;
    const failures = events.filter(isTraceFailureEvent).length;
    const retries = events.filter(
      (e) => e.message_type === "task_retry" || e.event_type === "a2a_remote_retry",
    ).length;
    const discoveryEvents = events.filter((e) => e.phase === "discovery").length;
    const executionEvents = events.filter((e) => e.phase === "execution").length;
    return { toolCalls, a2aMessages, failures, retries, discoveryEvents, executionEvents };
  }, [events]);

  return (
    <Card>
      <CardContent>
        <Stack spacing={2}>
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start">
            <Stack spacing={0.5}>
              <Typography variant="h6">{title}</Typography>
              <Typography variant="body2" sx={{ color: "text.secondary" }}>
                {subtitle ?? "Filter the protocol timeline by event type, actor, tool, and failure state."}
              </Typography>
            </Stack>
            {runtime === "llm" && (
              <Chip
                label="Expect 2-5s per LLM call"
                size="small"
                color="warning"
                icon={<WarningAmberRoundedIcon fontSize="small" />}
              />
            )}
          </Stack>

          <Grid container spacing={1.5}>
            <Grid size={{ xs: 6, md: 3 }}>
              <TraceStat
                label="Tool Calls"
                value={stats.toolCalls}
                icon={<PrecisionManufacturingOutlinedIcon fontSize="small" />}
              />
            </Grid>
            <Grid size={{ xs: 6, md: 3 }}>
              <TraceStat label="A2A Messages" value={stats.a2aMessages} icon={<HubOutlinedIcon fontSize="small" />} />
            </Grid>
            <Grid size={{ xs: 6, md: 3 }}>
              <TraceStat label="Failures" value={stats.failures} icon={<WarningAmberRoundedIcon fontSize="small" />} />
            </Grid>
            <Grid size={{ xs: 6, md: 3 }}>
              <TraceStat
                label="Visible Events"
                value={filteredEvents.length}
                icon={<FilterAltOutlinedIcon fontSize="small" />}
              />
            </Grid>
          </Grid>

          <Grid container spacing={1.5}>
            <Grid size={{ xs: 12, md: 6, xl: 2.4 }}>
              <TraceSelect label="Event" value={eventFilter} options={eventTypes} onChange={setEventFilter} />
            </Grid>
            <Grid size={{ xs: 12, md: 6, xl: 2.4 }}>
              <TraceSelect label="Actor" value={actorFilter} options={actors} onChange={setActorFilter} />
            </Grid>
            <Grid size={{ xs: 12, md: 6, xl: 2.4 }}>
              <TraceSelect label="Tool" value={toolFilter} options={tools} onChange={setToolFilter} />
            </Grid>
            <Grid size={{ xs: 12, md: 6, xl: 2.4 }}>
              <TraceSelect label="Protocol" value={protocolFilter} options={protocols} onChange={setProtocolFilter} />
            </Grid>
            <Grid size={{ xs: 12, md: 6, xl: 2.4 }}>
              <FormControl fullWidth size="small">
                <InputLabel id="failure-filter-label">Failures</InputLabel>
                <Select
                  labelId="failure-filter-label"
                  label="Failures"
                  value={failureFilter}
                  onChange={(event) => setFailureFilter(event.target.value)}
                >
                  <MenuItem value="all">All events</MenuItem>
                  <MenuItem value="only_failures">Only failures and warnings</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>

          <Divider />

          {runtime !== undefined && runtime !== "mock" && (
            <Alert severity="warning" sx={{ mb: 1 }}>
              This run used OpenAI GPT-4o-mini — latency reflects real API calls.
            </Alert>
          )}

          {/* === Tier 0: Summary Strip (always visible) === */}
          <Stack direction="row" spacing={2} flexWrap="wrap" useFlexGap
            sx={{ px: 1, py: 0.75, bgcolor: "action.hover", borderRadius: 1 }}>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              <strong>{events.length}</strong> total
            </Typography>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              <strong>{stats.toolCalls}</strong> tool calls
            </Typography>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              <strong>{stats.a2aMessages}</strong> A2A messages
            </Typography>
            <Typography variant="caption" sx={{ color: "text.secondary" }}>
              <strong>{stats.discoveryEvents}</strong> discovery / <strong>{stats.executionEvents}</strong> execution
            </Typography>
          </Stack>

          {/* === Tier 1: Protocol-Level (collapsed by default) === */}
          <Accordion defaultExpanded={false} disableGutters>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle2">
                Protocol Events
                <Typography component="span" variant="caption" sx={{ ml: 1, color: "text.secondary" }}>
                  ({filteredEvents.length} visible)
                </Typography>
              </Typography>
            </AccordionSummary>
            <AccordionDetails sx={{ p: 0 }}>
              <ProtocolTier events={filteredEvents} />
            </AccordionDetails>
          </Accordion>

          {/* === Tier 2: Full Trace (collapsed by default) === */}
          <Accordion defaultExpanded={false} disableGutters>
            <AccordionSummary expandIcon={<ExpandMoreIcon />}>
              <Typography variant="subtitle2">
                Full Trace
                <Typography component="span" variant="caption" sx={{ ml: 1, color: "text.secondary" }}>
                  (raw JSON)
                </Typography>
              </Typography>
            </AccordionSummary>
            <AccordionDetails>
              <FullTraceTier events={filteredEvents} />
            </AccordionDetails>
          </Accordion>

        </Stack>
      </CardContent>
    </Card>
  );
}

const RENDER_CAP = 150;

function ProtocolTier({ events }: { events: TraceEvent[] }) {
  const nonA2AEvents = events.filter(
    (e) => !isA2AEvent(e) && e.event_type !== "task_status" &&
           e.event_type !== "task_submit" && e.event_type !== "task_complete"
  );
  const a2aGroups = groupA2AEventsByTaskId(events);

  const nonA2ARows = nonA2AEvents.slice(0, RENDER_CAP);
  const groupEntries = Array.from(a2aGroups.entries());
  const cappedGroups = groupEntries.slice(0, Math.max(0, RENDER_CAP - nonA2ARows.length));
  const totalRows = nonA2ARows.length + cappedGroups.length;
  const cappedTotal = nonA2AEvents.length + a2aGroups.size;
  const isCapped = cappedTotal > RENDER_CAP;

  return (
    <Stack spacing={0.75} sx={{ p: 1 }}>
      {isCapped && (
        <Typography variant="caption" sx={{ color: "warning.main", px: 1 }}>
          Showing {totalRows} of {cappedTotal} events. Open Full Trace to see all.
        </Typography>
      )}
      {nonA2ARows.map((event) => (
        <ProtocolEventRow key={`${event.index}-${event.event_type}`} event={event} />
      ))}
      {cappedGroups.map(([taskId, groupEvents]) => {
        const lastStatus = [...groupEvents].reverse().find((e) => e.status)?.status ?? "unknown";
        return (
          <Accordion key={taskId} defaultExpanded={false} disableGutters
            sx={{ border: "1px solid", borderColor: "divider", borderRadius: "4px !important" }}>
            <AccordionSummary expandIcon={<ExpandMoreIcon />} sx={{ minHeight: 36, "& .MuiAccordionSummary-content": { my: 0.5 } }}>
              <Stack direction="row" spacing={1} alignItems="center">
                <Typography variant="caption" sx={{ fontFamily: "monospace" }}>{taskId}</Typography>
                <Chip label={lastStatus} size="small"
                  color={lastStatus === "completed" ? "success" : lastStatus === "failed" ? "error" : "default"} />
                <Typography variant="caption" sx={{ color: "text.secondary" }}>
                  {groupEvents.length} events
                </Typography>
              </Stack>
            </AccordionSummary>
            <AccordionDetails sx={{ p: 0.5 }}>
              <Stack spacing={0.5}>
                {groupEvents.map((e) => (
                  <ProtocolEventRow key={`${e.index}-${e.event_type}`} event={e} />
                ))}
              </Stack>
            </AccordionDetails>
          </Accordion>
        );
      })}
    </Stack>
  );
}

function ProtocolEventRow({ event }: { event: TraceEvent }) {
  const tone = traceEventTone(event);
  const borderColor = eventBorderColor(event);
  return (
    <Stack direction="row" spacing={1} alignItems="center"
      sx={{ px: 1, py: 0.5, borderLeft: `3px solid ${borderColor}`, borderRadius: 0.5, bgcolor: "background.paper" }}>
      <Chip label={`#${event.index}`} size="small" sx={{ fontSize: "0.65rem", height: 18 }} />
      {event.step_index !== undefined && (
        <Chip label={`S${event.step_index}`} size="small" color="primary"
          sx={{ fontSize: "0.65rem", height: 18 }} title="Step index" />
      )}
      <Chip label={traceLabel(event)} size="small"
        color={tone === "error" ? "error" : tone === "warning" ? "warning" : tone === "success" ? "success" : "default"} />
      {event.phase === "discovery" && (
        <Chip label="discovery" size="small" variant="outlined" sx={{ fontSize: "0.65rem", height: 18 }} />
      )}
      <Typography variant="caption" sx={{ flex: 1 }}>{traceEventSummary(event)}</Typography>
      <Typography variant="caption" sx={{ color: "text.secondary" }}>{traceEventActor(event)}</Typography>
    </Stack>
  );
}

function FullTraceTier({ events }: { events: TraceEvent[] }) {
  const capped = events.slice(0, RENDER_CAP);
  const isCapped = events.length > RENDER_CAP;
  return (
    <Stack spacing={0.5}>
      {isCapped && (
        <Typography variant="caption" sx={{ color: "warning.main" }}>
          Showing {RENDER_CAP} of {events.length} events. The saved JSON file contains the complete trace.
        </Typography>
      )}
      {capped.map((event) => (
        <Card key={`${event.index}-${event.event_type}-${event.timestamp_ms}`} variant="outlined"
          sx={{ borderLeft: `4px solid ${getProtocolColor("mcp")}` }}>
          <CardContent sx={{ pb: "8px !important", pt: "8px !important" }}>
            <Typography variant="caption" sx={{ fontFamily: "monospace", whiteSpace: "pre-wrap", wordBreak: "break-all" }}>
              {JSON.stringify(event, null, 2)}
            </Typography>
          </CardContent>
        </Card>
      ))}
    </Stack>
  );
}

function TraceSelect(props: { label: string; value: string; options: string[]; onChange: (value: string) => void }) {
  return (
    <FormControl fullWidth size="small">
      <InputLabel id={`${props.label}-label`}>{props.label}</InputLabel>
      <Select
        labelId={`${props.label}-label`}
        label={props.label}
        value={props.value}
        onChange={(event) => props.onChange(event.target.value)}
      >
        <MenuItem value="all">All</MenuItem>
        {props.options.map((option) => (
          <MenuItem key={option} value={option}>
            {option}
          </MenuItem>
        ))}
      </Select>
    </FormControl>
  );
}

function TraceStat(props: { label: string; value: number; icon: React.ReactNode }) {
  return (
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent sx={{ pb: "16px !important" }}>
        <Stack direction="row" justifyContent="space-between" alignItems="center">
          <Stack spacing={0.5}>
            <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.12em" }}>
              {props.label}
            </Typography>
            <Typography variant="h6" sx={{ color: "primary.main" }}>
              {props.value}
            </Typography>
          </Stack>
          {props.icon}
        </Stack>
      </CardContent>
    </Card>
  );
}
