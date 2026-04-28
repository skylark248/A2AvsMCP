---
phase: 07-race-backend-lanes-harness-recovery
plan: 05
subsystem: race-metrics
tags: [metrics, wasted-tokens, characteristic-event, pure-functions, replay-symmetric]
requirements: [RACE-04, RACE-06]
dependency_graph:
  requires:
    - "race/types.py (Plan 02 — typed substrate, indirect via type hints)"
    - "Phase 6 trace event schema (llm_call carries tokens_in/tokens_out/t_call_start_ms; fault_injected/fault_observed carry t_inject_ms/t_observed_ms/turn_index)"
  provides:
    - "compute_wasted_tokens(events, fault_id, lane) -> int (D-40)"
    - "median_retries(events, fault_id, target) -> int (D-37 pure_mcp)"
    - "median_delegations(events, fault_id) -> int (D-37 pure_a2a)"
    - "median_switches(events, fault_id) -> int (D-37 hybrid)"
    - "median_turns_after_fault(events, fault_id) -> int (D-37 fallback)"
    - "aggregate_for_classifier(per_run_traces, task_id, lane, *, characteristic_tool) -> dict (consumed by failure_mode_classifier in Plan 04)"
  affects:
    - "Plan 09 runners — call compute_wasted_tokens at fault_observed time to populate wasted_tokens_before_detection"
    - "Plan 10 harness — calls aggregate_for_classifier after race_done; result passed as agg to failure_mode_classifier"
tech_stack:
  added: []
  patterns:
    - "Module-level pure functions (no class) per evidence.py idiom"
    - "Defensive .get(field, default) accessors — malformed events produce 0/-1 sentinels, not crashes (T-07-05-01 mitigation)"
    - "statistics.median for per-lane medians; cast to int per agg-shape contract"
key_files:
  created:
    - "src/a2a_vs_mcp/race/metrics.py (178 LOC)"
  modified: []
decisions:
  - "Honored D-40 wasted-tokens window semantics verbatim: inclusive bounds [t_inject_ms, t_observed_ms], lane-filtered, missing inject OR observe -> 0"
  - "Honored D-37 lane-specific characteristic counts: pure_mcp/median_retries (target-name-filtered), pure_a2a/median_delegations (message_type=='task_submit'), hybrid/median_switches (alternation count post-inject), fallback/median_turns_after_fault"
  - "Pure module: no I/O, no time imports, no random, no statefulness — replay-symmetric by construction"
  - "No import of classifier.py — preserves the one-way dependency (classifier and runners both import metrics; metrics imports neither)"
  - "Wrote plan body verbatim — no deviations from the locked algorithm in 07-RESEARCH §6 or 07-PATTERNS metrics section"
metrics:
  duration_minutes: ~3
  completed_date: "2026-04-28T16:48:31Z"
  tasks_completed: 1
  files_created: 1
  files_modified: 0
  loc_added: 178
---

# Phase 7 Plan 05: race/metrics.py — Per-Fault, Per-Lane Aggregation Summary

Pure-functional metrics reducer over recorded race trace events: wasted-tokens-before-detection per fault (D-40) plus per-lane characteristic-event counts (D-37) plus harness-side aggregator producing the `agg` dict for `failure_mode_classifier`.

## What Shipped

**`src/a2a_vs_mcp/race/metrics.py`** — 178 LOC, six module-level pure functions:

1. **`compute_wasted_tokens(events, fault_id, lane) -> int`** — D-40 verbatim: sum `tokens_in + tokens_out` across all `llm_call` events whose `t_call_start_ms` falls in the inclusive window `[t_inject_ms, t_observed_ms]` for the same `lane`. Returns `0` if either fault marker is absent.
2. **`median_retries(events, fault_id, target) -> int`** — pure_mcp characteristic count: `tool_call` events with `tool_name == target` AND `turn_index > fault_inject_turn`.
3. **`median_delegations(events, fault_id) -> int`** — pure_a2a characteristic count: `agent_msg` events with `message_type == "task_submit"` AND `turn_index > fault_inject_turn`.
4. **`median_switches(events, fault_id) -> int`** — hybrid characteristic count: alternation pairs in the `tool_call`/`agent_msg` event sequence after fault inject.
5. **`median_turns_after_fault(events, fault_id) -> int`** — D-37 fallback metric: `max(turn_index) - fault_inject_turn`, clamped at 0.
6. **`aggregate_for_classifier(per_run_traces, task_id, lane, *, characteristic_tool=None) -> dict[str, Any]`** — runs the four per-fault primitives across N traces, computes `recovery_rate` from `done.score_pass`, `mean_wasted_tokens`, `mean_ttff_ms`, lane-specific medians plus the universal `median_turns_after_fault`. For `pure_mcp` also forwards `characteristic_tool` from `failure_script[0].target` for headline phrasing.

Plus two private helpers (`_find_fault_injected`, `_find_fault_observed`) that locate fault markers in O(n) without raising on absence.

## Why It Matters

- **D-40 lock**: master design §Cost computation requires server-side wasted-tokens at `fault_observed` time. UI must NEVER recompute (D-41). The runner now has the helper to populate `wasted_tokens_before_detection` on the `fault_observed` event payload at emission (Plan 09 wires this).
- **D-37 lock**: per-lane characteristic phrases (`"retried {tool} {n} times"`, `"delegated {n} times"`, `"switched protocol path {n} times"`, fallback `"continued for {n} turns"`) need pre-aggregated counts at headline-render time. `failure_mode_classifier` (Plan 04) consumes them via the agg dict shape.
- **Replay symmetry (D-33)**: pure functions over event lists ⇒ same trace on disk ⇒ same metrics on every replay. Phase 9 HEAT-03 fixture will assert this.
- **Single-direction dependency**: classifier and runners both import from metrics; metrics imports nothing from race/. Cycle-free.

## Verification

- Smoke test from plan exits 0 — exercises wasted-tokens math (350 = 200+50+80+20, lane-filtered, time-windowed), retry counting (2), delegation counting (1), turn-fallback (3), aggregate shape (`recovery_rate=1.0`, `mean_wasted_tokens=350`, `median_retries=2`).
- All 6 grep gates pass:
  - `from __future__ import annotations` present (line 14, immediately after the module docstring)
  - 6 `def`s match the public surface (1 each per requirement)
  - 0 `class` definitions (module-level idiom)
  - 0 imports of `time` / `datetime.now` / `random` (pure)
  - 178 LOC ≥ 90 minimum
  - `python3 -c "from a2a_vs_mcp.race import metrics"` clean
- `pytest tests/race/ -x -q` exits 0 — **37/37 race tests still green**, no regression on Phase 6 or Plan 02/03 work.

## Deviations from Plan

None. Plan body code shipped verbatim. Acceptance criteria all satisfied.

## Threat-Model Review

| Threat ID    | Disposition | Implementation                                                                                       |
| ------------ | ----------- | ---------------------------------------------------------------------------------------------------- |
| T-07-05-01   | mitigate    | All event-field reads use `.get(field, default)` — missing fields produce 0/−1 sentinels, never crash |
| T-07-05-02   | accept      | Wasted-token counts are intended for public headline display per master design §Cost computation     |
| T-07-05-03   | accept      | Phase 6 RunWriter (D-05 single-writer arbiter) prevents trace interleaving upstream of metrics       |

## Threat Flags

None. No new network endpoints, auth paths, file access, or schema changes — pure reducer over an existing in-memory event list shape locked in Phase 6.

## Commits

| Task | Description                                                            | Hash    |
| ---- | ---------------------------------------------------------------------- | ------- |
| 1    | feat(07-05): add race/metrics.py — pure functions for wasted-tokens + characteristic counts | cef8365 |

## Self-Check: PASSED

- FOUND: src/a2a_vs_mcp/race/metrics.py (178 LOC, 6 pure functions, 0 classes)
- FOUND: commit cef8365 in `git log --oneline`
- FOUND: smoke-test exit 0 (wasted_tokens=350, median_retries=2, median_delegations=1, median_turns_after_fault=3, recovery_rate=1.0)
- FOUND: pytest tests/race/ -x -q ⇒ 37 passed
