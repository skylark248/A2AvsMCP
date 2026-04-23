// Generated from FastAPI OpenAPI by scripts/generate_api_types.py.
// Do not edit by hand; update backend schemas and rerun the generator.

export interface ApiRunRequest {
  profile?: "dev" | "demo" | "llm";
  scenario?: string;
  mode?: "baseline" | "mcp" | "a2a" | "hybrid" | "all";
  runtime?: "mock" | "llm" | null;
  query?: string;
  customer_id?: string;
  save_report?: boolean | null;
  db_down?: boolean;
  docs_timeout?: boolean;
  malformed_task?: boolean;
  remote_a2a_timeout?: boolean;
  remote_a2a_bad_auth?: boolean;
  remote_a2a_missing_capability?: boolean;
  remote_a2a_malformed_response?: boolean;
  remote_a2a_task_failure?: boolean;
  disable_agent?: Array<"customer_data_agent" | "documentation_agent" | "policy_or_billing_agent">;
  mcp_transport?: "in_process" | "stdio" | "http" | "remote_http" | null;
  a2a_transport?: "local" | "remote" | null;
  export_logs?: boolean | null;
  remote_mcp_db_url?: string | null;
  remote_mcp_docs_url?: string | null;
  remote_mcp_registry_id?: string | null;
  remote_a2a_customer_url?: string | null;
  remote_a2a_documentation_url?: string | null;
  remote_a2a_policy_url?: string | null;
  remote_a2a_auth_token?: string | null;
  user_id?: string | null;
}

export interface AppliedTrendFiltersResponse {
  scenario: string;
  runtime: string;
  recommended_mode: string;
}

export interface AppliedTrendSortingResponse {
  mode_sort: string;
  mode_dir: string;
  scenario_sort: string;
  scenario_dir: string;
  report_sort: string;
  report_dir: string;
}

export interface AverageTotalsResponse {
  tool_calls: number;
  a2a_messages: number;
  failures: number;
}

export interface Body_run_demo_legacy_run_post {
  profile?: string;
  scenario?: string;
  mode?: string;
  runtime?: string;
  mcp_transport?: string;
  query?: string;
  customer_id?: string;
  save_report?: string | null;
  export_logs?: string | null;
  db_down?: string | null;
  docs_timeout?: string | null;
  malformed_task?: string | null;
  disable_agent?: Array<string> | null;
}

export interface ComparisonMetricsResponse {
  mode: string;
  latency_ms: number;
  tool_calls: number;
  a2a_messages: number;
  agents_involved: Array<string>;
  complexity: string;
  strengths: Array<string>;
  weaknesses: Array<string>;
  retries: number;
  failures: number;
}

export interface CountByModeResponse {
  mode: string;
  count: number;
}

export interface CountByScenarioResponse {
  scenario: string;
  count: number;
}

export interface HealthResponse {
  status: "ok";
  version: string;
  default_profile: string;
  profiles: Array<string>;
  frontend_build_present: boolean;
  frontend_index: string;
  artifacts_dir: string;
  reports_dir: string;
  scenarios: number;
  mcp_transport_default: string;
  a2a_transport_default: string;
  artifact_isolation_enabled?: boolean;
  telemetry_db?: string | null;
}

export interface ModeScorecardResponse {
  mode: string;
  overall_score: number;
  responsiveness_score: number;
  tooling_score: number;
  collaboration_score: number;
  resilience_score: number;
  presentation_score: number;
  headline: string;
}

export interface ModeTrendResponse {
  mode: string;
  appearances: number;
  recommended_count: number;
  avg_overall_score: number;
  avg_presentation_score: number;
  avg_resilience_score: number;
  avg_latency_ms: number;
  avg_tool_calls: number;
  avg_a2a_messages: number;
}

export interface RemoteA2AAgentResponse {
  role: string;
  url: string;
  enabled?: boolean | number;
}

export interface RemoteA2AHealthAgentResponse {
  role: string;
  url: string;
  enabled?: boolean | number;
  status: string;
  detail?: Record<string, unknown> | null;
  error?: string | null;
}

export interface RemoteA2AHealthResponse {
  agents: Array<RemoteA2AHealthAgentResponse>;
}

export interface RemoteA2ARegistryResponse {
  agents: Array<RemoteA2AAgentResponse>;
}

export interface RemoteMCPRegistryResponse {
  servers: Array<RemoteMCPServerResponse>;
}

export interface RemoteMCPServerResponse {
  id: string;
  label: string;
  db_url: string;
  docs_url: string;
  enabled?: boolean | number;
  updated_at?: string | null;
}

export interface ReportDetailResponse {
  report_name: string;
  summary: ReportSummaryResponse;
  results: Array<RunResultResponse>;
  export_url: string;
  pdf_export_url: string;
  evidence_export_url: string;
  sorting: ReportDetailSortingResponse;
}

export interface ReportDetailSortingResponse {
  score_sort: string;
  score_dir: string;
  result_sort: string;
  result_dir: string;
}

export interface ReportScorecardResponse {
  fastest_mode: string;
  most_tool_heavy_mode: string;
  most_collaborative_mode: string;
  most_resilient_mode: string;
  recommended_demo_mode: string;
  mode_scorecards?: Array<ModeScorecardResponse>;
  notes?: Array<string>;
}

export interface ReportSummaryResponse {
  report_name: string;
  scenario: string;
  title: string;
  runtime: string;
  generated_at: string;
  mode_count: number;
  total_tool_calls: number;
  total_a2a_messages: number;
  total_failures: number;
  talking_points?: Array<string>;
  scorecard: ReportScorecardResponse;
}

export interface ReportTrendSummaryResponse {
  total_reports: number;
  scenario_counts: Array<CountByScenarioResponse>;
  runtime_counts: Record<string, number>;
  recommended_mode_counts: Array<CountByModeResponse>;
  average_totals: AverageTotalsResponse;
  mode_trends: Array<ModeTrendResponse>;
  a2a_transport_counts?: Record<string, number>;
  recent_reports: Array<ReportSummaryResponse>;
  narrative: Array<string>;
  available_filters: TrendFiltersResponse;
  applied_filters: AppliedTrendFiltersResponse;
  applied_sorting: AppliedTrendSortingResponse;
}

export interface ReportsResponse {
  reports: Array<ReportSummaryResponse>;
}

export interface RunResponse {
  results: Array<RunResultResponse>;
  report_name: string | null;
  summary: ReportSummaryResponse;
}

export interface RunResultResponse {
  mode: string;
  runtime: string;
  ticket: TicketResponse;
  final_answer: string;
  metrics: ComparisonMetricsResponse;
  tools_used: Array<string>;
  agents_used: Array<string>;
  failures?: Array<string>;
  trace: Array<TraceEventResponse>;
  external_log_path?: string | null;
  a2a_transport?: string;
}

export interface ScenarioOptionResponse {
  key: string;
  label: string;
  query: string;
  difficulty: string;
  tags?: Array<string>;
}

export interface ScenariosResponse {
  scenarios: Array<ScenarioOptionResponse>;
}

export interface TelemetrySnapshotResponse {
  total_runs: number;
  total_reports: number;
  total_failures: number;
  avg_latency_ms: number;
  tool_calls: number;
  a2a_messages: number;
  users?: Array<string>;
  mode_counts?: Record<string, number>;
  a2a_transport_counts?: Record<string, number>;
}

export interface TalkingPointCard {
  headline: string;
  sentence: string;
  callout: string;
}

export interface TicketResponse {
  ticket_id: string;
  customer_id: string;
  query: string;
  scenario: string;
  title?: string | null;
  difficulty?: string | null;
  tags?: Array<string>;
  // Phase 3: per-scenario talking point for presenter card (manually patched — re-running generator will include this after api_schemas.py TalkingPointResponse is registered)
  talking_point?: TalkingPointCard | null;
}

export interface TraceEventResponse {
  index: number;
  event_type: string;
  timestamp_ms: number;
  message_type?: string | null;
  agent?: string | null;
  sender?: string | null;
  target?: string | null;
  tool?: string | null;
  server?: string | null;
  status?: string | null;
  protocol?: string | null;
  transport?: string | null;
  requested_transport?: string | null;
  error?: string | null;
  // Phase 2 enrichment fields (manually patched — re-running generator will also include these after api_schemas.py is updated)
  step_index?: number | null;
  phase?: "discovery" | "execution" | null;
  parallel_batch_id?: string | null;
  started_at?: number | null;
  completed_at?: number | null;
  [key: string]: unknown;
}

export interface TrendFiltersResponse {
  scenarios: Array<string>;
  runtimes: Array<string>;
  recommended_modes: Array<string>;
}

export interface TrendsResponse {
  trends: ReportTrendSummaryResponse;
}
