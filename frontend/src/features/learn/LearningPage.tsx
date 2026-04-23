import AccountTreeOutlinedIcon from "@mui/icons-material/AccountTreeOutlined";
import HubOutlinedIcon from "@mui/icons-material/HubOutlined";
import PlayArrowRoundedIcon from "@mui/icons-material/PlayArrowRounded";
import PrecisionManufacturingOutlinedIcon from "@mui/icons-material/PrecisionManufacturingOutlined";
import RouteOutlinedIcon from "@mui/icons-material/RouteOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  Grid,
  Stack,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";
import { useMemo, useState, type ReactNode } from "react";

import { runDemo } from "../../lib/api/client";
import { isA2AEvent, isTraceFailureEvent } from "../../lib/trace/utils";
import type { ApiRunRequest, DemoMode, RunResponse, TransportMode } from "../../lib/types/api";

type GuidedMode = Exclude<DemoMode, "all">;

interface GuidedStep {
  mode: GuidedMode;
  title: string;
  protocol: string;
  transport: TransportMode;
  icon: ReactNode;
  learnerTakeaway: string;
  realLifeExample: string;
  traceSignals: string[];
}

const guidedSteps: GuidedStep[] = [
  {
    mode: "baseline",
    title: "One agent, no protocol boundary",
    protocol: "Neither MCP nor A2A",
    transport: "in_process",
    icon: <RouteOutlinedIcon color="primary" />,
    learnerTakeaway:
      "A single agent owns the whole support task. It is easy to follow, but it does not teach tool contracts or delegation.",
    realLifeExample:
      "A support rep answers from memory without opening the order system, policy docs, or asking a specialist.",
    traceSignals: ["agent_reasoning", "comparison_report"],
  },
  {
    mode: "mcp",
    title: "One agent, structured tools",
    protocol: "MCP",
    transport: "http",
    icon: <PrecisionManufacturingOutlinedIcon color="primary" />,
    learnerTakeaway:
      "MCP gives the agent a standard way to discover and call external capabilities such as database and documentation tools.",
    realLifeExample:
      "A support rep stays responsible for the answer, but opens the order database and policy knowledge base through well-defined tool calls.",
    traceSignals: ["tool_discovery", "tool_call", "tool_transport_fallback"],
  },
  {
    mode: "a2a",
    title: "Specialists collaborate",
    protocol: "A2A-style task lifecycle",
    transport: "in_process",
    icon: <AccountTreeOutlinedIcon color="primary" />,
    learnerTakeaway:
      "Agent-to-agent coordination answers who should do the work, how tasks move, and how failures or retries are visible.",
    realLifeExample:
      "A triage rep asks customer data, documentation, and billing specialists for separate findings, then merges the answer.",
    traceSignals: ["agent_register", "task_request", "task_status", "task_result", "task_retry"],
  },
  {
    mode: "hybrid",
    title: "Specialists use tools",
    protocol: "A2A-style coordination plus MCP",
    transport: "http",
    icon: <HubOutlinedIcon color="primary" />,
    learnerTakeaway:
      "The enterprise pattern combines delegation between agents with MCP-backed access to tools and knowledge systems.",
    realLifeExample:
      "A triage agent routes work to specialists, and each specialist uses standard tool contracts to fetch order, billing, warranty, and policy evidence.",
    traceSignals: ["a2a_message", "tool_discovery", "tool_call", "triage_merge"],
  },
];

const comparisonRows = [
  {
    question: "What problem does it solve?",
    mcp: "Tool and data access for an agent.",
    a2a: "Task delegation and collaboration between agents.",
  },
  {
    question: "What is the unit of interaction?",
    mcp: "A tool call to a server capability.",
    a2a: "A task or message sent to another agent.",
  },
  {
    question: "What should you watch in this demo?",
    mcp: "tool_discovery, tool_call, transport, fallback.",
    a2a: "agent_register, task_request, task_status, task_result, retry.",
  },
  {
    question: "How this repo implements it",
    mcp: "Official MCP SDK servers and clients with in-process, stdio, HTTP, and remote HTTP paths.",
    a2a: "An educational A2A-style broker remains the local baseline, with a Phase 6 hosted remote A2A path for Agent Card discovery, task exchange, status, retries, and artifacts.",
  },
];

export function LearningPage() {
  const [activeMode, setActiveMode] = useState<GuidedMode>("baseline");
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RunResponse | null>(null);

  const activeStep = guidedSteps.find((step) => step.mode === activeMode) ?? guidedSteps[0]!;
  const activeResult = result?.results[0];
  const traceCounts = useMemo(() => {
    const trace = activeResult?.trace ?? [];
    return {
      total: trace.length,
      tools: trace.filter((event) => event.event_type === "tool_call").length,
      a2a: trace.filter(isA2AEvent).length,
      failures: trace.filter(isTraceFailureEvent).length,
    };
  }, [activeResult]);

  async function runFocusedStep(step: GuidedStep) {
    const payload: ApiRunRequest = {
      profile: "dev",
      scenario: "setup_and_warranty",
      mode: step.mode,
      runtime: "mock",
      query: "",
      customer_id: "",
      save_report: false,
      db_down: false,
      docs_timeout: false,
      malformed_task: false,
      disable_agent: [],
      mcp_transport: step.transport,
      export_logs: false,
      remote_mcp_db_url: "",
      remote_mcp_docs_url: "",
      remote_mcp_registry_id: null,
    };

    setRunning(true);
    setError(null);
    try {
      const payloadResult = await runDemo(payload);
      setResult(payloadResult);
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "The guided run failed.");
    } finally {
      setRunning(false);
    }
  }

  return (
    <Stack spacing={3}>
      <Stack spacing={1}>
        <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
          Learn
        </Typography>
        <Typography variant="h2" sx={{ color: "primary.main" }}>
          MCP answers tool access. A2A answers agent collaboration.
        </Typography>
        <Typography variant="body1" sx={{ maxWidth: 860, color: "text.secondary" }}>
          Start with one focused support ticket, then compare how the same work changes as tool calls, specialist
          delegation, retries, and trace events enter the architecture.
        </Typography>
      </Stack>

      <Alert severity="info">
        <strong>MCP</strong> — Uses the official Python MCP SDK with real tool discovery, resources (stable URIs like{" "}
        <code>policy://refund</code>), and prompt templates. All three MCP primitives are visible in traces.
        <br />
        <strong>A2A (local)</strong> — Uses an educational in-process broker that faithfully shapes Agent Cards, message
        envelopes, task lifecycle states, and artifact events to the A2A 1.0 spec — but does not send JSON-RPC over the
        wire locally. Use <strong>A2A Transport: remote</strong> on the Runs page to see real hosted A2A over HTTP.
        <br />
        Open <strong>/compare</strong> after running a scenario to see all four mode timelines side by side.
      </Alert>

      <Grid container spacing={2}>
        {guidedSteps.map((step) => (
          <Grid key={step.mode} size={{ xs: 12, md: 6, xl: 3 }}>
            <Card
              sx={{
                height: "100%",
                borderColor: activeMode === step.mode ? "primary.main" : undefined,
                bgcolor: activeMode === step.mode ? "rgba(23, 71, 95, 0.04)" : "background.paper",
              }}
            >
              <CardContent>
                <Stack spacing={1.5}>
                  <Stack direction="row" alignItems="center" spacing={1}>
                    {step.icon}
                    <Chip label={step.mode.toUpperCase()} size="small" />
                  </Stack>
                  <Typography variant="h6">{step.title}</Typography>
                  <Typography variant="body2" sx={{ color: "text.secondary" }}>
                    {step.learnerTakeaway}
                  </Typography>
                  <Button
                    variant={activeMode === step.mode ? "contained" : "outlined"}
                    onClick={() => setActiveMode(step.mode)}
                  >
                    Study {step.mode.toUpperCase()}
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={2}>
        <Grid size={{ xs: 12, lg: 5 }}>
          <Card sx={{ height: "100%" }}>
            <CardContent>
              <Stack spacing={2}>
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  <Chip label={activeStep.mode.toUpperCase()} color="primary" />
                  <Chip label={activeStep.protocol} />
                  <Chip label={`transport: ${activeStep.transport}`} />
                </Stack>
                <Typography variant="h5" sx={{ color: "primary.main" }}>
                  {activeStep.title}
                </Typography>
                <Typography variant="body1">{activeStep.realLifeExample}</Typography>
                <Divider />
                <Typography variant="subtitle2">Trace events to inspect</Typography>
                <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                  {activeStep.traceSignals.map((signal) => (
                    <Chip key={signal} label={signal} size="small" variant="outlined" />
                  ))}
                </Stack>
                <Button
                  startIcon={<PlayArrowRoundedIcon />}
                  variant="contained"
                  disabled={running}
                  onClick={() => void runFocusedStep(activeStep)}
                >
                  {running ? "Running" : `Run ${activeStep.mode.toUpperCase()} lesson`}
                </Button>
              </Stack>
            </CardContent>
          </Card>
        </Grid>

        <Grid size={{ xs: 12, lg: 7 }}>
          <Card sx={{ height: "100%" }}>
            <CardContent>
              <Stack spacing={2}>
                <Typography variant="h5" sx={{ color: "primary.main" }}>
                  Result Lens
                </Typography>
                {error ? <Alert severity="error">{error}</Alert> : null}
                {!activeResult ? (
                  <Typography variant="body2" sx={{ color: "text.secondary" }}>
                    Run a lesson to inspect the answer, protocol activity, and trace counts for this mode.
                  </Typography>
                ) : null}
                {activeResult ? (
                  <Stack spacing={2}>
                    <Grid container spacing={1.5}>
                      <Grid size={{ xs: 6, md: 3 }}>
                        <Metric label="Trace Events" value={traceCounts.total} />
                      </Grid>
                      <Grid size={{ xs: 6, md: 3 }}>
                        <Metric label="Tool Calls" value={traceCounts.tools} />
                      </Grid>
                      <Grid size={{ xs: 6, md: 3 }}>
                        <Metric label="A2A Messages" value={traceCounts.a2a} />
                      </Grid>
                      <Grid size={{ xs: 6, md: 3 }}>
                        <Metric label="Failures" value={traceCounts.failures} />
                      </Grid>
                    </Grid>
                    <Box>
                      <Typography variant="subtitle2" gutterBottom>
                        Customer answer
                      </Typography>
                      <Typography variant="body2" sx={{ color: "text.secondary" }}>
                        {activeResult.final_answer}
                      </Typography>
                    </Box>
                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                      {activeResult.metrics.strengths.map((strength) => (
                        <Chip key={strength} label={strength} size="small" color="success" variant="outlined" />
                      ))}
                      {activeResult.metrics.weaknesses.map((weakness) => (
                        <Chip key={weakness} label={weakness} size="small" color="warning" variant="outlined" />
                      ))}
                    </Stack>
                  </Stack>
                ) : null}
              </Stack>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      <Card>
        <CardContent>
          <Stack spacing={2}>
            <Typography variant="h5" sx={{ color: "primary.main" }}>
              MCP vs A2A Comparison
            </Typography>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Question</TableCell>
                    <TableCell>MCP</TableCell>
                    <TableCell>A2A</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {comparisonRows.map((row) => (
                    <TableRow key={row.question}>
                      <TableCell sx={{ fontWeight: 700 }}>{row.question}</TableCell>
                      <TableCell>{row.mcp}</TableCell>
                      <TableCell>{row.a2a}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Stack>
        </CardContent>
      </Card>
    </Stack>
  );
}

function Metric(props: { label: string; value: number }) {
  return (
    <Box sx={{ p: 1.5, border: "1px solid rgba(16, 32, 51, 0.1)", borderRadius: 2 }}>
      <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.1em" }}>
        {props.label}
      </Typography>
      <Typography variant="h5" sx={{ color: "primary.main" }}>
        {props.value}
      </Typography>
    </Box>
  );
}
