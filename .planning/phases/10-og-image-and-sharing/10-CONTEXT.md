# Phase 10: OG Image & Sharing - Context

**Gathered:** 2026-04-30
**Status:** Ready for planning

<domain>
## Phase Boundary

Make every `/race/<run_id>` URL shareable on social platforms. Server-render two PNGs via headless Chromium (Playwright), wire `og:image` + `twitter:image` meta tags on the replay page, and ship a client-side canvas fallback so users can copy the headline image even when server OG generation fails.

In scope:
- `GET /race/<run_id>/og.png` — Playwright-rendered 1200×630 cropped anchor (3 lanes + characteristic-failure banner) at `data/og/<run_id>-v<OG_LAYOUT_VERSION>.png`.
- `GET /race/<run_id>/heatmap.png` — Playwright-rendered 1200×900 heatmap card with annotation strip (`run_id · model · seed · n · task_ids`); shares the `OG_LAYOUT_VERSION` cache key.
- `?og=1` mode in `RacePage.tsx` — hides chrome (top bar, methodology, heatmap) and styles the anchor region for screenshot.
- `<meta property="og:image">` + `<meta name="twitter:image">` injection on `/race/<run_id>` HTML.
- "Copy headline image" button beside the characteristic-failure banner — client-side canvas snapshot of the same 1200×630 anchor region; fallback when server OG fails.
- 404 on unknown `run_id` BEFORE Playwright spawn (reuse Phase 6 `_validate_run_id` + existence check on `data/runs/<run_id>.json`).
- Cleanup task purges stale `<id>-v<old>.*` files when `OG_LAYOUT_VERSION` bumps.
- Mobile `?mode=summary` (<480px) integration — Phase 8 left a placeholder; Phase 10 wires consumption of the OG cache for the summary anchor image.

Out of scope:
- HMAC-signed PNG URLs — TODO 9, v2.1+.
- Per-cell heatmap drilldown — Phase 11+.
- Animated / multi-frame OG variants — directional pill says "directional · v1"; static.
- Real plan-emitter / multi-seed sharing UX — TODO 1 / TODO 2 territory.
- DESIGN.md formalization of OG layout tokens — Phase 13.

</domain>

<decisions>
## Implementation Decisions

### Playwright orchestration
- **D-61:** **Singleton `Browser` launched at FastAPI startup, shared across requests; `asyncio.Lock` serializes render calls.** One persistent Chromium instance via FastAPI lifespan event; new `BrowserContext` + `Page` per render; closed after each. The lock prevents concurrent misses for different `run_id`s from thrashing the browser.
  - **Why:** Cache misses settle to ~500ms-1s after warmup vs ~2-3s for spawn-per-request. Bounded resource footprint (one process); clean shutdown via lifespan; matches FastAPI's async-native design. Alternative spawn-per-request was the master-design baseline but punishes every cache miss with full-process spin-up. Pool (N=2-4) overkill for hackathon traffic.
- **D-62:** **Playwright failure → HTTP 503; client-side canvas fallback handles user recovery.** Render timeout, browser crash, or page error returns `503 Service Unavailable` with a short retry hint. The "Copy headline image" button (D-64/D-65) is the user-facing recovery path. Social crawlers re-fetch later; demo never serves a wrong-looking placeholder image as the OG embed.
  - **Why:** Honest failure signal beats silent placeholder corruption of shareable URLs. Lazy retry doubles worst-case latency for a demo platform. Static-placeholder PNG would silently mislead crawlers. The canvas fallback already covers user-side recovery, so 503 + log is sufficient on the server side.
- **D-63:** **PNG route tests mock the render function (`render_og_png(run_id) -> bytes` and the heatmap equivalent); no real Chromium in CI.** Tests assert: 404 on unknown `run_id` skips render entirely, 200 path calls render once + writes cache, second call hits cache + skips render, `OG_LAYOUT_VERSION` bump invalidates correctly, 503 on render exception. Real Playwright is exercised only at runtime / dev.
  - **Why:** Keeps CI image small and fast. Real-Chromium tests are fragile across browser upgrades and slow. Golden-PNG comparison is high-maintenance for a hackathon. Routing + caching + invalidation are the load-bearing logic worth testing; rendering correctness is verified manually during dev.

### Client-side canvas fallback
- **D-64:** **`html2canvas` library, lazy-loaded** when "Copy headline image" is first clicked. Bundle additions kept off the initial page load via dynamic `import()`. Snapshot the DOM anchor region (the same `data-og-anchor` element Playwright targets) so server and client paths share the same source of truth.
  - **Why:** Battle-tested cross-browser; ~45KB gzipped; matches master-design "1-2 hrs CC" budget. `foreignObject` SVG hand-roll is fragile across Safari + cross-origin font edge cases. Hand-rolled Canvas API redraw triples the implementation cost and drifts from the live page. Dropping the client fallback breaks OG-03.
- **D-65:** **Canvas output via `navigator.clipboard.write([new ClipboardItem({'image/png': blob})])` with download fallback.** Primary path puts the PNG on the OS clipboard so users paste directly into Twitter/Slack composer. On Firefox or any browser that rejects `ClipboardItem` for `image/png`, auto-trigger a download of `race-<run_id>.png`. UX coverage across all modern browsers without per-browser branching in the call site.
  - **Why:** Master design says "copied to clipboard"; ClipboardItem is the only API that delivers that promise. Download-only fallback is universal but degrades the UX from one-click-to-paste into attach-then-paste. Hybrid (clipboard primary + download fallback) is ~30 min extra work and matches the "fallback affordance" spirit of OG-03.

### Cache key strategy (resolves upstream conflict)
- **D-66:** **Manual `OG_LAYOUT_VERSION` Python integer constant in `serve_ui.py` (or a sibling module).** Cache filename pattern `data/og/<run_id>-v<OG_LAYOUT_VERSION>.png`. Developer bumps the constant when the anchor-region layout changes; cleanup task purges `<id>-v<old>.*` files on next request after a bump. Honors REQUIREMENTS.md OG-01 + OG-04 verbatim and master-design §"OG image" lock.
  - **Why:** Eng-review iter 2 Decision #3 revised this to SHA-over-scoped-anchor-CSS for auto-detection of layout drift, but that introduces a PostCSS plugin or hand-extracted rule list — too much new toolchain for hackathon scope. The manual constant is simple, predictable, zero-dep, and matches the existing `HEATMAP_BASELINE` constant pattern from Phase 9 D-56. SHA-CSS auto-invalidation is parked as a follow-up if manual bumps prove painful (see Deferred).

### Claude's Discretion (researcher / planner picks)
- **`?og=1` rendering surface** — `RacePage.tsx` reads the query param and conditionally hides chrome (top bar, methodology, heatmap) vs spinning up a separate `OgRacePage` component. Same component with conditional render is the natural extension of Phase 8 D-48 (replay route reuses `RacePage`); planner may pick a separate component if conditional logic gets too dense.
- **OG/render module location** — `src/a2a_vs_mcp/race/og.py` (new) vs in-line in `serve_ui.py` vs `src/a2a_vs_mcp/og.py` outside the race subpackage. Master design says "module constant in `serve_ui.py` (or a sibling)" — researcher picks; prefer a sibling module if Playwright lifecycle (browser singleton + lock) accumulates more than ~50 lines.
- **Cleanup task trigger** — startup hook (scan `data/og/`, delete files where `v<n>` < current `OG_LAYOUT_VERSION`) vs lazy delete-on-mismatch (when serving a fresh render, opportunistically delete old-version siblings for the same `run_id`). Both yield the same observable behavior; lazy is simpler and avoids a startup I/O pass.
- **Mobile `?mode=summary` consumption shape** — fetch `/race/<run_id>/og.png` URL client-side and render an `<img>` vs server reads disk cache and inlines as base64 data URL vs render canvas snapshot in the React tree. Phase 8 deferred to Phase 10; researcher picks based on which path keeps the existing Phase 8 placeholder boundary intact.
- **`data-og-anchor` element wiring** — which DOM element marks the screenshot region. Master design says 3 lanes + banner = 1200×630. Likely the existing 1200px central column up to and including the banner; planner pins the exact element + class.
- **Heatmap.png annotation strip rendering** — added to `HardnessFailureHeatmap.tsx` only when `?og=1` (or a separate flag) is set, vs a sibling component used only by the screenshot route. Implementation detail; either preserves the Phase 9 D-47 empty-state never-unmount rule.
- **Playwright dependency** — `playwright` Python package + browser install in dev/runtime; pin a known-good Chromium version. Researcher picks the install strategy (pyproject extras vs separate dev install script) and confirms macOS + Linux runtime parity.

### Folded Todos
- **TODO 3** — OG image generation. Promoted into v2.0 (PROJECT.md). OG-01..OG-04 close this todo on phase verification.
- **TODO 9** — HMAC-signed PNG URLs. **NOT folded** — explicitly deferred to v2.1+ per master design + REQUIREMENTS.md (hackathon-ephemeral demo; 404-on-unknown-run_id is sufficient hardening for v1).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 10 requirements + roadmap
- `.planning/REQUIREMENTS.md` §OG — OG-01..OG-04 verbatim acceptance criteria.
- `.planning/ROADMAP.md` §"Phase 10: OG Image & Sharing" — 4 success criteria (Twitter/LinkedIn/Slack unfurl, heatmap.png annotation, copy-headline button, 404-before-Playwright + cleanup).
- `.planning/STATE.md` — Phase 9 closed; Phase 10 unblocked because heatmap cells are now populated for Playwright capture.

### Master design (authoritative)
- `~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-design-20260427-193227.md`
  - §"OG image (promoted from TODO 3 → v1 scope)" — locks Playwright + headless Chromium, route shape, `?og=1` mode, cache path, layout-version constant, "Copy headline image" canvas fallback, ~2-3s cache-miss budget.
  - §"Web routes" — `serve_ui.py` adds `/race/<run_id>/og.png` and `/race/<run_id>/heatmap.png`; both share Playwright infra and `OG_LAYOUT_VERSION` cache key.
  - §"Heatmap export — `/race/<run_id>/heatmap.png`" — 1200×900 + annotation strip composition.
  - §"Responsive contract" — mobile <480px `?mode=summary` consumes the OG cached PNG (line 587, 591); Phase 10 owns the wiring that Phase 8 left as a placeholder.
- `~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-eng-review-test-plan-20260427-224635.md`
  - §"`serve_ui.py` PNG routes" (lines 51-57) — 404-before-Chromium-spawn assertion, cache-hit/miss matrix, scoped-CSS-SHA test guidance (D-66 supersedes the SHA refinement; the routing assertions still apply).
  - §"Mobile-summary mode" (lines 65-69) — OG cache miss → mobile renders WITHOUT spawning Playwright (uses canvas snapshot of anchor); `?mode=live` override forces live UI even on <480px.

### Upstream phase decisions (do not re-derive)
- `.planning/phases/06-tracerecorder-schema-gate-race-foundation/06-CONTEXT.md` — `_validate_run_id` regex `^[A-Za-z0-9_-]{1,64}$` lives in `race/replay.py`; reuse for the 404-before-spawn path-traversal guard.
- `.planning/phases/08-race-page-ui-visual-contract/08-CONTEXT.md`
  - **D-48** — replay = `/race/<run_id>` route; same `RacePage` component flips data source. Phase 10 `?og=1` mode is the same shape — same component, query-param-driven render variant.
  - Mobile `?mode=summary` placeholder boundary — Phase 8 only emitted the viewport check + redirect/render-decision; Phase 10 owns the rendered output integration with the OG cache.
- `.planning/phases/09-heatmap-replay-k3-calibration/09-CONTEXT.md`
  - **D-56** — `HEATMAP_BASELINE` module-constant pattern (Phase 9). `OG_LAYOUT_VERSION` (D-66) follows the same shape: single named constant, single source of truth, single test parametrization point.
  - **D-58** — `run_meta` event emitted as the first event of every trace; `heatmap.png` annotation strip (`run_id · model · seed · n · task_ids`) reads from `run_meta` for non-aggregated single-run annotation.

### Existing code Phase 10 reuses verbatim
- `src/a2a_vs_mcp/race/replay.py` — `_validate_run_id(run_id)` + `load_run(run_id, runs_dir)`. PNG routes reuse the validator (path-traversal guard) and existence check (404 trigger before Playwright spawn).
- `src/a2a_vs_mcp/race/runs.py` — `RUNS_DIR` constant; OG route resolves `run_id` → `data/runs/<run_id>.json` existence via this.
- `src/a2a_vs_mcp/race/config.py` — Phase 9 `HEATMAP_BASELINE` constant module; `OG_LAYOUT_VERSION` may live here OR alongside the route in `serve_ui.py` (Claude's discretion).
- `src/a2a_vs_mcp/web.py` — FastAPI app with `/api/race/heatmap` (Phase 9), `/api/race/runs/<run_id>/trace` (Phase 9), `/api/race/ws` (Phase 6). PNG routes mount alongside.
- `serve_ui.py` — UI server entry; OG meta-tag injection lands on the HTML response that already serves `/race/<run_id>`.

### Existing frontend assets
- `frontend/src/features/race/RacePage.tsx` — already gates on viewport <480px with a Phase 10 placeholder comment (line 56). `?og=1` mode reads from `useSearchParams`. The `?mode=summary` placeholder is the Phase 10 wiring target.
- `frontend/src/features/race/components/CharacteristicFailureBanner.tsx` (Phase 8) — "Copy headline image" button mounts beside this banner.
- `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` (Phase 9) — heatmap.png annotation strip extends this component or a sibling, gated by the OG render flag.
- `frontend/src/lib/types/race.ts` — `RaceEvent.type` discriminator (Phase 9 D-59 deferral) — Phase 10 reads aggregated/replay payloads, doesn't touch raw events; the deferral remains parked.

### Test infrastructure
- `tests/race/` — 37+ existing race tests (Phases 6/7/9). Phase 10 adds PNG-route tests with mocked `render_og_png` (D-63).
- `tests/conftest.py` — Phase 9 added `--update-snapshots` flag; OG tests do not need snapshot infra (D-63 mocks render output).

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`_validate_run_id` + `load_run`** (`race/replay.py`): direct reuse for 404-before-Playwright. Path-traversal guard already tested.
- **`RUNS_DIR` constant** (`race/runs.py`): authoritative path to `data/runs/<run_id>.json`. Existence check trigger.
- **`HEATMAP_BASELINE` pattern** (`race/config.py`, Phase 9 D-56): named constant with single source of truth — `OG_LAYOUT_VERSION` follows the identical shape.
- **`run_meta` event** (Phase 9 D-58, first event of every trace): supplies `model · seed · task_ids` for the heatmap.png annotation strip without re-deriving from disk.
- **`RacePage.tsx` Phase 10 placeholder** (line 56): `// Full ?mode=summary redirect ships in Phase 10. Plan 06 only emits the placeholder branch.` — explicit hand-off point.
- **`fetchRaceReplay` + `RaceReplayPayload`** (Phase 8/9 client lib): Phase 10 OG-mode fetch may piggyback on the same payload contract; planner picks.

### Established Patterns
- **Module-level constant for locked config** (Phase 6 D-12 `FaultKind`, Phase 7 D-28 Pydantic validators, Phase 9 D-56 `HEATMAP_BASELINE`) — `OG_LAYOUT_VERSION` extends the pattern.
- **FastAPI lifespan for long-lived resources** — Playwright `Browser` singleton (D-61) registers on `app.router.lifespan_context`. Cleanup on shutdown.
- **Disk-backed cache + lazy invalidation** (Phase 9 D-54 in-memory cache + `race_done` invalidation) — Phase 10 cache lives on disk (PNGs are large) but the lazy-invalidate-on-version-mismatch pattern mirrors the same shape.
- **Frontend `lazy()` + `Suspense`** (existing routes) — `html2canvas` lazy-loaded via dynamic `import()` matches the pattern; first click pays the bundle cost, not initial page load.

### Integration Points
- **`web.py` route mount** — PNG routes land alongside `/api/race/heatmap` and `/api/race/runs/<run_id>/trace` (Phase 9). FastAPI route decorators with explicit `response_class=Response(media_type="image/png")` (or `FileResponse` for cache hits).
- **`RacePage.tsx` ↔ `?og=1` mode** — `useSearchParams` reads the flag; conditional render hides top bar / methodology / heatmap; `data-og-anchor` element marks the screenshot region for both Playwright and `html2canvas`.
- **`CharacteristicFailureBanner` ↔ "Copy headline image" button** — button mounts beside the banner per master design line 509; click handler dynamically imports `html2canvas`, captures `data-og-anchor`, writes via `ClipboardItem`.
- **HTML response ↔ OG meta tags** — `<meta property="og:image" content="/race/<run_id>/og.png">` and `<meta name="twitter:image">` injected on the `/race/<run_id>` HTML response (server-side or via React Helmet equivalent — researcher picks).
- **Mobile fallback ↔ OG cache** — `?mode=summary` reads from the OG cache (already-rendered or freshly captured); Phase 8 placeholder branch is the wiring target.

</code_context>

<specifics>
## Specific Ideas

- **Master design promises "subsequent are instant" for cache hits.** D-66 (manual constant) + a `FileResponse` on hit deliver this trivially; the singleton browser (D-61) only matters on misses.
- **The OG embed is the demo's reach loop.** Master design §journey lines 509-511: "screenshots banner OR clicks to heatmap" → "tweets / shares". The `og:image` meta tag is the *only* server-side feature whose audience is non-users (social-media crawlers); the canvas fallback is the *user-facing* affordance. Both must work.
- **Mobile-summary is silently load-bearing.** Phase 8 emitted only the viewport detection. If Phase 10 ships PNG generation but doesn't wire `?mode=summary` consumption, mobile share-grabs degrade to "open on desktop." Researcher must close this loop.
- **Cache-miss latency budget = 2-3s (master design figure) → tightened to ~500ms-1s with D-61 singleton.** Worth noting in PLAN.md so plan-checker doesn't flag the latency budget as ambiguous.
- **Playwright is a NEW heavy dependency.** Adds `playwright` Python package + a Chromium binary install step. Researcher must confirm install strategy works under existing dev workflows + the macOS-darwin-25 target. Pin a known-good Chromium version to insulate from upstream churn.
- **`?og=1` chrome-strip MUST hide the heatmap.** Master design §OG line 528: "hides chrome (top bar, methodology, heatmap)." Heatmap belongs on `heatmap.png`, NOT on `og.png` — different aspect ratio and crop region.

</specifics>

<deferred>
## Deferred Ideas

- **HMAC-signed PNG URLs (TODO 9)** — production hardening for share URLs. Hackathon-scope ships unsigned with 404-on-unknown-run_id as the only guard. Promote when external traffic hits the demo or when share URLs leak from controlled audiences.
- **SHA-over-scoped-anchor-CSS auto-invalidation (eng-review iter 2 Decision #3 refinement)** — superseded by D-66 manual constant for v1. Promote if manual `OG_LAYOUT_VERSION` bumps are repeatedly forgotten and trigger stale-OG embeds in the wild.
- **Playwright browser pool (N=2-4)** — if hackathon traffic patterns surface lock-contention on the singleton (D-61), promote to a small bounded pool. Unlikely at v1 scale.
- **Multi-frame / animated OG variants** — directional pill says "directional · n=3 tasks · v1"; static is the v1 contract. v2.1+ if the share narrative needs motion.
- **Per-`OG_LAYOUT_VERSION` automated visual-regression test** — golden-PNG comparison rejected for v1 (D-63). Promote when layout drift starts breaking shares silently.
- **OG endpoint observability** — logging cache hits/misses + render latency to `/api/race/health` or a Prometheus surface. Out of scope; promote with TODO 9 if production push happens.

### Reviewed Todos (not folded)
- **TODO 9 (HMAC-signed PNG URLs)** — reviewed and explicitly deferred per master design + REQUIREMENTS.md. v2.1+ when threat model changes.

</deferred>

---

*Phase: 10-og-image-and-sharing*
*Context gathered: 2026-04-30*
