from __future__ import annotations

from ..schemas import AgentResult, SupportTicket
from .base import BaseAgent


class SingleSupportAgent(BaseAgent):
    agent_id = "single_support_agent"
    capabilities = ["resolve_ticket"]
    description = "Handles all support tasks without delegation."

    def resolve(self, ticket: SupportTicket) -> AgentResult:
        intent = self.classify(ticket)
        repo = self.context.repo
        evidence = {
            "customer": repo.get_customer_profile(ticket.customer_id),
            "orders": repo.get_order_history(ticket.customer_id),
            "billing": repo.get_payment_issues(ticket.customer_id, intent.order_id),
            "docs": repo.search_docs(ticket.query, intent.product_hint, intent.error_code) if intent.needs_docs else [],
            "warranty": repo.get_warranty(ticket.customer_id, intent.product_hint) if intent.needs_policy else [],
            "policy": repo.get_policy("warranty" if intent.needs_policy else "refund") if intent.needs_policy else {},
            "history": repo.get_ticket_history(ticket.customer_id),
        }
        self.context.trace.record("agent_reasoning", agent=self.agent_id, issue_type=intent.issue_type)
        summary = self.reasoner.summarize(ticket.query, evidence, issue_type=intent.issue_type)
        return AgentResult(agent_id=self.agent_id, summary=summary, details=evidence)
