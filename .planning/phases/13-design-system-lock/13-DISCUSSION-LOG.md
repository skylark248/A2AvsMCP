# Phase 13: Design System Lock - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-05-01
**Phase:** 13-design-system-lock
**Areas discussed:** DESIGN.md scope, Role-first boundary, Token doc format, Process

---

## DESIGN.md Scope

### Q1 — Content scope

| Option | Description | Selected |
|--------|-------------|----------|
| 5 mandated items only | Just the ROADMAP SC items — failureTagColor + 4 rules | ✓ |
| Full token inventory | Everything in theme.ts + eventColors.ts (palette, typography, shape, toneColor, protocolColor) | |

**User's choice:** 5 mandated items only
**Notes:** DESIGN.md is specifically about race-demo rules that kept getting relitigated. Full inventory would dilute focus.

---

### Q2 — Anti-patterns

| Option | Description | Selected |
|--------|-------------|----------|
| Yes — include anti-patterns | "Do NOT" rules alongside each positive rule | ✓ |
| No — positive rules only | Trust contributors to infer boundaries | |

**User's choice:** Yes — include anti-patterns
**Notes:** Codifies the relitigated decisions. More actionable than positive rules alone.

---

### Q3 — Governance section

| Option | Description | Selected |
|--------|-------------|----------|
| No governance section — reference only | Trust contributors to update DESIGN.md when they update source files | ✓ |
| Include a brief change protocol | One paragraph explaining how to keep DESIGN.md in sync | |

**User's choice:** No governance section
**Notes:** Governance adds weight without proportionate value for this document.

---

### Q4 — Self-check section

| Option | Description | Selected |
|--------|-------------|----------|
| Implied by structure | Good headers + prose satisfy the SC | ✓ |
| Include a Q&A self-check | 3 explicit Q&A pairs at the bottom | |

**User's choice:** Implied by structure
**Notes:** Explicit Q&A section felt like a quiz and adds noise.

---

## Role-first Boundary

### Q1 — Scope of contract

| Option | Description | Selected |
|--------|-------------|----------|
| Narrow: Run + Compare + Race only | Match ROADMAP exactly | ✓ |
| Broad: all pages with secondary.main overlines | Document pattern as it exists across 5+ pages | |
| Narrow contract, note broader presence | Define for mandated pages + add a note about Trends/Learn | |

**User's choice:** Narrow: Run + Compare + Race only
**Notes:** Keep scope tight. Trends/Learn following the pattern is incidental.

---

### Q2 — Visual vs implementation

| Option | Description | Selected |
|--------|-------------|----------|
| Visual rule only — secondary.main overline pattern | Design reference, not API doc | ✓ |
| Both — visual rule + implementation pointers | Pointer to roleFirstLabel() helps new contributors find code | |

**User's choice:** Visual rule only
**Notes:** DESIGN.md is a design reference. The roleFirstLabel() function is implementation detail that belongs in code comments.

---

## Token Doc Format

### Q1 — Detail level per item

| Option | Description | Selected |
|--------|-------------|----------|
| Intent + source file reference | Hex + intent + file pointer, no code snippets | |
| Intent + code snippet | Same plus short inline code snippet showing actual usage | ✓ |
| Intent only | Just the design rule in prose, no hex or file refs | |

**User's choice:** Intent + code snippet
**Notes:** Makes it immediately copy-paste usable for contributors adding a new surface.

---

### Q2 — failureTagColor presentation

| Option | Description | Selected |
|--------|-------------|----------|
| Markdown table | Tag / bg / text / Icon / Label — one row per failure state | ✓ |
| Prose list per entry | Written description for each of 5 entries | |
| Code block — reproduce object literal | Copy the const verbatim | |

**User's choice:** Markdown table
**Notes:** Scannable, copy-paste friendly. 5 entries is the right size for a table.

---

## Process

### Q1 — How DESIGN.md gets written

| Option | Description | Selected |
|--------|-------------|----------|
| Code archaeology — write DESIGN.md directly | Agent reads source files and produces DESIGN.md | |
| Run /design-consultation first, then write DESIGN.md | Two-step: skill invocation → DESIGN.md authoring | ✓ |
| Skip /design-consultation — CONTEXT.md IS the consultation | This discussion is the consultation | |

**User's choice:** Run /design-consultation first, then write DESIGN.md
**Notes:** User wants the design-consultation skill to run as a proper first step before DESIGN.md authoring.

---

### Q2 — Consultation scope

| Option | Description | Selected |
|--------|-------------|----------|
| 5 mandated items only | Feed the consultation the ROADMAP SC brief | ✓ |
| Full race demo visual language | Let consultation roam holistically | |

**User's choice:** 5 mandated items only
**Notes:** Matches scope decision from Area 1.

---

### Q3 — Output location

| Option | Description | Selected |
|--------|-------------|----------|
| .planning/DESIGN.md | Matches ROADMAP spec | ✓ |
| frontend/DESIGN.md | Closer to code it governs | |

**User's choice:** .planning/DESIGN.md
**Notes:** Planning docs live in .planning/ alongside PROJECT.md and REQUIREMENTS.md.

---

## Claude's Discretion

None — user made explicit choices on all questions.

## Deferred Ideas

- Full token inventory (protocolColor, toneColor, typography, borderRadius) — noted for future DESIGN.md expansion if contributors request it.
- Governance / change-protocol section — deferred; not valuable enough for Phase 13 scope.
