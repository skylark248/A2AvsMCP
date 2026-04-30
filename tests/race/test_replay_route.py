"""HEAT-03 backend half — /api/race/runs/{run_id}/trace route contract.

Path-traversal guard, missing-run 404, happy-path payload shape, schema_version=1.0.
Tests the replay endpoint that backs the frontend `/race/<run_id>` route via
`fetchRaceReplay` (Phase 8 typed stub at frontend/src/lib/api/client.ts:136-163).

Pinned decisions:
- HEAT-03: replay reads disk only, no live LLM, no event mutation.
- D-59: events shipped verbatim (backend `event_type` key NOT renamed to `type`).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from a2a_vs_mcp.web import app


@pytest.fixture
def runs_dir(tmp_path, monkeypatch):
    """Point web.py's RUNS_DIR at an isolated tmp directory.

    web.py imports RUNS_DIR at module load (line 45); replay.load_run takes
    runs_dir as a parameter, so monkeypatching the bound symbol in web.py is
    sufficient for the route to resolve traces in tmp_path.
    """
    monkeypatch.setattr("a2a_vs_mcp.web.RUNS_DIR", tmp_path)
    return tmp_path


def _write_run(runs_dir: Path, run_id: str, events: list[dict]) -> None:
    """Write an ndjson run file (one event per line)."""
    path = runs_dir / f"{run_id}.json"
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n")


# ---------------------------------------------------------------------------
# Test 1 — happy path: 200 with typed payload shape
# ---------------------------------------------------------------------------

def test_happy_path_returns_payload(runs_dir):
    """Valid existing run returns 200 + {run_id, events, schema_version='1.0'}."""
    events = [
        {
            "event_type": "run_meta",
            "trace_schema_version": "1.0",
            "model": "claude-sonnet-4-6",
            "seed": 42,
            "task_id": "summarize_repo",
            "lane": "pure_mcp",
            "run_id": "test-run-001",
        },
        {
            "event_type": "tick",
            "trace_schema_version": "1.0",
            "lane": "pure_mcp",
            "run_id": "test-run-001",
            "turn_index": 0,
            "ts_ms": 1000,
        },
    ]
    _write_run(runs_dir, "test-run-001", events)

    r = TestClient(app).get("/api/race/runs/test-run-001/trace")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["run_id"] == "test-run-001"
    assert body["schema_version"] == "1.0"
    assert isinstance(body["events"], list)
    assert len(body["events"]) == 2


# ---------------------------------------------------------------------------
# Test 2 — invalid run_id returns 400 with detail from _validate_run_id
# ---------------------------------------------------------------------------

def test_invalid_run_id_returns_400(runs_dir):
    """Path-traversal-flavored or over-length run_id returns 400."""
    client = TestClient(app)

    # Special character that hits the route but is rejected by RUN_ID_REGEX.
    r = client.get("/api/race/runs/INVALID@CHAR/trace")
    assert r.status_code == 400, r.text
    assert "invalid run_id" in r.json()["detail"]

    # Over-length (regex caps at 64 chars).
    r = client.get(f"/api/race/runs/{'a' * 65}/trace")
    assert r.status_code == 400, r.text
    assert "invalid run_id" in r.json()["detail"]


# ---------------------------------------------------------------------------
# Test 3 — missing run returns 404 with stable detail
# ---------------------------------------------------------------------------

def test_missing_run_returns_404(runs_dir):
    """Well-formed run_id with no on-disk file → 404."""
    r = TestClient(app).get("/api/race/runs/r-doesnotexist/trace")
    assert r.status_code == 404, r.text
    assert r.json()["detail"] == "run not found"


# ---------------------------------------------------------------------------
# Test 4 — exact response shape matches frontend RaceReplayPayload
# ---------------------------------------------------------------------------

def test_response_shape_matches_frontend_typed_stub(runs_dir):
    """Top-level keys EXACTLY match RaceReplayPayload (client.ts:136-140)."""
    events = [
        {
            "event_type": "run_meta",
            "trace_schema_version": "1.0",
            "model": "claude-sonnet-4-6",
            "seed": 42,
            "task_id": "summarize_repo",
            "lane": "pure_mcp",
            "run_id": "shape-run",
        },
    ]
    _write_run(runs_dir, "shape-run", events)

    r = TestClient(app).get("/api/race/runs/shape-run/trace")
    assert r.status_code == 200, r.text
    body = r.json()
    assert set(body.keys()) == {"run_id", "events", "schema_version"}
    assert body["schema_version"] == "1.0"


# ---------------------------------------------------------------------------
# Test 5 — events shipped verbatim (D-59 deferral: no event_type → type rename)
# ---------------------------------------------------------------------------

def test_events_shipped_verbatim_no_normalization(runs_dir):
    """Events carry backend `event_type` key (NOT renamed to `type`) — D-59."""
    events = [
        {
            "event_type": "run_meta",
            "trace_schema_version": "1.0",
            "model": "claude-sonnet-4-6",
            "seed": 42,
            "task_id": "summarize_repo",
            "lane": "pure_mcp",
            "run_id": "verbatim-run",
        },
    ]
    _write_run(runs_dir, "verbatim-run", events)

    r = TestClient(app).get("/api/race/runs/verbatim-run/trace")
    assert r.status_code == 200, r.text
    first = r.json()["events"][0]
    assert first["event_type"] == "run_meta"
    assert "type" not in first or first.get("type") != "run_meta"
