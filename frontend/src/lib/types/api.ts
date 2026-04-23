import type {
  ApiRunRequest as GeneratedApiRunRequest,
  HealthResponse as GeneratedHealthResponse,
  ReportDetailResponse as GeneratedReportDetailResponse,
  ReportsResponse as GeneratedReportsResponse,
  RunResponse as GeneratedRunResponse,
  ScenariosResponse as GeneratedScenariosResponse,
  TrendsResponse as GeneratedTrendsResponse,
  RemoteA2ARegistryResponse as GeneratedRemoteA2ARegistryResponse,
  RemoteA2AHealthResponse as GeneratedRemoteA2AHealthResponse,
} from "./api.generated";

export type OpenApiRunRequest = GeneratedApiRunRequest;
export type OpenApiRunResponse = GeneratedRunResponse;
export type OpenApiReportsResponse = GeneratedReportsResponse;
export type OpenApiReportDetailResponse = GeneratedReportDetailResponse;
export type OpenApiTrendsResponse = GeneratedTrendsResponse;
export type OpenApiScenariosResponse = GeneratedScenariosResponse;
export type OpenApiRemoteA2AHealthResponse = GeneratedRemoteA2AHealthResponse;

export type DemoMode = "baseline" | "mcp" | "a2a" | "hybrid" | "all";
export type RuntimeMode = "mock" | "llm";
export type TransportMode = "in_process" | "stdio" | "http" | "remote_http";
export type A2ATransportMode = "local" | "remote";

export interface ScenarioOption {
  key: string;
  label: string;
  query: string;
  difficulty: string;
  tags: string[];
}

export interface TraceEvent {
  index: number;
  event_type: string;
  timestamp_ms: number;
  message_type?: string;
  agent?: string;
  sender?: string;
  target?: string;
  tool?: string;
  server?: string;
  status?: string;
  protocol?: string;
  transport?: string;
  requested_transport?: string;
  error?: string;
  // Phase 2 enrichment fields
  step_index?: number;
  phase?: "discovery" | "execution";
  parallel_batch_id?: string;
  started_at?: number;
  completed_at?: number;
  [key: string]: unknown;
}

export interface ComparisonMetrics {
  mode: string;
  latency_ms: number;
  tool_calls: number;
  a2a_messages: number;
  agents_involved: string[];
  complexity: string;
  strengths: string[];
  weaknesses: string[];
  retries: number;
  failures: number;
}

export interface TalkingPointCard {
  headline: string;
  sentence: string;
  callout: string;
}

export interface RunResult {
  mode: string;
  runtime: string;
  ticket: {
    ticket_id: string;
    customer_id: string;
    query: string;
    scenario: string;
    title?: string;
    difficulty?: string;
    tags?: string[];
    // Phase 3: per-scenario talking point for presenter card
    talking_point?: TalkingPointCard | null;
  };
  final_answer: string;
  metrics: ComparisonMetrics;
  tools_used: string[];
  agents_used: string[];
  failures: string[];
  trace: TraceEvent[];
  external_log_path?: string | null;
  a2a_transport?: string;
  mcp_transport?: string;
}

export interface ModeScorecard {
  mode: string;
  overall_score: number;
  responsiveness_score: number;
  tooling_score: number;
  collaboration_score: number;
  resilience_score: number;
  presentation_score: number;
  headline: string;
}

export interface ReportScorecard {
  fastest_mode: string;
  most_tool_heavy_mode: string;
  most_collaborative_mode: string;
  most_resilient_mode: string;
  recommended_demo_mode: string;
  mode_scorecards: ModeScorecard[];
  notes: string[];
}

export interface ReportSummary {
  report_name: string;
  scenario: string;
  title: string;
  runtime: string;
  generated_at: string;
  mode_count: number;
  total_tool_calls: number;
  total_a2a_messages: number;
  total_failures: number;
  talking_points: string[];
  scorecard: ReportScorecard;
}

export interface RunResponse {
  results: RunResult[];
  report_name: string | null;
  summary: ReportSummary;
}

export interface ReportsResponse {
  reports: ReportSummary[];
}

export interface ReportDetailResponse {
  report_name: string;
  summary: ReportSummary;
  results: RunResult[];
  export_url: string;
  pdf_export_url: string;
  evidence_export_url: string;
  sorting: {
    score_sort: string;
    score_dir: string;
    result_sort: string;
    result_dir: string;
  };
}

export interface TrendRow {
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

export interface ReportTrendSummary {
  total_reports: number;
  scenario_counts: Array<{ scenario: string; count: number }>;
  runtime_counts: Record<string, number>;
  recommended_mode_counts: Array<{ mode: string; count: number }>;
  average_totals: {
    tool_calls: number;
    a2a_messages: number;
    failures: number;
  };
  mode_trends: TrendRow[];
  a2a_transport_counts: Record<string, number>;
  recent_reports: ReportSummary[];
  narrative: string[];
  available_filters: {
    scenarios: string[];
    runtimes: string[];
    recommended_modes: string[];
  };
  applied_filters: {
    scenario: string;
    runtime: string;
    recommended_mode: string;
  };
  applied_sorting: {
    mode_sort: string;
    mode_dir: string;
    scenario_sort: string;
    scenario_dir: string;
    report_sort: string;
    report_dir: string;
  };
}

export interface TrendsResponse {
  trends: ReportTrendSummary;
}

export interface ApiRunRequest {
  profile: string;
  scenario: string;
  mode: DemoMode;
  runtime?: RuntimeMode | null;
  query: string;
  customer_id: string;
  save_report?: boolean | null;
  db_down: boolean;
  docs_timeout: boolean;
  malformed_task: boolean;
  remote_a2a_timeout?: boolean;
  remote_a2a_bad_auth?: boolean;
  remote_a2a_missing_capability?: boolean;
  remote_a2a_malformed_response?: boolean;
  remote_a2a_task_failure?: boolean;
  disable_agent: string[];
  mcp_transport?: TransportMode | null;
  a2a_transport?: A2ATransportMode | null;
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

export interface RemoteMCPServer {
  id: string;
  label: string;
  db_url: string;
  docs_url: string;
  enabled?: boolean | number;
  updated_at?: string | null;
}

export interface RemoteMCPRegistryResponse {
  servers: RemoteMCPServer[];
}

export interface RemoteA2AAgent {
  role: string;
  url: string;
  enabled?: boolean | number;
}

export interface RemoteA2AHealthAgent extends RemoteA2AAgent {
  status: string;
  detail?: Record<string, unknown> | null;
  error?: string | null;
}

export type RemoteA2ARegistryResponse = GeneratedRemoteA2ARegistryResponse & {
  agents: RemoteA2AAgent[];
};

export type RemoteA2AHealthResponse = GeneratedRemoteA2AHealthResponse & {
  agents: RemoteA2AHealthAgent[];
};

export interface TelemetrySnapshot {
  total_runs: number;
  total_reports: number;
  total_failures: number;
  avg_latency_ms: number;
  tool_calls: number;
  a2a_messages: number;
  users: string[];
  mode_counts: Record<string, number>;
  a2a_transport_counts: Record<string, number>;
}
export type HealthResponse = GeneratedHealthResponse;
