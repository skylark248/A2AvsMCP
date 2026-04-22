from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
import uuid


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


@dataclass
class SupportTicket:
    ticket_id: str
    customer_id: str
    query: str
    scenario: str = "custom"
    title: str = ""
    difficulty: str = "standard"
    tags: list[str] = field(default_factory=list)


@dataclass
class FailureConfig:
    db_down: bool = False
    docs_timeout: bool = False
    unavailable_agents: list[str] = field(default_factory=list)
    malformed_task: bool = False
    remote_a2a_timeout: bool = False
    remote_a2a_bad_auth: bool = False
    remote_a2a_missing_capability: bool = False
    remote_a2a_malformed_response: bool = False
    remote_a2a_task_failure: bool = False

    def enabled(self) -> bool:
        return (
            self.db_down
            or self.docs_timeout
            or self.malformed_task
            or self.remote_a2a_timeout
            or self.remote_a2a_bad_auth
            or self.remote_a2a_missing_capability
            or self.remote_a2a_malformed_response
            or self.remote_a2a_task_failure
            or bool(self.unavailable_agents)
        )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentCard:
    agent_id: str
    name: str
    capabilities: list[str]
    description: str


@dataclass
class A2AMessage:
    message_type: str
    sender_agent: str
    target_agent: str
    capability: str
    payload: dict[str, Any]
    task_id: str
    context: dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: new_id("msg"))
    timestamp: str = field(default_factory=utc_now)
    attempt: int = 1

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentResult:
    agent_id: str
    summary: str
    details: dict[str, Any]
    confidence: float = 0.95
    status: str = "completed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ComparisonMetrics:
    mode: str
    latency_ms: float
    tool_calls: int
    a2a_messages: int
    agents_involved: list[str]
    complexity: str
    strengths: list[str]
    weaknesses: list[str]
    retries: int = 0
    failures: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RunOutput:
    mode: str
    runtime: str
    ticket: SupportTicket
    final_answer: str
    trace: list[dict[str, Any]]
    metrics: ComparisonMetrics
    tools_used: list[str]
    agents_used: list[str]
    failures: list[str] = field(default_factory=list)
    external_log_path: str | None = None
    a2a_transport: str = "local"
    mcp_transport: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["ticket"] = asdict(self.ticket)
        payload["metrics"] = self.metrics.to_dict()
        return payload


@dataclass
class ModeScorecard:
    mode: str
    overall_score: int
    responsiveness_score: int
    tooling_score: int
    collaboration_score: int
    resilience_score: int
    presentation_score: int
    headline: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ReportScorecard:
    fastest_mode: str
    most_tool_heavy_mode: str
    most_collaborative_mode: str
    most_resilient_mode: str
    recommended_demo_mode: str
    mode_scorecards: list[ModeScorecard] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["mode_scorecards"] = [card.to_dict() for card in self.mode_scorecards]
        return payload


@dataclass
class ReportSummary:
    report_name: str
    scenario: str
    title: str
    runtime: str
    generated_at: str
    mode_count: int
    total_tool_calls: int
    total_a2a_messages: int
    total_failures: int
    talking_points: list[str] = field(default_factory=list)
    scorecard: ReportScorecard | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if self.scorecard is not None:
            payload["scorecard"] = self.scorecard.to_dict()
        return payload



