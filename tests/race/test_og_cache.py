"""Phase 10 — unit tests for og_cache_path + cleanup_stale (D-63: no Chromium)."""
from __future__ import annotations

import pytest

from a2a_vs_mcp.race import og as og_mod
from a2a_vs_mcp.race.config import OG_LAYOUT_VERSION


@pytest.fixture
def og_tmp(tmp_path, monkeypatch):
    d = tmp_path / "og"
    d.mkdir()
    monkeypatch.setattr(og_mod, "OG_DIR", d)
    return d


def test_og_cache_path_filename_shape(og_tmp):
    p = og_mod.og_cache_path("r-abc", "og")
    assert p.parent == og_tmp
    assert p.name == f"r-abc-og-v{OG_LAYOUT_VERSION}.png"


def test_og_cache_path_heatmap_surface(og_tmp):
    p = og_mod.og_cache_path("r-abc", "heatmap")
    assert p.name == f"r-abc-heatmap-v{OG_LAYOUT_VERSION}.png"


def test_cleanup_stale_creates_dir_if_missing(tmp_path, monkeypatch):
    d = tmp_path / "og_does_not_exist_yet"
    monkeypatch.setattr(og_mod, "OG_DIR", d)
    og_mod.cleanup_stale("r-1", "og")
    assert d.exists() and d.is_dir()


def test_cleanup_stale_deletes_old_versions_only(og_tmp):
    # Stale files: v0, v(current+99). Current file: v<current>.
    current = OG_LAYOUT_VERSION
    keep = og_tmp / f"r-1-og-v{current}.png"
    old0 = og_tmp / "r-1-og-v0.png"
    old2 = og_tmp / f"r-1-og-v{current + 99}.png"
    unrelated = og_tmp / "r-2-og-v0.png"  # different run_id — must not delete
    for p in (keep, old0, old2, unrelated):
        p.write_bytes(b"x")
    og_mod.cleanup_stale("r-1", "og")
    assert keep.exists()
    assert not old0.exists()
    assert not old2.exists()
    assert unrelated.exists()  # OG-04 contract: per-run_id, per-surface scope


def test_cleanup_stale_scopes_by_surface(og_tmp):
    current = OG_LAYOUT_VERSION
    og_keep = og_tmp / f"r-1-og-v{current}.png"
    hm_old = og_tmp / "r-1-heatmap-v0.png"
    hm_keep = og_tmp / f"r-1-heatmap-v{current}.png"
    for p in (og_keep, hm_old, hm_keep):
        p.write_bytes(b"x")
    # Cleanup ONLY heatmap surface; og file untouched.
    og_mod.cleanup_stale("r-1", "heatmap")
    assert og_keep.exists()
    assert hm_keep.exists()
    assert not hm_old.exists()


def test_cleanup_stale_noop_when_only_current_exists(og_tmp):
    current = OG_LAYOUT_VERSION
    keep = og_tmp / f"r-1-og-v{current}.png"
    keep.write_bytes(b"x")
    og_mod.cleanup_stale("r-1", "og")
    assert keep.exists()
    assert list(og_tmp.iterdir()) == [keep]
