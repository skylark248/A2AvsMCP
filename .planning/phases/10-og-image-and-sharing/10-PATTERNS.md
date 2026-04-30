# Phase 10: OG Image & Sharing — Pattern Map

**Mapped:** 2026-04-30
**Files analyzed:** 13 (3 NEW backend, 3 NEW frontend, 5 MODIFY, 2 dep manifests)
**Analogs found:** 13 / 13 (every file has a concrete in-repo analog)

## File Classification

| New/Modified File | Action | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|--------|------|-----------|----------------|---------------|
| `src/a2a_vs_mcp/race/og.py` | NEW | service / render module | request-response (async) + disk-cache + browser-singleton | `src/a2a_vs_mcp/race/heatmap.py` (cache + invalidate pattern), `src/a2a_vs_mcp/race/runs.py` (module-level constant + Path resolve) | role-match (no Playwright analog yet) |
| `src/a2a_vs_mcp/race/config.py` | MODIFY | config (frozen module-level constant) | static (import-time) | existing `HEATMAP_BASELINE` block in same file | exact |
| `src/a2a_vs_mcp/race/heatmap.py` | NEW (sibling: `HeatmapAnnotationStrip.tsx`) | — | — | — (frontend file; see below) | — |
| `src/a2a_vs_mcp/web.py` | MODIFY | route handler (FastAPI) | request → validate → existence-check → cache-hit/miss → render → response | `/api/race/runs/{run_id}/trace` (lines 869-886) for 400/404 + validate, `/api/race/heatmap` (lines 858-866) for terse-route | exact |
| `tests/race/test_og_routes.py` | NEW | test (pytest + TestClient) | mock-render via `monkeypatch.setattr` | `tests/race/test_replay_route.py` | exact |
| `tests/race/test_og_cache.py` | NEW | test (unit) | pure function — pathlib glob + write_bytes | `tests/race/test_replay_route.py` `_write_run` helper + `tmp_path` fixture | role-match |
| `frontend/src/features/race/RacePage.tsx` | MODIFY | page component (variant-gated render) | useSearchParams → conditional JSX | existing `useParams` + `isReplay` + `isMobile` flags in same file (D-48) | exact |
| `frontend/src/features/race/components/CopyHeadlineImageButton.tsx` | NEW | component (button + dynamic import) | onClick → dynamic import → DOM capture → ClipboardItem write or download fallback | sibling `CharacteristicFailureBanner.tsx` (MUI structure), no existing dynamic-import button → use Pattern 4 from RESEARCH.md verbatim | role-match |
| `frontend/src/features/race/components/CharacteristicFailureBanner.tsx` | MODIFY | component (presentation) | static props | self-analog: extend with optional `actionSlot` prop OR mount the button beside in `RacePage.tsx` (RESEARCH §Module Layout favors "mounted from RacePage") | exact (self) |
| `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` | MODIFY | component (data-wired wrapper) | `useRaceHeatmap()` → transform → render; conditional annotation strip in OG flag | self-analog: existing footer at lines 88-95 is the data-driven model · seed · task_ids stub; annotation strip mirrors with `run_id` prepended | exact (self) |
| `frontend/src/features/race/components/HeatmapAnnotationStrip.tsx` | NEW | component (presentation) | static props (run_id · model · seed · n · task_ids) | the existing footer Typography in `HardnessFailureHeatmap.tsx` lines 88-95 | exact |
| `pyproject.toml` | MODIFY | config / dep manifest | static | existing `[project.optional-dependencies]` `dev`/`remote-a2a` blocks (lines 22-31) | exact |
| `frontend/package.json` | MODIFY | config / dep manifest | static | existing `"dependencies"` block (line 16) | exact |
| `.gitignore` | MODIFY | config | static | existing project entries | trivial |
| `data/og/` | NEW dir | disk-cache directory | filesystem | `data/runs/` (runtime-created via `RUNS_DIR.mkdir(parents=True, exist_ok=True)`) | exact |

---

## Pattern Assignments

### `src/a2a_vs_mcp/race/og.py` (NEW — service / render module)

**Primary analog:** `src/a2a_vs_mcp/race/heatmap.py` (cache+invalidate idiom) plus `src/a2a_vs_mcp/race/runs.py` (module-level Path constant resolved from `__file__`).

**Module docstring + import block** (copy `heatmap.py` lines 1-16 shape — module-purpose + locked decisions + `from __future__ import annotations` + concrete imports from the package):

```python
# heatmap.py:1-25 — analog
"""Heatmap aggregator + in-process cache (D-52, D-54, D-55, D-57).

get_heatmap() walks RUNS_DIR/*.json, filters runs by run_meta event match
against HEATMAP_BASELINE ...

Cache invalidated on race_done by harness via invalidate_cache(). Counts are
NEVER persisted; rebuilt on demand. NO live LLM. NO network. Pure ndjson scan
+ bucket. Mirrors the pure-function aggregator pattern of metrics.py.
"""
from __future__ import annotations

from collections import Counter
from typing import Any

from .config import HEATMAP_BASELINE, HeatmapBaseline
from .replay import load_run
from .runs import RUNS_DIR
from .tasks import TASK_CONFIGS
```

**OG module imports** (copy this exact shape — locked-decisions docstring header, then imports):

```python
"""Playwright singleton + asyncio.Lock + render helpers (D-61, D-62, D-66).

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
```

**Module-level Path constant** (copy `runs.py` line 22 — `parents[3]` pattern resolves to repo root from `race/`):

```python
# runs.py:21-22 — analog
# Repo root: parents[0]=race/, [1]=a2a_vs_mcp/, [2]=src/, [3]=<root>
RUNS_DIR: Path = Path(__file__).resolve().parents[3] / "data" / "runs"
```

→ OG module mirrors:
```python
OG_DIR: Path = Path(__file__).resolve().parents[3] / "data" / "og"
```

**Module-level cache invalidation contract** (copy `heatmap.py:33-36`):

```python
# heatmap.py:33-36 — analog
def invalidate_cache() -> None:
    """Drop the entire heatmap cache (D-54). Called by harness post-race_done."""
    _CACHE.clear()
```

→ OG module mirrors with `cleanup_stale(run_id, surface)` — pathlib glob + `unlink(missing_ok=True)` (RESEARCH §Pattern 3).

**Lifespan + render-with-lock signatures** — RESEARCH.md §Pattern 1 + 2 are the verbatim spec. The signatures the planner pins:

```python
@asynccontextmanager
async def og_lifespan(app: FastAPI) -> AsyncIterator[None]: ...

OG_RENDER_LOCK: asyncio.Lock  # initialized at module load; safe because asyncio.Lock since 3.10 binds lazily

OG_VIEWPORT = {"width": 1200, "height": 630}
HEATMAP_VIEWPORT = {"width": 1200, "height": 900}
RENDER_TIMEOUT_MS: int = 10_000

async def render_og_png(run_id: str, browser: Browser, base_url: str = "http://127.0.0.1:8008") -> bytes: ...
async def render_heatmap_png(run_id: str, browser: Browser, base_url: str = "http://127.0.0.1:8008") -> bytes: ...

def og_cache_path(run_id: str, surface: Literal["og", "heatmap"]) -> Path: ...
def cleanup_stale(run_id: str, surface: Literal["og", "heatmap"]) -> None: ...

__all__ = [
    "og_lifespan", "OG_RENDER_LOCK", "OG_DIR",
    "render_og_png", "render_heatmap_png",
    "og_cache_path", "cleanup_stale",
    "OG_VIEWPORT", "HEATMAP_VIEWPORT",
]
```

---

### `src/a2a_vs_mcp/race/config.py` (MODIFY — append `OG_LAYOUT_VERSION`)

**Analog:** the file itself, lines 19-49 — `HEATMAP_BASELINE` constant block. D-66 explicitly says "matches the existing `HEATMAP_BASELINE` constant pattern from Phase 9 D-56."

**Existing pattern** (config.py:19-49):

```python
@dataclass(frozen=True)
class HeatmapBaseline:
    """Frozen pinned-baseline tuple (D-56)."""
    model: str
    seed: int
    task_ids: tuple[str, ...]
    def to_dict(self) -> dict: ...

HEATMAP_BASELINE: HeatmapBaseline = HeatmapBaseline(
    model=MODEL,
    seed=SEED_DISCLOSURE,
    task_ids=("summarize_repo", "negotiate_meeting", "book_travel"),
)

__all__ = ["HEATMAP_BASELINE", "HeatmapBaseline"]
```

**OG-LAYOUT-VERSION extension** (append below `HEATMAP_BASELINE`, ahead of `__all__`):

```python
# D-66: manual integer; bump when og.py anchor-region layout changes.
# Cache filename pattern: data/og/<run_id>-<surface>-v<OG_LAYOUT_VERSION>.png.
OG_LAYOUT_VERSION: int = 1
```

Then update `__all__`:
```python
__all__ = ["HEATMAP_BASELINE", "HeatmapBaseline", "OG_LAYOUT_VERSION"]
```

**Why a bare `int` (not a frozen dataclass):** D-66 says "manual `OG_LAYOUT_VERSION` Python integer constant." `HEATMAP_BASELINE` is a tuple-of-3 (model, seed, task_ids) so it earns a frozen dataclass. `OG_LAYOUT_VERSION` is a single integer; the dataclass overhead is unjustified.

---

### `src/a2a_vs_mcp/web.py` (MODIFY — register lifespan + add 3 routes)

**Analog 1 (route shape):** `/api/race/runs/{run_id}/trace` (web.py:869-886) — `_validate_run_id` → 400, existence check → 404, body construction.

```python
# web.py:869-886 — analog
@app.get("/api/race/runs/{run_id}/trace")
def api_race_run_trace(run_id: str) -> dict:
    """Replay endpoint — load ndjson trace from disk for /race/<run_id> (HEAT-03).

    Path-traversal guard via _validate_run_id BEFORE any path resolution.
    No live LLM. No event mutation. schema_version is the disk schema (Phase 6 D-03).
    Events shipped verbatim (D-59 — backend `event_type` key NOT renamed).
    Frontend contract: matches RaceReplayPayload at client.ts:136-140.
    """
    try:
        _validate_run_id(run_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        events = load_run(run_id, RUNS_DIR)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="run not found")
    return {"run_id": run_id, "events": events, "schema_version": "1.0"}
```

**OG-PNG route mirror (PNG cache + render-on-miss):**

```python
@app.get("/race/{run_id}/og.png")
async def race_og_png(run_id: str, request: Request) -> Response:
    try:
        _validate_run_id(run_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not (RUNS_DIR / f"{run_id}.json").exists():
        raise HTTPException(status_code=404, detail="run not found")  # OG-04 — BEFORE Playwright spawn
    cleanup_stale(run_id, surface="og")  # D-66 lazy purge
    cache = og_cache_path(run_id, surface="og")
    if cache.exists():
        return FileResponse(cache, media_type="image/png")
    try:
        async with OG_RENDER_LOCK:
            data = await render_og_png(run_id, request.app.state.og_browser)
    except Exception as exc:
        raise HTTPException(status_code=503, detail="og render failed; please retry") from exc
    OG_DIR.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(data)
    return Response(data, media_type="image/png")
```

**Heatmap-PNG route:** same shape, `surface="heatmap"`, `render_heatmap_png`.

**Analog 2 (HTML SPA route shape):** `web.py:438-446` — existing SPA `@app.get("/", response_class=HTMLResponse)` patterns:

```python
# web.py:429-445 — analog
def render_react_app() -> Response:
    if FRONTEND_INDEX.exists():
        return FileResponse(FRONTEND_INDEX)
    return HTMLResponse(...)


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> Response:
    return render_react_app()


@app.get("/learn", response_class=HTMLResponse)
def learn_index(request: Request) -> Response:
    return render_react_app()
```

**HTML route w/ meta-tag injection** — RESEARCH §"OG Meta-Tag Injection Path" lines 553-572 is the verbatim spec; planner mounts adjacent to other SPA routes (~line 458):

```python
@app.get("/race/{run_id}", response_class=HTMLResponse)
def race_run_html(run_id: str, request: Request) -> HTMLResponse:
    try:
        _validate_run_id(run_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    base_url = str(request.base_url).rstrip("/")
    if (RUNS_DIR / f"{run_id}.json").exists():
        html_out = _inject_og_meta(_read_index_html(), run_id, base_url)
    else:
        html_out = _read_index_html()  # crawler-safe: no og:image at all
    return HTMLResponse(html_out)


@app.get("/race", response_class=HTMLResponse)
def race_html() -> Response:
    return render_react_app()
```

**Imports to add** (top of web.py, near lines 16 and 44):

```python
# already present — line 17:
from fastapi.responses import FileResponse, HTMLResponse, Response

# ADD after line 46:
from .race.og import (
    OG_RENDER_LOCK, OG_DIR, og_cache_path, cleanup_stale,
    render_og_png, render_heatmap_png, og_lifespan,
)
from .race.config import OG_LAYOUT_VERSION  # if needed for logging; otherwise remove
import html as _html
```

**Lifespan registration:** change line 61
```python
# BEFORE:  app = FastAPI(title="A2A vs MCP Demo UI")
# AFTER:
app = FastAPI(title="A2A vs MCP Demo UI", lifespan=og_lifespan)
```

---

### `tests/race/test_og_routes.py` (NEW — pytest + TestClient + mock render)

**Analog:** `tests/race/test_replay_route.py` (full file) — exact pattern for D-63 mock-render scenarios.

**Test-fixture pattern** (test_replay_route.py:22-37):

```python
# test_replay_route.py:22-37 — analog
@pytest.fixture
def runs_dir(tmp_path, monkeypatch):
    """Point web.py's RUNS_DIR at an isolated tmp directory."""
    monkeypatch.setattr("a2a_vs_mcp.web.RUNS_DIR", tmp_path)
    return tmp_path


def _write_run(runs_dir: Path, run_id: str, events: list[dict]) -> None:
    """Write an ndjson run file (one event per line)."""
    path = runs_dir / f"{run_id}.json"
    path.write_text("\n".join(json.dumps(e) for e in events) + "\n")
```

**OG mirror:** add a sibling fixture `og_dir` that monkeypatches `a2a_vs_mcp.web.OG_DIR` (and `a2a_vs_mcp.race.og.OG_DIR`) to `tmp_path / "og"`, plus the mock-render fixture for D-63:

```python
@pytest.fixture
def mock_render(monkeypatch):
    """D-63: mock render_og_png + render_heatmap_png; no real Chromium in CI."""
    calls = {"og": 0, "heatmap": 0}

    async def fake_render_og(run_id, browser, base_url="..."):
        calls["og"] += 1
        return b"\x89PNG\r\n\x1a\n" + b"og-fake-bytes"

    async def fake_render_heatmap(run_id, browser, base_url="..."):
        calls["heatmap"] += 1
        return b"\x89PNG\r\n\x1a\n" + b"heatmap-fake-bytes"

    monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_render_og)
    monkeypatch.setattr("a2a_vs_mcp.web.render_heatmap_png", fake_render_heatmap)
    # also stub app.state.og_browser since lifespan won't fire under TestClient default ctx
    return calls
```

**Test scenarios** (D-63 matrix; mirror existing test names from test_replay_route.py:44-156):

```python
# test_replay_route.py — test names map to OG counterparts
test_happy_path_returns_payload          → test_cache_miss_renders_once_and_writes
test_invalid_run_id_returns_400          → test_invalid_run_id_returns_400  # identical
test_missing_run_returns_404             → test_unknown_run_returns_404_before_render
test_response_shape_matches_frontend_typed_stub  → (drop — no frontend type for PNG)
test_events_shipped_verbatim_no_normalization    → test_render_exception_returns_503
                                          + test_cache_hit_skips_render
                                          + test_layout_version_bump_invalidates
```

**One-shot critical test (cache hit):**

```python
def test_cache_hit_skips_render(runs_dir, og_dir, mock_render):
    _write_run(runs_dir, "r1", [{"event_type": "run_meta", "trace_schema_version": "1.0", ...}])
    cache_file = og_dir / f"r1-og-v{OG_LAYOUT_VERSION}.png"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_bytes(b"\x89PNG\r\nprerendered")

    r = TestClient(app).get("/race/r1/og.png")
    assert r.status_code == 200
    assert r.content == b"\x89PNG\r\nprerendered"
    assert mock_render["og"] == 0  # render NEVER called
```

**Why TestClient bypasses lifespan:** `with TestClient(app) as client:` triggers lifespan; bare `TestClient(app).get(...)` does NOT. For OG render-mock tests, prefer `with TestClient(app) as client:` AND set `app.state.og_browser = MagicMock()` inside the context, OR keep tests bare and stub render-fn first so `request.app.state.og_browser` is never read in the mock path.

---

### `tests/race/test_og_cache.py` (NEW — unit tests for `og_cache_path` + `cleanup_stale`)

**Analog:** unit-test sections of `tests/race/test_replay_route.py` (`_write_run` helper) + standard `tmp_path` pytest fixture.

**Pattern:**

```python
def test_og_cache_path_includes_layout_version():
    p = og_cache_path("r1", "og")
    assert p.name == f"r1-og-v{OG_LAYOUT_VERSION}.png"


def test_cleanup_stale_purges_old_versions(monkeypatch, tmp_path):
    monkeypatch.setattr("a2a_vs_mcp.race.og.OG_DIR", tmp_path)
    (tmp_path / "r1-og-v0.png").write_bytes(b"old")
    (tmp_path / "r1-og-v1.png").write_bytes(b"current")
    (tmp_path / "r2-og-v0.png").write_bytes(b"different-run")  # untouched
    cleanup_stale("r1", "og")  # OG_LAYOUT_VERSION=1
    assert not (tmp_path / "r1-og-v0.png").exists()
    assert (tmp_path / "r1-og-v1.png").exists()
    assert (tmp_path / "r2-og-v0.png").exists()
```

---

### `frontend/src/features/race/RacePage.tsx` (MODIFY — `?og=1` chrome-strip + `data-og-anchor` + close mobile placeholder)

**Analog:** the file itself (Phase 8 D-48 same-component-different-flag pattern). Lines 49-57 are the variant-flag intake; lines 79-85 are the mobile placeholder (Phase 10 wiring target); lines 114-178 are the JSX tree where chrome-stripping conditionals land.

**Existing variant-gate pattern** (RacePage.tsx:48-65):

```tsx
// RacePage.tsx:48-65 — analog
export function RacePage({ __testState }: RacePageProps = {}) {
  const { run_id: routeRunId } = useParams<{ run_id?: string }>();
  const run_id = __testState ? (__testState.run_id ?? routeRunId) : routeRunId;
  const isReplay = Boolean(run_id);

  // UIRACE-05 mobile fallback (viewport check).
  // Full ?mode=summary redirect ships in Phase 10. Plan 06 only emits the placeholder branch.
  const isMobile = useMediaQuery("(max-width:479px)");

  const liveState = useRaceStream(!isMobile && !isReplay);
  const replay = useRaceReplay(isReplay && !isMobile ? run_id : undefined);
```

**Phase 10 additions** (drop-in adjacent to existing flags):

```tsx
import { useParams, useSearchParams } from "react-router-dom";  // add useSearchParams to existing import

// inside RacePage:
const [searchParams] = useSearchParams();
const isOg = searchParams.get("og") === "1";
const ogSurface = searchParams.get("surface");  // "heatmap" | null
```

**Existing mobile placeholder** (RacePage.tsx:79-85, the explicit Phase 10 hand-off):

```tsx
// RacePage.tsx:79-85 — Phase 10 wiring target
if (isMobile && !__testState) {
  return (
    <Box data-testid="race-mobile-summary-placeholder" sx={{ p: 4, textAlign: "center" }}>
      <Typography variant="body1">Loading summary…</Typography>
    </Box>
  );
}
```

**Phase 10 replacement** (RESEARCH lines 762-787 — `<img src="/race/<run_id>/og.png">` consumption):

```tsx
if (isMobile && !__testState) {
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
          onError={(e) => { (e.currentTarget as HTMLImageElement).style.display = "none"; }}
        />
      ) : (
        <Typography variant="body1">Open on desktop for the live race UI.</Typography>
      )}
    </Box>
  );
}
```

**Existing JSX tree shape** (RacePage.tsx:114-178) — chrome-stripping conditionals retrofit existing sections (RaceStatusStrip, ReplayScrubber, MethodologySection, HardnessFailureHeatmap). Wrap title-block + lane-row + banner in `<Box data-og-anchor>`; mount `<CopyHeadlineImageButton>` inside the banner-visible block (visible only when `!isOg`). RESEARCH §"?og=1 RacePage Variant" lines 591-657 has the full JSX shape.

**Critical:** the OG anchor wrapping element is the SAME `<Container component="main" sx={{ maxWidth: 1200 }}>` region (line 135) restricted to title + lane row + banner — `data-og-anchor` goes on a NEW `<Box>` immediately inside that Container, NOT on the Container itself (so the heatmap stays out of the OG crop).

---

### `frontend/src/features/race/components/CopyHeadlineImageButton.tsx` (NEW — dynamic-import button)

**Analog:** No existing dynamic-import button in the repo. Use RESEARCH §"html2canvas Lazy-Load + Clipboard Pattern" (lines 663-740) verbatim. MUI `<Button>` shape mirrors `CharacteristicFailureBanner.tsx` MUI imports (line 1).

**Sibling-style imports** (copy `CharacteristicFailureBanner.tsx:1` shape):

```tsx
// CharacteristicFailureBanner.tsx:1 — analog
import { Box, Typography } from "@mui/material";
```

**OG button imports:**

```tsx
import { Button } from "@mui/material";
import ContentCopyIcon from "@mui/icons-material/ContentCopy";
import { useState } from "react";
```

**Component signature + onClick handler** — verbatim from RESEARCH lines 671-739; no novelty in the planner. Key invariant: `await import("html2canvas")` MUST be inside the user-gesture onClick (not at module top).

**Test seam** (test file `CopyHeadlineImageButton.test.tsx`):
- Vitest `vi.mock('html2canvas', ...)` for the dynamic import
- Stub `navigator.clipboard.write` and `ClipboardItem` on globalThis
- Two assertions: clipboard primary path called when `ClipboardItem` defined; download fallback `<a download>` triggered when `clipboard.write` rejects.

---

### `frontend/src/features/race/components/CharacteristicFailureBanner.tsx` (MODIFY — beside-banner button mount)

**Analog (self):** the file itself, lines 29-57. RESEARCH §Module Layout line 411 picks "Optional `actionSlot` prop; mount `<CopyHeadlineImageButton>` beside header (mounted from RacePage)."

**Existing component signature** (lines 3-8):

```tsx
// CharacteristicFailureBanner.tsx:3-8 — analog
interface CharacteristicFailureBannerProps {
  header: string;
  clause: string;
}
```

**Phase 10 extension** — add optional slot:

```tsx
interface CharacteristicFailureBannerProps {
  header: string;
  clause: string;
  /** Phase 10: optional adjacent action (e.g. <CopyHeadlineImageButton>). Ignored in OG mode. */
  actionSlot?: React.ReactNode;
}
```

**JSX modification** — extend the existing `<Box role="banner">` to flex-row when actionSlot present, OR (preferred per RESEARCH) leave this component untouched and mount `<CopyHeadlineImageButton>` as a SIBLING in `RacePage.tsx` directly below the `<CharacteristicFailureBanner>` element. RESEARCH §Module Layout favors RacePage-side mounting because it keeps the banner component a pure presentation node and respects T-08-08 (no innerHTML, no new XSS surface).

**Recommendation for planner:** mount the button in `RacePage.tsx` (below the banner inside the same `BANNER_VISIBLE_STATES.includes(pageState)` conditional block, gated by `!isOg`). Don't add `actionSlot` prop unless plan-checker explicitly requires it.

---

### `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` (MODIFY — annotation strip when OG flag set)

**Analog (self):** the file itself, lines 53-98. The existing footer at lines 88-95 is the data-driven baseline-strip stub:

```tsx
// HardnessFailureHeatmap.tsx:88-95 — analog footer
{data ? (
  <Typography
    variant="caption"
    sx={{ color: "text.secondary", display: "block", mt: 1 }}
  >
    {data.baseline.model} · {data.baseline.seed} · {data.baseline.task_ids.join(", ")}
  </Typography>
) : null}
```

**Phase 10 extension** — annotation strip is a SIBLING component (`HeatmapAnnotationStrip.tsx`) rendered at the TOP of the heatmap card when `?og=1&surface=heatmap`, distinct from the live-UI footer. RESEARCH §"Heatmap.png annotation strip" picks this shape to preserve D-47 empty-state-never-unmount.

**Component signature change** — add optional flag:

```tsx
interface HardnessFailureHeatmapProps {
  /** Phase 10 OG: render the annotation strip + attach data-heatmap-anchor. */
  ogAnnotation?: boolean;
  /** Phase 10 OG: forwarded to the annotation strip for the run_id token. */
  runId?: string | null;
}

export function HardnessFailureHeatmap({ ogAnnotation = false, runId = null }: HardnessFailureHeatmapProps = {}) {
  const { data } = useRaceHeatmap();
  const cells = data ? toHeatmapCells(data) : {};
  // ... existing body ...
}
```

**Annotation strip mount** (additive — does NOT remove existing live-UI footer):

```tsx
{ogAnnotation && data ? (
  <HeatmapAnnotationStrip
    runId={runId}
    model={data.baseline.model}
    seed={data.baseline.seed}
    n={data.cells.reduce((acc, c) => acc + c.recovery_rate.den, 0)}  // total run count across cells
    taskIds={data.baseline.task_ids}
  />
) : null}
```

**D-47 empty-state preservation:** the annotation strip is rendered ONLY when `data` is non-null AND `ogAnnotation` is true. The existing `<HeatmapScaffold cells={cells} />` line 67 keeps its `cells={}` empty-pass-through behavior unchanged.

---

### `frontend/src/features/race/components/HeatmapAnnotationStrip.tsx` (NEW — presentation-only strip)

**Analog:** the existing footer Typography in `HardnessFailureHeatmap.tsx:88-95`. Same MUI `<Typography variant="caption">` shape, expanded with `runId` and `n` tokens.

**Component:**

```tsx
import { Box, Typography } from "@mui/material";

interface HeatmapAnnotationStripProps {
  runId: string | null;
  model: string;
  seed: number;
  n: number;
  taskIds: readonly string[];
}

export function HeatmapAnnotationStrip({ runId, model, seed, n, taskIds }: HeatmapAnnotationStripProps) {
  return (
    <Box data-testid="heatmap-annotation-strip" sx={{ mb: 2, p: 2, borderLeft: "4px solid", borderColor: "primary.main", bgcolor: "background.paper" }}>
      <Typography variant="caption" sx={{ color: "text.secondary", display: "block" }}>
        {runId ?? "(no run_id)"} · {model} · seed {seed} · n={n} · {taskIds.join(", ")}
      </Typography>
    </Box>
  );
}
```

T-09-15 / T-08-08 mitigation inherited automatically: all values rendered as React text children (auto-escaped); no `dangerouslySetInnerHTML`, no innerHTML.

---

### `pyproject.toml` (MODIFY — add `playwright` optional dep)

**Analog:** existing `[project.optional-dependencies]` block at lines 22-31:

```toml
# pyproject.toml:22-31 — analog
[project.optional-dependencies]
dev = [
  "ruff>=0.8.0",
  "pytest>=8.0",
  "pytest-asyncio>=0.24",
  "httpx>=0.28"
]
remote-a2a = [
  "a2a-sdk[http-server]==0.3.26"
]
```

**Phase 10 addition** (RESEARCH §Standard Stack lines 96-99):

```toml
og = [
  "playwright>=1.59,<2"
]
```

→ Install via `pip install -e ".[og]"` and `playwright install chromium` in dev/CI bootstrap (RESEARCH §Installation lines 94-103).

---

### `frontend/package.json` (MODIFY — add `html2canvas`)

**Analog:** existing `"dependencies"` block (line 16+, with @mui/material, react, react-dom, react-router-dom, react-syntax-highlighter).

**Addition:**

```json
"html2canvas": "^1.4.1"
```

Inserted alphabetically into the `"dependencies"` object. No transitive concerns; `html2canvas@1.4.1` has been stable since 2022-01-22 [VERIFIED in RESEARCH].

---

### `.gitignore` (MODIFY — add `data/og/*.png`)

**Analog:** existing project entries (data/runs/ already gitignored typically). Add:

```
data/og/*.png
```

---

## Shared Patterns

### Path-traversal validation
**Source:** `src/a2a_vs_mcp/race/replay.py:19-28` (`_validate_run_id` regex `^[A-Za-z0-9_-]{1,64}$`)
**Apply to:** all 3 new web.py routes (HTML + og.png + heatmap.png) — call BEFORE any Path resolution and BEFORE any Playwright spawn (OG-04).
```python
try:
    _validate_run_id(run_id)
except ValueError as e:
    raise HTTPException(status_code=400, detail=str(e))
```

### Existence check before render
**Source:** `(RUNS_DIR / f"{run_id}.json").exists()` — implicit in `load_run` at web.py:884; explicit form needed for OG to short-circuit BEFORE Playwright.
**Apply to:** og.png + heatmap.png routes (OG-04 contract: 404 BEFORE Playwright spawn).
```python
if not (RUNS_DIR / f"{run_id}.json").exists():
    raise HTTPException(status_code=404, detail="run not found")
```

### Module-level frozen constants
**Source:** `config.py:42-46` (`HEATMAP_BASELINE`) + `runs.py:22-25` (`RUNS_DIR`, `BATCH_SIZE`, `FORCED_FLUSH_EVENTS`).
**Apply to:** `OG_LAYOUT_VERSION` (config.py), `OG_DIR`, `OG_VIEWPORT`, `HEATMAP_VIEWPORT`, `RENDER_TIMEOUT_MS` (og.py).

### Disk-backed cache + lazy invalidation
**Source:** `heatmap.py:30-50` in-memory cache + `invalidate_cache()` (Phase 9 D-54).
**Apply to:** `og.py` `cleanup_stale()` — pathlib glob over stale `<id>-<surface>-v*.png` siblings.
```python
def cleanup_stale(run_id: str, surface: Literal["og", "heatmap"]) -> None:
    OG_DIR.mkdir(parents=True, exist_ok=True)
    keep = og_cache_path(run_id, surface).name
    for p in OG_DIR.glob(f"{run_id}-{surface}-v*.png"):
        if p.name != keep:
            p.unlink(missing_ok=True)
```

### Test fixture: monkeypatch `a2a_vs_mcp.web.RUNS_DIR` to `tmp_path`
**Source:** `tests/race/test_replay_route.py:22-31`.
**Apply to:** `test_og_routes.py` — same fixture for `RUNS_DIR`, plus a sibling fixture for `OG_DIR` (`monkeypatch.setattr("a2a_vs_mcp.web.OG_DIR", tmp_path / "og")`) and a `mock_render` fixture (D-63) stubbing `a2a_vs_mcp.web.render_og_png` + `render_heatmap_png`.

### MUI component imports + sx styling
**Source:** `CharacteristicFailureBanner.tsx:1` (`import { Box, Typography } from "@mui/material"`), `HardnessFailureHeatmap.tsx:18` (`import { Box, Chip, Stack, Typography } from "@mui/material"`).
**Apply to:** `CopyHeadlineImageButton.tsx`, `HeatmapAnnotationStrip.tsx` — same import shape; never reach for `styled-components` or other styling libs (project standard is MUI sx).

### React-router `useSearchParams` for variant flags
**Source:** `RacePage.tsx:17` (existing `useParams` from react-router-dom, paired with `useReducer` and `useEffect`).
**Apply to:** `?og=1` and `?surface=heatmap` reads — add `useSearchParams` to the existing import line; treat it as a peer of `isReplay` and `isMobile`.

### Test-text ID via `data-testid`
**Source:** `RacePage.tsx:81` (`data-testid="race-mobile-summary-placeholder"`), `CharacteristicFailureBanner.tsx:33` (`data-testid="characteristic-failure-banner"`).
**Apply to:** `data-og-anchor` (NOT a `data-testid` — used by Playwright + html2canvas selector); `data-heatmap-anchor` (same); `data-testid="copy-headline-image-button"`, `data-testid="heatmap-annotation-strip"`, `data-testid="race-mobile-summary"`.

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| (none) | — | — | Every Phase 10 file has a concrete in-repo analog. The novelty is *infrastructure* (Playwright lifespan + html2canvas dynamic import), not *business logic*. RESEARCH.md captures that infrastructure verbatim in §Pattern 1-4 — planner copies those code blocks rather than inventing. |

The closest "no real analog" is the FastAPI **lifespan registration** pattern itself — `web.py:61` currently constructs `app = FastAPI(...)` without a `lifespan=` argument. This is a one-line edit, but it's the first lifespan in the project. Planner should explicitly call this out as a load-bearing change in the Plan that touches `web.py` so plan-checker doesn't miss it.

---

## Metadata

**Analog search scope:**
- `src/a2a_vs_mcp/race/` (config, heatmap, replay, runs, ws, harness, types) — backend modules
- `src/a2a_vs_mcp/web.py` (full file) — route mount points
- `tests/race/` (test_replay_route, test_run_meta_event, test_heatmap_aggregator) — pytest fixtures
- `frontend/src/features/race/RacePage.tsx` — variant-gate pattern
- `frontend/src/features/race/components/` — MUI conventions
- `pyproject.toml`, `frontend/package.json` — dep manifests

**Files scanned (read in full or targeted):** 9 source files + 2 test files + 2 dep manifests + 2 phase planning files.

**Pattern extraction date:** 2026-04-30

## PATTERN MAPPING COMPLETE
