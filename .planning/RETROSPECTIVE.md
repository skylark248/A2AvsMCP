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

## Cross-Milestone Trends

(Populated as additional milestones ship.)

| Metric | v1.0 |
|--------|------|
| Phases | 5 |
| Plans | 16 |
| Tasks | ~28 |
| Commits | 88 |
| LOC at close | ~12,200 |
| Timeline (days) | 6 |
| Requirements satisfied | 22/22 |
| Phases with VERIFICATION.md | 4/5 |

---

*Living document — updated at each milestone close.*
