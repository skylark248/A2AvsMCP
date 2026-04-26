# Phase 5: Presentation Polish - Research

**Researched:** 2026-04-27
**Domain:** React/MUI UI polish — glossary popovers, role-first phrasing, runtime indicators, failure-mode trace visibility
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Glossary Popovers (PRES-02)**
- D-01: Glossary data lives in a hardcoded TypeScript map (`glossaryTerms.ts`) with ~15-20 entries. Static, deterministic, no fetch call. Keyed by term slug (e.g., `mcp`, `a2a`, `agent_card`, `tool_call`).
- D-02: Terms are detected via manual wrapping with a `<GlossaryTerm term="mcp">` component at known UI locations (result cards, trace headers, compare page selectors). No auto-detection regex.
- D-03: Definitions appear in MUI Tooltip on hover. One-sentence definition per term. Lightweight, no click required.
- D-04: Glossary terms have a dotted underline (`borderBottom: '1px dashed'`) as a hover affordance.

**Role-First Phrasing (PRES-01)**
- D-05: Role-first phrasing applied on first mention per page/view. First occurrence: "Tool Access Protocol (MCP)". Subsequent mentions on same page: just "MCP".
- D-06: Applied on Run page + Compare page only. Other pages keep existing labels.
- D-07: All four modes get role-first phrasing — MCP → "Tool Access Protocol (MCP)", A2A → "Agent Coordination Protocol (A2A)", Baseline → "Direct Agent (Baseline)", Hybrid → "Combined Protocol (Hybrid)".
- D-08: Talking-point cards are extended to all modes and scenarios.

**Real-LLM Visibility (PRES-03)**
- D-09: A persistent Chip in the run workspace header shows the active runtime: "Mock Runtime" (grey) or "OpenAI Runtime" (amber). Visual indicator only — runtime determined by `OPENAI_API_KEY` env var, not user-toggled.
- D-10: A static warning badge in the trace explorer header: "Expect 2-5s per LLM call" with amber color. Appears only when OpenAI runtime is active.
- D-11: A colored alert banner at the top of the trace accordion for LLM runs: "This run used OpenAI GPT-4o-mini — latency reflects real API calls". Appears only for non-mock runs.

**Failure-Mode Walkthrough (PRES-04)**
- D-12: Failure toggle checkboxes in RunWorkspacePage.tsx already work. Phase 5 makes failure outcomes visible in the trace (error events highlighted, failure summary in result card) without redesigning the toggle UI.

### Claude's Discretion
- Exact glossary term list and definitions (~15-20 terms)
- `GlossaryTerm` component implementation details (styled span + MUI Tooltip wrapper)
- Which specific locations in RunWorkspacePage and ComparePage get `<GlossaryTerm>` wrappers
- Exact role-first phrasing implementation (utility function vs inline strings)
- Whether talking-point cards for existing scenarios are authored by Claude or need user review
- Runtime indicator Chip exact styling and placement within the run workspace header
- Failure event highlight styling in trace explorer (color, icon choice)
- Whether `motion` (framer-motion) is used for any subtle animations on cards/badges

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PRES-01 | Talking-point cards added for all existing modes and new scenarios; all protocol labels use role-first phrasing | All 12 scenarios already have `talking_point` objects in scenarios.json — verified. Role-first phrasing via `GlossaryTerm` first-mention pattern. |
| PRES-02 | Protocol glossary popovers — hovering any protocol term shows a one-sentence definition | New `glossaryTerms.ts` map + `GlossaryTerm` component wrapping MUI Tooltip. MUI Tooltip is already installed. |
| PRES-03 | Real LLM path visually called out in trace explorer with a latency expectation badge on the LLM toggle | Runtime field on `RunResult` already exists (`item.runtime: string`). Chip and Alert patterns established in the codebase. |
| PRES-04 | `FailureConfig` failure paths made selectable and visible in the UI for a failure-mode walkthrough | `isTraceFailureEvent()` already in `utils.ts`. Failure filter already exists in TraceExplorer. Need failure summary in result card. |
</phase_requirements>

---

## Summary

Phase 5 is a pure UI polish phase — no new API endpoints, no new backend logic, no new scenarios. Every capability needed is already present in the codebase and needs surface-level wiring or wrapping. The work is additive: new small components, new data files, and targeted insertions into three existing files (`RunWorkspacePage.tsx`, `ComparePage.tsx`, `TraceExplorer.tsx`).

**Key finding:** All 12 scenarios already have `talking_point` objects in `scenarios.json` — PRES-01's "cards for all scenarios" requirement is already satisfied at the data layer. The work is ensuring the TalkingPointCard render path fires for all modes, including when `mode=all` runs return results for baseline, mcp, a2a, and hybrid simultaneously. The card render already uses `item.ticket?.talking_point` — so the only gap is verifying all modes receive the talking_point data through the API.

**Runtime detection:** `RunResult.runtime` is a plain `string` field (not optional, not nullable) containing values like `"mock"` or `"llm"`. This makes LLM detection straightforward: `item.runtime !== "mock"` or `item.runtime === "llm"`.

**Failure visibility:** `isTraceFailureEvent()` in `utils.ts` already identifies failure events. The TraceExplorer already has a "only failures" filter. The gap is: failure events are not visually distinguished in the result card (the `item.failures` string array exists but is not rendered).

**Primary recommendation:** Implement in four parallel tracks — (1) glossary system, (2) role-first phrasing wrappers, (3) runtime indicator badges, (4) failure outcome visibility. No dependencies between tracks.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Glossary term definitions | Frontend (static data) | — | Pure static TypeScript map, no API needed |
| GlossaryTerm component | Frontend (React component) | — | Styled span + MUI Tooltip, client-side only |
| Role-first phrasing | Frontend (React component) | — | Display concern, no backend involvement |
| Runtime indicator Chip | Frontend (React) | — | Reads `item.runtime` already returned by API |
| Latency badge in TraceExplorer | Frontend (React) | — | Static text, conditioned on runtime prop |
| LLM run alert banner | Frontend (React) | — | Conditioned on `runtime !== "mock"` |
| Failure event highlighting | Frontend (React) | — | `isTraceFailureEvent()` already exists |
| Failure summary in result card | Frontend (React) | — | `item.failures` string[] already in RunResult |
| Talking-point cards for all modes | Frontend (React) | — | Data already in scenarios.json; render path already exists |

---

## Standard Stack

### Core (Already Installed — No New Dependencies)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `@mui/material` | 7.3.1 | Tooltip, Chip, Alert, Paper, Typography | Project-wide UI library [VERIFIED: package.json] |
| `@mui/icons-material` | 7.3.1 | Warning/info icons for badges | Matches existing icon imports in TraceExplorer [VERIFIED: package.json] |
| `motion` (framer-motion) | 12.38.0 | Optional subtle animations | Already installed in Phase 4 (UI-05) [VERIFIED: package.json] |
| React | 19.2.0 | Component framework | Project standard [VERIFIED: package.json] |
| TypeScript | 5.9.3 | Type safety | Project standard [VERIFIED: package.json] |

**No new npm installs required for this phase.** All needed libraries are already in `package.json`.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| MUI Tooltip | Radix Popover / Floating UI | MUI Tooltip is already available and matches existing design system; no new dep needed |
| Static TS map for glossary | JSON file / API endpoint | Static TS map is type-safe, tree-shakeable, no async path — correct choice for deterministic demo content |
| Inline conditional for runtime | Separate hook | Inline is fine given the narrow scope — one `item.runtime !== "mock"` check |

---

## Architecture Patterns

### System Architecture Diagram

```
Run Page / Compare Page
        │
        ▼
┌─────────────────────────────────────────┐
│  GlossaryTerm component                 │
│  (wraps protocol labels at first use)   │
│         │                               │
│         ▼                               │
│  glossaryTerms.ts (static TS map)       │
│  key: slug → value: one-sentence def    │
│         │                               │
│         ▼                               │
│  MUI Tooltip (hover popover)            │
└─────────────────────────────────────────┘

RunWorkspacePage (result map)
        │
        ├── Runtime Chip (reads item.runtime)
        │         └─ "Mock Runtime" (grey) | "OpenAI Runtime" (amber)
        │
        └── TalkingPointCard (reads item.ticket.talking_point)
                  └─ Already renders for all modes via result.results.map()

TraceExplorer (receives runtime prop)
        │
        ├── Latency badge (if runtime === "llm")
        │         └─ "Expect 2-5s per LLM call" — amber Chip in header
        │
        └── LLM Alert banner (if runtime !== "mock")
                  └─ MUI Alert at top of accordion area

TraceExplorer (failure event rows)
        │
        └── ProtocolEventRow (already uses eventBorderColor)
                  └─ error tone → red border (#c62828) — already implemented
                     failure summary list → new addition to result card
```

### Recommended Project Structure

```
frontend/src/
├── lib/
│   └── glossary/
│       └── glossaryTerms.ts        # NEW — term slug → one-sentence definition map
├── components/
│   └── glossary/
│       └── GlossaryTerm.tsx        # NEW — styled span + MUI Tooltip wrapper
├── features/
│   ├── run-workspace/
│   │   └── RunWorkspacePage.tsx    # MODIFIED — runtime Chip, GlossaryTerm wrappers, failure summary
│   └── compare/
│       └── ComparePage.tsx         # MODIFIED — role-first phrasing, GlossaryTerm wrappers
└── components/
    └── traces/
        └── TraceExplorer.tsx       # MODIFIED — latency badge, LLM banner, runtime prop
```

### Pattern 1: GlossaryTerm Component

**What:** A styled `<span>` with dotted underline that wraps its children in an MUI Tooltip showing the glossary definition on hover.

**When to use:** Wherever a protocol term appears on first mention in RunWorkspacePage or ComparePage.

**Implementation:**
```typescript
// frontend/src/components/glossary/GlossaryTerm.tsx
// [ASSUMED] — pattern derived from D-01 through D-04 in CONTEXT.md
import Tooltip from "@mui/material/Tooltip";
import { glossaryTerms } from "../../lib/glossary/glossaryTerms";

interface GlossaryTermProps {
  term: string;         // slug key — e.g., "mcp", "a2a", "tool_call"
  children: React.ReactNode;
}

export function GlossaryTerm({ term, children }: GlossaryTermProps) {
  const definition = glossaryTerms[term];
  if (!definition) return <>{children}</>;
  return (
    <Tooltip title={definition} arrow>
      <span
        style={{
          borderBottom: "1px dashed currentColor",
          cursor: "help",
          textDecoration: "none",
        }}
      >
        {children}
      </span>
    </Tooltip>
  );
}
```

### Pattern 2: Glossary Terms Map

**What:** A TypeScript Record keyed by slug with one-sentence definitions for each protocol term.

**Suggested ~15-20 terms (Claude's discretion per CONTEXT.md D-01):**
```typescript
// frontend/src/lib/glossary/glossaryTerms.ts
// [ASSUMED] — term list per Claude's discretion
export const glossaryTerms: Record<string, string> = {
  mcp: "Model Context Protocol — a standard that lets an LLM call server-hosted tools via a structured request/response contract.",
  a2a: "Agent-to-Agent protocol — a Google-led standard where agents advertise capabilities via Agent Cards and delegate tasks to peer agents.",
  tool_call: "A discrete request from an LLM to invoke a named function exposed by an MCP server.",
  task_submit: "An A2A operation where one agent sends a unit of work to a specialist agent for asynchronous handling.",
  agent_card: "A JSON manifest that describes an A2A agent's identity, capabilities, and endpoint — the discovery document for peer agents.",
  transport: "The channel over which protocol messages travel — in-process (same process), stdio (subprocess pipe), HTTP, or remote HTTP.",
  broker: "The A2A orchestrator that receives a ticket, classifies intent, and dispatches tasks to the right specialist agents.",
  specialist_agent: "An A2A agent focused on a single domain (e.g., billing, documentation) that handles delegated tasks from the broker.",
  parallel_dispatch: "An A2A pattern where the broker sends tasks to multiple specialists simultaneously rather than sequentially.",
  step_index: "A monotonically increasing counter on trace events that shows the depth of sequential tool calls within a single run.",
  parallel_batch_id: "A shared identifier on events that belong to the same parallel dispatch batch, enabling swimlane grouping.",
  discovery_phase: "The initial portion of an A2A run where agents register and the broker resolves which specialists to contact.",
  execution_phase: "The portion of a run where tools are called (MCP) or tasks are dispatched (A2A) to produce the final answer.",
  mock_runtime: "A fully deterministic in-process execution path that requires no API keys and produces consistent trace data.",
  llm_runtime: "The OpenAI GPT-4o-mini execution path where real LLM calls are made — latency reflects live API response times.",
  baseline: "The single-agent execution mode where one LLM handles the ticket without MCP tools or A2A coordination.",
  hybrid: "A mode that combines MCP tool access with A2A agent coordination — both protocols active in the same run.",
};
```

### Pattern 3: Runtime Chip in RunWorkspacePage

**What:** A Chip adjacent to the existing transport badge chip, reading `item.runtime` from the run result.

**Implementation reference (existing transport chip pattern — line 866 of RunWorkspacePage.tsx):**
```tsx
// EXISTING pattern (line 864-868 of RunWorkspacePage.tsx) [VERIFIED: codebase read]
{item.mcp_transport ? (
  <Chip label={item.mcp_transport} size="small" variant="outlined" color="default" />
) : null}

// NEW runtime chip follows same pattern (D-09)
// [ASSUMED] — exact placement at Claude's discretion
<Chip
  label={item.runtime === "llm" ? "OpenAI Runtime" : "Mock Runtime"}
  size="small"
  color={item.runtime === "llm" ? "warning" : "default"}
  variant="outlined"
/>
```

### Pattern 4: TraceExplorer Runtime Props

**What:** Pass `runtime` prop into TraceExplorer to conditionally render the latency badge and LLM alert banner.

**Current TraceExplorer interface (verified):**
```typescript
// [VERIFIED: codebase read — TraceExplorer.tsx line 38-43]
interface TraceExplorerProps {
  events: TraceEvent[];
  title?: string;
  subtitle?: string;
  // NEW: runtime prop to conditionally render LLM indicators
  runtime?: string;  // will be added
}
```

**New conditional renders inside TraceExplorer:**
```tsx
// Latency badge (D-10) — in header area, amber Chip
{runtime === "llm" && (
  <Chip
    label="Expect 2-5s per LLM call"
    size="small"
    color="warning"
    icon={<WarningAmberRoundedIcon fontSize="small" />}
  />
)}

// LLM run Alert banner (D-11) — at top of accordion area
{runtime !== "mock" && runtime !== undefined && (
  <Alert severity="warning" sx={{ mb: 1 }}>
    This run used OpenAI GPT-4o-mini — latency reflects real API calls.
  </Alert>
)}
```

### Pattern 5: Failure Summary in Result Card

**What:** Render `item.failures` (already a `string[]` in `RunResult`) as visible failure chips or a list in the result card, below the final answer.

**Current state (verified):** `item.failures` field exists in `RunResult` interface (api.ts line 95) and is returned by the backend — but nothing in RunWorkspacePage renders it.

```tsx
// [ASSUMED] — exact styling at Claude's discretion
{item.failures.length > 0 && (
  <Stack spacing={0.5}>
    <Typography variant="caption" sx={{ color: "error.main", fontWeight: 600 }}>
      Failure Events ({item.failures.length})
    </Typography>
    <Stack direction="row" spacing={0.5} flexWrap="wrap" useFlexGap>
      {item.failures.map((f, i) => (
        <Chip key={i} label={f} size="small" color="error" variant="outlined" />
      ))}
    </Stack>
  </Stack>
)}
```

### Anti-Patterns to Avoid

- **Auto-detection regex for glossary terms:** D-02 explicitly locks manual wrapping — do not attempt to scan rendered text with regex.
- **Fetching glossary from an API:** D-01 locks static TS map — no fetch, no useEffect, no async path.
- **Applying role-first phrasing to all pages:** D-06 locks to Run page + Compare page only.
- **Redesigning failure toggle UI:** D-12 locks — existing checkboxes/switches stay; only add outcome visibility.
- **Adding new backend endpoints:** Out of scope per REQUIREMENTS.md (all visualization reads existing `GET /api/runs/{id}`).
- **Using recharts/xyflow for new visualizations:** Those are Phase 4 libraries; Phase 5 does not add new visualizations.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hover popover for glossary terms | Custom portal + position logic | MUI Tooltip | Already installed, handles positioning, keyboard accessibility, and touch targets automatically |
| Failure event detection | New event-type checking logic | `isTraceFailureEvent()` from utils.ts | Already handles all 8 failure event types (error, tool_error, a2a_remote_failure, triage_warning, task_retry, task_error, a2a_remote_retry) [VERIFIED: utils.ts] |
| Protocol color lookup for failure highlights | New color constants | `toneColor.error` from eventColors.ts | `#c62828` already defined; `eventBorderColor()` already applies it to error-tone events [VERIFIED: eventColors.ts] |
| Runtime badge color logic | New color system | MUI Chip `color="warning"` | Amber is MUI's standard warning color — no custom hex needed |

---

## Common Pitfalls

### Pitfall 1: TalkingPointCard not rendering for all modes

**What goes wrong:** Running in `mode=all` returns all four mode results. The render path `item.ticket?.talking_point` fires for each, but if the scenario data doesn't propagate the `talking_point` through the API for a given mode, the card is silently absent.

**Why it happens:** The `talking_point` field lives in `SupportTicket` on the backend (schemas.py line 26). The backend must attach it to every `RunOutput.ticket` regardless of mode. Verify this in the API response.

**How to avoid:** After Phase 5 implementation, run the demo with `mode=all` and confirm all four result cards show talking-point cards.

**Warning signs:** Cards appear for mcp and a2a but not for baseline or hybrid.

### Pitfall 2: GlossaryTerm on non-first mentions creates visual noise

**What goes wrong:** If `<GlossaryTerm>` is applied to every occurrence of "MCP" in a page, every instance gets the dotted underline — making the page look noisy.

**Why it happens:** D-05 specifies role-first phrasing only on first mention. Subsequent mentions should use plain text without wrapping.

**How to avoid:** Each page/view should have exactly one `<GlossaryTerm term="mcp">Tool Access Protocol (MCP)</GlossaryTerm>` per mode. Later occurrences of just "MCP" remain unwrapped.

**Warning signs:** More than one dotted-underline instance of the same term visible simultaneously on the page.

### Pitfall 3: TraceExplorer runtime prop not threaded through

**What goes wrong:** `TraceExplorer` is used in both `RunWorkspacePage` (inside the result card expansion) and in `CompareTracesPanel` (the side-by-side compare view). If only one call site passes `runtime`, the LLM badge appears inconsistently.

**Why it happens:** Adding a new prop requires updating all call sites.

**How to avoid:** After adding `runtime` to `TraceExplorerProps`, search all usages of `<TraceExplorer` and ensure each one passes the correct `runtime` value.

**Warning signs:** Latency badge appears in Run page but not in Compare page, or vice versa.

### Pitfall 4: Failure summary list renders for non-failure runs

**What goes wrong:** `item.failures` is always an array — for clean runs it's `[]`. If the render check is `item.failures` (truthy check on array), it renders an empty list.

**Why it happens:** Empty arrays are truthy in JavaScript.

**How to avoid:** Gate on `item.failures.length > 0`, not `item.failures`.

**Warning signs:** An empty "Failure Events (0)" section appears on every result card.

### Pitfall 5: MUI Tooltip flash on re-render

**What goes wrong:** If the `title` prop of MUI Tooltip is computed via an inline function on every render, React may cause the tooltip to flash or unmount/remount.

**Why it happens:** Unstable object references in the tooltip `title` prop.

**How to avoid:** The glossary map is a static module-level constant — accessing `glossaryTerms[term]` returns a string, not an object. String props are stable. No memoization needed.

---

## Code Examples

Verified patterns from existing codebase:

### Existing Transport Chip (Role Model for Runtime Chip)

```tsx
// Source: RunWorkspacePage.tsx line 864-868 [VERIFIED: codebase read]
{item.mcp_transport ? (
  <Chip label={item.mcp_transport} size="small" variant="outlined" color="default" />
) : null}
```

### Existing TalkingPointCard Render (Already Works)

```tsx
// Source: RunWorkspacePage.tsx lines 894-916 [VERIFIED: codebase read]
{item.ticket?.talking_point ? (
  <Paper
    elevation={0}
    sx={{
      borderLeft: `4px solid ${getProtocolColor(item.mode)}`,
      bgcolor: "action.hover",
      p: 1.5,
    }}
  >
    <Typography variant="subtitle2" fontWeight="bold">
      {item.ticket.talking_point.headline}
    </Typography>
    <Typography variant="body2" sx={{ mt: 0.5 }}>
      {item.ticket.talking_point.sentence}
    </Typography>
    <Typography variant="body2" sx={{ mt: 0.5, fontStyle: "italic", color: "text.secondary" }}>
      {item.ticket.talking_point.callout}
    </Typography>
  </Paper>
) : null}
```

### Existing Failure Detection

```typescript
// Source: frontend/src/lib/trace/utils.ts lines 22-32 [VERIFIED: codebase read]
export function isTraceFailureEvent(event: TraceEvent): boolean {
  return Boolean(
    event.error ||
    event.event_type === "tool_error" ||
    event.event_type === "a2a_remote_failure" ||
    event.event_type === "triage_warning" ||
    event.message_type === "task_retry" ||
    event.message_type === "task_error" ||
    event.event_type === "a2a_remote_retry",
  );
}
```

### Existing Protocol Color System

```typescript
// Source: frontend/src/lib/trace/eventColors.ts [VERIFIED: codebase read]
export const toneColor = {
  error: "#c62828",   // use for failure event highlight borders
  warning: "#ed6c02", // use for amber runtime badges
  success: "#2e7d32",
  info: "#757575",
} as const;

export const protocolColor: Record<string, string> = {
  mcp: "#1976d2",
  a2a: "#7b1fa2",
  hybrid: "#2e7d32",
  baseline: "#757575",
};
```

### Existing Failure Filter in TraceExplorer

```tsx
// Source: TraceExplorer.tsx lines 139-148 [VERIFIED: codebase read]
// "Only failures and warnings" filter already exists — wire failure count to result card
<MenuItem value="only_failures">Only failures and warnings</MenuItem>
```

---

## Runtime State Inventory

Step 2.5: SKIPPED — this is a greenfield additive phase, not a rename/refactor/migration.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `@mui/material` Tooltip | GlossaryTerm (PRES-02) | Yes | 7.3.1 | — |
| `@mui/material` Chip | Runtime indicator (PRES-03) | Yes | 7.3.1 | — |
| `@mui/material` Alert | LLM banner (PRES-03) | Yes | 7.3.1 | — |
| `motion` (framer-motion) | Optional card animations | Yes | 12.38.0 | Skip animations |
| Node.js / npm | Build | Yes | (project standard) | — |

**No missing dependencies.** All libraries required for Phase 5 are already installed.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Glossary as separate page | Inline Tooltip on hover | Standard UX pattern | Keeps presenter in flow without navigation |
| Protocol names as raw acronyms | Role-first phrasing on first use | D-05/07 decisions | Non-technical audience understands purpose before acronym |
| Failure modes only discoverable by toggle | Failure outcomes visible in trace | Phase 5 goal | Enables walkthrough without code changes |

**Deprecated/outdated:**
- `protocolColor` hardcoded at module level in RunWorkspacePage.tsx — already replaced by `getProtocolColor()` from eventColors.ts (D-15 from Phase 3 context, implemented in Phase 4).

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | GlossaryTerm component uses styled span + MUI Tooltip (not Popover or Modal) | Pattern 1 | Low — MUI Tooltip is the lightest-weight option and confirmed in D-03 |
| A2 | ~15-20 specific glossary terms listed in Code Examples | Glossary Terms Map | Low — Claude's discretion per D-01; list can be trimmed/extended during implementation |
| A3 | Runtime chip uses MUI `color="warning"` for amber (not custom hex) | Pattern 3 | Low — MUI warning color is amber (#ed6c02 equivalent); consistent with toneColor.warning |
| A4 | `item.runtime !== "mock"` is the correct LLM detection check | Pattern 4 | Low — `RunResult.runtime` is a required `string` field; values are "mock" or "llm" per RuntimeMode type |
| A5 | `motion` is optionally used for card/badge animations; skip if complexity outweighs benefit | Standard Stack | Low — motion is already installed; decision at implementation time |

**All core architectural claims are VERIFIED from codebase reads. Assumptions are limited to implementation detail choices within Claude's discretion (per CONTEXT.md).**

---

## Open Questions

1. **Do all four modes receive `talking_point` in the API response?**
   - What we know: scenarios.json has `talking_point` for all 12 scenarios. The `SupportTicket` dataclass has `talking_point: dict | None`. RunWorkspacePage renders it via `item.ticket?.talking_point`.
   - What's unclear: Does the backend attach the scenario's `talking_point` to every RunOutput regardless of mode (baseline, hybrid included)?
   - Recommendation: Implementer should verify by running `mode=all` and checking the API response JSON for all four `results[*].ticket.talking_point` fields before adding any fix.

2. **Where exactly does TraceExplorer get called with run results?**
   - What we know: TraceExplorer exists in RunWorkspacePage (likely nested in an expansion or directly in result cards — not visible in the current RunWorkspacePage.tsx render). It's also used by CompareTracesPanel.
   - What's unclear: The current RunWorkspacePage.tsx doesn't show a `<TraceExplorer>` render — the trace is shown via `ParallelAgentTimeline` only. TraceExplorer may be a click-through that hasn't been wired yet, or it may be in a tab.
   - Recommendation: Implementer should check if TraceExplorer is rendered inline per result or accessed via the Compare page. The runtime prop needs to be added to all call sites.

---

## Security Domain

> `security_enforcement` not set in config.json — treated as enabled. Phase 5 is client-side UI polish only.

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No | Phase is display-only; no auth flows |
| V3 Session Management | No | No session state added |
| V4 Access Control | No | No new data access paths |
| V5 Input Validation | No | Glossary terms are hardcoded; no user input flows into glossary |
| V6 Cryptography | No | No crypto operations |

### Known Threat Patterns

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| XSS via glossary definition rendered as HTML | Tampering | Definitions are plain strings in a static TS map; MUI Tooltip renders as text, not HTML — no sanitization needed |
| Rendering user-supplied `item.failures` strings | Tampering | React escapes string content by default; `item.failures` are server-generated strings, not user input |

**Security assessment:** Phase 5 introduces no new data input paths. All new content (glossary terms, role-first labels, runtime indicators) is static or derived from existing trusted API fields. No additional security controls required.

---

## Sources

### Primary (HIGH confidence)
- Codebase: `RunWorkspacePage.tsx` — verified runtime field access pattern, TalkingPointCard render, existing Chip patterns
- Codebase: `TraceExplorer.tsx` — verified current props interface, failure filter, summary strip structure
- Codebase: `eventColors.ts` — verified toneColor and protocolColor constants
- Codebase: `utils.ts` — verified `isTraceFailureEvent()` signature and all 8 failure event types
- Codebase: `api.ts` — verified `RunResult.runtime: string` (required field, not optional)
- Codebase: `scenarios.json` — verified all 12 scenarios have `talking_point` objects
- Codebase: `schemas.py` — verified `FailureConfig` dataclass with 9 boolean flags
- Codebase: `package.json` — verified installed library versions (MUI 7.3.1, motion 12.38.0)

### Secondary (MEDIUM confidence)
- MUI Tooltip documentation pattern — `title` prop renders as text tooltip on hover; `arrow` prop adds pointer; consistent with D-03 decision [ASSUMED from MUI API knowledge, consistent with MUI 7.x]

### Tertiary (LOW confidence)
- None — all claims verified from codebase or CONTEXT.md locked decisions.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries verified from package.json
- Architecture: HIGH — all component locations verified from codebase reads
- Pitfalls: HIGH — derived from actual code patterns observed in RunWorkspacePage.tsx, TraceExplorer.tsx, utils.ts
- Glossary term list: MEDIUM (Claude's discretion) — reasonable working list, can be adjusted during implementation

**Research date:** 2026-04-27
**Valid until:** 2026-05-27 (stable MUI and React codebase; no fast-moving dependencies)
