# Phase 7: Race Backend — Lanes, Harness, Recovery State Machine - Pattern Map

**Mapped:** 2026-04-28
**Files analyzed:** 30 NEW backend files + 6 NEW fixture/data files + 12 NEW test files + 1 modified config
**Analogs found:** 26 / 30 backend files (4 have no in-repo analog and reference RESEARCH.md)

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/a2a_vs_mcp/race/types.py` | model (dataclass + StrEnum + TypedDict) | transform | `src/a2a_vs_mcp/race/schemas.py` (Phase 6) + `src/a2a_vs_mcp/schemas.py` (FailureConfig) | exact |
| `src/a2a_vs_mcp/race/runners/__init__.py` | package init / re-exports | n/a | `src/a2a_vs_mcp/race/__init__.py` (Phase 6) | exact |
| `src/a2a_vs_mcp/race/runners/pure_mcp.py` | runner / orchestrator | request-response (LLM↔MCPClient↔mock) | `src/a2a_vs_mcp/agents/single_agent.py` (shape only — D-19 forbids subclass) + `src/a2a_vs_mcp/mcp/client.py` (call shape) | role-match |
| `src/a2a_vs_mcp/race/runners/pure_a2a.py` | runner / orchestrator | event-driven (broker.send_task) | `src/a2a_vs_mcp/agents/triage.py` (shape only) + `src/a2a_vs_mcp/a2a/broker.py` (`register` + `send_task`) | role-match |
| `src/a2a_vs_mcp/race/runners/hybrid.py` | runner (pre-scripted plan executor) | event-driven branching | `src/a2a_vs_mcp/agents/hybrid_specialists.py` (shape only) + `src/a2a_vs_mcp/race/turn.py` (dispatch-table pattern) | role-match (no analog for `on_fault` branching — see RESEARCH §4) |
| `src/a2a_vs_mcp/race/harness.py` | service (concurrency driver) | batch / pub-sub | RESEARCH §2 (no in-repo asyncio.Semaphore analog; `a2a/broker.py:send_tasks_parallel` is the closest concurrency primitive) | partial — RESEARCH-driven |
| `src/a2a_vs_mcp/race/classifier.py` | service (state machine + pure fn) | transform | `src/a2a_vs_mcp/race/turn.py` (dispatch-table pattern) + `src/a2a_vs_mcp/race/failure.py` (module-load constant + helper) | role-match |
| `src/a2a_vs_mcp/race/metrics.py` | utility (pure functions over events) | transform | `src/a2a_vs_mcp/evidence.py` (module-level helpers, no class) + `src/a2a_vs_mcp/race/runs.py` (event-list iteration) | role-match |
| `src/a2a_vs_mcp/race/judges/__init__.py` | package init | n/a | `src/a2a_vs_mcp/race/__init__.py` | exact |
| `src/a2a_vs_mcp/race/judges/haiku.py` | service (LLM client wrapper) | request-response | RESEARCH §3 (no in-repo Anthropic analog; `reasoning.py` is OpenAI-only and D-19 forbids reuse) | partial — RESEARCH-driven |
| `src/a2a_vs_mcp/race/mocks/github.py` | adapter (fixture-backed mock) | file-I/O + transform | `src/a2a_vs_mcp/evidence.py` (db_path-bound helpers) + `src/a2a_vs_mcp/race/failure.py:inject_fault` (chokepoint) | role-match |
| `src/a2a_vs_mcp/race/mocks/calendar.py` | adapter (fixture-backed mock) | file-I/O + transform | same as `mocks/github.py` | role-match |
| `src/a2a_vs_mcp/race/mocks/travel.py` | adapter (fixture-backed mock) | file-I/O + transform | same as `mocks/github.py` | role-match |
| `src/a2a_vs_mcp/race/tasks/summarize_repo/__init__.py` | registry module + scorer | transform | `src/a2a_vs_mcp/race/failure.py` (module-level enum/registry + Pydantic validator) + `src/a2a_vs_mcp/config.py` (PROFILES dict registry) | role-match |
| `src/a2a_vs_mcp/race/tasks/summarize_repo/task_config.yaml` | config / data | n/a | `REMOTE_A2A_REGISTRY.json` / `REMOTE_MCP_REGISTRY.json` (root JSON registries) — for layout idiom only; YAML content is verbatim from master design | partial |
| `src/a2a_vs_mcp/race/tasks/negotiate_meeting/__init__.py` | registry module + scorer | transform | same as summarize_repo | role-match |
| `src/a2a_vs_mcp/race/tasks/negotiate_meeting/task_config.yaml` | config / data | n/a | same | partial |
| `src/a2a_vs_mcp/race/tasks/book_travel/__init__.py` | registry module + scorer | transform | same | role-match |
| `src/a2a_vs_mcp/race/tasks/book_travel/task_config.yaml` | config / data | n/a | same | partial |
| `src/a2a_vs_mcp/race/tasks/loader.py` (D-28 surface) | utility (Pydantic loader) | transform | `src/a2a_vs_mcp/race/failure.py` (`_SCRIPT_ADAPTER` + `validate_failure_script`) | exact |
| `src/a2a_vs_mcp/mcp_servers/race_github.py` | MCP server (FastMCP) | request-response | `src/a2a_vs_mcp/mcp_servers/db_server.py` + `docs_server.py` | exact |
| `src/a2a_vs_mcp/mcp_servers/race_calendar.py` | MCP server (FastMCP) | request-response | same | exact |
| `src/a2a_vs_mcp/mcp_servers/race_travel.py` | MCP server (FastMCP) | request-response | same | exact |
| `src/a2a_vs_mcp/race/failure.py` (delta — add `InjectedFaultError`) | model (exception class) | n/a | `src/a2a_vs_mcp/race/failure.py` (existing module — patch in same module) | exact |
| `data/race/fixtures/github_repos.json` | data / seed fixtures | n/a | `src/a2a_vs_mcp/data/seeds/customers.json` (JSON seed shape) | exact |
| `data/race/fixtures/calendars.json` | data / seed fixtures | n/a | same | exact |
| `data/race/fixtures/travel.json` | data / seed fixtures | n/a | same | exact |
| `tests/race/test_runner_pure_mcp.py` | test (integration) | n/a | `tests/race/test_inject_fault.py` (unittest layout, race-recorder helper) | exact |
| `tests/race/test_runner_pure_a2a.py` | test (integration) | n/a | same | exact |
| `tests/race/test_runner_hybrid.py` | test (integration, on_fault branches) | n/a | same | exact |
| `tests/race/test_harness.py` | test (concurrency, mocked SDK) | n/a | `tests/race/test_inject_fault.py` + RESEARCH §8 (mocked AsyncAnthropic) | role-match |
| `tests/race/test_classifier_detector.py` | test (state machine + regex FP) | n/a | `tests/race/test_inject_fault.py` (FaultKind enum loop pattern) | exact |
| `tests/race/test_classifier_regex.py` | test (corpus-based) | n/a | same | exact |
| `tests/race/test_failure_mode_classifier.py` | test (snapshot, 15 fixtures) | n/a | same | exact |
| `tests/race/test_metrics.py` | test (unit, pure fn) | n/a | same | exact |
| `tests/race/test_haiku_judge.py` | test (mocked Anthropic SDK) | n/a | same + `unittest.mock.patch` for `anthropic.Anthropic` | role-match |
| `tests/race/test_task_registries.py` | test (Pydantic ValidationError startup) | n/a | `tests/race/test_inject_fault.py::PydanticValidatorTests` (lines 87-96) | exact |
| `tests/race/test_hardness_coverage.py` | test (data assertion) | n/a | same | exact |
| `tests/race/test_mocks_chokepoint.py` | test + extension of grep test | n/a | `tests/race/test_iron_rule_grep.py` (existing — extend, do not replace) | exact |
| `tests/race/fixtures/classifier_traces/` (9 JSON traces) | test fixtures | n/a | `tests/race/fixtures/` (existing — Phase 6 fixtures live here) | exact |
| `tests/race/fixtures/recovery_regex_corpus.jsonl` | test fixture (50-sample corpus) | n/a | same | exact |
| `pyproject.toml` (modified — add `anthropic>=0.40`) | config | n/a | existing `pyproject.toml` `[project] dependencies` block | exact |

---

## Pattern Assignments

### `src/a2a_vs_mcp/race/types.py` (model — dataclass + StrEnum + TypedDict)

**Analog:** `src/a2a_vs_mcp/race/schemas.py` (Phase 6) — same package idiom + `src/a2a_vs_mcp/schemas.py:30-92` for the project's broader dataclass+`to_dict()` idiom.

**Module-header pattern** (`race/schemas.py` lines 1-10):
```python
"""Wire-format dataclasses for /api/race/ws (TRC-04, D-06).

Every event carries lane + turn_index per D-15/D-17. Plain @dataclass + to_dict()
mirrors src/a2a_vs_mcp/schemas.py:30-92 idiom (Pydantic is reserved for api_schemas.py).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, ClassVar
```

**Dataclass + `to_dict()` pattern** (`race/schemas.py` lines 24-33):
```python
@dataclass
class TickEvent:
    lane: str
    turn_index: int
    task_id: str
    t_ms: int
    event_type: ClassVar[str] = "tick"
    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, **asdict(self)}
```

**StrEnum pattern (3.10-safe analog)** — copy from `race/failure.py:27-32`:
```python
# 3.10-safe StrEnum analog (RESEARCH.md Pitfall 6 — pyproject.toml pins >=3.10).
class FaultKind(str, Enum):
    RATE_LIMIT_429 = "rate_limit_429"
    PARTIAL_JSON = "partial_json"
    ...
```

Apply to `HardnessType` verbatim per RESEARCH §4 (string subclass + `Enum`, NOT `enum.StrEnum`).

**TypedDict choice for `ExecutionContext`** — RESEARCH §1 explicitly recommends `TypedDict, total=False` (not dataclass) since the dict is mutated in-flight by the hybrid runner. No in-repo TypedDict analog exists; this is RESEARCH-driven.

---

### `src/a2a_vs_mcp/race/runners/pure_mcp.py` (runner — request-response)

**Analog:** `src/a2a_vs_mcp/mcp/client.py` for the `call(tool, arguments)` shape; `src/a2a_vs_mcp/race/failure.py` for IRON-RULE-conforming module docstring.

**MCPClient construction + call pattern** (`mcp/client.py` lines 30-49 + 102-119):
```python
client = MCPClient(
    server_module="a2a_vs_mcp.mcp_servers.race_github",
    trace=recorder,
    project_root=PROJECT_ROOT,
    failure_config=None,                  # NOT used in race
    transport="in_process",               # demo profile default
)
result = client.call("get_repo_metadata", {"repo_id": "demo-org/demo-repo"})
```

**Critical:** pass `failure_config=None` — `MCPClient._simulate_failure` (lines 306-310) is wired to v1 `FailureConfig`. Race faults flow through `inject_fault()` chokepoint inside `race/mocks/*`.

**Detector wiring pattern** (RESEARCH §6, no in-repo analog yet — Phase 7 plants it):
```python
detectors: list[Detector] = []
def on_fault_injected(event: dict) -> None:
    detectors.append(Detector(
        fault_id=event["fault_id"],
        fault_kind=event["fault_kind"],
        target=event["target"],
        fault_inject_turn=event["turn_index"],
    ))
def on_event(event: dict) -> None:
    for d in detectors:
        if d.consume(event):
            wasted = compute_wasted_tokens(recorder.events, d.fault_id, lane)
            recorder.record("fault_observed", fault_id=d.fault_id, ...,
                            wasted_tokens_before_detection=wasted)
```

**Locked signature** (D-20, RESEARCH §4):
```python
async def run_pure_mcp(
    task_spec: TaskSpec,
    run_id: str,
    recorder: TraceRecorder,
    failure_script: list[FailureScriptEntry],
    sonnet_client: anthropic.AsyncAnthropic,
) -> RaceResult: ...
```

**Module-level functions, not classes** — matches `src/a2a_vs_mcp/evidence.py` (no `EvidenceService` class).

---

### `src/a2a_vs_mcp/race/runners/pure_a2a.py` (runner — event-driven)

**Analog:** `src/a2a_vs_mcp/a2a/broker.py` lines 26-59 (`A2ABroker.__init__` + `register` + `find_by_capability`) and lines 61-142 (`send_task` lifecycle).

**Broker construction + handler registration pattern** (`broker.py` lines 26-53):
```python
broker = A2ABroker(trace=recorder)            # trace = lane recorder
card = AgentCard(agent_id="race_github_agent",
                 capabilities=["fetch_repo_metadata"], ...)
broker.register(card, FixtureBackedAgentHandler("fetch_repo_metadata", recorder, run_id))
```

**Send pattern (NOTE: method is `send_task`, NOT `send_message` — CONTEXT.md D-24 is a typo, RESEARCH §5 confirms)** (`broker.py` line 61):
```python
result = broker.send_task(A2AMessage(
    sender_agent="race_lead",
    target_agent="race_github_agent",
    capability="fetch_repo_metadata",
    payload={"repo_id": "demo-org/demo-repo"},
    ...
))
```

**Handler `handle_task` contract** (verified from `broker.py` lines 206-231 — handler is invoked inside `_execute_with_timeout` ThreadPoolExecutor):
```python
class FixtureBackedAgentHandler:
    def __init__(self, capability: str, recorder: TraceRecorder, run_id: str) -> None:
        self.capability = capability
        self.recorder = recorder
        self.run_id = run_id

    def handle_task(self, message: A2AMessage) -> AgentResult:
        # Faults flow through race.mocks.* (inject_fault chokepoint).
        ...
        return AgentResult(agent_id=..., summary=..., details=..., confidence=1.0, status="completed")
```

---

### `src/a2a_vs_mcp/race/runners/hybrid.py` (runner — pre-scripted plan executor)

**Analog:** `src/a2a_vs_mcp/race/turn.py` (dispatch table pattern); the `on_fault` branching has no in-repo analog (Phase 7 introduces it).

**Dispatch-table pattern** (`race/turn.py` lines 9-14):
```python
TURN_DEFINING_EVENTS: dict[str, set[str]] = {
    "pure_mcp": {"tool_call"},
    "pure_a2a": {"agent_msg"},
    "hybrid": {"tool_call", "agent_msg"},
}
```

Apply same shape to `on_fault` dispatch in `race/runners/hybrid.py` (RESEARCH §4):
```python
async def _execute_step(step: HybridStep, ctx: ExecutionContext, ...) -> Any:
    try:
        return await _dispatch_step(step, ctx)
    except InjectedFaultError as exc:
        if step.on_fault == "retry_once":
            try:
                return await _dispatch_step(step, ctx)
            except InjectedFaultError:
                raise
        elif step.on_fault == "delegate":
            return await _dispatch_step(_delegate_alt_step(step), ctx)
        elif step.on_fault == "abort":
            raise
        elif step.on_fault == "continue":
            return None  # the "kept_going_without_noticing" path
```

**ExecutionContext placement** — `race/types.py`, NOT here (RESEARCH §1 — task `__init__.py` files import it; placing in `runners/hybrid.py` would force tasks to import a runner module).

---

### `src/a2a_vs_mcp/race/harness.py` (service — concurrency driver)

**Analog:** No in-repo asyncio.Semaphore pattern; `a2a/broker.py:144-179 (send_tasks_parallel)` is the closest in-repo concurrency primitive (uses `ThreadPoolExecutor`). Phase 7 introduces asyncio.

**Threading-Lock arbiter pattern** (mirror from `race/runs.py` lines 41-70 — for module-singleton state):
```python
# Module-level registries (process-singleton per run_id).
_WRITERS: dict[str, "RunWriter"] = {}
_REGISTRY_LOCK = threading.Lock()
```

**RESEARCH-driven (no in-repo analog)** — RESEARCH §2 mandates:
```python
# race/harness.py
import asyncio
import anthropic

HARNESS_CONCURRENCY: int = int(os.getenv("RACE_HARNESS_CONCURRENCY", "8"))
_SEMAPHORE = asyncio.Semaphore(HARNESS_CONCURRENCY)

TRANSIENT_RETRY_TYPES: tuple[type[Exception], ...] = (
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.InternalServerError,
    anthropic.RateLimitError,    # real Anthropic 429 — NOT injected
)

# NEVER retry InjectedFaultError (the test).
```

**Per-run timeout** — `asyncio.wait_for(run_coroutine, timeout=120)` per (lane, run_idx). `120s` locked from D-39.

**`race_done` emission** — harness owns this single event per master design + Phase 6 NEVER_COALESCE membership.

---

### `src/a2a_vs_mcp/race/classifier.py` (service — state machine + pure fn)

**Analog:** `race/turn.py` for the "module-load constant + helper" idiom; `race/failure.py` for the "Pydantic validator at module load" pattern.

**Module-load compiled regex** — RESEARCH §6 (no in-repo regex analog; closest is `race/turn.py:10` module-level dict):
```python
_ACK_FAULT_REGEX = re.compile(r"\b(error|errors|...)\b", re.IGNORECASE)
_NEGATION_TOKENS = re.compile(r"\b(no|not|without|never|...)\b", re.IGNORECASE)
_NEGATION_FAULT_TOKENS = re.compile(r"\b(error|fail|...)\b", re.IGNORECASE)
_SENTENCE_SPLIT = re.compile(r"[.!?]")
```

**Detector dataclass shape** (mirror `race/failure.py:36-44` + RESEARCH §6):
```python
@dataclass
class Detector:
    fault_id: str
    fault_kind: str
    target: str
    fault_inject_turn: int
    K: int = K_DEFAULT
    state: DetectorState = DetectorState.AWAITING_OBSERVATION
    t_observed_ms: int | None = None
    evidence_kind: str | None = None
```

**`failure_mode_classifier` 6-template dispatcher** — RESEARCH §6 lines 900-924, locked verbatim from master design.

---

### `src/a2a_vs_mcp/race/metrics.py` (utility — pure fns over events)

**Analog:** `src/a2a_vs_mcp/evidence.py` (module-level helpers, no class) — same idiom mandated by RESEARCH §10 Q3.

**Module-level helper pattern** (matches the `evidence.get_customer_profile(db_path, ...)` shape — first-arg is the data, second-arg+ are query keys):
```python
# race/metrics.py
import statistics

def median_retries(events: list[dict], fault_id: str, target: str) -> int:
    fi = next((e for e in events if e.get("event_type") == "fault_injected"
               and e.get("fault_id") == fault_id), None)
    if not fi:
        return 0
    inject_turn = fi.get("turn_index", -1)
    return sum(
        1 for e in events
        if e.get("event_type") == "tool_call"
        and e.get("tool_name") == target
        and e.get("turn_index", -1) > inject_turn
    )

def compute_wasted_tokens(events: list[dict], fault_id: str, lane: str) -> int: ...
def median_delegations(events: list[dict], fault_id: str) -> int: ...
def median_switches(events: list[dict], fault_id: str) -> int: ...
def aggregate_for_classifier(per_run_traces: list[list[dict]], task_id: str, lane: str) -> dict[str, Any]: ...
```

**Wasted-tokens algorithm** (D-40, locked from master design §Cost computation):
> Sum `tokens_in + tokens_out` across all `llm_call` events where `t_call_start_ms ∈ [t_inject_ms, t_observed_ms]` for the same lane.

---

### `src/a2a_vs_mcp/race/judges/haiku.py` (service — Anthropic SDK wrapper)

**Analog:** None in-repo — `reasoning.py` is OpenAI-bound and D-19 forbids reuse. RESEARCH §3 is the source.

**Locked module structure** (RESEARCH §3 lines 316-413):
```python
"""Haiku judge for race scorers (D-42).

Determinism: temperature=0. Anthropic does NOT support a `seed` parameter;
seed=42 is documentation-only.
Prompt caching: rubric system prompt is static -> cache_control type=ephemeral.
Haiku 4.5 minimum cache size = 2,048 tokens; pad rubrics to clear threshold.
"""
from __future__ import annotations
from dataclasses import dataclass
import os
import anthropic

HAIKU_MODEL: str = "claude-haiku-4-5"
TEMPERATURE: float = 0.0


@dataclass
class JudgeVerdict:
    passed: bool
    score: int
    rubric_total: int
    rationale: str
    tokens_in: int
    tokens_out: int


class HaikuJudge:
    def __init__(self, recorder: "TraceRecorder | None" = None) -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY not set; race judges require it.")
        self._client = anthropic.Anthropic(api_key=api_key)
        self._recorder = recorder

    def judge(self, *, rubric_system_prompt: str, artifact_user_prompt: str,
              max_tokens: int = 512) -> JudgeVerdict:
        msg = self._client.messages.create(
            model=HAIKU_MODEL,
            max_tokens=max_tokens,
            temperature=TEMPERATURE,
            system=[{
                "type": "text",
                "text": rubric_system_prompt,
                "cache_control": {"type": "ephemeral"},  # rubric is static
            }],
            messages=[{"role": "user", "content": artifact_user_prompt}],
        )
        ...
        if self._recorder is not None:
            self._recorder.record("llm_call", model=HAIKU_MODEL, role="judge",
                                  tokens_in=tokens_in, tokens_out=tokens_out)
```

**Trace integration** — recorder is optional dependency-injected so wasted-tokens computation can read these as `llm_call` events.

---

### `src/a2a_vs_mcp/race/mocks/{github,calendar,travel}.py` (adapter — fixture-backed mock)

**Analog:** `src/a2a_vs_mcp/evidence.py` (module-level helpers, db_path bound at server build time) + `src/a2a_vs_mcp/race/failure.py:inject_fault` (THE chokepoint per D-25).

**Fixture loading pattern** (mirror `evidence.py` style — pure functions, file-bound argument):
```python
# race/mocks/github.py
"""GitHub fixture mock. SINGLE FAULT CHOKEPOINT — every fault flows through inject_fault().

CI grep (tests/race/test_iron_rule_grep.py) enforces: no direct response mutation in this file
or in mcp_servers/race_*.py — all mutation routes through race.failure.inject_fault().
"""
from __future__ import annotations
import json
from pathlib import Path
from typing import Any

from ..failure import inject_fault, FaultKind

FIXTURES_DIR = Path(__file__).resolve().parents[3] / "data" / "race" / "fixtures" / "github"

def _load_fixture(name: str) -> Any:
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text())
```

**Single chokepoint pattern** (calls `inject_fault` from Phase 6 verbatim — `race/failure.py:47-83`):
```python
def get_repo_metadata(repo_id: str, *, recorder, run_id: str) -> dict[str, Any]:
    response = _load_fixture("repos")[repo_id]   # build response FIRST
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

**`_ACTIVE_FAULTS` propagation** — RESEARCH §10 Q2 recommends `contextvars.ContextVar` per `(run_id, lane)`, NOT a module-level dict (avoids cross-run pollution).

**IRON RULE invariant** — record-before-mutate is enforced inside `inject_fault()` itself (Phase 6 atomicity test verifies); mocks just call the helper.

---

### `src/a2a_vs_mcp/race/tasks/<task_id>/__init__.py` (registry module + scorer)

**Analog:** `src/a2a_vs_mcp/race/failure.py` (module-level enum/registry + `validate_failure_script`) + `src/a2a_vs_mcp/config.py` PROFILES dict idiom.

**Module-level registry pattern** (matches D-27, structurally identical to `race/failure.py:101` `_SCRIPT_ADAPTER`):
```python
# race/tasks/summarize_repo/__init__.py
from __future__ import annotations
from typing import Callable, Any

from ...mocks import github as github_mock
from ...types import ExecutionContext, ScoreCard
from ...judges.haiku import HaikuJudge

# D-27 registries — typo here = ValidationError at startup (loader cross-validates).
TARGETS: dict[str, Callable[..., Any]] = {
    "github_api.get_repo_metadata": github_mock.get_repo_metadata,
    "github_api.list_files": github_mock.list_files,
    "github_api.read_file": github_mock.read_file,
}

BINDS: dict[str, Callable[[ExecutionContext], Any]] = {
    # summarize_repo's hybrid_plan doesn't use bind in v1 yaml.
}
```

**`negotiate_meeting/__init__.py` is structural-only** (D-43): NO `HaikuJudge` import, scorer returns ScoreCard from pure structural checks.

**`book_travel/__init__.py` is composite** (D-42): both structural AND Haiku must pass — see RESEARCH §3 lines 452-467 for the locked composite shape.

---

### `src/a2a_vs_mcp/race/tasks/loader.py` (utility — Pydantic loader)

**Analog:** `src/a2a_vs_mcp/race/failure.py:101-110` — same TypeAdapter/validator-at-startup pattern.

**Pattern excerpt** (`race/failure.py` lines 101-110):
```python
_SCRIPT_ADAPTER: TypeAdapter[list[FailureScriptEntry]] = TypeAdapter(list[FailureScriptEntry])

def validate_failure_script(yaml_data: list[dict[str, Any]]) -> list[FailureScriptEntry]:
    """Pydantic-validated loader for failure_script YAML (D-12).

    Rejects unknown FaultKind values at startup. ...
    """
    return _SCRIPT_ADAPTER.validate_python(yaml_data)
```

**Phase 7 extension** (RESEARCH §7 — D-28 cross-validates `target` against TARGETS keys and `bind` against BINDS keys at import time):
```python
# race/tasks/loader.py uses importlib.resources to read YAML packaged inside
# src/a2a_vs_mcp/race/tasks/<id>/task_config.yaml (D-26).
yaml_text = resources.files(pkg).joinpath("task_config.yaml").read_text()
cfg = TaskConfig.model_validate(raw)
# Cross-validate every failure_script.target against TARGETS keys; raise ValidationError on miss.
```

**Startup hook** (`race/tasks/__init__.py` — module-level dict-comp triggers all validation at first import):
```python
V1_TASK_IDS = ["summarize_repo", "negotiate_meeting", "book_travel"]
TASK_CONFIGS: dict[str, tuple] = {tid: load_task_config(tid) for tid in V1_TASK_IDS}
```

---

### `src/a2a_vs_mcp/mcp_servers/race_{github,calendar,travel}.py` (MCP server — FastMCP)

**Analog (exact):** `src/a2a_vs_mcp/mcp_servers/db_server.py` and `docs_server.py`.

**Imports + builder pattern** (`db_server.py` lines 1-12):
```python
from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from a2a_vs_mcp import evidence


def build_server(db_path: Path) -> FastMCP:
    mcp = FastMCP("Support Database MCP", json_response=True)
```

**Tool registration pattern** (`db_server.py` lines 17-21):
```python
@mcp.tool()
def get_customer_profile(customer_id: str) -> dict[str, Any] | None:
    """Return a customer profile by customer ID."""
    return evidence.get_customer_profile(db_path, customer_id)
```

**Apply to race servers verbatim** — substitute `evidence` with `race.mocks.github` (etc.) and add `recorder` + `run_id` propagation per RESEARCH §5 contextvars recommendation:
```python
# src/a2a_vs_mcp/mcp_servers/race_github.py
from mcp.server.fastmcp import FastMCP
from a2a_vs_mcp.race.mocks import github as github_mock

def build_server() -> FastMCP:
    mcp = FastMCP("Race GitHub MCP", json_response=True)

    @mcp.tool()
    def get_repo_metadata(repo_id: str) -> dict[str, Any]:
        """Return repo metadata (mocked, fault-injectable)."""
        return github_mock.get_repo_metadata(repo_id)  # mock owns inject_fault chokepoint

    @mcp.tool()
    def list_files(repo_id: str, path: str = "") -> list[str]:
        return github_mock.list_files(repo_id, path)

    return mcp
```

**`main()` CLI entry point** — copy from `db_server.py:60-71` for parity:
```python
def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--transport", choices=["stdio", "streamable-http"], default="stdio")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    server = build_server()
    server.settings.host = args.host
    server.settings.port = args.port
    server.run(transport=args.transport)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

**Resource pattern (optional)** — `db_server.py:46-55` shows `@mcp.resource()` decorator. Race servers can ship resources for fixture browsing if useful (Claude's Discretion).

**Wiring choice** (RESEARCH §5): use `transport="stdio"` from `MCPClient` so the existing `SERVER_BUILDERS` dict in `mcp/client.py:24-27` is BYPASSED. Zero mutation to `mcp/client.py`.

---

### `src/a2a_vs_mcp/race/failure.py` — DELTA (add `InjectedFaultError`)

**Analog:** itself — same module, in-place addition.

**Required diff** (RESEARCH §2):
```python
# race/failure.py — add at top of file
class InjectedFaultError(RuntimeError):
    """Raised by _apply_mutation for RATE_LIMIT_429 + PARTIAL_COMMIT_5XX.

    Distinguishes injected faults from real Anthropic infra errors so the
    harness retry classifier never retries the test.
    """
```

**Update `_apply_mutation`** (lines 86-98):
```python
def _apply_mutation(kind: FaultKind, response: Any) -> Any:
    if kind is FaultKind.RATE_LIMIT_429:
        raise InjectedFaultError("HTTP 429 rate_limit (injected)")
    if kind is FaultKind.PARTIAL_COMMIT_5XX:
        raise InjectedFaultError("HTTP 503 partial_commit (injected)")
    return response
```

**Phase 6 test update** (`tests/race/test_inject_fault.py:33-42`):
```python
# Was: with self.assertRaises(RuntimeError):
# Now: with self.assertRaises(InjectedFaultError):
# (InjectedFaultError IS-A RuntimeError, so the existing test technically still passes,
#  but assert the more specific type to lock the contract.)
```

---

### `data/race/fixtures/{github_repos,calendars,travel}.json` (data / seed fixtures)

**Analog (exact):** `src/a2a_vs_mcp/data/seeds/customers.json`, `orders.json`, etc.

**Layout idiom** — JSON arrays of records with stable IDs. Path is OUTSIDE `src/` because it is data, not code (CONTEXT.md `<code_context>` integration points).

**Loading pattern** — `Path(__file__).resolve().parents[3] / "data" / "race" / "fixtures" / "<file>.json"` per `race/runs.py:21-22` (`RUNS_DIR` resolves the same way).

---

### `tests/race/test_*.py` (12 NEW test files)

**Analog (exact):** `tests/race/test_inject_fault.py` — sets the convention used by all 37 existing race tests.

**File header + recorder factory pattern** (`test_inject_fault.py` lines 1-17):
```python
"""IRON RULE atomicity + Pydantic failure_script validator (TRC-03)."""
from __future__ import annotations

import unittest

from pydantic import ValidationError

from a2a_vs_mcp.trace import TraceRecorder
from a2a_vs_mcp.race.failure import FaultKind, inject_fault, validate_failure_script
from a2a_vs_mcp.race.schemas import FaultInjectedEvent, FaultObservedEvent


def _make_recorder(run_id: str = "if-test", lane: str = "pure_mcp") -> TraceRecorder:
    return TraceRecorder(mode="mock", runtime="mock", task_id="t")
```

**Cleanup helper for run-id-bound tests** (`test_trace_schema.py` lines 12-17):
```python
def _cleanup(run_id: str) -> None:
    _WRITERS.pop(run_id, None)
    path = RUNS_DIR / f"{run_id}.json"
    if path.exists():
        path.unlink()
```

**Pydantic validator test pattern** (`test_inject_fault.py:87-96`) — Phase 7 `test_task_registries.py` mirrors verbatim:
```python
class PydanticValidatorTests(unittest.TestCase):
    def test_accepts_known_kinds(self) -> None:
        entries = validate_failure_script([{"kind": "rate_limit_429", "target": "github.repos"}])
        self.assertEqual(len(entries), 1)

    def test_rejects_unknown_kind(self) -> None:
        with self.assertRaises(ValidationError):
            validate_failure_script([{"kind": "WAT_NO_SUCH_KIND", "target": "x"}])
```

**Apply to Phase 7 tests:** `test_unknown_target_rejected`, `test_unknown_bind_rejected`, `test_v1_tasks_load`.

**Mocked Anthropic SDK pattern** (RESEARCH §8 — no in-repo analog; first use):
```python
# tests/race/test_haiku_judge.py
import unittest
from unittest.mock import patch, MagicMock

class HaikuJudgeTests(unittest.TestCase):
    @patch("a2a_vs_mcp.race.judges.haiku.anthropic.Anthropic")
    def test_temperature_zero(self, mock_anthropic) -> None:
        mock_client = MagicMock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = MagicMock(...)
        # ... assert call kwargs include temperature=0.0
```

**Class layout convention** (verified across all Phase 6 race tests): one `unittest.TestCase` subclass per concern, `if __name__ == "__main__": unittest.main()` footer.

---

### `tests/race/fixtures/classifier_traces/*.json` + `recovery_regex_corpus.jsonl`

**Analog:** `tests/race/fixtures/` directory exists from Phase 6 (currently holds wire-event fixtures). Phase 7 adds two new sub-directories.

**Authoring source** — verbatim from master design §The Assignment (9 fictional traces) and eng-review test plan (50-sample corpus).

---

### `pyproject.toml` (modified — add `anthropic>=0.40`)

**Analog:** existing `pyproject.toml` `[project] dependencies` block.

**Concrete change** (RESEARCH §3 + Environment Availability table line 1279):
```toml
# pyproject.toml [project] dependencies — add line:
"anthropic>=0.40",
```

Also verify `pyyaml` is a direct dependency (RESEARCH §Environment Availability — currently transitive); add explicitly if missing.

---

## Shared Patterns

### IRON RULE chokepoint (Phase 6 inheritance)

**Source:** `src/a2a_vs_mcp/race/failure.py:1-13` (module docstring) + `inject_fault()` body lines 47-83.

**Apply to:** All `race/mocks/*` modules and all `mcp_servers/race_*.py` MCP servers.

**Excerpt** (lines 1-13):
```python
"""IRON RULE: record before mutate.

Every fault injection MUST flow through inject_fault(). Direct mutation of
mock responses is forbidden under src/a2a_vs_mcp/race/. CI grep enforces
(see tests/race/test_iron_rule_grep.py from Plan 08).
...
"""
```

**Phase 7 extension:** the CI grep test extends to `mcp_servers/race_*.py` (RESEARCH §5 lines 736-751).

---

### `from __future__ import annotations` first line

**Source:** `.planning/codebase/CONVENTIONS.md` Python — Code Style:
> `from __future__ import annotations` is the first statement in every source file — applied universally.

**Apply to:** All NEW `.py` files in Phase 7. No exceptions. (Also mandates lowercase generics `dict`/`list`/`tuple` and PEP 604 `X | Y` unions everywhere.)

---

### Module-level constant + helper-fn idiom

**Source:** `src/a2a_vs_mcp/race/turn.py` lines 9-23 — `TURN_DEFINING_EVENTS` dict + `is_turn_defining()` helper.

**Apply to:**
- `race/classifier.py` — `_ACK_FAULT_REGEX` + `is_acknowledging_fault()`
- `race/runners/hybrid.py` — `ON_FAULT_DISPATCH: dict[str, Callable]` (optional; or inline if-elif)
- `race/tasks/loader.py` — `V1_TASK_IDS` + `load_task_config()`

---

### Dataclass-first + `to_dict()` for serializable types

**Source:** `src/a2a_vs_mcp/race/schemas.py` (8 wire-event dataclasses) + `src/a2a_vs_mcp/schemas.py` (FailureConfig, AgentCard, A2AMessage).

**Apply to:** `race/types.py` (`HardnessProfile`, `TaskSpec`, `ScoreCard`, `RaceResult`); `race/judges/haiku.py` (`JudgeVerdict`); `race/classifier.py` (`Detector`).

**Excerpt pattern**:
```python
@dataclass
class TaskSpec:
    task_id: str
    prompt: str
    allowed_tools: list[str]
    expected_shape: dict[str, type]
    hardness_profile: HardnessProfile

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)   # or custom for nested dataclasses
```

---

### Pydantic startup validation (D-28 + Phase 6 D-12 inheritance)

**Source:** `src/a2a_vs_mcp/race/failure.py:101-110` (TypeAdapter at module load).

**Apply to:** `race/tasks/loader.py` — TaskConfig + cross-validate `target` and `bind` against TARGETS/BINDS dicts at first import. Typo = startup `ValidationError`, never silent.

**Test pattern** (`tests/race/test_inject_fault.py:94-96`) — assert `pytest --collect-only` blows up on unknown target/bind.

---

### Recorder propagation through transports (Phase 6 lane/run_id contract)

**Source:** `src/a2a_vs_mcp/trace.py:11-22` — `TraceRecorder(mode, runtime, task_id, run_id=None, lane=None)`.

**Apply to:** Every NEW Phase 7 module that touches the trace. Race runners construct via:
```python
recorder = TraceRecorder(mode=lane, runtime="anthropic_sonnet", task_id=task_id, run_id=run_id, lane=lane)
```

`mode` is the lane name per D-18; `runtime` is the LLM backend identifier.

**Critical:** the `__post_init__` in `trace.py:31-34` lazy-imports `race.runs.get_writer` only when both `run_id` AND `lane` are set. Race runners MUST set both; v1 callers leave both `None`.

---

### Single-file-per-concern (no abstract base classes for v1)

**Source:** `.planning/codebase/CONVENTIONS.md` — observed across `mcp_servers/db_server.py` and `docs_server.py` (no shared base) and across `evidence.py` (module-level helpers, no service class).

**Apply to:**
- `mcp_servers/race_{github,calendar,travel}.py` — three independent modules, NO common base (RESEARCH §10 Q1 recommendation: NO).
- `race/runners/{pure_mcp,pure_a2a,hybrid}.py` — module-level coroutines, NOT classes (RESEARCH §4).
- `race/mocks/{github,calendar,travel}.py` — module-level fns, NOT a Mock class.

---

### Test layout (unittest.TestCase, race-recorder helper, cleanup hook)

**Source:** `tests/race/test_inject_fault.py` and `tests/race/test_trace_schema.py`.

**Apply to:** All 12 NEW test files under `tests/race/`. Pattern:
1. `from __future__ import annotations`
2. `import unittest`
3. Local `_make_recorder()` factory and (when run-id-bound) `_cleanup(run_id)` helper
4. One `unittest.TestCase` subclass per concern
5. `if __name__ == "__main__": unittest.main()` footer

---

## No Analog Found

Files where Phase 7 introduces a pattern not present in the existing codebase (planner should anchor to RESEARCH.md sections, not a code analog):

| File | Role | Data Flow | Reason | RESEARCH section |
|------|------|-----------|--------|------------------|
| `src/a2a_vs_mcp/race/harness.py` | service (asyncio.Semaphore concurrency + retry classifier) | batch | Project has no asyncio.Semaphore + AsyncAnthropic pattern; `a2a/broker.py:send_tasks_parallel` uses ThreadPoolExecutor (different model) | §2 D-38 Resolution |
| `src/a2a_vs_mcp/race/judges/haiku.py` | service (Anthropic SDK) | request-response | `reasoning.py` is OpenAI-only; D-19 explicitly forbids subclassing v1 reasoning code; first Anthropic SDK use in repo | §3 D-42 Resolution |
| `src/a2a_vs_mcp/race/runners/hybrid.py` `on_fault` branching | runner | event-driven branching | No existing pre-scripted-plan-executor in repo; `agents/hybrid_specialists.py` is dynamic (LLM-driven), not pre-scripted | §4 |
| `src/a2a_vs_mcp/race/classifier.py` `Detector` state machine | service | transform | No state-machine pattern exists in current repo; locked verbatim from master design pseudocode | §6 |

For these files, planner MUST reference the RESEARCH.md sections cited above for code shape, not a sibling file.

---

## Metadata

**Analog search scope:**
- `src/a2a_vs_mcp/` (full backend tree)
- `src/a2a_vs_mcp/race/` (Phase 6 modules — `failure.py`, `turn.py`, `runs.py`, `schemas.py`, `trace.py` extension)
- `src/a2a_vs_mcp/mcp/`, `mcp_servers/`, `a2a/` (transport contracts — D-23/D-24 reuse)
- `tests/race/` (Phase 6 test layout — 37 tests as the convention)
- `data/seeds/` (JSON fixture idiom)

**Files scanned:** 18 source files + 5 race-test files + 2 phase planning files + 2 codebase intel files = 27 files.

**Key conventions verified live:**
- `from __future__ import annotations` present in every source file (CONVENTIONS.md confirmed via spot-checks of `failure.py`, `turn.py`, `runs.py`, `db_server.py`, `broker.py`, `client.py`).
- Lowercase generics + PEP 604 unions universal.
- `@dataclass` + `to_dict()` is the project's serialization idiom.
- Pydantic reserved for boundaries (`api_schemas.py`, `failure.py:_SCRIPT_ADAPTER`); core schemas stay dataclass.
- `unittest.TestCase` (not bare `pytest` style) is the race-test convention.

**Known CONTEXT.md typo (surfaced in RESEARCH §5):** D-24 references `broker.send_message` — actual method in `a2a/broker.py:61` is `send_task`. All Phase 7 plans MUST use `send_task`.

**Pattern extraction date:** 2026-04-28

---

## PATTERN MAPPING COMPLETE

**Phase:** 7 — Race Backend — Lanes, Harness, Recovery State Machine
**Files classified:** 30 backend + 6 fixture/test-fixture + 12 tests + 1 config = 49
**Analogs found:** 26 / 30 backend files have in-repo analogs; 4 are RESEARCH-driven (harness, haiku judge, hybrid on_fault dispatch, Detector state machine).

### Coverage
- Files with exact analog: 18 (all 3 race MCP servers, types, loader, all 3 mocks, all 3 task `__init__.py` files, failure.py delta, all 12 tests, fixtures)
- Files with role-match analog: 8 (3 runners, classifier, metrics, ws-emitting harness pieces, judge verdict dataclass)
- Files with no analog (RESEARCH-anchored): 4 (harness asyncio.Semaphore, Haiku Anthropic client, hybrid on_fault dispatch, Detector state machine)

### Key Patterns Identified
- **MCP servers** copy `db_server.py` + `docs_server.py` shape verbatim — `from __future__ import annotations`, `FastMCP("...", json_response=True)`, `@mcp.tool()` decorators, optional `@mcp.resource()`, CLI `main()` argparse footer.
- **A2A handlers** register on a per-(run_id, lane) `A2ABroker(trace=recorder)`; method is `send_task` (not `send_message` — CONTEXT.md D-24 typo, RESEARCH §5 confirmed); `handle_task` runs inside ThreadPoolExecutor and returns `AgentResult`.
- **Mocks** route every fault through Phase 6 `inject_fault()` — single chokepoint; CI grep extends from `race/` to `mcp_servers/race_*.py` per RESEARCH §5.
- **Pydantic startup validation** mirrors `race/failure.py:101-110` (TypeAdapter pattern); applied to TaskConfig with cross-validation of `target` (against TARGETS) and `bind` (against BINDS).
- **TraceRecorder** in race mode = `TraceRecorder(mode=lane, runtime=..., task_id=..., run_id=run_id, lane=lane)`; `_writer` is auto-attached when both `run_id` + `lane` are set (Phase 6 D-18).
- **Module-level functions, not classes** — runners, mocks, metrics, classifier helpers all stay free-floating per `evidence.py` idiom.
- **Tests** use `unittest.TestCase`, local `_make_recorder()` factory, `_cleanup(run_id)` hook, single concern per class — verbatim from `tests/race/test_inject_fault.py` shape.

### File Created
`.planning/phases/07-race-backend-lanes-harness-recovery/07-PATTERNS.md`

### Ready for Planning
Pattern mapping complete. Planner can now reference analog file:line excerpts in PLAN.md actions. The 4 RESEARCH-anchored files are explicitly flagged so the planner reads RESEARCH §2/§3/§4/§6 instead of looking for a sibling code analog that does not exist.
