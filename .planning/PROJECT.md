# A2A vs MCP Demo Platform

## What This Is

An educational demo platform that runs the same customer support ticket through four execution modes — baseline, MCP, A2A, and hybrid — to teach engineers and decision-makers how the MCP and A2A protocols work, how they differ, and when to use each. The target audience is a mixed firm audience (technical and non-technical); the delivery format is a live walkthrough with slides.

After v1.0: the platform now exposes protocol differences as first-class visual elements (swimlane timelines, side-by-side trace panels, outcome metrics), embeds presenter narration via talking-point cards, and removes jargon friction with hover-glossary popovers and role-first phrasing.

## Core Value

A side-by-side, runnable comparison that makes the differences between MCP and A2A *visible* — not described, not diagrammed, but live and traceable.

**Status after v1.0:** Held. Shipping the comparison UI confirmed visibility is the right priority — the swimlane + side-by-side panels carry the demo more than any narrative.

## Current State (v2.0 — Shipped 2026-05-04)

- All 4 demo modes (baseline, mcp, a2a, hybrid) plus the new **Three-Lane Failure-Shape Race Demo** (Pure-MCP / Pure-A2A / Hybrid) run reliably under `runtime=mock, transport=in_process`
- Race demo: deterministic harness (`model=claude-sonnet-4-6, seed=42`), K=3 recovery state machine, 12-state Race page, hardness×failure heatmap, deterministic `/race/<run_id>` replay, Playwright-rendered OG + heatmap PNGs (1200×630 / 1200×900) with `OG_LAYOUT_VERSION` cache, "Copy headline image" canvas fallback
- `tool_discovery` scenario (TICKET-1013 + CUST-005) with `DiscoveryPhasePanel` mounted above trace explorer on `TraceWorkspacePage` (D-73 event-presence gate) and `CompareTracesPanel` (D-72 single panel above dual column)
- Comparison upgrades: `AnnotatedDiffView` (`alignTraces` pure-TS algorithm) + hand-rolled SVG `SequenceDiagramView` (5 fixed lifelines, click-to-pin, prefers-reduced-motion)
- `.planning/DESIGN.md` formalizing race-demo design tokens (`failureTagColor` map, methodology-as-flat, `secondary.main` replay-pill semantic, role-first first-mention contract, palette intent)
- Backend `POST /api/race/run` + `/api/race/ws?run_id=<id>` streaming end-to-end; backend 352/352 pytest, frontend 335/335 vitest
- v2.0 totals: 261 commits, +63,371 / -230 LOC across 330 files, 7 days execution
- v1.0 carry: 17-term glossary, role-first labels, runtime Chip + LLM Alert, ParallelAgentTimeline + CompareTracesPanel still in place

## Next Milestone Goals (v2.1 candidates — not yet committed)

Top backlog (`TODOS.md` promote conditions per item):

- **SDK-01:** A2A SDK 0.3.26 → 1.0.0 migration (broker core touch)
- **SDK-02:** MCP SDK v2 (`FastMCP` → `McpServer`) migration
- **TODO-01:** Real plan-emitter hybrid (replace v1 enum tool with `propose_plan` agent step generation)
- **TODO-02:** Multi-seed n=20+ benchmark mode with bootstrap CIs (conflicts with "no winner declared" rule — promote on benchmark-flavored signal only)
- **TODO-04:** Production trace schema migrator
- **TODO-09:** HMAC-signed PNG URLs (production hardening)
- **TODO-10:** LLM-judge replacement for `agent_msg_acknowledging_fault` regex (paraphrase resilience)

<details>
<summary>v2.0 milestone summary (Phases 6-16) — historical</summary>

**Goal:** Ship the Three-Lane Failure-Shape Race Demo as the new flagship surface, add the tool-discovery scenario, and deepen the comparison story with annotated-diff and sequence-diagram visualizations. **SHIPPED 2026-05-04.**

**Delivered:**
- Three-Lane Failure-Shape Race Demo (Pure-MCP / Pure-A2A / Hybrid) with hardness×failure heatmap, recovery state machine (K=3, multi-task calibrated), shareable `/race/<run_id>` URLs with Playwright-rendered OG images
- Tool discovery scenario + `DiscoveryPhasePanel` (DISC-01/02)
- Annotated diff view (VIZ-01) + interactive sequence diagram (VIZ-02)
- DESIGN.md lock via `/design-consultation` (DSGN-01)
- Gap closure: B1/B2/B3 race-demo wiring (Phase 14), Phase 7 VERIFICATION.md + REQUIREMENTS bookkeeping + Phase 12 cleanup (Phase 15), Phase 11 live human UAT (Phase 16)

**Promoted from v1 backlog:** DISC-01/02, VIZ-01/02, race demo, TODO 3 (OG image gen), TODO 5 (DESIGN.md), TODO 8 (K=3 multi-task calibration) — all closed in v2.0
**Deferred to v2.1+:** SDK-01/02, TODO 1/2/4/6/7/9/10

</details>

## Requirements

### Validated

- ✓ Four runnable demo modes (baseline, mcp, a2a, hybrid) — pre-existing, locked under `runtime=mock, transport=in_process` in v1.0
- ✓ Mock runtime (deterministic, no API key required) — pre-existing
- ✓ OpenAI runtime path (real LLM calls via `OPENAI_API_KEY`) — pre-existing, surfaced in UI in v1.0 via runtime Chip + LLM Alert
- ✓ Trace system emitting structured protocol events per run — pre-existing, enriched in v1.0 (TRACE-01..05)
- ✓ React + MUI frontend with run workspace and trace explorer — pre-existing, three-tier accordion in v1.0
- ✓ Learning page with guided educational content — pre-existing
- ✓ Report generation, history, and ZIP export — pre-existing
- ✓ MCP client with multi-transport (in-process, stdio, streamable-http, remote) — pre-existing
- ✓ A2A broker with retry logic, agent cards, full task lifecycle — pre-existing, gained `send_tasks_parallel()` + `timeout_ms=5000` in v1.0
- ✓ Presentation/slideshow mode — pre-existing
- ✓ Demo stability — STAB-01..05 — v1.0
- ✓ Trace enrichment — TRACE-01..05 — v1.0
- ✓ Multi-step + parallel scenarios — SCEN-01..03 — v1.0
- ✓ Comparison UI (metrics chips + swimlane + side-by-side) — UI-01..05 — v1.0
- ✓ Presentation polish (glossary + role-first + runtime + failure walkthrough) — PRES-01..04 — v1.0

### Validated in v2.0 (2026-05-04)

All 31 v2.0 requirements complete — see [milestones/v2.0-REQUIREMENTS.md](milestones/v2.0-REQUIREMENTS.md) for full REQ-ID traceability:

- ✓ **TRC-01..04** — TraceRecorder schema gate (LLM/tool/agent_msg fields, `trace_schema_version`, fault_injected/observed, ws event schema) — Phase 6
- ✓ **RACE-01..07** — Race backend lanes, harness, recovery state machine, three v1 tasks, mock APIs — Phase 7 (+ Phase 14 integration wiring)
- ✓ **UIRACE-01..07** — Race page UI, 12 page states, visual contract, failureTagColor token map, responsive, a11y, glossary — Phase 8
- ✓ **HEAT-01..04** — Hardness×failure heatmap, legend strip, deterministic replay, K=3 multi-task calibration — Phase 9
- ✓ **OG-01..04** — Playwright OG/heatmap PNGs, copy-headline canvas fallback, 404-before-spawn + cache invalidation — Phase 10
- ✓ **DISC-01/02** — `tool_discovery` scenario + DiscoveryPhasePanel — Phase 11 (+ Phase 15 W1 fix + Phase 16 live UAT)
- ✓ **VIZ-01/02** — Annotated diff (`alignTraces`) + interactive sequence diagram — Phase 12
- ✓ **DSGN-01** — `.planning/DESIGN.md` formalizing race-demo tokens — Phase 13

### Active (v2.1 candidates — uncommitted)

- [ ] SDK-01 — A2A SDK 0.3.26 → 1.0.0 migration (broker core touch)
- [ ] SDK-02 — MCP SDK v2 (`FastMCP` → `McpServer`) migration
- [ ] TODO-01 — Real plan-emitter hybrid (`propose_plan` agent step generation)
- [ ] TODO-02 — Multi-seed n=20+ benchmark mode with bootstrap CIs
- [ ] TODO-04 — Production trace schema migrator
- [ ] TODO-09 — HMAC-signed PNG URLs (production hardening)
- [ ] TODO-10 — LLM-judge replacement for `agent_msg_acknowledging_fault` regex

(See `TODOS.md` in repo root for full deferred backlog with promote conditions.)

### Out of Scope

| Feature | Reason | Held after v1.0? |
|---------|--------|------------------|
| User authentication / multi-user accounts | Single-presenter demo tool, not SaaS | ✓ Held |
| Cloud / production deployment | Localhost is the delivery format | ✓ Held |
| Persistent database (SQL/NoSQL) | File-based artifact storage sufficient | ✓ Held |
| WebSocket real-time trace streaming | Mock runs <1s; reconnect complexity vs near-zero value | ✓ Held |
| LLM-generated talking-point content | Non-deterministic; presenter loses confidence | ✓ Held |
| A2A remote transport as demo path | Infra dependency that can fail live | ✓ Held |
| Editable scenarios via UI | Form validation + persistence disproportionate | ✓ Held |
| OpenTelemetry / Jaeger / Zipkin export | External infra irrelevant for self-contained demo | ✓ Held |
| New API endpoints for trace visualization | All visualization reads existing `GET /api/runs/{id}` | ✓ Held |
| Separate `MCPToolCard` / `A2AAgentCard` components | One `CapabilityCard` with protocol prop | ✓ Held |

## Context

- v2.0 shipped: cumulative ~75,000 LOC (v1.0 baseline ~12,200 + v2.0 net +63,141) across Python (FastAPI backend) and TypeScript (React + MUI frontend)
- Tech stack: Python ≥3.10 / FastAPI / pytest / pytest-asyncio / httpx / Playwright (optional, for OG renders) / anthropic / pyyaml / React 18 / MUI / recharts / react-syntax-highlighter / html2canvas — **no @xyflow/react, no motion** (D-85 honored in Phase 12)
- Test posture: backend 352/352 pytest (race + non-race), frontend 335/335 vitest; zero TypeScript errors; production frontend build passes
- Demo posture: locked to `runtime=mock, transport=in_process` for demo day; race demo runs deterministically (`seed=42, temperature=0`) without API key; OpenAI runtime opt-in (non-race surfaces only)
- v2.0 deferred items: SDK-01/02, TODO 1/2/4/6/7/9/10 (10 items in `TODOS.md`); v1.0 process debt (P5 VERIFICATION.md, P4 visual checks) still carried

## Constraints

- **Tech stack**: Python ≥3.10 / FastAPI / React / MUI — extend within existing stack, no rewrites
- **API key**: Demo must run fully in `runtime=mock` without `OPENAI_API_KEY`; LLM features are an opt-in enhancement
- **Audience**: Non-technical viewers must understand the comparison without reading code
- **Single source of truth for protocol colors**: `eventColors.ts` on comparison/trace surface (UI-04 outcome)
- **Type drift discipline**: `api.ts` and `api.generated.ts` both need manual patching when adding fields

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Lock demo day to `runtime=mock, transport=in_process` | Demo day reliability matters more than LLM authenticity | ✓ Good — zero crashes across 5-day execution |
| Pin `mcp>=1.27,<2` and `a2a-sdk==0.3.26` for v1; defer SDK migrations to v2 | SDK-01 (A2A 1.0) is a major breaking release touching broker core | ✓ Good — 88 commits without SDK churn |
| New scenarios as `DemoRepository` entries | Existing platform dispatches by scenario; fits existing pattern | ✓ Good — TICKET-1011 + TICKET-1012 added with no infra change |
| Embed talking-point cards in UI | Walkthrough + slides format means demo app itself should carry context | ✓ Good — talking-points present on all 12 scenarios; landed in P3 |
| `task_submit` reserved for parallel; sequential a2a uses `a2a_message(task_request)` | Discovered during 03-03; assertion adjustment kept SCEN-01 contract met | ✓ Good — protocol-depth contrast still visible |
| `eventColors.ts` as single source of truth on comparison/trace surface (UI-04) | Centralized color tokens; all 5 consumers import | ✓ Good — zero hardcoded protocol hex on trace surface |
| Duplicate `ROLE_FIRST_LABELS` across RunWorkspacePage + ComparePage | 4 lines × 2 keeps pages self-contained vs shared util ceremony | — Pending — revisit if a third page needs the labels |
| Manual patches in both `api.ts` and `api.generated.ts` | Generator regen path documented in inline comments | ⚠ Revisit — drift is high-friction; consider regenerator script in v2 |
| Phase 5 shipped without phase-level VERIFICATION.md | Per-plan SUMMARYs + integration check covered all 4 PRES requirements | ⚠ Revisit — process gap; restore phase-level verification in v2 |
| Phase 6 PRE-DESIGN GATE first (front-loaded by design) | Schema-first ordering prevented downstream renegotiation | ✓ Good — Phases 7-10 consumed wire dataclasses without rework |
| Hybrid runner consolidated into Phase 7 with recovery state machine | Highest-risk seam concentrated, not spread | ✓ Good — recovery + hybrid landed together; no cross-phase coordination tax |
| `failureTagColor` map (5 entries) as single source of truth | Heatmap cells + failure-state badges cannot drift apart | ✓ Good — one Record<ClosedUnion> consumed by both surfaces |
| K=3 turn window + `agent_msg_acknowledging_fault` regex with negation guard | K∈{2,3,4,5} sweep on all 3 v1 tasks confirmed K=3 optimal | ✓ Good — calibration test in `tests/test_recovery_calibration.py` |
| Phase 7 `task_config.yaml` per-task callable registries (TARGETS + BINDS) | Pydantic startup validation catches schema drift; no late runtime errors | ✓ Good — three v1 tasks loaded clean across all 11 plans |
| Playwright as optional dependency (`pyproject [project.optional-dependencies] og`) | Module loadable in Chromium-free CI; lazy import inside lifespan | ✓ Good — D-63 mocked-render matrix tests run without binary |
| Audit-discovered blockers (B1/B2/B3) closed via gap-closure phases (14-16) | Cleaner traceability than re-opening completed phases | ✓ Good — phases 14-16 each have own SUMMARY + verification |
| DSGN-01 deliberately last (Phase 13) | `/design-consultation` benefits from race-demo rules already concrete | ✓ Good — DESIGN.md (158 lines) codified shipped patterns, not speculation |
| Two-gate inconsistency on DiscoveryPhasePanel (scenario-string vs event-presence) | Caught by milestone audit W1; harmonized in Phase 15-02 | ⚠ Revisit — should have been event-presence from Phase 11 mount-site wiring |
| `ReportService.save_report` used SupportTicket-keyed name without protocol | Compare-mode regression discovered live during Phase 16 UAT | ✓ Good — fix landed inline (merge protocol runs); flagged as "fix-during-UAT is fine here" |
| D-85 zero new dependencies for VIZ (no `@xyflow/react`, no `motion`) | Hand-rolled SVG sequence diagram + pure-TS alignTraces | ✓ Good — bundle stayed lean; full vitest coverage on hand-rolled code |

---

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd-transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd-complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-05-04 — v2.0 milestone closed (11 phases, 52 plans, 261 commits)*
