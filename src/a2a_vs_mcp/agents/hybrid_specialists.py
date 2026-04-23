from __future__ import annotations

from ..mcp.client import MCPClient
from ..schemas import A2AMessage, AgentResult
from .base import BaseAgent


class MCPEnabledMixin:
    db_server = "a2a_vs_mcp.mcp_servers.db_server"
    docs_server = "a2a_vs_mcp.mcp_servers.docs_server"

    def db_client(self) -> MCPClient:
        return self.context.get_mcp_client(self.db_server, db_path=str(self.context.repo.db_path))

    def docs_client(self) -> MCPClient:
        return self.context.get_mcp_client(self.docs_server, docs_dir=str(self.context.repo.docs_dir))

    def safe_call(self, client: MCPClient, tool: str, arguments: dict, default):
        try:
            return client.call(tool, arguments)
        except Exception as exc:
            self.context.trace.record("tool_error", tool=tool, error=str(exc), agent=self.agent_id)
            return default


class MCPDataAgent(MCPEnabledMixin, BaseAgent):
    agent_id = "customer_data_agent"
    capabilities = ["customer_data"]
    description = "Specialist for MCP-backed customer and order access."

    def handle_task(self, message: A2AMessage) -> AgentResult:
        ticket = message.payload["ticket"]
        intent = self.reasoner.classify(ticket["query"])
        client = self.db_client()
        details = {
            "customer": self.safe_call(client, "get_customer_profile", {"customer_id": ticket["customer_id"]}, None),
            "orders": self.safe_call(client, "get_order_history", {"customer_id": ticket["customer_id"]}, []),
            "billing": self.safe_call(
                client,
                "get_payment_issues",
                {"customer_id": ticket["customer_id"], "order_id": intent.order_id},
                [],
            ),
            "warranty": self.safe_call(
                client,
                "get_warranty",
                {"customer_id": ticket["customer_id"], "product": intent.product_hint},
                [],
            ),
        }
        summary = self.reasoner.summarize(ticket["query"], details, issue_type=intent.issue_type)
        return AgentResult(agent_id=self.agent_id, summary=summary, details=details)


class MCPDocumentationAgent(MCPEnabledMixin, BaseAgent):
    agent_id = "documentation_agent"
    capabilities = ["documentation"]
    description = "Specialist for MCP-backed document search."

    def handle_task(self, message: A2AMessage) -> AgentResult:
        ticket = message.payload["ticket"]
        intent = self.reasoner.classify(ticket["query"])
        client = self.docs_client()
        docs = self.safe_call(
            client,
            "search_docs",
            {"query": ticket["query"], "product": intent.product_hint, "error_code": intent.error_code},
            [],
        )
        details = {"docs": docs}
        summary = self.reasoner.summarize(ticket["query"], details, issue_type=intent.issue_type)
        return AgentResult(agent_id=self.agent_id, summary=summary, details=details)


class MCPPolicyBillingAgent(MCPEnabledMixin, BaseAgent):
    agent_id = "policy_or_billing_agent"
    capabilities = ["policy_billing"]
    description = "Specialist for MCP-backed policy and billing analysis."

    def handle_task(self, message: A2AMessage) -> AgentResult:
        ticket = message.payload["ticket"]
        intent = self.reasoner.classify(ticket["query"])
        db_client = self.db_client()
        docs_client = self.docs_client()
        lowered = ticket["query"].lower()
        policy_type = "return" if "return" in lowered or "return window" in lowered else "warranty" if intent.needs_policy else "refund"
        details = {
            "billing": self.safe_call(
                db_client,
                "get_payment_issues",
                {"customer_id": ticket["customer_id"], "order_id": intent.order_id},
                [],
            ),
            "warranty": self.safe_call(
                db_client,
                "get_warranty",
                {"customer_id": ticket["customer_id"], "product": intent.product_hint},
                [],
            ),
            "policy": self.safe_call(docs_client, "get_policy", {"policy_type": policy_type}, {}),
        }
        summary = self.reasoner.summarize(ticket["query"], details, issue_type=intent.issue_type)
        return AgentResult(agent_id=self.agent_id, summary=summary, details=details)
