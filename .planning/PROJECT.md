# A2A vs MCP Demo Platform

## What This Is

An educational demo platform that runs the same customer support ticket through four execution modes — baseline, MCP, A2A, and hybrid — to teach engineers and decision-makers how the MCP and A2A protocols work, how they differ, and when to use each. The target audience is a mixed firm audience (technical and non-technical); the delivery format is a live walkthrough with slides.

## Core Value

A side-by-side, runnable comparison that makes the differences between MCP and A2A *visible* — not described, not diagrammed, but live and traceable.

## Requirements

### Validated

- ✓ Four runnable demo modes (baseline, mcp, a2a, hybrid) — existing
- ✓ Mock runtime (deterministic, no API key required) — existing
- ✓ OpenAI runtime path (real LLM calls via OPENAI_API_KEY) — existing
- ✓ Trace system emitting structured protocol events per run — existing
- ✓ React + MUI frontend with run workspace and trace explorer — existing
- ✓ Learning page with guided educational content — existing
- ✓ Report generation, history, and ZIP export — existing
- ✓ MCP client with multi-transport (in-process, stdio, streamable-http, remote) — existing
- ✓ A2A broker with retry logic, agent cards, full task lifecycle — existing
- ✓ Presentation/slideshow mode — existing

### Active

- [ ] Multi-step workflow scenario — a ticket that requires chaining 3+ tool calls or agent handoffs, making the protocol depth visible
- [ ] Parallel agent task scenario — multiple A2A specialists running simultaneously, showing A2A's coordination advantage vs MCP's sequential tool calls
- [ ] Tool discovery scenario — side-by-side showing MCP's dynamic tool listing (server announces capabilities) vs A2A's agent card registry (agents self-describe)
- [ ] Comparison clarity improvements — UI enhancements that make A2A vs MCP differences unmissable for a non-technical viewer during a live walkthrough
- [ ] Real LLM visibility — make the OpenAI reasoning path easy to activate and clearly surfaced in the trace so audiences can see actual AI decision-making
- [ ] Slide-companion content — key takeaway panels or talking-point cards embedded in the UI per mode, aligned to the demo walkthrough script
- [ ] Demo stability pass — ensure all modes work flawlessly with `runtime=mock` (no API key needed for demo day)

### Out of Scope

- User authentication / multi-user accounts — this is a single-presenter demo tool, not a SaaS product
- Cloud/production deployment — localhost demo is the delivery format
- Persistent database (SQL/NoSQL) — file-based artifact storage is sufficient for demo purposes
- A2A remote transport improvements — local transport already demonstrates the protocol; remote adds infra complexity without educational value for this goal

## Context

- The existing codebase is clean and well-structured (see `.planning/codebase/`). All four modes already run; the educational scaffolding exists. The work is about deepening the scenarios and sharpening the presentation.
- The audience is mixed: engineers will appreciate trace depth and code fidelity; decision-makers need visual clarity on tradeoffs.
- Demo timeline: 1-2 months out.
- Current gaps: only one scenario (customer support / order status / setup error); comparison is hard to grasp at a glance; OpenAI mode exists but isn't highlighted.
- No CI, no coverage tooling — acceptable for a demo platform, but a stability pass before demo day is warranted.

## Constraints

- **Tech stack**: Python ≥3.10 / FastAPI / React / MUI — extend within existing stack, no rewrites
- **API key**: Demo must run fully in `runtime=mock` without OPENAI_API_KEY; LLM features are an opt-in enhancement
- **Timeline**: 1-2 months — prioritize scenario depth and comparison clarity over polish
- **Audience**: Non-technical viewers must understand the comparison without reading code

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep mock runtime as primary | Demo day reliability matters more than LLM authenticity | — Pending |
| Add new scenarios as new `DemoRepository` entries | Existing platform dispatches by scenario; new scenarios fit the existing pattern | — Pending |
| Embed talking-point cards in UI | Walkthrough + slides format means the demo app itself should carry context | — Pending |

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
*Last updated: 2026-04-22 after initialization*
