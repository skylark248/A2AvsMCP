from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from a2a_vs_mcp import evidence


def build_server(docs_dir: Path) -> FastMCP:
    mcp = FastMCP("Support Docs MCP", json_response=True)

    # --- Tools (callable capabilities) ---

    @mcp.tool()
    def search_docs(query: str, product: str | None = None, error_code: str | None = None) -> list[dict[str, Any]]:
        """Search the local support documentation corpus."""
        return evidence.search_docs(docs_dir, query, product, error_code)

    @mcp.tool()
    def get_policy(policy_type: str) -> dict[str, Any]:
        """Return refund or warranty policy content."""
        return evidence.get_policy(docs_dir, policy_type)

    # --- Resources (readable data at stable URIs, distinct from tool calls) ---

    @mcp.resource(
        "policy://refund",
        name="Refund Policy",
        description="Full text of the customer refund and return policy.",
        mime_type="text/markdown",
    )
    def resource_refund_policy() -> str:
        return (docs_dir / "refund_policy.md").read_text(encoding="utf-8")

    @mcp.resource(
        "policy://warranty",
        name="Warranty Rules",
        description="Full text of the product warranty and replacement rules.",
        mime_type="text/markdown",
    )
    def resource_warranty_rules() -> str:
        return (docs_dir / "warranty_rules.md").read_text(encoding="utf-8")

    # --- Prompts (reusable prompt templates the LLM host can invoke) ---
    # A third MCP primitive alongside tools and resources — lets the server ship
    # canned instructions that clients surface in the UI or pass to the model.

    @mcp.prompt(
        name="support_triage",
        description=(
            "Structured triage prompt for a support ticket. "
            "Instructs the model to gather evidence before forming a resolution."
        ),
    )
    def prompt_support_triage(ticket_query: str, customer_id: str) -> list[dict[str, Any]]:
        return [
            {
                "role": "user",
                "content": (
                    f"You are a support triage agent. Customer {customer_id} submitted:\n\n"
                    f"{ticket_query}\n\n"
                    "Before responding:\n"
                    "1. Call search_docs to find relevant documentation.\n"
                    "2. Call get_policy with type 'refund' or 'warranty' as needed.\n"
                    "3. Read policy://refund or policy://warranty for full policy text.\n"
                    "Only after gathering evidence, provide a concise resolution with cited sources."
                ),
            }
        ]

    return mcp


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--docs-dir", required=True)
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = build_server(Path(args.docs_dir))
    server.settings.host = args.host
    server.settings.port = args.port
    server.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())