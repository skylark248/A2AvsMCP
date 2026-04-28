"""TaskConfig pydantic loader (D-28).

Cross-validates each failure_script.target against the task's TARGETS registry
and each hybrid_plan.steps[].bind against BINDS. Typo = ValidationError at
import time (RESEARCH §7 + Phase 6 D-12 inheritance).

YAML loaded via yaml.safe_load (NEVER yaml.load — prevents arbitrary Python
object construction).
"""
from __future__ import annotations

from importlib import resources
from typing import Any, Callable, Literal

import yaml
from pydantic import BaseModel, ConfigDict, ValidationError, field_validator

from ..failure import FaultKind
from ..types import HardnessType


OnFault = Literal["retry_once", "delegate", "abort", "continue"]


class HybridStep(BaseModel):
    model_config = ConfigDict(extra="forbid")
    kind: Literal["tool", "delegate"]
    tool: str | None = None
    agent: str | None = None
    goal: str | None = None
    bind: str | None = None
    on_fault: OnFault | None = None


class HybridPlan(BaseModel):
    model_config = ConfigDict(extra="forbid")
    steps: list[HybridStep]


class FailureScriptYAMLEntry(BaseModel):
    model_config = ConfigDict(extra="allow")  # free-form per-kind extras allowed
    kind: FaultKind
    target: str
    after_calls: int = 0
    duration_calls: int = 1


class TaskConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    task_id: str
    hardness_profile: list[HardnessType]
    failure_script: list[FailureScriptYAMLEntry]
    hybrid_plan: HybridPlan

    @field_validator("hardness_profile")
    @classmethod
    def _profile_nonempty(cls, v: list[HardnessType]) -> list[HardnessType]:
        if not v:
            raise ValueError("hardness_profile must list at least one HardnessType")
        return v


def load_task_config(task_id: str) -> tuple[TaskConfig, dict[str, Callable], dict[str, Callable]]:
    """Load + validate task_config.yaml. Cross-validates target + bind identifiers
    against the task module's TARGETS and BINDS registries.

    Raises pydantic.ValidationError on:
      - unknown FaultKind / HardnessType / OnFault enum value
      - unknown failure_script.target (not in TARGETS keys)
      - unknown hybrid_plan.steps[].bind (not in BINDS keys)
    """
    pkg = f"a2a_vs_mcp.race.tasks.{task_id}"
    yaml_text = resources.files(pkg).joinpath("task_config.yaml").read_text()
    raw = yaml.safe_load(yaml_text)
    cfg = TaskConfig.model_validate(raw)

    mod = __import__(pkg, fromlist=["TARGETS", "BINDS"])
    targets: dict[str, Callable] = mod.TARGETS
    binds: dict[str, Callable] = mod.BINDS

    for entry in cfg.failure_script:
        if entry.target not in targets:
            raise ValueError(
                f"Unknown failure_script target '{entry.target}' in {task_id}/task_config.yaml; "
                f"known TARGETS: {sorted(targets.keys())}"
            )
    for step in cfg.hybrid_plan.steps:
        if step.bind is not None and step.bind not in binds:
            raise ValueError(
                f"Unknown hybrid_plan bind '{step.bind}' in {task_id}/task_config.yaml; "
                f"known BINDS: {sorted(binds.keys())}"
            )
    return cfg, targets, binds
