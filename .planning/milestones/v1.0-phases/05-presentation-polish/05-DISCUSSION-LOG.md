# Phase 5: Presentation Polish - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-27
**Phase:** 05-presentation-polish
**Areas discussed:** Glossary popovers, Role-first phrasing, Real-LLM visibility

---

## Glossary Popovers

### Data source

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcoded TS map | A glossaryTerms.ts file with ~15-20 entries. Simple, deterministic, presenter-controlled. | ✓ |
| JSON data file | A glossary.json loaded at startup. Easier for non-devs to edit. | |
| You decide | Claude picks the simplest approach. | |

**User's choice:** Hardcoded TS map
**Notes:** None

### Term detection

| Option | Description | Selected |
|--------|-------------|----------|
| Manual wrapping | Wrap protocol terms with a GlossaryTerm component at known UI locations. Predictable, no regex surprises. | ✓ |
| Auto-detect in text | A utility that scans rendered text for glossary keys and auto-wraps them. | |
| You decide | Claude picks based on how many locations need glossary terms. | |

**User's choice:** Manual wrapping
**Notes:** None

### Popover component

| Option | Description | Selected |
|--------|-------------|----------|
| MUI Tooltip | Appears on hover with one-sentence definition. Lightweight, already in MUI. | ✓ |
| MUI Popover | Click-to-open card with more room for content. | |
| You decide | Claude picks the lightest approach. | |

**User's choice:** MUI Tooltip
**Notes:** None

### Visual indicator

| Option | Description | Selected |
|--------|-------------|----------|
| Dotted underline | Subtle dashed border-bottom on glossary terms. Universal hover affordance. | ✓ |
| No indicator | Terms look like normal text. Tooltip appears as surprise on hover. | |
| You decide | Claude picks based on demo readability. | |

**User's choice:** Dotted underline
**Notes:** None

---

## Role-First Phrasing

### Application strategy

| Option | Description | Selected |
|--------|-------------|----------|
| First mention per page | First occurrence uses full role-first form. Subsequent mentions use abbreviation. | ✓ |
| Always use full form | Every label always says the full form. Maximum clarity but wordy. | |
| Header + glossary only | Role-first phrasing only in page headers and glossary tooltip. | |

**User's choice:** First mention per page
**Notes:** None

### UI surfaces

| Option | Description | Selected |
|--------|-------------|----------|
| Run page + Compare page | The two pages a presenter walks through during a demo. | ✓ |
| All pages with protocol labels | Run, Compare, Traces, Reports, Learning. More thorough. | |
| You decide | Claude picks the pages with highest demo-day visibility. | |

**User's choice:** Run page + Compare page
**Notes:** None

### All four modes

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, all four modes | Baseline, Hybrid, MCP, A2A all get role-first phrasing. | ✓ |
| MCP and A2A only | Only the two protocol modes get role-first phrasing. | |
| You decide | Claude decides based on layout. | |

**User's choice:** Yes, all four modes
**Notes:** Baseline -> "Direct Agent (Baseline)", Hybrid -> "Combined Protocol (Hybrid)"

---

## Real-LLM Visibility

### Toggle prominence

| Option | Description | Selected |
|--------|-------------|----------|
| Top toolbar chip | Persistent Chip in run workspace header showing runtime. Click not needed. | ✓ |
| Inline switch in settings panel | Switch component in existing settings area. | |
| You decide | Claude picks the most demo-friendly placement. | |

**User's choice:** Top toolbar chip (visual indicator only, not functional toggle)
**Notes:** Runtime determined by OPENAI_API_KEY env var

### Latency badge

| Option | Description | Selected |
|--------|-------------|----------|
| Static warning badge | Chip: "Expect 2-5s per LLM call" with amber color. No live measurement. | ✓ |
| Live latency indicator | Show actual measured latency per LLM call. Requires backend changes. | |
| Both static + live | Static badge plus actual latency per event. | |

**User's choice:** Static warning badge
**Notes:** None

### Trace indicator

| Option | Description | Selected |
|--------|-------------|----------|
| Banner above trace | Colored alert: "This run used OpenAI GPT-4o-mini...". Only for LLM runs. | ✓ |
| Per-event LLM icon | Small icon on each trace event involving LLM call. | |
| You decide | Claude picks based on layout constraints. | |

**User's choice:** Banner above trace
**Notes:** None

### Toggle functionality

| Option | Description | Selected |
|--------|-------------|----------|
| Visual indicator only | Shows which runtime is active based on env var. No toggle action. | ✓ |
| Functional toggle | Clicking switches between mock and OpenAI runtime via API call. | |

**User's choice:** Visual indicator only
**Notes:** Simpler, no backend API needed

---

## Claude's Discretion

- Exact glossary term list and definitions
- GlossaryTerm component implementation details
- Which specific locations get GlossaryTerm wrappers
- Role-first phrasing implementation (utility function vs inline)
- Talking-point card content for remaining scenarios
- Runtime indicator Chip exact styling
- Failure event highlight styling in trace explorer
- Whether to use motion (framer-motion) for subtle animations

## Deferred Ideas

- Failure-mode walkthrough (PRES-04) toggle redesign not discussed — existing UI works, focus is on trace visibility of failure outcomes
