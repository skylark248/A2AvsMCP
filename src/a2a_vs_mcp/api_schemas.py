from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


DemoMode = Literal["baseline", "mcp", "a2a", "hybrid", "all"]
RuntimeMode = Literal["mock", "llm", "fake_llm"]
TransportMode = Literal["in_process", "stdio", "http", "remote_http"]
A2ATransportMode = Literal["local", "remote"]
ProfileName = Literal["dev", "demo", "llm"]
AgentId = Literal["customer_data_agent", "documentation_agent", "policy_or_billing_agent"]


class ScenarioOptionResponse(BaseModel):
    key: str
    label: str
    query: str
    difficulty: str
    tags: list[str] = Field(default_factory=list)


class ScenariosResponse(BaseModel):
    scenarios: list[ScenarioOptionResponse]


class TicketResponse(BaseModel):
    ticket_id: str
    customer_id: str
    query: str
    scenario: str
    title: str | None = ""
    difficulty: str | None = "standard"
    tags: list[str] = Field(default_factory=list)


class TraceEventResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    index: int
    event_type: str
    timestamp_ms: float
    message_type: str | None = None
    agent: str | None = None
    sender: str | None = None
    target: str | None = None
    tool: str | None = None
    server: str | None = None
    status: str | None = None
    protocol: str | None = None
    transport: str | None = None
    requested_transport: str | None = None
    error: str | None = None


class ComparisonMetricsResponse(BaseModel):
    mode: str
    latency_ms: float
    tool_calls: int
    a2a_messages: int
    agents_involved: list[str]
    complexity: str
    strengths: list[str]
    weaknesses: list[str]
    retries: int
    failures: int


class RunResultResponse(BaseModel):
    mode: str
    runtime: str
    ticket: TicketResponse
    final_answer: str
    metrics: ComparisonMetricsResponse
    tools_used: list[str]
    agents_used: list[str]
    failures: list[str] = Field(default_factory=list)
    trace: list[TraceEventResponse]
    external_log_path: str | None = None
    a2a_transport: str = "local"
    mcp_transport: str | None = None


class ModeScorecardResponse(BaseModel):
    mode: str
    overall_score: int
    responsiveness_score: int
    tooling_score: int
    collaboration_score: int
    resilience_score: int
    presentation_score: int
    headline: str


class ReportScorecardResponse(BaseModel):
    fastest_mode: str
    most_tool_heavy_mode: str
    most_collaborative_mode: str
    most_resilient_mode: str
    recommended_demo_mode: str
    mode_scorecards: list[ModeScorecardResponse] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class ReportSummaryResponse(BaseModel):
    report_name: str
    scenario: str
    title: str
    runtime: str
    generated_at: str
    mode_count: int
    total_tool_calls: int
    total_a2a_messages: int
    total_failures: int
    talking_points: list[str] = Field(default_factory=list)
    scorecard: ReportScorecardResponse


class RunResponse(BaseModel):
    results: list[RunResultResponse]
    report_name: str | None
    summary: ReportSummaryResponse


class ReportsResponse(BaseModel):
    reports: list[ReportSummaryResponse]


class CountByScenarioResponse(BaseModel):
    scenario: str
    count: int


class CountByModeResponse(BaseModel):
    mode: str
    count: int


class AverageTotalsResponse(BaseModel):
    tool_calls: float
    a2a_messages: float
    failures: float


class ModeTrendResponse(BaseModel):
    mode: str
    appearances: int
    recommended_count: int
    avg_overall_score: float
    avg_presentation_score: float
    avg_resilience_score: float
    avg_latency_ms: float
    avg_tool_calls: float
    avg_a2a_messages: float


class TrendFiltersResponse(BaseModel):
    scenarios: list[str]
    runtimes: list[str]
    recommended_modes: list[str]


class AppliedTrendFiltersResponse(BaseModel):
    scenario: str
    runtime: str
    recommended_mode: str


class AppliedTrendSortingResponse(BaseModel):
    mode_sort: str
    mode_dir: str
    scenario_sort: str
    scenario_dir: str
    report_sort: str
    report_dir: str


class ReportTrendSummaryResponse(BaseModel):
    total_reports: int
    scenario_counts: list[CountByScenarioResponse]
    runtime_counts: dict[str, int]
    recommended_mode_counts: list[CountByModeResponse]
    average_totals: AverageTotalsResponse
    mode_trends: list[ModeTrendResponse]
    a2a_transport_counts: dict[str, int] = Field(default_factory=dict)
    recent_reports: list[ReportSummaryResponse]
    narrative: list[str]
    available_filters: TrendFiltersResponse
    applied_filters: AppliedTrendFiltersResponse
    applied_sorting: AppliedTrendSortingResponse


class TrendsResponse(BaseModel):
    trends: ReportTrendSummaryResponse


class ReportDetailSortingResponse(BaseModel):
    score_sort: str
    score_dir: str
    result_sort: str
    result_dir: str


class ReportDetailResponse(BaseModel):
    report_name: str
    summary: ReportSummaryResponse
    results: list[RunResultResponse]
    export_url: str
    pdf_export_url: str
    evidence_export_url: str
    sorting: ReportDetailSortingResponse



class RemoteMCPServerResponse(BaseModel):
    id: str
    label: str
    db_url: str
    docs_url: str
    enabled: bool | int = True
    updated_at: str | None = None


class RemoteMCPRegistryResponse(BaseModel):
    servers: list[RemoteMCPServerResponse]


class RemoteA2AAgentResponse(BaseModel):
    role: str
    url: str
    enabled: bool | int = True


class RemoteA2ARegistryResponse(BaseModel):
    agents: list[RemoteA2AAgentResponse]



class RemoteA2AHealthAgentResponse(RemoteA2AAgentResponse):
    status: str
    detail: dict[str, Any] | None = None
    error: str | None = None


class RemoteA2AHealthResponse(BaseModel):
    agents: list[RemoteA2AHealthAgentResponse]

class TelemetrySnapshotResponse(BaseModel):
    total_runs: int
    total_reports: int
    total_failures: int
    avg_latency_ms: float
    tool_calls: int
    a2a_messages: int
    users: list[str] = Field(default_factory=list)
    mode_counts: dict[str, int] = Field(default_factory=dict)
    a2a_transport_counts: dict[str, int] = Field(default_factory=dict)
class ApiRunRequest(BaseModel):
    profile: ProfileName = "dev"
    scenario: str = "order_status"
    mode: DemoMode = "all"
    runtime: RuntimeMode | None = None
    query: str = ""
    customer_id: str = ""
    save_report: bool | None = None
    db_down: bool = False
    docs_timeout: bool = False
    malformed_task: bool = False
    remote_a2a_timeout: bool = False
    remote_a2a_bad_auth: bool = False
    remote_a2a_missing_capability: bool = False
    remote_a2a_malformed_response: bool = False
    remote_a2a_task_failure: bool = False
    disable_agent: list[AgentId] = Field(default_factory=list)
    mcp_transport: TransportMode | None = None
    a2a_transport: A2ATransportMode | None = None
    export_logs: bool | None = None
    remote_mcp_db_url: str | None = None
    remote_mcp_docs_url: str | None = None
    remote_mcp_registry_id: str | None = None
    remote_a2a_customer_url: str | None = None
    remote_a2a_documentation_url: str | None = None
    remote_a2a_policy_url: str | None = None
    remote_a2a_auth_token: str | None = None
    user_id: str | None = None


class HealthResponse(BaseModel):
    status: Literal["ok"]
    version: str
    default_profile: str
    profiles: list[str]
    frontend_build_present: bool
    frontend_index: str
    artifacts_dir: str
    reports_dir: str
    scenarios: int
    mcp_transport_default: str
    a2a_transport_default: str
    artifact_isolation_enabled: bool = True
    telemetry_db: str | None = None







