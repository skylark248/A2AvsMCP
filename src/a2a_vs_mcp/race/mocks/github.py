"""GitHub fixture mock. SINGLE FAULT CHOKEPOINT per D-25.

Every fault flows through race.failure.inject_fault(). Direct response
mutation in this file is forbidden - CI grep enforces (extends Phase 6 D-13).

Functions take a TraceRecorder + run_id so inject_fault() can emit
fault_injected events on the per-(run_id, lane) recorder. Faults are armed
via the contextvars-backed ACTIVE_FAULTS registry in mocks/__init__.py.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from ..failure import inject_fault
from ...trace import TraceRecorder
from . import get_active_fault


# This file is at src/a2a_vs_mcp/race/mocks/github.py.
# parents[0]=mocks, parents[1]=race, parents[2]=a2a_vs_mcp, parents[3]=src, parents[4]=repo root.
FIXTURES_PATH = Path(__file__).resolve().parents[4] / "data" / "race" / "fixtures" / "github" / "repos.json"


def _load() -> dict[str, Any]:
    return json.loads(FIXTURES_PATH.read_text())


def get_repo_metadata(repo_id: str, *, recorder: TraceRecorder, run_id: str) -> dict[str, Any]:
    """Return repo metadata. Routes through inject_fault if armed for this target."""
    fixtures = _load()
    response = fixtures["repos"].get(repo_id)
    if response is None:
        raise KeyError(f"unknown repo_id: {repo_id}")
    target = "github_api.get_repo_metadata"
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


def list_files(repo_id: str, path: str = "", *, recorder: TraceRecorder, run_id: str) -> list[str]:
    fixtures = _load()
    response = fixtures["repos"].get(repo_id, {}).get("files", [])
    target = "github_api.list_files"
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


def read_file(repo_id: str, file_path: str, *, recorder: TraceRecorder, run_id: str) -> str:
    """Return synthetic file content (we don't ship real files; return a stub line)."""
    response = f"# {repo_id}::{file_path}\n# (synthetic content for mock)\n"
    target = "github_api.read_file"
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
