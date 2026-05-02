# Roadmap: A2A vs MCP Demo Platform

## Milestones

- ✅ **v1.0 Demo-Day-Ready Platform** — Phases 1-5 (shipped 2026-04-27) — see [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)
- 🚧 **v2.0 Race Demo + Discovery + Visualization** — Phases 6-16 (gap closure in progress — audit found B1/B2/B3 blockers)

## Phases

<details>
<summary>✅ v1.0 Demo-Day-Ready Platform (Phases 1-5) — SHIPPED 2026-04-27</summary>

- [x] Phase 1: Demo Stability Foundation (2/2 plans) — completed 2026-04-22
- [x] Phase 2: Backend Trace Enrichment (3/3 plans) — completed 2026-04-23
- [x] Phase 3: New Scenarios (4/4 plans) — completed 2026-04-23
- [x] Phase 4: Comparison UI (4/4 plans) — completed 2026-04-26
- [x] Phase 5: Presentation Polish (3/3 plans) — completed 2026-04-27

Full details: [milestones/v1.0-ROADMAP.md](milestones/v1.0-ROADMAP.md)

</details>

### 🚧 v2.0 Race Demo + Discovery + Visualization (Gap Closure In Progress)

- [x] **Phase 6: TraceRecorder Schema Gate & Race Foundation** — Pre-design gate that lands the trace + websocket schema everything else depends on (8/8 plans, completed 2026-04-28)
- [x] **Phase 7: Race Backend — Lanes, Harness, Recovery State Machine** — Three runners, harness, recovery classifier, tasks, mock APIs (11/11 plans, completed 2026-04-29)
- [x] **Phase 8: Race Page UI & Visual Contract** — Three-lane scoreboard, banner, methodology, 12 page states, responsive + a11y (7/7 plans, completed 2026-04-29)
- [x] **Phase 9: Heatmap, Replay & K=3 Calibration** — Hardness-vs-failure heatmap, deterministic replay, multi-task K=3 sweep (4/4 plans, completed 2026-04-30)
- [x] **Phase 10: OG Image & Sharing** — Playwright OG/heatmap PNGs, copy-headline fallback, cache invalidation
- [x] **Phase 11: Tool Discovery Scenario** — `tool_discovery` scenario + `DiscoveryPhasePanel` surfacing MCP/A2A discovery as first-class UI (4/4 plans, completed 2026-05-01)
- [x] **Phase 12: Comparison Visualization Upgrades** — Annotated trace diff + interactive sequence diagram (3/3 plans, completed 2026-05-01)
- [x] **Phase 13: Design System Lock** — `/design-consultation` produces DESIGN.md formalizing race-demo tokens (1/1 plans, completed 2026-05-01)
- [ ] **Phase 14: Race Demo Integration Fix** — Wire `run_race()` HTTP endpoint, fix WS `run_id` mismatch, wire `heatmap_has_data`, wire `ReplayScrubber` seek (closes B1, B2, B3, W2)
- [ ] **Phase 15: Verification & Cleanup** — Write `07-VERIFICATION.md`, fix `DiscoveryPhasePanel` gate inconsistency, fix REQUIREMENTS.md stale checkboxes, Phase 12 code quality (closes Phase 7 VERIF gap, W1, W-VERIF-1..3)
- [ ] **Phase 16: Discovery UAT** — Live UI runs for 4 Phase 11 human verification items; document A2A protocol path, D-72 layout, ordering confirmation (closes DISC-01, DISC-02 human items)

## Phase Details

### Phase 6: TraceRecorder Schema Gate & Race Foundation
**Goal**: Land the trace + websocket schema upgrades that the rest of v2.0 depends on, closing the design doc's PRE-DESIGN GATE.
**Depends on**: Nothing (first phase of v2.0)
**Requirements**: TRC-01, TRC-02, TRC-03, TRC-04
**Success Criteria** (what must be TRUE):
  1. A developer can replay a recorded run and query its events filtered by `(run_id, lane)` in causal order, with LLM, tool, and inter-agent message events all carrying their per-event timing fields.
  2. Every trace file written by TraceRecorder carries `trace_schema_version`, and a v1.0 fixture loaded through `race/replay.py` is recognized by the stub no-op migrator without error.
  3. When FailureConfig fires, both `fault_injected` and `fault_observed` events appear in the trace with `fault_id`, `fault_kind`, `target`, `t_inject_ms`, `t_observed_ms`, `evidence`, and `wasted_tokens_before_detection`.
  4. A websocket client connecting to `/api/race/ws` receives `tick`, `tool_call`, `agent_msg`, `fault_injected`, `fault_observed`, `done`, `error`, and `race_done` events, each tagged with a per-lane `turn_index`.
**Plans**: 8 plans
Plans:
- [x] 06-01-PLAN.md — race/ package skeleton + 8 WsEvent dataclasses
- [x] 06-02-PLAN.md — race/turn.py TURN_DEFINING_EVENTS dispatch table
- [x] 06-03-PLAN.md — TraceRecorder upgrade (schema_version, lane, run_id, turn_index, ndjson hook)
- [x] 06-04-PLAN.md — race/failure.py FaultKind + inject_fault IRON RULE + Pydantic validator
- [x] 06-05-PLAN.md — race/runs.py RunWriter + threading.Lock single-writer arbiter
- [x] 06-06-PLAN.md — race/replay.py stub migrator + path-traversal guard + (run_id, lane) query
- [x] 06-07-PLAN.md — race/ws.py ConnectionManager + /api/race/ws full lifecycle route
- [x] 06-08-PLAN.md — tests/race/ test suite (8 files; field-presence, ndjson, IRON RULE, ws lifecycle)

### Phase 7: Race Backend — Lanes, Harness, Recovery State Machine
**Goal**: Stand up the three runner lanes, the harness that drives parallel runs, the locked recovery state machine, and the three v1 tasks with their mock APIs.
**Depends on**: Phase 6
**Requirements**: RACE-01, RACE-02, RACE-03, RACE-04, RACE-05, RACE-06, RACE-07
**Success Criteria** (what must be TRUE):
  1. A user can run `summarize_repo`, `negotiate_meeting`, or `book_travel` end-to-end on any of the three lanes (pure_mcp, pure_a2a, hybrid) using only mocked APIs and FailureConfig-injected hard failures, and receive a `RaceResult` per run.
  2. A demo operator can launch the harness at `n=5` (or `n=1` in dev) with `model=claude-sonnet-4-6, seed=42, temperature=0`, and watch live websocket events stream while the harness only retries transient infrastructure errors (never injected faults).
  3. Every fault recorded in a run is tagged by the recovery classifier with one of `recovered | gave_up | kept_going_without_noticing | kept_going_to_failure | indeterminate`, using the K=3 turn window and the locked `agent_msg_acknowledging_fault` regex with negation guard.
  4. Each (lane, task) emits one of the six deterministic headline sentences (recovered / gave_up / kept_going_without_noticing / kept_going_to_failure / indeterminate / lane_failed) from `failure_mode_classifier`.
  5. Each of the four v1 hardness types appears in at least two of the three v1 tasks, verified by `HardnessProfile` inspection on the seeded `task_config.yaml` files.
**Plans**: 11 across 7 waves (W0-W6) — 11/11 complete (07-01..07-11; Phase 7 SHIPPED 2026-04-29)

### Phase 8: Race Page UI & Visual Contract
**Goal**: Deliver the three-lane race page that renders the locked information hierarchy, the full set of 12 page states, and the visual / responsive / accessibility contracts.
**Depends on**: Phase 6, Phase 7
**Requirements**: UIRACE-01, UIRACE-02, UIRACE-03, UIRACE-04, UIRACE-05, UIRACE-06, UIRACE-07
**Success Criteria** (what must be TRUE):
  1. A viewer landing on `/race` sees the locked hierarchy — top bar, status strip, three lanes in the 1200px central column, characteristic-failure banner with 4px primary rule and italic dynamic clause, methodology as flat section, heatmap — with the visual contract enforced (lane stripes, pill failure-state badges, correct border-radius scale).
  2. All 12 documented page states (pre-race, countdown, live n=1, live n=5, done, replay, sparse-heatmap, ws-disconnected, ws-reconnecting, indeterminate, lane-failed, heatmap-empty) render correctly, and a websocket reconnect resumes the client at its last `turn_index`.
  3. A keyboard-only user can navigate the page in correct Tab order with focus-visible outlines, screen readers announce `fault_observed` via `aria-live="polite"`, and `prefers-reduced-motion` and `prefers-contrast: more` are honored on every animated transition and stripe/outline.
  4. The page renders correctly across desktop (≥1200px three-lane row), tablet (768-1199 shrunk three lanes), small-tablet (480-767 compacted metrics), and mobile (<480 falls back to `?mode=summary` with cropped anchor PNG + heatmap).
  5. The 8 new race glossary terms (ttff, recovery_rate, hardness_profile, recovered, gave_up, kept_going_without_noticing, kept_going_to_failure, indeterminate) appear with first-mention popovers across the Race page, and the `failureTagColor` map (5 entries in `eventColors.ts`) is the single source of truth consumed by both heatmap cells and badges, paired with icon + label.
**Plans**: 7 plans across 4 waves
Plans:
- [ ] 08-01-PLAN.md — Tokens + glossary + FirstMentionProvider + GlossaryTerm Popover branch + shared race types (Wave 1)
- [ ] 08-02-PLAN.md — Routes (/race + /race/:run_id) + AppShell nav + RacePage shell + 12-state derivePageState (Wave 2)
- [ ] 08-03-PLAN.md — TDD raceReducer + useRaceStream(enabled) + useRaceReplay (Wave 3)
- [ ] 08-04a-PLAN.md — Lane/badge family: RaceLaneCard (with prefers-contrast widen) + RaceLaneTicker + FailureStateBadge + ReplayPill (Wave 3)
- [ ] 08-04b-PLAN.md — Chrome family: RaceStatusStrip + CharacteristicFailureBanner + MethodologySection (Wave 3)
- [ ] 08-05-PLAN.md — HeatmapScaffold (CSS Grid + role=grid/gridcell + empty-state overlay) + ReplayScrubber (Slider + 200ms aria-live throttle) (Wave 3)
- [ ] 08-06-PLAN.md — RacePage integration + 12-state fixtures + responsive (4 breakpoints) + a11y test suite (Wave 4)
**UI hint**: yes

### Phase 9: Heatmap, Replay & K=3 Calibration
**Goal**: Ship the hardness-vs-failure heatmap as the closing artifact, the deterministic `/race/<run_id>` replay path, and lock K=3 across all three v1 tasks.
**Depends on**: Phase 7, Phase 8
**Requirements**: HEAT-01, HEAT-02, HEAT-03, HEAT-04
**Success Criteria** (what must be TRUE):
  1. A viewer scrolling to the bottom of `/race` sees the heatmap with rows = HardnessType, columns = lane, each cell showing dominant_tag color + icon + pattern fill + recovery rate (e.g., `12/15`); cells are keyboard-focusable and the "directional · n=3 tasks · v1" pill renders in `secondary.main`.
  2. A 5-pill legend strip is always visible and the heatmap footer shows model · seed · pinned task IDs.
  3. Loading `/race/<run_id>` reads `data/runs/<run_id>.json`, replays without any live LLM call, and the recovery-rule state machine produces identical per-run tags to the original run, verified by a two-layer fixture test (snapshot + `--update-snapshots` flag).
  4. A K∈{2,3,4,5} sweep over the §The Assignment fictional traces for all three v1 tasks confirms K=3 produces the expected tag for every trace, with the test committed to `tests/test_recovery_calibration.py`.
**Plans**: 4 plans across 2 waves
Plans:
- [x] 09-01-PLAN.md — race/config.py HEATMAP_BASELINE + race/heatmap.py aggregator + cache + GET /api/race/heatmap + harness run_meta + invalidate_cache hook (Wave 1) — completed 2026-04-30
- [x] 09-02-PLAN.md — GET /api/race/runs/{run_id}/trace replay route + 400/404/schema tests (Wave 1) — completed 2026-04-30
- [x] 09-03-PLAN.md — pytest --update-snapshots flag + _replay_helpers.replay_with_k + test_replay_symmetry + tests/test_recovery_calibration.py K∈{2,3,4,5} sweep (Wave 1) — completed 2026-04-30
- [x] 09-04-PLAN.md — HardnessFailureHeatmap.tsx wrapper + useRaceHeatmap hook + fetchRaceHeatmap client + RacePage wiring (Wave 2) — completed 2026-04-30
**UI hint**: yes

### Phase 10: OG Image & Sharing
**Goal**: Make every `/race/<run_id>` URL shareable with server-rendered OG and heatmap PNGs, with a client-side fallback.
**Depends on**: Phase 8, Phase 9
**Requirements**: OG-01, OG-02, OG-03, OG-04
**Success Criteria** (what must be TRUE):
  1. Pasting a `/race/<run_id>` URL into Twitter, LinkedIn, or Slack unfurls a 1200×630 cropped anchor (3 lanes + banner) served from `/race/<run_id>/og.png`, cached at `data/og/<run_id>-v<OG_LAYOUT_VERSION>.png` and wired via `og:image` and `twitter:image` meta tags.
  2. Hitting `/race/<run_id>/heatmap.png` returns a 1200×900 heatmap card screenshot with `run_id · model · seed · n · task_ids` annotation, sharing the `OG_LAYOUT_VERSION` cache key.
  3. A user can click "Copy headline image" beside the banner and a client-side canvas snapshot of the same 1200×630 anchor region is copied to clipboard, even if server OG generation has failed.
  4. Hitting `/race/<run_id>/og.png` or `/heatmap.png` for an unknown `run_id` returns 404 before Playwright spawns, and bumping `OG_LAYOUT_VERSION` causes stale `<id>-v<old>.*` files to be purged on next request.
**Plans**: 5 plans across 4 waves
Plans:
- [x] 10-01-PLAN.md — race/og.py module (Playwright lifespan + asyncio.Lock + cache helpers) + OG_LAYOUT_VERSION + .gitignore + pyproject optional-dep + cache unit tests (Wave 1)
- [x] 10-02-PLAN.md — web.py lifespan registration + /race + /race/{run_id} HTML route w/ meta-tag injection + /race/{run_id}/og.png + /race/{run_id}/heatmap.png + 9-test D-63 mocked-render matrix (Wave 2)
- [x] 10-03-PLAN.md — RacePage `?og=1` mode + data-og-anchor/data-og-ready/data-heatmap-anchor sentinels + WS-gating + HardnessFailureHeatmap ogAnnotation prop + HeatmapAnnotationStrip component (Wave 2)
- [x] 10-04-PLAN.md — html2canvas dep + CopyHeadlineImageButton (lazy import + ClipboardItem + download fallback) + CharacteristicFailureBanner actionSlot prop + RacePage button mount + 4 vitest cases (Wave 3)
- [x] 10-05-PLAN.md — Phase 8 mobile-summary placeholder closure: <img src=/race/{run_id}/og.png> consumer w/ onError graceful degradation (Wave 4)
**UI hint**: yes

### Phase 11: Tool Discovery Scenario
**Goal**: Surface MCP tool discovery and A2A agent-card discovery as a first-class UI section above the trace explorer, on a dedicated scenario.
**Depends on**: Phase 6 (trace schema)
**Requirements**: DISC-01, DISC-02
**Success Criteria** (what must be TRUE):
  1. A demo operator can run the new `tool_discovery` scenario from `DemoRepository` on both MCP and A2A protocols and observe the discovery phase exercising stale-capability-cache and unknown-tool-fallback failure modes.
  2. A viewer of the run sees a `DiscoveryPhasePanel` above the trace explorer rendering the MCP tool catalog and A2A agent cards side-by-side with timestamps, before any execution-phase events.
**Plans**: 4 plans across 3 waves
Plans:
- [x] 11-01-PLAN.md — Wave 0 refactor: extract JsonTree + FIELD_ANNOTATIONS + annotate from ProtocolEnvelopeDrawer to lib/trace/JsonTree.tsx (DISC-02)
- [x] 11-02-PLAN.md — Wave 1 backend: TICKET-1013 + CUST-005 seed rows + pytest coverage proving discovery+fallback emission (DISC-01)
- [x] 11-03-PLAN.md — Wave 1 frontend: DiscoveryPhasePanel.tsx component + DiscoveryPhasePanelProps + 5 vitest cases (incl. a2a_remote_discovery skill chips) (DISC-02)
- [x] 11-04-PLAN.md — Wave 2 mount-site wiring: TraceWorkspacePage gate (D-73) + CompareTracesPanel single-panel above dual-column (D-72) + integration verification (DISC-02)
**UI hint**: yes

### Phase 12: Comparison Visualization Upgrades
**Goal**: Deepen the existing comparison story with annotated diff between two protocol traces and an interactive sequence diagram for a single trace.
**Depends on**: Phase 6 (trace schema for alignment fields)
**Requirements**: VIZ-01, VIZ-02
**Success Criteria** (what must be TRUE):
  1. A viewer on `CompareTracesPanel` can open an annotated diff view that aligns matching events line-by-line and visually highlights divergence points (added vs removed steps, role-first labels) between two protocol traces.
  2. A viewer on `TraceExplorer` can open an interactive sequence diagram with vertical lifelines per actor and horizontal arrows per message, click-to-pin a message, and have the animation honor `prefers-reduced-motion`.
**Plans**:

**Wave 1**
- [x] 12-01: alignTraces pure function + vitest (`frontend/src/components/traces/diffAlign.ts`) — VIZ-01 algorithm foundation
- [x] 12-02: SequenceDiagramView + TraceExplorer toggle (List|Sequence) + vitest — closes VIZ-02

**Wave 2** *(blocked on Wave 1 completion)*
- [x] 12-03: AnnotatedDiffView + CompareTracesPanel toggle (Side-by-side|Annotated diff) + vitest — closes VIZ-01 (depends_on: 12-01)

**Cross-cutting constraints**:
- D-78 role-first labels via `traceLabel()` from `frontend/src/lib/trace/utils.ts`
- D-84 reuse existing tokens (`failureTagColor`, `getProtocolColor`, MUI palette) — no new colors
- D-85 zero new dependencies — no `@xyflow/react`, no `motion` library imports

**UI hint**: yes

### Phase 13: Design System Lock
**Goal**: Run `/design-consultation` against the now-shipped race demo and produce `.planning/DESIGN.md` formalizing the new design tokens and rules so future surfaces stop relitigating them.
**Depends on**: Phase 8, Phase 9, Phase 10 (race demo + heatmap + OG must exist for the consultation to formalize)
**Requirements**: DSGN-01
**Success Criteria** (what must be TRUE):
  1. `.planning/DESIGN.md` exists and codifies the `failureTagColor` map (5 entries), the methodology-as-flat-section rule, `secondary.main` as replay-pill semantic, the role-first first-mention contract scoped to Run + Compare + Race pages, and the primary/secondary palette intent.
  2. A new contributor opening DESIGN.md can answer "where does this color come from / when do I render flat vs in a card / how do I introduce role-first labels on a new page" without reading source.
**Plans**: 1 plan
Plans:
- [x] 13-01-PLAN.md — /design-consultation + author .planning/DESIGN.md (5 mandated items: failureTagColor table, methodology-as-flat, secondary.main semantic, role-first contract, palette intent) (Wave 1)
**UI hint**: yes

### Phase 14: Race Demo Integration Fix
**Goal**: Make the race demo functionally end-to-end: a user can start a race via HTTP, watch live WebSocket events stream into the Race page, and see the heatmap page-state reflect real data. Also wire the replay scrubber to seek.
**Depends on**: Phase 7, Phase 8, Phase 9
**Gap Closure**: B1 (no HTTP race trigger), B2 (WS run_id mismatch), B3 (heatmap_has_data hardcoded), W2 (scrubber no-op)
**Requirements**: RACE-01, RACE-02, RACE-03, RACE-04, RACE-05, RACE-06, RACE-07, TRC-04, UIRACE-01, UIRACE-02, UIRACE-03, HEAT-01, HEAT-02, HEAT-03
**Success Criteria** (what must be TRUE):
  1. A user can POST to `/api/race/run` (or equivalent) with task/lane config, receive a `run_id`, open `/race?run_id=<id>`, and watch live WebSocket events stream through all 12 page states.
  2. `useRaceStream` successfully connects to `/api/race/ws` with the correct `run_id` query param — no HTTP 422 errors on connect.
  3. When a completed race has heatmap data, `RacePage` `derivePageState` receives `heatmap_has_data: true` and transitions to the correct heatmap-populated state.
  4. Dragging the `ReplayScrubber` in replay mode (`/race/<run_id>`) seeks the displayed state to the selected turn index.
**Plans**: 4 plans
Plans:
- [ ] 14-01-PLAN.md — Add `POST /api/race/run` endpoint: generate `run_id`, call `run_race(ws_emitter=MANAGER.publish)` as background task, return `{run_id}` (backend)
- [ ] 14-02-PLAN.md — Fix `useRaceStream.ts:buildWsUrl()`: receive `run_id` prop, append to WS URL; update `RacePage` to fetch run_id from start-race call before opening WS
- [ ] 14-03-PLAN.md — Wire `useRaceHeatmap()` data into `heatmap_has_data` in `RacePage.tsx`; add `heatmap_has_data` to `derivePageState` inputs correctly
- [ ] 14-04-PLAN.md — Wire `ReplayScrubber.onScrub`: implement turn-index seek in `useRaceReplay`, pass seek handler down to scrubber

### Phase 15: Verification & Cleanup
**Goal**: Close all documentation and code-quality gaps found by the audit: write the missing Phase 7 verification document, fix the DiscoveryPhasePanel gate inconsistency, fix stale REQUIREMENTS.md checkboxes, and clean up Phase 12 code-quality warnings.
**Depends on**: Phase 7, Phase 11, Phase 12
**Gap Closure**: Phase 7 missing VERIFICATION.md, W1 (TraceWorkspacePage gate), REQUIREMENTS.md stale checkboxes (OG/DISC/VIZ), W-VERIF-1..3
**Requirements**: RACE-01..07 (verification doc), DISC-02 (gate fix)
**Success Criteria** (what must be TRUE):
  1. `07-VERIFICATION.md` exists aggregating Phase 7 plan SUMMARY evidence and test results for RACE-01..07.
  2. `TraceWorkspacePage` DiscoveryPhasePanel gate uses event-presence (same strategy as `CompareTracesPanel`) — panel appears for imported NDJSON runs with `tool_discovery` events.
  3. REQUIREMENTS.md checkboxes for OG-01..04, VIZ-01..02 updated to `[x]`; traceability Status updated to Complete.
  4. Phase 12 code quality items resolved: duplicate `traceEventProtocol` import removed, D-83 reduced-motion test fixed, dead `pinnedEventId` prop removed from `ProtocolTier`.
**Plans**: 4 plans
Plans:
- [ ] 15-01-PLAN.md — Write `07-VERIFICATION.md`: read all 11 Phase 7 SUMMARY.md files, aggregate RACE-01..07 evidence, confirm pytest 345/345, write structured verification document
- [ ] 15-02-PLAN.md — Fix `TraceWorkspacePage` DiscoveryPhasePanel gate: replace `detail?.summary?.scenario === "tool_discovery"` with event-presence check matching `CompareTracesPanel`
- [ ] 15-03-PLAN.md — Fix REQUIREMENTS.md: update OG-01..04, DISC-01..02, VIZ-01..02 checkboxes to `[x]` and Status to Complete; update traceability coverage count
- [ ] 15-04-PLAN.md — Phase 12 cleanup: remove duplicate import (W-VERIF-1), fix D-83 test (W-VERIF-2), remove dead `pinnedEventId` prop from `ProtocolTier` (W-VERIF-3)

### Phase 16: Discovery UAT
**Goal**: Complete the 4 outstanding human verification items from Phase 11 by running the tool_discovery scenario live in both MCP and A2A modes, confirming D-72 single-panel layout, ordering, and stale-cache UX story. Document results to advance Phase 11 VERIFICATION.md status from `human_needed` to `passed`.
**Depends on**: Phase 11, Phase 14 (race demo must be functional for live runs)
**Gap Closure**: W3 (Phase 11 human verification items)
**Requirements**: DISC-01, DISC-02
**Success Criteria** (what must be TRUE):
  1. `tool_discovery` scenario runs successfully on both MCP and A2A protocols via live UI; `DiscoveryPhasePanel` populates both columns with real events.
  2. In compare mode, exactly ONE full-width `DiscoveryPhasePanel` renders above the dual-column Grid (D-72 confirmed by eye).
  3. The panel renders strictly above all execution-phase events in the visual flow (ordering confirmed).
  4. The stale-cache warning icon (`aria-label="Stale capability cache"`) appears when `requested_transport` differs from `transport`.
  5. `11-VERIFICATION.md` status updated from `human_needed` to `passed` with evidence from live runs.
**Plans**: 1 plan
Plans:
- [ ] 16-01-PLAN.md — Live UAT: run tool_discovery in MCP + A2A mode, verify 4 human items, update `11-VERIFICATION.md` status and evidence

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Demo Stability Foundation | v1.0 | 2/2 | Complete | 2026-04-22 |
| 2. Backend Trace Enrichment | v1.0 | 3/3 | Complete | 2026-04-23 |
| 3. New Scenarios | v1.0 | 4/4 | Complete | 2026-04-23 |
| 4. Comparison UI | v1.0 | 4/4 | Complete | 2026-04-26 |
| 5. Presentation Polish | v1.0 | 3/3 | Complete | 2026-04-27 |
| 6. TraceRecorder Schema Gate & Race Foundation | v2.0 | 8/8 | Complete | 2026-04-28 |
| 7. Race Backend — Lanes, Harness, Recovery | v2.0 | 11/11 | Complete | 2026-04-29 |
| 8. Race Page UI & Visual Contract | v2.0 | 7/7 | Complete | 2026-04-29 |
| 9. Heatmap, Replay & K=3 Calibration | v2.0 | 4/4 | Complete | 2026-04-30 |
| 10. OG Image & Sharing | v2.0 | 3/3 | Complete | 2026-04-30 |
| 11. Tool Discovery Scenario | v2.0 | 4/4 | Complete | 2026-05-01 |
| 12. Comparison Visualization Upgrades | v2.0 | 3/3 | Complete | 2026-05-01 |
| 13. Design System Lock | v2.0 | 1/1 | Complete | 2026-05-01 |
| 14. Race Demo Integration Fix | v2.0 | 0/4 | Not started | - |
| 15. Verification & Cleanup | v2.0 | 0/4 | Not started | - |
| 16. Discovery UAT | v2.0 | 0/1 | Not started | - |
