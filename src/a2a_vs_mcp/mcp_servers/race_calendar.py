"""Race Calendar MCP server (RACE-07).

Wraps race.mocks.calendar. Two tools: get_free_busy, propose_time.
Faults route through race.mocks.calendar -> race.failure module's chokepoint (D-25).
"""
from __future__ import annotations

import argparse
from typing import Any

from mcp.server.fastmcp import FastMCP

from a2a_vs_mcp.race.mocks import calendar as calendar_mock
from a2a_vs_mcp.mcp_servers.race_context import current_recorder, current_run_id


def build_server() -> FastMCP:
    mcp = FastMCP("Race Calendar MCP", json_response=True)

    @mcp.tool()
    def get_free_busy(owner: str) -> dict[str, Any]:
        """Return free/busy windows for a calendar owner."""
        return calendar_mock.get_free_busy(
            owner, recorder=current_recorder(), run_id=current_run_id()
        )

    @mcp.tool()
    def propose_time(owners: list[str], duration_min: int) -> dict[str, Any]:
        """Compute mutual free window across owners."""
        return calendar_mock.propose_time(
            owners, duration_min, recorder=current_recorder(), run_id=current_run_id()
        )

    return mcp


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = build_server()
    server.settings.host = args.host
    server.settings.port = args.port
    server.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
