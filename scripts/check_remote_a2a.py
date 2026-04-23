from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a2a_vs_mcp.a2a.registry import DEFAULT_REMOTE_A2A_REGISTRY, RemoteA2ARegistry
from a2a_vs_mcp.a2a.remote_client import RemoteA2AClient
from a2a_vs_mcp.schemas import A2AMessage, new_id


CAPABILITY_BY_ROLE = {
    "customer_data": "customer_data",
    "documentation": "documentation",
    "policy_billing": "policy_billing",
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check remote A2A specialist Agent Cards and task handling.")
    parser.add_argument("--customer-url", default="")
    parser.add_argument("--documentation-url", default="")
    parser.add_argument("--policy-url", default="")
    parser.add_argument("--token", default="")
    parser.add_argument("--timeout", type=float, default=5.0)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    registry = RemoteA2ARegistry(ROOT).load()
    endpoints = {
        "customer_data": args.customer_url or registry.get("customer_data") or DEFAULT_REMOTE_A2A_REGISTRY["customer_data"],
        "documentation": args.documentation_url or registry.get("documentation") or DEFAULT_REMOTE_A2A_REGISTRY["documentation"],
        "policy_billing": args.policy_url or registry.get("policy_billing") or DEFAULT_REMOTE_A2A_REGISTRY["policy_billing"],
    }
    ticket = {
        "ticket_id": "REMOTE-A2A-CHECK",
        "customer_id": "CUST-001",
        "query": "I was double charged and need help checking warranty and setup notes.",
        "scenario": "remote_a2a_check",
        "title": "Remote A2A Check",
    }
    for role, endpoint in endpoints.items():
        client = RemoteA2AClient(endpoint, timeout_s=args.timeout, token=args.token or None)
        card = client.fetch_agent_card()
        skills = card.get("skills") or []
        capability = CAPABILITY_BY_ROLE[role]
        tags = {tag for skill in skills for tag in (skill.get("tags") or [])}
        if capability not in tags:
            raise SystemExit(f"{role} card at {endpoint} does not advertise {capability}")
        agent_id = card.get("metadata", {}).get("agentId") or role
        message = A2AMessage(
            message_type="task_request",
            sender_agent="remote_check",
            target_agent=agent_id,
            capability=capability,
            payload={"ticket": ticket},
            task_id=new_id("remote-check"),
        )
        result = client.send_task(
            message,
            runtime="mock",
            use_mcp=False,
            mcp_transport="in_process",
            remote_mcp_urls={},
            failure_config={},
        )
        if result.get("status") != "completed":
            raise SystemExit(f"{role} task did not complete: {result}")
        print(f"ok {role}: {endpoint} -> {agent_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
