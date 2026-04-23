from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from a2a_vs_mcp import evidence


def build_server(db_path: Path) -> FastMCP:
    mcp = FastMCP("Support Database MCP", json_response=True)

    # --- Tools (callable capabilities) ---

    @mcp.tool()
    def get_customer_profile(customer_id: str) -> dict[str, Any] | None:
        """Return a customer profile by customer ID."""
        return evidence.get_customer_profile(db_path, customer_id)

    @mcp.tool()
    def get_order_history(customer_id: str) -> list[dict[str, Any]]:
        """Return all orders for a customer."""
        return evidence.get_order_history(db_path, customer_id)

    @mcp.tool()
    def get_payment_issues(customer_id: str, order_id: str | None = None) -> list[dict[str, Any]]:
        """Return payment issues for a customer or specific order."""
        return evidence.get_payment_issues(db_path, customer_id, order_id)

    @mcp.tool()
    def get_ticket_history(customer_id: str) -> list[dict[str, Any]]:
        """Return historical tickets for a customer."""
        return evidence.get_ticket_history(db_path, customer_id)

    @mcp.tool()
    def get_warranty(customer_id: str, product: str | None = None) -> list[dict[str, Any]]:
        """Return warranty records for a customer and optional product."""
        return evidence.get_warranty(db_path, customer_id, product)

    # --- Resources (readable data at stable URIs, distinct from tool calls) ---
    # Template resource: URI parameter {customer_id} matches the function parameter.
    # Clients can read customer://C001 directly without calling a tool.

    @mcp.resource(
        "customer://{customer_id}",
        name="Customer Profile",
        description="Full customer profile record readable at a stable URI.",
        mime_type="application/json",
    )
    def resource_customer_profile(customer_id: str) -> str:
        import json
        profile = evidence.get_customer_profile(db_path, customer_id)
        return json.dumps(profile, indent=2) if profile else "{}"

    return mcp


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--db-path", required=True)
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = build_server(Path(args.db_path))
    server.settings.host = args.host
    server.settings.port = args.port
    server.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())