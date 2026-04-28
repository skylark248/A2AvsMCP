from __future__ import annotations

"""Recovery state machine + headline classifier (D-31, D-33, D-35, D-36, D-37).

This module IS the recovery brain of the race demo. Two responsibilities:

1. ``Detector`` — stateful K=3-turn observer per fault. Runners (Plan 09) and
   the replay path (Phase 9 HEAT-03) instantiate the SAME class over the SAME
   event stream, which is how D-33 replay symmetry is guaranteed by construction.
   See master design §Per-fault state machine for the WAITING / AWAITING_OBSERVATION
   / OBSERVED transitions and §Recovery detection for terminal-tag rules (D-34).

2. ``failure_mode_classifier`` — pure deterministic reduction of per-run tags +
   aggregates into one of six locked headline templates (D-35) used by the
   harness (Plan 10) for per-lane banner clauses.

D-36 contract: ``_ACK_FAULT_REGEX``, ``_NEGATION_TOKENS``, ``_NEGATION_FAULT_TOKENS``,
``_SENTENCE_SPLIT`` are compiled ONCE at module load. Sentence-split + negation guard
implements ``agent_msg_acknowledging_fault`` per master design §Recovery detection.

NO I/O, NO network, NO randomness, NO LLM calls in this module. Pure functions over
recorded events and aggregates.
"""

from dataclasses import dataclass
from enum import Enum
import re
from typing import Any, Literal


K_DEFAULT: int = 3


class DetectorState(str, Enum):
    """Per-fault detection state. WAITING is reserved for "no fault scripted yet";
    runners construct a Detector only after seeing fault_injected, so the dataclass
    default is AWAITING_OBSERVATION (master design + RESEARCH §6 line 811)."""

    WAITING = "waiting"
    AWAITING_OBSERVATION = "awaiting_observation"
    OBSERVED = "observed"


# D-36: regex compiled ONCE at module load (locked verbatim from master design
# §Recovery detection; mirrors RESEARCH §6 lines 774-787).
_ACK_FAULT_REGEX = re.compile(
    r"\b(error|errors|errored|fail|failed|failing|failure|429|5\d\d|timeout|timed.out|"
    r"retry|retrying|retried|unable|cannot|couldn[' ]?t|did[' ]?not|didn[' ]?t|didnt|"
    r"stale|invalid|malformed|truncat\w+|partial|rate.?limit\w*|unauthorized|forbidden|"
    r"missing.\w*field|unexpected|unparse\w+)\b",
    re.IGNORECASE,
)
_NEGATION_TOKENS = re.compile(
    r"\b(no|not|without|never|isn[' ]?t|wasn[' ]?t|aren[' ]?t)\b", re.IGNORECASE,
)
_NEGATION_FAULT_TOKENS = re.compile(
    r"\b(error|fail|issue|problem|fault|429|5\d\d|timeout|retry)\b", re.IGNORECASE,
)
_SENTENCE_SPLIT = re.compile(r"[.!?]")


def is_acknowledging_fault(text: str) -> bool:
    """D-36: regex with negation guard. Sentence boundary = [.!?] or end-of-message.

    Negation guard: if a sentence matches ``_ACK_FAULT_REGEX`` BUT also contains
    BOTH a ``_NEGATION_TOKENS`` match AND a ``_NEGATION_FAULT_TOKENS`` match, the
    sentence is dropped (treated as a non-acknowledgment). This handles phrasings
    like "no errors here" or "without any timeout" while accepting the
    Reviewer Concern #1 false-negative on "I cannot retry this 429" — the FN
    target is monitored alongside FP via the Plan 11 50-sample regex corpus.
    """
    sentences = _SENTENCE_SPLIT.split(text) if text else []
    for sent in sentences:
        if not _ACK_FAULT_REGEX.search(sent):
            continue
        if _NEGATION_TOKENS.search(sent) and _NEGATION_FAULT_TOKENS.search(sent):
            continue
        return True
    return False


@dataclass
class Detector:
    """Stateful per-fault state machine (D-31).

    Runner instantiates one Detector per fault_injected event and feeds every
    subsequent event into ``consume()``. When ``consume()`` returns True (state
    flipped to OBSERVED), the runner emits a fault_observed trace event. At
    ``done`` arrival, the runner calls ``finalize_at_done(score_pass)`` to mint
    the terminal recovery tag. At ``race_done`` without a ``done`` for this lane,
    the runner calls ``finalize_at_race_done_no_done()`` (D-34: indeterminate).
    """

    fault_id: str
    fault_kind: str
    target: str
    fault_inject_turn: int
    K: int = K_DEFAULT
    state: DetectorState = DetectorState.AWAITING_OBSERVATION
    t_observed_ms: int | None = None
    evidence_kind: str | None = None  # "tool_error" | "agent_msg" | "retry"

    def consume(self, event: dict) -> bool:
        """Feed one event. Returns True iff state flipped to OBSERVED on this call.

        D-32 logic (RESEARCH §6 lines 815-832):
        - Out-of-window check: ``cur_turn - fault_inject_turn > K`` → no observation.
        - Three observation paths, in priority order:
          1. ``tool_call`` with ``status == "error"`` → evidence_kind = "tool_error"
          2. ``tool_call`` with ``tool_name == target`` AND ``turn > fault_inject_turn``
             → evidence_kind = "retry"
          3. ``agent_msg`` whose content passes ``is_acknowledging_fault``
             → evidence_kind = "agent_msg"
        """
        if self.state != DetectorState.AWAITING_OBSERVATION:
            return False
        cur_turn = event.get("turn_index", -1)
        if cur_turn - self.fault_inject_turn > self.K:
            return False  # window closed; observation impossible
        et = event.get("event_type")
        if et == "tool_call" and event.get("status") == "error":
            return self._observe(event, "tool_error")
        if (
            et == "tool_call"
            and event.get("tool_name") == self.target
            and cur_turn > self.fault_inject_turn
        ):
            return self._observe(event, "retry")
        if et == "agent_msg":
            content = event.get("content", "")
            if is_acknowledging_fault(content):
                return self._observe(event, "agent_msg")
        return False

    def _observe(self, event: dict, evidence_kind: str) -> bool:
        self.state = DetectorState.OBSERVED
        self.t_observed_ms = event.get("t_ms") or event.get("t_call_ms") or 0
        self.evidence_kind = evidence_kind
        return True

    def finalize_at_done(self, score_pass: bool) -> str:
        """Terminal tag at ``done`` event arrival (D-34 + master design §Per-fault
        state machine). Five tags: recovered | gave_up | kept_going_without_noticing
        | kept_going_to_failure | indeterminate."""
        if self.state == DetectorState.OBSERVED and score_pass:
            return "recovered"
        if self.state == DetectorState.OBSERVED and not score_pass:
            return "gave_up"
        if self.state == DetectorState.AWAITING_OBSERVATION and score_pass:
            return "kept_going_without_noticing"
        if self.state == DetectorState.AWAITING_OBSERVATION and not score_pass:
            return "kept_going_to_failure"
        return "indeterminate"

    def finalize_at_race_done_no_done(self) -> str:
        """D-34: race_done arrived without a ``done`` for this lane → indeterminate."""
        return "indeterminate"


# ---------------------------------------------------------------------------
# Headline classifier (D-35, D-37) — pure reduction over per-run tags + agg.
# ---------------------------------------------------------------------------

LANE = Literal["pure_mcp", "pure_a2a", "hybrid"]


def failure_mode_classifier(
    lane: LANE,
    task_id: str,
    per_run_tags: list[str],
    agg: dict[str, Any],
) -> str:
    """6 templates, locked verbatim from master design §failure_mode_classifier.

    Dispatcher over the dominant tag across ``per_run_tags`` (D-35). The asterisk
    pairs ``*...*`` are markdown italics consumed by the banner-clause renderer
    in Plan 10 (harness). NEVER calls live time, randomness, or LLM — pure
    function over inputs to satisfy D-33 replay symmetry.
    """
    n = len(per_run_tags)
    if n == 0 or all(t == "lane_failed" for t in per_run_tags):
        return _template_lane_failed(lane, task_id, agg)
    dominant = _dominant_tag(per_run_tags)
    fault_summary = _fault_summary(task_id)
    if dominant == "recovered":
        return (
            f"{lane} *recovered {agg['recovery_rate']*n:.0f}/{n} times* "
            f"after {fault_summary}; avg {agg['mean_wasted_tokens']:.0f} wasted tokens."
        )
    if dominant == "gave_up":
        return (
            f"{lane} noticed the {fault_summary} but "
            f"*gave up at turn {agg.get('median_give_up_turn', 0)}*; "
            f"recovery {agg['recovery_rate']*100:.0f}%."
        )
    if dominant == "kept_going_without_noticing":
        phrase = _characteristic_event_phrase(lane, agg)
        return (
            f"{lane} *{phrase}* after {fault_summary}; "
            f"recovery {agg['recovery_rate']*100:.0f}%."
        )
    if dominant == "kept_going_to_failure":
        return (
            f"{lane} *kept going past {fault_summary}* and failed the score gate; "
            f"recovery 0%."
        )
    if dominant == "indeterminate":
        ind = sum(1 for t in per_run_tags if t == "indeterminate")
        return f"{lane} produced *{ind}/{n} indeterminate runs* on this task — disclosed."
    raise ValueError(f"Unknown dominant tag: {dominant}")


def _template_lane_failed(lane: str, task_id: str, agg: dict[str, Any]) -> str:
    """Sixth template (D-35): lane infra failure — judge timeout, broker error, etc."""
    reason = agg.get("lane_failed_reason", "infra error")
    return f"{lane} could not complete {task_id}: {reason}."


def _dominant_tag(tags: list[str]) -> str:
    """Mode of tags; ties broken by precedence:
    recovered > gave_up > kept_going_without_noticing > kept_going_to_failure > indeterminate.
    """
    PRECEDENCE = [
        "recovered",
        "gave_up",
        "kept_going_without_noticing",
        "kept_going_to_failure",
        "indeterminate",
    ]
    counts = {t: tags.count(t) for t in PRECEDENCE}
    max_count = max(counts.values()) if counts else 0
    for t in PRECEDENCE:
        if counts.get(t, 0) == max_count:
            return t
    return "indeterminate"


def _fault_summary(task_id: str) -> str:
    """Per-task short clause used in headlines (master design §failure_mode_classifier)."""
    return {
        "summarize_repo": "rate-limit + schema drift on the GitHub mock",
        "negotiate_meeting": "schema drift on calendar windows",
        "book_travel": "partial commit on booking + rate-limit on hotel search",
    }.get(task_id, f"fault on {task_id}")


def _characteristic_event_phrase(lane: str, agg: dict[str, Any]) -> str:
    """D-37 lookup. Counts derived from trace at headline-render time, NOT stored."""
    if lane == "pure_mcp":
        n_retries = agg.get("median_retries")
        tool = agg.get("characteristic_tool", "the_tool")
        if n_retries is not None:
            return f"retried {tool} {n_retries} times"
    elif lane == "pure_a2a":
        n_delegations = agg.get("median_delegations")
        if n_delegations is not None:
            return f"delegated {n_delegations} times"
    elif lane == "hybrid":
        n_switches = agg.get("median_switches")
        if n_switches is not None:
            return f"switched protocol path {n_switches} times"
    n_turns = agg.get("median_turns_after_fault", 0)
    return f"continued for {n_turns} turns"
