"""Phase 10 — Playwright singleton + asyncio.Lock + render helpers for /race/<id>/og.png + heatmap.png.

D-61: Singleton Browser at FastAPI startup; asyncio.Lock serializes concurrent renders.
      BrowserContext + Page are per-render and closed in finally.
D-62: Render failure raised as exception; caller (web.py) translates to HTTP 503.
D-63: Tests mock render_og_png / render_heatmap_png via monkeypatch.setattr.
D-66: Cache pattern data/og/<run_id>-<surface>-v<OG_LAYOUT_VERSION>.png with lazy purge.

Risk-1 note: OG_RENDER_LOCK is constructed at module-import time. Python 3.10+ lazy-binds
asyncio.Lock to the calling event loop on first acquire, so module scope is safe under
uvicorn. If a future async-runtime change breaks this, move the lock construction into
og_lifespan and stash on app.state.og_render_lock.

Risk-4 note: Use wait_until=domcontentloaded + explicit wait_for_selector — networkidle
is unreliable for SPAs that hold a WebSocket. ?og=1 mode in RacePage suppresses WS opening.

Risk-10 note: render_og_png waits for [data-og-anchor][data-og-ready="true"] — RacePage
sets data-og-ready after useRaceReplay folds events. Skipping this ships blank lane cards.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import TYPE_CHECKING, AsyncIterator, Literal

from .config import OG_LAYOUT_VERSION

if TYPE_CHECKING:  # avoid hard import at module load — playwright is an optional dep
    from fastapi import FastAPI
    from playwright.async_api import Browser

OG_DIR: Path = Path(__file__).resolve().parents[3] / "data" / "og"
OG_RENDER_LOCK: asyncio.Lock = asyncio.Lock()
RENDER_TIMEOUT_MS: int = 10_000
OG_VIEWPORT: dict[str, int] = {"width": 1200, "height": 630}
HEATMAP_VIEWPORT: dict[str, int] = {"width": 1200, "height": 900}


@asynccontextmanager
async def og_lifespan(app: "FastAPI") -> AsyncIterator[None]:
    """FastAPI lifespan: start Playwright + headless Chromium; close on shutdown."""
    from playwright.async_api import async_playwright  # lazy import (D-61)

    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    app.state.og_playwright = pw
    app.state.og_browser = browser
    try:
        yield
    finally:
        await browser.close()
        await pw.stop()


async def render_og_png(
    run_id: str,
    browser: "Browser",
    base_url: str = "http://127.0.0.1:8008",
) -> bytes:
    """Render the 1200x630 anchor PNG for run_id. Caller MUST hold OG_RENDER_LOCK (D-61)."""
    ctx = await browser.new_context(viewport=OG_VIEWPORT, device_scale_factor=2)
    try:
        page = await ctx.new_page()
        page.set_default_timeout(RENDER_TIMEOUT_MS)
        await page.goto(f"{base_url}/race/{run_id}?og=1", wait_until="domcontentloaded")
        anchor = await page.wait_for_selector(
            '[data-og-anchor][data-og-ready="true"]', state="visible"
        )
        return await anchor.screenshot(type="png")
    finally:
        await ctx.close()


async def render_heatmap_png(
    run_id: str,
    browser: "Browser",
    base_url: str = "http://127.0.0.1:8008",
) -> bytes:
    """Render the 1200x900 heatmap PNG for run_id. Caller MUST hold OG_RENDER_LOCK."""
    ctx = await browser.new_context(viewport=HEATMAP_VIEWPORT, device_scale_factor=2)
    try:
        page = await ctx.new_page()
        page.set_default_timeout(RENDER_TIMEOUT_MS)
        await page.goto(
            f"{base_url}/race/{run_id}?og=1&surface=heatmap",
            wait_until="domcontentloaded",
        )
        anchor = await page.wait_for_selector("[data-heatmap-anchor]", state="visible")
        return await anchor.screenshot(type="png")
    finally:
        await ctx.close()


def og_cache_path(run_id: str, surface: Literal["og", "heatmap"]) -> Path:
    """Return data/og/<run_id>-<surface>-v<OG_LAYOUT_VERSION>.png (D-66)."""
    return OG_DIR / f"{run_id}-{surface}-v{OG_LAYOUT_VERSION}.png"


def cleanup_stale(run_id: str, surface: Literal["og", "heatmap"]) -> None:
    """Lazy delete-on-mismatch (Claude's discretion: chose lazy over startup hook).

    Globs OG_DIR for <run_id>-<surface>-v*.png and unlinks any whose name differs
    from the current cache filename. OG-04 success criterion.
    """
    OG_DIR.mkdir(parents=True, exist_ok=True)
    keep = og_cache_path(run_id, surface).name
    for p in OG_DIR.glob(f"{run_id}-{surface}-v*.png"):
        if p.name != keep:
            p.unlink(missing_ok=True)


__all__ = [
    "og_lifespan",
    "OG_RENDER_LOCK",
    "OG_DIR",
    "og_cache_path",
    "cleanup_stale",
    "render_og_png",
    "render_heatmap_png",
    "OG_VIEWPORT",
    "HEATMAP_VIEWPORT",
    "RENDER_TIMEOUT_MS",
]
