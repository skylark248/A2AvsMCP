# Phase 8 Discussion Log — Race Page UI & Visual Contract

**Date:** 2026-04-29
**Mode:** discuss (default), 4 areas selected by user

This log is a human-reference audit trail. Downstream agents read `08-CONTEXT.md`, not this file.

---

## Areas Selected

User selected (multi-select): WS state architecture, Heatmap rendering, Replay mode UX, First-mention popover semantics.

(Mobile fallback `?mode=summary` and Page state machine surface were offered but deprioritized — both are downstream-of-research or cross-phase coordination items.)

---

## Area 1: WS State Architecture

**Q1.** Where does live race websocket state live?

Options presented:
- Custom hook + useReducer (Recommended)
- React Context + reducer
- Zustand store
- Redux Toolkit slice

**User selected:** Custom hook + useReducer → **D-44**.

**Q2.** On ws reconnect, how does client resume?

Options presented:
- Per-lane last turn_index sent on reconnect (Recommended)
- Single global last turn_index
- Replay full trace from disk

**User selected:** Per-lane last turn_index → **D-45**.

---

## Area 2: Heatmap Rendering

**Q1.** How is the hardness-vs-failure heatmap rendered?

Options presented:
- CSS Grid + DOM cells (Recommended)
- SVG (recharts custom shape)
- Canvas
- Hybrid SVG + DOM legend

**User selected:** CSS Grid + DOM cells → **D-46**.

**Q2.** How does the heatmap-empty state render?

Options presented:
- Same grid scaffold, neutral cell + hint copy (Recommended)
- Hide grid, show empty illustration
- Skeleton placeholder

**User selected:** Same grid scaffold + hint copy → **D-47**.

---

## Area 3: Replay Mode UX

**Q1.** How does a viewer reach replay mode?

Options presented:
- Separate route /race/<run_id> (Recommended)
- Query param /race?run_id=X
- Toggle button on done-state, no URL change

**User selected:** Separate route /race/<run_id> → **D-48**.

**Q2.** How is replay state visually distinguished from live?

Options presented:
- Right-aligned pill in status strip + scrubber (Recommended)
- Banner-level callout
- Watermark only

**User selected:** Status-strip pill + scrubber → **D-49**.

---

## Area 4: First-Mention Popover Semantics

**Q1.** First-mention popover trigger + component?

Options presented:
- Click → MUI Popover; Tooltip on hover thereafter (Recommended)
- Hover-only Tooltip (extend existing)
- Inline expandable definition

**User selected:** Click → MUI Popover; Tooltip thereafter → **D-50**.

**Q2.** How is "first mention" tracked?

Options presented:
- Route-scoped React Context (Recommended)
- sessionStorage
- localStorage

**User selected:** Route-scoped React Context → **D-51**.

---

## Decisions Summary

| ID | Area | Decision |
|----|------|----------|
| D-44 | WS state | useRaceStream() custom hook + useReducer over event stream |
| D-45 | WS reconnect | Per-lane last turn_index cursor on ws URL |
| D-46 | Heatmap render | CSS Grid + DOM cells |
| D-47 | Heatmap empty | Preserve grid scaffold, neutral cells + hint copy |
| D-48 | Replay route | Separate /race/<run_id> route |
| D-49 | Replay UX | Status-strip pill + scrubber |
| D-50 | Popover | Click→MUI Popover (first), Tooltip (subsequent) |
| D-51 | First-mention tracking | Route-scoped React Context, no persistence |

---

## Deferred Ideas (cross-phase)

- OG image rendering → Phase 10
- Heatmap data backend → Phase 9 (HEAT-01/02)
- Multi-task K=3 calibration data → Phase 9 (HEAT-04)
- Replay backend trace fetch endpoint → Phase 9 (HEAT-03)

---

## Scope Creep Redirected

None during this discussion — all 4 areas stayed within Phase 8 boundary.

---

## Claude's Discretion (deferred to research / planning)

- Page-state machine surface (explicit FSM enum vs derived state)
- Mobile fallback `?mode=summary` rendering approach
- Scrubber visual design (MUI Slider variant)
- MUI Popover anchor positioning per term
