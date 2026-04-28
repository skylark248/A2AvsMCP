"""Contextvars-backed propagation of (recorder, run_id) into race MCP server tool fns.

Runner (Plan 09) calls set_mcp_tool_context(recorder=..., run_id=...) BEFORE
client.call(...) and resets after. Tool functions read via current_recorder() /
current_run_id() and pass them to race.mocks.<module>.<fn>(...).

Only valid for transport='in_process' — stdio runs in subprocess, contextvars
do not cross. Race lanes use in_process per RESEARCH §5.
"""
from __future__ import annotations

from contextvars import ContextVar
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..trace import TraceRecorder


@dataclass
class _ToolCtx:
    recorder: "TraceRecorder | None"
    run_id: str | None


MCP_TOOL_CONTEXT: ContextVar[_ToolCtx] = ContextVar(
    "race_mcp_tool_context", default=_ToolCtx(recorder=None, run_id=None),
)


def set_mcp_tool_context(*, recorder, run_id: str) -> object:
    """Returns a Token usable with MCP_TOOL_CONTEXT.reset(token)."""
    return MCP_TOOL_CONTEXT.set(_ToolCtx(recorder=recorder, run_id=run_id))


def current_recorder():
    return MCP_TOOL_CONTEXT.get().recorder


def current_run_id() -> str:
    rid = MCP_TOOL_CONTEXT.get().run_id
    if rid is None:
        raise RuntimeError(
            "race MCP tool invoked outside set_mcp_tool_context() — runner must wrap call sites"
        )
    return rid
