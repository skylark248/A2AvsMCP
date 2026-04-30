# Phase 10: OG Image & Sharing — Research

**Researched:** 2026-04-30
**Domain:** Server-rendered social-share PNGs (Playwright + FastAPI lifespan) + client-side canvas fallback (html2canvas) + SPA OG meta-tag injection.
**Confidence:** HIGH on stack + integration points; MEDIUM on cross-browser ClipboardItem behavior (Firefox).

## Summary

Phase 10 ships two FastAPI PNG endpoints that drive a singleton headless Chromium (Playwright Python) over a re-rendered `RacePage` in `?og=1` mode, plus a "Copy headline image" button using `html2canvas` as a client-side fallback. The non-obvious finding from this research session: **`/race/<run_id>` is currently served by the SPA's `createBrowserRouter` — there is no FastAPI route for it.** Social crawlers therefore receive the static `frontend/dist/index.html` (which contains NO og/twitter meta tags). OG meta-tag injection requires a NEW FastAPI HTML route for `/race/{run_id}` that reads the built `index.html`, injects meta tags into `<head>`, and returns the modified HTML. This is load-bearing for OG-01 and was not made explicit in CONTEXT.md.

Six other concrete decisions emerge from the codebase shape:
1. The OG/render module belongs at `src/a2a_vs_mcp/race/og.py` (sibling to `heatmap.py`/`replay.py`/`runs.py`), not in `serve_ui.py` (which is just a 13-line uvicorn entrypoint).
2. `OG_LAYOUT_VERSION` belongs in `race/config.py` next to `HEATMAP_BASELINE` (D-66 says "or a sibling module"; `config.py` is already the sibling).
3. `?og=1` chrome-strip should land as same-component conditional in `RacePage.tsx` — the existing component already gates on `__testState`, `isMobile`, `isReplay`; adding one more `useSearchParams` boolean fits the established pattern.
4. The `data-og-anchor` element is the existing 1200px `<Container component="main">` (line 135), restricted to the title block + lane row + banner (heatmap removed).
5. Heatmap.png annotation strip ships as a sibling component (`HeatmapAnnotationStrip`) inside `HardnessFailureHeatmap` rendered only when `?og=1&surface=heatmap`. Keeps the data-driven footer untouched.
6. Mobile `?mode=summary` consumes the OG cached PNG via `<img src="/race/<run_id>/og.png">` — no Playwright spawn on mobile, the user's first GET serves a cached file or an inline `<img>` fallback that the canvas button (already present) can re-snap. This closes the Phase 8 placeholder cleanly.

**Primary recommendation:** Use `playwright==1.59.0` (Python), `html2canvas==1.4.1` (frontend). Pin Chromium via Playwright's bundled browser (`playwright install chromium`) — no separate Chromium pin file needed; Playwright's version-locked download URL is the pin.

## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-61:** Singleton `Browser` launched at FastAPI startup (lifespan), shared across requests; `asyncio.Lock` serializes render calls. New `BrowserContext` + `Page` per render; closed after each.
- **D-62:** Playwright failure → HTTP 503; client-side canvas fallback handles user recovery. No silent placeholder PNG.
- **D-63:** PNG route tests mock the render function (`render_og_png(run_id) -> bytes` and heatmap equivalent); no real Chromium in CI. Test matrix: 404 unknown run_id, 200 cache miss → render once + write cache, 200 cache hit → no render, OG_LAYOUT_VERSION bump → invalidate, render exception → 503.
- **D-64:** `html2canvas` library, lazy-loaded via dynamic `import()` on first "Copy headline image" click. Captures the same `data-og-anchor` element Playwright targets.
- **D-65:** Canvas output via `navigator.clipboard.write([new ClipboardItem({'image/png': blob})])` with download fallback (filename `race-<run_id>.png`).
- **D-66:** Manual `OG_LAYOUT_VERSION` Python integer constant. Cache filename `data/og/<run_id>-v<OG_LAYOUT_VERSION>.png`. Cleanup task purges `<id>-v<old>.*` on next request after a bump.

### Claude's Discretion
- `?og=1` rendering surface (same-component vs separate `OgRacePage`) → **same-component** (recommended below).
- OG/render module location → **`src/a2a_vs_mcp/race/og.py`** (recommended below).
- Cleanup task trigger (startup hook vs lazy delete-on-mismatch) → **lazy** (recommended below).
- Mobile `?mode=summary` consumption shape → **`<img src="/race/<run_id>/og.png">` fetch** (recommended below).
- `data-og-anchor` element → **the existing 1200px `<Container component="main">` restricted to title-block + lane-row + banner** (recommended below).
- Heatmap.png annotation strip → **sibling `HeatmapAnnotationStrip` inside `HardnessFailureHeatmap`, gated by `?og=1&surface=heatmap`** (recommended below).
- Playwright dependency install strategy → **`pyproject.toml [project.optional-dependencies] og = ["playwright>=1.59,<2"]` + `playwright install chromium` step in dev/CI bootstrap** (recommended below).

### Deferred Ideas (OUT OF SCOPE)
- HMAC-signed PNG URLs (TODO 9) — v2.1+.
- SHA-over-scoped-anchor-CSS auto-invalidation — eng-review iter 2 Decision #3 superseded by D-66.
- Playwright browser pool (N=2-4) — v2.1+ if singleton lock contends.
- Multi-frame / animated OG variants — directional pill says static.
- Per-`OG_LAYOUT_VERSION` automated visual-regression / golden-PNG comparison test.
- OG endpoint observability (cache hits/misses + render latency on `/api/race/health`).

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| OG-01 | `/race/<run_id>/og.png` Playwright route → 1200×630 cropped anchor; cached at `data/og/<run_id>-v<OG_LAYOUT_VERSION>.png`; `<meta property="og:image">` + `<meta name="twitter:image">` injection | Implementation Approach §OG-01; OG Meta-Tag Injection Path |
| OG-02 | `/race/<run_id>/heatmap.png` Playwright route → 1200×900 with `run_id · model · seed · n · task_ids` annotation; shares `OG_LAYOUT_VERSION` cache key | Implementation Approach §OG-02; Heatmap.png annotation strip |
| OG-03 | "Copy headline image" button beside banner → client-side canvas snapshot of same 1200×630 anchor; ships as fallback | html2canvas Lazy-Load + Clipboard Pattern |
| OG-04 | 404 on unknown run_id BEFORE Playwright spawn; cleanup task purges stale `<id>-v<old>.*` files when `OG_LAYOUT_VERSION` bumps | Implementation Approach §OG-04; Test Strategy |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| OG meta-tag injection on `/race/{run_id}` HTML | API / Backend (FastAPI HTML route) | — | Social crawlers don't execute JS. Meta tags MUST be in the initial HTML response. SPA-only render = broken unfurl. [VERIFIED: routes.tsx has no server route for `/race`; only React Router] |
| Server-rendered PNG generation | API / Backend (Playwright over FastAPI) | — | Crawlers fetch `og.png` URL directly; no client involvement possible. Lifespan-singleton browser owns this. [CITED: D-61] |
| Cropped-anchor screenshot region (`data-og-anchor`) | Frontend Server-rendered DOM | Browser (html2canvas re-capture) | Both Playwright (server-side) and html2canvas (client-side) target the same DOM element so server + client paths share source of truth. [CITED: D-64] |
| `?og=1` chrome strip | Frontend (RacePage.tsx conditional) | — | Pure presentation logic; `useSearchParams` reads flag; conditional render hides/shows sections. |
| Cache invalidation on layout-version bump | API / Backend (lazy on next request) | — | `OG_LAYOUT_VERSION` is a Python constant; route reads it and globs `data/og/<run_id>-v*.{png}` to delete mismatches. [CITED: D-66] |
| "Copy headline image" button (clipboard write) | Browser (html2canvas + Clipboard API) | API (download fallback path is still client-only) | Must run in user gesture context; clipboard write requires direct user-event. Server cannot do this. [CITED: D-65] |
| Mobile `?mode=summary` image | Browser (`<img>` tag fetching `/race/<run_id>/og.png`) | API (serves cached PNG; spawns Playwright on miss) | Phase 8 placeholder ships an `<img>` reference; the API serves it. No Playwright on mobile because the cache is populated by the desktop user's first OG fetch. |
| 404-before-Playwright guard | API / Backend (reuse `_validate_run_id` + RUNS_DIR existence check) | — | `_validate_run_id` already exists; existence check is `(RUNS_DIR / f"{run_id}.json").exists()`. Both happen before any browser interaction. [VERIFIED: replay.py:22, runs.py:22] |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `playwright` (Python) | `>=1.59,<2` | Headless Chromium control via async API; `BrowserContext` per render; `page.screenshot(clip=...)` for region capture | Microsoft-maintained, async-native FastAPI fit (`async_playwright`), bundles its own browser, version-pinned download URL = our Chromium pin. [VERIFIED: pip index versions playwright → 1.59.0 latest, 2026-04-30] |
| `html2canvas` | `^1.4.1` | Client-side DOM-to-canvas rasterization | Battle-tested cross-browser; ~45 KB gzipped; one-line API (`html2canvas(node)` → Canvas). [VERIFIED: npm view html2canvas version → 1.4.1; CITED: D-64] |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| FastAPI lifespan context | (already on `fastapi>=0.135`) | `@asynccontextmanager` register on `app.router.lifespan_context` for browser launch/shutdown | Browser singleton lives across requests; clean shutdown on Ctrl-C. [CITED: FastAPI lifespan docs — startup/shutdown deprecated in favor of lifespan since 0.93] |
| `asyncio.Lock` | stdlib | Serialize concurrent renders against the singleton browser | Prevents two simultaneous misses from racing the same `BrowserContext` slot. [CITED: D-61] |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `playwright` Python async | `pyppeteer` | Pyppeteer is unmaintained; Playwright's async-native FastAPI fit is the deciding factor. |
| `html2canvas` | `dom-to-image-more`, `modern-screenshot`, hand-rolled `foreignObject` SVG | dom-to-image has Safari font-loading bugs; foreignObject hits Safari cross-origin font issues. D-64 already locked html2canvas. |
| Lifespan-singleton browser | Spawn-per-request | 2-3s every miss vs ~500ms-1s with warm browser. Master design budget. |
| Lifespan-singleton browser | Bounded pool (N=2-4) | Hackathon traffic doesn't justify the lock-bypass complexity. Deferred. |
| Server-side meta tag injection | Client-side `react-helmet-async` | Crawlers don't run JS — Helmet is a no-op for OG. Server-side mandatory. |

**Installation:**
```bash
# Backend (Python)
# Add to pyproject.toml [project.optional-dependencies]:
# og = ["playwright>=1.59,<2"]
pip install -e ".[og]"
playwright install chromium  # bundled browser pin

# Frontend
cd frontend && npm install --save html2canvas@^1.4.1
```

**Version verification (performed 2026-04-30):**
- `pip index versions playwright` → `1.59.0` latest [VERIFIED]
- `npm view html2canvas version` → `1.4.1` (released 2022-01-22, stable) [VERIFIED]

## Architecture Patterns

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│ SOCIAL CRAWLER (Twitter/LinkedIn/Slack)                                     │
│   GET /race/<run_id>                                                        │
└──────────────────┬──────────────────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FastAPI: @app.get("/race/{run_id}", response_class=HTMLResponse)  [NEW]     │
│   1. _validate_run_id(run_id) → 400 if invalid                              │
│   2. (RUNS_DIR / f"{run_id}.json").exists() → if not, still 200 (SPA shows  │
│      error in-app; meta tags omit og:image to avoid social-crawler 404)     │
│   3. Read frontend/dist/index.html bytes                                    │
│   4. Inject <meta property="og:image" content="https://host/race/<id>/og.png">│
│      Inject <meta name="twitter:image"> + og:url + og:type + og:title +     │
│        og:description + twitter:card=summary_large_image                    │
│   5. Return HTMLResponse                                                    │
└──────────────────┬──────────────────────────────────────────────────────────┘
                   │ then crawler fetches:
                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ FastAPI: @app.get("/race/{run_id}/og.png")           [NEW]                  │
│   1. _validate_run_id → 400                                                 │
│   2. (RUNS_DIR / f"{run_id}.json").exists() → 404 if missing  [OG-04]       │
│   3. cache_path = data/og/<run_id>-v<OG_LAYOUT_VERSION>.png                 │
│   4. cleanup: glob data/og/<run_id>-v*.png, delete mismatches  [OG-04]      │
│   5. if cache_path.exists(): return FileResponse(cache_path)  [cache hit]   │
│   6. async with og_render_lock: bytes = await render_og_png(run_id)         │
│      ┌─ render_og_png ──────────────────────────────────────┐               │
│      │ ctx = await browser.new_context(viewport=1200x630)   │               │
│      │ page = await ctx.new_page()                          │               │
│      │ await page.goto(f"http://127.0.0.1:8008/race/{id}?og=1")              │
│      │ anchor = await page.query_selector('[data-og-anchor]')│               │
│      │ bytes = await anchor.screenshot(type="png")          │               │
│      │ await ctx.close()                                    │               │
│      └──────────────────────────────────────────────────────┘               │
│   7. cache_path.write_bytes(bytes)                                          │
│   8. return Response(bytes, media_type="image/png")                         │
│                                                                              │
│   On exception: 503 Service Unavailable + log; do NOT cache                 │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                       (singleton, lifespan)
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│ Playwright Browser (one Chromium process, app.state.browser)                │
│   launched in lifespan: await async_playwright().start() then chromium.launch()│
│   shut down in lifespan: await browser.close() then await playwright.stop() │
└─────────────────────────────────────────────────────────────────────────────┘

USER PATH (browser):
GET /race/<run_id> → SPA mounts → RacePage renders →
  user clicks "Copy headline image" beside banner →
    dynamic import('html2canvas') →
      capture document.querySelector('[data-og-anchor]') →
        canvas.toBlob(blob => navigator.clipboard.write([new ClipboardItem({'image/png': blob})]))
          on failure: trigger <a download="race-<run_id>.png"> click
```

### Recommended Project Structure
```
src/a2a_vs_mcp/race/
├── og.py                # NEW — Playwright lifespan, asyncio.Lock, render_og_png/render_heatmap_png, cache helpers
├── config.py            # EXISTING — add OG_LAYOUT_VERSION constant alongside HEATMAP_BASELINE
├── replay.py            # EXISTING — _validate_run_id reused
├── runs.py              # EXISTING — RUNS_DIR reused
└── heatmap.py           # EXISTING — get_heatmap unchanged

src/a2a_vs_mcp/web.py    # EDIT — register lifespan, mount 3 new routes (HTML + 2 PNG), import from race.og

frontend/src/features/race/
├── RacePage.tsx         # EDIT — read ?og=1 via useSearchParams, conditionally hide top bar/methodology/heatmap, attach data-og-anchor
├── components/
│   ├── CharacteristicFailureBanner.tsx  # EDIT — add adjacent CopyHeadlineImageButton
│   ├── CopyHeadlineImageButton.tsx       # NEW — html2canvas dynamic import + clipboard + download fallback
│   ├── HardnessFailureHeatmap.tsx        # EDIT — render HeatmapAnnotationStrip when ?og=1&surface=heatmap
│   └── HeatmapAnnotationStrip.tsx        # NEW — run_id · model · seed · n · task_ids strip on heatmap.png

data/og/                 # NEW dir, gitignored — disk cache
```

### Pattern 1: FastAPI Lifespan + Singleton Resource (D-61)
**What:** Launch a long-lived resource (Playwright Browser) at app startup; clean up at shutdown.
**When to use:** Any resource whose initialization cost > per-request work and is safe to share.

```python
# Source: FastAPI lifespan docs (current as of FastAPI 0.135) +
# Playwright async_playwright() pattern (https://playwright.dev/python/docs/api/class-playwright)
# src/a2a_vs_mcp/race/og.py

from contextlib import asynccontextmanager
import asyncio
from fastapi import FastAPI
from playwright.async_api import async_playwright, Browser, Playwright

OG_RENDER_LOCK = asyncio.Lock()  # D-61: serialize concurrent renders

@asynccontextmanager
async def og_lifespan(app: FastAPI):
    pw: Playwright = await async_playwright().start()
    browser: Browser = await pw.chromium.launch(headless=True)
    app.state.og_browser = browser
    app.state.og_playwright = pw
    try:
        yield
    finally:
        await browser.close()
        await pw.stop()

# In web.py:
# app = FastAPI(title="...", lifespan=og_lifespan)
```

### Pattern 2: Render-with-Lock Helper (D-61, D-62)
```python
# Source: Playwright Python async API + asyncio.Lock pattern.
# src/a2a_vs_mcp/race/og.py

OG_VIEWPORT = {"width": 1200, "height": 630}
HEATMAP_VIEWPORT = {"width": 1200, "height": 900}
RENDER_TIMEOUT_MS = 10_000  # network + selector + screenshot ceiling

async def render_og_png(run_id: str, browser: Browser, base_url: str = "http://127.0.0.1:8008") -> bytes:
    """Render the 1200×630 anchor PNG for run_id. Caller must hold OG_RENDER_LOCK."""
    ctx = await browser.new_context(viewport=OG_VIEWPORT, device_scale_factor=2)
    try:
        page = await ctx.new_page()
        page.set_default_timeout(RENDER_TIMEOUT_MS)
        await page.goto(f"{base_url}/race/{run_id}?og=1", wait_until="networkidle")
        anchor = await page.wait_for_selector("[data-og-anchor]", state="visible")
        return await anchor.screenshot(type="png")
    finally:
        await ctx.close()

async def render_heatmap_png(run_id: str, browser: Browser, base_url: str = "http://127.0.0.1:8008") -> bytes:
    ctx = await browser.new_context(viewport=HEATMAP_VIEWPORT, device_scale_factor=2)
    try:
        page = await ctx.new_page()
        page.set_default_timeout(RENDER_TIMEOUT_MS)
        await page.goto(f"{base_url}/race/{run_id}?og=1&surface=heatmap", wait_until="networkidle")
        anchor = await page.wait_for_selector("[data-heatmap-anchor]", state="visible")
        return await anchor.screenshot(type="png")
    finally:
        await ctx.close()
```

### Pattern 3: Cache + Cleanup Helper (D-66, OG-04)
```python
# Source: pathlib glob + write_bytes; standard disk-cache idiom.
# src/a2a_vs_mcp/race/og.py

from pathlib import Path
from .config import OG_LAYOUT_VERSION

OG_DIR: Path = Path(__file__).resolve().parents[3] / "data" / "og"

def og_cache_path(run_id: str, surface: str) -> Path:
    """surface ∈ {'og', 'heatmap'}; cache path data/og/<run_id>-<surface>-v<N>.png"""
    return OG_DIR / f"{run_id}-{surface}-v{OG_LAYOUT_VERSION}.png"

def cleanup_stale(run_id: str, surface: str) -> None:
    """Lazy delete-on-mismatch (Claude's discretion: lazy chosen over startup hook)."""
    OG_DIR.mkdir(parents=True, exist_ok=True)
    keep = og_cache_path(run_id, surface).name
    for p in OG_DIR.glob(f"{run_id}-{surface}-v*.png"):
        if p.name != keep:
            p.unlink(missing_ok=True)
```

### Pattern 4: html2canvas Lazy Import + Clipboard (D-64, D-65)
```typescript
// Source: html2canvas README (https://html2canvas.hertzen.com/) +
// MDN Clipboard API (https://developer.mozilla.org/en-US/docs/Web/API/ClipboardItem)
// frontend/src/features/race/components/CopyHeadlineImageButton.tsx

async function captureAndCopy(runId: string) {
  const anchor = document.querySelector<HTMLElement>('[data-og-anchor]');
  if (!anchor) return;

  // Dynamic import — bundle splits; first click pays the ~45KB cost.
  const { default: html2canvas } = await import('html2canvas');
  const canvas = await html2canvas(anchor, {
    backgroundColor: '#ffffff',
    scale: 2,           // 2× device pixels for 1200×630 retina output
    useCORS: true,
  });

  const blob: Blob | null = await new Promise(r => canvas.toBlob(r, 'image/png'));
  if (!blob) return;

  // Primary: ClipboardItem write (D-65)
  if (typeof ClipboardItem !== 'undefined' && navigator.clipboard?.write) {
    try {
      await navigator.clipboard.write([new ClipboardItem({ 'image/png': blob })]);
      return; // success
    } catch {
      /* fall through to download */
    }
  }

  // Fallback: download (D-65)
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `race-${runId}.png`;
  a.click();
  URL.revokeObjectURL(url);
}
```

### Anti-Patterns to Avoid
- **Mounting `/race/{run_id}` only as a SPA route:** social crawlers receive zero meta tags. MUST add a server-side HTML route.
- **`page.screenshot(clip={x,y,width,height})` with hardcoded coords:** breaks on every viewport tweak. Use `element.screenshot()` on `[data-og-anchor]`.
- **Sync Playwright API in FastAPI:** blocks the event loop. Use `playwright.async_api`.
- **Browser-per-request:** ~2-3s on every miss; defeats lifespan singleton.
- **`asyncio.Lock` in module scope without lifespan binding:** lock instance must be created INSIDE the running event loop or it binds to the wrong loop. Either initialize in lifespan or use the FastAPI app.state pattern.
- **Caching 503 responses:** never write the cache file in the exception path. Cache only on successful screenshot bytes.
- **`html2canvas` against `document.body`:** captures the whole viewport including chrome. Always target `[data-og-anchor]`.
- **`navigator.clipboard.write` outside a user gesture:** browsers reject silently. Must be triggered by `onClick`.
- **Allowing `OG_LAYOUT_VERSION` to read from env / runtime config:** D-66 says manual integer constant in source. Drift kills cache invariance.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DOM → PNG in browser | Custom canvas redraw / SVG `foreignObject` hand-roll | `html2canvas` | Cross-browser font + image edge cases (CITED: D-64) |
| Headless browser control | `subprocess` Chromium with stdin commands | `playwright.async_api` | Lifecycle, timeouts, screenshot crop are battle-tested |
| Image clipboard write | Construct base64 + execCommand | `navigator.clipboard.write([new ClipboardItem(...)])` | Only API that puts native PNG on OS clipboard |
| HTML meta-tag string concat | `f"<meta property='og:image' content='{url}'>"` interpolation | Use a small `_inject_meta_tags(html: str, tags: dict[str,str]) -> str` helper that escapes attribute values via `html.escape` | Crawler-fed values (run_id, title) need escaping or the OG embed breaks |
| Path-traversal regex | New regex per route | Reuse `_validate_run_id` from `race/replay.py:22` | Already tested at unit + route level (Phase 6/9) |
| ndjson run-existence probe | New file-system check | Reuse `RUNS_DIR / f"{run_id}.json"`.exists() | Single source of truth |
| Disk cache + invalidation | Custom hash-key store | `pathlib.Path` + glob + `unlink(missing_ok=True)` | Standard idiom; D-66 manual constant gives deterministic key |

**Key insight:** Phase 10 has heavy *infrastructure* novelty (Playwright + html2canvas) but zero *business-logic* novelty. The `_validate_run_id` + `RUNS_DIR` + `RaceReplayPayload` plumbing is already shipped. Phase 10 is "wire the existing payload through a screenshot pipeline." Don't reinvent any of the upstream pieces.

## Implementation Approach (per requirement)

### OG-01 — `/race/<run_id>/og.png` route + meta tags

**Backend route (`web.py`, mounted near line 858 next to `/api/race/heatmap`):**
```python
from fastapi.responses import FileResponse, Response
from .race.og import (
    OG_RENDER_LOCK, og_cache_path, cleanup_stale, render_og_png, OG_DIR,
)
from .race.config import OG_LAYOUT_VERSION

@app.get("/race/{run_id}/og.png")
async def race_og_png(run_id: str, request: Request) -> Response:
    try:
        _validate_run_id(run_id)
    except ValueError:
        raise HTTPException(400, "invalid run_id")
    if not (RUNS_DIR / f"{run_id}.json").exists():
        raise HTTPException(404, "run not found")  # OG-04: BEFORE Playwright spawn
    cleanup_stale(run_id, surface="og")  # D-66 lazy purge
    cache = og_cache_path(run_id, surface="og")
    if cache.exists():
        return FileResponse(cache, media_type="image/png")
    try:
        async with OG_RENDER_LOCK:
            data = await render_og_png(run_id, request.app.state.og_browser)
    except Exception as exc:
        raise HTTPException(503, "og render failed; please retry") from exc
    OG_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(data)
    return Response(data, media_type="image/png")
```

**Meta-tag injection (NEW `/race/{run_id}` HTML route — see §OG Meta-Tag Injection Path).**

### OG-02 — `/race/<run_id>/heatmap.png` route

Mirror of OG-01 with `surface="heatmap"`, viewport 1200×900, selector `[data-heatmap-anchor]`. Shares `OG_LAYOUT_VERSION`. Single test parametrization point.

### OG-03 — "Copy headline image" button

- New `CopyHeadlineImageButton.tsx` component, mounted beside `CharacteristicFailureBanner` in `RacePage.tsx`.
- MUI `<Button startIcon={<ContentCopyIcon />}>Copy headline image</Button>`.
- `onClick` calls `captureAndCopy(runId)` (Pattern 4 above).
- Test seam: mock `html2canvas` import + `navigator.clipboard.write` in vitest.

### OG-04 — 404 before Playwright + cleanup on bump

- Validation + existence check happen before any `await OG_RENDER_LOCK` acquisition.
- `cleanup_stale(run_id, surface)` runs unconditionally on every request (cheap glob; the 4-cell directory rarely accumulates files).
- Test matrix verifies bump invalidation by writing a stale `<id>-og-v0.png` then GETing with `OG_LAYOUT_VERSION = 1`.

## Module Layout & Files Modified

| File | Action | Purpose |
|------|--------|---------|
| `src/a2a_vs_mcp/race/og.py` | NEW | Lifespan ctx mgr, `OG_RENDER_LOCK`, `OG_DIR`, `og_cache_path`, `cleanup_stale`, `render_og_png`, `render_heatmap_png` |
| `src/a2a_vs_mcp/race/config.py` | EDIT | Add `OG_LAYOUT_VERSION: int = 1` constant alongside `HEATMAP_BASELINE` |
| `src/a2a_vs_mcp/web.py` | EDIT | Register `lifespan=og_lifespan` on `app`; add 3 routes: `/race/{run_id}` (HTML+meta inject), `/race/{run_id}/og.png`, `/race/{run_id}/heatmap.png` |
| `pyproject.toml` | EDIT | Add `[project.optional-dependencies] og = ["playwright>=1.59,<2"]` |
| `frontend/src/features/race/RacePage.tsx` | EDIT | Read `?og=1` via `useSearchParams`; conditional render hides top bar / methodology / heatmap; attach `data-og-anchor` to title-block + lane-row + banner subtree |
| `frontend/src/features/race/components/CopyHeadlineImageButton.tsx` | NEW | Lazy `import('html2canvas')` + ClipboardItem write + download fallback |
| `frontend/src/features/race/components/CharacteristicFailureBanner.tsx` | EDIT | Optional `actionSlot` prop; mount `<CopyHeadlineImageButton>` beside header (mounted from RacePage) |
| `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` | EDIT | When `?og=1&surface=heatmap`, render `<HeatmapAnnotationStrip>` + attach `data-heatmap-anchor` |
| `frontend/src/features/race/components/HeatmapAnnotationStrip.tsx` | NEW | Render `run_id · model · seed · n · task_ids` strip; reads run_meta event from `useRaceReplay`; only mounts under OG flag |
| `frontend/package.json` | EDIT | Add `"html2canvas": "^1.4.1"` |
| `data/og/` | NEW dir | Gitignored disk cache; created lazily on first miss |
| `.gitignore` | EDIT | Add `data/og/*.png` |
| `tests/race/test_og_routes.py` | NEW | D-63 mock-render test matrix (5 scenarios) |
| `tests/race/test_og_cache.py` | NEW | Cache-key + cleanup helpers unit tests |
| `frontend/src/features/race/components/CopyHeadlineImageButton.test.tsx` | NEW | Mocks html2canvas + clipboard; asserts download fallback path |

**Key signatures (for the planner):**
```python
# race/og.py
@asynccontextmanager async def og_lifespan(app: FastAPI) -> AsyncIterator[None]
OG_RENDER_LOCK: asyncio.Lock
OG_DIR: Path
def og_cache_path(run_id: str, surface: Literal["og", "heatmap"]) -> Path
def cleanup_stale(run_id: str, surface: Literal["og", "heatmap"]) -> None
async def render_og_png(run_id: str, browser: Browser, base_url: str = "...") -> bytes
async def render_heatmap_png(run_id: str, browser: Browser, base_url: str = "...") -> bytes
```

```python
# race/config.py — append
OG_LAYOUT_VERSION: int = 1
```

## Playwright Lifespan + Lock Pattern

```python
# src/a2a_vs_mcp/race/og.py
"""Playwright singleton + asyncio.Lock + render helpers for /race/<id>/og.png + heatmap.png.

D-61: Singleton Browser at FastAPI startup; asyncio.Lock serializes concurrent renders.
D-62: Render failure → caller raises HTTPException(503).
D-66: Cache pattern data/og/<run_id>-<surface>-v<OG_LAYOUT_VERSION>.png (lazy purge).
"""
from __future__ import annotations
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Literal

from fastapi import FastAPI
from playwright.async_api import async_playwright, Browser

from .config import OG_LAYOUT_VERSION

OG_DIR: Path = Path(__file__).resolve().parents[3] / "data" / "og"
OG_RENDER_LOCK: asyncio.Lock = asyncio.Lock()  # ⚠ pitfall: see Risks §1
RENDER_TIMEOUT_MS: int = 10_000
OG_VIEWPORT = {"width": 1200, "height": 630}
HEATMAP_VIEWPORT = {"width": 1200, "height": 900}

@asynccontextmanager
async def og_lifespan(app: FastAPI) -> AsyncIterator[None]:
    pw = await async_playwright().start()
    browser = await pw.chromium.launch(headless=True)
    app.state.og_browser = browser
    app.state.og_playwright = pw
    try:
        yield
    finally:
        await browser.close()
        await pw.stop()

async def render_og_png(run_id: str, browser: Browser,
                        base_url: str = "http://127.0.0.1:8008") -> bytes:
    """Caller MUST hold OG_RENDER_LOCK."""
    ctx = await browser.new_context(viewport=OG_VIEWPORT, device_scale_factor=2)
    try:
        page = await ctx.new_page()
        page.set_default_timeout(RENDER_TIMEOUT_MS)
        await page.goto(f"{base_url}/race/{run_id}?og=1", wait_until="networkidle")
        anchor = await page.wait_for_selector("[data-og-anchor]", state="visible")
        return await anchor.screenshot(type="png")
    finally:
        await ctx.close()

# render_heatmap_png mirrors with HEATMAP_VIEWPORT + ?og=1&surface=heatmap + [data-heatmap-anchor]

def og_cache_path(run_id: str, surface: Literal["og", "heatmap"]) -> Path:
    return OG_DIR / f"{run_id}-{surface}-v{OG_LAYOUT_VERSION}.png"

def cleanup_stale(run_id: str, surface: Literal["og", "heatmap"]) -> None:
    OG_DIR.mkdir(parents=True, exist_ok=True)
    keep = og_cache_path(run_id, surface).name
    for p in OG_DIR.glob(f"{run_id}-{surface}-v*.png"):
        if p.name != keep:
            p.unlink(missing_ok=True)
```

```python
# src/a2a_vs_mcp/web.py — at module-level, near line 61
from .race.og import og_lifespan
app = FastAPI(title="A2A vs MCP Demo UI", lifespan=og_lifespan)
```

## OG Meta-Tag Injection Path

**Critical finding:** `/race/<run_id>` is currently NOT mounted on FastAPI. `routes.tsx` (lines 73-132) declares `path: "race"` and `path: "race/:run_id"` purely in `createBrowserRouter`. Crawlers fetching `/race/<run_id>` get nothing — there is no fallback HTML route in `web.py`.

**Required:** Add a `@app.get("/race/{run_id}", response_class=HTMLResponse)` route that:
1. Validates `run_id` (reuses `_validate_run_id`).
2. Reads `frontend/dist/index.html` once (cache the bytes at module load).
3. Injects meta tags into `<head>`.
4. Returns the modified HTML so the SPA still mounts.

**Implementation:**
```python
# src/a2a_vs_mcp/web.py
import html as _html

# Cache the index.html bytes at import time (file is built into dist/).
_INDEX_HTML_CACHE: str | None = None
def _read_index_html() -> str:
    global _INDEX_HTML_CACHE
    if _INDEX_HTML_CACHE is None:
        _INDEX_HTML_CACHE = FRONTEND_INDEX.read_text(encoding="utf-8")
    return _INDEX_HTML_CACHE

def _inject_og_meta(html_doc: str, run_id: str, base_url: str) -> str:
    """Insert OG + Twitter meta tags before </head>. All values escaped."""
    title = f"Three-Lane Race · {run_id}"
    description = "How three protocol lanes recover (or don't) from injected faults — A2A vs MCP."
    image_url = f"{base_url}/race/{_html.escape(run_id, quote=True)}/og.png"
    page_url = f"{base_url}/race/{_html.escape(run_id, quote=True)}"
    tags = (
        f'<meta property="og:type" content="article">'
        f'<meta property="og:url" content="{page_url}">'
        f'<meta property="og:title" content="{_html.escape(title, quote=True)}">'
        f'<meta property="og:description" content="{_html.escape(description, quote=True)}">'
        f'<meta property="og:image" content="{image_url}">'
        f'<meta property="og:image:width" content="1200">'
        f'<meta property="og:image:height" content="630">'
        f'<meta name="twitter:card" content="summary_large_image">'
        f'<meta name="twitter:title" content="{_html.escape(title, quote=True)}">'
        f'<meta name="twitter:description" content="{_html.escape(description, quote=True)}">'
        f'<meta name="twitter:image" content="{image_url}">'
    )
    return html_doc.replace("</head>", tags + "</head>", 1)

@app.get("/race/{run_id}", response_class=HTMLResponse)
def race_run_html(run_id: str, request: Request) -> HTMLResponse:
    try:
        _validate_run_id(run_id)
    except ValueError:
        raise HTTPException(400, "invalid run_id")
    # Don't 404 here — let the SPA show its in-app empty state for unknown runs;
    # but only inject og:image if the run is real, so crawlers don't see a broken image.
    base_url = str(request.base_url).rstrip("/")
    if (RUNS_DIR / f"{run_id}.json").exists():
        html_out = _inject_og_meta(_read_index_html(), run_id, base_url)
    else:
        html_out = _read_index_html()  # crawler-safe: no og:image at all
    return HTMLResponse(html_out)

# ALSO add a `/race` (no run_id) route so the SPA still works on the live page.
@app.get("/race", response_class=HTMLResponse)
def race_html() -> Response:
    return render_react_app()
```

**Crawler compatibility verified:**
- Twitter: `twitter:card=summary_large_image`, `twitter:image`, dimensions 1200×630 → 2:1 ratio matches Twitter's preferred summary_large_image specs.
- LinkedIn: `og:image` + `og:image:width/height` + absolute URL → required by LinkedIn's Post Inspector.
- Slack/Discord: `og:title`, `og:description`, `og:image`, `og:url` → standard OpenGraph unfurl.
- All values HTML-attribute-escaped via `html.escape(..., quote=True)` to defeat T-08-08-style injection.

[CITED: ogp.me OpenGraph spec; Twitter cards documentation; LinkedIn Post Inspector requirements]

## ?og=1 RacePage Variant + data-og-anchor element pin

**Pattern:** same-component conditional. `RacePage.tsx` already has 4 mode flags (`__testState`, `isMobile`, `isReplay`, plus the page-state derivation); adding `og` is one more `useSearchParams` boolean. A separate `OgRacePage` would duplicate the lane-card layout.

```typescript
// frontend/src/features/race/RacePage.tsx — additions

import { useSearchParams } from "react-router-dom";

export function RacePage({ __testState }: RacePageProps = {}) {
  const [searchParams] = useSearchParams();
  const isOg = searchParams.get("og") === "1";
  const ogSurface = searchParams.get("surface");  // "heatmap" | null

  // ... existing live/replay dispatch ...

  // OG mode forces replay shape: ?og=1 always implies a run_id is present.
  // If isOg && !run_id, render an explicit empty placeholder (Playwright never reaches this).

  return (
    <Box data-testid={isReplay ? "race-replay-mode" : "race-live-mode"}>
      {/* Top bar: hide when isOg */}
      {!isOg ? (
        <RaceStatusStrip state={pageState} runId={baseState.run_id} timestampLabel={null} />
      ) : null}

      {/* Scrubber: hide when isOg */}
      {isReplay && !isOg ? <ReplayScrubber ... /> : null}

      <Container component="main" sx={{ maxWidth: 1200, py: isOg ? 2 : 6 }}>
        {/* OG ANCHOR: title-block + lane-row + banner only.
            HEATMAP and METHODOLOGY excluded per CONTEXT §specifics line 528. */}
        {ogSurface !== "heatmap" ? (
          <Box data-og-anchor sx={{ width: 1200, ...(isOg ? { bgcolor: "background.default" } : {}) }}>
            <Stack spacing={isOg ? 3 : 6}>
              {/* title block */}
              <Box>
                <Typography variant="overline" sx={{ color: "secondary.main" }}>
                  Three-Lane Failure Race
                </Typography>
                <Typography variant="h1" sx={{ color: "primary.main", maxWidth: 900 }}>
                  How three protocol lanes recover (or don't) from injected faults
                </Typography>
              </Box>
              {/* lane row */}
              <Box data-testid="race-lane-row" sx={{ display: "flex", flexDirection: { xs: "column", md: "row" }, gap: 4 }}>
                <RaceLaneCard lane={baseState.lanes.pure_mcp} />
                <RaceLaneCard lane={baseState.lanes.pure_a2a} />
                <RaceLaneCard lane={baseState.lanes.hybrid} />
              </Box>
              {/* banner */}
              {BANNER_VISIBLE_STATES.includes(pageState) ? (
                <CharacteristicFailureBanner header={bannerHeader} clause={bannerClause} />
              ) : null}
              {/* COPY-HEADLINE BUTTON — hidden in OG mode; visible only in live UI */}
              {!isOg && BANNER_VISIBLE_STATES.includes(pageState) ? (
                <CopyHeadlineImageButton runId={run_id ?? ""} />
              ) : null}
            </Stack>
          </Box>
        ) : null}

        {/* Methodology: hide when isOg */}
        {!isOg ? <MethodologySection /> : null}

        {/* Heatmap: hidden in og.png mode; visible (with annotation strip) in heatmap.png mode */}
        {!isOg || ogSurface === "heatmap" ? (
          <Box {...(ogSurface === "heatmap" ? { "data-heatmap-anchor": true, sx: { width: 1200 } } : {})}>
            <HardnessFailureHeatmap ogAnnotation={ogSurface === "heatmap"} runId={run_id ?? null} />
          </Box>
        ) : null}
      </Container>
    </Box>
  );
}
```

**`data-og-anchor` element:** the new wrapping `<Box data-og-anchor>` around `[title-block + lane-row + banner]` — a 1200×~630 region. Playwright's `anchor.screenshot()` crops to this element's bounding box automatically; height naturally matches the OG aspect ratio because the title block's typography + 3 lane cards + banner together sit close to 630px at the chosen MUI spacing.

## html2canvas Lazy-Load + Clipboard Pattern

```typescript
// frontend/src/features/race/components/CopyHeadlineImageButton.tsx
import { Button } from "@mui/material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { useState } from "react";

interface Props { runId: string; }

export function CopyHeadlineImageButton({ runId }: Props) {
  const [busy, setBusy] = useState(false);
  const [feedback, setFeedback] = useState<"copied" | "downloaded" | "error" | null>(null);

  async function onClick() {
    if (busy || !runId) return;
    setBusy(true); setFeedback(null);
    try {
      const anchor = document.querySelector<HTMLElement>("[data-og-anchor]");
      if (!anchor) throw new Error("no og anchor");

      const { default: html2canvas } = await import("html2canvas");  // lazy chunk
      const canvas = await html2canvas(anchor, {
        backgroundColor: "#ffffff",
        scale: 2,
        useCORS: true,
        logging: false,
      });

      const blob = await new Promise<Blob | null>(r => canvas.toBlob(r, "image/png"));
      if (!blob) throw new Error("toBlob failed");

      // Primary: ClipboardItem (D-65)
      const clipboardOk =
        typeof window.ClipboardItem !== "undefined" &&
        typeof navigator.clipboard?.write === "function";
      if (clipboardOk) {
        try {
          await navigator.clipboard.write([new ClipboardItem({ "image/png": blob })]);
          setFeedback("copied");
          return;
        } catch {
          /* fall through to download */
        }
      }
      // Fallback: download
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `race-${runId}.png`;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
      setFeedback("downloaded");
    } catch {
      setFeedback("error");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Button
      onClick={onClick}
      disabled={busy}
      startIcon={<ContentCopyIcon />}
      variant="outlined"
      data-testid="copy-headline-image-button"
      aria-live="polite"
    >
      {busy ? "Capturing…"
        : feedback === "copied" ? "Copied to clipboard"
        : feedback === "downloaded" ? "Downloaded"
        : feedback === "error" ? "Capture failed — retry"
        : "Copy headline image"}
    </Button>
  );
}
```

**Cross-browser notes:**
- Chrome/Edge: ClipboardItem + image/png supported since 2021. [HIGH]
- Safari (macOS 13.1+, iOS 16.4+): supported. [VERIFIED via MDN compatibility table]
- Firefox: `ClipboardItem` is available behind a flag in older versions; treated as unsupported by feature detection — falls through to download. [MEDIUM — Firefox image/png clipboard write was being shipped through 2024-2026; the runtime feature check + try/catch is the right pattern regardless]

**Bundle impact:** dynamic `import('html2canvas')` produces a separate Vite chunk. First click pays ~45KB gzipped. Initial page-load size unchanged.

## Mobile ?mode=summary Wiring (close Phase 8 placeholder)

Phase 8 left this branch (RacePage.tsx:79-85):
```tsx
if (isMobile && !__testState) {
  return (
    <Box data-testid="race-mobile-summary-placeholder" sx={{ p: 4, textAlign: "center" }}>
      <Typography variant="body1">Loading summary…</Typography>
    </Box>
  );
}
```

**Phase 10 wires:**
```tsx
if (isMobile && !__testState) {
  // Read run_id (replay) or null (live mode → still placeholder text).
  const ogImageUrl = run_id ? `/race/${run_id}/og.png` : null;
  return (
    <Box data-testid="race-mobile-summary" sx={{ p: 2, textAlign: "center" }}>
      {ogImageUrl ? (
        <Box
          component="img"
          src={ogImageUrl}
          alt={`Race summary for ${run_id}`}
          loading="lazy"
          sx={{ width: "100%", maxWidth: 1200, height: "auto", borderRadius: 2 }}
          onError={(e) => {
            // 503 from Playwright → degrade to text marker; user can rotate to landscape.
            (e.currentTarget as HTMLImageElement).style.display = "none";
          }}
        />
      ) : (
        <Typography variant="body1">Open on desktop for the live race UI.</Typography>
      )}
    </Box>
  );
}
```

**Why this shape:**
- No Playwright on mobile: the `<img>` GET hits the *same* `/race/{run_id}/og.png` route. If desktop user already loaded the page, the cache file exists and the mobile fetch is a static FileResponse. If mobile is the first visitor, the route triggers a Playwright render, which runs *server-side* (mobile device unaffected); the lifespan singleton handles it.
- No base64 inlining: keeps the Phase 8 placeholder boundary clean — only the `<img src>` URL is the new wiring; nothing else in `RacePage.tsx` mobile branch grows.
- `onError` graceful degradation: if the route 503s (D-62), the image hides; the user can rotate to landscape for the full UI.
- Closes UIRACE-05 success criterion (mobile <480px renders cropped anchor PNG + heatmap; ROADMAP says "Phase 8 ships placeholder; Phase 10 ships full PNG").

## Heatmap.png Annotation Strip Rendering Surface

**Decision:** sibling component `HeatmapAnnotationStrip.tsx` rendered conditionally inside `HardnessFailureHeatmap`, not a separate route-only component.

**Why:** `HardnessFailureHeatmap` already reads `useRaceHeatmap()` for `data.baseline.{model, seed, task_ids}` (lines 88-94). The annotation strip needs `run_id · model · seed · n · task_ids` — same data plus `run_id` (from `useParams`) and `n` (run count, available in `data` from Phase 9). Adding a sibling component keeps the existing footer alone (which is the live-UI footer, different visual style) and gates the screenshot-only strip.

```typescript
// frontend/src/features/race/components/HeatmapAnnotationStrip.tsx
import { Box, Typography } from "@mui/material";
import type { HeatmapPayload } from "../../../lib/types/race";

interface Props {
  runId: string;
  baseline: HeatmapPayload["baseline"];
  n: number;
}

export function HeatmapAnnotationStrip({ runId, baseline, n }: Props) {
  return (
    <Box
      data-testid="heatmap-annotation-strip"
      sx={{
        bgcolor: "background.paper",
        borderTop: "2px solid",
        borderColor: "primary.main",
        p: 2,
        mt: 2,
      }}
    >
      <Typography variant="caption" sx={{ color: "text.primary", fontFamily: "monospace" }}>
        {runId} · {baseline.model} · seed={baseline.seed} · n={n} · {baseline.task_ids.join(", ")}
      </Typography>
    </Box>
  );
}
```

`HardnessFailureHeatmap` accepts new optional props `ogAnnotation?: boolean` + `runId?: string | null`; mounts the strip when `ogAnnotation && runId && data`. `n` reads from `data.n_runs` (Phase 9 already exposes this — confirm via `lib/types/race.ts` HeatmapPayload). The Phase 9 D-47 empty-state never-unmount rule is preserved (the strip is additive, not a replacement).

## Test Strategy (D-63 mock-render — inject mechanism + matrix)

**Mock injection mechanism:** module-level monkeypatch via `monkeypatch.setattr` on `a2a_vs_mcp.web.render_og_png` and `render_heatmap_png`. Pattern matches Phase 9 `test_replay_route.py:30` (`monkeypatch.setattr("a2a_vs_mcp.web.RUNS_DIR", tmp_path)`).

```python
# tests/race/test_og_routes.py
"""OG-01..OG-04 PNG routes — mock render fn (D-63)."""
from __future__ import annotations
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from a2a_vs_mcp.web import app


@pytest.fixture
def og_env(tmp_path, monkeypatch):
    runs = tmp_path / "runs"; runs.mkdir()
    og = tmp_path / "og"; og.mkdir()
    monkeypatch.setattr("a2a_vs_mcp.web.RUNS_DIR", runs)
    monkeypatch.setattr("a2a_vs_mcp.race.og.OG_DIR", og)
    monkeypatch.setattr("a2a_vs_mcp.race.config.OG_LAYOUT_VERSION", 1)
    return {"runs": runs, "og": og}


def _write_run(runs: Path, run_id: str) -> None:
    (runs / f"{run_id}.json").write_text(
        json.dumps({"event_type": "run_meta", "trace_schema_version": "1.0",
                    "model": "claude-sonnet-4-6", "seed": 42, "task_id": "summarize_repo",
                    "lane": "pure_mcp", "run_id": run_id}) + "\n"
    )


# Test 1 — 404 BEFORE Playwright spawn (OG-04)
def test_unknown_run_id_returns_404_without_render(og_env, monkeypatch):
    calls = []
    async def fake_render(*a, **k): calls.append(1); return b"x"
    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_render)
    r = TestClient(app).get("/race/r-doesnotexist/og.png")
    assert r.status_code == 404
    assert calls == []  # render NEVER called


# Test 2 — invalid run_id returns 400 (path-traversal guard)
def test_invalid_run_id_returns_400(og_env):
    r = TestClient(app).get("/race/INVALID@CHAR/og.png")
    assert r.status_code == 400


# Test 3 — cache miss → render once + write cache (200)
def test_cache_miss_renders_once_and_writes(og_env, monkeypatch):
    _write_run(og_env["runs"], "r-1")
    calls = []
    async def fake_render(run_id, browser, base_url="..."):
        calls.append(run_id); return b"PNGBYTES"
    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_render)
    r = TestClient(app).get("/race/r-1/og.png")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content == b"PNGBYTES"
    assert calls == ["r-1"]
    assert (og_env["og"] / "r-1-og-v1.png").read_bytes() == b"PNGBYTES"


# Test 4 — cache hit → no render (200 from disk)
def test_cache_hit_skips_render(og_env, monkeypatch):
    _write_run(og_env["runs"], "r-2")
    (og_env["og"] / "r-2-og-v1.png").write_bytes(b"CACHED")
    calls = []
    async def fake_render(*a, **k): calls.append(1); return b"NEW"
    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_render)
    r = TestClient(app).get("/race/r-2/og.png")
    assert r.status_code == 200
    assert r.content == b"CACHED"
    assert calls == []


# Test 5 — OG_LAYOUT_VERSION bump invalidates + cleans up old (OG-04)
def test_version_bump_invalidates_and_cleans(og_env, monkeypatch):
    _write_run(og_env["runs"], "r-3")
    (og_env["og"] / "r-3-og-v0.png").write_bytes(b"OLD")
    monkeypatch.setattr("a2a_vs_mcp.race.config.OG_LAYOUT_VERSION", 1)
    async def fake_render(*a, **k): return b"NEW"
    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_render)
    r = TestClient(app).get("/race/r-3/og.png")
    assert r.status_code == 200
    assert r.content == b"NEW"
    assert not (og_env["og"] / "r-3-og-v0.png").exists()  # cleaned up
    assert (og_env["og"] / "r-3-og-v1.png").read_bytes() == b"NEW"


# Test 6 — render exception → 503, no cache write (D-62)
def test_render_exception_returns_503_and_does_not_cache(og_env, monkeypatch):
    _write_run(og_env["runs"], "r-4")
    async def fake_render(*a, **k): raise RuntimeError("playwright crashed")
    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_render)
    r = TestClient(app).get("/race/r-4/og.png")
    assert r.status_code == 503
    assert not list(og_env["og"].glob("r-4-*.png"))


# Test 7 — heatmap.png mirrors og.png (parametrized)
@pytest.mark.parametrize("surface,route", [("og", "/race/r-5/og.png"), ("heatmap", "/race/r-5/heatmap.png")])
def test_both_surfaces_share_invariants(og_env, monkeypatch, surface, route):
    _write_run(og_env["runs"], "r-5")
    async def fake_og(*a, **k): return b"OG"
    async def fake_hm(*a, **k): return b"HM"
    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_og)
    monkeypatch.setattr("a2a_vs_mcp.web.render_heatmap_png", fake_hm)
    r = TestClient(app).get(route)
    assert r.status_code == 200
    expected = b"HM" if surface == "heatmap" else b"OG"
    assert r.content == expected


# Test 8 — meta tag injection on /race/{run_id} HTML (OG-01)
def test_html_route_injects_og_meta_tags(og_env):
    _write_run(og_env["runs"], "r-6")
    r = TestClient(app).get("/race/r-6")
    assert r.status_code == 200
    body = r.text
    assert 'property="og:image"' in body
    assert 'content="http://testserver/race/r-6/og.png"' in body
    assert 'name="twitter:card" content="summary_large_image"' in body
    assert 'property="og:url"' in body


# Test 9 — meta tags omitted for unknown run_id (no broken-image embed)
def test_html_route_omits_image_for_unknown_run(og_env):
    r = TestClient(app).get("/race/r-doesnotexist")
    assert r.status_code == 200  # SPA mounts; in-app empty state
    assert 'property="og:image"' not in r.text
```

**Frontend tests** (`CopyHeadlineImageButton.test.tsx`):
- Mock `html2canvas` via `vi.mock('html2canvas', () => ({ default: vi.fn(...) }))`.
- Mock `navigator.clipboard.write` and `window.ClipboardItem`.
- Test 1: clipboard write succeeds → button text "Copied to clipboard".
- Test 2: ClipboardItem undefined → download path triggers (`document.createElement('a').click` spy).
- Test 3: html2canvas rejection → "Capture failed — retry".
- Test 4: missing `[data-og-anchor]` → no-op + error feedback.

## Dependency Pinning

| Dep | Version | Pin Strategy | Notes |
|-----|---------|-------------|-------|
| `playwright` (Python) | `>=1.59,<2` in `pyproject.toml [project.optional-dependencies] og` | Major-version cap; minor-floor at known-good | Latest as of 2026-04-30 [VERIFIED via `pip index versions playwright`] |
| Chromium | bundled by Playwright; pinned via `playwright install chromium` | Playwright's version-locked download URL is the pin | No separate Chromium binary version file. Each Playwright minor pins a specific Chromium build. To upgrade Chromium, bump Playwright. |
| `html2canvas` | `^1.4.1` in `frontend/package.json` | Caret (allows patch+minor up to 2.0) | Latest as of 2026-04-30 [VERIFIED via `npm view html2canvas version`]; library is stable (last release Jan 2022) |

**Install sequence:**
```bash
pip install -e ".[og,dev]"
playwright install chromium  # downloads ~140MB; idempotent
cd frontend && npm install
```

**CI note (D-63):** Tests mock the render function — Chromium download is NOT required in CI. `playwright install chromium` runs only in dev/runtime environments.

## Risks + Landmines

### Risk 1: Module-level `asyncio.Lock()` binds to wrong event loop
**What goes wrong:** `OG_RENDER_LOCK = asyncio.Lock()` evaluated at import time may bind to a transient event loop, then never acquire under the running uvicorn loop.
**Mitigation:** Either (a) construct the lock inside `og_lifespan` and stash on `app.state.og_render_lock`, or (b) trust that Python 3.10+ makes module-level `asyncio.Lock()` lazy-bind to the calling loop — which it does as of 3.10+. Plan recommends option (a) for clarity and reliability.

### Risk 2: Playwright `goto(...)` to `127.0.0.1:8008` requires uvicorn to be the same process
**What goes wrong:** Playwright fetches `http://127.0.0.1:8008/race/<id>?og=1` to render. If uvicorn is bound only to a different host/port, the goto fails.
**Mitigation:** `serve_ui.py` binds 8008. Plan can read host/port from a single source. For tests with mock render fn, this is irrelevant.

### Risk 3: Self-referential render — Playwright loads `/race/<id>` which itself triggers OG meta-tag injection
**What goes wrong:** During render, Playwright hits the SPA HTML route, which parses + injects meta tags. Slight extra latency but harmless (meta tags don't affect canvas/screenshot output).
**Mitigation:** None needed; behavior is correct. Worth noting in PLAN.md so this isn't flagged as a bug.

### Risk 4: `wait_until="networkidle"` is unreliable for SPAs that maintain WS connections
**What goes wrong:** `RacePage` opens a WebSocket in live mode. `networkidle` may never fire if WS keeps the connection considered "active."
**Mitigation:** In `?og=1` mode, `RacePage` already enters replay mode (run_id present). Replay mode does NOT open a WS (`liveState = useRaceStream(false)` when `isReplay`). For extra safety, also gate WS opening on `!isOg` in `RacePage.tsx`. Use `wait_until="domcontentloaded"` + explicit `wait_for_selector("[data-og-anchor]", state="visible")` instead of networkidle.

### Risk 5: html2canvas + Material UI font / cross-origin assets
**What goes wrong:** html2canvas can't render `@font-face` URLs from cross-origin sources without CORS headers. Result: text falls back to system font in the canvas screenshot.
**Mitigation:** App uses Segoe UI fallback (TODO 6). All fonts are local. `useCORS: true` covers any future cross-origin font.

### Risk 6: `data/og/` not in `.gitignore`
**What goes wrong:** Cached PNGs accidentally committed.
**Mitigation:** Plan adds `data/og/*.png` to `.gitignore` as a Wave 0 task.

### Risk 7: SPA route hijacks server route in serving order
**What goes wrong:** FastAPI's static file mounts (`/assets`) + the catch-all SPA route order can shadow the new `/race/{run_id}` HTML route.
**Mitigation:** Mount the explicit GET `/race/{run_id}` route BEFORE any catch-all. There is currently no SPA catch-all in `web.py` (each SPA path is registered explicitly: `/`, `/learn`, `/reports`, `/traces`, `/presentation`, `/trends`, `/reports/{report_name}`). Phase 10 adds explicit `/race`, `/race/{run_id}` routes — same pattern. No conflict.

### Risk 8: Playwright downloads Chromium on first install — ~140MB
**What goes wrong:** Cold dev install adds ~30s + bandwidth.
**Mitigation:** Document `playwright install chromium` in the README. Acceptable for the demo.

### Risk 9: `_INDEX_HTML_CACHE` becomes stale on frontend rebuild
**What goes wrong:** Module-level cache of `index.html` survives across frontend rebuilds during dev.
**Mitigation:** For dev, restart uvicorn after `npm run build`. Or skip the cache and read every request (small file, negligible cost). Plan can pick.

### Risk 10: `wait_for_selector` timing — `useRaceReplay` is async
**What goes wrong:** Playwright loads `/race/<id>?og=1`, which fires `useRaceReplay(run_id)` — a `fetch('/api/race/runs/<id>/trace')` that needs to complete, dispatch through the reducer, render lanes. If `wait_for_selector("[data-og-anchor]")` doesn't also wait for lane data, screenshot may capture empty lanes.
**Mitigation:** Add an explicit "ready" sentinel: when `replay.trace` has been folded, RacePage adds a `data-og-ready="true"` attribute to the anchor. Playwright waits via `page.wait_for_selector('[data-og-anchor][data-og-ready="true"]')`. Critical landmine — without this, OG renders ship blank cards.

### Risk 11: Two FastAPI lifespans
**What goes wrong:** If a future feature adds another lifespan, FastAPI takes only one `lifespan=` arg.
**Mitigation:** Compose: write a single `og_lifespan` now; if multiple emerge later, refactor to a fan-out lifespan. Document in og.py docstring.

## Plan Decomposition Suggestion

Suggested 5-plan slicing across 3 waves. Granularity is `coarse` per `.planning/config.json`.

### Wave 1 — Backend foundation (parallel-safe; nothing depends on frontend yet)

**10-01-PLAN: OG render module + lifespan + Playwright dependency**
- NEW `src/a2a_vs_mcp/race/og.py` (lifespan ctx mgr, `OG_RENDER_LOCK`, `OG_DIR`, `og_cache_path`, `cleanup_stale`, `render_og_png`, `render_heatmap_png` skeletons)
- EDIT `src/a2a_vs_mcp/race/config.py` (add `OG_LAYOUT_VERSION = 1`)
- EDIT `pyproject.toml` (add `[project.optional-dependencies] og`)
- EDIT `.gitignore` (add `data/og/*.png`)
- Unit tests: `test_og_cache.py` for `og_cache_path` + `cleanup_stale`
- Closes: dependency wiring, module structure
- Requirements touched: foundation for OG-01..OG-04

**10-02-PLAN: PNG routes + meta-tag HTML route + D-63 test matrix**
- EDIT `src/a2a_vs_mcp/web.py`: register `lifespan=og_lifespan`; add `/race/{run_id}`, `/race/{run_id}/og.png`, `/race/{run_id}/heatmap.png`, `/race` routes; helpers `_read_index_html`, `_inject_og_meta`
- NEW `tests/race/test_og_routes.py` (9 tests above — full D-63 matrix)
- Requirements: OG-01 (route + meta), OG-02 (heatmap.png route), OG-04 (404 + invalidation + cleanup)
- Depends on: 10-01

### Wave 2 — Frontend `?og=1` variant + screenshot anchor (parallel-safe with Wave 3)

**10-03-PLAN: RacePage `?og=1` mode + `data-og-anchor` + heatmap surface flag**
- EDIT `frontend/src/features/race/RacePage.tsx`: `useSearchParams` → `isOg` + `ogSurface`; conditional render hides top bar / scrubber / methodology; wraps title-block + lane-row + banner in `<Box data-og-anchor>`; passes `ogAnnotation` + `runId` to `HardnessFailureHeatmap`; gates WS open on `!isOg`; adds `data-og-ready` sentinel after replay.trace folds
- NEW `frontend/src/features/race/components/HeatmapAnnotationStrip.tsx`
- EDIT `frontend/src/features/race/components/HardnessFailureHeatmap.tsx`: optional `ogAnnotation` + `runId` props; mount strip + `data-heatmap-anchor` when set
- Unit tests: `RacePage.test.tsx` updates verifying `?og=1` chrome strip; `HeatmapAnnotationStrip.test.tsx`
- Requirements: OG-01 (screenshot surface), OG-02 (heatmap surface)
- Depends on: 10-01 (`OG_LAYOUT_VERSION` constant referenced indirectly via cache)

### Wave 3 — Client-side fallback + mobile wiring (parallel with Wave 2; both touch RacePage but different sections — keep an eye on merge conflict in RacePage.tsx)

**10-04-PLAN: CopyHeadlineImageButton (html2canvas + clipboard + download)**
- NEW `frontend/src/features/race/components/CopyHeadlineImageButton.tsx`
- EDIT `frontend/package.json` (add `html2canvas: ^1.4.1`)
- EDIT `frontend/src/features/race/RacePage.tsx`: mount `<CopyHeadlineImageButton>` beside banner when `!isOg && BANNER_VISIBLE_STATES.includes(pageState)`
- NEW `frontend/src/features/race/components/CopyHeadlineImageButton.test.tsx` (4 tests above)
- Requirements: OG-03
- Depends on: 10-03 (needs `data-og-anchor` to exist in DOM tree)

**10-05-PLAN: Mobile `?mode=summary` wiring + Phase 8 placeholder closure**
- EDIT `frontend/src/features/race/RacePage.tsx`: replace mobile placeholder Box (lines 79-85) with `<img src={/race/${run_id}/og.png}>` + onError graceful degradation
- Frontend test: mobile-viewport mock + assert `<img>` element references the OG route
- Requirements: closes Phase 8 placeholder (UIRACE-05 mobile success criterion handoff)
- Depends on: 10-02 (route must exist), 10-03 (RacePage already touched)

### Wave assignment summary
- **Wave 1 (parallel-safe):** 10-01, 10-02
- **Wave 2:** 10-03 (depends on 10-01 constants only)
- **Wave 3:** 10-04, 10-05 (both depend on 10-03 RacePage shape — may need careful merge ordering or single-author execution)

**Slimmer alternative (3 plans, if planner prefers fewer files):**
- 10-01 (everything backend: og.py + config.py + routes + tests)
- 10-02 (everything frontend except canvas: RacePage `?og=1` + HeatmapAnnotationStrip + mobile img)
- 10-03 (CopyHeadlineImageButton + html2canvas dep)

## Common Pitfalls

### Pitfall 1: Playwright `wait_until="networkidle"` hanging on SPA
**What goes wrong:** Page never reaches networkidle because the SPA holds a WS or polling.
**Why it happens:** WebSocket connections keep network "active" indefinitely.
**How to avoid:** Use `wait_until="domcontentloaded"` + explicit `wait_for_selector('[data-og-anchor][data-og-ready="true"]')`. Gate WS opening on `!isOg`.
**Warning signs:** Render times > 5s; Playwright timeout exceptions in dev.

### Pitfall 2: ClipboardItem rejected silently in Firefox
**What goes wrong:** `navigator.clipboard.write([new ClipboardItem(...)])` rejects with `NotAllowedError` in some Firefox configurations.
**How to avoid:** Wrap clipboard write in try/catch; fall through to download.
**Warning signs:** User reports "nothing happened" on click in Firefox.

### Pitfall 3: html2canvas blanks on `position: fixed` / `position: sticky`
**What goes wrong:** Fixed/sticky chrome elements render incorrectly or duplicate in canvas.
**How to avoid:** `?og=1` already strips top bar; banner is `position: static`. Verify no MUI default fixed positioning leaks through.

### Pitfall 4: OG meta tags rejected by Slack/LinkedIn for non-absolute URLs
**What goes wrong:** Relative `og:image="/race/x/og.png"` works in Twitter but fails LinkedIn parsers.
**How to avoid:** Always construct absolute URL via `request.base_url` + path. Test crawler with LinkedIn Post Inspector before sharing.

### Pitfall 5: `OG_LAYOUT_VERSION` bump forgotten after layout edit
**What goes wrong:** Stale-OG embeds in shared URLs.
**How to avoid:** Add a checklist item to PR template: "Did this PR change `data-og-anchor` subtree styling? If yes, bump `OG_LAYOUT_VERSION`." Alternatively, a `pre-commit` hook that diffs RacePage.tsx against last-bumped commit. (Out of scope for v1.)

### Pitfall 6: Cache miss + rapid concurrent requests
**What goes wrong:** Two requests for same uncached run race past existence check; second waits on lock; first writes cache; second renders again unnecessarily.
**How to avoid:** Add a re-check inside the lock: `async with OG_RENDER_LOCK: if cache.exists(): return FileResponse(cache); ...`. Single-flight pattern.

### Pitfall 7: HTML route returns mocked-style stub instead of real index.html in tests
**What goes wrong:** Tests construct an empty `frontend/dist/index.html` for asserting injection; real shipping code reads non-existent file.
**How to avoid:** Test fixture writes a minimal `<html><head></head><body></body></html>` to a tmp index path; monkeypatch `_read_index_html` to return it. Real-prod path uses the Vite-built file.

## Code Examples (verified or from official docs)

### Playwright Python lifespan (from playwright.dev/python)
```python
# Source: https://playwright.dev/python/docs/api/class-playwright (latest)
async with async_playwright() as pw:
    browser = await pw.chromium.launch(headless=True)
    context = await browser.new_context(viewport={"width": 1200, "height": 630})
    page = await context.new_page()
    await page.goto("...")
    img_bytes = await page.screenshot(type="png")
    await context.close()
    await browser.close()
```

### Element-bounded screenshot
```python
# Source: https://playwright.dev/python/docs/screenshots (latest)
elem = await page.wait_for_selector('.my-element')
await elem.screenshot(path='element.png')
```

### html2canvas usage
```javascript
// Source: https://html2canvas.hertzen.com/ (1.4.1)
import html2canvas from 'html2canvas';
const canvas = await html2canvas(document.querySelector('#capture'));
canvas.toBlob(blob => { /* ... */ }, 'image/png');
```

### ClipboardItem (image/png)
```javascript
// Source: MDN https://developer.mozilla.org/en-US/docs/Web/API/ClipboardItem
const item = new ClipboardItem({ 'image/png': blob });
await navigator.clipboard.write([item]);
```

### FastAPI lifespan
```python
# Source: https://fastapi.tiangolo.com/advanced/events/ (current)
from contextlib import asynccontextmanager
@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    yield
    # shutdown
app = FastAPI(lifespan=lifespan)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| FastAPI `@app.on_event("startup")` | `lifespan=` context manager | FastAPI 0.93+ (2023) | We're on 0.135; use lifespan. |
| `pyppeteer` for headless Chromium | `playwright.async_api` | Playwright supplanted Pyppeteer ~2020 | Maintenance + async-native |
| `dom-to-image` for client snapshot | `html2canvas` (or `modern-screenshot`) | Stable for years | D-64 locks html2canvas |
| Server-rendered Twitter cards | Same — meta tags must be in initial HTML | Unchanged 2010s-present | Crawlers don't run JS |
| `document.execCommand('copy')` for clipboard | `navigator.clipboard.write([new ClipboardItem(...)])` | execCommand deprecated; ClipboardItem widely supported 2021+ | D-65 uses ClipboardItem |

**Deprecated/outdated:**
- `app.on_event("startup")` — superseded by lifespan (warning only; still works)
- `execCommand('copy')` for image data — never supported binary blobs reliably

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | LinkedIn Post Inspector requires absolute `og:image` URLs | OG Meta-Tag Injection | Medium — would only fail LinkedIn unfurl; Twitter/Slack would still work |
| A2 | Firefox `ClipboardItem` for `image/png` may be flag-gated | html2canvas Lazy-Load | Low — feature detection + try/catch already covers it; download fallback works |
| A3 | `wait_until="networkidle"` unreliable when WS is open | Risks §4 | Medium — if wrong, default config works; if right (likely), we need the `data-og-ready` sentinel |
| A4 | Playwright bundled Chromium is the deterministic pin | Dependency Pinning | Low — well-documented; verifiable by `playwright install --dry-run` |
| A5 | `n` (run count) is exposed in HeatmapPayload from Phase 9 | Heatmap.png annotation | Low — verifiable in `lib/types/race.ts`; if absent, derive from `cells[].recovery_rate.den` sum |
| A6 | `<img src="/race/<id>/og.png">` on mobile won't trigger Playwright on the user's device | Mobile wiring | None — Playwright always runs server-side; this is an `<img>` HTTP fetch |
| A7 | Module-level `asyncio.Lock()` in Python 3.10+ lazy-binds correctly | Risks §1 | Medium — recommendation to construct in lifespan removes the risk regardless |
| A8 | Master design's "~500ms-1s warm cache miss" is achievable | (Specifics summary) | Low — driven by Playwright performance; will measure during dev |
| A9 | `frontend/dist/index.html` is built before the server starts in production | Meta-tag injection | High — if dist doesn't exist, the OG HTML route falls back to the `render_react_app()` 503 path. Plan must guard. |

## Open Questions (RESOLVED)

1. **n (run count) field name in HeatmapPayload** — **(RESOLVED)** Plan 10-03 Task 2 directs executor to inspect `frontend/src/lib/types/race.ts` HeatmapPayload during implementation; if absent, derive from `Σ recovery_rate.den` per row. No blocker for planning.

2. **Should `/race` (no run_id) also gain the OG meta-tag treatment?** — **(RESOLVED)** Out of scope. Only `/race/{run_id}` URLs are shareable artifacts. `/race` returns plain `render_react_app()` per Plan 10-02.

3. **Single-flight on cache miss (Pitfall 6)** — **(RESOLVED)** Plan 10-02 Task 2 implements inside-lock re-check (2-line addition).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | All backend | ✓ | (existing project requires-python) | — |
| FastAPI lifespan | Browser singleton | ✓ | fastapi>=0.135 | — |
| `playwright` (Python) | render fns | ✗ (must install) | target 1.59 | none — required |
| Chromium (bundled by Playwright) | Real renders | ✗ (`playwright install chromium`) | locked by Playwright minor | for CI: D-63 mocks render fn — Chromium NOT required in CI |
| `html2canvas` | Client snapshot | ✗ (must install) | target 1.4.1 | none — required for OG-03 |
| `ContentCopyIcon` from `@mui/icons-material` | Button UI | ✓ | already in package.json (`@mui/icons-material: ^7.3.1`) | — |
| `useSearchParams` from react-router-dom | `?og=1` reading | ✓ | already in package.json | — |

**Missing dependencies with no fallback:** `playwright` (Python), `html2canvas` — both are install steps in the plan.
**Missing dependencies with fallback:** Chromium binary in CI — D-63 mocks render fn so CI does NOT need Chromium.

## Project Constraints (from CLAUDE.md)

- **Backend tests:** `pytest` (run on every plan completion).
- **Frontend tests:** `cd frontend && npm test` (vitest run).
- **Frontend dev:** `cd frontend && npm run dev` (Vite).
- **Start app:** `python serve_ui.py` (uvicorn 8008).
- **claude-mem (port 37701):** save significant decisions; query before starting work.
- **graphify:** read `graphify-out/GRAPH_REPORT.md` for architecture questions; run `graphify update .` after code edits.
- **gstack `/browse` skill:** for any web browsing — never `mcp__claude-in-chrome__*`.

These constraints are operational; Phase 10 implementation does not contradict any of them.

## Sources

### Primary (HIGH confidence)
- `/Users/.../A2AvsMCP/.planning/phases/10-og-image-and-sharing/10-CONTEXT.md` — D-61..D-66, all locked decisions
- `/Users/.../A2AvsMCP/.planning/REQUIREMENTS.md` §OG — OG-01..OG-04 verbatim
- `/Users/.../A2AvsMCP/.planning/ROADMAP.md` Phase 10 §Success Criteria
- `/Users/.../A2AvsMCP/src/a2a_vs_mcp/web.py` — confirmed: no `/race/{run_id}` HTML route exists (load-bearing finding)
- `/Users/.../A2AvsMCP/frontend/src/app/routes.tsx` — confirmed: `/race/:run_id` is a SPA-only route via `createBrowserRouter`
- `/Users/.../A2AvsMCP/src/a2a_vs_mcp/race/replay.py` — `_validate_run_id` reuse confirmed
- `/Users/.../A2AvsMCP/src/a2a_vs_mcp/race/config.py` — `HEATMAP_BASELINE` pattern; `OG_LAYOUT_VERSION` follows
- `/Users/.../A2AvsMCP/tests/race/test_replay_route.py` — D-63 mock injection mechanism (`monkeypatch.setattr` on bound symbol)
- `/Users/.../A2AvsMCP/frontend/src/features/race/RacePage.tsx` — Phase 8 placeholder (line 79-85), `data-og-anchor` insertion site
- `pip index versions playwright` (run 2026-04-30) → `1.59.0` latest [VERIFIED]
- `npm view html2canvas version` (run 2026-04-30) → `1.4.1` [VERIFIED]
- Playwright Python docs (https://playwright.dev/python/docs/api/class-playwright) — `async_playwright`, screenshots [CITED]
- FastAPI lifespan docs (https://fastapi.tiangolo.com/advanced/events/) [CITED]
- MDN Clipboard API + ClipboardItem (https://developer.mozilla.org/en-US/docs/Web/API/ClipboardItem) [CITED]

### Secondary (MEDIUM confidence)
- ogp.me OpenGraph spec — meta-tag schema [CITED]
- Twitter cards documentation — summary_large_image requirements [CITED]

### Tertiary (LOW confidence)
- Firefox ClipboardItem image/png support state — assumed flag-gated through 2024-2026; behavior verified empirically via try/catch fallback regardless [ASSUMED]

## Validation Architecture

> **Skipped per `.planning/config.json`:** `workflow.nyquist_validation: false`. Standard plan-checker dimensions apply (no Wave-0 test-framework gap analysis needed beyond the per-plan test files listed in Module Layout).

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — Playwright + html2canvas verified via live registry queries 2026-04-30
- Architecture (lifespan + lock + meta-injection): HIGH — load-bearing finding (no SPA-side OG injection possible) is grounded in `routes.tsx` + `web.py` reads
- Test strategy (D-63 mock pattern): HIGH — directly mirrors Phase 9 `test_replay_route.py:30` `monkeypatch.setattr` pattern
- Mobile `?mode=summary` wiring: HIGH — single-line change in existing placeholder branch; fully scoped
- Cross-browser ClipboardItem behavior: MEDIUM — Firefox edge cases handled via feature detection + try/catch; download fallback is universal
- `data-og-ready` sentinel timing (Risk 10): MEDIUM — proposed but not benchmarked; landmine flagged for plan-time verification

**Research date:** 2026-04-30
**Valid until:** 2026-05-30 (30 days — Playwright minors release ~monthly; html2canvas stable)

## RESEARCH COMPLETE

**Phase:** 10 — OG Image & Sharing
**Confidence:** HIGH on stack + architecture; MEDIUM on cross-browser clipboard + screenshot timing landmines.

### Key Findings

1. **Load-bearing discovery:** `/race/<run_id>` is a SPA-only route in `frontend/src/app/routes.tsx`. There is NO server-side HTML route in `web.py`. OG meta-tag injection therefore requires a NEW `@app.get("/race/{run_id}", response_class=HTMLResponse)` route that reads `frontend/dist/index.html`, injects og/twitter meta tags, and returns the modified HTML. Without this, social crawlers receive zero meta tags. CONTEXT.md does not call this out explicitly — it is the most important architecture insight in this research.
2. **Mock injection mechanism for D-63:** `monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_render)` — directly mirrors Phase 9 `test_replay_route.py:30` `monkeypatch.setattr("a2a_vs_mcp.web.RUNS_DIR", tmp_path)`. No new test infra needed.
3. **`data-og-ready` sentinel landmine (Risk 10):** without an explicit ready signal, Playwright may screenshot before `useRaceReplay` finishes folding events. Critical to surface in PLAN.md.
4. **Module placement:** `src/a2a_vs_mcp/race/og.py` (sibling of `heatmap.py` / `replay.py` / `runs.py`); `OG_LAYOUT_VERSION` in `race/config.py` next to `HEATMAP_BASELINE`.
5. **Versions verified live:** `playwright==1.59.0`, `html2canvas==1.4.1`. Chromium is pinned implicitly via Playwright bundled-browser.
6. **Mobile placeholder closure:** `<img src="/race/<run_id>/og.png">` with `onError` graceful degradation — closes Phase 8 placeholder in 8 lines, no Playwright on mobile device, leverages the same backend cache populated by desktop visitors.

### File Created
`/Users/shivanshchoudhary/Downloads/Projects/A2AvsMCP/.planning/phases/10-og-image-and-sharing/10-RESEARCH.md`

### Confidence Assessment
| Area | Level | Reason |
|------|-------|--------|
| Standard Stack | HIGH | Versions verified live via pip + npm registry queries 2026-04-30 |
| Architecture | HIGH | All file paths + integration points read from real source; SPA-vs-server routing definitively confirmed |
| Pitfalls | MEDIUM-HIGH | 11 enumerated risks; Risks 1, 4, 10 are the most consequential and have explicit mitigations |
| Test Strategy | HIGH | Mock-render pattern is a clone of an already-shipping test pattern (Phase 9) |
| Cross-browser | MEDIUM | Firefox ClipboardItem state is the only piece resting on feature-detection-and-fallback rather than direct testing |

### Open Questions
1. (RESOLVED) Exact field name of `n` (run count) in `HeatmapPayload` — Plan 10-03 Task 2 inspects at execution time; fallback `Σ recovery_rate.den`.
2. (RESOLVED) Inside-lock re-check (single-flight on cache miss) — Plan 10-02 Task 2 implements.

### Ready for Planning
Research complete. Five-plan decomposition (or three-plan slim version) provided with explicit wave assignments. Planner can now create PLAN.md files with no further investigation.
