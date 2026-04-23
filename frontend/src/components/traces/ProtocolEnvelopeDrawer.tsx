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
  Tooltip,
  Typography,
} from "@mui/material";

import type { TraceEvent } from "../../lib/types/api";
import { isA2AEvent, traceEventProtocol, traceLabel } from "../../lib/trace/utils";

interface ProtocolEnvelopeDrawerProps {
  event: TraceEvent | null;
  onClose: () => void;
}

// Spec field annotations — explains each key a learner might not recognise
const FIELD_ANNOTATIONS: Record<string, string> = {
  protocolVersion: "A2A spec version — must be '1.0' for interoperability.",
  messageId: "Unique message ID for idempotency and tracing.",
  taskId: "Links this message to the task lifecycle (submitted → working → completed).",
  contextId: "Groups related messages in one conversation context.",
  role: "ROLE_USER = sent by orchestrator. ROLE_AGENT = reply from specialist.",
  parts: "Multi-modal payload array. Each part has a 'kind': text, data, or file.",
  skills: "A2A Agent Card capabilities — what tasks this agent can accept.",
  preferredTransport: "Transport hint: JSONRPC over HTTP(S) is the A2A default.",
  "capabilities.streaming": "Whether this agent supports SSE streaming responses.",
  kind: "Event shape: 'status-update' = lifecycle signal, 'artifact-update' = result payload.",
  final: "true = task is done (completed or failed), no more status events expected.",
  artifactId: "Stable ID for the result artifact — used to update partial artifacts.",
  protocol: "official_mcp_sdk = real MCP SDK, not a hand-rolled wrapper.",
  transport: "in_process | stdio | http | remote_http — actual transport used.",
  requested_transport: "The transport the caller asked for (may differ if fallback occurred).",
  tools: "MCP tool list discovered via tools/list — name, description, inputSchema.",
  arguments: "JSON arguments passed to the MCP tool call.",
  "status.state": "A2A task state machine: submitted → working → completed | failed | canceled.",
};

function annotate(key: string, parentKey?: string): string | undefined {
  const full = parentKey ? `${parentKey}.${key}` : key;
  return FIELD_ANNOTATIONS[full] ?? FIELD_ANNOTATIONS[key];
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

// Recursively render JSON with per-key tooltips for known spec fields
function JsonTree({
  data,
  depth = 0,
  parentKey,
}: {
  data: unknown;
  depth?: number;
  parentKey?: string;
}) {
  if (data === null || data === undefined) {
    return <span style={{ color: "#888" }}>null</span>;
  }
  if (typeof data === "boolean") {
    return <span style={{ color: "#c0392b" }}>{String(data)}</span>;
  }
  if (typeof data === "number") {
    return <span style={{ color: "#2980b9" }}>{data}</span>;
  }
  if (typeof data === "string") {
    return <span style={{ color: "#27ae60" }}>&quot;{data}&quot;</span>;
  }
  if (Array.isArray(data)) {
    if (data.length === 0) return <span>[]</span>;
    return (
      <Box component="span">
        {"["}
        <Box component="div" sx={{ ml: 2 }}>
          {data.map((item, idx) => (
            <Box key={idx} component="div">
              <JsonTree data={item} depth={depth + 1} />
              {idx < data.length - 1 ? "," : ""}
            </Box>
          ))}
        </Box>
        {"]"}
      </Box>
    );
  }
  if (typeof data === "object") {
    const entries = Object.entries(data as Record<string, unknown>);
    if (entries.length === 0) return <span>{"{}"}</span>;
    return (
      <Box component="span">
        {"{"}
        <Box component="div" sx={{ ml: 2 }}>
          {entries.map(([key, value], idx) => {
            const note = annotate(key, parentKey);
            return (
              <Box key={key} component="div" sx={{ display: "flex", alignItems: "flex-start", gap: 0.5 }}>
                <Tooltip title={note ?? ""} placement="left" arrow disableHoverListener={!note}>
                  <Box
                    component="span"
                    sx={{
                      color: note ? "secondary.main" : "primary.main",
                      fontWeight: note ? 600 : 400,
                      cursor: note ? "help" : "default",
                      textDecoration: note ? "underline dotted" : "none",
                      whiteSpace: "nowrap",
                    }}
                  >
                    &quot;{key}&quot;
                  </Box>
                </Tooltip>
                <span>:{" "}</span>
                <JsonTree data={value} depth={depth + 1} parentKey={key} />
                {idx < entries.length - 1 ? "," : ""}
              </Box>
            );
          })}
        </Box>
        {"}"}
      </Box>
    );
  }
  return <span>{String(data)}</span>;
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
