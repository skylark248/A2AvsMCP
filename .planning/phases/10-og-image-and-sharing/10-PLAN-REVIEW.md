# Phase 10 — OG Image & Sharing — Plan Review

**Reviewer:** gsd-plan-checker (goal-backward)
**Reviewed:** 2026-04-30 17:10 GMT+5:30
**Plans checked:** 5 (10-01, 10-02, 10-03, 10-04, 10-05)
**Phase goal:** Make every `/race/<run_id>` URL shareable with server-rendered OG and heatmap PNGs, with a client-side fallback.

---

## 1. Requirement Coverage

| Req | ROADMAP success criterion | Covering plan(s) | Status |
|-----|---------------------------|------------------|--------|
| OG-01 | SC-1 (Twitter/LinkedIn/Slack unfurl + meta tags + og.png cache) | 10-01 (cache helpers + render skel), 10-02 (HTML route + meta-tag injection + og.png route + lifespan), 10-03 (`?og=1` + `data-og-anchor` + `data-og-ready`), 10-05 (mobile `<img>` consumer) | COVERED |
| OG-02 | SC-2 (heatmap.png 1200×900 + annotation strip) | 10-01 (render_heatmap_png + HEATMAP_VIEWPORT), 10-02 (heatmap.png route), 10-03 (HeatmapAnnotationStrip + `data-heatmap-anchor`) | COVERED |
| OG-03 | SC-3 (Copy headline image button + canvas + clipboard + fallback) | 10-04 (CopyHeadlineImageButton + html2canvas lazy + ClipboardItem + download fallback + actionSlot mount) | COVERED |
| OG-04 | SC-4 (404-before-Playwright + cleanup on version bump) | 10-01 (cleanup_stale + cache path helpers), 10-02 (`_validate_run_id` 400 + RUNS_DIR existence 404 BEFORE render call + cleanup_stale invocation) | COVERED |

All four phase requirement IDs (OG-01..OG-04) appear in at least one plan's `requirements` frontmatter field. **PASS**.

---

## 2. Locked Decision Coverage (D-61..D-66)

| Decision | Required behavior | Implementation site | Status |
|----------|-------------------|---------------------|--------|
| D-61 | Singleton Browser via FastAPI lifespan + asyncio.Lock | 10-01 Task 2 (`og_lifespan` + `OG_RENDER_LOCK = asyncio.Lock()`); 10-02 Task 1 (`app = FastAPI(..., lifespan=og_lifespan)`); 10-02 Task 2 (`async with OG_RENDER_LOCK:`) | OK |
| D-62 | Render exception → HTTP 503 (no silent placeholder); no cache write on failure | 10-02 Task 2 (`except Exception: raise HTTPException(503,...)` after the lock, BEFORE `cache.write_bytes`); 10-02 Task 3 Test 6 asserts no cache file written on exception | OK |
| D-63 | Tests mock `render_og_png`/`render_heatmap_png` via monkeypatch — no Chromium in CI | 10-01 Task 3 (no Playwright import; pure path tests); 10-02 Task 3 (`monkeypatch.setattr("a2a_vs_mcp.web.render_og_png", fake)` matrix x9); 10-04 Task 2 (`vi.mock("html2canvas")`) | OK |
| D-64 | html2canvas lazy-loaded via dynamic `import()` | 10-04 Task 1 (`const { default: html2canvas } = await import("html2canvas")` inside onClick); acceptance criterion enforces zero static top-level imports | OK |
| D-65 | ClipboardItem primary + download fallback | 10-04 Task 1 (`navigator.clipboard.write([new ClipboardItem(...)])` then `URL.createObjectURL`+`<a download>` on rejection); 10-04 Task 2 Test 2 covers fallback path | OK |
| D-66 | Manual `OG_LAYOUT_VERSION` int constant; cache pattern; lazy cleanup-on-mismatch | 10-01 Task 1 (`OG_LAYOUT_VERSION: int = 1` in race/config.py); 10-01 Task 2 (`og_cache_path` + `cleanup_stale`); 10-02 Task 2 (`cleanup_stale` invoked before cache lookup on every request) | OK with caveat (see Issue 1) |

All 6 locked decisions have implementing tasks. No contradictions detected.

---

## 3. Dependency Graph + Wave Parallelism

| Plan | Wave | depends_on | files_modified |
|------|------|------------|----------------|
| 10-01 | 1 | [] | `race/og.py`, `race/config.py`, `pyproject.toml`, `.gitignore`, `tests/race/test_og_cache.py` |
| 10-02 | 2 | [10-01] | `web.py`, `tests/race/test_og_routes.py` |
| 10-03 | 2 | [10-01] | `RacePage.tsx`, `HardnessFailureHeatmap.tsx`, `HeatmapAnnotationStrip.tsx` |
| 10-04 | 3 | [10-03] | `package.json`, `CopyHeadlineImageButton.tsx`, `CopyHeadlineImageButton.test.tsx`, `CharacteristicFailureBanner.tsx`, `RacePage.tsx` |
| 10-05 | 4 | [10-02, 10-03, 10-04] | `RacePage.tsx` |

**Wave-2 parallelism (10-02 || 10-03):** No file overlap (backend vs frontend). **OK.**
**Wave-3 (10-04):** Single plan; touches `RacePage.tsx` AFTER 10-03 has landed. **OK.**
**Wave-4 (10-05):** Single plan; touches `RacePage.tsx` AFTER 10-04 has landed. **OK.**

`web.py` only modified by 10-02 ✓
`HardnessFailureHeatmap.tsx` only modified by 10-03 ✓
`RacePage.tsx` ownership: 10-03 (Wave 2) → 10-04 (Wave 3) → 10-05 (Wave 4). Serial ordering enforced via `depends_on`. ✓

No cycles; no forward references; no parallel-wave file conflicts. **PASS.**

---

## 4. Critical Research Discovery Coverage

| Discovery | Plan task addressing it | Status |
|-----------|-------------------------|--------|
| HTML route addition with og/twitter meta injection (RESEARCH §Key Findings #1 — load-bearing) | 10-02 Task 1 (`@app.get("/race/{run_id}", response_class=HTMLResponse)` + `_inject_og_meta`) | OK |
| `data-og-ready="true"` sentinel + Playwright `wait_for_selector` blocking | 10-01 Task 2 render_og_png (`wait_for_selector('[data-og-anchor][data-og-ready="true"]')`); 10-03 Task 2 (`data-og-ready={isOgReady ? "true" : undefined}` after replay fold) | OK |
| Lifespan registration on `web.py` (currently absent) | 10-02 Task 1 step 2 explicitly mutates `app = FastAPI(..., lifespan=og_lifespan)` | OK |
| Mobile `?mode=summary` placeholder closure (Phase 8 hand-off) | 10-05 Task 1 replaces placeholder JSX with `<img src='/race/<id>/og.png'>` | OK |
| Single-flight cache miss recheck inside lock (RESEARCH Open Question 3) | 10-02 Task 2 `async with OG_RENDER_LOCK: if cache.exists(): return FileResponse(...)` re-check before render | OK |
| Mobile path correctness (no Playwright on user device) | 10-05 uses HTTP `<img>` fetch — server cache hit/miss; cache populated by desktop visitors | OK |
| Phase 6 `_validate_run_id` reuse for path-traversal guard before Playwright spawn | 10-02 Task 1 + Task 2 each invoke `_validate_run_id` first; 400 on ValueError | OK |
| Phase 9 D-47 empty-state never-unmount preservation | 10-03 Task 1 — strip is ADDITIVE inside the populated-data branch only; D-47 outer guard unchanged | OK |
| Phase 9 D-58 `run_meta` source for annotation strip | 10-03 Task 1 uses `data.baseline.{model,seed,task_ids}` from HeatmapPayload (aggregated from `run_meta` per Phase 9 D-58) | OK |

All critical research findings are explicitly delivered.

---

## 5. Task Completeness

Every task across all 5 plans has:
- `<files>` element with concrete paths
- `<read_first>` block listing canonical analogs and RESEARCH/PATTERNS line ranges
- `<behavior>` block describing observable invariants
- `<action>` block with concrete code blocks (verbatim or near-verbatim)
- `<verify>` with `<automated>` runnable command
- `<acceptance_criteria>` with grep counts, file existence, exit-0 commands, and test-pass counts
- `<done>` with measurable terminal state

No vague actions ("implement auth"), no subjective acceptance criteria ("looks correct"), no missing fields. **PASS.**

---

## 6. Scope Sanity

| Plan | Tasks | Files modified | Estimated context |
|------|-------|----------------|-------------------|
| 10-01 | 3 | 5 | normal |
| 10-02 | 3 | 2 (large web.py edit + new test file) | normal |
| 10-03 | 2 | 3 | normal |
| 10-04 | 3 | 5 | normal |
| 10-05 | 1 | 1 | small |

All within budget (target 2-3 tasks/plan). **PASS.**

---

## 7. Issues Identified

### BLOCKERS

**Issue 1 — Dimension 11: Research Resolution (#1602)**

```yaml
issue:
  dimension: research_resolution
  severity: blocker
  description: "RESEARCH.md `## Open Questions` section (line 1206) is NOT marked `(RESOLVED)`. Three open questions remain without inline RESOLVED markers, even though answers are implemented in plans:"
  file: "10-RESEARCH.md"
  line: 1206
  unresolved_questions:
    - "Q1: 'n (run count) field name in HeatmapPayload' — plan 10-03 Task 1 read_first instructs the executor to inspect `lib/types/race.ts` and substitute the correct field name; the question is implicitly deferred to execution rather than resolved at plan-time. RESEARCH lists it without a RESOLVED marker."
    - "Q2: 'Should `/race` (no run_id) also gain OG meta-tag treatment?' — plan 10-02 Task 1 ships `/race` as plain `_read_index_html()` (no meta tags). De-facto resolved (Recommendation: out of scope) but no inline RESOLVED marker."
    - "Q3: 'Single-flight on cache miss (Pitfall 6)' — plan 10-02 Task 2 includes the inside-lock re-check (resolved per Recommendation). No inline RESOLVED marker."
  fix_hint: "Update RESEARCH.md `## Open Questions` to `## Open Questions (RESOLVED)` and append RESOLVED inline markers to all three questions: Q1 RESOLVED → executor inspects type at plan time per 10-03 read_first; Q2 RESOLVED → out of scope, plain index.html for /race; Q3 RESOLVED → inside-lock re-check shipped in 10-02."
```

This is a Dimension 11 BLOCKER per gsd-plan-checker spec. Even though all three questions have de-facto answers in the plans, the RESEARCH.md document does not carry the explicit `(RESOLVED)` section heading or inline markers. Per the dimension spec: "If section heading has `(RESOLVED)` suffix → PASS; otherwise FAIL."

### WARNINGS

**Issue 2 — Dimension 1: ROADMAP cache path text contradiction**

```yaml
issue:
  dimension: requirement_coverage
  severity: warning
  description: "Plans implement cache filename as `data/og/<run_id>-<surface>-v<OG_LAYOUT_VERSION>.png` (with `-<surface>-` segment) but ROADMAP SC-1 literal text and CONTEXT D-66 spec the pattern as `data/og/<run_id>-v<OG_LAYOUT_VERSION>.png` (no surface segment). REQUIREMENTS.md OG-01 also uses the no-surface form. The surface-segmented form is necessary because og.png and heatmap.png share OG_DIR and would otherwise collide on `<run_id>-v1.png`."
  plans: ["10-01", "10-02"]
  fix_hint: "Either (a) bring the cache pattern in line with the locked text by using two subdirectories `data/og/<run_id>-v<N>.png` and `data/heatmap/<run_id>-v<N>.png`, OR (b) document the deliberate extension in PLAN frontmatter must_haves and update CONTEXT/REQUIREMENTS as a clarifying erratum. Recommended: (b) — surface-segmented is what the implementation needs and what RESEARCH+PATTERNS already specify; just record the divergence so future verifiers don't flag it."
```

The plans are internally consistent and RESEARCH.md/PATTERNS.md endorse the surface-segmented form, but the locked decision text (D-66 in CONTEXT.md and SC-1 in ROADMAP.md) reads the no-surface form. A plan-checker following CONTEXT verbatim would flag a contradiction.

**Issue 3 — Dimension 2: ROADMAP cleanup wildcard breadth**

```yaml
issue:
  dimension: task_completeness
  severity: warning
  description: "ROADMAP SC-4 says cleanup purges stale `<id>-v<old>.*` files (any extension). Plans 10-01 and 10-02 only glob `<id>-<surface>-v*.png`. With surface-segmented filenames this is consistent (only `.png` files exist) but the literal `.*` extension wildcard from ROADMAP isn't honored if a future surface adds e.g. `.webp`."
  plans: ["10-01", "10-02"]
  fix_hint: "Acceptable for v1 (only PNGs are produced). Document in 10-01 Task 2 cleanup_stale docstring that the glob is intentionally PNG-only; revisit when additional formats are introduced."
```

**Issue 4 — Dimension 4: Plan 10-03 isOgReady derivation deferred to executor**

```yaml
issue:
  dimension: key_links_planned
  severity: warning
  description: "Plan 10-03 Task 2 step 4 says `the executor must read useRaceReplay.ts and pick the most reliable signal` — the exact `isOgReady` derivation (the most safety-critical wiring for Risk 10 / blank-card OG ships) is left to executor judgment. While the suggested pattern `replay.trace !== null && baseState.lanes.pure_mcp != null` is given, the plan does not pin the actual hook field name."
  plan: "10-03"
  task: 2
  fix_hint: "Have planner inspect `useRaceReplay.ts` once at plan time and write the exact derivation into the plan action (e.g., `replay.trace !== null && Object.keys(replay.lanes ?? {}).length === 3`). Removes execution-time guesswork from the most critical visual-correctness gate."
```

This is a quality concern, not a blocker. The plan provides a credible suggested pattern and the read_first directs the executor to confirm against the hook source. Acceptable.

---

## 8. Pre-Execution Quality Gates Met

| Check | Result |
|-------|--------|
| Every requirement ID in plans `requirements` frontmatter | PASS |
| Every locked decision (D-61..D-66) has implementing task | PASS |
| Wave-parallelism file conflicts | PASS (no overlaps within a wave) |
| Tasks have `<read_first>` and `<acceptance_criteria>` | PASS |
| Subjective acceptance criteria | None — all use grep counts, exit codes, file existence |
| Vague actions missing concrete values | None — all actions have verbatim code or explicit field names |
| Critical RESEARCH discoveries delivered | PASS (all 9 enumerated) |
| Mobile path correctness | PASS (HTTP `<img>`, no client Playwright) |
| Phase boundary preservation (Phase 6/8/9) | PASS |
| Dimension 11 (Research Resolution) | **FAIL** — open questions not marked RESOLVED |

---

## VERDICT: REVISE_REQUIRED

The 5-plan decomposition is structurally excellent: requirements are mapped, locked decisions are honored, dependency waves are clean, no parallel-wave file conflicts, all critical RESEARCH discoveries (HTML route, `data-og-ready` sentinel, lifespan registration, mobile placeholder closure, single-flight cache recheck) are delivered, and acceptance criteria are objective and runnable. Phase 6 / Phase 8 / Phase 9 boundaries are preserved.

The single BLOCKER is Dimension 11 procedural: RESEARCH.md `## Open Questions` (line 1206) lacks the `(RESOLVED)` suffix and inline RESOLVED markers, even though all three questions have de-facto answers (Q1 deferred to executor type-inspection per 10-03 read_first; Q2 out-of-scope, plain HTML for `/race`; Q3 single-flight re-check shipped in 10-02 Task 2).

### Required revision actions

1. **[BLOCKER]** Edit `/Users/shivanshchoudhary/Downloads/Projects/A2AvsMCP/.planning/phases/10-og-image-and-sharing/10-RESEARCH.md` line 1206:
   - Change `## Open Questions` → `## Open Questions (RESOLVED)`
   - Append inline `RESOLVED:` markers to each of the 3 questions documenting the resolution path (executor inspection / out-of-scope / shipped in 10-02).
   - Repeat at line 1318 (`### Open Questions` summary block — the `## RESEARCH COMPLETE` recap).

2. **[WARNING — recommended, not blocking]** Add a one-line erratum note to `10-CONTEXT.md` D-66 and `.planning/REQUIREMENTS.md` OG-01 acknowledging the surface-segmented cache filename `<run_id>-<surface>-v<N>.png`. Alternatively, leave as-is and let the next phase verifier read RESEARCH.md/PATTERNS.md for the canonical form.

3. **[WARNING — quality, optional]** In 10-03 Task 2, pin the exact `isOgReady` derivation by name after a one-time inspection of `useRaceReplay.ts` at plan time (instead of "executor decides"). Removes Risk-10 ambiguity from the most safety-critical visual gate.

Once revision 1 lands, re-run plan-checker for sign-off. Revisions 2 and 3 are quality improvements that can ship as-is or be folded into a follow-up planner pass.

