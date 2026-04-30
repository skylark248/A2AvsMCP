# Phase 10: OG Image & Sharing - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-30
**Phase:** 10-og-image-and-sharing
**Areas discussed:** Playwright lifecycle, Client canvas fallback, Cache key strategy (live conflict)

---

## Playwright lifecycle

### Q1 — Browser management

| Option | Description | Selected |
|--------|-------------|----------|
| Singleton + asyncio.Lock | One persistent Browser at startup, shared via lock; ~500ms-1s cache misses; clean lifespan shutdown | ✓ |
| Spawn-per-request | Each cache miss launches its own Chromium; ~2-3s; race-safe; trivial mocking | |
| Browser pool (N=2-4) | Pre-warmed pool; best burst concurrency; pool sizing/health complexity | |
| Subprocess Playwright CLI | Shell out to `playwright screenshot` per request; slowest; easiest CI mock | |

**User's choice:** Singleton + asyncio.Lock (Recommended)
**Notes:** Captured as D-61. Bounded resource footprint; FastAPI lifespan-native; lock prevents thrash on concurrent misses.

---

### Q2 — Failure mode

| Option | Description | Selected |
|--------|-------------|----------|
| 503 + client-canvas fallback | HTTP 503 on render failure; client canvas button is recovery; crawlers re-fetch later | ✓ |
| Static placeholder PNG | Generic disk PNG on failure; crawlers always get something; risk of silent wrong-image | |
| Lazy retry with one fallback render | Spawn fresh browser once on crash, retry; doubles worst-case latency | |
| 503 + log only | Plain 503; relies on canvas fallback prominence | |

**User's choice:** 503 + client-canvas fallback (Recommended)
**Notes:** Captured as D-62. Honest failure signal; canvas button covers user side; demo never serves wrong-looking embed.

---

### Q3 — CI test strategy

| Option | Description | Selected |
|--------|-------------|----------|
| Mock the render function | `render_og_png` mocked; assert routing/cache/invalidation/503; no Chromium in CI | ✓ |
| Real Playwright in CI | Chromium installed in CI image; most realistic; slowest; fragile | |
| Golden PNG fixture comparison | Pre-generated PNGs in repo; catches drift; high maintenance | |
| Skip PNG content tests, only test routing | Routing-only mocks; trust Playwright for output correctness | |

**User's choice:** Mock the render function (Recommended)
**Notes:** Captured as D-63. CI stays small/fast; routing+caching+invalidation are the load-bearing logic; rendering correctness verified manually in dev.

---

## Client canvas fallback

### Q1 — Canvas implementation

| Option | Description | Selected |
|--------|-------------|----------|
| html2canvas library | ~45KB gz; lazy-loaded; battle-tested cross-browser | ✓ |
| foreignObject SVG hand-roll | Zero deps; fragile across Safari + cross-origin fonts | |
| Canvas API redraw | Hand-paint anchor region from race state; pixel-perfect; high cost | |
| Drop client fallback | Server-only OG; saves time but breaks OG-03 | |

**User's choice:** html2canvas library (Recommended)
**Notes:** Captured as D-64. Lazy-loaded via dynamic import; same `data-og-anchor` element that Playwright targets.

---

### Q2 — Output mechanism

| Option | Description | Selected |
|--------|-------------|----------|
| Clipboard via ClipboardItem | `navigator.clipboard.write([new ClipboardItem({'image/png': blob})])`; modern browser support; FF gated | ✓ |
| Download as PNG file | `race-<run_id>.png` download trigger; universal support; attach-then-paste UX | |
| Open in new tab as data URL | Right-click-save UX; works everywhere; clunky | |
| Both — clipboard primary, download fallback | Try clipboard first; auto-download on failure | |

**User's choice:** Clipboard via ClipboardItem (Recommended)
**Notes:** Captured as D-65. Implementation includes a download fallback for browsers (Firefox) that gate `ClipboardItem` for `image/png`. Effective behavior matches the "Both" hybrid.

---

## Cache key strategy (upstream conflict resolution)

### Q1 — Cache key

| Option | Description | Selected |
|--------|-------------|----------|
| Manual OG_LAYOUT_VERSION constant | Python int constant; developer bumps on layout change; matches REQUIREMENTS.md OG-01 verbatim | ✓ |
| Scoped-CSS-SHA auto-detect | SHA over `.race-anchor *` CSS rules; auto-invalidates on layout drift; PostCSS plugin needed | |
| Hybrid — manual + auto warning | Manual constant primary; startup logs warning if SHA changed since last bump | |
| Defer decision to researcher | Flag as Claude's discretion; researcher picks based on codebase state | |

**User's choice:** Manual OG_LAYOUT_VERSION constant (Recommended)
**Notes:** Captured as D-66. Resolves the master-design vs eng-review-iter-2 Decision #3 conflict. Simple, predictable, zero-toolchain; matches Phase 9 D-56 `HEATMAP_BASELINE` constant pattern. SHA-CSS refinement parked in Deferred Ideas.

---

## Claude's Discretion

Listed in CONTEXT.md `<decisions>` → "Claude's Discretion" subsection. Highlights:
- `?og=1` rendering surface — RacePage conditional render vs separate OgRacePage component (researcher pick).
- OG/render module location — `race/og.py` vs `serve_ui.py` inline vs sibling module.
- Cleanup task trigger — startup hook vs lazy delete-on-mismatch.
- Mobile `?mode=summary` consumption shape — fetch URL vs server-inlined data URL vs canvas snapshot.
- `data-og-anchor` element wiring — exact DOM marker for the screenshot region.
- Heatmap.png annotation strip rendering — same component conditional vs sibling component.
- Playwright dependency strategy — pyproject extras vs separate dev install script; pin Chromium version.

## Deferred Ideas

Listed in CONTEXT.md `<deferred>`. Highlights:
- HMAC-signed PNG URLs (TODO 9) — explicitly NOT folded; v2.1+ promote condition is external traffic / leak risk.
- SHA-over-scoped-anchor-CSS auto-invalidation — superseded by D-66; promote if manual bumps go missed.
- Playwright browser pool (N=2-4) — promote on lock contention.
- Multi-frame / animated OG variants — v2.1+.
- Per-`OG_LAYOUT_VERSION` automated visual-regression test — promote on silent layout drift incidents.
- OG endpoint observability (cache hit/miss, render latency) — production push only.
