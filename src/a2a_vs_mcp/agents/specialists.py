from __future__ import annotations

from ..schemas import AgentResult, A2AMessage
from .base import BaseAgent


class CustomerDataAgent(BaseAgent):
    agent_id = "customer_data_agent"
    capabilities = ["customer_data"]
    description = "Specialist for orders, payments, warranties, and ticket history."

    def handle_task(self, message: A2AMessage) -> AgentResult:
        ticket = message.payload["ticket"]
        intent = self.reasoner.classify(ticket["query"])
        repo = self.context.repo
        details = {
            "customer": repo.get_customer_profile(ticket["customer_id"]),
            "orders": repo.get_order_history(ticket["customer_id"]),
            "billing": repo.get_payment_issues(ticket["customer_id"], intent.order_id),
            "warranty": repo.get_warranty(ticket["customer_id"], intent.product_hint),
            "history": repo.get_ticket_history(ticket["customer_id"]),
        }
        summary = self.reasoner.summarize(ticket["query"], details, issue_type=intent.issue_type)
        return AgentResult(agent_id=self.agent_id, summary=summary, details=details)


class DocumentationAgent(BaseAgent):
    agent_id = "documentation_agent"
    capabilities = ["documentation"]
    description = "Specialist for troubleshooting and knowledge base lookup."

    def handle_task(self, message: A2AMessage) -> AgentResult:
        ticket = message.payload["ticket"]
        intent = self.reasoner.classify(ticket["query"])
        docs = self.context.repo.search_docs(ticket["query"], intent.product_hint, intent.error_code)
        details = {"docs": docs}
        summary = self.reasoner.summarize(ticket["query"], details, issue_type=intent.issue_type)
        return AgentResult(agent_id=self.agent_id, summary=summary, details=details)


class PolicyBillingAgent(BaseAgent):
    agent_id = "policy_or_billing_agent"
    capabilities = ["policy_billing"]
    description = "Specialist for returns, refunds, payments, and warranty policy."

    def handle_task(self, message: A2AMessage) -> AgentResult:
        ticket = message.payload["ticket"]
        intent = self.reasoner.classify(ticket["query"])
        lowered = ticket["query"].lower()
        policy_type = "return" if "return" in lowered or "return window" in lowered else "warranty" if intent.needs_policy else "refund"
        details = {
            "billing": self.context.repo.get_payment_issues(ticket["customer_id"], intent.order_id),
            "policy": self.context.repo.get_policy(policy_type),
            "warranty": self.context.repo.get_warranty(ticket["customer_id"], intent.product_hint),
        }
        summary = self.reasoner.summarize(ticket["query"], details, issue_type=intent.issue_type)
        return AgentResult(agent_id=self.agent_id, summary=summary, details=details)
