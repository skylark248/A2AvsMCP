"""Race Travel MCP server (RACE-07).

Wraps race.mocks.travel. Three tools: search_flights, search_hotels,
book_itinerary. Faults route through race.mocks.travel -> race.failure module's chokepoint (D-25).
"""
from __future__ import annotations

import argparse
from typing import Any

from mcp.server.fastmcp import FastMCP

from a2a_vs_mcp.race.mocks import travel as travel_mock
from a2a_vs_mcp.mcp_servers.race_context import current_recorder, current_run_id


def build_server() -> FastMCP:
    mcp = FastMCP("Race Travel MCP", json_response=True)

    @mcp.tool()
    def search_flights(origin: str, destination: str) -> list[dict[str, Any]]:
        """Search flights by origin/destination."""
        return travel_mock.search_flights(
            origin, destination, recorder=current_recorder(), run_id=current_run_id()
        )

    @mcp.tool()
    def search_hotels(city: str) -> list[dict[str, Any]]:
        """Search hotels by city."""
        return travel_mock.search_hotels(
            city, recorder=current_recorder(), run_id=current_run_id()
        )

    @mcp.tool()
    def book_itinerary(flight_ids: list[str], hotel_id: str, nights: int) -> dict[str, Any]:
        """Book flights + hotel; returns confirmation + total cost."""
        return travel_mock.book_itinerary(
            flight_ids, hotel_id, nights, recorder=current_recorder(), run_id=current_run_id()
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
