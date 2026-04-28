"""Race judges — LLM-based rubric scorers (D-42).

Exports HaikuJudge for summarize_repo + book_travel scorers.
negotiate_meeting is structural-only per D-43 and never imports from here.
"""
from __future__ import annotations

from .haiku import HaikuJudge, JudgeVerdict, HAIKU_MODEL, TEMPERATURE

__all__ = ["HaikuJudge", "JudgeVerdict", "HAIKU_MODEL", "TEMPERATURE"]
