import CloseOutlinedIcon from "@mui/icons-material/CloseOutlined";
import CodeOutlinedIcon from "@mui/icons-material/CodeOutlined";
import HubOutlinedIcon from "@mui/icons-material/HubOutlined";
import PrecisionManufacturingOutlinedIcon from "@mui/icons-material/PrecisionManufacturingOutlined";
import {
  Alert,
  Box,
  Chip,
  Divider,
  Drawer,
  IconButton,
  Stack,
  Typography,
} from "@mui/material";

import { JsonTree } from "../../lib/trace/JsonTree";
import type { TraceEvent } from "../../lib/types/api";
import { isA2AEvent, traceEventProtocol, traceLabel } from "../../lib/trace/utils";

interface ProtocolEnvelopeDrawerProps {
  event: TraceEvent | null;
  onClose: () => void;
}

// Extract the interesting envelope fields from a trace event
function envelopePayload(event: TraceEvent): { label: string; data: unknown }[] {
  const chunks: { label: string; data: unknown }[] = [];
  const proto = traceEventProtocol(event);

  if (proto === "a2a" || isA2AEvent(event)) {
    if (event.a2a_agent_card) chunks.push({ label: "Agent Card (A2A spec)", data: event.a2a_agent_card });
    if (event.a2a_message) chunks.push({ label: "Message Envelope (A2A spec)", data: event.a2a_message });
    if (event.a2a_task_event) chunks.push({ label: "Status-Update Event (A2A spec)", data: event.a2a_task_event });
    if (event.a2a_artifact_event) chunks.push({ label: "Artifact-Update Event (A2A spec)", data: event.a2a_artifact_event });
    if (event.a2a_task) chunks.push({ label: "Task Snapshot (A2A spec)", data: event.a2a_task });
  }

  if (proto === "mcp" || event.event_type === "tool_call" || event.event_type === "tool_discovery") {
    if (event.arguments) chunks.push({ label: "Tool Call Arguments (MCP)", data: event.arguments });
    if (event.tools) chunks.push({ label: "Discovered Tools (MCP tools/list)", data: event.tools });
  }

  // Fallback: strip noise fields and show the raw event
  if (chunks.length === 0) {
    const { index: _i, timestamp_ms: _t, ...rest } = event;
    chunks.push({ label: "Raw Trace Event", data: rest });
  }

  return chunks;
}

const PROTO_NOTES: Record<string, string> = {
  a2a:
    "A2A 1.0 protocol shapes: Agent Cards advertise skills, message/send exchanges tasks, tasks/get retrieves status. Underlined fields have spec annotations — hover to read.",
  mcp:
    "MCP protocol shapes: tools/list discovers capabilities, tools/call invokes them. The official Python MCP SDK handles JSON-RPC serialisation and transport.",
  runtime:
    "Internal runtime event — not part of MCP or A2A wire format, but useful for tracing orchestration logic.",
};

export function ProtocolEnvelopeDrawer({ event, onClose }: ProtocolEnvelopeDrawerProps) {
  const open = Boolean(event);
  const proto = event ? traceEventProtocol(event) : "runtime";
  const label = event ? traceLabel(event) : "";
  const chunks = event ? envelopePayload(event) : [];
  const isA2A = proto === "a2a";
  const isMCP = proto === "mcp";

  return (
    <Drawer
      anchor="right"
      open={open}
      onClose={onClose}
      PaperProps={{ sx: { width: { xs: "100%", sm: 520 }, p: 3, display: "flex", flexDirection: "column", gap: 2 } }}
    >
      <Stack direction="row" alignItems="center" justifyContent="space-between">
        <Stack direction="row" spacing={1} alignItems="center">
          {isA2A ? (
            <HubOutlinedIcon color="secondary" />
          ) : isMCP ? (
            <PrecisionManufacturingOutlinedIcon color="secondary" />
          ) : (
            <CodeOutlinedIcon color="secondary" />
          )}
          <Typography variant="h6">Protocol Envelope</Typography>
        </Stack>
        <IconButton onClick={onClose} size="small" aria-label="close envelope drawer">
          <CloseOutlinedIcon />
        </IconButton>
      </Stack>

      <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
        <Chip label={label} size="small" />
        <Chip
          label={proto.toUpperCase()}
          size="small"
          color={isA2A ? "secondary" : isMCP ? "primary" : "default"}
          variant="outlined"
        />
        {event?.transport ? <Chip label={`transport: ${String(event.transport)}`} size="small" variant="outlined" /> : null}
        {event?.requested_transport && event.requested_transport !== event.transport ? (
          <Chip label={`requested: ${String(event.requested_transport)}`} size="small" variant="outlined" color="warning" />
        ) : null}
      </Stack>

      <Alert severity="info" icon={false} sx={{ fontSize: "0.78rem", py: 0.5 }}>
        {PROTO_NOTES[proto] ?? PROTO_NOTES.runtime}
      </Alert>

      <Divider />

      <Box sx={{ overflowY: "auto", flex: 1 }}>
        <Stack spacing={3}>
          {chunks.map(({ label: chunkLabel, data }) => (
            <Box key={chunkLabel}>
              <Typography
                variant="overline"
                sx={{ color: "secondary.main", letterSpacing: "0.14em", display: "block", mb: 1 }}
              >
                {chunkLabel}
              </Typography>
              <Box
                sx={{
                  background: "#1a2332",
                  borderRadius: 1,
                  p: 2,
                  fontFamily: "monospace",
                  fontSize: "0.72rem",
                  lineHeight: 1.6,
                  color: "#e8e8e8",
                  overflowX: "auto",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                <JsonTree data={data} />
              </Box>
            </Box>
          ))}
        </Stack>
      </Box>
    </Drawer>
  );
}
