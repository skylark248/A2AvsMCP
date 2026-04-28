---
phase: 07-race-backend-lanes-harness-recovery
plan: 06
subsystem: race-judges
tags: [llm-judge, anthropic, haiku, prompt-cache, rubric, D-42]
requirements: []
dependency_graph:
  requires:
    - "anthropic>=0.40 direct dep (Plan 01 added to pyproject.toml)"
    - "ANTHROPIC_API_KEY env var (per Plan 01 user_setup contract)"
  provides:
    - "HaikuJudge — stateless Anthropic Haiku 4.5 judge wrapper"
    - "JudgeVerdict — typed verdict dataclass (passed, score, rubric_total, rationale, tokens_in, tokens_out)"
    - "HAIKU_MODEL constant: claude-haiku-4-5"
    - "TEMPERATURE constant: 0.0"
  affects:
    - "Plan 08 task scorer registries — summarize_repo + book_travel scorers import HaikuJudge"
    - "Plan 09 runners — invoke task scorers post-run; scorers wrap HaikuJudge calls"
tech_stack:
  added:
    - "anthropic SDK (declared in pyproject.toml from Plan 01; first usage in this plan)"
  patterns:
    - "System-prompt-only prompt caching (cache_control type=ephemeral) — rubric is static across calls"
    - "Verdict parsing deferred to caller — HaikuJudge.judge() returns raw structured response, scorer module decodes"
    - "TYPE_CHECKING import guard for TraceRecorder to avoid runtime import cycles"
key_files:
  created:
    - "src/a2a_vs_mcp/race/judges/__init__.py (re-exports)"
    - "src/a2a_vs_mcp/race/judges/haiku.py (108 LOC — HaikuJudge + JudgeVerdict + module constants)"
  modified: []
key_decisions:
  - "D-42: Haiku judge in race/judges/haiku.py — independent of classifier (NOT same module)"
  - "Determinism: temperature=0.0; Anthropic does not support seed param (verified against SDK source); ~1% token-level variance from FP rounding disclosed in master design §Cross-model T4"
  - "Caching: rubric system prompt is cache_control=ephemeral; small rubrics (<2048 tokens) won't actually cache, callers may pad for cost discipline"
  - "Mitigation for stochasticity: rubrics count items (structural), not freeform prose — robust to ±1 token variance"
patterns_established:
  - "JudgeVerdict dataclass shape: (passed: bool, score: int, rubric_total: int, rationale: str, tokens_in: int, tokens_out: int)"
  - "Stateless judge contract: each judge() call self-contained; no internal state between calls"
requirements_completed: []  # RACE requirements close in Plan 09 (runners) + Plan 10 (harness)
duration: ~127s (agent quota-killed before SUMMARY commit; orchestrator authored post-quota-restore)
completed: 2026-04-28T22:18+05:30
---

# Plan 07-06: race/judges/haiku.py Summary

**Anthropic Haiku 4.5 judge wrapper shipped: HaikuJudge stateless class + JudgeVerdict dataclass; merge commit a82ed2e brought worktree commits 51c00d5 + 3e0fe43 to master. 37/37 race tests still green.**

## Performance

- **Duration:** ~127s agent run; terminated by Anthropic quota at 2:30am window before SUMMARY commit
- **Tasks:** 2/2 (package init + haiku module) committed in worktree
- **Files modified:** 2 created (judges/__init__.py + judges/haiku.py)

## Accomplishments

- `HaikuJudge` is a stateless wrapper around `anthropic.Anthropic.messages.create()` with model = `claude-haiku-4-5`, temperature = 0.0.
- `JudgeVerdict` standardizes the shape returned by every judge call: pass/fail flag, integer score, rubric total, rationale string, and per-call token counts (for downstream cost telemetry in Plan 10 harness).
- System prompt is marked `cache_control=ephemeral` — Haiku 4.5's 2,048-token cache minimum is documented in module docstring with a note that small rubrics fall below threshold.
- TYPE_CHECKING import shields race/trace.TraceRecorder so runtime imports don't cycle.
- D-43 carve-out documented: negotiate_meeting is structural-only and never imports from this module.

## Recovery Note

Agent ran successfully in worktree, committed both code commits (51c00d5 + 3e0fe43), but hit Anthropic free-tier quota at "2:30am Asia/Calcutta" before the SUMMARY-commit step in execute-plan.md. Orchestrator post-quota-restore: merged worktree branch with `--no-ff` (a82ed2e), force-removed the locked worktree, ran race test suite (37/37 green), and authored this SUMMARY.

## Verification

- [x] `from a2a_vs_mcp.race.judges import HaikuJudge, JudgeVerdict, HAIKU_MODEL, TEMPERATURE` succeeds
- [x] `HAIKU_MODEL == "claude-haiku-4-5"` and `TEMPERATURE == 0.0` (verified via repl)
- [x] All 37 Phase 6 + Phase 7 race tests still green after merge
- [x] D-42 honored: judge module lives at race/judges/haiku.py, NOT inside classifier.py

## Tail-end Sequencing

Plan 08 task scorer registries (summarize_repo + book_travel) will import `HaikuJudge` and decode raw JSON verdicts into structured pass/fail. Plan 11 will add `tests/race/test_haiku_judge.py` to exercise the wrapper with mocked Anthropic responses.
