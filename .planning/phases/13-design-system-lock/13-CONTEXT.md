# Phase 13: Design System Lock - Context

**Gathered:** 2026-05-01
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce `.planning/DESIGN.md` — a written design reference formalizing the race-demo design tokens and rules that were relitigated during Phases 8–12. The deliverable is a reference document, not new UI code.

**Process:** Run `/design-consultation` (skill) first, scoped to the 5 mandated items from ROADMAP SC. Then the execution agent writes DESIGN.md from the consultation output + code archaeology.

**What is NOT in scope:** New UI implementation, changes to theme.ts or eventColors.ts, documenting non-race-demo tokens (protocolColor, toneColor, typography scale, borderRadius), governance procedures.

</domain>

<decisions>
## Implementation Decisions

### DESIGN.md Content Scope
- **D-86:** Cover exactly the 5 ROADMAP-mandated items — failureTagColor map, methodology-as-flat rule, secondary.main replay-pill semantic, role-first first-mention contract, primary/secondary palette intent. No full token inventory.
- **D-87:** Include explicit "do NOT" anti-patterns alongside each positive rule. E.g., "do not apply MUI Card elevation to methodology sections," "do not use secondary.main outside replay-pill and role-first overlines." These codify the relitigated decisions.
- **D-88:** No governance/change-protocol section. DESIGN.md is a reference document only.
- **D-89:** No self-check Q&A section. The ROADMAP success criterion ("contributor can answer 3 questions without reading source") is satisfied by clear structure + prose, not an explicit quiz.

### Role-first Contract Boundary
- **D-90:** Document the role-first contract as scoped to **Run + Compare + Race pages only** (matches ROADMAP SC exactly). Trends + Learn pages apply the same pattern incidentally — do not expand scope.
- **D-91:** Document the visual rule only: `variant="overline"` + `color="secondary.main"` + `letterSpacing: "0.16em"` for role labels on first mention. Do NOT document the `roleFirstLabel()` implementation detail — that is code, not design.

### Token Documentation Format
- **D-92:** Each of the 5 mandated items: **intent statement + source file reference + short inline code snippet** showing actual usage. Example: `bgcolor: "secondary.main"` from ReplayPill.tsx.
- **D-93:** failureTagColor map: present as a **markdown table** with columns `Tag | bg | text | Icon | Label | Intent`. Single source of truth pointer: `frontend/src/lib/trace/eventColors.ts`.

### Process and Output
- **D-94:** Run `/design-consultation` skill **first** in execution, scoped to the 5 mandated items as the consultation brief. Write DESIGN.md from the consultation output.
- **D-95:** DESIGN.md lives at `.planning/DESIGN.md` (matches ROADMAP spec). Not in frontend/.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Design Token Sources (read these to extract values for DESIGN.md)
- `frontend/src/lib/trace/eventColors.ts` — `failureTagColor` canonical source (5 entries: recovered, gave_up, kept_going_without_noticing, kept_going_to_failure, indeterminate); single source of truth per UIRACE-04
- `frontend/src/app/theme.ts` — MUI theme: `primary.main = #17475f`, `secondary.main = #b85c38`, `background.default = #f3efe7`, `background.paper = #fffdfa`

### Pattern Implementation Sources (read for code snippets in DESIGN.md)
- `frontend/src/features/race/components/MethodologySection.tsx` — methodology-as-flat pattern: `Box component="aside"` + `bgcolor: "background.default"` + no elevation (UIRACE-03)
- `frontend/src/features/race/components/ReplayPill.tsx` — secondary.main replay-pill implementation: `bgcolor: "secondary.main"` on Chip (D-49)
- `frontend/src/features/run-workspace/RunWorkspacePage.tsx` — role-first overline pattern: `variant="overline"` + `color="secondary.main"` + `letterSpacing: "0.16em"`

### Planning References
- `.planning/ROADMAP.md` Phase 13 section — success criteria spec (the 5 mandated items + 2 SC)
- `.planning/REQUIREMENTS.md` DSGN-01 — requirement definition

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `failureTagColor` in `eventColors.ts`: already has all 5 entries with bg/text/Icon/label — copy values directly into the markdown table; no guessing required.
- `appTheme` in `theme.ts`: palette values are authoritative — extract `primary.main`, `secondary.main`, `background.default`, `background.paper` directly.

### Established Patterns
- **Methodology-as-flat:** `Box component="aside"` with `bgcolor: "background.default"` and `py: 6`. No `Paper`, no `Card`, no `elevation` prop. This is the pattern DESIGN.md must formalize.
- **secondary.main dual-use:** same token (#b85c38) used for both replay-pill background AND role-first overline labels — the design intent is "warm accent for non-primary emphasis." DESIGN.md must make this dual-use explicit so contributors don't add a third use.
- **UIRACE-04 accessibility constraint:** color must never be the sole channel in failureTagColor — each entry pairs color with an Icon. This is a "do NOT" rule to capture in DESIGN.md.

### Integration Points
- DESIGN.md is read by humans, not imported by code. No TypeScript integration needed.
- `/design-consultation` skill is the first execution step — read its output before authoring DESIGN.md prose.

</code_context>

<specifics>
## Specific Ideas

- The failureTagColor "do NOT" rule to capture: "Do not add a 6th failure tag without pairing it with a unique Icon — color alone violates UIRACE-04."
- The methodology anti-pattern to capture: "Do not wrap the methodology section in a MUI Card or Paper — it must remain a flat Box aside with `bgcolor: background.default`."
- secondary.main boundary to capture: "Do not use secondary.main (#b85c38) for any purpose other than replay-pill background and role-first overline labels. For other accent needs, use primary.main or a toneColor."

</specifics>

<deferred>
## Deferred Ideas

- Full token inventory (protocolColor, toneColor, typography scale, borderRadius: 18, background.*) — out of scope for Phase 13; could be a future DESIGN.md expansion if contributors request it.
- Governance / change-protocol section — deferred; trust contributors to update DESIGN.md when they update source files.

</deferred>

---

*Phase: 13-design-system-lock*
*Context gathered: 2026-05-01*
