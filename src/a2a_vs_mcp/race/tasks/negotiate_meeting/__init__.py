"""negotiate_meeting task registry (D-27, D-30, D-43 — structural-only).

D-43: this task does NOT import any LLM judge. score() returns success
based on a structural check only:
  - proposed time fits inside ALL 3 owners' free_busy windows.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Callable

from ...mocks import calendar as calendar_mock
from ...types import ExecutionContext, ScoreCard

TARGETS: dict[str, Callable[..., Any]] = {
    "calendar_api.get_free_busy": calendar_mock.get_free_busy,
    "calendar_api.propose_time": calendar_mock.propose_time,
}

BINDS: dict[str, Callable[[ExecutionContext], Any]] = {
    "combined_owners": lambda ctx: list((ctx.get("tool_outputs") or {}).get("free_busy_owners", [])),
}


def _within(window: dict[str, str], start: datetime, end: datetime) -> bool:
    w_start = datetime.fromisoformat(window["start"])
    w_end = datetime.fromisoformat(window["end"])
    return w_start <= start and end <= w_end


def score(result: dict[str, Any], trace: list[dict], judge: Any = None) -> ScoreCard:
    """Structural pass: proposed time fits in all 3 owners' free windows."""
    proposal = result.get("proposed_time") or result.get("proposal")
    free_busy_by_owner = result.get("free_busy_by_owner", {})
    if not proposal or not free_busy_by_owner:
        return ScoreCard(success=False, ttff_ms=0, recovered=False,
                         wasted_tokens_before_detection=None, failure_mode="structural_failed",
                         cost_usd=0.0, latency_ms=0)
    try:
        prop_start = datetime.fromisoformat(proposal["start"])
        prop_end = datetime.fromisoformat(proposal["end"])
    except (KeyError, ValueError):
        return ScoreCard(success=False, ttff_ms=0, recovered=False,
                         wasted_tokens_before_detection=None, failure_mode="structural_failed",
                         cost_usd=0.0, latency_ms=0)
    for owner, fb in free_busy_by_owner.items():
        if not any(w.get("status") == "free" and _within(w, prop_start, prop_end) for w in fb.get("free_busy", [])):
            return ScoreCard(success=False, ttff_ms=0, recovered=False,
                             wasted_tokens_before_detection=None, failure_mode="structural_failed",
                             cost_usd=0.0, latency_ms=0)
    return ScoreCard(success=True, ttff_ms=0, recovered=False,
                     wasted_tokens_before_detection=None, failure_mode="success",
                     cost_usd=0.0, latency_ms=0)
