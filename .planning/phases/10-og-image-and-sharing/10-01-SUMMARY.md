---
phase: 10-og-image-and-sharing
plan: 01
subsystem: og-image
tags: [phase-10, og-image, playwright, fastapi-lifespan, asyncio-lock, cache, optional-dependency]

# Dependency graph
requires:
  - phase: 09-heatmap-replay-k3-calibration
    provides: HEATMAP_BASELINE module-constant pattern (D-56) — OG_LAYOUT_VERSION mirrors shape
  - phase: 06-tracerecorder-schema-gate-race-foundation
    provides: RUNS_DIR Path(__file__).resolve().parents[3] anchor — OG_DIR mirrors shape
provides:
  - race/og.py module with og_lifespan, OG_RENDER_LOCK, OG_DIR, og_cache_path, cleanup_stale, render_og_png, render_heatmap_png
  - OG_LAYOUT_VERSION=1 integer constant in race/config.py (D-66, manual bump policy)
  - playwright>=1.59,<2 optional-dependency under [project.optional-dependencies] og
  - data/og/*.png .gitignore line (defensive — parent /data/* already ignored)
  - 6 unit tests in tests/race/test_og_cache.py covering cache-path arithmetic + cleanup_stale invariants
affects: [10-02-routes-and-html, 10-03-frontend-og-mode, 10-04-canvas-fallback, 10-05-cleanup-and-mobile]

# Tech tracking
tech-stack:
  added: [playwright (optional-dep, runtime only)]
  patterns:
    - "FastAPI lifespan asynccontextmanager owning Playwright Browser singleton (D-61)"
    - "Module-scope asyncio.Lock for cross-request render serialization (Risk-1 documented in docstring)"
    - "Lazy import of optional heavy dep inside lifespan body — module loadable in Chromium-free CI (D-63)"
    - "Disk-backed cache with deterministic filename and lazy version-mismatch purge (D-66, OG-04)"

key-files:
  created:
    - src/a2a_vs_mcp/race/og.py
    - tests/race/test_og_cache.py
  modified:
    - src/a2a_vs_mcp/race/config.py
    - pyproject.toml
    - .gitignore

key-decisions:
  - "OG_LAYOUT_VERSION=1 baseline; manual bump policy (D-66, no env / runtime config)"
  - "OG_RENDER_LOCK at module scope; Risk-1 lazy-bind to event loop documented but not mitigated in Wave 1"
  - "Lazy delete-on-mismatch chosen over startup hook for cleanup_stale (planner discretion in 10-CONTEXT)"
  - "Render helpers wait for [data-og-anchor][data-og-ready=\"true\"] (Risk-10) and use wait_until=domcontentloaded (Risk-4)"
  - "Lazy playwright import keeps og module loadable for Chromium-free CI (D-63 prerequisite)"

patterns-established:
  - "Optional-dep import gating pattern: TYPE_CHECKING guard for type-only refs + lazy import inside async functions"
  - "Per-render BrowserContext + Page lifecycle: open in try, close in finally; caller holds the global lock"
  - "Cache key composition: <run_id>-<surface>-v<INT_VERSION>.png with single-source-of-truth integer"

requirements-completed: [OG-01, OG-02, OG-04]

# Metrics
duration: ~25min
completed: 2026-04-30
---

# Phase 10 Plan 01: OG Module Foundation Summary

**race/og.py ships Playwright Browser-singleton lifespan, asyncio.Lock render serialization, deterministic disk-cache helpers (data/og/<id>-<surface>-v<OG_LAYOUT_VERSION>.png), and Chromium-free unit tests — Wave 2 can now mount routes without touching Playwright internals.**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-04-30T12:51:00Z
- **Completed:** 2026-04-30T13:16:44Z
- **Tasks:** 3
- **Files modified:** 5 (2 created, 3 modified)

## Accomplishments
- New `src/a2a_vs_mcp/race/og.py` (124 lines) with all 7 mandated exports plus 3 viewport/timeout constants — module imports cleanly without `playwright` installed (D-63 prerequisite for the Wave 2 mocked test matrix).
- `OG_LAYOUT_VERSION: int = 1` appended to `race/config.py` and re-exported via `__all__`; `from a2a_vs_mcp.race.config import OG_LAYOUT_VERSION` returns `1`.
- `playwright>=1.59,<2` declared under `[project.optional-dependencies] og` — co-located with the existing `dev` and `remote-a2a` extras; CI install path unchanged.
- `data/og/*.png` ignore line appended to `.gitignore` (defensive; parent `/data/*` already covers the directory).
- 6 deterministic unit tests in `tests/race/test_og_cache.py` exercise `og_cache_path` filename shape (og + heatmap surfaces), `cleanup_stale` dir auto-create, stale-version selective unlink, per-run_id and per-surface scoping, and the no-op-when-only-current case. All 6 pass; full race suite remains green at 196 tests (190 prior + 6 new).

## Task Commits

Each task was committed atomically with `--no-verify` (parallel-executor mode):

1. **Task 1: OG_LAYOUT_VERSION + .gitignore + pyproject.toml** — `1e51789` (feat)
2. **Task 2: race/og.py module (lifespan + lock + cache helpers + render skeletons)** — `f56e33d` (feat)
3. **Task 3: tests/race/test_og_cache.py (6 tests, no Chromium)** — `306c878` (test)

_Note: TDD plan-level — full RED gate skipped because helpers and tests are independent surfaces; Task 3 functions as the post-hoc test gate. Both helpers were authored against explicit acceptance criteria so the GREEN/test contract is preserved._

## Files Created/Modified
- `src/a2a_vs_mcp/race/og.py` (created) — 7 public exports: `og_lifespan`, `OG_RENDER_LOCK`, `OG_DIR`, `og_cache_path`, `cleanup_stale`, `render_og_png`, `render_heatmap_png`. Plus constants `OG_VIEWPORT={1200x630}`, `HEATMAP_VIEWPORT={1200x900}`, `RENDER_TIMEOUT_MS=10_000`. Lazy `from playwright.async_api import async_playwright` inside `og_lifespan` body keeps module load Chromium-free.
- `tests/race/test_og_cache.py` (created) — 6 tests, pure synchronous path arithmetic; uses `monkeypatch.setattr(og_mod, "OG_DIR", tmp_path/"og")` per Phase 6/9 test pattern.
- `src/a2a_vs_mcp/race/config.py` (modified) — appended `OG_LAYOUT_VERSION: int = 1` (D-66 docstring with cache-pattern + bump-trigger); added to `__all__`.
- `pyproject.toml` (modified) — extended `[project.optional-dependencies]` table with `og = ["playwright>=1.59,<2"]`.
- `.gitignore` (modified) — appended `# Phase 10 — OG image disk cache` comment + `data/og/*.png` line.

## Public API Surface of `race/og.py`

| Export | Type | Purpose |
| --- | --- | --- |
| `og_lifespan` | `@asynccontextmanager async def(app)` | FastAPI lifespan: starts Playwright + headless Chromium; stashes both on `app.state.og_playwright`/`og_browser`; closes on shutdown. |
| `OG_RENDER_LOCK` | `asyncio.Lock` (module-scope) | Serializes concurrent renders across both surfaces (D-61). Caller MUST hold during render. |
| `OG_DIR` | `Path` | `<repo>/data/og` — mirrors `RUNS_DIR` shape (`Path(__file__).resolve().parents[3] / "data" / "og"`). |
| `og_cache_path(run_id, surface)` | `(str, Literal["og","heatmap"]) -> Path` | Returns `OG_DIR / f"{run_id}-{surface}-v{OG_LAYOUT_VERSION}.png"`. |
| `cleanup_stale(run_id, surface)` | `(str, Literal["og","heatmap"]) -> None` | Creates `OG_DIR` if missing; unlinks `<run_id>-<surface>-v*.png` files whose name != current. OG-04 contract. |
| `render_og_png(run_id, browser, base_url=...)` | `async (str, Browser, str) -> bytes` | 1200x630 anchor PNG; navigates `?og=1`; waits for `[data-og-anchor][data-og-ready="true"]`. |
| `render_heatmap_png(run_id, browser, base_url=...)` | `async (str, Browser, str) -> bytes` | 1200x900 PNG; navigates `?og=1&surface=heatmap`; waits for `[data-heatmap-anchor]`. |
| `OG_VIEWPORT` | `dict[str,int]` | `{"width": 1200, "height": 630}` |
| `HEATMAP_VIEWPORT` | `dict[str,int]` | `{"width": 1200, "height": 900}` |
| `RENDER_TIMEOUT_MS` | `int` | `10_000` (set via `page.set_default_timeout`). |

## OG_LAYOUT_VERSION at Ship Time

`OG_LAYOUT_VERSION = 1` (the v1 baseline; D-66 mandates manual bump on any anchor-region layout change). Wave 2 cache filenames will be `data/og/<run_id>-og-v1.png` and `data/og/<run_id>-heatmap-v1.png`.

## Test Status for `tests/race/test_og_cache.py`

- **Test count:** 6 functions (matches plan acceptance: `grep -c '^def test_'` returns `6`).
- **Status:** all 6 PASS in 0.88s.
- **Imports:** zero `playwright` references (D-63 satisfied: pure cache-path logic).
- **Full race suite:** 196 passed in 1.50s (190 baseline + 6 new). No Phase 6/7/8/9 regression.

## Decisions Made
- Followed plan as specified for all three tasks; no implementation choices outside the spec.
- Lazy-purge over startup-hook for `cleanup_stale` (planner discretion called out in 10-CONTEXT lines 53-54). Rationale: avoids a startup I/O pass and matches the disk cache lifecycle Wave 2 needs.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 — Acceptance criterion drift] Adjusted module-header docstring wording to satisfy `grep -c 'wait_until="domcontentloaded"'` exact-2 acceptance check**
- **Found during:** Task 2 verification.
- **Issue:** The plan's Task 2 acceptance criterion requires the literal string `wait_until="domcontentloaded"` to appear exactly twice in `race/og.py` (once per render fn, mitigating Risk-4). My initial draft also embedded the literal in the module docstring's Risk-4 note, producing a count of 3.
- **Fix:** Rewrote the docstring sentence to use bareword form `wait_until=domcontentloaded` (no quotes), preserving the documentation while matching the acceptance grep pattern. Both render-function literals remain unchanged.
- **Files modified:** `src/a2a_vs_mcp/race/og.py` (docstring only)
- **Verification:** `grep -c 'wait_until="domcontentloaded"' src/a2a_vs_mcp/race/og.py` returns `2`. `grep -c 'data-og-ready'` returns `3` (header + render_og_png + selector). All other acceptance greps pass.
- **Committed in:** `f56e33d` (Task 2 commit, single edit before commit).

**2. [Rule 2 — Missing critical hygiene] Added `__all__` exports to `race/og.py` and re-added `OG_LAYOUT_VERSION` to `race/config.py`'s `__all__`**
- **Found during:** Task 1 + Task 2 implementation.
- **Issue:** Plan listed the module exports but did not explicitly require an `__all__` declaration. Without it, `from a2a_vs_mcp.race.og import *` would behave inconsistently and the module's intended public surface is implicit. The existing `race/config.py` had a tight `__all__ = ["HEATMAP_BASELINE", "HeatmapBaseline"]` — appending the constant without updating `__all__` would silently exclude it from star-imports.
- **Fix:** Added `__all__` block to `race/og.py` enumerating all 10 documented exports; added `OG_LAYOUT_VERSION` to `race/config.py`'s `__all__` list.
- **Files modified:** `src/a2a_vs_mcp/race/og.py`, `src/a2a_vs_mcp/race/config.py`
- **Verification:** Module import + `from ... import OG_LAYOUT_VERSION` both succeed; full race suite still green.
- **Committed in:** `1e51789` (config) and `f56e33d` (og.py).

---

**Total deviations:** 2 auto-fixed (1 acceptance-criterion alignment, 1 missing public-API hygiene).
**Impact on plan:** Neither deviation alters semantics; both strengthen the public contract for Wave 2 consumers and align with the plan's stated acceptance gates. No scope creep.

## Issues Encountered
- **`.gitignore` parent-rule shadowing:** the existing `.gitignore` already ignores `/data/*` (with re-includes only for `/data/race/fixtures/**`), so the new `data/og/*.png` line is functionally redundant — `data/og/*.png` is already untracked because `data/og/` itself is ignored. Kept the explicit line per plan mandate (plan Action step 2 requires the literal line, and `grep -c 'data/og' .gitignore >= 1`); it serves as in-file documentation that this path is intentionally cached and ignored. No behavioral risk.

## Threat Surface Scan
No new trust boundaries beyond those documented in plan `<threat_model>` (T-10-01-01..05). The OG cache writes are gated by `run_id` validation in Wave 2 (`_validate_run_id` from `race/replay.py`); Wave 1 unit tests use synthetic in-memory paths only.

## Next Phase Readiness
- Wave 2 (`10-02`) can `from a2a_vs_mcp.race.og import og_lifespan, og_cache_path, cleanup_stale, render_og_png, render_heatmap_png, OG_RENDER_LOCK, OG_DIR` without modifying `og.py`.
- Wave 2 can `monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake_fn)` once `web.py` imports those names — module-level binding pattern verified by Task 3.
- `OG_LAYOUT_VERSION` is the single cache-key version source for both surfaces; Wave 2 will reference it via `cleanup_stale` (lazy purge on first request after a future bump).
- No live Chromium download required for CI — `playwright` extra is opt-in; lazy import keeps the module loadable in the default `pip install -e .[dev]` workflow.

---

## Self-Check: PASSED

- Created files exist:
  - FOUND: src/a2a_vs_mcp/race/og.py
  - FOUND: tests/race/test_og_cache.py
- Modified files contain expected content:
  - FOUND: `OG_LAYOUT_VERSION: int = 1` in src/a2a_vs_mcp/race/config.py
  - FOUND: `data/og/*.png` in .gitignore
  - FOUND: `playwright>=1.59,<2` in pyproject.toml
- Commits exist on master:
  - FOUND: 1e51789 (Task 1)
  - FOUND: f56e33d (Task 2)
  - FOUND: 306c878 (Task 3)
- Verification gates pass:
  - PASS: race/og module imports cleanly without Chromium
  - PASS: OG_LAYOUT_VERSION == 1
  - PASS: tests/race/test_og_cache.py — 6 passed
  - PASS: tests/race/ — 196 passed, no regression

---
*Phase: 10-og-image-and-sharing*
*Completed: 2026-04-30*
