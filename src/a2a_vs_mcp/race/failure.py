"""IRON RULE: record before mutate.

Every fault injection MUST flow through inject_fault(). Direct mutation of
mock responses is forbidden under src/a2a_vs_mcp/race/. CI grep enforces
(see tests/race/test_iron_rule_grep.py from Plan 08).

Owns FaultKind enum (D-12), FailureScriptEntry dataclass + Pydantic YAML loader
(D-12), and the inject_fault() helper that emits fault_injected events with the
TRC-03 schema (fault_id, fault_kind, target, t_inject_ms) to TraceRecorder.

fault_observed recording is Phase 7's recovery state machine (D-14). Phase 6
only ships the schema + emit path for fault_injected.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any
import time

from pydantic import TypeAdapter

from ..trace import TraceRecorder


class InjectedFaultError(RuntimeError):
    """Raised by _apply_mutation for RATE_LIMIT_429 and PARTIAL_COMMIT_5XX faults.

    Distinguishes injected faults from real Anthropic infra errors so the
    harness retry classifier never retries the test. Phase 7 D-38: harness
    retries anthropic.RateLimitError but NEVER InjectedFaultError.

    IS-A RuntimeError so existing Phase 6 callers that catch RuntimeError
    still work.
    """


# 3.10-safe StrEnum analog (RESEARCH.md Pitfall 6 — pyproject.toml pins >=3.10).
class FaultKind(str, Enum):
    RATE_LIMIT_429 = "rate_limit_429"
    PARTIAL_JSON = "partial_json"
    SCHEMA_DRIFT = "schema_drift"
    EVENTUAL_CONSISTENCY_READ = "eventual_consistency_read"
    PARTIAL_COMMIT_5XX = "partial_commit_5xx"


@dataclass
class FailureScriptEntry:
    kind: FaultKind
    target: str
    after_calls: int = 0
    duration_calls: int = 1
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def inject_fault(
    recorder: TraceRecorder,
    *,
    fault_id: str,
    kind: FaultKind,
    target: str,
    original_response: Any,
) -> Any:
    """Atomic record-then-mutate. Returns the mutated response.

    IRON RULE: emits the fault_injected event BEFORE computing the mutation
    (D-11). If _apply_mutation raises, the event is still on the recorder —
    callers can observe the injection even on raise paths.

    Args:
        recorder: a TraceRecorder constructed with run_id + lane (D-18 race mode).
        fault_id: caller-supplied unique id (Phase 7 mints from failure_script).
        kind: one of the 5 FaultKind enum values (D-12).
        target: dotted resource path being faulted (e.g. "github.repos.search").
        original_response: ALREADY-BUILT response from the mock API caller.
            MUST be built BEFORE this function is called (RESEARCH.md Pitfall 3).

    Returns:
        The mutated response (or raises if the kind models a hard failure
        like RATE_LIMIT_429 / PARTIAL_COMMIT_5XX).
    """
    t_inject_ms = int(time.time() * 1000)
    # Step 1 (record) — runs FIRST per IRON RULE.
    recorder.record(
        "fault_injected",
        fault_id=fault_id,
        fault_kind=kind.value,
        target=target,
        t_inject_ms=t_inject_ms,
    )
    # Step 2 (mutate) — runs only after the event is on the recorder.
    return _apply_mutation(kind, original_response)


def _apply_mutation(kind: FaultKind, response: Any) -> Any:
    """Per-kind mutation dispatcher. Phase 7's mock APIs flesh this out;
    Phase 6 ships the dispatcher with rate_limit_429 + partial_commit_5xx
    as the two raise-style faults so the IRON RULE atomicity test can
    assert events are recorded BEFORE the raise."""
    if kind is FaultKind.RATE_LIMIT_429:
        raise InjectedFaultError("HTTP 429 rate_limit (injected)")
    if kind is FaultKind.PARTIAL_COMMIT_5XX:
        raise InjectedFaultError("HTTP 503 partial_commit (injected)")
    # Soft mutations (partial_json, schema_drift, eventual_consistency_read)
    # land in Phase 7's mock APIs; Phase 6 returns the original response unchanged
    # so the inject_fault contract is exercised end-to-end without partial logic.
    return response


_SCRIPT_ADAPTER: TypeAdapter[list[FailureScriptEntry]] = TypeAdapter(list[FailureScriptEntry])


def validate_failure_script(yaml_data: list[dict[str, Any]]) -> list[FailureScriptEntry]:
    """Pydantic-validated loader for failure_script YAML (D-12).

    Rejects unknown FaultKind values at startup. Phase 7 task_config.yaml loaders
    call this after yaml.safe_load() before handing the script to the harness.
    """
    return _SCRIPT_ADAPTER.validate_python(yaml_data)
