# Requirements: A2A vs MCP Demo Platform — Milestone v2.0

**Defined:** 2026-04-28
**Core Value:** A side-by-side, runnable comparison that makes the differences between MCP and A2A visible — not described, not diagrammed, but live and traceable.

**Milestone goal:** Ship the Three-Lane Failure-Shape Race Demo as the new flagship surface, plus tool-discovery scenario and visualization upgrades that deepen the existing comparison story.

---

## v2.0 Requirements

Each requirement maps to exactly one roadmap phase (see Traceability).

### Race Schema & Trace Foundation (TRC)

Backend trace and websocket schema upgrades the rest of the race depends on.

- [x] **TRC-01**: TraceRecorder emits `t_call_start_ms`, `tokens_in`, `tokens_out` per LLM call; `t_call_ms`, `tool_name`, `status`, `error_kind` per tool call; `t_ms`, `sender`, `recipient`, `content` per inter-agent message; queryable post-run by `(run_id, lane)` in causal order
- [x] **TRC-02**: `trace_schema_version` field added to TraceRecorder; stub no-op migrator recognizes v1.0 traces in `race/replay.py`
- [x] **TRC-03**: FailureConfig emits `fault_injected` events to TraceRecorder with `fault_id`, `fault_kind`, `target`, `t_inject_ms`; emits `fault_observed` events with `evidence`, `wasted_tokens_before_detection`, `t_observed_ms` (schema + persistence path; runtime emission of fault_observed deferred to Phase 7 per D-14)
- [x] **TRC-04**: Websocket event schema (`/api/race/ws`) supports `tick`, `tool_call`, `agent_msg`, `fault_injected`, `fault_observed`, `done`, `error`, `race_done`; every event carries `turn_index` per-lane

### Race Backend (RACE)

Lanes, harness, recovery state machine, tasks.

- [x] **RACE-01**: `HardnessType` enum with 4 v1 entries (LONG_CHAIN, RATE_PRESSURE, SCHEMA_VARIANCE, MULTI_SOURCE_SYNTHESIS); `HardnessProfile` dataclass; each v1 type appears in ≥2 tasks
- [x] **RACE-02**: Three runners — `runners/pure_mcp.py`, `runners/pure_a2a.py`, `runners/hybrid.py` — each consumes a per-task `task_config.yaml` and returns a `RaceResult`
- [x] **RACE-03**: `harness.py` drives N parallel runs per (lane, task); demo `n=5`, dev `n=1`; deterministic `model=claude-sonnet-4-6, seed=42, temperature=0, per_run_timeout_s=120`; emits live websocket events; only retries transient infrastructure errors (not injected faults)
- [x] **RACE-04**: Recovery state machine in `race/classifier.py` tags each fault as `recovered | gave_up | kept_going_without_noticing | kept_going_to_failure | indeterminate`; uses K=3 turn window; `agent_msg_acknowledging_fault` regex with negation guard (locked in design doc)
- [x] **RACE-05**: Three v1 tasks — `summarize_repo`, `negotiate_meeting`, `book_travel` — with full `task_config.yaml` (failure_script + hybrid_plan + hardness_profile) and per-task scorer (Haiku judge / structural / composite)
- [x] **RACE-06**: `failure_mode_classifier(lane, task_id, per_run_tags, per_run_aggregate_stats)` produces deterministic per-lane headline sentences from 6 templates (recovered / gave_up / kept_going_without_noticing / kept_going_to_failure / indeterminate / lane_failed)
- [x] **RACE-07**: Mock APIs for the 3 v1 tasks — GitHub mock (5 fixture repos), calendar mock (3 fixture calendars), travel mock (search + booking + fixtures)

### Race Page UI (UIRACE)

Three-lane scoreboard, banner, methodology, page states.

- [ ] **UIRACE-01**: `frontend/src/features/race/RacePage.tsx` renders the locked information hierarchy — top bar, status strip, three lanes (1200px central column), characteristic-failure banner, methodology, heatmap
- [ ] **UIRACE-02**: All 12 page states render correctly (pre-race, countdown, live n=1, live n=5, done, replay, sparse-heatmap, ws-disconnected, ws-reconnecting, indeterminate, lane-failed, heatmap-empty); WS reconnect resumes from last `turn_index`
- [ ] **UIRACE-03**: Visual contract enforced — left-edge lane stripe, pill-shaped failure-state badge, border-radius scale (lane=18 / banner=0 / badge=4 / heatmap-cell=0 / pills=999), banner h1 left-aligned with 4px primary rule and italic dynamic clause, methodology as flat section (no Paper/Card), label-above-value ticker
- [ ] **UIRACE-04**: `failureTagColor` token map (5 entries) added to `frontend/src/lib/trace/eventColors.ts`; consumed by both heatmap cells and failure-state badges; color paired with icon + label (never sole information channel)
- [ ] **UIRACE-05**: Responsive contract — desktop ≥1200px three-lane row, tablet 768-1199 shrinks but keeps three lanes, small-tablet 480-767 compacts metrics, mobile <480 renders `?mode=summary` with cropped anchor PNG + heatmap
- [ ] **UIRACE-06**: Accessibility contract — keyboard nav (Tab order, focus-visible), WCAG AA contrast, ARIA landmarks (banner / main / aside), `prefers-reduced-motion` honored on all animated transitions, `prefers-contrast: more` widens stripe + outline, fault_observed announced via `aria-live="polite"`
- [ ] **UIRACE-07**: 8 new glossary terms added (ttff, recovery_rate, hardness_profile, recovered, gave_up, kept_going_without_noticing, kept_going_to_failure, indeterminate); first-mention rule extended to Race page

### Heatmap & Replay (HEAT)

Closing artifact + deterministic replay.

- [ ] **HEAT-01**: `HardnessFailureHeatmap.tsx` renders rows = HardnessType, columns = lane; cell shows dominant_tag color + icon + pattern fill + recovery rate (e.g., `12/15`); cells keyboard-focusable; "directional · n=3 tasks · v1" pill in `secondary.main`
- [ ] **HEAT-02**: Heatmap legend strip always visible (5 inline pills); footer shows model · seed · pinned task IDs
- [ ] **HEAT-03**: Replay route `/race/<run_id>` reads `data/runs/<run_id>.json` (no live LLM); recovery-rule state machine re-fires identically on replay; verified by two-layer fixture test (per-run tag snapshot + `--update-snapshots` flag)
- [ ] **HEAT-04**: K=3 multi-task calibration — sweep K∈{2,3,4,5} on all 3 v1 tasks using fictional traces from §The Assignment; confirm K=3 produces expected tag for all traces (TODO 8 promoted)

### OG Image & Sharing (OG)

Shareable URLs with social-embed images (TODO 3 promoted).

- [ ] **OG-01**: `/race/<run_id>/og.png` Playwright route renders 1200×630 cropped anchor (3 lanes + banner) via `RacePage.tsx?og=1` mode; cached at `data/og/<run_id>-v<OG_LAYOUT_VERSION>.png`; served via `<meta property="og:image">` and `<meta name="twitter:image">`
- [ ] **OG-02**: `/race/<run_id>/heatmap.png` Playwright route renders 1200×900 heatmap card screenshot with annotation strip (`run_id · model · seed · n · task_ids`); shares `OG_LAYOUT_VERSION` cache key with og.png
- [ ] **OG-03**: "Copy headline image" button beside banner — client-side canvas snapshot of the same 1200×630 anchor region; ships as fallback if OG generation fails
- [ ] **OG-04**: 404 on unknown `run_id` before Playwright spawn; cleanup task purges stale `<id>-v<old>.*` files when `OG_LAYOUT_VERSION` bumps

### Tool Discovery (DISC)

v1 backlog: surface MCP/A2A discovery as first-class UI element.

- [ ] **DISC-01**: New `tool_discovery` scenario in `DemoRepository` exercising MCP tool discovery and A2A agent-card discovery on the same task; failure modes include stale capability cache and unknown-tool fallback
- [ ] **DISC-02**: `DiscoveryPhasePanel.tsx` component renders the discovery phase as a first-class section above the trace explorer; shows tool catalog (MCP) and agent cards (A2A) side-by-side with timestamps

### Visualization (VIZ)

v1 backlog: annotated diff + sequence diagram.

- [ ] **VIZ-01**: Annotated diff view between two protocol traces — line-by-line comparison panel that aligns matching events and highlights divergence points (added vs. removed steps, role-first labels), reachable from CompareTracesPanel header
- [ ] **VIZ-02**: Interactive sequence diagram (vertical lifelines per actor, horizontal arrows per message) for a single trace; reachable from TraceExplorer; honors `prefers-reduced-motion` and click-to-pin

### Design System Lock (DSGN)

TODO 5 promoted: formalize race-demo's de-facto design rules.

- [ ] **DSGN-01**: Run `/design-consultation` and produce `.planning/DESIGN.md` formalizing the race-demo design tokens — `failureTagColor` map, methodology-as-flat rule, `secondary.main` as replay-pill semantic, role-first first-mention contract scoped to Run + Compare + Race pages, primary/secondary palette intent

---

## Deferred Requirements (v2.1+)

Acknowledged but not in current roadmap. Promoted from v1 backlog or TODOS.md per their promote conditions.

### SDK migrations (SDK)

- **SDK-01**: A2A SDK 0.3.26 → 1.0.0 migration (broker core touch)
- **SDK-02**: MCP SDK v2 migration (`FastMCP` → `McpServer`, server-side rewrite of all MCP servers)

### TODOs (carried)

- **TODO-01**: Real plan-emitter hybrid (replace v1 enum tool with `propose_plan` agent step generation)
- **TODO-02**: Multi-seed n=20+ benchmark mode with bootstrap CIs and per-axis winner declaration
- **TODO-04**: Production trace schema migrator (real transformations of v1.0 fixtures)
- **TODO-06**: Real display typeface (replace Segoe UI fallback)
- **TODO-07**: HardnessFailureHeatmap auto-renders rows from `HardnessType` enum
- **TODO-09**: HMAC-signed PNG URLs (production hardening)
- **TODO-10**: LLM-judge replacement for `agent_msg_acknowledging_fault` regex (paraphrase resilience)

### v1.0 Process Debt

- Phase 5 missing phase-level VERIFICATION.md (bookkeeping; integration check covered code paths)
- Phase 4 — 3 visual verification items deferred to demo-day rehearsal (swimlane overlap, compare scroll sync, metrics chip visibility)

---

## Out of Scope

Explicitly excluded from v2.0 to prevent scope creep. Reasoning per item.

| Feature | Reason |
|---------|--------|
| Dark mode on Race page | Theme is light-only; race demo not the place to introduce a mode toggle |
| Live OpenAI mode on Race page | Race lane locks deterministic mocks with FailureConfig; live LLM is a different product |
| Per-cell heatmap drilldown to full trace | Cell tooltip + sample-trace link is enough; deep drilldown lives in existing TraceExplorer |
| Animation on heatmap cell render | Static grid; animation distracts from "directional" honesty pill |
| Login / saved runs / user-owned share-pages | Anonymous shareable URLs only in v2.0; auth is leaderboard-10x scope (post-v2) |
| Sound / haptic on failure-state badge | Reduced-motion compliance trumps; sound design is a separate phase |
| Per-task "explain why this failure mode" inline copy | Methodology + failure script disclose enough; explanatory prose stays in post body |
| Real plan-emitter hybrid in v2.0 | TODO 1 — agent-driven decision policy is v2.1+ scope; v2.0 hybrid uses pre-scripted `hybrid_plan.steps[].on_fault` enum |
| Multi-seed statistical benchmark | TODO 2 — conflicts with "no winner declared" rule; promote on benchmark-flavored signal only |
| HMAC URL signing | TODO 9 — hackathon-ephemeral demo; 404-on-unknown-run_id sufficient |
| Production trace migrator | TODO 4 — only matters when an actual v1.0 fixture replay is requested |

---

## Traceability

Populated by roadmap creation 2026-04-28. Phases 6-13 carry the v2.0 milestone.

| Requirement | Phase | Status |
|-------------|-------|--------|
| TRC-01 | Phase 6 | Complete |
| TRC-02 | Phase 6 | Complete |
| TRC-03 | Phase 6 | Complete |
| TRC-04 | Phase 6 | Complete |
| RACE-01 | Phase 7 | Complete |
| RACE-02 | Phase 7 | Complete |
| RACE-03 | Phase 7 | Pending |
| RACE-04 | Phase 7 | Complete |
| RACE-05 | Phase 7 | Complete |
| RACE-06 | Phase 7 | Pending |
| RACE-07 | Phase 7 | Pending |
| UIRACE-01 | Phase 8 | Pending |
| UIRACE-02 | Phase 8 | Pending |
| UIRACE-03 | Phase 8 | Pending |
| UIRACE-04 | Phase 8 | Pending |
| UIRACE-05 | Phase 8 | Pending |
| UIRACE-06 | Phase 8 | Pending |
| UIRACE-07 | Phase 8 | Pending |
| HEAT-01 | Phase 9 | Pending |
| HEAT-02 | Phase 9 | Pending |
| HEAT-03 | Phase 9 | Pending |
| HEAT-04 | Phase 9 | Pending |
| OG-01 | Phase 10 | Pending |
| OG-02 | Phase 10 | Pending |
| OG-03 | Phase 10 | Pending |
| OG-04 | Phase 10 | Pending |
| DISC-01 | Phase 11 | Pending |
| DISC-02 | Phase 11 | Pending |
| VIZ-01 | Phase 12 | Pending |
| VIZ-02 | Phase 12 | Pending |
| DSGN-01 | Phase 13 | Pending |

**Coverage:**
- v2.0 requirements: 31 total
- Mapped to phases: 31 ✓
- Unmapped: 0

---
*Requirements defined: 2026-04-28*
*Last updated: 2026-04-28 — roadmap created, traceability populated (Phases 6-13)*
