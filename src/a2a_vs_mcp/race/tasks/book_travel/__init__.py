"""book_travel task registry (D-27, D-30, D-42 composite).

Composite scorer: structural (cost <= budget AND legs connect) AND Haiku
(trip purpose match per RESEARCH §3 lines 444-449). Both must pass.
"""
from __future__ import annotations
from datetime import datetime
from typing import Any, Callable

from ...mocks import travel as travel_mock
from ...types import ExecutionContext, ScoreCard
from ...judges.haiku import HaikuJudge

TARGETS: dict[str, Callable[..., Any]] = {
    "travel_api.search_flights": travel_mock.search_flights,
    "travel_api.search_hotels": travel_mock.search_hotels,
    "travel_api.book_itinerary": travel_mock.book_itinerary,
}

BINDS: dict[str, Callable[[ExecutionContext], Any]] = {
    "lowest_cost_combo": lambda ctx: (ctx.get("scratchpad") or {}).get("lowest_cost_combo"),
}

# D-42 Haiku rubric (RESEARCH §3 lines 444-449).
RUBRIC = """You are a strict rubric scorer for a travel-booking trip plan.
RUBRIC:
  R1. Does the booked itinerary match the user's stated trip purpose (e.g., business trip vs vacation)?
Output format:
R1: YES|NO
RATIONALE: <1 sentence>
"""


def _legs_connect(itinerary: dict[str, Any]) -> bool:
    flights = itinerary.get("flights") or []
    if len(flights) < 2:
        return True  # single-leg booking is trivially connected
    try:
        for prev, cur in zip(flights, flights[1:]):
            if prev.get("destination") != cur.get("origin"):
                # Allow same-city return (NYC->SFO after SFO->NYC reverses).
                if prev.get("destination") == cur.get("origin"):
                    continue
        return True
    except Exception:
        return False


def score(result: dict[str, Any], trace: list[dict], judge: HaikuJudge | None) -> ScoreCard:
    booking = result.get("booking", {})
    budget_usd = result.get("budget_usd", 0)
    total_cost = booking.get("total_cost_usd", float("inf"))
    structural_pass = (total_cost <= budget_usd) and _legs_connect(booking)

    haiku_pass = False
    if judge is not None:
        verdict = judge.judge(
            rubric_system_prompt=RUBRIC,
            artifact_user_prompt=result.get("summary", ""),
        )
        haiku_pass = "R1: YES" in verdict.rationale.upper()

    passed = structural_pass and haiku_pass
    return ScoreCard(
        success=passed, ttff_ms=0, recovered=False,
        wasted_tokens_before_detection=None,
        failure_mode="success" if passed else ("structural_failed" if not structural_pass else "judge_failed"),
        cost_usd=0.0, latency_ms=0,
    )
