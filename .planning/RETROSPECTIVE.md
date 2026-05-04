# Retrospective — A2A vs MCP Demo Platform

Living retrospective. New milestone sections appended on close. Cross-milestone trends updated as data accumulates.

---

## Milestone: v1.0 — Demo-Day-Ready Platform

**Shipped:** 2026-04-27
**Phases:** 5 | **Plans:** 16 | **Tasks:** ~28 | **Commits:** 88 | **LOC:** ~12,200 | **Timeline:** 6 days

### What Was Built

Five-phase deepening of the A2A vs MCP demo platform: stability foundation (P1), backend trace enrichment (P2), multi-step + parallel scenarios (P3), comparison-clarity UI (P4), and presentation polish (P5). Shipped 22/22 v1 requirements, 88 commits, ~12,200 LOC in 6 days.

### What Worked

- **Sequential phase ordering with hard data contracts.** P2 set the trace-event field contract; P3 + P4 + P5 consumed it without renegotiation. Zero protocol/schema rework downstream.
- **Code-first, plan-second discipline on enrichment fields.** P2 plans 02-01 actually pre-implemented several P2-03 test prerequisites — tests landed GREEN at the RED commit, documented as TDD gate notes rather than reworked.
- **Single source of truth for protocol colors (UI-04).** Consolidating `protocolColor` into `eventColors.ts` paid off across 5 consumers (TraceExplorer, ComparePage, CompareTracesPanel, RunWorkspacePage, ParallelAgentTimeline) — no hardcoded protocol hex on the trace surface.
- **`runtime=mock, transport=in_process` lockdown.** Zero crashes across 5-day execution despite touching the broker, trace recorder, and three frontend pages.
- **Plan reviews caught real problems.** plan-eng-review iter 2 surfaced 11 structural gaps; plan-CEO-review caught a hybrid-drop heatmap-credibility regression that 6 prior reviews missed.
- **Per-plan SUMMARY frontmatter.** Made post-hoc traceability and verification cross-referencing trivial — even where requirements_completed wasn't always populated, decision sections + key-files served as forensic evidence.

### What Was Inefficient

- **Bookkeeping drift in REQUIREMENTS.md traceability.** 14/22 rows still marked Pending at milestone close despite shipped work — the milestone-close workflow had to flip them in the archive. Status updates should land at phase-transition time, not milestone-close time.
- **Phase 5 shipped without a VERIFICATION.md.** Process gap, not a code gap. PRES-01..04 were wired per integration check, but the formal phase-level artifact every other phase produced was skipped. Invariant should be enforced at phase-transition.
- **Phase 4 visual checks deferred.** 3 items (swimlane overlap, compare scroll sync, metrics chip visibility) are code-verifiable in principle via Playwright/visual snapshot but were left for demo-day rehearsal.
- **`api.ts` + `api.generated.ts` dual-patching.** Both files required manual edits when adding fields (talking_point in P3 caused 4 TypeScript errors that auto-fix recovered from). Costs minutes per field.
- **`ROLE_FIRST_LABELS` duplicated across 2 pages.** Intentional (page self-containment), but if a third page needs the labels in v2, this should be promoted to a shared module.
- **`gsd-sdk` binary missing from PATH.** Forced manual file-read fallback in audit-milestone + complete-milestone workflows. Worked, but slower.

### Patterns Established

- **Three-tier accordion trace UI** — summary strip (always visible) + protocol tier (collapsed) + full trace tier (collapsed) + 150-event soft render cap.
- **Tag-driven dispatch branches** — `if "parallel_investigation" in ticket.tags: return self._resolve_parallel(...)` as the first line of `resolve_with_broker()`. Crash-safe, deterministic.
- **`getProtocolColor()` import + `eventBorderColor()` helper** — module-level color tokens consumed everywhere instead of hardcoded hex.
- **`GlossaryTerm` Tooltip wrapping** — module-level `Record<string, string>` keyed by term slug + reusable component with dotted underline span.
- **Scenario test grouping** — each `SCEN-XX` gets its own `TestCase` class (`Scen01Tests`, `Scen02Tests`) instead of accreting onto a monolithic `DemoModeTests`.
- **TDD GREEN-at-RED documentation** — when prior plans pre-implemented test prerequisites, the test commit serves as a regression guard, not a discovery commit; documented in SUMMARY rather than reworked.

### Key Lessons

1. **Lock the data contract first.** P2 set the trace-event schema for P3-P5 consumption. Schema-first ordering prevented schema renegotiation downstream.
2. **Status updates need to be a phase-transition invariant.** REQUIREMENTS.md drift cost an audit cycle at close.
3. **Phase-level VERIFICATION.md should be a hard gate.** Per-plan SUMMARYs + integration check are good but not a substitute for the phase-level artifact.
4. **Plan reviews are cheap and high-yield.** plan-eng-review iter 2 + plan-CEO-review caught structural risks that single-pass review missed.
5. **`runtime=mock, transport=in_process` lockdown is worth its weight.** Demo-day reliability paid off across 88 commits without a single crash investigation.
6. **TypeScript dual-type drift is a tax.** `api.ts` ≠ `api.generated.ts` cost 4 TS errors per field addition. v2 should explore generator regeneration.

### Cost Observations

- Sessions: multiple across 6 days (gsd-progress, plan-eng-review iter 1+2, plan-CEO-review iter 1+2, plan-design-review iter 1-3, autoplan, execute-phase × 5)
- Plan reviews caught 11 structural gaps + 11 CEO outside-voice risks the primary reviews missed
- Notable: 1,100k+ tokens of past work captured in claude-mem; 98% savings via observation summaries vs raw context reload

---

## Milestone: v2.0 — Race Demo + Discovery + Visualization

**Shipped:** 2026-05-04
**Phases:** 11 (6-16) | **Plans:** 52 | **Commits:** 261 | **LOC delta:** +63,371 / -230 | **Timeline:** 7 days

### What Was Built

Eleven-phase build of the Three-Lane Failure-Shape Race Demo flagship surface: TraceRecorder schema gate (P6) → race backend with K=3 recovery state machine across three lanes/three tasks (P7) → Race page UI with 12 page states + a11y contract (P8) → hardness×failure heatmap + deterministic replay + K=3 multi-task calibration (P9) → Playwright OG/heatmap PNGs + canvas fallback (P10) → tool_discovery scenario + DiscoveryPhasePanel (P11) → annotated diff + interactive sequence diagram (P12) → DESIGN.md formalization (P13). Phases 14-16 closed audit-discovered gaps: race-demo HTTP/WS wiring (B1/B2/B3 + W2), Phase 7 VERIFICATION.md + REQUIREMENTS bookkeeping + Phase 12 cleanup, Phase 11 live human UAT (4/4 passed). All 31 v2.0 requirements complete.

### What Worked

- **PRE-DESIGN GATE (Phase 6) front-loaded.** Schema-first ordering prevented downstream renegotiation across 11 phases. Phase 7-10 consumed the 8 WsEvent dataclasses + IRON RULE atomicity without rework.
- **Risk consolidation in Phase 7.** Hybrid runner (highest-risk seam per design doc) + recovery state machine landed in the same phase. No cross-phase coordination tax.
- **K=3 calibration as test, not heuristic.** `tests/test_recovery_calibration.py` swept K∈{2,3,4,5} on all three v1 tasks; K=3 verified, not assumed.
- **`failureTagColor` map as single source of truth.** Heatmap cells + failure-state badges consume one Record<ClosedUnion>; cannot drift.
- **D-85 zero-new-deps for VIZ.** Hand-rolled SVG sequence diagram + pure-TS `alignTraces` instead of `@xyflow/react` / `motion`. Bundle stayed lean; full vitest coverage on hand-rolled code.
- **Playwright as optional dep + lazy import.** Module loadable in Chromium-free CI via `[project.optional-dependencies] og`; D-63 mocked-render matrix tests run without binary.
- **Audit-driven gap closure as separate phases (14-16) instead of re-opening shipped phases.** Cleaner traceability: each gap-closure phase has its own SUMMARY + verification surface; original phases stay archived.
- **DSGN-01 deliberately last (Phase 13).** `/design-consultation` codified shipped patterns, not speculation. DESIGN.md (158 lines) describes what already shipped.
- **Phase 11 D-67..D-73 explicit decision freeze before implementation.** Decision log included mounting policy, A2A column union behavior, sibling placeholder semantics — eliminated drift across 4 plans.
- **Inline UAT-bonus fix (Phase 16).** `ReportService.save_report` compare-mode regression caught live during UAT and fixed in same session — pragmatic over process.

### What Was Inefficient

- **Two-gate inconsistency (W1) shipped in Phase 11 and lived until Phase 15.** `TraceWorkspacePage` used scenario-string check; `CompareTracesPanel` used event-presence. Caught only at audit. Should have been event-presence from initial mount-site wiring (Plan 11-04). Cost: one Phase 15 plan (15-02) + one regression-cycle.
- **REQUIREMENTS.md drift carried v1.0 pattern into v2.0.** Stale checkboxes for OG/DISC/VIZ at audit time. Phase 15-03 verified rather than mass-flipped — but checkbox sync should land at phase-transition, not at audit.
- **Phase 7 missing VERIFICATION.md until Phase 15.** Same v1.0 process gap (P5) repeated. Phase-level verification should be a hard gate at phase-transition, not a milestone-close repair.
- **B1/B2/B3 race-demo wiring blockers shipped through Phase 7-9 unnoticed.** Phase 7 emitted on `MANAGER.publish` that nothing called; Phase 8 emitted WS without `run_id`; Phase 9 hardcoded `heatmap_has_data=false` with TODO comment that was never tracked. Integration check for end-to-end "user can hit /race and see live data" was missing across three phases. Cost: Phase 14 (4 plans).
- **Subagent quota crashes mid-phase.** Phase 10 Wave 2 (10-02 + 10-03) and Phase 12 (12-03) hit quota mid-write; salvaged via the `feedback_subagent_quota_recovery` rule. Cost: minor — recovery was clean — but exposes latent dependency on subagent budget.
- **Playwright dev-env setup friction.** Phase 16 UAT setup hit `__dirlock` lockfile issue + missing `chromium_headless_shell-1217` binary despite earlier installs; SQLAlchemy/aiohttp transitively missing from `[dev]` install. Cost: ~30 minutes of manual setup before UAT could start.

### Patterns Established

- **PRE-DESIGN GATE phase as first phase of a major milestone.** Land contracts before features.
- **Decision freeze before implementation.** D-XX series in `<phase>-CONTEXT.md` enumerated and locked before plans were written. Phases 6, 7, 11 all did this; reduced re-litigation across plans.
- **Audit-driven gap-closure phases over phase reopening.** When a milestone audit surfaces blockers, add new phases (14-16) instead of re-opening shipped phases. Preserves original phase closure narrative.
- **Single-source-of-truth tokens enforced via Record<ClosedUnion>.** `failureTagColor` map; static lookup forbids drift. Pattern reusable for future v2.1 surfaces.
- **`tests/test_*_calibration.py` for tunable parameters.** K=3, OG_LAYOUT_VERSION, etc. — calibration values held to a test, not a comment.
- **`<phase>-VERIFICATION.md` as phase-transition invariant** (re-established post-v1.0 process gap; Phase 15-01 closed Phase 7 retroactively).

### Key Lessons

1. **Integration tests are not phase tests.** Phase 7 unit-tested run_race; Phase 8 unit-tested WS reducer; Phase 9 unit-tested heatmap. Nobody tested "POST /api/race/run → live WS events render heatmap." Three independent green phases produced a non-functional surface. Add a phase-level smoke gate: "can a user hit the surface end-to-end?"
2. **Audit doc + gap-closure phases is a viable pattern.** Treating audit as triage input (not as "fail the milestone") let v2.0 close cleanly via 14/15/16 instead of dragging out original phases.
3. **DiscoveryPhasePanel two-gate inconsistency is the canonical example of "almost-the-same code in two places".** When two consumer call-sites need the same gating logic, factor the gate into a shared helper at first integration, not at audit time.
4. **Stale REQUIREMENTS.md checkboxes are still a recurring tax.** v1.0 rolled in 14 stale rows; v2.0 rolled in OG/DISC/VIZ stale boxes. The fix is sustained discipline at phase-transition, not stricter audit.
5. **Hand-rolled SVG + pure-TS algorithms beat new dependencies for visualization.** D-85 was the right call: VIZ shipped on time, full coverage, no bundle bloat.
6. **Playwright is an optional dep, not a hard dep.** Treat browser binaries the same way: lazy install, lazy import, mock in CI. Phase 10 D-63 was the right pattern; v2.1 should formalize Playwright env-setup ergonomics.
7. **Live human UAT catches what unit + integration tests miss.** `ReportService.save_report` overwrite bug only manifested when a user clicked compare on a real ticket. Reserve human UAT phases for behaviors that depend on persistence, sequencing, or cross-feature coupling.

### Cost Observations

- Sessions: 7-day execution span across 11 phases (vs v1.0 6 days / 5 phases — denser but bigger surface)
- Subagent quota: hit twice (Phase 10 Wave 2, Phase 12 Wave 2) — recoverable but adds friction
- Plan reviews: less plan-review cycling than v1.0 (CEO/eng/design ran on initial roadmap, not per-phase)
- Audit cost: one milestone audit (2026-05-02) → 3 gap-closure phases (4+4+1 plans) — net win, identified 3 BLOCKERS that would have surfaced on demo day instead

---

## Cross-Milestone Trends

(Populated as additional milestones ship.)

| Metric | v1.0 | v2.0 |
|--------|------|------|
| Phases | 5 | 11 |
| Plans | 16 | 52 |
| Tasks | ~28 | ~140 |
| Commits | 88 | 261 |
| LOC delta | +12,200 | +63,371 / -230 |
| Timeline (days) | 6 | 7 |
| Requirements satisfied | 22/22 | 31/31 |
| Phases with VERIFICATION.md at close | 4/5 | 11/11 (Phase 7 retro via Phase 15) |
| Audit-discovered blockers | 0 | 3 (B1/B2/B3) |
| Gap-closure phases needed | 0 | 3 (14/15/16) |

---

*Living document — updated at each milestone close.*
