# Milestones — A2A vs MCP Demo Platform

Historical record of shipped versions. Each entry summarizes what was delivered.

---

## v1.0 — Demo-Day-Ready Platform

**Shipped:** 2026-04-27
**Phases:** 5 (Phases 1-5)
**Plans:** 16
**Tasks:** ~28
**Timeline:** 2026-04-22 → 2026-04-27 (6 days)
**Commits:** 88
**LOC at close:** ~12,200

**Delivered:** Five-phase deepening of the A2A vs MCP demo platform from working prototype to demo-day-ready comparison tool. All four modes run flawlessly without an API key; trace events carry the enriched data contract; multi-step and parallel-agent scenarios make protocol depth visible; comparison UI exposes differences as first-class visual elements (swimlane timelines, side-by-side traces, outcome metrics); glossary popovers + role-first phrasing + failure walkthrough complete demo readiness for a mixed audience.

**Key Accomplishments:**

1. **Phase 1 — Stability Foundation:** Pinned `mcp>=1.27,<2` and `a2a-sdk==0.3.26`; built `FakeReasoningEngine` stub for LLM path coverage without an API key; migrated test suite to pytest + pytest-asyncio + httpx (async FastAPI integration test); shipped transport-mode badge in run header (mcp/hybrid only)

2. **Phase 2 — Backend Trace Enrichment:** Added `step_index`, `parallel_batch_id`, `started_at`, `completed_at`, and `phase` (discovery/execution) fields across all trace event types; built `A2ABroker.send_tasks_parallel()` with `timeout_ms=5000`; shipped three-tier accordion `TraceExplorer` (summary strip / protocol / full trace, 150-event render cap)

3. **Phase 3 — New Scenarios:** Added TICKET-1011 (multi-step `device_failure_warranty_refund`) and TICKET-1012 (parallel `vip_parallel_escalation`) to the seed; wired `TriageAgent._resolve_parallel()` for tag-driven parallel dispatch; shipped `TalkingPointResponse` Pydantic model + `TalkingPointCard` JSX in result cards (12 scenarios all carry talking-point objects)

4. **Phase 4 — Comparison UI:** Built `eventColors.ts` as single source of truth for protocol palette; shipped outcome metric chips (latency / round-trips / agents) on result cards; built `ParallelAgentTimeline` swimlane (recharts vertical BarChart) showing overlapping vs sequential agent execution; built `CompareTracesPanel` (dual synchronized `TraceExplorer` with scroll-sync mutex)

5. **Phase 5 — Presentation Polish:** Shipped 17-term `glossaryTerms.ts` + `GlossaryTerm.tsx` (MUI Tooltip + dotted underline); threaded `runtime` prop through TraceExplorer + CompareTracesPanel for latency badge + LLM Alert; added role-first phrasing ("Tool Access Protocol (MCP)", "Agent Coordination Protocol (A2A)"), runtime Chip, and failure summary chips on RunWorkspacePage and ComparePage

**Verification status:** Phases 1-3 PASSED at must-have level. Phase 4 PASSED at code level (3 visual checks deferred to demo-day rehearsal). Phase 5 wired end-to-end per integration check; phase-level VERIFICATION.md not produced (deferred bookkeeping).

**Known deferred items at close:**
- 3 visual verification items (P4): swimlane overlap, compare scroll sync, metrics chip visibility
- 1 missing artifact (P5): phase-level VERIFICATION.md
- 10 items in `TODOS.md` from plan-review feedback (CEO / eng / design / test)
- 6 v2 backlog items: DISC-01/02 (tool discovery), VIZ-01/02 (annotated diff + sequence diagram), SDK-01/02 (A2A 1.0 + MCP v2 migrations)

**Audit:** [.planning/milestones/v1.0-MILESTONE-AUDIT.md](milestones/v1.0-MILESTONE-AUDIT.md) — status `tech_debt` (no critical blockers, 22/22 requirements satisfied)
**Roadmap archive:** [.planning/milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
**Requirements archive:** [.planning/milestones/v1.0-REQUIREMENTS.md](milestones/v1.0-REQUIREMENTS.md)

---

## v2.0 — Race Demo + Discovery + Visualization

**Shipped:** 2026-05-04
**Phases:** 11 (Phases 6-16)
**Plans:** 52
**Timeline:** 2026-04-28 → 2026-05-04 (7 days)
**Commits:** 261
**Files Changed:** 330 (+63,371 / -230)

**Delivered:** Eleven-phase build of the Three-Lane Failure-Shape Race Demo (Pure-MCP / Pure-A2A / Hybrid runners with K=3 recovery state machine, hardness×failure heatmap, deterministic replay, shareable `/race/<run_id>` URLs with Playwright-rendered OG images), the Tool Discovery scenario with first-class `DiscoveryPhasePanel`, comparison visualization upgrades (annotated diff + interactive sequence diagram), and a formalized `DESIGN.md` design-system lock. Three gap-closure phases (14-16) wired the race-demo HTTP/WS integration, closed verification documentation, and ran live human UAT to flip Phase 11 from `human_needed` to `passed`.

**Key Accomplishments:**

1. **Phases 6-7 — Race Foundation + Backend:** TraceRecorder schema gate (8 WsEvent dataclasses, IRON RULE atomicity, threading.Lock RunWriter); three runner lanes + harness driving N parallel runs at deterministic `model=claude-sonnet-4-6, seed=42, temperature=0`; recovery state machine with K=3 turn window and `agent_msg_acknowledging_fault` regex; three v1 tasks (`summarize_repo`, `negotiate_meeting`, `book_travel`) with mock APIs

2. **Phase 8 — Race Page UI:** Three-lane scoreboard with locked information hierarchy in 1200px central column; 12 page states (pre-race / countdown / live n=1 / live n=5 / done / replay / sparse-heatmap / ws-disconnected / ws-reconnecting / indeterminate / lane-failed / heatmap-empty); `failureTagColor` map (5 entries) as single source of truth; full a11y contract (Tab order, focus-visible, aria-live, prefers-reduced-motion, prefers-contrast); 4-breakpoint responsive

3. **Phases 9-10 — Heatmap, Replay, Sharing:** Hardness-vs-failure heatmap (`HardnessFailureHeatmap.tsx` with rows = HardnessType, columns = lane, "directional · n=3 tasks · v1" pill); deterministic `/race/<run_id>` replay with two-layer fixture test; K∈{2,3,4,5} multi-task calibration confirming K=3; Playwright-rendered `/race/<run_id>/og.png` (1200×630) and `/heatmap.png` (1200×900) with `OG_LAYOUT_VERSION` cache; client-side canvas snapshot fallback via "Copy headline image"

4. **Phase 11 — Tool Discovery:** New `tool_discovery` scenario (TICKET-1013 + CUST-005 seed) exercising stale-capability-cache and unknown-tool-fallback failure modes on both MCP and A2A protocols; `DiscoveryPhasePanel.tsx` rendering MCP tool catalog + A2A agent cards side-by-side above the trace explorer; integrated into `TraceWorkspacePage` (D-73 gate) and `CompareTracesPanel` (D-72 single panel above dual column)

5. **Phase 12 — Visualization Upgrades:** Pure-TS `alignTraces()` for VIZ-01 algorithmic foundation; `AnnotatedDiffView` with side-by-side|annotated-diff toggle; hand-rolled SVG `SequenceDiagramView` (5 lifelines, click-to-pin, prefers-reduced-motion); zero new dependencies, zero new colors

6. **Phase 13 — Design System Lock:** `.planning/DESIGN.md` (158 lines) codifying the `failureTagColor` table, methodology-as-flat rule, `secondary.main` as replay-pill semantic, role-first first-mention contract, primary/secondary palette intent

7. **Phases 14-16 — Gap Closure:** B1/B2/B3/W2 race-demo wiring fixed (POST `/api/race/run`, WS `run_id` query param, `heatmap_has_data` data wiring, `ReplayScrubber.onScrub` seek); Phase 7 `07-VERIFICATION.md` aggregating RACE-01..07 evidence; `TraceWorkspacePage` discovery-panel gate harmonized with `CompareTracesPanel` event-presence check; Phase 12 code-quality cleanup; Phase 11 live human UAT (4/4 checks passed) closing `DISC-01/02` human items; bonus inline fix for `ReportService.save_report` compare-mode protocol overwrite

**Verification status:** All 31 v2.0 requirements complete. Backend 352/352 pytest. Frontend 335/335 vitest. Phase 11 verification status flipped from `human_needed` to `passed` after Phase 16 UAT (2026-05-04). Phase 7 VERIFICATION.md landed retroactively in Phase 15 (closing v1.0 process debt for v2.0).

**Audit:** [.planning/milestones/v2.0-MILESTONE-AUDIT.md](milestones/v2.0-MILESTONE-AUDIT.md) — status `gaps_found` at 2026-05-02; gaps closed by Phases 14-16 (B1/B2/B3, Phase 7 VERIF, REQUIREMENTS bookkeeping, W1, Phase 11 human items)
**Roadmap archive:** [.planning/milestones/v2.0-ROADMAP.md](milestones/v2.0-ROADMAP.md)
**Requirements archive:** [.planning/milestones/v2.0-REQUIREMENTS.md](milestones/v2.0-REQUIREMENTS.md)

---
