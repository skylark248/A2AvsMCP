# A2A vs MCP Demo Platform

## What This Is

An educational demo platform that runs the same customer support ticket through four execution modes — baseline, MCP, A2A, and hybrid — to teach engineers and decision-makers how the MCP and A2A protocols work, how they differ, and when to use each. The target audience is a mixed firm audience (technical and non-technical); the delivery format is a live walkthrough with slides.

After v1.0: the platform now exposes protocol differences as first-class visual elements (swimlane timelines, side-by-side trace panels, outcome metrics), embeds presenter narration via talking-point cards, and removes jargon friction with hover-glossary popovers and role-first phrasing.

## Core Value

A side-by-side, runnable comparison that makes the differences between MCP and A2A *visible* — not described, not diagrammed, but live and traceable.

**Status after v1.0:** Held. Shipping the comparison UI confirmed visibility is the right priority — the swimlane + side-by-side panels carry the demo more than any narrative.

## Current State (v1.0 — Shipped 2026-04-27)

- All 4 demo modes (baseline, mcp, a2a, hybrid) run reliably under `runtime=mock, transport=in_process` — no API key required
- Trace events carry the full enrichment contract: `step_index`, `parallel_batch_id`, `started_at`, `completed_at`, `phase`
- 12 seed scenarios including TICKET-1011 (multi-step) and TICKET-1012 (parallel agents)
- Comparison UI: outcome metrics chips, `ParallelAgentTimeline` (recharts swimlane), `CompareTracesPanel` (dual synchronized TraceExplorer)
- Presentation polish: 17-term glossary popovers, role-first protocol labels, runtime indicators (latency badge + LLM Alert), failure summary chips
- 88 commits, ~12,200 LOC (Python + TypeScript), 5 days execution

## Current Milestone: v2.0 Race Demo + Discovery + Visualization

**Goal:** Ship the Three-Lane Failure-Shape Race Demo as the new flagship surface, add the tool-discovery scenario, and deepen the comparison story with annotated-diff and sequence-diagram visualizations.

**Target features:**
- Three-Lane Failure-Shape Race Demo (Pure-MCP / Pure-A2A / Hybrid) with hardness×failure heatmap, recovery state machine (K=3, multi-task calibrated), shareable `/race/<run_id>` URLs with server-rendered OG images
- Tool discovery scenario + `DiscoveryPhasePanel` (DISC-01/02) — surface MCP/A2A discovery as first-class UI
- Annotated diff view between protocol traces (VIZ-01)
- Interactive sequence diagram for protocol flows (VIZ-02)
- DESIGN.md lock via `/design-consultation` (TODO 5) — formalize new race-demo tokens (`failureTagColor`, methodology-as-flat, secondary-as-replay-pill)

**Promoted TODOs:** TODO 3 (OG image gen), TODO 5 (DESIGN.md), TODO 8 (K=3 multi-task calibration)
**Deferred:** SDK-01/02 (A2A 1.0 + MCP v2 migrations), TODO 1/2/4/6/7/9/10 — promote conditions in `TODOS.md`

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

### Active

Set during `/gsd-new-milestone` for v2.0 — see `.planning/REQUIREMENTS.md` for the v2.0 REQ-ID list. Categories:

- **RACE-** — Three-Lane Failure-Shape Race Demo (lanes, hardness/failure, heatmap, recovery state machine, OG image, shareable URLs)
- **DISC-** — Tool discovery scenario + DiscoveryPhasePanel
- **VIZ-** — Annotated diff view + interactive sequence diagram
- **DSGN-** — DESIGN.md lock + design-system formalization

### Promoted into v2.0 (from v1 backlog)

- DISC-01 / DISC-02 — Tool discovery scenario + DiscoveryPhasePanel
- VIZ-01 / VIZ-02 — Annotated diff view + interactive sequence diagram
- Three-Lane Failure-Shape Race Demo (CEO+eng+design-cleared design, hybrid restored)
- TODOs 3 (OG image), 5 (DESIGN.md), 8 (K=3 multi-task calibration)

### Carried to v2.1+ Backlog

- SDK-01 / SDK-02 — A2A SDK 1.0 migration + MCP SDK v2 (`FastMCP` → `McpServer`)
- TODOs 1, 2, 4, 6, 7, 9, 10 in `TODOS.md` (project root) — promote conditions per item

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

- v1.0 shipped: ~12,200 LOC across Python (FastAPI backend) and TypeScript (React + MUI frontend)
- Tech stack: Python 3.10+ / FastAPI / pytest / React / MUI / recharts / @xyflow/react / motion / react-syntax-highlighter
- Test posture: 78 backend tests (pytest + pytest-asyncio + httpx async ASGI); zero TypeScript errors; production frontend build passes
- Demo posture: locked to `runtime=mock, transport=in_process` for demo day; OpenAI runtime opt-in
- Audience: mixed (engineers + decision-makers); demo timeline 1-2 months out from milestone start
- v1.0 deferred items: 3 P4 visual checks, 1 missing P5 VERIFICATION.md, 10 TODOS.md items, 6 v2 backlog requirements

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
*Last updated: 2026-04-28 — v2.0 milestone started (Race Demo + Discovery + Visualization)*
