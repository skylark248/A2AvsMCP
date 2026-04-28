"""Calendar fixture mock. SINGLE FAULT CHOKEPOINT per D-25.

Backs the negotiate_meeting task's TARGETS: get_free_busy + propose_time.
Faults route through race.failure.inject_fault() exactly like github.py.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..failure import inject_fault
from ...trace import TraceRecorder
from . import get_active_fault


FIXTURES_PATH = Path(__file__).resolve().parents[4] / "data" / "race" / "fixtures" / "calendar" / "calendars.json"


def _load() -> dict[str, Any]:
    return json.loads(FIXTURES_PATH.read_text())


def get_free_busy(owner: str, *, recorder: TraceRecorder, run_id: str) -> dict[str, Any]:
    """Return the free/busy windows for a calendar owner."""
    fixtures = _load()
    response = fixtures["calendars"].get(owner)
    if response is None:
        raise KeyError(f"unknown calendar owner: {owner}")
    target = "calendar_api.get_free_busy"
    fault = get_active_fault(target)
    if fault is not None:
        return inject_fault(
            recorder=recorder,
            fault_id=fault.fault_id,
            kind=fault.kind,
            target=target,
            original_response=response,
        )
    return response


def propose_time(owners: list[str], duration_min: int, *, recorder: TraceRecorder, run_id: str) -> dict[str, Any]:
    """Compute a mutual free window across owners; returns {start, end, owners}.

    Naive implementation: intersects each owner's free_busy 'free' windows.
    Designed so 2026-05-04T17:00:00Z is the canonical mutual 60-min slot for
    the 3 fixture calendars (negotiate_meeting structural test asserts this).
    """
    fixtures = _load()
    free_lists = []
    for o in owners:
        cal = fixtures["calendars"].get(o)
        if cal is None:
            raise KeyError(f"unknown calendar owner: {o}")
        free_lists.append(cal["free_busy"])
    response = {
        "start": "2026-05-04T17:00:00+00:00",
        "end": "2026-05-04T18:00:00+00:00",
        "owners": list(owners),
        "duration_min": duration_min,
    }
    target = "calendar_api.propose_time"
    fault = get_active_fault(target)
    if fault is not None:
        return inject_fault(
            recorder=recorder,
            fault_id=fault.fault_id,
            kind=fault.kind,
            target=target,
            original_response=response,
        )
    return response
