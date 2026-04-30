import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import WarningAmberRoundedIcon from "@mui/icons-material/WarningAmberRounded";
import Accordion from "@mui/material/Accordion";
import AccordionDetails from "@mui/material/AccordionDetails";
import AccordionSummary from "@mui/material/AccordionSummary";
import { Box, Card, CardContent, Chip, Grid, Stack, Tooltip, Typography } from "@mui/material";
import { useMemo } from "react";

import { protocolColor, toneColor } from "../../lib/trace/eventColors";
import { JsonTree } from "../../lib/trace/JsonTree";
import type { TraceEvent } from "../../lib/types/api";

export interface DiscoveryPhasePanelProps {
  mcpEvents: TraceEvent[];
  a2aEvents: TraceEvent[];
  scenario: string;
  defaultExpanded?: boolean;
}

interface McpToolDescriptor {
  name: string;
  description?: string;
  inputSchema?: unknown;
}

function coerceToolDescriptor(entry: unknown): McpToolDescriptor | null {
  if (typeof entry === "string") {
    return { name: entry };
  }
  if (entry && typeof entry === "object") {
    const obj = entry as Record<string, unknown>;
    const name = typeof obj.name === "string" ? obj.name : undefined;
    if (!name) return null;
    return {
      name,
      description: typeof obj.description === "string" ? obj.description : undefined,
      inputSchema:
        obj.inputSchema && typeof obj.inputSchema === "object" ? obj.inputSchema : undefined,
    };
  }
  return null;
}

function renderMcpToolCards(event: TraceEvent, relMs: number) {
  const tools = Array.isArray(event.tools) ? (event.tools as unknown[]) : [];
  const requestedTransport =
    typeof event.requested_transport === "string" ? event.requested_transport : undefined;
  const transport = typeof event.transport === "string" ? event.transport : undefined;
  const isFallback = Boolean(requestedTransport) && requestedTransport !== transport;

  return tools
    .map((entry, idx) => {
      const tool = coerceToolDescriptor(entry);
      if (!tool) return null;
      return (
        <Card
          key={`${event.index}-${tool.name}-${idx}`}
          variant="outlined"
          sx={{
            borderRadius: 2,
            mb: 1,
            borderLeft: isFallback ? `2px solid ${toneColor.warning}` : undefined,
          }}
        >
          <CardContent sx={{ py: 1.5 }}>
            <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
              <Stack spacing={0.5} sx={{ minWidth: 0, flex: 1 }}>
                <Typography variant="body2" fontWeight={600}>
                  {tool.name}
                </Typography>
                {tool.description ? (
                  <Typography variant="body2" color="text.secondary">
                    {tool.description}
                  </Typography>
                ) : null}
              </Stack>
              <Stack direction="row" spacing={1} alignItems="center">
                {isFallback ? (
                  <Tooltip title="Stale capability cache — tool list returned no match for this query">
                    <WarningAmberRoundedIcon
                      aria-label="Stale capability cache"
                      fontSize="small"
                      sx={{ color: toneColor.warning }}
                    />
                  </Tooltip>
                ) : null}
                <Typography variant="caption" color="text.secondary">
                  +{relMs}ms
                </Typography>
              </Stack>
            </Stack>
            {tool.inputSchema ? (
              <Accordion disableGutters elevation={0} sx={{ mt: 1, background: "transparent" }}>
                <AccordionSummary expandIcon={<ExpandMoreIcon fontSize="small" />} sx={{ px: 0, minHeight: 0 }}>
                  <Typography variant="caption">Input Schema</Typography>
                </AccordionSummary>
                <AccordionDetails sx={{ px: 0 }}>
                  <Box
                    sx={{
                      background: "#1a2332",
                      borderRadius: 1,
                      p: 1.5,
                      fontFamily: "monospace",
                      fontSize: "0.72rem",
                      color: "#e8e8e8",
                      overflowX: "auto",
                    }}
                  >
                    <JsonTree data={tool.inputSchema} />
                  </Box>
                </AccordionDetails>
              </Accordion>
            ) : null}
          </CardContent>
        </Card>
      );
    })
    .filter((node): node is JSX.Element => node !== null);
}

interface AgentBucket {
  tools?: TraceEvent;
  card?: TraceEvent;
}

function renderA2aAgentCards(events: TraceEvent[], rel: (e: TraceEvent) => number) {
  const toolDiscoveryEvents = events.filter(
    (e) => e.event_type === "tool_discovery" && Boolean(e.remote_agent),
  );
  const agentCardEvents = events.filter((e) => e.event_type === "a2a_remote_discovery");

  const buckets = new Map<string, AgentBucket>();

  for (const e of toolDiscoveryEvents) {
    const key = typeof e.remote_agent === "string" ? e.remote_agent : undefined;
    if (!key) continue;
    const existing = buckets.get(key) ?? {};
    existing.tools = e;
    buckets.set(key, existing);
  }

  for (const e of agentCardEvents) {
    const card = (e.a2a_agent_card ?? null) as Record<string, unknown> | null;
    const cardAgentId =
      card && typeof card.agent_id === "string" ? (card.agent_id as string) : undefined;
    const fallbackKey = typeof e.remote_agent === "string" ? e.remote_agent : undefined;
    const key = cardAgentId ?? fallbackKey;
    if (!key) continue;
    const existing = buckets.get(key) ?? {};
    existing.card = e;
    buckets.set(key, existing);
  }

  const cards: JSX.Element[] = [];
  for (const [agentId, bucket] of buckets) {
    const referenceEvent = bucket.tools ?? bucket.card;
    const relMs = referenceEvent ? rel(referenceEvent) : 0;

    const cardPayload = (bucket.card?.a2a_agent_card ?? null) as Record<string, unknown> | null;
    const skills =
      cardPayload && Array.isArray(cardPayload.skills)
        ? (cardPayload.skills as unknown[]).filter((s): s is string => typeof s === "string")
        : [];

    const toolList = bucket.tools && Array.isArray(bucket.tools.tools)
      ? (bucket.tools.tools as unknown[])
          .map((t) => {
            if (typeof t === "string") return t;
            if (t && typeof t === "object") {
              const name = (t as Record<string, unknown>).name;
              return typeof name === "string" ? name : null;
            }
            return null;
          })
          .filter((n): n is string => Boolean(n))
      : [];

    cards.push(
      <Card key={agentId} variant="outlined" sx={{ borderRadius: 2, mb: 1 }}>
        <CardContent sx={{ py: 1.5 }}>
          <Stack direction="row" justifyContent="space-between" alignItems="flex-start" spacing={1}>
            <Typography variant="body2" fontWeight={600}>
              {agentId}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              +{relMs}ms
            </Typography>
          </Stack>
          {skills.length > 0 ? (
            <Stack direction="row" spacing={0.5} flexWrap="wrap" sx={{ mt: 0.5 }}>
              {skills.map((skill) => (
                <Chip key={skill} label={skill} size="small" variant="outlined" />
              ))}
            </Stack>
          ) : null}
          {toolList.length > 0 ? (
            <Typography variant="caption" color="text.secondary" sx={{ display: "block", mt: 0.5 }}>
              Tools: {toolList.join(", ")}
            </Typography>
          ) : null}
        </CardContent>
      </Card>,
    );
  }

  return cards;
}

export function DiscoveryPhasePanel({
  mcpEvents,
  a2aEvents,
  scenario,
  defaultExpanded,
}: DiscoveryPhasePanelProps) {
  const baseMs = useMemo(() => {
    const all = [...mcpEvents, ...a2aEvents];
    if (all.length === 0) return 0;
    return Math.min(...all.map((e) => e.timestamp_ms));
  }, [mcpEvents, a2aEvents]);

  const rel = (e: TraceEvent) => e.timestamp_ms - baseMs;

  return (
    <Accordion defaultExpanded={defaultExpanded ?? true} data-scenario={scenario}>
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Stack direction="row" spacing={1} alignItems="center" flexWrap="wrap">
          <Typography variant="h6">Discovery Phase</Typography>
          <Chip
            label={`${mcpEvents.length} tools discovered`}
            size="small"
            variant="outlined"
            sx={{ color: protocolColor.mcp, borderColor: protocolColor.mcp }}
          />
          <Chip
            label={`${a2aEvents.length} agents found`}
            size="small"
            variant="outlined"
            sx={{ color: protocolColor.a2a, borderColor: protocolColor.a2a }}
          />
        </Stack>
      </AccordionSummary>
      <AccordionDetails>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, md: 6 }}>
            {/* MCP column */}
            <Box sx={{ borderLeft: `4px solid ${protocolColor.mcp}`, pl: 2, mb: 2 }}>
              <Typography
                component="h3"
                variant="overline"
                sx={{ color: protocolColor.mcp, letterSpacing: "0.14em", display: "block" }}
              >
                MCP — Tool Catalog
              </Typography>
            </Box>
            {mcpEvents.length === 0 ? (
              <Box sx={{ py: 3, textAlign: "center" }}>
                <Typography variant="body2" color="text.disabled">
                  Run on MCP to populate
                </Typography>
              </Box>
            ) : (
              <Stack spacing={1}>
                {mcpEvents.flatMap((event) => renderMcpToolCards(event, rel(event)))}
              </Stack>
            )}
          </Grid>
          <Grid size={{ xs: 12, md: 6 }}>
            {/* A2A column */}
            <Box sx={{ borderLeft: `4px solid ${protocolColor.a2a}`, pl: 2, mb: 2 }}>
              <Typography
                component="h3"
                variant="overline"
                sx={{ color: protocolColor.a2a, letterSpacing: "0.14em", display: "block" }}
              >
                A2A — Agent Cards
              </Typography>
            </Box>
            {a2aEvents.length === 0 ? (
              <Box sx={{ py: 3, textAlign: "center" }}>
                <Typography variant="body2" color="text.disabled">
                  Run on A2A to populate
                </Typography>
              </Box>
            ) : (
              <Stack spacing={1}>{renderA2aAgentCards(a2aEvents, rel)}</Stack>
            )}
          </Grid>
        </Grid>
      </AccordionDetails>
    </Accordion>
  );
}
