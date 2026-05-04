# TODOS

Deferred work captured during plan reviews. Each item has motivation, tradeoffs, and the conditions under which it should be promoted.

---

## TODO 1 — Real plan-emitter hybrid (v2)

**What:** Replace the v1 `decide_recovery(tool_response, error_text) -> {retry|delegate|abort|continue}` enum tool with `propose_plan(tool_response, error_text) -> list[step]`. Each step is a tool call + on_fault choice the agent constructs.

**Why:** Plan eng review (Tension 1, 2026-04-27) called the v1 enum out as "enum-selection by LLM, not real agent-driven hybrid." The Headline framing is now demoted to factual ("Hybrid retried 3 times then delegated") because v1 cannot deliver the agency the original "Hybrid spent .31 on indecision" banner implied. v2 closes the gap.

**Pros:**
- Real agent-driven hybrid story; quotable headline returns.
- Sells the protocol-comparison narrative more honestly.
- Differentiated from any other public hybrid demo.

**Cons:**
- Unbounded plan space breaks replay determinism — multi-seed required for stable rates.
- New persistence (the plan itself, not just the trace) and replay strategy.
- Likely requires dropping the "no winner declared" rule because variance will demand statistical comparison.
- ~10–15 hrs CC.

**Context:** v1 lock-ins to preserve compatibility with — `race/runners/hybrid.py` uses pre-fixed step sequence with agent-chosen on_fault enum; agent never sees `fault_kind` directly. The v2 plan emitter will need new schema in `race/failure.py` for emitted plan steps and a non-deterministic replay path that re-fires the state machine on the recorded plan instead of recomputing it.

**Depends on / blocked by:** v1 ship + 1–2 weeks of demo feedback signaling that audiences want real agent agency, not just protocol-shape comparison.

**Promote when:** Demo audience repeatedly asks "can the hybrid actually choose its own steps?" OR a benchmark-flavored v2 is greenlit.

---

## TODO 2 — Multi-seed statistical-significance benchmark mode

**What:** Per-(lane, task) n=20+ runs with bootstrap confidence intervals on recovery-rate, TTFF, and wasted-tokens. Add winner-per-axis declaration with significance bars.

**Why:** Plan eng review (Tension 5, 2026-04-27) chose "failure-mode atlas with race-energy demo" framing over the benchmark pivot. If reception signals benchmark interest after v1 ships, this becomes the path.

**Pros:**
- Quantifiable claims; serious benchmark posture.
- Defensible against "so which one won" question.
- Aligns the UI promise (race) with the methodology.

**Cons:**
- ~20× cost (~$90+ per task per lane at Sonnet rates).
- ~6–8 hrs CC for harness + CI changes.
- Directly conflicts with the locked v1 "no winner declared" rule.
- Re-frames the project from teaching tool to benchmark.

**Context:** v1 default n=5 runs per (lane, task) for demo, n=1 for dev. Harness in `race/harness.py` is the obvious extension point. Bootstrap CIs would live in `race/statistics.py` (new). The "no winner" classifier in `race/classifier.py` would need a sibling `race/winner.py` invoked only in benchmark mode.

**Depends on / blocked by:** v1 ship; reception signal favoring benchmark over atlas.

**Promote when:** Audience is engineers asking "what does the data say" (not "show me the failure modes"), OR a sponsor/stakeholder wants protocol-procurement-grade comparison.

---

## TODO 3 — OG image generation for shareable `/race/<run_id>` URLs

**What:** Server-side render a per-run OG image (heatmap + per-lane headline + project branding) returned by `<og:image>` meta on `/race/<run_id>`.

**Why:** v1 ships with plain URLs. Social embeds (Twitter/LinkedIn/Slack) carry the heatmap into feeds, increasing reach for the shareable demo claim.

**Pros:**
- Direct lift on social engagement.
- Reuses already-computed heatmap matrix from `/api/race/<run_id>/heatmap`.

**Cons:**
- Server-side rendering infra (Playwright headless, or a Python image lib).
- ~3–5 hrs CC.
- Cache invalidation logic for the OG cache.

**Context:** `frontend/src/features/race/HardnessFailureHeatmap.tsx` is the source-of-truth render. OG generation needs either (a) headless Chromium that loads the page and screenshots, or (b) a server-side Python re-implementation of the heatmap as PNG via Pillow. (a) is more accurate but heavier; (b) drifts from the live page if the design changes.

**Depends on / blocked by:** v1 ship; observed engagement on plain URLs to justify the lift.

**Promote when:** Plain URLs hit a measurable engagement floor (or a CTA partner wants embeddable runs), AND the leaderboard 10x scope is greenlit.

---

## TODO 4 — Production trace schema migrator

**What:** Real migrator that walks v1.0 trace JSON files (`{task_id}_{mode}.json` from `_run_baseline`/`_run_mcp`/`_run_a2a`/`_run_hybrid`) into the Phase 0 race schema (with `run_id`, `lane`, `turn_index`, `error_kind`, `t_unix_ms`, `trace_schema_version`).

**Why:** Outside voice (2026-04-27) flagged that existing recorded fixtures become unreplayable after Phase 0 unless schema versioning is shipped. v1 ships only the `trace_schema_version` field + a stub no-op migrator that recognizes v1.0 traces but does not transform them. Real migrator only matters if v1.0 fixtures need to be replayed in race tooling.

**Pros:**
- Future-proofs against schema drift across releases.
- Makes the `trace_schema_version` field load-bearing rather than decorative.

**Cons:**
- ~2–3 hrs CC.
- Likely not needed if no v1.0 recorded fixtures are actually useful for race testing.

**Context:** Phase 0 adds `trace_schema_version: int` to TraceRecorder. The stub migrator lives in `race/replay.py` as `migrate_trace(events, from_version) -> events`. Real migrator implements actual transformations (synthesize `run_id` from filename, map old event types to new, set `lane = mode`, etc.).

**Depends on / blocked by:** Discovering an actual use case where a v1.0 trace must be replayed in race tooling.

**Promote when:** A user asks "can I see what an old demo run would look like in the new race UI" OR a v1.0 → race regression test requires replaying historical fixtures.

---

## TODO 5 — Run /design-consultation to lock DESIGN.md

**What:** Run the gstack /design-consultation skill after race demo v1 ships. Produce DESIGN.md that formalizes the de-facto design system — primary/secondary palette intent, the new `failureTagColor` map, when methodology renders flat vs in a card, the meaning of `secondary.main` (replay/non-live state), and the role-first first-mention contract scoped to Run + Compare + Race pages.

**Why:** Plan-design-review (2026-04-27) found that the race demo introduced three new design system rules: a 5-entry `failureTagColor` token, methodology-as-flat-section break of card-default, secondary brand repurposed as the replay-pill semaphore. None of these live in a project-wide contract today; theme.ts + eventColors.ts are the only authoritative files. Future surfaces will reinvent or drift unless DESIGN.md is locked.

**Pros:**
- Future pages stop relitigating these decisions.
- Reviewers have a contract to point at instead of taste arguments.
- New contributors onboard against a document, not a spelunk.

**Cons:**
- ~3–4 hr investment when /design-consultation runs (interactive skill).
- Requires the user to drive the consultation; not a CC-only task.
- Premature if a 4th surface never lands.

**Context:** Race demo design doc (`shivanshchoudhary-master-design-20260427-193227.md`) explicitly flags the new tokens and rules under "Alignment notes." Existing Phase 5 `05-UI-SPEC.md` is per-phase, not project-wide. /design-consultation skill produces a DESIGN.md and color/font preview pages.

**Depends on / blocked by:** Race demo v1 ships AND a 4th UI surface is on the horizon (or audience feedback signals design-system incoherence).

**Promote when:** /design-consultation is run OR a 4th surface introduces another tag-style token map OR audience screenshots show inconsistent visual identity across pages.

---

## TODO 6 — Real display typeface (replace Segoe UI)

**What:** Replace the theme.ts `fontFamily: '"Segoe UI", "Helvetica Neue", sans-serif'` for h1/h2 (display roles) with a real display typeface. Keep Segoe UI fallback for body text. Candidates: Söhne (Drei Schriftgiesserei), Fraunces (variable serif, free), Inter Display (free).

**Why:** AI-slop blacklist #11: `system-ui` or default-stack fonts as primary display read as "I gave up on typography." Race demo banner (h1, 2.4rem, the quotable artifact) sits at the visual center of the social-share screenshot — it deserves a typeface, not a fallback chain. Plan-design-review (2026-04-27) flagged this as low-medium AI-slop risk.

**Pros:**
- Visceral lift on every screenshot the project produces; banner reads as intentional.
- Engineer audience picks up "this team thought about it" cue.
- Reusable across future surfaces.

**Cons:**
- Webfont budget: licensing for Söhne (~$2k+) or self-hosting Fraunces / Inter (free, +30-80kb).
- Typography decision should NOT be improvised by an implementer mid-impl.
- Defaults are fine for v1 ship — premature without audience feedback signal.

**Context:** Project uses MUI 7.3.1; `theme.ts` typography overrides are minimal. Webfont swap is a one-file change (theme.ts + index.html `<link>` for the font CDN/self-host).

**Depends on / blocked by:** Race demo v1 ships AND audience signal (or /design-consultation surfaces typography as an explicit gap).

**Promote when:** Audience feedback on race-demo screenshots cites generic vibe OR a quote from a designer-flavored viewer mentions the type OR /design-consultation runs.

---

## TODO 7 — HardnessFailureHeatmap auto-renders rows from enum

**What:** `HardnessFailureHeatmap.tsx` reads the `HardnessType` enum at render time and auto-creates one row per enum entry (rather than hardcoding the 4 v1 types in JSX). Rows for types with zero v1 task coverage render greyed with the "no v1 task covers this type" tooltip; rows with coverage render normally.

**Why:** Success criterion in the design doc says: "a new hardness type can be added in <30 minutes." If the heatmap component hardcodes rows, adding `HardnessType.AMBIGUITY` (the v1-dropped type) back in v2 requires touching the component too — silently breaking the criterion. Plan-design-review (2026-04-27) caught the gap; promoted as an enforceability fix rather than v1 scope.

**Pros:**
- Enforces the v1 success criterion rather than aspiring to it.
- Future hardness types ship in <30 min as promised.
- Greyed row + tooltip is already the v1 visual contract for empty cells; adding a row is a no-op for that case.

**Cons:**
- ~1 hr CC during implementation.
- Slightly more JSX complexity than a hardcoded list.
- Pure ergonomics — buys nothing for the v1 demo itself.

**Context:** `HardnessType` is a Python `StrEnum` in the design doc. Frontend will need a TypeScript mirror (e.g., `frontend/src/lib/race/hardnessTypes.ts`) that gets regenerated/maintained from the Python source. Heatmap iterates that array.

**Depends on / blocked by:** Race demo v1 ships AND a 4th HardnessType candidate emerges.

**Promote when:** A 4th HardnessType is added AND the patch requires changes to `HardnessFailureHeatmap.tsx` beyond updating the enum (i.e., the >30 min violation actually fires).

---

## TODO 8 — Multi-task K=3 calibration

**What:** Run the per-fault state-machine over the 9 fictional traces from §The Assignment for `negotiate_meeting` and `book_travel`. Sweep K∈{2,3,4,5}. Confirm K=3 produces the expected tag for all 9. If K≠3 wins on any trace, design re-opens.

**Why:** Plan eng-review iter 2 (Issue 9, 2026-04-27) chose spike-only K calibration (Day 0 measures FP/FN on `summarize_repo` only). Outside voice (#2) reinforced this is convergence-on-local-optimum: K=3 is the recovery-rule's central parameter, recovery_rate is the headline metric, and 2 of 3 v1 tasks ship without ground-truth verification of K. Multi-source synthesis tasks (negotiate_meeting) and long-chain pressure tasks (book_travel) have different turn semantics — the larger lag-to-retry on those tasks is exactly what K is supposed to bound.

**Pros:**
- Closes the residual recovery-rule risk on the demo's headline metric.
- Confirms K=3 is right or surfaces the right K before a 4th task gets added.
- Cheap follow-up after fictional traces are already authored as part of the Assignment.

**Cons:**
- ~1.5 hr CC.
- Adds maintenance: if K changes, snapshot fixtures + heatmap canonical run regenerate.
- Demo ships with the risk live until the calibration runs.

**Context:** §Recovery detection state machine, lines 144-186 of `shivanshchoudhary-master-design-20260427-193227.md`. The 9 fictional traces are produced as the second deliverable in §The Assignment (line ~701). Calibration test lives in `tests/test_recovery_calibration.py` (new). Re-uses the Assignment work — no new fixture authoring needed.

**Depends on / blocked by:** v1 ship + The Assignment's 9 fictional traces being authored + at least one canonical demo run on each task.

**Promote when:** Any heatmap cell shows surprising recovery_rate, OR K=3 fails on 1+ trace in calibration sweep, OR a 4th task is added.

---

## TODO 9 — HMAC-signed PNG URLs (production hardening)

**What:** Sign `/race/<run_id>/og.png` and `/race/<run_id>/heatmap.png` with HMAC. Run page bakes signed URL into `<meta property="og:image">` and the heatmap export button. Route validates HMAC before serving (and before Chromium spawn on cache miss).

**Why:** Plan eng-review iter 2 (Issue 6, 2026-04-27) chose 404-on-unknown-run_id only — pragmatic for hackathon scope. Adversary can still loop valid run_ids if they enumerate them (run_id is in the public URL). Each cache miss spawns headless Chromium. Production deploy needs proper auth.

**Pros:**
- Eliminates the scrape-vector class of attacks entirely.
- Cache hit rate becomes a function of legitimate users only.
- Standard pattern; no novel infra.

**Cons:**
- ~2 hr CC + key rotation policy + key storage.
- Adds key-management failure mode (key leak = forge URLs).
- Overkill for v1 hackathon scope — no measurable threat.

**Context:** `/race/<run_id>/og.png` and `/race/<run_id>/heatmap.png` are Playwright screenshot routes (design doc §OG image, §Heatmap export). Unauthenticated v1 returns 404 on unknown run_id pre-Chromium-spawn (decision #6). HMAC adds: route param `?sig=<hmac>`, runtime constant `OG_HMAC_SECRET` (env var), validator before any disk lookup.

**Depends on / blocked by:** Hosted demo deploy publicly + observable scrape attempts OR Playwright resource alarm fires.

**Promote when:** A scrape attempt produces an alarm OR demo moves from hackathon-ephemeral to a long-lived hosted URL.

---

## TODO 10 — Paraphrase-resilient recovery detection (regex → LLM judge)

**What:** Replace `agent_msg_acknowledging_fault` regex with an LLM-judge classifier (Claude Haiku) returning `{ack | not_ack}` on each `agent_msg` event. Run alongside the regex during a transition window; promote LLM judge once it dominates on FP/FN against a hand-labeled corpus.

**Why:** Outside voice (#3, 2026-04-27) flagged the 30-token regex with negation guard as folklore wearing state-machine costume. FP <10% / FN <5% gates are measured on the `summarize_repo` corpus only — paraphrases like "something's off", "this doesn't look right", "I'm not sure what came back" pass under the regex but a Haiku judge catches them. The recovery rule is load-bearing for the demo's headline metric; "did the agent notice" is exactly the kind of soft semantic judgment LLMs are better at than regex.

**Pros:**
- Catches paraphrases and cross-model voice variation regex misses.
- Failure mode is a Haiku quality issue, not a regex maintenance issue (much cleaner ownership).
- Future tasks/models compose without regex re-tuning.

**Cons:**
- ~3 hr CC + Haiku call per `agent_msg` event = added latency in live race (mitigatable via async fire-and-forget then reconciliation post-race).
- Cost: Haiku per agent message at n=5 across 3 lanes = ~$0.05-0.20 per demo run. Negligible at v1 scale, real at benchmark scale.
- Failure mode at runtime: Haiku unavailable → degraded fall-back to regex → quality drift.

**Context:** Recovery rule defined in design doc §Recovery detection (lines 144-186). Current regex at line 159. FP/FN corpus at `tests/fixtures/recovery_regex_corpus.jsonl`. The transition window is the right way in: keep regex as live primitive in v1, ship Haiku judge in shadow mode, promote when Haiku FN < regex FN on the same corpus.

**Depends on / blocked by:** v1 ships AND regex measured FN > 5% on a real production trace (any task/model) OR a single trace ships where regex misses an obvious ack.

**Promote when:** A real-world trace surfaces an ack the regex missed AND the regex re-tune required is non-local (touches existing rules, not just additive tokens).
