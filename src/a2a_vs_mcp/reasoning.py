from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import json
import os
import re


@dataclass
class TicketIntent:
    issue_type: str
    needs_docs: bool
    needs_data: bool
    needs_policy: bool
    order_id: str | None = None
    error_code: str | None = None
    product_hint: str | None = None


class MockReasoner:
    def classify(self, query: str) -> TicketIntent:
        lowered = query.lower()
        order_id = self._match(r"(ord-\d+)", lowered)
        error_code = self._match(r"(x\d+)", lowered)
        product_hint = "HomeSensor Pro" if "homesensor" in lowered else "SmartHub Mini" if "smarthub" in lowered else None
        billing = any(term in lowered for term in ("charged twice", "payment", "double", "billing"))
        warranty = any(term in lowered for term in ("warranty", "return", "replacement"))
        troubleshooting = any(term in lowered for term in ("error", "setup", "failing", "defect"))
        order = any(term in lowered for term in ("where is my order", "delivery", "order", "delayed", "shipment"))
        if billing:
            issue_type = "billing"
        elif troubleshooting:
            issue_type = "troubleshooting"
        elif warranty:
            issue_type = "warranty_return"
        else:
            issue_type = "order_status"
        return TicketIntent(
            issue_type=issue_type,
            needs_docs=troubleshooting,
            needs_data=billing or order or warranty,
            needs_policy=warranty or billing,
            order_id=order_id,
            error_code=error_code,
            product_hint=product_hint,
        )

    def summarize(self, ticket: str, evidence: dict[str, Any], issue_type: str | None = None) -> str:
        clauses = self._build_clauses(evidence)
        if not clauses:
            return "I could not find enough information to resolve the ticket."
        selected_keys = self._select_clause_order(ticket, issue_type, clauses)
        selected = [clauses[key] for key in selected_keys if key in clauses]
        return " ".join(selected)

    def _build_clauses(self, evidence: dict[str, Any]) -> dict[str, str]:
        clauses: dict[str, str] = {}
        if evidence.get("orders"):
            order = evidence["orders"][0]
            clauses["order"] = (
                f"Order {order['order_id']} for {order['product']} is currently '{order['status']}' with tracking {order['tracking_id']} and ETA {order['eta']}."
            )
        if evidence.get("billing"):
            payment = evidence["billing"][0]
            clauses["billing"] = (
                f"A duplicate-charge issue appears on order {payment['order_id']} with status '{payment['status']}'."
            )
        if evidence.get("docs"):
            top = evidence["docs"][0]
            clauses["docs"] = (
                f"The best troubleshooting guidance comes from {top['document']}: restart the device, reconnect to 2.4 GHz Wi-Fi, and retry pairing."
            )
        if evidence.get("warranty"):
            warranty = evidence["warranty"][0] if evidence["warranty"] else None
            if warranty:
                clauses["warranty"] = (
                    f"The product is still under {warranty['coverage']} warranty until {warranty['expires_on']}."
                )
        if evidence.get("policy"):
            policy = evidence["policy"]
            document = policy.get("document") if isinstance(policy, dict) else None
            content = policy.get("content", "") if isinstance(policy, dict) else ""
            lowered = content.lower()
            if "30 days" in lowered or "return within 30 days" in lowered:
                clauses["policy"] = "Returns normally require a valid return window, but warranty-backed defects can still be reviewed for replacement or approved return."
            elif "warranty" in lowered or document == "warranty_rules.md":
                clauses["policy"] = "Warranty policy allows repair, replacement, or an approved return when the defect is still covered."
            elif document:
                clauses["policy"] = f"Policy guidance comes from {document}."
        return clauses

    def _select_clause_order(self, ticket: str, issue_type: str | None, clauses: dict[str, str]) -> list[str]:
        lowered = ticket.lower()
        wants_order = any(term in lowered for term in ("delay", "delayed", "delivery", "shipment", "where is my order"))
        wants_billing = any(term in lowered for term in ("charged twice", "payment", "double", "billing"))
        wants_troubleshooting = any(term in lowered for term in ("error", "setup", "failing", "defect"))
        wants_warranty = any(term in lowered for term in ("warranty", "replacement"))
        wants_return = "return" in lowered
        wants_policy = "return window" in lowered or "policy" in lowered or (wants_return and wants_warranty)

        desired: list[str] = []
        if wants_billing:
            desired.append("billing")
        if wants_order:
            desired.append("order")
        if wants_troubleshooting:
            desired.append("docs")
        if wants_warranty:
            desired.append("warranty")
        if wants_policy:
            desired.append("policy")

        if not desired:
            defaults = {
                "billing": ["billing", "order", "policy"],
                "troubleshooting": ["docs", "warranty", "policy"],
                "warranty_return": ["warranty", "policy", "order"],
                "order_status": ["order", "billing", "warranty"],
            }
            desired = defaults.get(issue_type or "order_status", ["order", "billing", "docs"])

        ordered: list[str] = []
        for key in desired:
            if key in clauses and key not in ordered:
                ordered.append(key)

        minimum = 2 if len(ordered) < 2 else len(ordered)
        for fallback in ["order", "billing", "docs", "warranty", "policy"]:
            if len(ordered) >= max(minimum, len(desired)):
                break
            if fallback in clauses and fallback not in ordered:
                ordered.append(fallback)

        max_clauses = min(max(len(desired), 2 if len(clauses) > 1 else 1), 3)
        return ordered[:max_clauses]

    def _match(self, pattern: str, query: str) -> str | None:
        found = re.search(pattern, query, re.IGNORECASE)
        return found.group(1).upper() if found else None


class LLMReasoner(MockReasoner):
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.enabled = bool(self.api_key)
        self._client = None
        if self.enabled:
            from openai import OpenAI

            self._client = OpenAI(api_key=self.api_key)

    def classify(self, query: str) -> TicketIntent:
        if not self.enabled or self._client is None:
            return super().classify(query)
        try:
            prompt = (
                "Classify the support ticket into one of: order_status, billing, troubleshooting, warranty_return. "
                "Return JSON with keys: issue_type, needs_docs, needs_data, needs_policy, order_id, error_code, product_hint. "
                "Set unknown optional fields to null. Product hint should be either 'SmartHub Mini', 'HomeSensor Pro', or null."
            )
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": query},
                ],
                text={
                    "format": {
                        "type": "json_schema",
                        "name": "ticket_intent",
                        "strict": True,
                        "schema": {
                            "type": "object",
                            "additionalProperties": False,
                            "properties": {
                                "issue_type": {
                                    "type": "string",
                                    "enum": ["order_status", "billing", "troubleshooting", "warranty_return"],
                                },
                                "needs_docs": {"type": "boolean"},
                                "needs_data": {"type": "boolean"},
                                "needs_policy": {"type": "boolean"},
                                "order_id": {"type": ["string", "null"]},
                                "error_code": {"type": ["string", "null"]},
                                "product_hint": {"type": ["string", "null"]},
                            },
                            "required": [
                                "issue_type",
                                "needs_docs",
                                "needs_data",
                                "needs_policy",
                                "order_id",
                                "error_code",
                                "product_hint",
                            ],
                        },
                    }
                },
            )
            content = getattr(response, "output_text", "") or "{}"
            payload = json.loads(content)
            return TicketIntent(**payload)
        except Exception:
            return super().classify(query)

    def summarize(self, ticket: str, evidence: dict[str, Any], issue_type: str | None = None) -> str:
        if not self.enabled or self._client is None:
            return super().summarize(ticket, evidence, issue_type=issue_type)
        try:
            prompt = (
                "You are a support agent. Write a concise, customer-facing answer using the provided evidence. "
                "Do not invent facts. Prefer a direct answer with at most three short sentences and one recommended next step if needed."
            )
            response = self._client.responses.create(
                model=self.model,
                input=[
                    {"role": "system", "content": prompt},
                    {
                        "role": "user",
                        "content": json.dumps(
                            {
                                "ticket": ticket,
                                "issue_type": issue_type,
                                "evidence": evidence,
                            },
                            indent=2,
                        ),
                    },
                ],
            )
            text = getattr(response, "output_text", "").strip()
            return text or super().summarize(ticket, evidence, issue_type=issue_type)
        except Exception:
            return super().summarize(ticket, evidence, issue_type=issue_type)


_FAKE_SUMMARIES: dict[str, str] = {
    "order_status": (
        "Your order is currently in transit and on track for delivery within the estimated window. "
        "The tracking number has been confirmed as active with the carrier. "
        "No further action is required from your end at this time."
    ),
    "billing": (
        "I can see a duplicate charge has been flagged on your account for the referenced order. "
        "Our billing team has initiated a review and you can expect a resolution within 3 to 5 business days. "
        "We apologise for the inconvenience and will notify you by email once the refund is processed."
    ),
    "troubleshooting": (
        "Based on the error code you provided, the recommended fix is a factory reset followed by re-pairing on the 2.4 GHz band. "
        "Hold the reset button for 10 seconds until the indicator light flashes twice, then retry the pairing process. "
        "If the issue persists after two attempts, our warranty team can arrange an expedited replacement."
    ),
    "warranty_return": (
        "Your device falls within the standard 12-month warranty coverage and qualifies for a full replacement unit. "
        "Please initiate the return through the support portal using the order number and a pre-paid shipping label will be emailed within 24 hours. "
        "The replacement will ship once the defective unit is received at our service centre."
    ),
}


class FakeReasoningEngine(MockReasoner):
    """Deterministic reasoning stub for tests that exercise the LLM path without an API key.

    classify() delegates to MockReasoner (keyword-based, fully deterministic).
    summarize() returns canned, realistic customer support text keyed on issue_type.
    Selected via runtime="fake_llm" in build_reasoner() in agents/base.py.
    """

    def summarize(self, ticket: str, evidence: dict[str, Any], issue_type: str | None = None) -> str:
        key = issue_type or "order_status"
        return _FAKE_SUMMARIES.get(key, _FAKE_SUMMARIES["order_status"])

