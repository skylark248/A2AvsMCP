"""Race metrics — pure functions over event lists (D-37, D-40).

compute_wasted_tokens: sum tokens_in+tokens_out across llm_call events whose
t_call_start_ms falls in [t_inject_ms, t_observed_ms] for the same lane.
Master design §Cost computation, locked.

median_retries / median_delegations / median_switches / median_turns_after_fault:
per-lane characteristic-event counts derived at headline-render time per D-37.
Counts are NEVER stored; they're recomputed from the trace as needed.

aggregate_for_classifier: harness-side aggregator that produces the `agg` dict
consumed by failure_mode_classifier in classifier.py.
"""
from __future__ import annotations

import statistics
from typing import Any


def _find_fault_injected(events: list[dict], fault_id: str) -> dict | None:
    return next(
        (e for e in events
         if e.get("event_type") == "fault_injected" and e.get("fault_id") == fault_id),
        None,
    )


def _find_fault_observed(events: list[dict], fault_id: str) -> dict | None:
    return next(
        (e for e in events
         if e.get("event_type") == "fault_observed" and e.get("fault_id") == fault_id),
        None,
    )


def compute_wasted_tokens(events: list[dict], fault_id: str, lane: str) -> int:
    """D-40: sum tokens_in+tokens_out for llm_call events between inject and observe.

    Returns 0 if either fault_injected or fault_observed is missing
    (e.g., kept_going_without_noticing — no observation, no waste attributable).
    """
    fi = _find_fault_injected(events, fault_id)
    fo = _find_fault_observed(events, fault_id)
    if fi is None or fo is None:
        return 0
    t0 = fi.get("t_inject_ms", 0)
    t1 = fo.get("t_observed_ms", 0)
    total = 0
    for e in events:
        if e.get("event_type") != "llm_call":
            continue
        if e.get("lane") != lane:
            continue
        ts = e.get("t_call_start_ms", -1)
        if t0 <= ts <= t1:
            total += int(e.get("tokens_in", 0)) + int(e.get("tokens_out", 0))
    return total


def median_retries(events: list[dict], fault_id: str, target: str) -> int:
    """Per-run retry count = tool_call events with tool_name==target after fault_inject_turn."""
    fi = _find_fault_injected(events, fault_id)
    if fi is None:
        return 0
    inject_turn = fi.get("turn_index", -1)
    return sum(
        1 for e in events
        if e.get("event_type") == "tool_call"
        and e.get("tool_name") == target
        and e.get("turn_index", -1) > inject_turn
    )


def median_delegations(events: list[dict], fault_id: str) -> int:
    """Per-run delegation count = agent_msg events with message_type=='task_submit' after fault_inject_turn."""
    fi = _find_fault_injected(events, fault_id)
    if fi is None:
        return 0
    inject_turn = fi.get("turn_index", -1)
    return sum(
        1 for e in events
        if e.get("event_type") == "agent_msg"
        and e.get("message_type") == "task_submit"
        and e.get("turn_index", -1) > inject_turn
    )


def median_switches(events: list[dict], fault_id: str) -> int:
    """Per-run protocol-boundary crossings AFTER fault_inject_turn.

    A 'switch' = consecutive (tool_call -> agent_msg) or (agent_msg -> tool_call)
    transitions in event order. Counts pairs of adjacent qualifying events.
    """
    fi = _find_fault_injected(events, fault_id)
    if fi is None:
        return 0
    inject_turn = fi.get("turn_index", -1)
    qual = [
        e.get("event_type") for e in events
        if e.get("event_type") in ("tool_call", "agent_msg")
        and e.get("turn_index", -1) > inject_turn
    ]
    switches = 0
    for prev, cur in zip(qual, qual[1:]):
        if prev != cur:
            switches += 1
    return switches


def median_turns_after_fault(events: list[dict], fault_id: str) -> int:
    """Fallback metric per D-37: max(turn_index) - fault_inject_turn."""
    fi = _find_fault_injected(events, fault_id)
    if fi is None:
        return 0
    inject_turn = fi.get("turn_index", -1)
    max_turn = max((e.get("turn_index", -1) for e in events), default=inject_turn)
    return max(0, max_turn - inject_turn)


def aggregate_for_classifier(
    per_run_traces: list[list[dict]],
    task_id: str,
    lane: str,
    *,
    characteristic_tool: str | None = None,
) -> dict[str, Any]:
    """Aggregate across n runs into the `agg` dict consumed by failure_mode_classifier.

    Caller passes `characteristic_tool` from the task_config's failure_script[0].target
    (used only for pure_mcp's headline phrase per D-37).
    """
    n = len(per_run_traces)
    recovered_count = 0
    wasted: list[int] = []
    ttff: list[int] = []
    retries: list[int] = []
    delegations: list[int] = []
    switches: list[int] = []
    turns: list[int] = []
    for trace in per_run_traces:
        # Each trace owns at least one fault_id (failure_script may have multiples).
        fids = [e["fault_id"] for e in trace if e.get("event_type") == "fault_injected"]
        for fid in fids:
            wasted.append(compute_wasted_tokens(trace, fid, lane))
            fi = _find_fault_injected(trace, fid)
            fo = _find_fault_observed(trace, fid)
            if fi is not None and fo is not None:
                ttff.append(int(fo.get("t_observed_ms", 0)) - int(fi.get("t_inject_ms", 0)))
            if lane == "pure_mcp" and characteristic_tool:
                retries.append(median_retries(trace, fid, characteristic_tool))
            if lane == "pure_a2a":
                delegations.append(median_delegations(trace, fid))
            if lane == "hybrid":
                switches.append(median_switches(trace, fid))
            turns.append(median_turns_after_fault(trace, fid))
        # Recovery rate sourced from the run's done event.
        done = next((e for e in trace if e.get("event_type") == "done"), None)
        if done is not None and done.get("score_pass") is True:
            recovered_count += 1

    def _med(xs: list[int]) -> int:
        return int(statistics.median(xs)) if xs else 0

    agg: dict[str, Any] = {
        "recovery_rate": (recovered_count / n) if n else 0.0,
        "mean_wasted_tokens": (sum(wasted) / len(wasted)) if wasted else 0.0,
        "mean_ttff_ms": (sum(ttff) / len(ttff)) if ttff else 0.0,
        "median_turns_after_fault": _med(turns),
    }
    if lane == "pure_mcp":
        agg["median_retries"] = _med(retries)
        if characteristic_tool:
            agg["characteristic_tool"] = characteristic_tool
    elif lane == "pure_a2a":
        agg["median_delegations"] = _med(delegations)
    elif lane == "hybrid":
        agg["median_switches"] = _med(switches)
    return agg
