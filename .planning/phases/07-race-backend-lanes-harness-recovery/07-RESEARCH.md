# Phase 7: Race Backend — Lanes, Harness, Recovery State Machine - Research

**Researched:** 2026-04-28
**Domain:** Multi-lane race runner orchestration, Anthropic SDK concurrency, recovery state machine, Pydantic-validated callable registries
**Confidence:** HIGH (Phase 6 substrate fully read; transport contracts read; master design read in full; rate-limit + seed behavior verified via Anthropic docs)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-19** Fresh race runners. New `race/runners/{pure_mcp,pure_a2a,hybrid}.py` files. v1 agents (`agents/single_agent.py`, `specialists.py`, `hybrid_specialists.py`, `triage.py`) are NOT subclassed and NOT touched. Race lanes are independent of v1 demo evolution; SupportTicket/AgentResult abstractions do not leak into race.
- **D-20** Runner contract: `run(task_spec: TaskSpec, run_id: str, recorder: TraceRecorder, failure_script: list[FaultEntry]) -> RaceResult`. Each runner constructs its own `TraceRecorder` via the Phase 6 `(run_id, lane)` constructor. The harness threads `run_id` in.
- **D-21** Hybrid runner is the **pre-scripted plan executor** (v1 contract). Interprets `task_config.hybrid_plan.steps` linearly, branching on `on_fault` enum (`retry_once | delegate | abort | continue`). Agent-driven decision policy is v2+.
- **D-22** Mocks live behind real MCP + A2A transport. `race/mocks/{github,calendar,travel}.py` are pure Python adapter modules (single fault chokepoint via `inject_fault()`).
- **D-23** Three new MCP servers `mcp_servers/race_{github,calendar,travel}.py` wrap the mocks. `pure_mcp` and `hybrid` lanes call them via the existing `MCPClient`. Reuse, do not duplicate.
- **D-24** A2A side: register fixture-backed agent handlers on the existing `A2ABroker`. `pure_a2a` and `hybrid` lanes route via real `broker.send_task` (note: actual method name in `a2a/broker.py:61` is `send_task`, not `send_message` — CONTEXT.md typo). Reuse, do not duplicate.
- **D-25** `inject_fault()` (Phase 6, `race/failure.py`) is the only mutation point. CI grep from Phase 6 D-13 still applies; extends to `mcp_servers/race_*.py` and A2A handlers.
- **D-26** YAMLs at `src/a2a_vs_mcp/race/tasks/<task_id>/task_config.yaml` — importable via `importlib.resources`.
- **D-27** Each task ships `src/a2a_vs_mcp/race/tasks/<task_id>/__init__.py` registering `TARGETS: dict[str, Callable]` and `BINDS: dict[str, Callable[[ExecutionContext], Any]]`.
- **D-28** Pydantic validators reject unknown `target` and `bind` identifiers at startup. Same pattern as Phase 6 D-12.
- **D-29** `failure_script[].kind` enum is the Phase 6 `FaultKind` (5 values, locked). `hybrid_plan.steps[].on_fault` enum locked at 4 values: `retry_once | delegate | abort | continue`.
- **D-30** Hardness coverage check (locked): LONG_CHAIN ∈ {summarize_repo, book_travel}, RATE_PRESSURE ∈ {summarize_repo, book_travel}, SCHEMA_VARIANCE ∈ {summarize_repo, negotiate_meeting}, MULTI_SOURCE_SYNTHESIS ∈ {negotiate_meeting, book_travel}.
- **D-31** `race/classifier.py` owns the K=3 detection algorithm. Classifier exposes stateful `Detector(K: int = 3)`.
- **D-32** Each runner instantiates one `Detector` per `fault_injected` event. Feeds subsequent events; on OBSERVED transition calls `recorder.record('fault_observed', ...)`.
- **D-33** Replay symmetry guaranteed by construction: replay re-instantiates same `Detector` over recorded event stream.
- **D-34** Recovery tag emission at `done` via terminal-state rules. `indeterminate` = `race_done` arrives with no `done` and detector still WAITING/AWAITING_OBSERVATION.
- **D-35** `failure_mode_classifier(lane, task_id, per_run_tags, agg) -> str` lives in `race/classifier.py`. 6 templates locked verbatim from master design.
- **D-36** `agent_msg_acknowledging_fault` regex with negation guard locked verbatim. Compiled once at module load. Sentence-split by `[.!?]` or end-of-message. False-positive target <10%.
- **D-37** `characteristic_event` lookup table per lane: pure_mcp → median_retries, pure_a2a → median_delegations, hybrid → median_switches. Fallback to `median_turns_after_fault`.
- **D-39** `race_done` event emitted by harness when all (lane, task) tuples complete or per-run 120s timeout fires.
- **D-40** Wasted-tokens computed server-side from `data/runs/<run_id>.json` at `fault_observed` time. Lives in `race/metrics.py`.
- **D-41** Wasted-tokens emitted as field on `fault_observed` payload. `fault_observed` is in NEVER_COALESCE.
- **D-43** `negotiate_meeting` is structural-only. No LLM judge.

### Claude's Discretion

- Layout of `race/runners/` package (single file per lane vs subpackage).
- Where `ExecutionContext` is defined (`race/runners/hybrid.py` vs `race/types.py`).
- Whether `mcp_servers/race_*.py` files share a common base.
- Mock fixture data (5 GitHub repos, 3 calendars, travel inventory).
- Whether `Detector` and `failure_mode_classifier` share module-level state pool.
- **D-38 (planner note)**: Harness concurrency model — bounded `asyncio.Semaphore` vs full sequential vs `asyncio.gather` + retry-backoff. Closed in §D-38 Resolution below.
- **D-42 (planner note)**: Haiku judge integration — reuse `reasoning.py` Anthropic client vs new `race/judges/`. Closed in §D-42 Resolution below.

### Deferred Ideas (OUT OF SCOPE)

- Real plan-emitter hybrid (TODO 1).
- Multi-seed benchmark beyond seed=42 (TODO 2).
- Paraphrase-resilient recovery via LLM judge (TODO 10).
- Cross-run aggregate analytics beyond per-(lane, task) headline (Phase 9).
- Real (non-stub) trace migrator (TODO 4).
- Per-tool retry budget config (v2+).
- AST-based lint plugin for inject_fault IRON RULE (CI grep is sufficient).
- UI for race page / heatmap / banner (Phases 8–9).
- Replay route deterministic test (Phase 9 HEAT-03).
- K∈{2,3,4,5} sweep (Phase 9 HEAT-04).
- OG / heatmap PNG (Phase 10).

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **RACE-01** | `HardnessType` enum with 4 v1 entries; `HardnessProfile` dataclass; each v1 type appears in ≥2 tasks. | §1 Architecture Overview (`race/types.py`); §8 Validation Architecture (`test_hardness_coverage.py`). |
| **RACE-02** | Three runners — `pure_mcp.py`, `pure_a2a.py`, `hybrid.py` — each consumes a per-task `task_config.yaml` and returns `RaceResult`. | §4 Runner Contracts; §5 Mock + Transport Wiring. |
| **RACE-03** | `harness.py` drives N parallel runs per (lane, task); `n=5` demo / `n=1` dev; deterministic model/seed/temperature; `per_run_timeout_s=120`; live ws emission; only retries transient infrastructure errors. | §2 D-38 Resolution: Harness Concurrency. |
| **RACE-04** | Recovery state machine in `race/classifier.py` tags each fault; K=3 turn window; locked regex with negation guard. | §6 Recovery Classifier. |
| **RACE-05** | Three v1 tasks with full `task_config.yaml` + per-task scorer (Haiku / structural / composite). | §3 D-42 Resolution: Judge Integration; §7 Per-task Callable Registries. |
| **RACE-06** | `failure_mode_classifier` produces deterministic per-lane headline sentences from 6 templates. | §6 Recovery Classifier (`failure_mode_classifier` shape + `characteristic_event` derivation). |
| **RACE-07** | Mock APIs for the 3 v1 tasks — GitHub mock (5 fixture repos), calendar mock (3 fixture calendars), travel mock (search + booking + fixtures). | §5 Mock + Transport Wiring; §1 Architecture Overview. |

</phase_requirements>

## Project Constraints (from CLAUDE.md)

- Python 3.10+; FastAPI; pytest. Backend tests run via `pytest`.
- Frontend at `frontend/src/` not touched in Phase 7.
- gstack `/browse` for web browsing; never use `mcp__claude-in-chrome__*` tools (not relevant — Phase 7 is pure backend).
- Memory store at http://localhost:37701; save significant decisions via `POST /api/memory/save` with `project: "A2AvsMCP"`.
- Project skills available via slash commands; not invoked during research.

## Summary

Phase 7 stands up the v2.0 race demo's compute substrate on top of Phase 6's already-shipped trace + ws schema. Three runner lanes (pure_mcp, pure_a2a, hybrid) execute three v1 tasks (summarize_repo, negotiate_meeting, book_travel) under a deterministic harness, with all faults flowing through the Phase 6 `inject_fault()` chokepoint. The recovery classifier (`Detector(K=3)`) is owned in `race/classifier.py` and instantiated inline by runners, guaranteeing replay symmetry. The harness drives 15 concurrent Anthropic Sonnet calls per `(n=5, 3 lanes, 1 task)` invocation — well under Tier 1 limits but must be bounded with a semaphore to absorb token-burst variance.

Two prior gray areas closed in this research: **(D-38)** harness concurrency uses a bounded `asyncio.Semaphore(8)` with transient-only retry on HTTP 5xx / 429 / connection-reset (NOT on injected faults). **(D-42)** Haiku judge ships in a new `race/judges/` module — `reasoning.py` is OpenAI-bound and would force coupling that violates D-19's "fresh race code" stance; a small dedicated Anthropic client with prompt caching on the static rubric system prompt is cleaner. Critically: **the Anthropic SDK does NOT support a `seed` parameter** — `seed=42` is for documentation/methodology only. Determinism comes from `temperature=0` plus deterministic mocks; LLM micro-variance is documented (master design §"Cross-model T4: seed sweep" already discloses).

**Primary recommendation:** Adopt the package layout in §1, the `Semaphore(8)` concurrency model in §2, the dedicated `race/judges/haiku.py` module in §3. Persist all judge calls into the trace as `llm_call` events so wasted-tokens computation reads them. Lock the runner contract signature in §4 verbatim; treat ExecutionContext as a thin TypedDict in `race/types.py` (not a class) to avoid premature abstraction.

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Concurrency control (n=5 × 3 lanes parallel) | Harness (`race/harness.py`) | — | Single owner of `asyncio.Semaphore` + retry classifier; runners stay sync-first. |
| Per-lane execution | Runner (`race/runners/<lane>.py`) | TraceRecorder | Each runner owns its TraceRecorder + Detector lifecycle per (run_id, lane). |
| MCP transport | Existing `mcp/client.py` | New `mcp_servers/race_*.py` | Phase 7 ADDS servers; client is reused verbatim per D-23. |
| A2A transport | Existing `a2a/broker.py` | New per-lane fixture handlers | Phase 7 REGISTERS handlers; broker is reused verbatim per D-24. |
| Fault mutation | `race/failure.py::inject_fault()` (Phase 6) | `race/mocks/*` | Single chokepoint per D-25; CI grep enforces. |
| Fault detection | `race/classifier.py::Detector` | Runner (consumer) | Algorithm owns the K=3 logic; runner instantiates per fault. |
| Headline classification | `race/classifier.py::failure_mode_classifier` | Harness (caller at race_done) | Pure function; same module = single recovery-analysis concept. |
| Wasted tokens | `race/metrics.py::compute_wasted_tokens` | TraceRecorder (data source) | Reads ndjson at `fault_observed` time per D-40. |
| LLM (Sonnet) per-run | Harness | Anthropic SDK | Each runner gets a model client from harness; harness owns retry. |
| LLM (Haiku) judge | `race/judges/haiku.py` | Per-task scorer in `race/tasks/<id>/__init__.py` | Dedicated module per D-42 resolution. |
| Task config + registries | `race/tasks/<id>/__init__.py` (per task) | Pydantic loader in `race/tasks/loader.py` | Per-task self-registration; loader validates at startup. |

---

## 1. Architecture Overview

### Package layout (recommendation, locked)

```
src/a2a_vs_mcp/race/
├── __init__.py                     # existing (Phase 6); add re-exports for new modules
├── schemas.py                      # existing (Phase 6) — wire events
├── turn.py                         # existing (Phase 6) — TURN_DEFINING_EVENTS
├── failure.py                      # existing (Phase 6) — FaultKind, inject_fault, validate_failure_script
├── runs.py                         # existing (Phase 6) — RunWriter
├── replay.py                       # existing (Phase 6) — load_run, migrate_v1
├── ws.py                           # existing (Phase 6) — ConnectionManager
│
├── types.py                        # NEW — HardnessType, HardnessProfile, TaskSpec, RaceResult, ScoreCard, ExecutionContext (TypedDict)
├── classifier.py                   # NEW — Detector(K=3), failure_mode_classifier, regex (compiled once)
├── metrics.py                      # NEW — compute_wasted_tokens(events, fault_id, lane) -> int
├── harness.py                      # NEW — drive N×3×1 runs; emits race_done; owns Semaphore + retry classifier
│
├── runners/
│   ├── __init__.py                 # NEW — re-export run_pure_mcp, run_pure_a2a, run_hybrid
│   ├── pure_mcp.py                 # NEW — pure_mcp runner
│   ├── pure_a2a.py                 # NEW — pure_a2a runner
│   └── hybrid.py                   # NEW — pre-scripted plan executor; on_fault dispatch
│
├── judges/
│   ├── __init__.py                 # NEW
│   └── haiku.py                    # NEW — Anthropic Haiku client with prompt caching, deterministic config
│
├── mocks/
│   ├── __init__.py                 # NEW
│   ├── github.py                   # NEW — 5-repo fixture; called by both MCP server + A2A handler
│   ├── calendar.py                 # NEW — 3-calendar fixture
│   └── travel.py                   # NEW — search/booking + fixtures
│
└── tasks/
    ├── __init__.py                 # NEW
    ├── loader.py                   # NEW — Pydantic loader: TaskConfig schema + startup validation per D-28
    ├── summarize_repo/
    │   ├── __init__.py             # NEW — TARGETS + BINDS registries; scorer
    │   └── task_config.yaml        # NEW — verbatim from master design §task_config.yaml
    ├── negotiate_meeting/
    │   ├── __init__.py             # NEW — structural scorer (no Haiku)
    │   └── task_config.yaml        # NEW
    └── book_travel/
        ├── __init__.py             # NEW — composite scorer (structural AND Haiku)
        └── task_config.yaml        # NEW

src/a2a_vs_mcp/mcp_servers/
├── race_github.py                  # NEW — wraps race.mocks.github
├── race_calendar.py                # NEW — wraps race.mocks.calendar
└── race_travel.py                  # NEW — wraps race.mocks.travel

data/race/fixtures/                 # NEW — outside src/ because it's data
├── github/repos.json               # 5 repos
├── calendar/calendars.json         # 3 calendars
└── travel/inventory.json           # flights + hotels

tests/race/
├── (existing — TRC-01..04, do not modify)
├── test_hardness_coverage.py       # RACE-01
├── test_pure_mcp_runner.py         # RACE-02
├── test_pure_a2a_runner.py         # RACE-02
├── test_hybrid_runner.py           # RACE-02 + on_fault branching
├── test_harness_concurrency.py     # RACE-03 (semaphore + retry-classifier)
├── test_classifier_detector.py     # RACE-04 (K=3 + regex FP target)
├── test_classifier_failure_mode.py # RACE-06 (15-fixture snapshot)
├── test_task_config_loader.py      # RACE-05 (Pydantic startup validation)
├── test_mocks_chokepoint.py        # RACE-07 + extends Phase 6 D-13 grep
├── test_judge_determinism.py       # D-42 verification
├── test_metrics_wasted_tokens.py   # D-40
├── conftest.py                     # shared fixtures: run_id minting, recorder factory, deterministic clock
└── fixtures/
    ├── classifier_traces/          # 9 fictional traces (master design §The Assignment)
    └── recovery_regex_corpus.jsonl # 50 hand-labeled samples (eng-review test plan)
```

### ExecutionContext placement (Claude's Discretion → recommendation)

**Place `ExecutionContext` in `race/types.py`** (not in `runners/hybrid.py`). Rationale:
- Both `BINDS: dict[str, Callable[[ExecutionContext], Any]]` (D-27) in `tasks/<id>/__init__.py` and `runners/hybrid.py` consume it. Putting it next to `TaskSpec`/`RaceResult` keeps types co-located.
- Task `__init__.py` files import from `race.types`; if context lived in `runners/hybrid.py`, every task would import a runner module — backwards.

### ExecutionContext shape (minimal v1)

```python
# race/types.py
from typing import TypedDict, Any

class ExecutionContext(TypedDict, total=False):
    """Mutable per-(run, lane) state visible to hybrid_plan.bind callables.

    Hybrid runner builds this incrementally as steps execute. Bind callables
    READ from it; they never mutate. Mutation is the runner's job.
    """
    task_input: dict[str, Any]              # initial prompt + task-level args (e.g., budget_usd for book_travel)
    subagent_outputs: dict[str, Any]        # keyed by subagent name — populated after each `kind: delegate` step
    tool_outputs: dict[str, Any]            # keyed by tool name — populated after each `kind: tool` step
    scratchpad: dict[str, Any]              # free-form per-task state (e.g., book_travel's "lowest_cost_combo" computation)
```

Why TypedDict (not @dataclass): no construction overhead, `dict.get()` works, extends naturally if v2 adds keys, no methods needed (pure data shape). Aligns with project's "dataclass-first for owned-by-class data; dict for free-form state" tendency (`agents/base.py` uses both).

### Module sizing sanity check

- `race/types.py` ≈ 60 lines (5 dataclasses + 1 TypedDict + 1 StrEnum)
- `race/classifier.py` ≈ 200 lines (Detector ~80, failure_mode_classifier ~80, regex compile + helpers ~40)
- `race/harness.py` ≈ 180 lines (Semaphore, retry classifier, gather coordination, race_done emission)
- `race/runners/{pure_mcp,pure_a2a}.py` ≈ 120 lines each
- `race/runners/hybrid.py` ≈ 200 lines (4 on_fault branches × scaffolding)
- `race/judges/haiku.py` ≈ 100 lines

Total Phase 7 net-new code: ~1,800 LOC backend + ~1,500 LOC tests. Single phase, 4 waves.

---

## 2. D-38 Resolution: Harness Concurrency

### The math

Demo invocation: `n=5 runs × 3 lanes × 1 task = 15 concurrent Sonnet calls per harness invocation`.
Worst-case sustained: dev mode is `n=1`; demo mode is the ceiling (n=5). Each task is invoked separately (the harness drives one task at a time across all 3 lanes per CONTEXT.md §Phase Boundary), so true concurrency tops out at 15 in-flight Anthropic calls.

### Anthropic rate limits at default tier (Tier 1) [VERIFIED: platform.claude.com/docs/en/api/rate-limits via WebSearch 2026-04-28]

| Limit | Tier 1 (default) | Tier 2 | Tier 3 | Tier 4 |
|-------|-----------------|--------|--------|--------|
| Requests / min (RPM) | 50 | (not surfaced in search) | 2,000 | 4,000 |
| Input tokens / min (ITPM) — Sonnet 4.x bucket | 30,000 | (not surfaced) | 800,000 | 2,000,000 |
| Output tokens / min (OTPM) — Sonnet 4.x bucket | 8,000–10,000 | (not surfaced) | 160,000–200,000 | 400,000–800,000 |

Sonnet 4.x rate limit is shared across `claude-sonnet-4-6`, `claude-sonnet-4-5`, `claude-sonnet-4` (same bucket). [VERIFIED]

### Risk profile at n=5

- **RPM:** 15 concurrent requests well under 50 RPM Tier 1. No risk.
- **ITPM:** A `summarize_repo` run sends ~3,000–5,000 input tokens (system prompt + tool results + multi-turn). 15 × 5,000 ≈ 75,000 input tokens **in a burst** — over the 30,000 ITPM ceiling if all 15 land in the same minute. **MEDIUM risk.**
- **OTPM:** Each run produces ~500–1,500 output tokens. 15 × 1,500 = 22,500 — over the 8–10k OTPM ceiling if synchronized. **HIGH risk** without bounding.

### Three concurrency models compared

| Model | Pros | Cons | Verdict |
|-------|------|------|---------|
| **A: Full sequential** (`for run in runs: await run()`) | Trivially under all limits; no retry headache | n=5 × 3 lanes × ~30s/run ≈ 7.5 min wall clock — kills "live race" feel | REJECT |
| **B: `asyncio.gather(*tasks)` unbounded** | Maximum parallelism, simplest code | Will hit OTPM with 15 × 1.5k synchronized output bursts; first 429 cascades and harness has to retry-on-429 vs distinguish from injected `rate_limit_429` faults | REJECT |
| **C: `asyncio.Semaphore(N)` bounded** | Caps concurrency at N; ITPM/OTPM headroom; predictable | Need to pick N | **ACCEPT** |

### Recommended N: **`asyncio.Semaphore(8)`**

Reasoning:
- 8 concurrent × 1,500 OTPM output ≈ 12k OTPM peak — at edge of Tier 1 OTPM but with natural staggering (Sonnet streams at ~50 t/s, so peak compresses).
- 8 leaves headroom for **judge calls** (Haiku). Haiku has its own 4.x bucket but counts toward total concurrency budget. Reserve 7 slots for Sonnet, 1 for Haiku judge calls invoked at run-end.
- 8 means each (lane, run_idx) tuple of n=5 × 3 lanes = 15 starts in two waves of ~7+8, completing ~30s + 30s ≈ 60s wall-clock — fits the demo's "live race" energy.
- Concrete: `_SEMAPHORE = asyncio.Semaphore(8)` at module scope in `race/harness.py`. The per-run async coroutine acquires before any Anthropic call, releases on return.

If demo machine is provisioned at Tier 2 or higher, N can be raised — surface it as `HARNESS_CONCURRENCY: int = int(os.getenv("RACE_HARNESS_CONCURRENCY", "8"))` so demo operators can tune without a code change.

### Retry classifier (transient-only — D-38 mandate)

```python
# race/harness.py
import anthropic  # Anthropic SDK

# These are RETRIED with exponential backoff (max 3 attempts).
TRANSIENT_RETRY_TYPES: tuple[type[Exception], ...] = (
    anthropic.APIConnectionError,    # connection-reset, DNS, TCP-level
    anthropic.APITimeoutError,       # client-side request timeout
    anthropic.InternalServerError,   # HTTP 500-599 from Anthropic
    anthropic.RateLimitError,        # HTTP 429 from Anthropic infra (NOT from injected faults)
)

# These are NEVER retried — they are the test.
NEVER_RETRY = (
    "InjectedFaultError",  # custom marker class; raised by mocks via inject_fault()
    # Any exception with `__injected__ = True` attribute set by inject_fault path
)
```

**Critical distinction:** `anthropic.RateLimitError` (real Anthropic 429) IS retried. The injected `FaultKind.RATE_LIMIT_429` (Phase 6 `_apply_mutation`) raises a `RuntimeError` in user code — it must be re-tagged so the harness's exception classifier can distinguish it.

**Recommendation:** Phase 7 adds a custom exception type `InjectedFaultError(RuntimeError)` in `race/failure.py`; `_apply_mutation` raises this for `RATE_LIMIT_429` and `PARTIAL_COMMIT_5XX` instead of bare `RuntimeError`. Existing Phase 6 IRON RULE atomicity test (`test_inject_fault.py:test_record_runs_before_raise`) needs trivial update from `assertRaises(RuntimeError)` → `assertRaises(InjectedFaultError)`.

### Backoff schedule

`time.sleep(2 ** attempt + jitter)` per `attempt ∈ {1, 2, 3}`. Total max wait: 2+4+8 = 14s. Stays under the 120s `per_run_timeout_s` budget (D-39).

### Per-run timeout (D-39)

Use `asyncio.wait_for(run_coroutine, timeout=120)` per (lane, run_idx). On `asyncio.TimeoutError`, the harness emits a `done` event with `outcome="timeout"` and the run's RaceResult is tagged accordingly (master design §Harness failure taxonomy: `success | timeout | tool_error | model_error | judge_failed | injected_fault_*`).

---

## 3. D-42 Resolution: Judge Integration

### Reuse `reasoning.py` vs new `race/judges/`

`reasoning.py` (read in full):
- Hardcoded to OpenAI (`from openai import OpenAI`, `client.responses.create`, `OPENAI_MODEL`).
- Two reasoner classes (`MockReasoner`, `LLMReasoner`, `FakeReasoningEngine`) all bound to ticket-classification + summarize-customer-support taxonomies.
- Subclassing `LLMReasoner` to swap-in Anthropic would force the SupportTicket abstraction onto the race judge — exactly what D-19 forbids ("SupportTicket/AgentResult abstractions do not leak into race").

**Verdict:** Reuse is forbidden by D-19. New module required.

### Recommended module: `race/judges/haiku.py`

```python
# race/judges/haiku.py
"""Haiku judge for race scorers (D-42).

Used by:
  - race/tasks/summarize_repo/__init__.py — judges purpose, ≥3 modules, entry point (3/3 = success).
  - race/tasks/book_travel/__init__.py    — judges trip purpose match (composite with structural).

NOT used by negotiate_meeting (D-43 — structural-only).

Determinism: temperature=0. Anthropic does NOT support a `seed` parameter
[VERIFIED: anthropics/anthropic-sdk-python — seed parameter absent]; seed=42
is documentation/methodology only (master design seed-sweep §T4 already
discloses LLM stochasticity at temp=0).

Prompt caching: rubric system prompt is static across all calls in a phase →
mark with cache_control type=ephemeral. Saves ~90% of system-prompt input
tokens after first call (Anthropic prompt-cache: read tokens are 0.1× base).
[CITED: docs.claude.com/en/docs/build-with-claude/prompt-caching]
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
import os

import anthropic  # NEW dep — see §Environment Availability


HAIKU_MODEL: str = "claude-haiku-4-5"  # locked per master design §Judge / scorer
TEMPERATURE: float = 0.0


@dataclass
class JudgeVerdict:
    passed: bool
    score: int           # raw count of rubric items satisfied (0..N)
    rubric_total: int    # N (denominator)
    rationale: str       # short human-readable; surfaced in trace for debugging
    tokens_in: int
    tokens_out: int


class HaikuJudge:
    """Stateless wrapper. Caller passes a system_prompt (the rubric) and a user_prompt
    (the artifact to judge). Verdict parsing is the caller's job; judge returns
    structured Anthropic Message + accounting.
    """

    def __init__(self, recorder: "TraceRecorder | None" = None) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set; race judges require it.")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._recorder = recorder

    def judge(
        self,
        *,
        rubric_system_prompt: str,        # marked for cache
        artifact_user_prompt: str,        # the run's output to evaluate
        max_tokens: int = 512,
    ) -> JudgeVerdict:
        msg = self._client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=max_tokens,
            temperature=TEMPERATURE,
            system=[
                {
                    "type": "text",
                    "text": rubric_system_prompt,
                    "cache_control": {"type": "ephemeral"},  # rubric is static across runs
                }
            ],
            messages=[{"role": "user", "content": artifact_user_prompt}],
        )
        text = msg.content[0].text if msg.content else ""
        tokens_in = msg.usage.input_tokens
        tokens_out = msg.usage.output_tokens
        # Caller parses `text` per its rubric; this method is generic.
        if self._recorder is not None:
            self._recorder.record(
                "llm_call",
                model=HAIKU_MODEL,
                role="judge",
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                t_call_start_ms=...,  # filled by recorder
            )
        return JudgeVerdict(
            passed=False,           # caller fills via rubric parse
            score=0,
            rubric_total=0,
            rationale=text,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
        )
```

### Determinism notes

1. **No seed parameter exists in Anthropic Messages API** [VERIFIED: WebSearch 2026-04-28; cookbook + SDK source confirm]. The `seed=42` in master design §Harness defaults is for methodology disclosure only — operators see it in run footers and methodology section.
2. **`temperature=0.0` is necessary but not sufficient.** Anthropic docs explicitly state: "even with temperature 0.0, the results will not be fully deterministic" [CITED: theneuralbase.com / claude API docs synthesis]. Hardware-level non-determinism (FP rounding across GPU shards) introduces ~1% token-level variance.
3. **Mitigation:** All race judges have **structural rubrics** — count rubric items, not freeform prose. Counting is robust to ±1 token variance. Master design §Cross-model T4 already discloses seed sweep `[42, 43, 44, 45, 46]` would show this; v1 ships seed=42 only and discloses non-determinism in methodology footer.
4. **What we CAN guarantee:** identical structural scores across re-runs of the same trace (because mocks are deterministic, only judge prose varies).

### Rubric prompts (per-task)

#### `summarize_repo` rubric

```
SYSTEM: You are a strict rubric scorer. Read the assistant output and answer YES/NO for each item.
RUBRIC:
  R1. Does the summary state the repository's purpose in one sentence?
  R2. Does the summary mention at least 3 distinct modules?
  R3. Does the summary identify the entry point (CLI, main, app)?
Output format (verbatim, machine-parseable):
R1: YES|NO
R2: YES|NO
R3: YES|NO
RATIONALE: <1 sentence>
```

Pass condition: `R1 == YES AND R2 == YES AND R3 == YES` (3/3, master design §Judge).

#### `book_travel` Haiku rubric (composite with structural)

```
SYSTEM: You are a strict rubric scorer for a travel-booking trip plan.
RUBRIC:
  R1. Does the booked itinerary match the user's stated trip purpose (e.g., business trip vs vacation)?
Output format:
R1: YES|NO
RATIONALE: <1 sentence>
```

Composite scoring lives in `race/tasks/book_travel/__init__.py::score()`:
```python
def score(result, trace, judge: HaikuJudge | None) -> ScoreCard:
    structural_pass = (
        result.total_cost_usd <= result.budget_usd
        and _legs_connect(result.itinerary)
    )
    haiku_pass = judge.judge(
        rubric_system_prompt=BOOK_TRAVEL_RUBRIC,
        artifact_user_prompt=result.summary,
    ).passed if judge else False
    return ScoreCard(
        success=structural_pass and haiku_pass,
        ...
    )
```

### Why prompt caching matters here

Without cache: each of 15 runs × 2 Haiku tasks × ~400 token rubric = 12,000 input tokens of rubric (paid full price).
With cache (5-min ephemeral, default): rubric is paid 1× at first call (1.25× write cost), then 0.1× per subsequent call. Net savings ≈ 88% on system-prompt input tokens. [CITED: platform.claude.com/docs/en/build-with-claude/prompt-caching]

**Note:** Haiku 4.5 minimum cache size is 2,048 tokens [CITED: same]. The summarize_repo rubric is ~400 tokens — **below the cache minimum**. Phase 7 should pad rubrics with a stable rubric-format preamble (instructions for output format, common edge-cases) to clear the 2,048-token threshold, OR accept that summarize_repo rubric won't actually cache (still works correctly, just no savings). Recommend padding for cost discipline; document threshold in `race/judges/haiku.py` docstring.

### Anthropic SDK installation

`anthropic>=0.40` (current stable, supports `cache_control`, Haiku 4.5, Sonnet 4.6 model IDs). Add to `pyproject.toml [project] dependencies`. Currently NOT installed (`python3 -c "import anthropic"` returns ModuleNotFoundError — see §Environment Availability).

---

## 4. Runner Contracts

### Locked signatures

```python
# race/runners/pure_mcp.py
async def run_pure_mcp(
    task_spec: TaskSpec,
    run_id: str,
    recorder: TraceRecorder,
    failure_script: list[FailureScriptEntry],
    sonnet_client: anthropic.AsyncAnthropic,
) -> RaceResult: ...

# race/runners/pure_a2a.py
async def run_pure_a2a(
    task_spec: TaskSpec,
    run_id: str,
    recorder: TraceRecorder,
    failure_script: list[FailureScriptEntry],
    sonnet_client: anthropic.AsyncAnthropic,
) -> RaceResult: ...

# race/runners/hybrid.py
async def run_hybrid(
    task_spec: TaskSpec,
    run_id: str,
    recorder: TraceRecorder,
    failure_script: list[FailureScriptEntry],
    hybrid_plan: HybridPlan,    # parsed task_config.hybrid_plan
    sonnet_client: anthropic.AsyncAnthropic,
) -> RaceResult: ...
```

Note: D-20 says `run(...)`; the recommendation is **module-level functions, not classes**. Rationale: each runner is a coroutine + helpers; a class adds no state worth holding (recorder + detectors are per-call). Matches the project's `evidence.py` pattern (module-level helpers, no `EvidenceService` class).

### TaskSpec (locked from master design §Task interface)

```python
# race/types.py
from dataclasses import dataclass, field
from enum import Enum

class HardnessType(str, Enum):
    LONG_CHAIN = "long_chain"
    RATE_PRESSURE = "rate_pressure"
    SCHEMA_VARIANCE = "schema_variance"
    MULTI_SOURCE_SYNTHESIS = "multi_source"

@dataclass
class HardnessProfile:
    types: list[HardnessType]

@dataclass
class TaskSpec:
    task_id: str
    prompt: str                       # the LLM prompt (same across all 3 lanes per master design §Prompt fairness)
    allowed_tools: list[str]          # tool names available to this task (drawn from TARGETS keys)
    expected_shape: dict[str, type]   # for structural scoring
    hardness_profile: HardnessProfile

@dataclass
class ScoreCard:
    success: bool
    ttff_ms: int                      # turn-of-first-fault, derived
    recovered: bool
    wasted_tokens_before_detection: int | None
    failure_mode: str                 # one of harness failure-taxonomy values
    cost_usd: float
    latency_ms: int

@dataclass
class RaceResult:
    run_id: str
    lane: str
    task_id: str
    hardness_profile: HardnessProfile
    score_card: ScoreCard
    trace_id: str                     # = run_id; trace per (run_id, lane) at data/runs/<run_id>.json
```

### Hybrid `on_fault` dispatch (D-29 enum)

```python
# race/runners/hybrid.py
async def _execute_step(step: HybridStep, ctx: ExecutionContext, ...) -> Any:
    try:
        result = await _dispatch_step(step, ctx)
        return result
    except InjectedFaultError as exc:
        if step.on_fault == "retry_once":
            try:
                return await _dispatch_step(step, ctx)
            except InjectedFaultError:
                raise  # exhausted retry; propagate
        elif step.on_fault == "delegate":
            return await _dispatch_step(_delegate_alt_step(step), ctx)
        elif step.on_fault == "abort":
            raise  # bubble up; runner ends with score_gate=FAIL
        elif step.on_fault == "continue":
            return None  # ignore fault; proceed to next step (this is the "kept_going_without_noticing" path)
```

Tests for each branch are in `tests/race/test_hybrid_runner.py` (see §8).

---

## 5. Mock + Transport Wiring

### MCPClient call shape (verified from `mcp/client.py:102-119`)

```python
client = MCPClient(
    server_module="a2a_vs_mcp.mcp_servers.race_github",
    trace=recorder,
    project_root=PROJECT_ROOT,
    failure_config=None,                  # NOT used in race; race uses inject_fault() chokepoint
    transport="in_process",               # demo locks in_process per project profile
)
result = client.call("get_repo_metadata", {"repo_id": "demo-org/demo-repo"})
```

**Critical:** `MCPClient._simulate_failure()` (lines 306-310) is wired to `FailureConfig` (v1 demo) and looks for `db_down` / `docs_timeout`. Race lanes pass `failure_config=None` so this path is inert; faults flow through the new `inject_fault()` chokepoint inside the race MCP server's tool dispatch.

### Race MCP server shape (template from `mcp_servers/db_server.py`)

```python
# src/a2a_vs_mcp/mcp_servers/race_github.py
from __future__ import annotations
from mcp.server.fastmcp import FastMCP
from a2a_vs_mcp.race.mocks import github as github_mock

def build_server() -> FastMCP:
    mcp = FastMCP("Race GitHub MCP", json_response=True)

    @mcp.tool()
    def get_repo_metadata(repo_id: str) -> dict:
        """Return repo metadata (mocked, fault-injectable)."""
        return github_mock.get_repo_metadata(repo_id)  # mock owns inject_fault chokepoint

    @mcp.tool()
    def list_files(repo_id: str, path: str = "") -> list[str]:
        return github_mock.list_files(repo_id, path)

    # ... more tools per task_config TARGETS
    return mcp
```

**Wire into `MCPClient.SERVER_BUILDERS`** in `mcp/client.py` (lines 24-27): add three new entries. This is the ONE small mutation needed to existing code; not a behavior change, just a registry addition. Strictly speaking this violates the "don't touch transport" letter, but the registry IS extension-point — confirm with planner.

**Alternative:** Don't touch `mcp/client.py`. Instead, race code uses `transport="stdio"` for race servers (which builds StdioServerParameters from server_module string and doesn't consult `SERVER_BUILDERS`). Cleaner — no v1 file mutation. **Recommend this path.**

### Race mock shape (single fault chokepoint per D-25)

```python
# race/mocks/github.py
"""GitHub fixture mock. SINGLE FAULT CHOKEPOINT — every fault flows through inject_fault()."""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from ..failure import inject_fault, FaultKind

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "data" / "race" / "fixtures" / "github"

# Module-level state: which fault is "live" right now per (run_id, target).
# Set by harness BEFORE the runner invokes the mock (or via contextvars per run).
_ACTIVE_FAULTS: dict[tuple[str, str], FaultEntry] = {}  # (run_id, target) -> entry

def _load_fixture(name: str) -> Any:
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text())

def get_repo_metadata(repo_id: str, *, recorder, run_id: str) -> dict[str, Any]:
    """Returns repo metadata; routes through inject_fault() if a fault is scripted for this target."""
    response = _load_fixture("repos")[repo_id]   # raw fixture
    fault = _ACTIVE_FAULTS.get((run_id, "github_api.get_repo_metadata"))
    if fault is not None:
        return inject_fault(
            recorder=recorder,
            fault_id=fault.id,
            kind=fault.kind,
            target="github_api.get_repo_metadata",
            original_response=response,
        )
    return response
```

**The recorder + run_id parameters** are how the mock reaches into the trace. They're injected by either:
- The MCP server's tool function (which receives them via `contextvars` set by the runner before `client.call()`), OR
- The A2A handler's `handle_task` method (same contextvars pattern).

**Alternative pattern (cleaner):** Wrap the mock in a small adapter per (run, lane) that pre-binds recorder + run_id. Each tool function in the race MCP server constructs the adapter. Picks up project's existing pattern (`evidence.get_customer_profile(db_path, ...)` — db_path is bound at server build time).

Recommend the contextvars pattern: less ceremony, no per-call partial application.

### A2A broker handler shape

The broker's `handle_task` contract (verified from `broker.py:206-231`):

```python
class FixtureBackedAgentHandler:
    """Race-specific A2A agent handler. One per (lane, capability)."""

    def __init__(self, capability: str, recorder: TraceRecorder, run_id: str) -> None:
        self.capability = capability
        self.recorder = recorder
        self.run_id = run_id

    def handle_task(self, message: A2AMessage) -> AgentResult:
        """Called by A2ABroker._execute_with_timeout() inside ThreadPoolExecutor.

        message.payload carries the task input (e.g., {"repo_id": "..."}).
        Returns AgentResult with summary + details + confidence + status.

        Faults flow through race.mocks.* (inject_fault chokepoint).
        """
        if self.capability == "fetch_repo_metadata":
            data = github_mock.get_repo_metadata(
                message.payload["repo_id"],
                recorder=self.recorder,
                run_id=self.run_id,
            )
            return AgentResult(
                agent_id=f"race_github_agent",
                summary=f"Fetched metadata for {message.payload['repo_id']}",
                details={"repo": data},
                confidence=1.0,
                status="completed",
            )
        # ... more capabilities
```

Registration:
```python
broker = A2ABroker(trace=recorder)  # trace is the lane's recorder
card = AgentCard(agent_id="race_github_agent", capabilities=["fetch_repo_metadata"], ...)
broker.register(card, FixtureBackedAgentHandler("fetch_repo_metadata", recorder, run_id))
```

Send:
```python
result = broker.send_task(A2AMessage(
    sender_agent="race_lead",
    target_agent="race_github_agent",
    capability="fetch_repo_metadata",
    payload={"repo_id": "demo-org/demo-repo"},
    ...
))
```

**Note on broker method name:** CONTEXT.md D-24 says `broker.send_message`. The actual method in `a2a/broker.py:61` is **`send_task`**. Research found this — flag for planner. (`send_message` does not exist.)

### Single fault chokepoint enforcement (extends Phase 6 D-13 grep)

Phase 6 grep test (`tests/race/test_iron_rule_grep.py`) checks only `src/a2a_vs_mcp/race/`. Phase 7 must extend to:

```python
# tests/race/test_iron_rule_grep.py — Phase 7 additions
ALL_FAULT_DIRS = [
    Path(__file__).resolve().parents[2] / "src" / "a2a_vs_mcp" / "race",
    Path(__file__).resolve().parents[2] / "src" / "a2a_vs_mcp" / "mcp_servers",  # race_github.py etc.
]

def test_no_direct_response_mutation_in_mcp_servers():
    """race_*.py MCP servers MUST call into race.mocks.*; the mocks call inject_fault."""
    # Forbid: literal raise RuntimeError("HTTP 4xx") in race_*.py
    # Allowed: tool fn body that calls into race.mocks.module.function(...)
    ...
```

---

## 6. Recovery Classifier (Detector + failure_mode_classifier)

### Detector class shape (D-31, D-32 — locked)

```python
# race/classifier.py
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import re

K_DEFAULT: int = 3

class DetectorState(str, Enum):
    WAITING = "waiting"
    AWAITING_OBSERVATION = "awaiting_observation"
    OBSERVED = "observed"

# D-36: regex compiled ONCE at module load.
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
    """D-36: regex with negation guard. Sentence boundary = [.!?] or end-of-message."""
    sentences = _SENTENCE_SPLIT.split(text) if text else []
    for sent in sentences:
        if not _ACK_FAULT_REGEX.search(sent):
            continue
        # Negation guard: if BOTH a negation token AND a fault token appear in the same sentence, drop.
        if _NEGATION_TOKENS.search(sent) and _NEGATION_FAULT_TOKENS.search(sent):
            continue
        return True
    return False


@dataclass
class Detector:
    """Stateful per-fault state machine (D-31)."""
    fault_id: str
    fault_kind: str
    target: str
    fault_inject_turn: int
    K: int = K_DEFAULT
    state: DetectorState = DetectorState.AWAITING_OBSERVATION
    t_observed_ms: int | None = None
    evidence_kind: str | None = None  # "tool_error" | "agent_msg" | "retry"

    def consume(self, event: dict) -> bool:
        """Feed one event. Returns True if state flipped to OBSERVED on this event."""
        if self.state != DetectorState.AWAITING_OBSERVATION:
            return False
        cur_turn = event.get("turn_index", -1)
        if cur_turn - self.fault_inject_turn > self.K:
            return False  # window closed; observation impossible
        et = event.get("event_type")
        if et == "tool_call" and event.get("status") == "error":
            return self._observe(event, "tool_error")
        if et == "tool_call" and event.get("tool_name") == self.target and cur_turn > self.fault_inject_turn:
            # retry_event: tool_name == fault.target AND turn_index > fault_inject_turn AND no successful call in interval
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
        """Per master design state machine — compute terminal tag at `done` event."""
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
        """D-34: race_done arrived without `done` for this lane — indeterminate."""
        return "indeterminate"
```

### Runner integration

```python
# race/runners/pure_mcp.py — sketch
detectors: list[Detector] = []

# When a fault_injected event is recorded by the mock layer:
# (recorder.record('fault_injected', ...) returns to user code)
# Runner sees the event in recorder.events and instantiates Detector:
def on_fault_injected(event: dict) -> None:
    detectors.append(Detector(
        fault_id=event["fault_id"],
        fault_kind=event["fault_kind"],
        target=event["target"],
        fault_inject_turn=event["turn_index"],
    ))

# Every subsequent event is fed to all live detectors:
def on_event(event: dict) -> None:
    for d in detectors:
        if d.consume(event):
            # state flipped to OBSERVED — emit fault_observed
            wasted = compute_wasted_tokens(recorder.events, d.fault_id, lane)
            recorder.record(
                "fault_observed",
                fault_id=d.fault_id,
                fault_kind=d.fault_kind,
                target=d.target,
                t_observed_ms=d.t_observed_ms,
                evidence=d.evidence_kind,
                wasted_tokens_before_detection=wasted,
            )
```

### `failure_mode_classifier` shape (D-35, D-37 — verbatim)

```python
# race/classifier.py
from typing import Literal

LANE = Literal["pure_mcp", "pure_a2a", "hybrid"]


def failure_mode_classifier(
    lane: LANE,
    task_id: str,
    per_run_tags: list[str],   # per-run recovery tags across n runs
    agg: dict[str, Any],       # {recovery_rate, mean_wasted_tokens, mean_ttff_ms, characteristic_event}
) -> str:
    """6 templates, locked verbatim from master design §failure_mode_classifier."""
    n = len(per_run_tags)
    if n == 0 or all(t == "lane_failed" for t in per_run_tags):
        return _template_lane_failed(lane, task_id, agg)
    dominant = _dominant_tag(per_run_tags)  # mode, ties broken by precedence
    fault_summary = _fault_summary(task_id)
    if dominant == "recovered":
        return f"{lane} *recovered {agg['recovery_rate']*n:.0f}/{n} times* after {fault_summary}; avg {agg['mean_wasted_tokens']:.0f} wasted tokens."
    if dominant == "gave_up":
        return f"{lane} noticed the {fault_summary} but *gave up at turn {agg.get('median_give_up_turn', 0)}*; recovery {agg['recovery_rate']*100:.0f}%."
    if dominant == "kept_going_without_noticing":
        phrase = _characteristic_event_phrase(lane, agg)
        return f"{lane} *{phrase}* after {fault_summary}; recovery {agg['recovery_rate']*100:.0f}%."
    if dominant == "kept_going_to_failure":
        return f"{lane} *kept going past {fault_summary}* and failed the score gate; recovery 0%."
    if dominant == "indeterminate":
        ind = sum(1 for t in per_run_tags if t == "indeterminate")
        return f"{lane} produced *{ind}/{n} indeterminate runs* on this task — disclosed."
    raise ValueError(f"Unknown dominant tag: {dominant}")


def _dominant_tag(tags: list[str]) -> str:
    """Mode of tags; ties broken by precedence: recovered > gave_up > kept_going_without_noticing > kept_going_to_failure > indeterminate."""
    PRECEDENCE = ["recovered", "gave_up", "kept_going_without_noticing", "kept_going_to_failure", "indeterminate"]
    counts = {t: tags.count(t) for t in PRECEDENCE}
    max_count = max(counts.values())
    for t in PRECEDENCE:
        if counts[t] == max_count:
            return t
    return "indeterminate"


def _characteristic_event_phrase(lane: LANE, agg: dict[str, Any]) -> str:
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
    # Fallback (counts absent — rare)
    n_turns = agg.get("median_turns_after_fault", 0)
    return f"continued for {n_turns} turns"
```

### `characteristic_event` count derivation (NEW — surfaced from trace fields)

These per-lane counts are **computed from trace events at headline-render time** (master design Reviewer Concern #3 — "not stored, derived"). The harness assembles `agg` after all n runs complete:

| Lane | Metric | Trace field source | Computation |
|------|--------|--------------------|-------------|
| pure_mcp | `median_retries` | `tool_call` events with `tool_name == fault.target` and `turn_index > fault_inject_turn`, scoped per fault_id, then taken across n runs | `statistics.median([count_per_run])` |
| pure_mcp | `characteristic_tool` | `failure_script[0].target` from task_config (the first targeted tool) | constant per task |
| pure_a2a | `median_delegations` | `agent_msg` events with `message_type == "task_submit"` (broker delegation) and `turn_index > fault_inject_turn` | `statistics.median([count_per_run])` |
| hybrid | `median_switches` | count of (lane-internal) protocol-boundary crossings: `tool_call → agent_msg` or `agent_msg → tool_call` transitions in event order, AFTER `fault_inject_turn` | `statistics.median([count_per_run])` |
| any (fallback) | `median_turns_after_fault` | max `turn_index` − `fault_inject_turn` per run | `statistics.median([turns_per_run])` |

These counts live in `race/metrics.py`:

```python
# race/metrics.py
import statistics
from typing import Any

def median_retries(events: list[dict], fault_id: str, target: str) -> int:
    """Per-run retry count = number of tool_call events with tool_name==target after fault_inject_turn (until done)."""
    fi = next((e for e in events if e.get("event_type") == "fault_injected" and e.get("fault_id") == fault_id), None)
    if not fi:
        return 0
    inject_turn = fi.get("turn_index", -1)
    return sum(
        1 for e in events
        if e.get("event_type") == "tool_call"
        and e.get("tool_name") == target
        and e.get("turn_index", -1) > inject_turn
    )

def median_delegations(events: list[dict], fault_id: str) -> int: ...
def median_switches(events: list[dict], fault_id: str) -> int: ...
def median_turns_after_fault(events: list[dict], fault_id: str) -> int: ...
def aggregate_for_classifier(per_run_traces: list[list[dict]], task_id: str, lane: str) -> dict[str, Any]: ...
```

---

## 7. Per-task Callable Registries (TARGETS + BINDS)

### Pattern reference: Phase 6 D-12 FaultKind validator (`race/failure.py:101-110`)

```python
_SCRIPT_ADAPTER: TypeAdapter[list[FailureScriptEntry]] = TypeAdapter(list[FailureScriptEntry])

def validate_failure_script(yaml_data: list[dict[str, Any]]) -> list[FailureScriptEntry]:
    return _SCRIPT_ADAPTER.validate_python(yaml_data)
```

Phase 7 extends with `target` and `bind` validation. Per D-28: typo → startup `ValidationError`, not silent runtime failure.

### Recommended TaskConfig schema (Pydantic v2)

```python
# race/tasks/loader.py
from __future__ import annotations
from typing import Callable, Literal
from importlib import resources

import yaml
from pydantic import BaseModel, ValidationError, field_validator

from ..failure import FaultKind, FailureScriptEntry


OnFault = Literal["retry_once", "delegate", "abort", "continue"]


class HybridStep(BaseModel):
    kind: Literal["tool", "delegate"]
    tool: str | None = None        # required when kind == "tool"
    agent: str | None = None       # required when kind == "delegate"
    goal: str | None = None
    bind: str | None = None        # bind key — must be in task's BINDS registry
    on_fault: OnFault | None = None


class HybridPlan(BaseModel):
    steps: list[HybridStep]


class FailureScriptYAMLEntry(BaseModel):
    kind: FaultKind
    target: str
    after_calls: int = 0
    duration_calls: int = 1
    # Free-form per-fault-kind extras (truncate_at_byte, target_calendar_id, drift, behavior, ...)
    model_config = {"extra": "allow"}


class TaskConfig(BaseModel):
    task_id: str
    hardness_profile: list[str]   # validated against HardnessType enum names
    failure_script: list[FailureScriptYAMLEntry]
    hybrid_plan: HybridPlan


def load_task_config(task_id: str) -> tuple[TaskConfig, dict[str, Callable], dict[str, Callable]]:
    """Load + validate. Per D-28 typos raise ValidationError at import time.

    Returns: (config, TARGETS, BINDS) — the registries from race/tasks/<id>/__init__.py.
    """
    pkg = f"a2a_vs_mcp.race.tasks.{task_id}"
    yaml_text = resources.files(pkg).joinpath("task_config.yaml").read_text()
    raw = yaml.safe_load(yaml_text)
    cfg = TaskConfig.model_validate(raw)

    # Import the task module to surface TARGETS + BINDS registries.
    mod = __import__(pkg, fromlist=["TARGETS", "BINDS"])
    targets: dict[str, Callable] = mod.TARGETS
    binds: dict[str, Callable] = mod.BINDS

    # Cross-validate every failure_script.target against TARGETS keys.
    for entry in cfg.failure_script:
        if entry.target not in targets:
            raise ValidationError.from_exception_data(
                title=f"Unknown target '{entry.target}' in {task_id}/task_config.yaml; "
                      f"known: {sorted(targets.keys())}",
                line_errors=[],
            )
    # Cross-validate every hybrid_plan.steps[].bind against BINDS keys (when bind is set).
    for step in cfg.hybrid_plan.steps:
        if step.bind is not None and step.bind not in binds:
            raise ValidationError.from_exception_data(
                title=f"Unknown bind '{step.bind}' in {task_id}/task_config.yaml; "
                      f"known: {sorted(binds.keys())}",
                line_errors=[],
            )
    return cfg, targets, binds
```

### Per-task `__init__.py` shape

```python
# race/tasks/summarize_repo/__init__.py
"""summarize_repo task registry.

TARGETS — failure_script.target strings → mock callables.
BINDS   — hybrid_plan.steps[].bind keys → ExecutionContext resolvers.
score() — per-task scorer (Haiku rubric, 3/3).
"""
from __future__ import annotations
from typing import Callable, Any

from ...mocks import github as github_mock
from ...types import ExecutionContext, ScoreCard, RaceResult
from ...judges.haiku import HaikuJudge

# D-27 registries
TARGETS: dict[str, Callable[..., Any]] = {
    "github_api.get_repo_metadata": github_mock.get_repo_metadata,
    "github_api.list_files": github_mock.list_files,
    "github_api.read_file": github_mock.read_file,
}

BINDS: dict[str, Callable[[ExecutionContext], Any]] = {
    # summarize_repo's hybrid_plan doesn't actually use bind in v1 yaml — included for symmetry.
}

# D-42 rubric
_RUBRIC = """You are a strict rubric scorer. ... R1/R2/R3 ... output format ..."""

def score(result: dict, trace: list[dict], judge: HaikuJudge | None) -> ScoreCard:
    if judge is None:
        # CI / dev mode without ANTHROPIC_API_KEY — skip Haiku, return failure (test should set up judge).
        return ScoreCard(success=False, ...)
    verdict = judge.judge(rubric_system_prompt=_RUBRIC, artifact_user_prompt=result["summary"])
    # Parse verdict.rationale → extract R1/R2/R3 YES/NO
    r1 = "R1: YES" in verdict.rationale.upper()
    r2 = "R2: YES" in verdict.rationale.upper()
    r3 = "R3: YES" in verdict.rationale.upper()
    return ScoreCard(success=(r1 and r2 and r3), ...)
```

### Startup validation hook

```python
# race/tasks/__init__.py
from .loader import load_task_config

V1_TASK_IDS = ["summarize_repo", "negotiate_meeting", "book_travel"]
TASK_CONFIGS: dict[str, tuple] = {tid: load_task_config(tid) for tid in V1_TASK_IDS}
```

This module-level dict-comp **runs at first import** of `race.tasks`. Any typo in any task_config.yaml → `ValidationError` at import time → `pytest --collect-only` fails noisy. Matches eng-review test plan Critical Path #9.

---

## 8. Validation Architecture

### Test framework

| Property | Value |
|----------|-------|
| Framework | `pytest>=8.0` + `pytest-asyncio>=0.24` (already in pyproject `[project.optional-dependencies] dev`) |
| Config file | `pyproject.toml [tool.pytest.ini_options] asyncio_mode = "auto"` (already set) |
| Quick run command | `pytest tests/race/ -x` |
| Full suite command | `pytest` |

Phase 6 tests (`tests/race/test_*` — 37 tests, all green per STATE.md) MUST stay green. Phase 7 adds a parallel set; existing tests untouched.

### Phase Requirements → Test Map

| Req | Behavior | Test Type | Automated Command | File Exists? |
|-----|----------|-----------|-------------------|--------------|
| **RACE-01** | HardnessType enum has 4 v1 values | unit | `pytest tests/race/test_hardness_coverage.py::test_enum_values -x` | ❌ Wave 0 |
| **RACE-01** | Each HardnessType in ≥2 of 3 v1 task_configs | integration | `pytest tests/race/test_hardness_coverage.py::test_coverage_two_each -x` | ❌ Wave 0 |
| **RACE-02** | pure_mcp runner returns RaceResult; consumes task_config | integration | `pytest tests/race/test_pure_mcp_runner.py -x` | ❌ Wave 0 |
| **RACE-02** | pure_a2a runner registers handlers + uses real broker | integration | `pytest tests/race/test_pure_a2a_runner.py -x` | ❌ Wave 0 |
| **RACE-02** | hybrid runner executes hybrid_plan.steps in order | integration | `pytest tests/race/test_hybrid_runner.py::test_steps_in_order -x` | ❌ Wave 0 |
| **RACE-02** | hybrid on_fault=retry_once branch | integration | `pytest tests/race/test_hybrid_runner.py::test_on_fault_retry_once -x` | ❌ Wave 0 |
| **RACE-02** | hybrid on_fault=delegate branch | integration | `pytest tests/race/test_hybrid_runner.py::test_on_fault_delegate -x` | ❌ Wave 0 |
| **RACE-02** | hybrid on_fault=abort branch | integration | `pytest tests/race/test_hybrid_runner.py::test_on_fault_abort -x` | ❌ Wave 0 |
| **RACE-02** | hybrid on_fault=continue branch (kept-going path) | integration | `pytest tests/race/test_hybrid_runner.py::test_on_fault_continue -x` | ❌ Wave 0 |
| **RACE-03** | Harness drives N tuples; n=1 dev path | integration | `pytest tests/race/test_harness_concurrency.py::test_n1_dev -x` | ❌ Wave 0 |
| **RACE-03** | Harness Semaphore caps concurrency at 8 | unit | `pytest tests/race/test_harness_concurrency.py::test_semaphore_bound -x` | ❌ Wave 0 |
| **RACE-03** | Retry on transient (mock anthropic.RateLimitError) succeeds | unit | `pytest tests/race/test_harness_concurrency.py::test_retry_transient -x` | ❌ Wave 0 |
| **RACE-03** | NO retry on InjectedFaultError (the test) | unit | `pytest tests/race/test_harness_concurrency.py::test_no_retry_injected -x` | ❌ Wave 0 |
| **RACE-03** | per_run_timeout=120 fires; emits done outcome=timeout | unit | `pytest tests/race/test_harness_concurrency.py::test_per_run_timeout -x` | ❌ Wave 0 |
| **RACE-03** | model=claude-sonnet-4-6, temperature=0 propagated | unit | `pytest tests/race/test_harness_concurrency.py::test_deterministic_args -x` | ❌ Wave 0 |
| **RACE-03** | Harness emits race_done event | integration | `pytest tests/race/test_harness_concurrency.py::test_race_done_emitted -x` | ❌ Wave 0 |
| **RACE-04** | Detector K=3 turn window observation | unit | `pytest tests/race/test_classifier_detector.py::test_k3_window -x` | ❌ Wave 0 |
| **RACE-04** | Detector observes via tool_error | unit | `pytest tests/race/test_classifier_detector.py::test_observe_tool_error -x` | ❌ Wave 0 |
| **RACE-04** | Detector observes via ack_msg | unit | `pytest tests/race/test_classifier_detector.py::test_observe_ack_msg -x` | ❌ Wave 0 |
| **RACE-04** | Detector observes via retry | unit | `pytest tests/race/test_classifier_detector.py::test_observe_retry -x` | ❌ Wave 0 |
| **RACE-04** | Regex FP <10% on 50-sample corpus | calibration | `pytest tests/race/test_classifier_detector.py::test_regex_fp_target -x` | ❌ Wave 0 (corpus fixture) |
| **RACE-04** | Negation guard drops "didn't fail" / "no error" | unit | `pytest tests/race/test_classifier_detector.py::test_negation_guard -x` | ❌ Wave 0 |
| **RACE-04** | All 5 terminal-state tags computed correctly | unit | `pytest tests/race/test_classifier_detector.py::test_terminal_states -x` | ❌ Wave 0 |
| **RACE-04** | 9 fictional traces (3 lanes × 3 fixtures) tag as expected | snapshot | `pytest tests/race/test_classifier_detector.py::test_assignment_traces -x` | ❌ Wave 0 |
| **RACE-05** | All 3 task_config.yaml load successfully at import | unit | `pytest tests/race/test_task_config_loader.py::test_v1_tasks_load -x` | ❌ Wave 0 |
| **RACE-05** | Unknown target raises ValidationError at startup | unit | `pytest tests/race/test_task_config_loader.py::test_unknown_target_rejected -x` | ❌ Wave 0 |
| **RACE-05** | Unknown bind raises ValidationError at startup | unit | `pytest tests/race/test_task_config_loader.py::test_unknown_bind_rejected -x` | ❌ Wave 0 |
| **RACE-05** | summarize_repo Haiku scorer 3/3 logic | unit (mocked judge) | `pytest tests/race/test_task_config_loader.py::test_summarize_scorer -x` | ❌ Wave 0 |
| **RACE-05** | negotiate_meeting structural-only (no Haiku call) | unit | `pytest tests/race/test_task_config_loader.py::test_negotiate_no_haiku -x` | ❌ Wave 0 |
| **RACE-05** | book_travel composite (structural AND Haiku) | unit (mocked judge) | `pytest tests/race/test_task_config_loader.py::test_book_travel_composite -x` | ❌ Wave 0 |
| **RACE-06** | 15-fixture snapshot test (5 templates × 3 lanes) | snapshot | `pytest tests/race/test_classifier_failure_mode.py -x` | ❌ Wave 0 |
| **RACE-06** | Tied-tags precedence rule | unit | `pytest tests/race/test_classifier_failure_mode.py::test_tie_precedence -x` | ❌ Wave 0 |
| **RACE-06** | lane_failed extension template | unit | `pytest tests/race/test_classifier_failure_mode.py::test_lane_failed -x` | ❌ Wave 0 |
| **RACE-06** | characteristic_event_phrase per lane | unit | `pytest tests/race/test_classifier_failure_mode.py::test_characteristic_phrase -x` | ❌ Wave 0 |
| **RACE-07** | GitHub mock: 5 fixture repos load | unit | `pytest tests/race/test_mocks_chokepoint.py::test_github_5_repos -x` | ❌ Wave 0 |
| **RACE-07** | Calendar mock: 3 fixture calendars | unit | `pytest tests/race/test_mocks_chokepoint.py::test_calendar_3 -x` | ❌ Wave 0 |
| **RACE-07** | Travel mock: search + book + inventory | unit | `pytest tests/race/test_mocks_chokepoint.py::test_travel_search_book -x` | ❌ Wave 0 |
| **RACE-07** | Single fault chokepoint grep extends to mcp_servers/race_*.py | grep | `pytest tests/race/test_iron_rule_grep.py::test_no_mutation_in_race_servers -x` | ⚠ extend |
| **D-40** | Wasted-tokens computed from trace at fault_observed | unit | `pytest tests/race/test_metrics_wasted_tokens.py -x` | ❌ Wave 0 |
| **D-40** | Wasted-tokens null for non-OBSERVED tags | unit | `pytest tests/race/test_metrics_wasted_tokens.py::test_null_for_kept_going -x` | ❌ Wave 0 |
| **D-42** | Haiku judge respects temperature=0 | unit (mocked SDK) | `pytest tests/race/test_judge_determinism.py::test_temp_zero -x` | ❌ Wave 0 |
| **D-42** | Haiku judge marks system prompt with cache_control | unit (assert SDK call args) | `pytest tests/race/test_judge_determinism.py::test_cache_control -x` | ❌ Wave 0 |

### Sampling rate

- **Per task commit:** `pytest tests/race/ -x` (target <30s wall clock)
- **Per wave merge:** `pytest` (full suite — race + Phase 6 regression + v1 demo regression)
- **Phase gate:** Full suite green; the 9-fictional-trace snapshot signed off; regex FP target met on 50-sample corpus.

### Wave 0 gaps

- [ ] `tests/race/conftest.py` — shared fixtures: `make_recorder(run_id, lane)`, `mock_anthropic_async()`, `clean_runs_dir()`.
- [ ] `tests/race/fixtures/classifier_traces/*.json` — 9 fictional traces (3 lanes × 3 task scenarios), authored verbatim from master design §The Assignment.
- [ ] `tests/race/fixtures/recovery_regex_corpus.jsonl` — 50 hand-labeled samples (eng-review test plan unchanged from iter 1).
- [ ] `data/race/fixtures/{github,calendar,travel}/*.json` — mock fixture data.
- [ ] All test files listed in §1 layout — no test infrastructure exists for race-runner-level testing yet (Phase 6 covers schema + ws + IRON RULE only).

---

## 9. Risks + Mitigations

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Harness rate-limit blowup at n=5** (15 concurrent calls × ~5k input tokens each → 75k ITPM exceeds 30k Tier 1) | HIGH | `Semaphore(8)` caps at 8 in-flight; staggered start. Surface `RACE_HARNESS_CONCURRENCY` env var for Tier 2+ machines. Retry classifier handles real 429s with backoff. |
| **Anthropic SDK has no `seed` parameter — non-determinism at temperature=0** | MEDIUM | Disclosed in master design §T4; structural rubrics (count rubric items, not prose) are robust to ±1 token variance. Methodology footer publishes the "seed=42" stamp as documentation only. |
| **Haiku 4.5 cache minimum is 2,048 tokens; summarize_repo rubric is ~400 tokens** | LOW | Pad rubrics with stable preamble to clear the threshold; OR accept no caching on small rubrics (still works correctly, just costlier). Document in `judges/haiku.py` docstring. |
| **A2A handler fault chokepoint drift** (a developer adds a handler that mutates a response without `inject_fault()`) | HIGH | Phase 6 D-13 grep extends to `mcp_servers/race_*.py` AND any A2A handler module. CI test `test_iron_rule_grep.py::test_no_mutation_in_race_servers`. |
| **Replay-symmetry violation** (Detector behaves differently in replay vs live) | HIGH | Same Detector class consumed by both paths. Phase 9 HEAT-03 fixture asserts identical tags. Phase 7 plants the fixture (saves a known run + its expected tags) so Phase 9 has the data to test. |
| **Negation guard false-negative** ("I cannot retry this 429") | MEDIUM | Master design Reviewer Concern #1. Phase 7 measures FN alongside FP on the 50-sample corpus; >5% FN re-opens regex. TODO 10 captures full LLM-judge replacement. |
| **`run_id` collision across concurrent harness invocations** | LOW | Phase 6 D-02 mints `run_id` in harness via `uuid.uuid4().hex`; collision probability ~0. |
| **`_ACTIVE_FAULTS` module-level dict pollutes across runs** | MEDIUM | Use `contextvars.ContextVar` instead of module dict — per-run isolation by construction. Document in `race/mocks/__init__.py`. |
| **Anthropic SDK not installed; Phase 7 cannot run live** | HIGH | Add `anthropic>=0.40` to `pyproject.toml [project] dependencies`. Wave 0 task. CI tests use `unittest.mock.patch("anthropic.AsyncAnthropic")` to avoid live keys. |
| **D-24 typo: CONTEXT.md says `broker.send_message`; actual method is `broker.send_task`** | LOW | Surface to planner; correct in plan docs. Code uses `send_task`. |
| **15 LOC mutation to `mcp/client.py:SERVER_BUILDERS` registry to register race servers** | LOW | Use `transport="stdio"` for race servers — `SERVER_BUILDERS` is bypassed for stdio. Zero mutation to existing code. |

---

## 10. Open Questions for Planner

All questions below are surfaced for **planner awareness**, not blockers. Each has a recommended resolution; planner can ratify or override.

1. **Q: Should `mcp_servers/race_*.py` share a common `_RaceServerBase` builder?**
   Recommendation: NO. Three independent modules (~30 LOC each) following `db_server.py` shape verbatim. Common base = abstraction that doesn't pay for itself at v1 surface.

2. **Q: How does `_ACTIVE_FAULTS` reach the mock?**
   Recommendation: `contextvars.ContextVar` per `(run_id, lane)`. Set by runner before invoking transport; read by mock at fault dispatch. Cleaner than threading state through MCP/A2A which weren't designed for it.

3. **Q: Is `run_pure_mcp` a coroutine `async def` or sync `def`?**
   Recommendation: `async def` to match Anthropic AsyncAnthropic client. The MCPClient itself is sync (uses `anyio.run` internally per `mcp/client.py:116`); the runner wraps `client.call(...)` in `asyncio.to_thread()` if needed.

4. **Q: Where does the harness's `model_prices.yaml` live (master design §Cost model)?**
   Recommendation: `src/a2a_vs_mcp/race/model_prices.yaml`, alongside types. Cost computation is a small helper in `race/metrics.py`. v1 doesn't surface cost in headlines (master design: "wasted_tokens" is the surfaced metric).

5. **Q: Is `failure_mode_classifier` invoked by the harness or by Phase 8 UI?**
   Recommendation: Harness calls it once after `race_done` to populate per-lane headlines into the final `RaceResult` set — written to disk. UI (Phase 8) reads from disk. Phase 7 ships the data; Phase 8 renders.

6. **Q: Should the harness emit `tick` events at all, or only the runners?**
   Recommendation: Runners emit ticks (they own the per-lane time/token budget). Harness emits only `race_done`. Matches Phase 6 D-08 NEVER_COALESCE membership.

7. **Q: How does `score_pass` reach the Detector at `done` time?**
   Recommendation: Runner computes ScoreCard via per-task `score()` (which may call Haiku); on success/failure, runner calls `detector.finalize_at_done(score_pass)` for each live detector. Then runner records `done` event with the ScoreCard.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python ≥3.10 | Race code | ✓ | 3.10+ (pyproject pinned) | — |
| `pytest>=8.0` | All race tests | ✓ | dev extras | — |
| `pytest-asyncio>=0.24` | async runner tests | ✓ | dev extras | — |
| `mcp[cli]>=1.27` | race MCP servers | ✓ | already pinned | — |
| `pydantic>=2.x` | TaskConfig + failure_script validators | ✓ (transitively via fastapi/mcp) | — | — |
| `pyyaml` | task_config.yaml loader | ⚠ (transitively via fastapi?) | unverified | Add explicit dep |
| **`anthropic`** | Sonnet runner LLM, Haiku judge | ✗ | — | **None — must add to pyproject** |
| `a2a-sdk[http-server]` | A2A broker (already used by v1) | ✓ (optional dep) | 0.3.26 | — |

**Missing dependencies with no fallback:**
- `anthropic>=0.40` — REQUIRED. Wave 0 task: `pip install anthropic` → add to `pyproject.toml [project] dependencies`. Tests mock the SDK client to avoid live API key.

**Missing dependencies with fallback:**
- `pyyaml` — verify with `python -c "import yaml"` at Wave 0. If missing, add explicitly. Likely present transitively but should be a direct dep since `task_config.yaml` is a v2.0 first-class file format.

**Required environment variable for live runs:**
- `ANTHROPIC_API_KEY` — set on demo machine. Tests run without it (mocked SDK).

---

## Validation Architecture (Nyquist)

> nyquist_validation enabled (no explicit override in `.planning/config.json`).

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.0 + pytest-asyncio 0.24 |
| Config file | pyproject.toml `[tool.pytest.ini_options]` |
| Quick run | `pytest tests/race/ -x` |
| Full suite | `pytest` |

### Phase Requirements → Test Map

See §8 above (full table). Coverage: 7/7 RACE requirements, plus D-40 (wasted tokens) and D-42 (judge determinism). All Phase 6 tests stay green (regression check).

### Sampling Rate

- **Per task commit:** quick race-only run.
- **Per wave merge:** full suite.
- **Phase gate:** full suite green; 9-fictional-trace snapshot accepted; regex FP <10% on 50-sample corpus.

### Wave 0 Gaps

- [ ] `tests/race/conftest.py` — recorder factory, runs-dir cleaner, mock SDK fixture
- [ ] `tests/race/fixtures/classifier_traces/*.json` — 9 fictional traces (3 lanes × 3 trace patterns from master design §The Assignment)
- [ ] `tests/race/fixtures/recovery_regex_corpus.jsonl` — 50 hand-labeled samples (carry-over from eng-review test plan iter 1)
- [ ] `data/race/fixtures/{github,calendar,travel}/*.json` — mock fixture data (5 repos, 3 calendars, travel inventory)
- [ ] Add `anthropic>=0.40` and explicit `pyyaml` to `pyproject.toml`
- [ ] Test files listed in §1 (12 new test_*.py files under `tests/race/`)

---

## Sources

### Primary (HIGH confidence)

- `.planning/phases/07-race-backend-lanes-harness-recovery/07-CONTEXT.md` — D-19..D-43 locked decisions
- `.planning/phases/06-tracerecorder-schema-gate-race-foundation/06-CONTEXT.md` — Phase 6 inheritance
- `~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-design-20260427-193227.md` §High-Level Architecture, §Recovery detection, §task_config.yaml, §failure_mode_classifier, §Cost model, §Tasks, §The Assignment
- `~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-eng-review-test-plan-20260427-224635.md` — recovery state-machine fixtures, K=3 FP target, hardness coverage, harness deterministic-seed test, hybrid_plan branching tests
- `src/a2a_vs_mcp/race/{schemas,turn,failure,runs,replay,ws}.py` — Phase 6 substrate read in full
- `src/a2a_vs_mcp/mcp/client.py` — MCPClient.call() signature + transport modes
- `src/a2a_vs_mcp/a2a/broker.py` — `send_task` (NOT `send_message`) + `register(card, handler)` + `handle_task` contract
- `src/a2a_vs_mcp/mcp_servers/{db_server,docs_server}.py` — FastMCP template shape
- `src/a2a_vs_mcp/reasoning.py` — verified OpenAI-bound (D-42 reuse rejected)
- `src/a2a_vs_mcp/trace.py` — TraceRecorder constructor + ndjson hook

### Secondary (MEDIUM confidence — official docs verified via search)

- [Anthropic API Rate Limits](https://platform.claude.com/docs/en/api/rate-limits) — Tier 1 default 50 RPM / 30k ITPM / 8-10k OTPM for Sonnet 4.x; Sonnet 4.6/4.5/4 share bucket
- [Anthropic Prompt Caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching) — `cache_control: {type: "ephemeral"}`; Haiku 4.5 minimum 2,048 tokens; cache-read 0.1× base price
- [Claude API Quota Tiers and Limits Explained 2026](https://www.aifreeapi.com/en/posts/claude-api-quota-tiers-limits) — confirms Tier 1/3/4 specifics
- [TokenCalculator: Claude API Rate Limits April 2026](https://tokencalculator.com/blog/claude-api-rate-limits-april-2026) — corroborates Tier 1 defaults

### Tertiary (LOW confidence — flagged for re-validation if used live)

- Sonnet 4.x output tokens "8,000–10,000" range — sources disagree on exact value (8k vs 10k); planner can lock to whichever is current at demo machine's tier. Either way, `Semaphore(8)` is conservative.

### Negative claims (verified)

- **Anthropic Messages API has NO seed parameter** — verified across [theneuralbase.com](https://theneuralbase.com/anthropic/qna/how-to-set-temperature-in-claude-api/), [unstract.com](https://unstract.com/blog/understanding-why-deterministic-output-from-llms-is-nearly-impossible/), [vincentschmalbach.com](https://www.vincentschmalbach.com/does-temperature-0-guarantee-deterministic-llm-outputs/), and the absence of any `seed` parameter in the [anthropic-sdk-python repository](https://github.com/anthropics/anthropic-sdk-python). The master design's `seed=42` is documentation/methodology only.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | Demo machine runs at Tier 1 (50 RPM, 30k ITPM) | §2 D-38 | If actually Tier 2+, `Semaphore(8)` is over-conservative; can raise to 16. Cost: slower demo, no correctness impact. |
| A2 | Sonnet output bursts ~1,500 tokens per run | §2 D-38 | If runs produce 3k+ output tokens, OTPM exceeds Tier 1 ceiling even at 8 concurrent. Mitigation: lower N to 5, or restrict `max_tokens`. |
| A3 | Anthropic SDK 0.40+ supports `cache_control` and Haiku 4.5 | §3 D-42 | If SDK version differs, syntax may change. Pin tested version. |
| A4 | `pyyaml` is transitively available | §Environment | Could be absent; Wave 0 verifies. |
| A5 | `mcp/client.py:SERVER_BUILDERS` is bypassed for `transport="stdio"` | §5 | Verified via reading `mcp/client.py:160-167` (stdio path uses `_build_stdio_params` not `SERVER_BUILDERS`). HIGH confidence. |
| A6 | A2A broker's `handle_task` is the canonical handler entry point | §5 | Verified via `broker.py:226` (`handler.handle_task(message)` invocation). HIGH confidence. |
| A7 | Wasted-tokens trace fields (`tokens_in`, `tokens_out`, `t_call_start_ms`) are populated by Phase 6 TraceRecorder | §6 | Phase 6 D-03 + TRC-01 lock these — but Phase 6 doesn't add an `llm_call` event type; runners must emit it explicitly. Surface to planner: define `llm_call` event schema in Phase 7. |
| A8 | The 9 fictional traces from master design §The Assignment are the planner's responsibility to author into `tests/race/fixtures/classifier_traces/` | §8 Wave 0 | Master design says "Day 0 spike" should produce them — Phase 7 takes over that responsibility since spike is rolled into the phase. |
| A9 | `seed=42` in trace metadata is a documentation field, NOT passed to Anthropic SDK | §3 D-42 | Verified via Anthropic SDK source (no seed param). Methodology footer surfaces it; SDK never sees it. |

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Phase 6 substrate + transport contracts read in full
- Architecture: HIGH — package layout follows established conventions
- Pitfalls: HIGH — eng-review test plan + master design Reviewer Concerns provide explicit list
- D-38 resolution: HIGH — rate limits verified at multiple sources
- D-42 resolution: HIGH — Anthropic SDK seed absence verified, prompt caching docs read
- ExecutionContext shape: MEDIUM — proposed minimal TypedDict; planner may expand if hybrid v1 needs more state

**Research date:** 2026-04-28
**Valid until:** 2026-05-28 (30 days for stable; rate-limit numbers and SDK behavior shift on Anthropic platform side)

---

## RESEARCH COMPLETE

**Phase:** 7 — Race Backend — Lanes, Harness, Recovery State Machine
**Confidence:** HIGH

### Key Findings

- **D-38 closed:** `asyncio.Semaphore(8)` with transient-only retry classifier (HTTP 5xx + 429 + connection-reset). Custom `InjectedFaultError` to distinguish injected 429s from real ones — minor Phase 6 update needed.
- **D-42 closed:** New `race/judges/haiku.py` module (NOT reuse of `reasoning.py` — that's OpenAI-bound and would force SupportTicket abstraction onto race per D-19). Anthropic prompt caching (ephemeral, 5-min) on rubric system prompts. **Anthropic SDK has NO seed parameter** — `seed=42` is methodology disclosure only.
- **ExecutionContext** lives in `race/types.py` as a `TypedDict`; binds resolve via `BINDS[step.bind](ctx)`.
- **Detector + failure_mode_classifier** co-located in `race/classifier.py`; characteristic_event counts derived at headline-render time from trace fields (`tool_call.tool_name`, `agent_msg.message_type`, etc.) — never stored.
- **Per-task callable registries** validated via Pydantic at first import of `race.tasks` — typo in `target` or `bind` → import-time `ValidationError`, breaks `pytest --collect-only` per eng-review Critical Path #9.
- **Single fault chokepoint** (D-25) extends Phase 6 D-13 grep to `mcp_servers/race_*.py`. The `_ACTIVE_FAULTS` registry uses `contextvars.ContextVar` per (run_id, lane) — not a module-level dict — for safe concurrent runs.
- **Anthropic SDK is NOT installed** — Wave 0 must add `anthropic>=0.40` to `pyproject.toml`.
- **CONTEXT.md D-24 typo:** `broker.send_message` should read `broker.send_task` (verified via `a2a/broker.py:61`).

### Confidence Assessment

| Area | Level | Reason |
|------|-------|--------|
| Standard stack | HIGH | Phase 6 substrate read; transport contracts verified |
| Architecture | HIGH | Layout follows project conventions; module sizes pre-budgeted |
| D-38 (concurrency) | HIGH | Rate limits cross-verified at 4 sources; Semaphore(8) leaves OTPM headroom |
| D-42 (judge integration) | HIGH | Anthropic SDK seed absence + prompt caching mechanics verified at official docs |
| Recovery classifier | HIGH | Master design pseudocode + regex are verbatim-locked; algorithm is deterministic |
| Validation architecture | HIGH | Test list maps 1:1 to RACE-01..07 + eng-review test plan |
| Pitfalls / risks | HIGH | Eng-review test plan + master design Reviewer Concerns are explicit |

### Ready for Planning

Research complete. Planner can now:
- Decompose Phase 7 into ~4 waves (types/registries → mocks/transport → runners/harness → classifier/scorers).
- Lock `Semaphore(8)`, `anthropic>=0.40`, `race/judges/haiku.py` module location.
- Author 12 new test files mapped to RACE-01..07 + D-40 + D-42.
- Plant the 9-fictional-trace fixtures + 50-sample regex corpus in Wave 0.

Sources:
- [Anthropic Rate Limits](https://platform.claude.com/docs/en/api/rate-limits)
- [Anthropic Prompt Caching](https://docs.claude.com/en/docs/build-with-claude/prompt-caching)
- [Claude API Quota Tiers 2026](https://www.aifreeapi.com/en/posts/claude-api-quota-tiers-limits)
- [TokenCalculator: Claude Rate Limits April 2026](https://tokencalculator.com/blog/claude-api-rate-limits-april-2026)
- [Determinism nearly impossible (LLM outputs)](https://unstract.com/blog/understanding-why-deterministic-output-from-llms-is-nearly-impossible/)
- [Anthropic temperature behavior](https://theneuralbase.com/anthropic/qna/how-to-set-temperature-in-claude-api/)
