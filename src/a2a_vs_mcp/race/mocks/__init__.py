"""Race mocks - single fault chokepoint per D-25.

Every mock callable in github.py / calendar.py / travel.py routes response
mutation through race.failure.inject_fault(). CI grep test
(tests/race/test_mocks_chokepoint.py) extends Phase 6 D-13 enforcement to
this directory and to mcp_servers/race_*.py.

Per-run state lives in ACTIVE_FAULTS, a contextvars.ContextVar mapping
target-string -> ActiveFault. Runner sets it BEFORE invoking transport,
clears it after the run. Cross-run pollution is impossible by construction
(contextvars are per-task in asyncio + per-thread in sync code).
"""
from __future__ import annotations
from contextvars import ContextVar
from dataclasses import dataclass

from ..failure import FaultKind


@dataclass
class ActiveFault:
    fault_id: str
    kind: FaultKind
    target: str


ACTIVE_FAULTS: ContextVar[dict[str, ActiveFault]] = ContextVar(
    "race_active_faults", default={},
)


def set_active_faults(faults: dict[str, ActiveFault]) -> object:
    """Set faults; returns a Token. Caller must call ACTIVE_FAULTS.reset(token) later."""
    return ACTIVE_FAULTS.set(dict(faults))


def get_active_fault(target: str) -> ActiveFault | None:
    """Lookup helper used by mock functions."""
    return ACTIVE_FAULTS.get().get(target)
