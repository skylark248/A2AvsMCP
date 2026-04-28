"""Haiku judge for race scorers (D-42).

Used by:
  - race/tasks/summarize_repo/__init__.py — judges purpose, >=3 modules, entry point (3/3 = success).
  - race/tasks/book_travel/__init__.py    — judges trip purpose match (composite with structural).

NOT used by negotiate_meeting (D-43 — structural-only).

Determinism: temperature=0. Anthropic does NOT support a `seed` parameter
(verified against anthropics/anthropic-sdk-python source); seed=42 in master
design §Harness defaults is documentation/methodology only. Master design
§Cross-model T4 already discloses LLM stochasticity at temp=0 (~1% token-level
variance from FP rounding across GPU shards). Mitigation: rubrics count items
(structural), not freeform prose — robust to ±1 token variance.

Prompt caching: rubric system prompt is static across all calls in a phase, so
mark with cache_control type=ephemeral. Haiku 4.5 minimum cache size = 2,048
tokens; small rubrics (~400 tokens for summarize_repo) fall below threshold and
won't actually cache — still works correctly, just no savings. Pad rubrics to
>=2,048 tokens with stable preamble for cost discipline (caller's job).
"""
from __future__ import annotations

from dataclasses import dataclass
import os
from typing import TYPE_CHECKING

import anthropic

if TYPE_CHECKING:
    from ...trace import TraceRecorder


HAIKU_MODEL: str = "claude-haiku-4-5"
TEMPERATURE: float = 0.0


@dataclass
class JudgeVerdict:
    """Structured verdict returned by HaikuJudge.judge()."""
    passed: bool
    score: int
    rubric_total: int
    rationale: str
    tokens_in: int
    tokens_out: int


class HaikuJudge:
    """Stateless Anthropic Haiku 4.5 judge.

    Caller supplies a system_prompt (the rubric) and a user_prompt (the
    artifact to evaluate). The verdict's `passed`/`score`/`rubric_total`
    fields are filled by the CALLER's rubric parser; this class returns the
    raw model output as `rationale` plus token accounting.
    """

    def __init__(self, recorder: "TraceRecorder | None" = None) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set; race judges require it. "
                "Set on demo machine; tests should mock anthropic.Anthropic."
            )
        self._client = anthropic.Anthropic(api_key=api_key)
        self._recorder = recorder

    def judge(
        self,
        *,
        rubric_system_prompt: str,
        artifact_user_prompt: str,
        max_tokens: int = 512,
    ) -> JudgeVerdict:
        """Run the rubric against the artifact. Returns JudgeVerdict (passed/score
        come back at 0/0; caller parses `rationale` per its rubric format)."""
        msg = self._client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=max_tokens,
            temperature=TEMPERATURE,
            system=[
                {
                    "type": "text",
                    "text": rubric_system_prompt,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": artifact_user_prompt}],
        )
        text = msg.content[0].text if msg.content else ""
        tokens_in = msg.usage.input_tokens
        tokens_out = msg.usage.output_tokens
        if self._recorder is not None:
            self._recorder.record(
                "llm_call",
                model=HAIKU_MODEL,
                role="judge",
                tokens_in=tokens_in,
                tokens_out=tokens_out,
            )
        return JudgeVerdict(
            passed=False,
            score=0,
            rubric_total=0,
            rationale=text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )
