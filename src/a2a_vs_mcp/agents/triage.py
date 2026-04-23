from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..a2a.broker import A2ABroker
from ..schemas import AgentResult, SupportTicket
from .base import BaseAgent


class TriageAgent(BaseAgent):
    agent_id = "triage_agent"
    capabilities = ["triage"]
    description = "Coordinates specialists and merges results."

    def resolve_with_broker(self, ticket: SupportTicket, broker: A2ABroker) -> AgentResult:
        if "parallel_investigation" in ticket.tags:
            return self._resolve_parallel(ticket, broker)
        intent = self.classify(ticket)
        self.context.trace.record("agent_reasoning", agent=self.agent_id, issue_type=intent.issue_type)
        results: list[AgentResult] = []
        if intent.needs_data or intent.issue_type in {"order_status", "billing", "warranty_return"}:
            result = self._request_specialist(ticket, broker, "customer_data")
            if result:
                results.append(result)
        if intent.needs_docs:
            result = self._request_specialist(ticket, broker, "documentation")
            if result:
                results.append(result)
        if intent.needs_policy or intent.issue_type in {"billing", "warranty_return"}:
            result = self._request_specialist(ticket, broker, "policy_billing")
            if result:
                results.append(result)

        merged_details = {result.agent_id: result.details for result in results}
        final_answer = self._merge(ticket, results, intent.issue_type)
        self.context.trace.record(
            "triage_merge",
            ticket_id=ticket.ticket_id,
            contributors=[result.agent_id for result in results],
            final_answer=final_answer,
        )
        return AgentResult(agent_id=self.agent_id, summary=final_answer, details=merged_details)

    def _request_specialist(self, ticket: SupportTicket, broker: A2ABroker, capability: str) -> AgentResult | None:
        try:
            card = broker.find_by_capability(capability)
            payload = {"ticket": asdict(ticket)}
            if self.context.failure_config.malformed_task and capability == "policy_billing":
                payload = {"broken": True}
            return broker.send_task(
                self.new_task_message(card.agent_id, capability, payload, task_id=ticket.ticket_id)
            )
        except Exception as exc:
            self.context.trace.record(
                "triage_warning",
                capability=capability,
                error=str(exc),
                ticket_id=ticket.ticket_id,
            )
            return None

    def _resolve_parallel(self, ticket: SupportTicket, broker: A2ABroker) -> AgentResult:
        self.context.trace.record(
            "agent_reasoning",
            agent=self.agent_id,
            issue_type="parallel_investigation",
        )
        capabilities = ["customer_data", "documentation", "policy_billing"]
        messages = [
            self.new_task_message(
                broker.find_by_capability(cap).agent_id,
                cap,
                {"ticket": asdict(ticket)},
                task_id=ticket.ticket_id,
            )
            for cap in capabilities
        ]
        results = broker.send_tasks_parallel(messages)
        merged_details = {r.agent_id: r.details for r in results}
        final_answer = self._merge(ticket, results, "parallel_investigation")
        self.context.trace.record(
            "triage_merge",
            ticket_id=ticket.ticket_id,
            contributors=[r.agent_id for r in results],
            final_answer=final_answer,
        )
        return AgentResult(agent_id=self.agent_id, summary=final_answer, details=merged_details)

    def _merge(self, ticket: SupportTicket, results: list[AgentResult], issue_type: str) -> str:
        if not results:
            return "No specialist was able to complete this ticket. Check the trace for the failure path."

        combined_evidence = self._combine_details(results)
        customer_answer = self.reasoner.summarize(ticket.query, combined_evidence, issue_type=issue_type)

        contribution_lines: list[str] = []
        for result in results:
            useful_keys = [key for key, value in result.details.items() if value]
            contribution_lines.append(f"{result.agent_id}: supplied {', '.join(sorted(useful_keys))}")

        internal_summary = " | ".join(contribution_lines)
        return f"Triage summary for {ticket.ticket_id}: {customer_answer} Internal contributions: {internal_summary}"

    def _combine_details(self, results: list[AgentResult]) -> dict[str, Any]:
        merged: dict[str, Any] = {}
        for result in results:
            for key, value in result.details.items():
                if not value:
                    continue
                if isinstance(value, list):
                    bucket = merged.setdefault(key, [])
                    seen = {repr(item) for item in bucket}
                    for item in value:
                        marker = repr(item)
                        if marker not in seen:
                            bucket.append(item)
                            seen.add(marker)
                elif isinstance(value, dict):
                    bucket = merged.setdefault(key, {})
                    for sub_key, sub_value in value.items():
                        if sub_value and sub_key not in bucket:
                            bucket[sub_key] = sub_value
                else:
                    merged.setdefault(key, value)
        return merged
