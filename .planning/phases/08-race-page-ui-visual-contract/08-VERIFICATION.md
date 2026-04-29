---
phase: 08-race-page-ui-visual-contract
verified: 2026-04-29T17:33:00Z
status: passed
verdict: PASS
score: 7/7 must-haves verified (UIRACE-01..UIRACE-07) + 8/8 design decisions (D-44..D-51)
re_verification:
  previous_status: none
  previous_score: n/a
test_run:
  total: 267
  passed: 267
  files: 27
  duration_s: 14.28
build:
  typecheck: clean (tsc --noEmit exit 0)
  vite_build: clean (built in 2.94s)
deferred_to_later_phases:
  - item: "Heatmap data backend (cells populated)"
    addressed_in: "Phase 9 (HEAT-01/HEAT-02)"
    evidence: "RacePage.tsx:94 — `heatmap_has_data = false` constant; HeatmapScaffold renders empty overlay scaffold (D-47 contract)"
  - item: "Replay backend trace endpoint /api/race/runs/:run_id/trace"
    addressed_in: "Phase 9 (HEAT-03)"
    evidence: "useRaceReplay.ts:5 — `Phase 9 HEAT-03 ships the backend; Phase 8 ships the typed call signature only`"
  - item: "OG image / mobile <480 cropped anchor PNG"
    addressed_in: "Phase 10 (OG Image & Sharing)"
    evidence: "RacePage.tsx:78 — `Phase 8 emits a placeholder; Phase 10 OG Image ships the cropped anchor PNG`"
  - item: "Scrubber turn-index navigation (actual data binding)"
    addressed_in: "Phase 9 (HEAT-03 replay path)"
    evidence: "RacePage.tsx:132-135 — onScrub stub; component is rendered + announces correctly"
---

# Phase 8: Race Page UI & Visual Contract — Verification Report

**Phase Goal:** Deliver the three-lane race page that renders the locked information hierarchy, the full set of 12 page states, and the visual / responsive / accessibility contracts.

**Verified:** 2026-04-29 17:33 IST
**Status:** PASS
**Verdict:** PASS (clean)
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths (UIRACE-01..UIRACE-07 + D-44..D-51)

| #  | Truth                                                                                                  | Status     | Evidence                                                                                                                                                                                                                                                                                                                                                                                              |
| -- | ------------------------------------------------------------------------------------------------------ | ---------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1  | UIRACE-01 — Locked information hierarchy in `RacePage.tsx`                                              | VERIFIED  | `RacePage.tsx:121-178` — RaceStatusStrip → optional ReplayScrubber (replay only) → Container `maxWidth: 1200` → page title → 3-lane row (`race-lane-row` flexbox) → CharacteristicFailureBanner → MethodologySection → HeatmapScaffold. Order matches UI-SPEC lines 188-201 verbatim.                                                                                                                  |
| 2  | UIRACE-02 — All 12 PageState values render correctly + WS reconnect resumes per-lane `last_turn_index`  | VERIFIED  | `pageState.ts:32-76` covers each branch (replay, ws-disconnected, ws-reconnecting, lane-failed, indeterminate, heatmap-empty, sparse-heatmap, done, countdown, pre-race, live-n5, live-n1). `__fixtures__/raceStateFixtures.ts:28-144` provides one fixture per state. `__fixtures__/fixtures.test.ts` round-trip invariant for all 12 — passes. `useRaceStream.ts:21-27` per-lane cursor on WS URL.   |
| 3  | UIRACE-03 — Border-radius scale: lane=18 (theme), badge=4, pills=999, banner=0, heatmap cells=0         | VERIFIED  | `FailureStateBadge.tsx:24` `borderRadius: "4px"`; `ReplayPill.tsx:21` `borderRadius: "999px"`; `CharacteristicFailureBanner.tsx:39` `borderRadius: 0`; `HeatmapScaffold.tsx:123` `borderRadius: 0`; lane card uses theme default 18 (RaceLaneCard.tsx — no override).                                                                                                                                  |
| 4  | UIRACE-04 — `failureTagColor` 5-entry map; color never sole channel                                     | VERIFIED  | `eventColors.ts:44-60` — 5 entries (recovered, gave_up, kept_going_without_noticing, kept_going_to_failure, indeterminate) each carrying `bg` + `text` + `Icon` + `label`. Consumed by both `FailureStateBadge.tsx:13-29` (icon + label + color) AND `HeatmapScaffold.tsx:108-163` (4-channel: bg + Icon + recoveryFraction text + visuallyHidden `cfg.label`).                                          |
| 5  | UIRACE-05 — Mobile (<480) emits `data-testid="race-mobile-summary-placeholder"`                         | VERIFIED  | `RacePage.tsx:79-85` — when `useMediaQuery("(max-width:479px)")` returns true and no `__testState`, returns `<Box data-testid="race-mobile-summary-placeholder">`. `RacePage.responsive.test.tsx:50-95` exercises 4 breakpoints (1280/1024/600 → lane row; 400 → placeholder). Tests pass.                                                                                                              |
| 6  | UIRACE-06 — A11y contract (Tab order, aria-live, prefers-reduced-motion, prefers-contrast, focus-visible) | VERIFIED  | `RaceLaneCard.tsx:82` aria-live="polite" on event feed; `RaceStatusStrip.tsx:76` aria-live="polite"; `ReplayScrubber.tsx:90` aria-live="polite" with 200ms throttle (D-49); `RaceLaneCard.tsx:42-54` prefers-contrast widens stripe 4→6px; `ReplayScrubber.tsx:79-84` prefers-reduced-motion 0ms; `HeatmapScaffold.tsx:131-138` focus-visible 3px (4px high-contrast). `RacePage.a11y.test.tsx` 6 tests pass. |
| 7  | UIRACE-07 — 8 race glossary terms + first-mention popover                                               | VERIFIED  | `glossaryTerms.ts:40-47` — 8 terms verbatim (ttff, recovery_rate, hardness_profile, recovered, gave_up, kept_going_without_noticing, kept_going_to_failure, indeterminate). `GlossaryTerm.tsx:23-67` first-mention branch with click+Popover+"Got it" dismiss. `MethodologySection.tsx:41-43` wraps ttff/recovery_rate/hardness_profile in `<GlossaryTerm>`. `RaceLaneCard.tsx:63-65` wraps lane name. |
| 8  | D-44 — `useRaceStream` owns WS + `useReducer`; no global store                                          | VERIFIED  | `useRaceStream.ts:36-76` — calls `useReducer(raceReducer, initialRaceState)`; opens native WebSocket inside `useEffect`. No store/provider/context for WS state. `RacePage.tsx` consumes hook directly.                                                                                                                                                                                                |
| 9  | D-45 — WS reconnect resumes per-lane `last_turn_index` via URL query params                              | VERIFIED  | `useRaceStream.ts:21-27` `buildWsUrl(state)` emits `?pure_mcp=N&pure_a2a=N&hybrid=N` with N = `state.lanes[lane].last_turn_index`. URL constructed inside the effect; closure captures `stateRef.current` at connect time.                                                                                                                                                                              |
| 10 | D-46 — `failureTagColor` is single source of truth, consumed by both badge + heatmap                    | VERIFIED  | Single `export const failureTagColor` in `eventColors.ts:54`. Imported by `FailureStateBadge.tsx:2` and `HeatmapScaffold.tsx:19`. No duplicate map definitions found.                                                                                                                                                                                                                                  |
| 11 | D-47 — heatmap-empty preserves grid scaffold (does NOT unmount)                                         | VERIFIED  | `HeatmapScaffold.tsx:73-170` always mounts the `<Box role="grid">` scaffold; `isEmpty` flag (lines 66-70) only conditionally adds an absolutely-positioned overlay (lines 172-195) on top. Grid dimensions stay stable.                                                                                                                                                                                |
| 12 | D-48 — `/race` vs `/race/:run_id` flips data source (useRaceStream vs useRaceReplay)                    | VERIFIED  | `routes.tsx:114-129` — both routes registered, both render `<FirstMentionProvider><RacePage/></FirstMentionProvider>`. `RacePage.tsx:49-65` uses `useParams()` to detect `run_id`, then conditionally calls `useRaceStream(!isMobile && !isReplay)` vs `useRaceReplay(...)`.                                                                                                                          |
| 13 | D-49 — ReplayPill in StatusStrip on replay; aria-live throttled scrubber                                 | VERIFIED  | `RaceStatusStrip.tsx:81` renders `<ReplayPill runId={runId}/>` only when `runId` present; `ReplayPill.tsx:14-29` uses 999px radius, `secondary.main` (#b85c38), 14px/700/uppercase per UI-SPEC line 69. `ReplayScrubber.tsx:12-95` throttles aria-live to 200ms during drag, full announce on `onChangeCommitted`.                                                                                       |
| 14 | D-50 — First-mention click→Popover with "Got it"; subsequent mentions = Tooltip                          | VERIFIED  | `GlossaryTerm.tsx:23-67` — `isFirstMention` branch returns `<Popover>` with click handler + Enter/Space keyboard handler + "Got it" Button (line 60); `markSeen(term)` called on dismiss; subsequent mentions fall through to `<Tooltip>` branch (lines 70-83).                                                                                                                                       |
| 15 | D-51 — FirstMentionProvider Set resets on route exit; no sessionStorage/localStorage                     | VERIFIED  | `FirstMentionProvider.tsx:12-13` — `useState<Set<string>>(() => new Set())` (re-initializes each mount; route exit unmounts provider per `routes.tsx:117-119` per-route wrapping). Grep confirms zero `sessionStorage` / `localStorage` access in `context/` (only D-51 comment + test verifying absence).                                                                                              |

**Score:** 15/15 truths verified (7 UIRACE + 8 D-decision contracts).

---

### Required Artifacts

| Artifact                                                  | Expected                                             | Status    | Details                                                                                                                                  |
| --------------------------------------------------------- | ---------------------------------------------------- | --------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `frontend/src/features/race/RacePage.tsx`                 | Locked information hierarchy + 12-state branches     | VERIFIED  | 194 lines; composes all Plan 01-05 outputs; `__testState` test seam present                                                              |
| `frontend/src/features/race/pageState.ts`                 | derivePageState covering 12 PageState values         | VERIFIED  | 76 lines; priority-ordered cascade (replay > ws lifecycle > lane-failed > all-terminal > pre-race/countdown > live)                       |
| `frontend/src/features/race/raceReducer.ts`               | Pure reducer over RaceEvent union                    | VERIFIED  | Imported by useRaceStream + RacePage replay path; tested by raceReducer.test.ts                                                         |
| `frontend/src/features/race/hooks/useRaceStream.ts`       | WS hook with reducer + per-lane cursor               | VERIFIED  | D-44 + D-45 implemented; `enabled` gate (T-08-16) for mobile branch                                                                       |
| `frontend/src/features/race/hooks/useRaceReplay.ts`       | Replay fetch hook with run_id validation              | VERIFIED  | T-08-05 isValidRunId guard; cleanup pattern matches ReportDetailPage                                                                     |
| `frontend/src/features/race/context/FirstMentionProvider.tsx` | Route-scoped Set; no storage                     | VERIFIED  | 33 lines; null-safe (returns null outside provider — backward-compat per 08-PATTERNS.md)                                                |
| `frontend/src/features/race/components/RaceStatusStrip.tsx` | 48px strip + ReplayPill slot + aria-live           | VERIFIED  | 12-state copy table from UI-SPEC lines 263-278                                                                                          |
| `frontend/src/features/race/components/RaceLaneCard.tsx`    | Protocol stripe + ticker + badge + aria-live feed | VERIFIED  | High-contrast widen via useMediaQuery (functional, not just sx string)                                                                  |
| `frontend/src/features/race/components/RaceLaneTicker.tsx`  | TTFF / Recovery Rate / Turns / Score             | VERIFIED  | Tested independently                                                                                                                     |
| `frontend/src/features/race/components/FailureStateBadge.tsx` | Chip with tag color + Icon + label             | VERIFIED  | 32 lines; consumes failureTagColor                                                                                                      |
| `frontend/src/features/race/components/CharacteristicFailureBanner.tsx` | role=banner + 4px primary rule + h2 + italic clause | VERIFIED | borderRadius: 0; Display 1.6rem/700                                                                              |
| `frontend/src/features/race/components/MethodologySection.tsx` | Flat aside + GlossaryTerm wraps                | VERIFIED  | role="complementary"; ttff/recovery_rate/hardness_profile wrapped                                                                       |
| `frontend/src/features/race/components/HeatmapScaffold.tsx` | CSS Grid + role=grid/gridcell + 4-channel + empty overlay | VERIFIED | 199 lines; visuallyHidden sr-only label channel                                                                            |
| `frontend/src/features/race/components/ReplayPill.tsx`     | 999 radius pill, secondary.main, 14px/700/uppercase | VERIFIED  | 31 lines                                                                                                                                  |
| `frontend/src/features/race/components/ReplayScrubber.tsx` | Slider + 200ms throttled aria-live + reduced-motion | VERIFIED  | onChangeCommitted flushes pending value on release                                                                                       |
| `frontend/src/lib/trace/eventColors.ts` (extended)         | failureTagColor 5-entry map                          | VERIFIED  | Lines 44-60                                                                                                                              |
| `frontend/src/lib/glossary/glossaryTerms.ts` (extended)    | 8 race glossary terms                                | VERIFIED  | Lines 40-47 verbatim per UI-SPEC                                                                                                          |
| `frontend/src/components/glossary/GlossaryTerm.tsx` (extended) | First-mention Popover branch                  | VERIFIED  | Click + Enter/Space handlers; null-safe outside provider                                                                                |
| `frontend/src/app/routes.tsx` (extended)                   | /race + /race/:run_id with FirstMentionProvider     | VERIFIED  | Lines 114-129                                                                                                                            |
| `frontend/src/features/race/__fixtures__/raceStateFixtures.ts` | 12 fixtures, one per PageState               | VERIFIED  | 144 lines; round-trips through derivePageState                                                                                          |
| `frontend/src/features/race/__fixtures__/fixtures.test.ts` | Invariant test for all 12                          | VERIFIED  | test.each over ALL 12 states                                                                                                            |
| `frontend/src/features/race/RacePage.responsive.test.tsx` | UIRACE-05 4 breakpoints                              | VERIFIED  | 1280/1024/600/400; placeholder copy assertion                                                                                            |
| `frontend/src/features/race/RacePage.a11y.test.tsx`        | UIRACE-06 a11y suite                                 | VERIFIED  | 6 tests: tab→gridcell, aria-live fault_observed, ws-reconnecting, prefers-reduced-motion, prefers-contrast functional DOM, XSS guard    |

---

### Key Link Verification

| From                     | To                              | Via                                                  | Status |
| ------------------------ | ------------------------------- | ---------------------------------------------------- | ------ |
| RacePage                 | useRaceStream                    | direct hook call (line 62)                           | WIRED  |
| RacePage                 | useRaceReplay                    | direct hook call (line 65)                           | WIRED  |
| RacePage                 | derivePageState                  | function call (line 95)                              | WIRED  |
| RacePage                 | RaceStatusStrip / RaceLaneCard / CharacteristicFailureBanner / MethodologySection / HeatmapScaffold / ReplayScrubber | JSX composition (lines 121-177)                | WIRED  |
| useRaceStream            | raceReducer                     | useReducer (line 37)                                 | WIRED  |
| useRaceStream            | /api/race/ws                    | new WebSocket (line 49) with per-lane cursor query   | WIRED  |
| HeatmapScaffold          | failureTagColor                  | import + lookup (line 19, 109)                      | WIRED  |
| FailureStateBadge        | failureTagColor                  | import + lookup (line 2, 13)                        | WIRED  |
| GlossaryTerm             | useFirstMention                  | useContext via FirstMentionProvider (line 8)        | WIRED  |
| routes.tsx /race + /race/:run_id | RacePage                  | lazy + FirstMentionProvider wrap (lines 117-129)    | WIRED  |
| MethodologySection       | GlossaryTerm                    | JSX wraps for ttff / recovery_rate / hardness_profile | WIRED  |
| RaceLaneCard             | GlossaryTerm                    | JSX wrap on lane name                                | WIRED  |
| RaceLaneCard             | FailureStateBadge               | JSX (line 78) when terminal_tag set                  | WIRED  |
| RaceStatusStrip          | ReplayPill                      | JSX (line 81) when runId present                     | WIRED  |

---

### Behavioral Spot-Checks

| Behavior                                  | Command                                              | Result        | Status |
| ----------------------------------------- | ---------------------------------------------------- | ------------- | ------ |
| Test suite green                          | `cd frontend && npm test -- --run`                   | 267/267 pass, 27/27 files | PASS   |
| TypeScript typecheck clean                | `cd frontend && npx tsc --noEmit`                    | exit 0, no diagnostics    | PASS   |
| Vite build clean                          | `cd frontend && npm run build`                       | built in 2.94s, no errors | PASS   |
| `RacePage-*.js` chunk emitted             | check `dist/assets/RacePage-*.js`                    | 34.28 kB / 11.80 kB gzip  | PASS   |
| Fixture invariant for 12 PageState values | included in test suite (fixtures.test.ts)            | passes                    | PASS   |
| Responsive UIRACE-05 4 breakpoints        | included in test suite (RacePage.responsive.test.tsx) | passes                    | PASS   |
| A11y UIRACE-06 6 tests                    | included in test suite (RacePage.a11y.test.tsx)      | passes                    | PASS   |
| No `dangerouslySetInnerHTML` in feature   | `grep -rn "dangerouslySetInnerHTML" features/race/` | only in test assertions verifying absence | PASS |
| No sessionStorage/localStorage in FirstMentionProvider | `grep -rn ...`                          | only in D-51 comment + test verifying absence | PASS |

---

### Requirements Coverage

| Requirement | Description | Status | Evidence |
| ----------- | ----------- | ------ | -------- |
| UIRACE-01   | Locked information hierarchy in RacePage.tsx                       | SATISFIED | RacePage.tsx:121-178 hierarchy order |
| UIRACE-02   | All 12 page states + WS reconnect resumes from `turn_index`         | SATISFIED | pageState.ts cascade + fixtures + useRaceStream per-lane cursor |
| UIRACE-03   | Visual contract — radii scale, banner rule, italic clause, ticker   | SATISFIED | All 5 radius values + banner rule (4px primary) + italic span + label-above-value ticker |
| UIRACE-04   | failureTagColor token map (5 entries); color paired w/ icon + label | SATISFIED | eventColors.ts:54-60; consumed by badge + heatmap; 4-channel cell |
| UIRACE-05   | Responsive contract — desktop / tablet / small-tablet / mobile       | SATISFIED | flexDirection xs:column md:row + mobile placeholder + 4-breakpoint test |
| UIRACE-06   | A11y contract — Tab, focus-visible, AA, ARIA landmarks, prefers-* | SATISFIED | role="banner" / role="main" (via Container component="main") / role="complementary" / role="grid"+gridcell; prefers-contrast widen functional; aria-live throttled scrubber |
| UIRACE-07   | 8 new race glossary terms + first-mention popover                    | SATISFIED | 8 terms verbatim + GlossaryTerm Popover branch + FirstMentionProvider route-scoped |

No orphaned requirements. All 7 UIRACE requirements claimed by Phase 8 plans are satisfied.

---

### Anti-Patterns Found

None. Targeted greps confirm:
- Zero `dangerouslySetInnerHTML` in implementation files (only in test assertions verifying absence — T-08-08/T-08-04/T-08-14 mitigations).
- Zero `sessionStorage` / `localStorage` access in FirstMentionProvider (D-51 honored).
- No TODO/FIXME blockers in feature code.
- WS hook does not leak — cleanup via `active = false` + `socket.close()` (useRaceStream.ts:69-72).
- useRaceReplay does not leak — cleanup via `active = false` (useRaceReplay.ts:64-66).

---

### Deferred Items (out of Phase 8 scope, addressed downstream)

| # | Item | Addressed In | Evidence |
|---|------|--------------|----------|
| 1 | Heatmap data backend (cell population from API) | Phase 9 (HEAT-01/HEAT-02) | RacePage.tsx:94 `heatmap_has_data = false`; HeatmapScaffold renders empty overlay per D-47 contract |
| 2 | Replay backend `/api/race/runs/:run_id/trace` endpoint | Phase 9 (HEAT-03) | useRaceReplay.ts:5 inline comment; client.ts ships typed call signature only |
| 3 | OG image / mobile <480 cropped anchor PNG | Phase 10 (OG Image & Sharing) | RacePage.tsx:78 inline comment; placeholder shape only |
| 4 | Scrubber turn-index navigation (actual data binding) | Phase 9 (HEAT-03 deterministic replay) | RacePage.tsx:132-135 onScrub stub |
| 5 | Discovery panel | Phase 11 | listed in 08-CONTEXT.md `<deferred>` |
| 6 | DESIGN.md token lock | Phase 13 | listed in 08-CONTEXT.md `<deferred>` |

These are intentional deferrals documented in 08-CONTEXT.md and the Phase 9/10 ROADMAP entries. They do not affect Phase 8's verdict.

---

### Human Verification Required

None required. Every UIRACE requirement is verified programmatically:
- UIRACE-01 hierarchy: source-code section ordering (deterministic)
- UIRACE-02 page states: fixtures.test.ts invariant locks all 12
- UIRACE-03 radii: grepped from sx values
- UIRACE-04 failureTagColor: import-tracing single source of truth
- UIRACE-05 breakpoints: jsdom + matchMedia mock in responsive test suite
- UIRACE-06 a11y: 6 functional tests including DOM border-left-width assertion under prefers-contrast
- UIRACE-07 glossary: term inventory + GlossaryTerm Popover branch test

If a stakeholder later wants visual review for polish (typography rhythm, perceived contrast), that's a separate `/design-review` and not gated on Phase 8 PASS.

---

## Verdict

**PASS — clean.**

All 7 UIRACE success criteria from ROADMAP.md are satisfied. All 8 D-44..D-51 design decisions from 08-CONTEXT.md are honored in code. Test suite is fully green (267/267, 27 files). TypeScript typecheck and Vite build pass with no errors. Deferred items (heatmap data backend, replay backend, OG image) are intentional Phase 9/10 hand-offs explicitly documented in CONTEXT.md `<deferred>` and inline source comments.

### Recommended Next Action

Proceed to Phase 9 (Heatmap, Replay & K=3 Calibration). Phase 8 ships the rendering layer + empty-state contract; Phase 9 wires the heatmap data API (HEAT-01/HEAT-02), the deterministic replay path (HEAT-03), and locks K=3 calibration across v1 tasks (HEAT-04). The HeatmapScaffold + useRaceReplay typed call signatures are ready to receive Phase 9 backend payloads without UI changes.

---

*Verified: 2026-04-29 17:33 IST*
*Verifier: Claude (gsd-verifier, Opus 4.7 1M context)*
