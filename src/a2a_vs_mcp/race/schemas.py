"""Wire-format dataclasses for /api/race/ws (TRC-04, D-06).

Every event carries lane + turn_index per D-15/D-17. Plain @dataclass + to_dict()
mirrors src/a2a_vs_mcp/schemas.py:30-92 idiom (Pydantic is reserved for api_schemas.py).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar

# The 8 wire event types per CONTEXT.md D-06. WS schema test (Plan 08) asserts each appears.
WIRE_EVENT_TYPES: frozenset[str] = frozenset({
    "tick",
    "tool_call",
    "agent_msg",
    "fault_injected",
    "fault_observed",
    "done",
    "error",
    "race_done",
})


@dataclass
class TickEvent:
    lane: str
    turn_index: int
    task_id: str
    t_ms: int
    event_type: ClassVar[str] = "tick"
    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, **asdict(self)}


@dataclass
class ToolCallEvent:
    lane: str
    turn_index: int
    tool_name: str
    status: str  # "ok" | "error"
    t_call_ms: int
    error_kind: str | None = None
    event_type: ClassVar[str] = "tool_call"
    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, **asdict(self)}


@dataclass
class AgentMsgEvent:
    lane: str
    turn_index: int
    sender: str
    recipient: str
    content: str
    t_ms: int
    event_type: ClassVar[str] = "agent_msg"
    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, **asdict(self)}


@dataclass
class FaultInjectedEvent:
    lane: str
    turn_index: int
    fault_id: str
    fault_kind: str  # FaultKind.value (Plan 04)
    target: str
    t_inject_ms: int
    event_type: ClassVar[str] = "fault_injected"
    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, **asdict(self)}


@dataclass
class FaultObservedEvent:
    lane: str
    turn_index: int
    fault_id: str
    fault_kind: str
    target: str
    t_observed_ms: int
    evidence: str
    wasted_tokens_before_detection: int
    event_type: ClassVar[str] = "fault_observed"
    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, **asdict(self)}


@dataclass
class DoneEvent:
    lane: str
    turn_index: int
    task_id: str
    outcome: str  # "success" | "failure" | "timeout"
    event_type: ClassVar[str] = "done"
    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, **asdict(self)}


@dataclass
class ErrorEvent:
    lane: str
    turn_index: int
    error_kind: str
    message: str
    event_type: ClassVar[str] = "error"
    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, **asdict(self)}


@dataclass
class RaceDoneEvent:
    run_id: str
    turn_index: int  # max turn_index across lanes; D-17 says every event carries one
    outcome_per_lane: dict[str, str] = field(default_factory=dict)
    event_type: ClassVar[str] = "race_done"
    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, **asdict(self)}
