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
