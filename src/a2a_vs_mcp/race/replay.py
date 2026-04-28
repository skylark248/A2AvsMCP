"""Replay loader + stub no-op migrator for ndjson run files (TRC-02, D-07).

Phase 6 ships the IDENTITY v1.0 -> v1.0 migrator. Real schema-migration logic
is TODO 4, deferred indefinitely (master design + CONTEXT.md §"Specifics").

Path-traversal guard: _validate_run_id rejects anything outside ^[A-Za-z0-9_-]{1,64}$.
HIGH-severity threat per RESEARCH.md §"Security Domain" V12 (Plan 07's ws route
imports this regex too).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1.0"})

_RUN_ID_RE: re.Pattern[str] = re.compile(r"[A-Za-z0-9_-]{1,64}")


def _validate_run_id(run_id: str) -> None:
    """Reject run_ids that could escape the runs directory (path traversal).

    Pattern: ^[A-Za-z0-9_-]{1,64}$ via re.fullmatch.
    """
    if not _RUN_ID_RE.fullmatch(run_id):
        raise ValueError(f"invalid run_id: {run_id!r}")


def migrate_v1(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Stub no-op migrator. v1.0 -> v1.0 identity. Real migration is TODO 4.

    Validates that the FIRST event's trace_schema_version is in
    SUPPORTED_SCHEMA_VERSIONS. Empty input is allowed.
    """
    if not events:
        return events
    version = events[0].get("trace_schema_version")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ValueError(
            f"Unsupported trace_schema_version: {version!r}; "
            f"supported={sorted(SUPPORTED_SCHEMA_VERSIONS)}"
        )
    return events


def load_run(run_id: str, runs_dir: Path) -> list[dict[str, Any]]:
    """Load all events for a run from ndjson + run them through migrate_v1.

    Args:
        run_id: validated against _RUN_ID_RE before any path resolution.
        runs_dir: typically RUNS_DIR from race.runs.
    """
    _validate_run_id(run_id)
    path = runs_dir / f"{run_id}.json"
    text = path.read_text(encoding="utf-8")
    events = [
        json.loads(line)
        for line in text.splitlines()
        if line.strip()
    ]
    return migrate_v1(events)


def events_for_lane(events: list[dict[str, Any]], lane: str) -> list[dict[str, Any]]:
    """Filter events by lane, preserving causal (input) order.

    TRC-01 'queryable post-run by (run_id, lane) in causal order' is
    delivered by load_run -> events_for_lane composition.
    """
    return [ev for ev in events if ev.get("lane") == lane]
