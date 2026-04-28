from __future__ import annotations

from pathlib import Path
from typing import Any, Callable
import anyio
import json
import os
import socket
import subprocess
import sys
import tempfile
import time

from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client

from ..schemas import FailureConfig
from ..trace import TraceRecorder
from ..mcp_servers.db_server import build_server as build_db_server
from ..mcp_servers.docs_server import build_server as build_docs_server
from ..mcp_servers import race_github, race_calendar, race_travel


SERVER_BUILDERS: dict[str, Callable[..., Any]] = {
    "a2a_vs_mcp.mcp_servers.db_server": build_db_server,
    "a2a_vs_mcp.mcp_servers.docs_server": build_docs_server,
    "a2a_vs_mcp.mcp_servers.race_github": lambda **_: race_github.build_server(),
    "a2a_vs_mcp.mcp_servers.race_calendar": lambda **_: race_calendar.build_server(),
    "a2a_vs_mcp.mcp_servers.race_travel": lambda **_: race_travel.build_server(),
}


class MCPClient:
    def __init__(
        self,
        server_module: str,
        trace: TraceRecorder,
        project_root: Path,
        failure_config: FailureConfig | None = None,
        transport: str = "in_process",
        remote_url: str | None = None,
        **server_args: str,
    ) -> None:
        self.server_module = server_module
        self.trace = trace
        self.project_root = project_root
        self.server_args = server_args
        self.failure_config = failure_config or FailureConfig()
        self.requested_transport = transport
        self.transport = transport
        self.remote_url = remote_url
        self.server = self._build_server() if transport == "in_process" else None
        self.http_process: subprocess.Popen[str] | None = None
        self.http_stderr_file = None
        self.http_url: str | None = None
        if transport == "http":
            self._start_http_server()
        if transport == "remote_http":
            self.http_url = remote_url
        try:
            self._discovered_tools = self._discover_tools(transport)
        except Exception as exc:
            if transport == "in_process":
                raise
            self.close()
            self.transport = "in_process"
            self.server = self._build_server()
            self.trace.record(
                "tool_transport_fallback",
                server=self.server_module,
                requested_transport=transport,
                active_transport=self.transport,
                error=str(exc),
            )
            self._discovered_tools = self._discover_tools(self.transport)
        self.trace.record(
            "tool_discovery",
            server=self.server_module,
            tools=self._discovered_tools,
            protocol="official_mcp_sdk",
            transport=self.transport,
            requested_transport=self.requested_transport,
        )
        # Discover resources and prompts to show learners all three MCP primitives.
        # Resources expose data at stable URIs; prompts are reusable templates.
        # Neither requires an explicit tool call — they are distinct MCP primitives.
        try:
            discovered = self._discover_resources_and_prompts(self.transport)
            if discovered["resources"] or discovered["prompts"]:
                self.trace.record(
                    "mcp_capability_discovery",
                    server=self.server_module,
                    protocol="official_mcp_sdk",
                    transport=self.transport,
                    resources=discovered["resources"],
                    prompts=discovered["prompts"],
                    note=(
                        "MCP exposes three primitives: tools (callable), "
                        "resources (readable URIs), and prompts (reusable templates)."
                    ),
                )
        except Exception:
            pass  # Resource/prompt discovery is informational — never block execution

    def call(self, tool: str, arguments: dict[str, Any]) -> Any:
        if tool not in self._discovered_tools:
            raise RuntimeError(f"Tool '{tool}' is not exposed by {self.server_module}")
        self._simulate_failure(tool)
        self.trace.record(
            "tool_call",
            tool=tool,
            arguments=arguments,
            server=self.server_module,
            protocol="official_mcp_sdk",
            transport=self.transport,
            requested_transport=self.requested_transport,
        )
        if self.transport == "stdio":
            return anyio.run(self._call_once_stdio, tool, arguments)
        if self.transport in {"http", "remote_http"}:
            return anyio.run(self._call_once_http, tool, arguments)
        return anyio.run(self._call_once_in_process, tool, arguments)

    def _discover_resources_and_prompts(self, transport: str) -> dict[str, list[str]]:
        if transport == "stdio":
            return anyio.run(self._list_resources_prompts_stdio)
        if transport in {"http", "remote_http"}:
            return anyio.run(self._list_resources_prompts_http)
        return anyio.run(self._list_resources_prompts_in_process)

    async def _list_resources_prompts_in_process(self) -> dict[str, list[str]]:
        assert self.server is not None
        resources = await self.server.list_resources()
        prompts = await self.server.list_prompts()
        return {
            "resources": [str(r.uri) for r in resources],
            "prompts": [p.name for p in prompts],
        }

    async def _list_resources_prompts_stdio(self) -> dict[str, list[str]]:
        async with stdio_client(self._build_stdio_params()) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                resources = await session.list_resources()
                prompts = await session.list_prompts()
                return {
                    "resources": [str(r.uri) for r in resources.resources],
                    "prompts": [p.name for p in prompts.prompts],
                }

    async def _list_resources_prompts_http(self) -> dict[str, list[str]]:
        assert self.http_url is not None
        async with streamable_http_client(self.http_url) as streams:
            async with ClientSession(*streams[:2]) as session:
                await session.initialize()
                resources = await session.list_resources()
                prompts = await session.list_prompts()
                return {
                    "resources": [str(r.uri) for r in resources.resources],
                    "prompts": [p.name for p in prompts.prompts],
                }

    def _discover_tools(self, transport: str) -> list[str]:
        if transport == "stdio":
            return anyio.run(self._list_tools_stdio)
        if transport == "remote_http" and not self.http_url:
            raise ValueError(f"Remote MCP URL is required for {self.server_module}")
        if transport in {"http", "remote_http"}:
            return anyio.run(self._list_tools_http)
        return anyio.run(self._list_tools_in_process)

    async def _list_tools_in_process(self) -> list[str]:
        assert self.server is not None
        tools = await self.server.list_tools()
        return [tool.name for tool in tools]

    async def _call_once_in_process(self, tool: str, arguments: dict[str, Any]) -> Any:
        assert self.server is not None
        result = await self.server.call_tool(tool, arguments)
        if isinstance(result, tuple) and len(result) == 2:
            _, structured = result
        else:
            structured = result
        if structured is not None:
            return self._unwrap_structured(structured)
        return None

    async def _list_tools_stdio(self) -> list[str]:
        async with stdio_client(self._build_stdio_params()) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                result = await session.list_tools()
                return [tool.name for tool in result.tools]

    async def _call_once_stdio(self, tool: str, arguments: dict[str, Any]) -> Any:
        async with stdio_client(self._build_stdio_params()) as streams:
            async with ClientSession(*streams) as session:
                await session.initialize()
                result = await session.call_tool(tool, arguments)
                structured = getattr(result, "structuredContent", None)
                if structured is not None:
                    return self._unwrap_structured(structured)
                return self._unwrap_structured(getattr(result, "content", None))

    async def _list_tools_http(self) -> list[str]:
        assert self.http_url is not None
        async with streamable_http_client(self.http_url) as streams:
            async with ClientSession(*streams[:2]) as session:
                await session.initialize()
                result = await session.list_tools()
                return [tool.name for tool in result.tools]

    async def _call_once_http(self, tool: str, arguments: dict[str, Any]) -> Any:
        assert self.http_url is not None
        async with streamable_http_client(self.http_url) as streams:
            async with ClientSession(*streams[:2]) as session:
                await session.initialize()
                result = await session.call_tool(tool, arguments)
                structured = getattr(result, "structuredContent", None)
                if structured is not None:
                    return self._unwrap_structured(structured)
                return self._unwrap_structured(getattr(result, "content", None))

    def _build_stdio_params(self) -> StdioServerParameters:
        args = ["-m", self.server_module]
        normalized_args = {key.replace("_", "-"): value for key, value in self.server_args.items()}
        if self.server_module.endswith("db_server"):
            args.extend(["--db-path", str(normalized_args["db-path"])])
        else:
            args.extend(["--docs-dir", str(normalized_args["docs-dir"])])
        return StdioServerParameters(
            command=sys.executable,
            args=args,
            cwd=str(self.project_root),
        )

    def _build_server(self) -> Any:
        builder = SERVER_BUILDERS[self.server_module]
        normalized_args = {key.replace("_", "-"): value for key, value in self.server_args.items()}
        if self.server_module.endswith("db_server"):
            return builder(Path(normalized_args["db-path"]))
        if self.server_module.endswith("docs_server"):
            return builder(Path(normalized_args["docs-dir"]))
        # Race MCP servers (race_github, race_calendar, race_travel) take no
        # path args — recorder + run_id arrive via mcp_servers.race_context
        # contextvars set by the runner before client.call().
        return builder(**normalized_args)

    def _start_http_server(self) -> None:
        port = self._find_open_port()
        args = ["-m", self.server_module, "--transport", "streamable-http", "--host", "127.0.0.1", "--port", str(port)]
        normalized_args = {key.replace("_", "-"): value for key, value in self.server_args.items()}
        if self.server_module.endswith("db_server"):
            args.extend(["--db-path", str(normalized_args["db-path"])])
        else:
            args.extend(["--docs-dir", str(normalized_args["docs-dir"])])
        env = os.environ.copy()
        src_path = str(self.project_root / "src")
        existing_pythonpath = env.get("PYTHONPATH", "")
        env["PYTHONPATH"] = src_path if not existing_pythonpath else os.pathsep.join([src_path, existing_pythonpath])
        self.http_stderr_file = tempfile.TemporaryFile(mode="w+", encoding="utf-8")
        self.http_process = subprocess.Popen(
            [sys.executable, *args],
            cwd=str(self.project_root),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=self.http_stderr_file,
            text=True,
        )
        self._wait_for_port(port)
        self.http_url = f"http://127.0.0.1:{port}/mcp"

    def _find_open_port(self) -> int:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("127.0.0.1", 0))
            sock.listen(1)
            return int(sock.getsockname()[1])

    def _wait_for_port(self, port: int, timeout_s: float = 5.0) -> None:
        deadline = time.time() + timeout_s
        while time.time() < deadline:
            if self.http_process is not None and self.http_process.poll() is not None:
                stderr_tail = self._collect_http_process_stderr()
                detail = f" Stderr: {stderr_tail}" if stderr_tail else ""
                raise RuntimeError(f"HTTP MCP server exited before becoming ready for {self.server_module}.{detail}")
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.2)
                try:
                    sock.connect(("127.0.0.1", port))
                    return
                except OSError:
                    time.sleep(0.05)
        stderr_tail = self._collect_http_process_stderr(terminate=True)
        detail = f" Stderr: {stderr_tail}" if stderr_tail else ""
        raise TimeoutError(f"Timed out waiting for HTTP MCP server on port {port}.{detail}")

    def _collect_http_process_stderr(self, terminate: bool = False) -> str:
        process = self.http_process
        if process is not None and process.poll() is None:
            if not terminate:
                return ""
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
        if self.http_stderr_file is None:
            return ""
        self.http_stderr_file.flush()
        self.http_stderr_file.seek(0)
        return self.http_stderr_file.read().strip()[-1200:]

    def _simulate_failure(self, tool: str) -> None:
        if self.failure_config.db_down and self.server_module.endswith("db_server"):
            raise RuntimeError(f"Simulated database outage while calling {tool}")
        if self.failure_config.docs_timeout and self.server_module.endswith("docs_server"):
            raise TimeoutError(f"Simulated docs timeout while calling {tool}")

    def _unwrap_structured(self, payload: Any) -> Any:
        if isinstance(payload, dict) and set(payload.keys()) == {"result"}:
            return payload["result"]
        if isinstance(payload, list) and payload:
            first = payload[0]
            text = getattr(first, "text", None)
            if isinstance(text, str):
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return text
        return payload

    def close(self) -> None:
        if self.http_process is not None and self.http_process.poll() is None:
            self.http_process.terminate()
            try:
                self.http_process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                self.http_process.kill()
                self.http_process.wait(timeout=2)
        if self.http_stderr_file is not None:
            self.http_stderr_file.close()
        self.http_process = None
        self.http_stderr_file = None
        self.http_url = None







