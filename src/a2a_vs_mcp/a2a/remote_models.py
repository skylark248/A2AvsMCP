from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..agents.hybrid_specialists import MCPDataAgent, MCPDocumentationAgent, MCPPolicyBillingAgent
from ..agents.specialists import CustomerDataAgent, DocumentationAgent, PolicyBillingAgent
from ..schemas import AgentCard
from .protocol import a2a_skill_id, agent_card_payload
from .sdk_compat import remote_binding_metadata


SPECIALIST_SPECS: dict[str, dict[str, Any]] = {
    "customer_data": {
        "agent_id": "customer_data_agent",
        "label": "Customer Data Agent",
        "capabilities": ["customer_data"],
        "description": "Remote specialist for customer, order, payment, warranty, and ticket history evidence.",
        "local_class": CustomerDataAgent,
        "hybrid_class": MCPDataAgent,
    },
    "documentation": {
        "agent_id": "documentation_agent",
        "label": "Setup Documentation Agent",
        "capabilities": ["documentation"],
        "description": "Remote specialist for setup, troubleshooting, and knowledge-base evidence.",
        "local_class": DocumentationAgent,
        "hybrid_class": MCPDocumentationAgent,
    },
    "policy_billing": {
        "agent_id": "policy_or_billing_agent",
        "label": "Policy Billing Agent",
        "capabilities": ["policy_billing"],
        "description": "Remote specialist for refund, payment, return, and warranty policy evidence.",
        "local_class": PolicyBillingAgent,
        "hybrid_class": MCPPolicyBillingAgent,
    },
}


def supported_specialist_roles() -> list[str]:
    return sorted(SPECIALIST_SPECS)


def card_for_role(role: str) -> AgentCard:
    spec = SPECIALIST_SPECS[role]
    return AgentCard(
        agent_id=spec["agent_id"],
        name=spec["label"],
        capabilities=list(spec["capabilities"]),
        description=spec["description"],
    )


def remote_agent_card_payload(role: str, service_url: str) -> dict[str, Any]:
    card = card_for_role(role)
    payload = agent_card_payload(card)
    payload["url"] = service_url.rstrip("/")
    payload["preferredTransport"] = "JSONRPC"
    payload["supportedInterfaces"] = [
        {
            "protocolBinding": "JSONRPC",
            "url": service_url.rstrip("/"),
        }
    ]
    payload["metadata"] = {
        **payload.get("metadata", {}),
        **remote_binding_metadata(),
        "agentId": card.agent_id,
        "role": role,
        "demoScope": "hosted-remote-a2a-specialist",
    }
    payload["skills"] = [
        {
            "id": a2a_skill_id(capability),
            "name": capability.replace("_", " ").title(),
            "description": f"Handles {capability.replace('_', ' ')} tasks over the remote A2A demo binding.",
            "tags": [capability],
            "inputModes": ["application/json", "text/plain"],
            "outputModes": ["application/json", "text/plain"],
            "examples": [f"Resolve a support ticket requiring {capability.replace('_', ' ')}."],
        }
        for capability in card.capabilities
    ]
    return payload


def agent_card_from_payload(payload: dict[str, Any]) -> AgentCard:
    metadata = payload.get("metadata") or {}
    skills = payload.get("skills") or []
    capabilities: list[str] = []
    for skill in skills:
        tags = skill.get("tags") or []
        for tag in tags:
            if tag not in capabilities:
                capabilities.append(tag)
    if not capabilities:
        capabilities = list(payload.get("capabilities") or [])
    return AgentCard(
        agent_id=str(metadata.get("agentId") or payload.get("name") or "remote_agent"),
        name=str(payload.get("name") or metadata.get("agentId") or "Remote Agent"),
        capabilities=capabilities,
        description=str(payload.get("description") or "Remote A2A specialist."),
    )


def agent_class_for_role(role: str, *, use_mcp: bool) -> type:
    spec = SPECIALIST_SPECS[role]
    return spec["hybrid_class"] if use_mcp else spec["local_class"]


def serializable_card(card: AgentCard) -> dict[str, Any]:
    return asdict(card)
