# Phase 5: Presentation Polish - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Make the demo ready for a mixed audience: talking-point cards guide narration for all modes and scenarios, glossary popovers remove jargon friction by defining protocol terms on hover, the real-LLM runtime path is clearly surfaced with a latency expectation badge, and failure modes are selectable in the UI with outcomes visible in the trace. All protocol labels use role-first phrasing on first mention.

This phase does NOT add new scenarios, new trace fields, new comparison UI components, or new API endpoints. It polishes existing surfaces for demo-day readiness.

</domain>

<decisions>
## Implementation Decisions

### Glossary Popovers (PRES-02)
- **D-01:** Glossary data lives in a **hardcoded TypeScript map** (`glossaryTerms.ts`) with ~15-20 entries. Static, deterministic, no fetch call. Keyed by term slug (e.g., `mcp`, `a2a`, `agent_card`, `tool_call`).
- **D-02:** Terms are detected via **manual wrapping** with a `<GlossaryTerm term="mcp">` component at known UI locations (result cards, trace headers, compare page selectors). No auto-detection regex.
- **D-03:** Definitions appear in **MUI Tooltip** on hover. One-sentence definition per term. Lightweight, no click required — ideal for live demo pacing.
- **D-04:** Glossary terms have a **dotted underline** (`borderBottom: '1px dashed'`) as a hover affordance. Subtle but discoverable.

### Role-First Phrasing (PRES-01)
- **D-05:** Role-first phrasing applied on **first mention per page/view**. First occurrence: "Tool Access Protocol (MCP)". Subsequent mentions on same page: just "MCP". Avoids verbosity while ensuring clarity.
- **D-06:** Applied on **Run page + Compare page** — the two pages a presenter walks through during the demo. Other pages (Learning, Reports, Traces) keep existing labels.
- **D-07:** **All four modes** get role-first phrasing:
  - MCP → "Tool Access Protocol (MCP)"
  - A2A → "Agent Coordination Protocol (A2A)"
  - Baseline → "Direct Agent (Baseline)"
  - Hybrid → "Combined Protocol (Hybrid)"
- **D-08:** Talking-point cards are extended to **all modes and scenarios** (PRES-01 requires this). Existing scenarios from Phase 3 already have cards; remaining existing scenarios and mode-level cards are added.

### Real-LLM Visibility (PRES-03)
- **D-09:** A persistent **Chip in the run workspace header** shows the active runtime: "Mock Runtime" (grey) or "OpenAI Runtime" (amber). Visual indicator only — runtime is determined by `OPENAI_API_KEY` env var, not toggled by the user.
- **D-10:** A **static warning badge** in the trace explorer header: "Expect 2-5s per LLM call" with amber color. Appears only when OpenAI runtime is active. Sets audience expectations without requiring live measurement.
- **D-11:** A **colored alert banner** at the top of the trace accordion for LLM runs: "This run used OpenAI GPT-4o-mini — latency reflects real API calls". Appears only for non-mock runs. Clear, one-time callout.

### Failure-Mode Walkthrough (PRES-04)
- **D-12:** User deferred this area — existing failure toggle checkboxes in `RunWorkspacePage.tsx` already work. Phase 5 makes failure **outcomes visible in the trace** (error events highlighted, failure summary in result card) without redesigning the toggle UI.

### Claude's Discretion
- Exact glossary term list and definitions (which ~15-20 terms to include)
- `GlossaryTerm` component implementation details (styled span + MUI Tooltip wrapper)
- Which specific locations in RunWorkspacePage and ComparePage get `<GlossaryTerm>` wrappers
- Exact role-first phrasing implementation (utility function vs inline strings)
- Whether talking-point cards for existing scenarios are authored by Claude or need user review
- Runtime indicator Chip exact styling and placement within the run workspace header
- Failure event highlight styling in trace explorer (color, icon choice)
- Whether `motion` (framer-motion) is used for any subtle animations on cards/badges

</decisions>

<specifics>
## Specific Ideas

- **Glossary dotted underline**: `<span style={{ borderBottom: '1px dashed currentColor', cursor: 'help' }}>MCP</span>` wrapped in MUI Tooltip — minimal visual impact, universal hover convention.
- **Runtime chip**: Should match the transport badge Chip pattern from Phase 1 — same size, position next to it in the header row. Grey for mock, amber for OpenAI.
- **Latency badge**: "Expect 2-5s per LLM call" — this is the typical GPT-4o-mini response time. Should feel like a conference talk footnote, not an error message.
- **Role-first phrasing**: The `<GlossaryTerm>` component can double as the first-mention vehicle — the first `<GlossaryTerm term="mcp">Tool Access Protocol (MCP)</GlossaryTerm>` on the page shows the full form with tooltip; subsequent bare `MCP` mentions don't need wrapping.

</specifics>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project requirements
- `.planning/PROJECT.md` — Core value, constraints, audience (mixed technical/non-technical)
- `.planning/REQUIREMENTS.md` — PRES-01 through PRES-04 acceptance criteria (primary spec for this phase)

### Existing code (must read before implementing)
- `frontend/src/features/run-workspace/RunWorkspacePage.tsx` — Result cards, mode headers, failure toggle checkboxes, TalkingPointCard placement, runtime chip goes here
- `frontend/src/features/compare/ComparePage.tsx` — Compare page mode selectors — role-first phrasing and glossary terms applied here
- `frontend/src/components/traces/TraceExplorer.tsx` — Trace accordion — latency badge and LLM banner go here
- `frontend/src/lib/trace/eventColors.ts` — Color system single source of truth — failure highlight colors should come from here
- `frontend/src/lib/types/api.ts` — RunResult type with runtime field needed for LLM detection
- `frontend/src/lib/types/api.generated.ts` — Generated types — check for runtime/reasoning fields

### Prior phase context
- `.planning/phases/03-new-scenarios/03-CONTEXT.md` — D-11 through D-15: TalkingPointCard structure, seed data pattern, MUI Paper with colored border
- `.planning/phases/04-comparison-ui/04-CONTEXT.md` — D-10/D-11/D-12: eventColors.ts as color source of truth, protocol color palette

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TalkingPointCard` inline in `RunWorkspacePage.tsx` — Paper with colored left border, already renders headline/sentence/callout from `talking_point` field
- `eventColors.ts` — protocol colors (mcp=#1976d2, a2a=#7b1fa2, hybrid=#2e7d32, baseline=#757575) and event tone colors
- MUI `Tooltip` component — already available in MUI 7.3, no new dependency
- MUI `Chip` component — used for transport badge, metrics chips — runtime indicator follows same pattern
- MUI `Alert` component — available for LLM trace banner
- `motion` (framer-motion) — installed in Phase 4 (UI-05), available for subtle animations
- `FailureConfig` dataclass in `schemas.py` — 9 boolean failure flags already defined and wired through the API

### Established Patterns
- Chips in run workspace header row — transport badge, metrics chips — runtime Chip follows same placement
- `scenarios.json` seed data with `talking_point` objects — extend to all scenarios
- `protocolColor` lookup from `eventColors.ts` — glossary and role-first phrasing components use same color system
- Failure toggles as checkboxes in advanced settings panel of RunWorkspacePage

### Integration Points
- `frontend/src/lib/glossary/glossaryTerms.ts` — new file with term definitions map
- `frontend/src/components/glossary/GlossaryTerm.tsx` — new component (styled span + MUI Tooltip)
- `RunWorkspacePage.tsx` header — add runtime indicator Chip next to transport badge
- `TraceExplorer.tsx` header — add latency expectation badge and LLM run banner
- `RunWorkspacePage.tsx` + `ComparePage.tsx` — wrap protocol terms with `<GlossaryTerm>` on first mention

</code_context>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope. Failure-mode walkthrough (PRES-04) is in scope but implementation details are at Claude's discretion.

</deferred>

---

*Phase: 05-presentation-polish*
*Context gathered: 2026-04-27*
