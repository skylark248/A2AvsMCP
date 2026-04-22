from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from ..dataset import DemoRepository
from ..reasoning import FakeReasoningEngine, LLMReasoner, MockReasoner, TicketIntent
from ..schemas import A2AMessage, AgentCard, AgentResult, FailureConfig, SupportTicket, new_id
from ..trace import TraceRecorder



def build_reasoner(runtime: str) -> MockReasoner:
    if runtime == "llm":
        return LLMReasoner()
    if runtime == "fake_llm":
        return FakeReasoningEngine()
    return MockReasoner()


@dataclass
class AgentContext:
    repo: DemoRepository
    trace: TraceRecorder
    runtime: str
    mcp_transport: str
    project_root: Path
    failure_config: FailureConfig
    remote_mcp_urls: dict[str, str] = field(default_factory=dict)
    mcp_clients: dict[tuple[str, str, str, tuple[tuple[str, str], ...]], Any] = field(default_factory=dict)

    def get_mcp_client(self, server_module: str, **server_args: str) -> Any:
        from ..mcp.client import MCPClient

        remote_url = None
        if self.mcp_transport == "remote_http":
            role = "db" if server_module.endswith("db_server") else "docs"
            remote_url = self.remote_mcp_urls.get(role)
        key = (server_module, self.mcp_transport, remote_url or "", tuple(sorted(server_args.items())))
        if key not in self.mcp_clients:
            self.mcp_clients[key] = MCPClient(
                server_module,
                self.trace,
                self.project_root,
                failure_config=self.failure_config,
                transport=self.mcp_transport,
                remote_url=remote_url,
                **server_args,
            )
        return self.mcp_clients[key]

    def close_mcp_clients(self) -> None:
        for client in self.mcp_clients.values():
            client.close()
        self.mcp_clients.clear()


class BaseAgent:
    agent_id = "base-agent"
    capabilities: list[str] = []
    description = "Base agent"

    def __init__(self, context: AgentContext) -> None:
        self.context = context
        self.reasoner = build_reasoner(context.runtime)
        self.context.trace.record(
            "runtime_config",
            agent=self.agent_id,
            runtime=context.runtime,
            llm_enabled=getattr(self.reasoner, "enabled", False),
            llm_model=getattr(self.reasoner, "model", None),
            failure_config=context.failure_config.to_dict(),
        )

    @property
    def card(self) -> AgentCard:
        return AgentCard(
            agent_id=self.agent_id,
            name=self.agent_id.replace("-", " ").title(),
            capabilities=self.capabilities,
            description=self.description,
        )

    def classify(self, ticket: SupportTicket) -> TicketIntent:
        return self.reasoner.classify(ticket.query)

    def handle_task(self, message: A2AMessage) -> AgentResult:
        raise NotImplementedError

    def new_task_message(
        self,
        target_agent: str,
        capability: str,
        payload: dict[str, Any],
        context: dict[str, Any] | None = None,
        task_id: str | None = None,
    ) -> A2AMessage:
        return A2AMessage(
            message_type="task_request",
            sender_agent=self.agent_id,
            target_agent=target_agent,
            capability=capability,
            payload=payload,
            context=context or {},
            task_id=task_id or new_id("task"),
        )





