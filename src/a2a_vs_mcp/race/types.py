"""Phase 7 type substrate (RACE-01/02/05).

HardnessType (4 v1 enum values, locked per master design §Hardness vector).
HardnessProfile / TaskSpec / ScoreCard / RaceResult — dataclass-first with
to_dict() per project schemas.py convention.
ExecutionContext — TypedDict (mutable per-run state for hybrid binds).

Pure module: no I/O, no side effects, no imports from runners/harness/classifier.
Every downstream Phase 7 module imports from here. Pydantic is reserved for
boundary validators (api_schemas.py, race/failure.py loader); core types stay
@dataclass per project convention (mirrors race/schemas.py + schemas.py).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, TypedDict


# 3.10-safe StrEnum analog (mirrors race/failure.py:39-44 — pyproject pins >=3.10).
# RESEARCH.md Pitfall 6: do NOT use enum.StrEnum (3.11+ only).
class HardnessType(str, Enum):
    LONG_CHAIN = "long_chain"
    RATE_PRESSURE = "rate_pressure"
    SCHEMA_VARIANCE = "schema_variance"
    MULTI_SOURCE_SYNTHESIS = "multi_source"


@dataclass
class HardnessProfile:
    """Set of HardnessType tags for a task. Plan 11 hardness-coverage test
    inspects these against D-30 locked coverage matrix."""

    types: list[HardnessType]

    def to_dict(self) -> dict[str, Any]:
        return {"types": [t.value for t in self.types]}


@dataclass
class TaskSpec:
    """Locked task contract per master design §Task interface + RESEARCH §4.

    expected_shape maps result-key -> Python type (e.g. {"summary": str}).
    Serialized via type.__name__ since `type` objects are not JSON-native.
    """

    task_id: str
    prompt: str
    allowed_tools: list[str]
    expected_shape: dict[str, type]
    hardness_profile: HardnessProfile

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "prompt": self.prompt,
            "allowed_tools": list(self.allowed_tools),
            "expected_shape": {
                k: getattr(v, "__name__", str(v)) for k, v in self.expected_shape.items()
            },
            "hardness_profile": self.hardness_profile.to_dict(),
        }


@dataclass
class ScoreCard:
    """Per-(lane, task, run) outcome. Replay-symmetric: deserializable from a
    trace replay (no live state references). Used by harness aggregation +
    headline classifier in Plan 09/10."""

    success: bool
    ttff_ms: int
    recovered: bool
    wasted_tokens_before_detection: int | None
    failure_mode: str
    cost_usd: float
    latency_ms: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RaceResult:
    """Locked runner return value per D-20. Each lane runner constructs and
    returns one of these per run; harness collects N per (lane, task)."""

    run_id: str
    lane: str
    task_id: str
    hardness_profile: HardnessProfile
    score_card: ScoreCard
    trace_id: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "lane": self.lane,
            "task_id": self.task_id,
            "hardness_profile": self.hardness_profile.to_dict(),
            "score_card": self.score_card.to_dict(),
            "trace_id": self.trace_id,
        }


class ExecutionContext(TypedDict, total=False):
    """Mutable per-(run, lane) state visible to hybrid_plan.bind callables.

    Hybrid runner builds this incrementally as steps execute. Bind callables
    READ from it; they never mutate. Mutation is the runner's job.
    """

    task_input: dict[str, Any]
    subagent_outputs: dict[str, Any]
    tool_outputs: dict[str, Any]
    scratchpad: dict[str, Any]
