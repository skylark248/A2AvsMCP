"""Race GitHub MCP server (RACE-07).

Wraps race.mocks.github. Three tools: get_repo_metadata, list_files, read_file.
All faults flow through race.mocks.github -> race.failure module's chokepoint (D-25).

Recorder + run_id reach mock callables via mcp_servers.race_context contextvars
(set by runner before MCPClient.call). Use transport='in_process' so contextvars
propagate within the same Python process (RESEARCH §5).
"""
from __future__ import annotations

import argparse
from typing import Any

from mcp.server.fastmcp import FastMCP

from a2a_vs_mcp.race.mocks import github as github_mock
from a2a_vs_mcp.mcp_servers.race_context import current_recorder, current_run_id


def build_server() -> FastMCP:
    mcp = FastMCP("Race GitHub MCP", json_response=True)

    @mcp.tool()
    def get_repo_metadata(repo_id: str) -> dict[str, Any]:
        """Return repo metadata (mocked, fault-injectable per D-25)."""
        return github_mock.get_repo_metadata(
            repo_id, recorder=current_recorder(), run_id=current_run_id()
        )

    @mcp.tool()
    def list_files(repo_id: str, path: str = "") -> list[str]:
        """List files in a repo path (mocked, fault-injectable)."""
        return github_mock.list_files(
            repo_id, path, recorder=current_recorder(), run_id=current_run_id()
        )

    @mcp.tool()
    def read_file(repo_id: str, file_path: str) -> str:
        """Read a file's content (mocked, synthetic content)."""
        return github_mock.read_file(
            repo_id, file_path, recorder=current_recorder(), run_id=current_run_id()
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
