"""summarize_repo task registry (D-27, D-30, D-42).

TARGETS — failure_script.target -> mock callable.
BINDS   — hybrid_plan.bind key -> ExecutionContext resolver.
score() — per-task scorer using HaikuJudge (R1/R2/R3 = 3/3 pass).
"""
from __future__ import annotations
from typing import Any, Callable

from ...mocks import github as github_mock
from ...types import ExecutionContext, ScoreCard
from ...judges.haiku import HaikuJudge

# D-27 registries
TARGETS: dict[str, Callable[..., Any]] = {
    "github_api.get_repo_metadata": github_mock.get_repo_metadata,
    "github_api.list_files": github_mock.list_files,
    "github_api.read_file": github_mock.read_file,
}

BINDS: dict[str, Callable[[ExecutionContext], Any]] = {
    "from_subagent_output": lambda ctx: ctx.get("subagent_outputs", {}).get("summarizer"),
}

# D-42 rubric — locked verbatim from RESEARCH §3 lines 425-437.
RUBRIC = """You are a strict rubric scorer. Read the assistant output and answer YES/NO for each item.
RUBRIC:
  R1. Does the summary state the repository's purpose in one sentence?
  R2. Does the summary mention at least 3 distinct modules?
  R3. Does the summary identify the entry point (CLI, main, app)?
Output format (verbatim, machine-parseable):
R1: YES|NO
R2: YES|NO
R3: YES|NO
RATIONALE: <1 sentence>
"""


def score(result: dict[str, Any], trace: list[dict], judge: HaikuJudge | None) -> ScoreCard:
    if judge is None:
        return ScoreCard(success=False, ttff_ms=0, recovered=False,
                         wasted_tokens_before_detection=None, failure_mode="judge_failed",
                         cost_usd=0.0, latency_ms=0)
    summary = result.get("summary", "")
    verdict = judge.judge(rubric_system_prompt=RUBRIC, artifact_user_prompt=summary)
    text = verdict.rationale.upper()
    r1 = "R1: YES" in text
    r2 = "R2: YES" in text
    r3 = "R3: YES" in text
    passed = r1 and r2 and r3
    return ScoreCard(
        success=passed, ttff_ms=0, recovered=False,
        wasted_tokens_before_detection=None,
        failure_mode="success" if passed else "judge_failed",
        cost_usd=0.0, latency_ms=0,
    )
