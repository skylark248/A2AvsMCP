"""Phase 10 — OG-01..OG-04 PNG + HTML route tests (D-63: mock render fn; no Chromium in CI)."""
from __future__ import annotations

import contextlib
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from a2a_vs_mcp.web import app


@pytest.fixture
def og_env(tmp_path, monkeypatch):
    runs = tmp_path / "runs"
    runs.mkdir()
    og = tmp_path / "og"
    og.mkdir()
    monkeypatch.setattr("a2a_vs_mcp.web.RUNS_DIR", runs)
    monkeypatch.setattr("a2a_vs_mcp.race.og.OG_DIR", og)
    monkeypatch.setattr("a2a_vs_mcp.web.OG_DIR", og, raising=False)
    monkeypatch.setattr("a2a_vs_mcp.race.config.OG_LAYOUT_VERSION", 1)
    monkeypatch.setattr(
        "a2a_vs_mcp.web._INDEX_HTML_CACHE",
        "<html><head><title>x</title></head><body></body></html>",
    )

    # D-63: bypass og_lifespan so tests don't need Chromium. Routes only read
    # `request.app.state.og_browser` to pass to render_*_png — and those are
    # monkeypatched per-test, so the browser value is never dereferenced.
    @contextlib.asynccontextmanager
    async def _noop_lifespan(_app):
        _app.state.og_browser = None
        yield

    monkeypatch.setattr(app.router, "lifespan_context", _noop_lifespan)
    return {"runs": runs, "og": og}

def _write_run(runs: Path, run_id: str) -> None:
    line = json.dumps({
        "event_type": "run_meta",
        "trace_schema_version": "1.0",
        "model": "claude-sonnet-4-6",
        "seed": 42,
        "task_id": "summarize_repo",
        "lane": "pure_mcp",
        "run_id": run_id,
    })
    (runs / f"{run_id}.json").write_text(line + "\n")


# Test 1 — OG-04: 404 BEFORE Playwright spawn (render fn never called)
def test_unknown_run_id_returns_404_without_render(og_env, monkeypatch):
    calls: list[str] = []

    async def fake_render(run_id, browser, base_url="..."):
        calls.append(run_id)
        return b"x"

    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_render)
    with TestClient(app) as client:
        r = client.get("/race/r-doesnotexist/og.png")
        assert r.status_code == 404
        assert calls == []


    # Test 2 — Path-traversal guard: invalid run_id returns 400
def test_invalid_run_id_returns_400(og_env):
    with TestClient(app) as client:
        r = client.get("/race/INVALID@CHAR/og.png")
        assert r.status_code == 400


    # Test 3 — Cache miss renders once + writes cache (200)
def test_cache_miss_renders_once_and_writes(og_env, monkeypatch):
    _write_run(og_env["runs"], "r-1")
    calls: list[str] = []

    async def fake_render(run_id, browser, base_url="..."):
        calls.append(run_id)
        return b"PNGBYTES"

    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_render)
    with TestClient(app) as client:
        r = client.get("/race/r-1/og.png")
        assert r.status_code == 200
        assert r.headers["content-type"] == "image/png"
        assert r.content == b"PNGBYTES"
        assert calls == ["r-1"]
        assert (og_env["og"] / "r-1-og-v1.png").read_bytes() == b"PNGBYTES"


    # Test 4 — Cache hit skips render
def test_cache_hit_skips_render(og_env, monkeypatch):
    _write_run(og_env["runs"], "r-2")
    (og_env["og"] / "r-2-og-v1.png").write_bytes(b"CACHED")
    calls: list[int] = []

    async def fake_render(*a, **k):
        calls.append(1)
        return b"NEW"

    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_render)
    with TestClient(app) as client:
        r = client.get("/race/r-2/og.png")
        assert r.status_code == 200
        assert r.content == b"CACHED"
        assert calls == []


    # Test 5 — OG-04: version bump invalidates + cleans up old
def test_version_bump_invalidates_and_cleans(og_env, monkeypatch):
    _write_run(og_env["runs"], "r-3")
    (og_env["og"] / "r-3-og-v0.png").write_bytes(b"OLD")

    async def fake_render(*a, **k):
        return b"NEW"

    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_render)
    with TestClient(app) as client:
        r = client.get("/race/r-3/og.png")
        assert r.status_code == 200
        assert r.content == b"NEW"
        assert not (og_env["og"] / "r-3-og-v0.png").exists()
        assert (og_env["og"] / "r-3-og-v1.png").read_bytes() == b"NEW"


    # Test 6 — D-62: render exception → 503, no cache write
def test_render_exception_returns_503_and_does_not_cache(og_env, monkeypatch):
    _write_run(og_env["runs"], "r-4")

    async def fake_render(*a, **k):
        raise RuntimeError("playwright crashed")

    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_render)
    with TestClient(app) as client:
        r = client.get("/race/r-4/og.png")
        assert r.status_code == 503
        assert not list(og_env["og"].glob("r-4-*.png"))


    # Test 7 — Heatmap mirrors og.png (parametrized)
@pytest.mark.parametrize(
    "surface,route,expected",
    [
        ("og", "/race/r-5/og.png", b"OG"),
        ("heatmap", "/race/r-5/heatmap.png", b"HM"),
    ],
)
def test_both_surfaces_share_invariants(og_env, monkeypatch, surface, route, expected):
    _write_run(og_env["runs"], "r-5")

    async def fake_og(*a, **k):
        return b"OG"

    async def fake_hm(*a, **k):
        return b"HM"

    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_og)
    monkeypatch.setattr("a2a_vs_mcp.web.render_heatmap_png", fake_hm)
    with TestClient(app) as client:
        r = client.get(route)
        assert r.status_code == 200
        assert r.content == expected


    # Test 8 — OG-01: meta tags injected on /race/{run_id} HTML for known run
def test_html_route_injects_og_meta_tags(og_env):
    _write_run(og_env["runs"], "r-6")
    with TestClient(app) as client:
        r = client.get("/race/r-6")
        assert r.status_code == 200
        body = r.text
        assert 'property="og:image"' in body
        assert 'content="http://testserver/race/r-6/og.png"' in body
        assert 'name="twitter:card" content="summary_large_image"' in body
        assert 'property="og:url"' in body


    # Test 9 — Crawler-safe: no og:image for unknown run (no broken-image embed)
def test_html_route_omits_image_for_unknown_run(og_env):
    with TestClient(app) as client:
        r = client.get("/race/r-doesnotexist")
        assert r.status_code == 200
        assert 'property="og:image"' not in r.text
