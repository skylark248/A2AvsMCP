# Phase 12: Comparison Visualization Upgrades - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-01
**Phase:** 12-comparison-visualization-upgrades
**Areas discussed:** Diff alignment, Diff layout, Sequence rendering, Sequence mount, Divergence visual, Actor lanes, Diff scope

---

## Diff Alignment (VIZ-01)

| Option | Description | Selected |
|--------|-------------|----------|
| By turn_index + event_type | Match events sharing turn_index AND event_type. Cheap, deterministic, leverages Phase 6 schema. | ✓ |
| By semantic key (actor + tool + role) | Match on (actor, tool/role, event_type) ignoring turn_index. More matches, fuzzier. | |
| LCS on event_type stream | Classic diff over event_type sequence. Visually diff-like, ignores semantic signals. | |
| Hybrid: turn_index primary + semantic fallback | turn_index match first, fallback within ±1 turn on (actor, tool). Best fidelity, most code. | |

**User's choice:** Recommended option (turn_index + event_type).
**Notes:** Aligns with Phase 6 schema guarantees; deterministic and cheap.

---

## Diff Layout (VIZ-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Toggle on CompareTracesPanel header | Header gets `Side-by-side | Annotated diff` toggle. Switches in place. No new route. | ✓ |
| Side-by-side with connecting lines | Both columns + connector lines + color marks. Heavier render. | |
| Unified single-column git-style | One column, +/- gutter, role-first labels. Compact, loses dual-column metaphor. | |
| Modal / new route | Diff lives outside CompareTracesPanel. Cleaner separation, extra navigation. | |

**User's choice:** Recommended option (in-place toggle).

---

## Sequence Rendering (VIZ-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Pure SVG hand-rolled | Lifelines + arrows in one SVG. Full control. No new dep. ~200–400 LOC. | ✓ |
| @xyflow/react (in deps) | Reuse node/edge model. Free-form graph fights sequence-diagram constraints. | |
| Add mermaid sequenceDiagram | Declarative + familiar. Click-to-pin needs escape hatches. ~1MB dep. | |
| Add d3 + custom layout | Maximum power. Heavy dep + steep learning curve for one component. | |

**User's choice:** Recommended option (pure SVG).

---

## Sequence Mount (VIZ-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Toggle in TraceExplorer header; pin highlights row | `List | Sequence` toggle. Pin scrolls + highlights matching row when toggled to List. | ✓ |
| Collapsible section above event list | Diagram + list visible together; pin auto-scrolls list. More screen real estate used. | |
| Separate route /trace/:id/sequence | Dedicated page; pin persists via URL hash. Cleanest separation, extra navigation. | |
| Modal overlay | Fullscreen modal. Good for focus, breaks flow. | |

**User's choice:** Recommended option (header toggle + cross-view pin).

---

## Divergence Visual (VIZ-01)

| Option | Description | Selected |
|--------|-------------|----------|
| Background tint + +/- gutter chip | Subtle success/error tint + chip; warning border for matched-divergent. Quiet but legible. | ✓ |
| Strong full-row color fill | Saturated colors. Loudest, can overpower. | |
| Marker column only | Just glyph in gutter. Minimal, easy to miss. | |
| Connector lines + fade unmatched | Lines + 50% opacity. Visual but expensive. | |

**User's choice:** Recommended option (tint + chip).

---

## Actor Lanes (VIZ-02)

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed roles: User / Orchestrator / LLM / Tool / Remote Agent | Five canonical lanes via traceEventActor(). Predictable, role-first labels. | ✓ |
| One lane per distinct actor instance | Each tool/agent gets own lane. Most precise, lanes explode. | |
| Two lanes: Local vs Remote | MCP-side / A2A-side. Loses granularity. | |
| Configurable lane density | Default fixed-roles + user toggle. More code/state. | |

**User's choice:** Recommended option (5 fixed roles).

---

## Diff Scope (VIZ-01)

| Option | Description | Selected |
|--------|-------------|----------|
| All event_types | No pre-filter. Reuses TraceExplorer filters on top. | ✓ |
| Execution-phase only | Drops tool_discovery + meta. Simpler, hides Phase 11 discovery divergence. | |
| User-selectable via existing filters | Diff respects current TraceExplorer filters. Most flexible. | |
| Tool_call + agent_msg only | Cleanest diff. Loses fault/divergence signal. | |

**User's choice:** Recommended option (all event_types).

---

## Claude's Discretion

- Animation timing curves and easing values when motion is permitted.
- Internal data structure for alignment output (e.g., `DiffRow[]` shape).
- Hit-target sizing and z-order for SVG arrow click areas (a11y minimums apply).
- Whether the diff view reuses TraceExplorer's filter chrome at the top.
- Pinned-event state location (component-local vs lifted into TraceExplorer parent).

## Deferred Ideas

- Connector lines between matched events in side-by-side mode.
- Per-instance lifelines in sequence diagram (one lane per tool/agent).
- Sequence diagram on RacePage / ReportDetailPage.
- Diff export (copy as markdown / share URL).
- Sequence diagram applied with TraceExplorer event filters — likely in scope, planner confirms.
