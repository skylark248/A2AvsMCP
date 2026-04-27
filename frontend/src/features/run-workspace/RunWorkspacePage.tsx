import PlayArrowRoundedIcon from "@mui/icons-material/PlayArrowRounded";
import ShareOutlinedIcon from "@mui/icons-material/ShareOutlined";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControl,
  FormControlLabel,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";

import { GlossaryTerm } from "../../components/glossary/GlossaryTerm";
import { useAppUi } from "../../app/ui/AppUiProvider";
import { ContentCardSkeleton, FilterCardSkeleton, PageIntroSkeleton } from "../../components/loading/LoadingSkeletons";
import {
  fetchRemoteA2aHealth,
  fetchRemoteA2aRegistry,
  fetchRemoteMcpRegistry,
  fetchScenarios,
  runDemo,
} from "../../lib/api/client";
import { demoPresets, guidedStoryModes, type DemoPreset } from "../../lib/demo/presets";
import { ParallelAgentTimeline } from "../../components/timeline/ParallelAgentTimeline";
import { getProtocolColor } from "../../lib/trace/eventColors";
import type {
  A2ATransportMode,
  ApiRunRequest,
  DemoMode,
  RemoteA2AAgent,
  RemoteA2AHealthAgent,
  RemoteMCPServer,
  RunResponse,
  RuntimeMode,
  ScenarioOption,
  TransportMode,
} from "../../lib/types/api";

const ROLE_FIRST_LABELS: Record<string, string> = {
  mcp: "Tool Access Protocol (MCP)",
  a2a: "Agent Coordination Protocol (A2A)",
  baseline: "Direct Agent (Baseline)",
  hybrid: "Combined Protocol (Hybrid)",
};

function roleFirstLabel(mode: string): string {
  return ROLE_FIRST_LABELS[mode] ?? mode.toUpperCase();
}

const modeOptions: DemoMode[] = ["all", "baseline", "mcp", "a2a", "hybrid"];
const runtimeOptions: RuntimeMode[] = ["mock", "llm"];
const transportOptions: TransportMode[] = ["in_process", "stdio", "http", "remote_http"];
const a2aTransportOptions: A2ATransportMode[] = ["local", "remote"];

const initialForm: ApiRunRequest = {
  profile: "dev",
  scenario: "order_status",
  mode: "all",
  runtime: null,
  query: "",
  customer_id: "",
  save_report: true,
  db_down: false,
  docs_timeout: false,
  malformed_task: false,
  remote_a2a_timeout: false,
  remote_a2a_bad_auth: false,
  remote_a2a_missing_capability: false,
  remote_a2a_malformed_response: false,
  remote_a2a_task_failure: false,
  disable_agent: [],
  mcp_transport: null,
  a2a_transport: null,
  export_logs: null,
  remote_mcp_db_url: "",
  remote_mcp_docs_url: "",
  remote_mcp_registry_id: null,
  remote_a2a_customer_url: "",
  remote_a2a_documentation_url: "",
  remote_a2a_policy_url: "",
  remote_a2a_auth_token: "",
};
function formFromSearchParams(searchParams: URLSearchParams): ApiRunRequest {
  return {
    profile: searchParams.get("profile") ?? initialForm.profile,
    scenario: searchParams.get("scenario") ?? initialForm.scenario,
    mode: (searchParams.get("mode") as DemoMode | null) ?? initialForm.mode,
    runtime: (searchParams.get("runtime") as RuntimeMode | null) ?? null,
    query: searchParams.get("query") ?? "",
    customer_id: searchParams.get("customer_id") ?? "",
    save_report: searchParams.get("save_report") === "false" ? false : true,
    db_down: searchParams.get("db_down") === "true",
    docs_timeout: searchParams.get("docs_timeout") === "true",
    malformed_task: searchParams.get("malformed_task") === "true",
    remote_a2a_timeout: searchParams.get("remote_a2a_timeout") === "true",
    remote_a2a_bad_auth: searchParams.get("remote_a2a_bad_auth") === "true",
    remote_a2a_missing_capability: searchParams.get("remote_a2a_missing_capability") === "true",
    remote_a2a_malformed_response: searchParams.get("remote_a2a_malformed_response") === "true",
    remote_a2a_task_failure: searchParams.get("remote_a2a_task_failure") === "true",
    disable_agent: [],
    mcp_transport: (searchParams.get("mcp_transport") as TransportMode | null) ?? null,
    a2a_transport: (searchParams.get("a2a_transport") as A2ATransportMode | null) ?? null,
    export_logs: searchParams.get("export_logs") === "true" ? true : null,
    remote_mcp_db_url: searchParams.get("remote_mcp_db_url") ?? "",
    remote_mcp_docs_url: searchParams.get("remote_mcp_docs_url") ?? "",
    remote_mcp_registry_id: searchParams.get("remote_mcp_registry_id"),
    remote_a2a_customer_url: searchParams.get("remote_a2a_customer_url") ?? "",
    remote_a2a_documentation_url: searchParams.get("remote_a2a_documentation_url") ?? "",
    remote_a2a_policy_url: searchParams.get("remote_a2a_policy_url") ?? "",
    remote_a2a_auth_token: "",
  };
}

function formToSearchParams(form: ApiRunRequest): URLSearchParams {
  const params = new URLSearchParams();
  if (form.profile !== initialForm.profile) params.set("profile", form.profile);
  if (form.scenario !== initialForm.scenario) params.set("scenario", form.scenario);
  if (form.mode !== initialForm.mode) params.set("mode", form.mode);
  if (form.runtime) params.set("runtime", form.runtime);
  if (form.query.trim()) params.set("query", form.query);
  if (form.customer_id.trim()) params.set("customer_id", form.customer_id);
  if (!form.save_report) params.set("save_report", "false");
  if (form.db_down) params.set("db_down", "true");
  if (form.docs_timeout) params.set("docs_timeout", "true");
  if (form.malformed_task) params.set("malformed_task", "true");
  if (form.remote_a2a_timeout) params.set("remote_a2a_timeout", "true");
  if (form.remote_a2a_bad_auth) params.set("remote_a2a_bad_auth", "true");
  if (form.remote_a2a_missing_capability) params.set("remote_a2a_missing_capability", "true");
  if (form.remote_a2a_malformed_response) params.set("remote_a2a_malformed_response", "true");
  if (form.remote_a2a_task_failure) params.set("remote_a2a_task_failure", "true");
  if (form.mcp_transport) params.set("mcp_transport", form.mcp_transport);
  if (form.a2a_transport) params.set("a2a_transport", form.a2a_transport);
  if (form.export_logs) params.set("export_logs", "true");
  if (form.remote_mcp_db_url?.trim()) params.set("remote_mcp_db_url", form.remote_mcp_db_url);
  if (form.remote_mcp_docs_url?.trim()) params.set("remote_mcp_docs_url", form.remote_mcp_docs_url);
  if (form.remote_mcp_registry_id?.trim()) params.set("remote_mcp_registry_id", form.remote_mcp_registry_id);
  if (form.remote_a2a_customer_url?.trim()) params.set("remote_a2a_customer_url", form.remote_a2a_customer_url);
  if (form.remote_a2a_documentation_url?.trim())
    params.set("remote_a2a_documentation_url", form.remote_a2a_documentation_url);
  if (form.remote_a2a_policy_url?.trim()) params.set("remote_a2a_policy_url", form.remote_a2a_policy_url);
  return params;
}

function formFromPreset(preset: DemoPreset): ApiRunRequest {
  return {
    ...initialForm,
    profile: preset.profile,
    scenario: preset.scenario,
    mode: preset.mode,
    runtime: preset.runtime,
    mcp_transport: preset.mcp_transport,
    a2a_transport: null,
    db_down: preset.failure_toggles.includes("db_down"),
    docs_timeout: preset.failure_toggles.includes("docs_timeout"),
    malformed_task: preset.failure_toggles.includes("malformed_task"),
    remote_a2a_timeout: preset.failure_toggles.includes("remote_a2a_timeout"),
    remote_a2a_bad_auth: preset.failure_toggles.includes("remote_a2a_bad_auth"),
    remote_a2a_missing_capability: preset.failure_toggles.includes("remote_a2a_missing_capability"),
    remote_a2a_malformed_response: preset.failure_toggles.includes("remote_a2a_malformed_response"),
    remote_a2a_task_failure: preset.failure_toggles.includes("remote_a2a_task_failure"),
    save_report: true,
    export_logs: preset.profile === "demo" ? true : null,
    remote_mcp_db_url: "",
    remote_mcp_docs_url: "",
    remote_mcp_registry_id: null,
    remote_a2a_customer_url: "",
    remote_a2a_documentation_url: "",
    remote_a2a_policy_url: "",
    remote_a2a_auth_token: "",
  };
}
export function RunWorkspacePage() {
  const { showToast } = useAppUi();
  const [searchParams, setSearchParams] = useSearchParams();
  const [scenarios, setScenarios] = useState<ScenarioOption[]>([]);
  const [remoteRegistry, setRemoteRegistry] = useState<RemoteMCPServer[]>([]);
  const [remoteA2aRegistry, setRemoteA2aRegistry] = useState<RemoteA2AAgent[]>([]);
  const [remoteA2aHealth, setRemoteA2aHealth] = useState<RemoteA2AHealthAgent[]>([]);
  const [remoteA2aHealthLoading, setRemoteA2aHealthLoading] = useState(false);
  const [remoteA2aHealthError, setRemoteA2aHealthError] = useState<string | null>(null);
  const [form, setForm] = useState<ApiRunRequest>(() => formFromSearchParams(searchParams));
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<RunResponse | null>(null);

  useEffect(() => {
    setForm(formFromSearchParams(searchParams));
  }, [searchParams]);

  useEffect(() => {
    const next = formToSearchParams(form).toString();
    const current = searchParams.toString();
    if (next !== current) {
      setSearchParams(formToSearchParams(form), { replace: true });
    }
  }, [form, searchParams, setSearchParams]);
  useEffect(() => {
    let active = true;

    async function loadScenarios() {
      try {
        const items = await fetchScenarios();
        if (!active) {
          return;
        }
        setScenarios(items);
        const firstScenario = items[0];
        if (firstScenario && !searchParams.get("scenario")) {
          setForm((current) => ({
            ...current,
            scenario: current.scenario || firstScenario.key,
          }));
        }
      } catch (loadError) {
        if (active) {
          setError(loadError instanceof Error ? loadError.message : "Failed to load scenarios.");
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    void loadScenarios();

    return () => {
      active = false;
    };
  }, [searchParams]);

  useEffect(() => {
    let active = true;

    async function loadRemoteRegistry() {
      try {
        const payload = await fetchRemoteMcpRegistry();
        if (active) {
          setRemoteRegistry(payload.servers.filter((server) => Boolean(server.enabled)));
        }
      } catch {
        if (active) {
          setRemoteRegistry([]);
        }
      }
    }

    void loadRemoteRegistry();

    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    let active = true;

    async function loadRemoteA2aRegistry() {
      try {
        const payload = await fetchRemoteA2aRegistry();
        if (active) {
          setRemoteA2aRegistry(payload.agents.filter((agent) => Boolean(agent.enabled)));
        }
      } catch {
        if (active) {
          setRemoteA2aRegistry([]);
        }
      }
    }

    void loadRemoteA2aRegistry();

    return () => {
      active = false;
    };
  }, []);
  const selectedScenario = scenarios.find((scenario) => scenario.key === form.scenario);
  const selectedPreset = demoPresets.find(
    (preset) =>
      preset.scenario === form.scenario && preset.mode === form.mode && preset.mcp_transport === form.mcp_transport,
  );

  async function refreshRemoteA2aHealth() {
    setRemoteA2aHealthLoading(true);
    setRemoteA2aHealthError(null);
    try {
      const payload = await fetchRemoteA2aHealth({
        customer_url: form.remote_a2a_customer_url ?? "",
        documentation_url: form.remote_a2a_documentation_url ?? "",
        policy_url: form.remote_a2a_policy_url ?? "",
      });
      setRemoteA2aHealth(payload.agents);
    } catch (healthError) {
      setRemoteA2aHealth([]);
      setRemoteA2aHealthError(healthError instanceof Error ? healthError.message : "Remote A2A health check failed.");
    } finally {
      setRemoteA2aHealthLoading(false);
    }
  }
  async function handleShare() {
    const url = window.location.href;
    try {
      await navigator.clipboard.writeText(url);
      showToast({ message: "Shareable run setup copied to clipboard.", severity: "success" });
    } catch {
      showToast({ message: `Copy this link: ${url}`, severity: "info" });
    }
  }
  async function handleRun() {
    setRunning(true);
    setError(null);
    try {
      const payload = await runDemo(form);
      setResult(payload);
    } catch (runError) {
      setError(runError instanceof Error ? runError.message : "The run failed.");
    } finally {
      setRunning(false);
    }
  }
  function applyPreset(presetId: string) {
    const preset = demoPresets.find((item) => item.id === presetId);
    if (!preset) {
      return;
    }
    setResult(null);
    setError(null);
    setForm(formFromPreset(preset));
    showToast({ message: `${preset.title} loaded.`, severity: "success" });
  }

  function applyStoryMode(mode: DemoMode) {
    setResult(null);
    setError(null);
    setForm((current) => ({
      ...current,
      mode,
      query: "",
      customer_id: "",
      save_report: true,
    }));
  }
  return (
    <Stack spacing={3}>
      {loading ? (
        <PageIntroSkeleton />
      ) : (
        <Box>
          <Typography variant="overline" sx={{ color: "secondary.main", letterSpacing: "0.16em" }}>
            Interactive Workspace
          </Typography>
          <Typography variant="h1" sx={{ maxWidth: 900, color: "primary.main", mb: 1 }}>
            Compare baseline, MCP, A2A, and hybrid flows from one React workspace.
          </Typography>
          <Typography variant="body1" sx={{ maxWidth: 760, color: "text.secondary" }}>
            Use local or hosted transports to compare the same support ticket across protocol boundaries, failure modes,
            traces, and presentation-ready reports.
          </Typography>
        </Box>
      )}

      {error ? <Alert severity="error">{error}</Alert> : null}

      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 4 }}>
          {loading ? (
            <FilterCardSkeleton fields={1} />
          ) : (
            <Card>
              <CardContent>
                <Stack spacing={2.5}>
                  <Stack direction="row" justifyContent="space-between" alignItems="center">
                    <Typography variant="h3">Run Controls</Typography>
                    <Button
                      variant="text"
                      size="small"
                      startIcon={<ShareOutlinedIcon fontSize="small" />}
                      onClick={() => void handleShare()}
                    >
                      Share setup
                    </Button>
                  </Stack>

                  <FormControl fullWidth>
                    <InputLabel id="preset-label">Demo Preset</InputLabel>
                    <Select
                      labelId="preset-label"
                      label="Demo Preset"
                      value={selectedPreset?.id ?? ""}
                      onChange={(event) => applyPreset(event.target.value)}
                    >
                      <MenuItem value="">Custom setup</MenuItem>
                      {demoPresets.map((preset) => (
                        <MenuItem key={preset.id} value={preset.id}>
                          {preset.title}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  {selectedPreset ? <Alert severity="info">{selectedPreset.description}</Alert> : null}

                  <Stack spacing={1}>
                    <Typography variant="subtitle2" sx={{ color: "text.secondary" }}>
                      Guided Story
                    </Typography>
                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                      {guidedStoryModes.map((mode) => (
                        <Button
                          key={mode}
                          variant={form.mode === mode ? "contained" : "outlined"}
                          size="small"
                          onClick={() => applyStoryMode(mode)}
                        >
                          {mode.toUpperCase()}
                        </Button>
                      ))}
                    </Stack>
                  </Stack>
                  <FormControl fullWidth>
                    <InputLabel id="scenario-label">Scenario</InputLabel>
                    <Select
                      labelId="scenario-label"
                      label="Scenario"
                      value={form.scenario}
                      onChange={(event) => setForm((current) => ({ ...current, scenario: event.target.value }))}
                    >
                      {scenarios.map((scenario) => (
                        <MenuItem key={scenario.key} value={scenario.key}>
                          {scenario.label}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <TextField
                    label="Custom Query Override"
                    multiline
                    minRows={3}
                    value={form.query}
                    onChange={(event) => setForm((current) => ({ ...current, query: event.target.value }))}
                    helperText="When this is filled, the backend treats the ticket as a custom scenario."
                  />

                  <TextField
                    label="Customer ID"
                    value={form.customer_id}
                    onChange={(event) => setForm((current) => ({ ...current, customer_id: event.target.value }))}
                  />

                  <FormControl fullWidth>
                    <InputLabel id="mode-label">Mode</InputLabel>
                    <Select
                      labelId="mode-label"
                      label="Mode"
                      value={form.mode}
                      onChange={(event) => setForm((current) => ({ ...current, mode: event.target.value as DemoMode }))}
                    >
                      {modeOptions.map((mode) => (
                        <MenuItem key={mode} value={mode}>
                          {mode.toUpperCase()}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl fullWidth>
                    <InputLabel id="runtime-label">Runtime Override</InputLabel>
                    <Select
                      labelId="runtime-label"
                      label="Runtime Override"
                      value={form.runtime ?? ""}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          runtime: event.target.value ? (event.target.value as RuntimeMode) : null,
                        }))
                      }
                    >
                      <MenuItem value="">Profile default</MenuItem>
                      {runtimeOptions.map((runtime) => (
                        <MenuItem key={runtime} value={runtime}>
                          {runtime}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  <FormControl fullWidth>
                    <InputLabel id="transport-label">Transport Override</InputLabel>
                    <Select
                      labelId="transport-label"
                      label="Transport Override"
                      value={form.mcp_transport ?? ""}
                      onChange={(event) =>
                        setForm((current) => ({
                          ...current,
                          mcp_transport: event.target.value ? (event.target.value as TransportMode) : null,
                        }))
                      }
                    >
                      <MenuItem value="">Profile default</MenuItem>
                      {transportOptions.map((transport) => (
                        <MenuItem key={transport} value={transport}>
                          {transport}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  <FormControl fullWidth>
                    <InputLabel id="a2a-transport-label">A2A Transport</InputLabel>
                    <Select
                      labelId="a2a-transport-label"
                      label="A2A Transport"
                      value={form.a2a_transport ?? ""}
                      onChange={(event) =>
                        setForm((current) => {
                          const nextTransport = event.target.value ? (event.target.value as A2ATransportMode) : null;
                          const registryDefaults = Object.fromEntries(
                            remoteA2aRegistry.map((agent) => [agent.role, agent.url]),
                          );
                          return {
                            ...current,
                            a2a_transport: nextTransport,
                            remote_a2a_customer_url:
                              nextTransport === "remote"
                                ? current.remote_a2a_customer_url || registryDefaults.customer_data || ""
                                : current.remote_a2a_customer_url,
                            remote_a2a_documentation_url:
                              nextTransport === "remote"
                                ? current.remote_a2a_documentation_url || registryDefaults.documentation || ""
                                : current.remote_a2a_documentation_url,
                            remote_a2a_policy_url:
                              nextTransport === "remote"
                                ? current.remote_a2a_policy_url || registryDefaults.policy_billing || ""
                                : current.remote_a2a_policy_url,
                          };
                        })
                      }
                    >
                      <MenuItem value="">Profile default</MenuItem>
                      {a2aTransportOptions.map((transport) => (
                        <MenuItem key={transport} value={transport}>
                          {transport === "local" ? "Local broker" : "Remote HTTP"}
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>

                  {form.a2a_transport === "remote" ? (
                    <Stack spacing={1.5}>
                      <Alert severity="info">
                        Remote A2A uses hosted specialist services and records discovery, send, status, artifact, retry,
                        and failure events in the trace. Start the three remote specialist servers before running this
                        path.
                      </Alert>
                      <Stack spacing={1}>
                        <Stack direction="row" spacing={1} alignItems="center" justifyContent="space-between">
                          <Typography variant="subtitle2" sx={{ color: "text.secondary" }}>
                            Remote Health
                          </Typography>
                          <Button
                            size="small"
                            variant="outlined"
                            onClick={() => void refreshRemoteA2aHealth()}
                            disabled={remoteA2aHealthLoading}
                          >
                            {remoteA2aHealthLoading ? "Checking..." : "Check"}
                          </Button>
                        </Stack>
                        {remoteA2aHealthError ? <Alert severity="warning">{remoteA2aHealthError}</Alert> : null}
                        {remoteA2aHealth.length > 0 ? (
                          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                            {remoteA2aHealth.map((agent) => (
                              <Chip
                                key={`${agent.role}-${agent.url}`}
                                label={`${agent.role}: ${agent.status}`}
                                color={agent.status === "ok" ? "success" : "error"}
                                size="small"
                                variant="outlined"
                              />
                            ))}
                          </Stack>
                        ) : (
                          <Typography variant="body2" sx={{ color: "text.secondary" }}>
                            Check the configured endpoints before a remote run.
                          </Typography>
                        )}
                      </Stack>
                      <TextField
                        label="Remote Customer A2A URL"
                        value={form.remote_a2a_customer_url ?? ""}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, remote_a2a_customer_url: event.target.value }))
                        }
                        placeholder="http://127.0.0.1:9101"
                      />
                      <TextField
                        label="Remote Setup A2A URL"
                        value={form.remote_a2a_documentation_url ?? ""}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, remote_a2a_documentation_url: event.target.value }))
                        }
                        placeholder="http://127.0.0.1:9102"
                      />
                      <TextField
                        label="Remote Policy A2A URL"
                        value={form.remote_a2a_policy_url ?? ""}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, remote_a2a_policy_url: event.target.value }))
                        }
                        placeholder="http://127.0.0.1:9103"
                      />
                      <TextField
                        label="Remote A2A Token"
                        type="password"
                        value={form.remote_a2a_auth_token ?? ""}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, remote_a2a_auth_token: event.target.value }))
                        }
                        helperText="Optional demo bearer token. It is sent to the backend but is not added to share links."
                      />
                    </Stack>
                  ) : null}

                  {form.mcp_transport === "remote_http" ? (
                    <Stack spacing={1.5}>
                      <Alert severity="warning">
                        Remote MCP endpoints must expose the same tool names as the local demo DB and docs servers. If
                        an endpoint is unavailable, the backend falls back to local in-process MCP.
                      </Alert>
                      <FormControl fullWidth>
                        <InputLabel id="remote-mcp-registry-label">Remote MCP Registry</InputLabel>
                        <Select
                          labelId="remote-mcp-registry-label"
                          label="Remote MCP Registry"
                          value={form.remote_mcp_registry_id ?? ""}
                          onChange={(event) => {
                            const server = remoteRegistry.find((item) => item.id === event.target.value);
                            setForm((current) => ({
                              ...current,
                              remote_mcp_registry_id: event.target.value || null,
                              remote_mcp_db_url: server?.db_url ?? current.remote_mcp_db_url ?? "",
                              remote_mcp_docs_url: server?.docs_url ?? current.remote_mcp_docs_url ?? "",
                            }));
                          }}
                        >
                          <MenuItem value="">Manual URLs</MenuItem>
                          {remoteRegistry.map((server) => (
                            <MenuItem key={server.id} value={server.id}>
                              {server.label}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                      <TextField
                        label="Remote DB MCP URL"
                        value={form.remote_mcp_db_url ?? ""}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, remote_mcp_db_url: event.target.value }))
                        }
                        placeholder="https://example.com/db/mcp"
                      />
                      <TextField
                        label="Remote Docs MCP URL"
                        value={form.remote_mcp_docs_url ?? ""}
                        onChange={(event) =>
                          setForm((current) => ({ ...current, remote_mcp_docs_url: event.target.value }))
                        }
                        placeholder="https://example.com/docs/mcp"
                      />
                    </Stack>
                  ) : null}
                  <Divider />

                  <Typography variant="subtitle2" sx={{ color: "text.secondary" }}>
                    Failure Simulation
                  </Typography>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={form.db_down}
                        onChange={(_, checked) => setForm((current) => ({ ...current, db_down: checked }))}
                      />
                    }
                    label="Database down"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={form.docs_timeout}
                        onChange={(_, checked) => setForm((current) => ({ ...current, docs_timeout: checked }))}
                      />
                    }
                    label="Docs timeout"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={form.malformed_task}
                        onChange={(_, checked) => setForm((current) => ({ ...current, malformed_task: checked }))}
                      />
                    }
                    label="Malformed task"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={Boolean(form.remote_a2a_timeout)}
                        onChange={(_, checked) =>
                          setForm((current) => ({
                            ...current,
                            remote_a2a_timeout: checked,
                            a2a_transport: checked ? "remote" : current.a2a_transport,
                          }))
                        }
                      />
                    }
                    label="Remote A2A timeout"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={Boolean(form.remote_a2a_bad_auth)}
                        onChange={(_, checked) =>
                          setForm((current) => ({
                            ...current,
                            remote_a2a_bad_auth: checked,
                            a2a_transport: checked ? "remote" : current.a2a_transport,
                          }))
                        }
                      />
                    }
                    label="Remote A2A bad auth"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={Boolean(form.remote_a2a_missing_capability)}
                        onChange={(_, checked) =>
                          setForm((current) => ({
                            ...current,
                            remote_a2a_missing_capability: checked,
                            a2a_transport: checked ? "remote" : current.a2a_transport,
                          }))
                        }
                      />
                    }
                    label="Remote A2A missing capability"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={Boolean(form.remote_a2a_malformed_response)}
                        onChange={(_, checked) =>
                          setForm((current) => ({
                            ...current,
                            remote_a2a_malformed_response: checked,
                            a2a_transport: checked ? "remote" : current.a2a_transport,
                          }))
                        }
                      />
                    }
                    label="Remote A2A malformed response"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={Boolean(form.remote_a2a_task_failure)}
                        onChange={(_, checked) =>
                          setForm((current) => ({
                            ...current,
                            remote_a2a_task_failure: checked,
                            a2a_transport: checked ? "remote" : current.a2a_transport,
                          }))
                        }
                      />
                    }
                    label="Remote A2A task failure"
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={Boolean(form.save_report)}
                        onChange={(_, checked) => setForm((current) => ({ ...current, save_report: checked }))}
                      />
                    }
                    label="Save report"
                  />

                  <Button
                    startIcon={<PlayArrowRoundedIcon />}
                    onClick={() => void handleRun()}
                    disabled={running || loading}
                    size="large"
                  >
                    {running ? "Running..." : "Run Demo"}
                  </Button>
                </Stack>
              </CardContent>
            </Card>
          )}
        </Grid>

        <Grid size={{ xs: 12, lg: 8 }}>
          <Stack spacing={3}>
            {loading ? (
              <ContentCardSkeleton rows={3} height={80} />
            ) : (
              <Card>
                <CardContent>
                  <Stack spacing={1.5}>
                    <Typography variant="h3">Scenario Brief</Typography>
                    <Typography variant="body1">
                      {selectedScenario?.query ?? "Select a scenario to see its support ticket prompt."}
                    </Typography>
                    <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
                      {selectedScenario ? (
                        <>
                          <Chip
                            label={`Difficulty: ${selectedScenario.difficulty}`}
                            color="secondary"
                            variant="outlined"
                          />
                          {selectedScenario.tags.map((tag) => (
                            <Chip key={tag} label={tag} size="small" />
                          ))}
                        </>
                      ) : null}
                    </Stack>
                  </Stack>
                </CardContent>
              </Card>
            )}

            {loading ? (
              <ContentCardSkeleton rows={5} height={220} />
            ) : (
              <Card>
                <CardContent>
                  <Stack spacing={2}>
                    <Typography variant="h3">Results</Typography>
                    {!result && !running ? (
                      <Alert severity="info">
                        Run a scenario to populate the comparison view, scorecard, and report summary.
                      </Alert>
                    ) : null}
                    {result ? (
                      <Stack spacing={2}>
                        <Alert severity="success">
                          {result.summary.scorecard.recommended_demo_mode.toUpperCase()} is currently the recommended
                          presentation mode for this run.
                        </Alert>
                        <Grid container spacing={2}>
                          {result.results.map((item) => (
                            <Grid key={item.mode} size={{ xs: 12, md: 6 }}>
                              <Card variant="outlined" sx={{ height: "100%" }}>
                                <CardContent>
                                  <Stack spacing={1.25}>
                                    <Stack direction="row" justifyContent="space-between" alignItems="center">
                                      <Typography variant="h6">
                                        <GlossaryTerm term={item.mode}>
                                          {roleFirstLabel(item.mode)}
                                        </GlossaryTerm>
                                      </Typography>
                                      <Stack direction="row" spacing={0.5} alignItems="center">
                                        {item.mcp_transport ? (
                                          <Chip label={item.mcp_transport} size="small" variant="outlined" color="default" />
                                        ) : null}
                                        <Chip
                                          label={item.runtime === "llm" ? "OpenAI Runtime" : "Mock Runtime"}
                                          size="small"
                                          color={item.runtime === "llm" ? "warning" : "default"}
                                          variant="outlined"
                                        />
                                      </Stack>
                                    </Stack>
                                    {/* D-01: Outcome metrics chips — below mode header, above final answer */}
                                    <Stack direction="row" spacing={0.5} alignItems="center">
                                      <Chip
                                        label={`${item.metrics.latency_ms}ms`}
                                        size="small"
                                        sx={{ bgcolor: getProtocolColor(item.mode), color: "#fff" }}
                                      />
                                      <Chip
                                        label={`${item.metrics.tool_calls + item.metrics.a2a_messages} round-trips`}
                                        size="small"
                                        variant="outlined"
                                      />
                                      <Chip
                                        label={`${item.metrics.agents_involved.length} agents`}
                                        size="small"
                                        variant="outlined"
                                      />
                                    </Stack>
                                    <Typography variant="body2" sx={{ color: "text.secondary" }}>
                                      {item.final_answer}
                                    </Typography>
                                    <Divider />
                                    {/* D-06: Swimlane timeline — only renders if events have parallel or step data */}
                                    <ParallelAgentTimeline events={item.trace} mode={item.mode} />
                                    {item.ticket?.talking_point ? (
                                      <Paper
                                        elevation={0}
                                        sx={{
                                          borderLeft: `4px solid ${getProtocolColor(item.mode)}`,
                                          bgcolor: "action.hover",
                                          p: 1.5,
                                        }}
                                      >
                                        <Typography variant="subtitle2" fontWeight="bold">
                                          {item.ticket.talking_point.headline}
                                        </Typography>
                                        <Typography variant="body2" sx={{ mt: 0.5 }}>
                                          {item.ticket.talking_point.sentence}
                                        </Typography>
                                        <Typography
                                          variant="body2"
                                          sx={{ mt: 0.5, fontStyle: "italic", color: "text.secondary" }}
                                        >
                                          {item.ticket.talking_point.callout}
                                        </Typography>
                                      </Paper>
                                    ) : null}
                                    {item.failures.length > 0 && (
                                      <Stack spacing={0.5}>
                                        <Typography variant="caption" sx={{ color: "error.main", fontWeight: 600 }}>
                                          Failure Events ({item.failures.length})
                                        </Typography>
                                        <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
                                          {item.failures.map((f, i) => (
                                            <Chip key={i} label={f} size="small" color="error" variant="outlined" />
                                          ))}
                                        </Stack>
                                      </Stack>
                                    )}
                                  </Stack>
                                </CardContent>
                              </Card>
                            </Grid>
                          ))}
                        </Grid>
                        <Card variant="outlined">
                          <CardContent>
                            <Stack spacing={1.25}>
                              <Typography variant="h6">Report Summary</Typography>
                              <Typography variant="body2">Saved report: {result.report_name ?? "unsaved"}</Typography>
                              <Stack spacing={0.75}>
                                {result.summary.talking_points.map((point) => (
                                  <Typography key={point} variant="body2" sx={{ color: "text.secondary" }}>
                                    - {point}
                                  </Typography>
                                ))}
                              </Stack>
                            </Stack>
                          </CardContent>
                        </Card>
                      </Stack>
                    ) : null}
                  </Stack>
                </CardContent>
              </Card>
            )}
          </Stack>
        </Grid>
      </Grid>
    </Stack>
  );
}
