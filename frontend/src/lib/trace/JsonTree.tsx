import { Box, Tooltip } from "@mui/material";

// Spec field annotations — explains each key a learner might not recognise
export const FIELD_ANNOTATIONS: Record<string, string> = {
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

export function annotate(key: string, parentKey?: string): string | undefined {
  const full = parentKey ? `${parentKey}.${key}` : key;
  return FIELD_ANNOTATIONS[full] ?? FIELD_ANNOTATIONS[key];
}

// Recursively render JSON with per-key tooltips for known spec fields
export function JsonTree({
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
