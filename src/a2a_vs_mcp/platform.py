from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
import os

from .a2a.broker import A2ABroker
from .a2a.registry import RemoteA2ARegistry
from .a2a.remote_broker import RemoteA2ABroker
from .agents.base import AgentContext
from .agents.hybrid_specialists import MCPDataAgent, MCPDocumentationAgent, MCPPolicyBillingAgent
from .agents.single_agent import SingleSupportAgent
from .agents.specialists import CustomerDataAgent, DocumentationAgent, PolicyBillingAgent
from .agents.triage import TriageAgent
from .config import ProfileConfig, resolve_profile
from .identity import normalize_user_id, user_artifact_root
from .dataset import DemoRepository
from .mcp.client import MCPClient
from .schemas import ComparisonMetrics, FailureConfig, RunOutput, SupportTicket, new_id
from .trace import TraceRecorder


class DemoPlatform:
    def __init__(
        self,
        project_root: Path,
        runtime: str | None = None,
        mcp_transport: str | None = None,
        a2a_transport: str | None = None,
        profile_name: str | None = None,
        export_logs: bool | None = None,
        remote_mcp_urls: dict[str, str] | None = None,
        remote_a2a_urls: dict[str, str] | None = None,
        remote_a2a_auth_token: str | None = None,
        user_id: str | None = None,
    ) -> None:
        self.project_root = project_root
        self.user_id = normalize_user_id(user_id)
        self.artifact_root = user_artifact_root(project_root, self.user_id)
        self.profile: ProfileConfig = resolve_profile(
            profile_name,
            runtime=runtime,
            mcp_transport=mcp_transport or os.getenv("MCP_TRANSPORT"),
            a2a_transport=a2a_transport or os.getenv("A2A_TRANSPORT"),
            export_logs=export_logs,
        )
        self.runtime = self.profile.runtime
        self.mcp_transport = self.profile.mcp_transport
        self.a2a_transport = self.profile.a2a_transport
        self.export_logs = self.profile.export_logs
        self.remote_mcp_urls = remote_mcp_urls or {
            "db": os.getenv("REMOTE_MCP_DB_URL", ""),
            "docs": os.getenv("REMOTE_MCP_DOCS_URL", ""),
        }
        registry_urls = RemoteA2ARegistry(project_root).load()
        self.remote_a2a_urls = remote_a2a_urls or {
            "customer_data": os.getenv("REMOTE_A2A_CUSTOMER_URL", registry_urls.get("customer_data", "")),
            "documentation": os.getenv("REMOTE_A2A_DOCUMENTATION_URL", registry_urls.get("documentation", "")),
            "policy_billing": os.getenv("REMOTE_A2A_POLICY_URL", registry_urls.get("policy_billing", "")),
        }
        self.remote_a2a_auth_token = remote_a2a_auth_token if remote_a2a_auth_token is not None else os.getenv("REMOTE_A2A_TOKEN")
        self.repo = DemoRepository(project_root)
        self.scenarios = self.repo.load_scenarios()

    def get_ticket(self, scenario: str | None, query: str | None, customer_id: str | None) -> SupportTicket:
        if scenario:
            return self.scenarios[scenario]
        return SupportTicket(ticket_id=new_id("ticket"), customer_id=customer_id or "CUST-001", query=query or "", scenario="custom", title="Custom Ticket")

    def run(self, mode: str, ticket: SupportTicket, failure_config: FailureConfig | None = None) -> RunOutput:
        failure_config = failure_config or FailureConfig()
        trace = TraceRecorder(mode=mode, runtime=self.runtime, task_id=ticket.ticket_id)
        trace.record(
            "ticket_received",
            ticket=asdict(ticket),
            failure_config=failure_config.to_dict(),
            mcp_transport=self.mcp_transport,
            a2a_transport=self.a2a_transport,
            profile=self.profile.to_dict(),
            user_id=self.user_id,
        )
        if mode == "baseline":
            result = self._run_baseline(trace, ticket, failure_config)
        elif mode == "mcp":
            result = self._run_mcp(trace, ticket, failure_config)
        elif mode == "a2a":
            result = self._run_a2a(trace, ticket, failure_config)
        elif mode == "hybrid":
            result = self._run_hybrid(trace, ticket, failure_config)
        else:
            raise ValueError(f"Unknown mode: {mode}")
        trace_path = trace.save(self.artifact_root / "traces")
        external_log_path = None
        if self.export_logs:
            external_log_path = trace.export_external(
                self.artifact_root / "logs",
                profile=self.profile.name,
                requested_transport=self.mcp_transport,
                requested_a2a_transport=self.a2a_transport,
                trace_file=str(trace_path),
            )
        failures = self._failure_messages(trace)
        metrics = self._build_metrics(mode, trace, result["agents_used"])
        trace.record(
            "comparison_report",
            metrics=metrics.to_dict(),
            trace_file=str(trace_path),
            external_log_file=str(external_log_path) if external_log_path else None,
            failures=failures,
            a2a_transport=self.a2a_transport,
        )
        return RunOutput(
            mode=mode,
            runtime=self.runtime,
            ticket=ticket,
            final_answer=result["final_answer"],
            trace=trace.events,
            metrics=metrics,
            tools_used=result["tools_used"],
            agents_used=result["agents_used"],
            failures=failures,
            external_log_path=str(external_log_path) if external_log_path else None,
            a2a_transport=self.a2a_transport,
            mcp_transport=self.mcp_transport if mode in ("mcp", "hybrid") else None,
        )

    def _context(self, trace: TraceRecorder, failure_config: FailureConfig) -> AgentContext:
        return AgentContext(self.repo, trace, self.runtime, self.mcp_transport, self.project_root, failure_config, remote_mcp_urls=self.remote_mcp_urls)

    def _run_baseline(self, trace: TraceRecorder, ticket: SupportTicket, failure_config: FailureConfig) -> dict:
        context = self._context(trace, failure_config)
        agent = SingleSupportAgent(context)
        result = agent.resolve(ticket)
        return {"final_answer": result.summary, "tools_used": [], "agents_used": [agent.agent_id]}

    def _safe_tool_call(self, trace: TraceRecorder, client: MCPClient, tool: str, arguments: dict, default, agent_id: str):
        try:
            return client.call(tool, arguments)
        except Exception as exc:
            trace.record("tool_error", tool=tool, error=str(exc), agent=agent_id)
            return default

    def _run_mcp(self, trace: TraceRecorder, ticket: SupportTicket, failure_config: FailureConfig) -> dict:
        context = self._context(trace, failure_config)
        agent = SingleSupportAgent(context)
        intent = agent.classify(ticket)
        db_client = MCPClient(
            "a2a_vs_mcp.mcp_servers.db_server",
            trace,
            self.project_root,
            failure_config=failure_config,
            transport=self.mcp_transport,
            db_path=str(self.repo.db_path),
            remote_url=self.remote_mcp_urls.get("db") if self.mcp_transport == "remote_http" else None,
        )
        docs_client = MCPClient(
            "a2a_vs_mcp.mcp_servers.docs_server",
            trace,
            self.project_root,
            failure_config=failure_config,
            transport=self.mcp_transport,
            docs_dir=str(self.repo.docs_dir),
            remote_url=self.remote_mcp_urls.get("docs") if self.mcp_transport == "remote_http" else None,
        )
        try:
            evidence = {
                "customer": self._safe_tool_call(trace, db_client, "get_customer_profile", {"customer_id": ticket.customer_id}, None, agent.agent_id),
                "orders": self._safe_tool_call(trace, db_client, "get_order_history", {"customer_id": ticket.customer_id}, [], agent.agent_id),
                "billing": self._safe_tool_call(trace, db_client, "get_payment_issues", {"customer_id": ticket.customer_id, "order_id": intent.order_id}, [], agent.agent_id),
                "history": self._safe_tool_call(trace, db_client, "get_ticket_history", {"customer_id": ticket.customer_id}, [], agent.agent_id),
                "docs": self._safe_tool_call(
                    trace,
                    docs_client,
                    "search_docs",
                    {"query": ticket.query, "product": intent.product_hint, "error_code": intent.error_code},
                    [],
                    agent.agent_id,
                ) if intent.needs_docs else [],
                "policy": self._safe_tool_call(
                    trace,
                    docs_client,
                    "get_policy",
                    {"policy_type": "warranty" if intent.needs_policy else "refund"},
                    {},
                    agent.agent_id,
                ) if intent.needs_policy or intent.issue_type == "billing" else {},
                "warranty": self._safe_tool_call(
                    trace,
                    db_client,
                    "get_warranty",
                    {"customer_id": ticket.customer_id, "product": intent.product_hint},
                    [],
                    agent.agent_id,
                ) if intent.needs_policy or intent.issue_type == "billing" else [],
            }
        finally:
            db_client.close()
            docs_client.close()
        trace.record("agent_reasoning", agent=agent.agent_id, issue_type=intent.issue_type, via="mcp", mcp_transport=self.mcp_transport)
        final_answer = agent.reasoner.summarize(ticket.query, evidence, issue_type=intent.issue_type)
        return {
            "final_answer": final_answer,
            "tools_used": self._tool_names(trace),
            "agents_used": [agent.agent_id],
        }

    def _register_specialists(self, broker: A2ABroker, specialists: list, failure_config: FailureConfig) -> list[str]:
        registered = []
        for specialist in specialists:
            if specialist.agent_id in failure_config.unavailable_agents:
                broker.trace.record("a2a_message", message_type="agent_unavailable", sender=specialist.agent_id)
                continue
            broker.register(specialist.card, specialist)
            registered.append(specialist.agent_id)
        return registered

    def _remote_broker(self, trace: TraceRecorder, failure_config: FailureConfig, *, use_mcp: bool) -> RemoteA2ABroker:
        timeout_ms = 8000 if use_mcp and self.mcp_transport in {"stdio", "http", "remote_http"} else 5000
        return RemoteA2ABroker(
            trace,
            endpoints=self.remote_a2a_urls,
            runtime=self.runtime,
            mcp_transport=self.mcp_transport,
            project_root=self.project_root,
            failure_config=failure_config,
            remote_mcp_urls=self.remote_mcp_urls,
            use_mcp=use_mcp,
            max_retries=1,
            timeout_ms=timeout_ms,
            auth_token=self.remote_a2a_auth_token,
        )

    def _run_a2a(self, trace: TraceRecorder, ticket: SupportTicket, failure_config: FailureConfig) -> dict:
        context = self._context(trace, failure_config)
        triage = TriageAgent(context)
        if self.a2a_transport == "remote":
            broker = self._remote_broker(trace, failure_config, use_mcp=False)
            broker.discover()
            result = triage.resolve_with_broker(ticket, broker)
            agents_used = [triage.agent_id] + sorted(broker.cards)
            return {"final_answer": result.summary, "tools_used": [], "agents_used": agents_used}
        broker = A2ABroker(trace)
        specialists = [CustomerDataAgent(context), DocumentationAgent(context), PolicyBillingAgent(context)]
        registered = self._register_specialists(broker, specialists, failure_config)
        result = triage.resolve_with_broker(ticket, broker)
        agents_used = [triage.agent_id] + registered
        return {"final_answer": result.summary, "tools_used": [], "agents_used": agents_used}

    def _run_hybrid(self, trace: TraceRecorder, ticket: SupportTicket, failure_config: FailureConfig) -> dict:
        context = self._context(trace, failure_config)
        triage = TriageAgent(context)
        if self.a2a_transport == "remote":
            broker = self._remote_broker(trace, failure_config, use_mcp=True)
            broker.discover()
            result = triage.resolve_with_broker(ticket, broker)
            agents_used = [triage.agent_id] + sorted(broker.cards)
            return {"final_answer": result.summary, "tools_used": self._tool_names(trace), "agents_used": agents_used}
        broker_timeout_ms = 5000 if self.mcp_transport in {"stdio", "http"} else 1500
        broker = A2ABroker(trace, timeout_ms=broker_timeout_ms)
        specialists = [MCPDataAgent(context), MCPDocumentationAgent(context), MCPPolicyBillingAgent(context)]
        registered = self._register_specialists(broker, specialists, failure_config)
        try:
            result = triage.resolve_with_broker(ticket, broker)
        finally:
            context.close_mcp_clients()
        agents_used = [triage.agent_id] + registered
        return {"final_answer": result.summary, "tools_used": self._tool_names(trace), "agents_used": agents_used}

    def _tool_names(self, trace: TraceRecorder) -> list[str]:
        return [event["tool"] for event in trace.events if event["event_type"] == "tool_call"]

    def _failure_messages(self, trace: TraceRecorder) -> list[str]:
        failures = [event["error"] for event in trace.events if event.get("message_type") == "task_error"]
        failures.extend(event["error"] for event in trace.events if event.get("event_type") == "tool_error")
        failures.extend(event["error"] for event in trace.events if event.get("event_type") == "triage_warning")
        failures.extend(event["error"] for event in trace.events if event.get("event_type") == "a2a_remote_failure")
        return failures

    def _build_metrics(self, mode: str, trace: TraceRecorder, agents_used: list[str]) -> ComparisonMetrics:
        tool_calls = len([event for event in trace.events if event["event_type"] == "tool_call"])
        a2a_messages = len([
            event
            for event in trace.events
            if event["event_type"] == "a2a_message" or event["event_type"].startswith("a2a_remote_")
        ])
        retries = len([event for event in trace.events if event.get("message_type") == "task_retry" or event.get("event_type") == "a2a_remote_retry"])
        failures = len([event for event in trace.events if event.get("message_type") == "task_error" or event.get("event_type") in {"tool_error", "triage_warning", "a2a_remote_failure"}])
        complexity_map = {
            "baseline": "low",
            "mcp": "medium",
            "a2a": "medium" if self.a2a_transport == "local" else "high",
            "hybrid": "high",
        }
        strengths_map = {
            "baseline": ["Simple and fast to explain", "Lowest orchestration overhead"],
            "mcp": ["Strong tool boundaries", "Structured data access with reusable servers"],
            "a2a": ["Shows delegation and specialization", "Makes collaboration explicit"] if self.a2a_transport == "local" else ["Shows hosted agent discovery", "Makes the agent network boundary explicit"],
            "hybrid": ["Most realistic enterprise shape", "Clear separation of tools vs agents"] if self.a2a_transport == "local" else ["Most realistic hosted enterprise shape", "Shows remote agents plus MCP-backed evidence"],
        }
        weaknesses_map = {
            "baseline": ["No protocol comparison", "Single agent becomes crowded quickly"],
            "mcp": ["No agent collaboration", "Single agent still owns all decision-making"],
            "a2a": ["Specialists need local logic", "No standardized external tool layer"] if self.a2a_transport == "local" else ["Requires remote specialist services", "More network and protocol failure modes"],
            "hybrid": ["Highest implementation complexity", "More moving parts to operate and debug"],
        }
        return ComparisonMetrics(
            mode=mode,
            latency_ms=trace.latency_ms(),
            tool_calls=tool_calls,
            a2a_messages=a2a_messages,
            agents_involved=agents_used,
            complexity=complexity_map[mode],
            strengths=strengths_map[mode],
            weaknesses=weaknesses_map[mode],
            retries=retries,
            failures=failures,
        )
