---
phase: 11
plan: 03
subsystem: frontend
tags: [frontend, mui, component, vitest, panel, discovery]
wave: 1
requires:
  - 11-01 (JsonTree extraction at frontend/src/lib/trace/JsonTree.tsx)
provides:
  - DiscoveryPhasePanel component (presentational, MUI Accordion + 2-col Grid)
  - DiscoveryPhasePanelProps interface (mcpEvents, a2aEvents, scenario, defaultExpanded)
  - 5-case vitest suite covering baseline, both placeholders, stale-cache fallback, a2a_remote_discovery skill-chip join
affects:
  - Plan 11-04 (Wave 2) — mount-site wiring on TraceWorkspacePage and CompareTracesPanel will import DiscoveryPhasePanel + DiscoveryPhasePanelProps from this file
tech-stack:
  added: []
  patterns:
    - MUI Grid v2 size syntax (Grid size={{ xs: 12, md: 6 }}) consistent with LearningPage
    - vitest harness wrapping in ThemeProvider+CssBaseline per RunWorkspacePage.test.tsx
    - JsonTree-only canonical import (FIELD_ANNOTATIONS/annotate not consumed)
    - Failure-mode highlight via existing requested_transport vs transport divergence (no new event_type)
key-files:
  created:
    - frontend/src/components/traces/DiscoveryPhasePanel.tsx (292 lines)
    - frontend/src/components/traces/__tests__/DiscoveryPhasePanel.test.tsx (118 lines)
  modified: []
decisions:
  - D-71 placeholder copy verbatim — "Run on {MCP|A2A} to populate" (no inline run button)
  - D-73 caller gates scenario === "tool_discovery"; component is gate-agnostic
  - Open Question #1 RESOLVED — A2A column unions tool_discovery (with remote_agent) AND a2a_remote_discovery, joining by remote_agent === a2a_agent_card.agent_id
  - Open Question #2 — defaultExpanded default = true
metrics:
  duration: 4m
  tasks_completed: 2
  files_changed: 2
  tests_added: 5
  completed: 2026-05-01
requirements: [DISC-02]
---

# Phase 11 Plan 03: DiscoveryPhasePanel Component Summary

**One-liner:** New MUI Accordion panel rendering MCP tool catalog and A2A agent cards side-by-side with stale-cache transport-fallback highlights, paired with a 5-case vitest suite verifying placeholder copy and the a2a_remote_discovery skill-chip join.

## What Shipped

### Component (`frontend/src/components/traces/DiscoveryPhasePanel.tsx`)

- Presentational React component with `DiscoveryPhasePanelProps` interface (`mcpEvents`, `a2aEvents`, `scenario`, `defaultExpanded`).
- MUI `Accordion` (defaultExpanded=true) with summary chips: `${N} tools discovered` (MCP color) and `${N} agents found` (A2A color).
- `<Grid container spacing={3}>` two columns (xs:12, md:6) — MCP left, A2A right.
- Per-column header: 4px left-border in `protocolColor.{mcp|a2a}` + `Typography variant="overline"` with letterSpacing 0.14em.
- MCP column: `Card variant="outlined"` per tool entry; renders name, optional description, `+{rel}ms` timestamp; nested compact `Accordion` for `inputSchema` rendering JSON inside a `#1a2332` monospace surface via `JsonTree`. Handles both string-form tool names and object-form descriptors.
- A2A column: joins `tool_discovery` events (with `remote_agent`) to `a2a_remote_discovery` events (with `a2a_agent_card.skills`) by matching `remote_agent === a2a_agent_card.agent_id`. Renders agent name, skill chips (size=small, outlined), and per-agent tool list.
- Empty placeholders (D-71 verbatim): "Run on MCP to populate" / "Run on A2A to populate" centered Boxes.
- Failure-row highlight: `requested_transport && requested_transport !== transport` triggers a 2px left-border in `toneColor.warning` and a `WarningAmberRoundedIcon` with `aria-label="Stale capability cache"` inside a Tooltip with the long-form copy. Reuses existing wire signal (no new event_type) per RESEARCH anti-pattern #2.
- Threat mitigation T-11-03-01: zero `dangerouslySetInnerHTML`; all user-shaped strings flow through JSX text nodes (React escaping).
- Honors RESEARCH Pitfall #1: never references `event.phase`; consumes pre-filtered arrays from caller.

### Tests (`frontend/src/components/traces/__tests__/DiscoveryPhasePanel.test.tsx`)

5 cases, all wrapped in `<ThemeProvider theme={appTheme}><CssBaseline />…</ThemeProvider>`:

1. **Baseline** — panel chrome + both column headers render; A2A placeholder visible when MCP-only.
2. **MCP-only placeholder** — A2A copy renders; MCP copy absent.
3. **A2A-only placeholder** — MCP copy renders; A2A copy absent.
4. **Stale-cache fallback** — fixture with `requested_transport: "stdio"` and `transport: "in_process"` renders the warning icon (asserted via `getAllByLabelText(/Stale capability cache/i)`).
5. **Skill-chip join (Open Question #1)** — fixture with both a `tool_discovery` event (`remote_agent: "documentation"`) and an `a2a_remote_discovery` event (`a2a_agent_card.skills: ["lookup_warranty", "check_order"]`) renders both skill labels.

## Verification

| Gate | Result |
|------|--------|
| `cd frontend && npx tsc --noEmit -p tsconfig.json` | exit 0 — zero TS errors |
| `cd frontend && npm test -- --run DiscoveryPhasePanel` | 5/5 cases pass |
| `cd frontend && npm test -- --run` (full suite) | 291/291 pass (286 baseline + 5 new) |
| Task 1 grep gates (18 acceptance criteria) | ALL PASS |
| Task 2 grep gates (8 acceptance criteria) | ALL PASS |
| `grep -c "dangerouslySetInnerHTML" DiscoveryPhasePanel.tsx` | 0 (T-11-03-01) |
| `grep -c "event.phase" DiscoveryPhasePanel.tsx` | 0 (Pitfall #1) |

## Commits

| Task | Type | Hash | Description |
|------|------|------|-------------|
| 1 | feat | a84c511 | DiscoveryPhasePanel component (component layer of DISC-02) |
| 2 | test | b84acd3 | 5-case vitest suite (baseline + placeholders + fallback + skill-chip join) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Test Bug] Stale-cache assertion needed `getAllByLabelText` not `getByLabelText`**

- **Found during:** Task 2 verification (initial test run)
- **Issue:** Test 4 used `screen.getByLabelText(/Stale capability cache/i)` but the fixture event has `tools: ["get_order_history", "get_warranty"]` — two tools means the component renders TWO cards, each with its own warning icon (correct behavior per the plan's contract). Testing Library threw "Found multiple elements" rather than passing.
- **Fix:** Changed assertion to `getAllByLabelText(...)` and verified `length >= 1`. The component behavior is correct (warning highlight applied per-card on the affected event); only the test query needed adjustment to match the multi-card rendering.
- **Files modified:** `frontend/src/components/traces/__tests__/DiscoveryPhasePanel.test.tsx` (single edit before commit b84acd3).
- **Commit:** b84acd3 (fix landed in same Task 2 commit; not a separate commit because the test file had not been committed yet at the moment of the fix).

No other deviations — plan executed essentially as written.

## Plan 11-04 Handoff Contract

Plan 11-04 (mount-site wiring) imports:

```typescript
import { DiscoveryPhasePanel } from "../../components/traces/DiscoveryPhasePanel";
import type { DiscoveryPhasePanelProps } from "../../components/traces/DiscoveryPhasePanel";
```

Caller responsibilities (filter at mount, NOT inside the component — Pitfall #1):

- `mcpEvents` = `events.filter((e) => e.event_type === "tool_discovery" && !e.remote_agent)`
- `a2aEvents` = `events.filter((e) => (e.event_type === "tool_discovery" && Boolean(e.remote_agent)) || e.event_type === "a2a_remote_discovery")`
- `scenario` — caller pre-gates on D-73 for TraceWorkspacePage; CompareTracesPanel passes `"tool_discovery"`.

The component partitions `a2aEvents` internally and joins by `remote_agent === a2a_agent_card.agent_id`.

## Decisions Made

- **defaultExpanded default = true** — implemented as `defaultExpanded ?? true` so callers can override for collapsed-default mounts (Plan 11-04 may pass `defaultExpanded={false}` if Plan 11-04 reviewers prefer collapsed-by-default in the compare view; current default is open).
- **Tool descriptor coercion** — accepts both string-form tool names and `{name, description, inputSchema}` objects in `event.tools[]`, since the wire format from MCP `tool_discovery` may be either depending on the server.
- **Skill chip key** — `<Chip key={skill}>` since the agent skill list is a `string[]` and labels are unique within an agent's card.

## Threat Flags

None — no new network endpoints, auth paths, file access, or schema changes at trust boundaries. T-11-03-01 (XSS through tool/skill text) mitigated by JSX text escaping; verified by `dangerouslySetInnerHTML` grep gate returning 0.

## Self-Check: PASSED

- `frontend/src/components/traces/DiscoveryPhasePanel.tsx` — FOUND
- `frontend/src/components/traces/__tests__/DiscoveryPhasePanel.test.tsx` — FOUND
- Commit a84c511 — FOUND in `git log --all --oneline`
- Commit b84acd3 — FOUND in `git log --all --oneline`
- Full vitest suite — 291/291 GREEN
- TypeScript compile — clean (zero errors)
