# Phase 9: Heatmap, Replay & K=3 Calibration - Context

**Gathered:** 2026-04-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Ship the closing-artifact hardness-vs-failure heatmap (HEAT-01/02), the deterministic `/race/<run_id>` replay backend (HEAT-03), and lock K=3 across all three v1 tasks via a parametrized calibration sweep (HEAT-04). Phase 8 already shipped the rendering scaffold + empty-state contract + replay route + typed `fetchRaceReplay` client signature. Phase 9 wires the data layer behind those surfaces.

In scope:
- `GET /api/race/heatmap` — new aggregate endpoint serving (HardnessType × lane) cells.
- `GET /api/race/runs/<run_id>/trace` — replay endpoint backing the Phase 8 `fetchRaceReplay` client (currently un-implemented).
- `src/a2a_vs_mcp/race/heatmap.py` (or sibling) — aggregation logic, in-memory cache, baseline filter.
- `src/a2a_vs_mcp/race/config.py` (new constants module if absent) — `HEATMAP_BASELINE` pinned (model, seed, task_ids).
- `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` — replaces or wraps Phase 8 `HeatmapScaffold` once cells exist.
- 5-pill legend strip + footer (`model · seed · pinned task IDs`) read from baseline payload.
- Two-layer fixture test for replay-symmetric tags (snapshot + `--update-snapshots` flag).
- K∈{2,3,4,5} sweep test across 3 v1 tasks at `tests/test_recovery_calibration.py`.

Out of scope:
- OG / heatmap PNG export — Phase 10.
- Per-cell drilldown to `TraceExplorer` — Phase 11+.
- Multi-seed / multi-model heatmap views — TODO 2 territory.
- Heatmap aggregation across spike/dev artifact runs — silently excluded by baseline filter (D-57).
- Frontend page-state / status-strip changes — Phase 8 is the locked rendering layer.

</domain>

<decisions>
## Implementation Decisions

### Heatmap data API surface
- **D-52:** **`GET /api/race/heatmap`** — new dedicated aggregate endpoint. Backend buckets by `(HardnessType, lane)` server-side and returns render-ready cells. Frontend renders without recomputation.
  - **Why:** Bucketization in Python keeps `HardnessProfile` + per-fault tag logic colocated with the classifier (Phase 7 D-31..D-37). Frontend stays thin; one cache lives server-side instead of per-tab.
- **D-53:** **Minimal cell shape** — each cell is `{hardness_type, lane, dominant_tag, recovery_rate: {num, den}, sample_run_id}`. UIRACE-01 needs color (via `failureTagColor[dominant_tag]`) + icon + pattern fill + recovery_rate string (`"12/15"` is `${num}/${den}` UI-formatted) + cell focus link. Nothing else.
  - **Why:** Full tag distribution payload doubles the response size for a v1 view that has no breakdown UI; promote later if Phase 11+ adds a hover-distribution view. `sample_run_id` covers the locked footer "pinned task IDs" hand-off and gives Phase 11+ a free deep-link.

### Heatmap caching
- **D-54:** **Process-local in-memory dict cache**, keyed by `(model, seed, task_ids_tuple)`. Invalidated on `race_done` (subscribe to `ws.MANAGER` publish, or direct call from harness post-race_done — researcher's pick). First post-race request rebuilds from `data/runs/`.
  - **Why:** v1 corpus is bounded (n=5 × 3 lanes × 3 tasks ≤ 45 runs); rebuild cost is trivially absorbed at race_done boundary, not per-GET. No disk writes, no stale-after-restart concern (warm-fill on first GET). ETag/HTTP-cache layered on top is optional optimization (deferred).

### Heatmap aggregation scope
- **D-55:** **Pinned-baseline filter** — heatmap aggregates only runs matching the locked v1 baseline: `model=claude-sonnet-4-6`, `seed=42`, `task_ids ∈ {summarize_repo, negotiate_meeting, book_travel}`. Spike runs, future seeds, off-task experiments do **not** contribute cells.
  - **Why:** Footer promises `model · seed · pinned task IDs` (HEAT-02). The footer is the contract; aggregation must honor it. Heterogeneous cells from dev seed-drift would silently corrupt the closing artifact.
- **D-56:** **`HEATMAP_BASELINE` module constant** in `src/a2a_vs_mcp/race/config.py` (create if absent). Single source of truth for the pinned (model, seed, task_ids). Footer reads from it. Aggregator filters from it. Cache key derived from it.
  - **Why:** Existing v1 baseline values already exist in scattered places (harness D-38 `model=claude-sonnet-4-6, seed=42`; tasks list in `race/tasks/`). Promoting to one named constant kills drift; mirrors Phase 6 D-12 / Phase 7 D-28 startup-validator pattern.
- **D-57:** **Off-baseline runs silently excluded** from `/api/race/heatmap` aggregation. Same runs remain **fully loadable** via `/race/<run_id>` replay (replay reads disk regardless of pinned filter). No warning log, no visual marker.
  - **Why:** Heatmap is the curated closing artifact (UIRACE pill: "directional · n=3 tasks · v1"); replay is the per-run forensic surface. They have different audiences and different rules. Logging every off-baseline run during a multi-week dev cycle becomes noise; visual markers contaminate the screenshot demo grabs.

### Claude's Discretion (researcher / planner picks)
- **Replay tag computation (HEAT-03)** — Backend re-runs Python `Detector(K=3)` over the recorded ndjson trace and ships pre-classified per-fault tags vs ship raw events and JS Detector port re-derives vs serve persisted tags from the original recording. D-33 (Phase 7) requires replay-symmetric tags by construction; whichever approach the researcher picks must satisfy the two-layer fixture test. Recommendation surface to researcher: re-running `Detector` server-side reuses the locked Python implementation (single source of truth), avoids JS port drift, and the fixture test then asserts `replay_tags == record_tags`.
- **K=3 calibration fixture format (HEAT-04)** — Fictional traces from master design §The Assignment can live as inline pytest parametrize data, ndjson under `tests/race/fixtures/calibration/<task_id>.json`, or YAML. Test parametrization can be one test per `(task, K)` pair or a single table-driven sweep. Either is acceptable; planner picks for ergonomics. Required: K=3 must produce the expected tag for every fictional trace across all 3 tasks; K∈{2,4,5} variance is asserted (the "calibration" claim — K=3 is locked because alternatives drift).
- **Two-layer fixture test mechanism** — `pytest --update-snapshots` flag can be a custom pytest plugin, `pytest-snapshot`, `syrupy`, or hand-rolled. Researcher picks based on existing test deps + Phase 7 fixture conventions.
- **Cache invalidation transport** — `ws.MANAGER.publish(race_done)` listener vs direct callback registered by harness vs file-watcher on `data/runs/` mtime. All produce the same observable behavior; researcher picks for coupling preference.
- **HardnessFailureHeatmap.tsx vs HeatmapScaffold.tsx** — replace the Phase 8 stub, extend it, or wrap it. Phase 8 left this open (D-46 only locks the rendering primitive: CSS Grid + DOM cells). Planner picks; either way the legend strip + footer must read from the API payload (not hardcoded) so D-56 baseline drives them.
- **Aggregator module location** — `src/a2a_vs_mcp/race/heatmap.py`, or extending `race/metrics.py`, or a `serve_ui.py`-local helper. Implementation detail.

### Folded Todos
- **TODO 8** — K=3 multi-task calibration. Promoted into v2.0 (PROJECT.md). HEAT-04 closes this todo on phase verification.

### Plan-phase additions (2026-04-29, locked during /gsd-plan-phase 9)
- **D-58:** **Add `run_meta` event to ndjson trace.** Harness emits `run_meta {model, seed, task_id, baseline_version}` as the first event of every run. Heatmap aggregator reads `run_meta` per run for D-55 baseline filter; replay endpoint preserves it. Backfill is not required — pre-D-58 runs are silently excluded by D-57 (no `run_meta` ⇒ off-baseline).
  - **Why:** Run files lack a model/seed envelope today; without `run_meta` the baseline filter is a no-op and footer (model · seed · pinned task IDs) cannot honor D-55. Long-term correct design vs lazy "assume all baseline" hack.
- **D-59:** **Defer `RaceEvent.type` (frontend) vs `event_type` (backend ndjson) normalization to a later phase.** HardnessFailureHeatmap reads aggregated cells, not raw events; replay endpoint returns trace as-is so the existing `useRaceReplay` typed stub is satisfied without a normalization pass. The mismatch becomes load-bearing only when a future phase reads raw events on the frontend.
  - **Why:** Phase 8 didn't trip on it; in-scope Phase 9 surfaces (heatmap cells + replay payload pass-through) don't either. Lower risk to defer than to widen Phase 9 scope.
- **D-60:** **Skip `/gsd-ui-phase 9` for the heatmap UI.** Phase 8 UI-SPEC + ROADMAP §Phase 9 success criteria #1+#2 + this CONTEXT D-53 cell shape already specify the heatmap visual contract (rows × columns, cell composition, legend strip, footer). HardnessFailureHeatmap.tsx is a data-wiring upgrade of HeatmapScaffold.tsx, not a new design.
  - **Why:** Visual contract is fully covered upstream; running ui-phase would duplicate locked decisions and add a step. Plan-checker still verifies cell markup against D-46 (CSS Grid + role=gridcell, failureTagColor lookup).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 9 requirements + roadmap
- `.planning/REQUIREMENTS.md` §HEAT — HEAT-01..HEAT-04 verbatim acceptance criteria.
- `.planning/ROADMAP.md` §"Phase 9: Heatmap, Replay & K=3 Calibration" — 4 success criteria.
- `.planning/STATE.md` — Phase 8 closed; v2.0 milestone position.

### Master design (authoritative)
- `~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-design-20260427-193227.md`
  - §Heatmap (closing artifact) — `HardnessFailureHeatmap.tsx` row/column contract; "directional · n=3 tasks · v1" pill.
  - §Heatmap card composition — top-strip pill, legend, grid, footer (model · seed · pinned task IDs).
  - §Heatmap collapse rule — `kept_going_*` collapse for display-only; recovery_rate denominator counts separately.
  - §Replay & TraceRecorder audit — `/race/<run_id>` reads `data/runs/<run_id>.json`, no live LLM.
  - §Recovery detection — full state machine pseudocode + K=3 turn window + 5 terminal tags.
  - §Distribution Plan — two-layer fixture test contract (per-run tag snapshot + `--update-snapshots`).
- `~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-eng-review-test-plan-20260427-224635.md` — Phase 9 test obligations: K∈{2,3,4,5} sweep on 3 tasks, replay determinism fixture.

### Upstream phase decisions (do not re-derive)
- `.planning/phases/06-tracerecorder-schema-gate-race-foundation/06-CONTEXT.md` — D-01..D-18 (RunWriter arbiter, ndjson schema v1.0, replay loader stub, FaultKind enum).
- `.planning/phases/07-race-backend-lanes-harness-recovery/07-CONTEXT.md` — D-19..D-43, especially:
  - **D-31..D-34** — `Detector(K=3)` ownership, replay-symmetry-by-construction, terminal tag rules.
  - **D-35..D-37** — `failure_mode_classifier` + 6 templates + characteristic_event lookup.
  - **D-38..D-39** — harness model/seed locks, `race_done` emission.
  - **D-41** — `fault_observed` payload includes `wasted_tokens` (NEVER_COALESCE).
- `.planning/phases/08-race-page-ui-visual-contract/08-CONTEXT.md` — D-44..D-51, especially:
  - **D-46** — heatmap render = CSS Grid + DOM `role="gridcell"` cells; `failureTagColor` map drives `backgroundColor`; cell radius=0.
  - **D-47** — heatmap-empty state preserves grid scaffold; **never unmounts**. Phase 9 fills cells without breaking this.
  - **D-48** — replay = separate route `/race/<run_id>`; same `RacePage` component flips data source on route param.
- `.planning/phases/08-race-page-ui-visual-contract/08-VERIFICATION.md` — what Phase 8 actually shipped (267 frontend tests, 12 page-state matrix, replay scrubber).

### Existing code Phase 9 reuses verbatim
- `src/a2a_vs_mcp/race/classifier.py` — `Detector(K)` class + `failure_mode_classifier`. **Single source of truth for K=3 detection.** HEAT-04 sweep parametrizes `Detector(K=k)`; HEAT-03 replay re-instantiates `Detector(K=3)` per D-33.
- `src/a2a_vs_mcp/race/replay.py` — `load_run(run_id, runs_dir)` + `_validate_run_id` regex `^[A-Za-z0-9_-]{1,64}$`. Phase 9 replay endpoint must reuse the validator (path-traversal guard).
- `src/a2a_vs_mcp/race/runs.py` — `RUNS_DIR` constant; aggregator scans this directory.
- `src/a2a_vs_mcp/race/ws.py` — `MANAGER` (ConnectionManager) for `race_done` event hook (D-54 cache invalidation).
- `src/a2a_vs_mcp/race/types.py` — `HardnessType` StrEnum (4 v1 values), `HardnessProfile` dataclass.
- `src/a2a_vs_mcp/race/tasks/<id>/task_config.yaml` — per-task `HardnessProfile` (drives heatmap row eligibility per Phase 7 D-30 coverage rule).
- `src/a2a_vs_mcp/web.py` — `/api/race/ws` mount point at line 857; new endpoints land here.

### Existing frontend assets
- `frontend/src/features/race/components/HeatmapScaffold.tsx` — Phase 8 empty-grid renderer. Phase 9 either replaces or extends.
- `frontend/src/features/race/hooks/useRaceReplay.ts` + `frontend/src/lib/api/client.ts` (`fetchRaceReplay`, `RaceReplayPayload`, `isValidRunId`) — Phase 8 client signature already wired; Phase 9 backend must satisfy `{run_id, events, schema_version}`.
- `frontend/src/lib/trace/eventColors.ts` — `failureTagColor` map (UIRACE-04, 5 entries). Heatmap cell `backgroundColor` reads from here.
- `frontend/src/lib/types/race.ts` — extend with `HeatmapCell` + `HeatmapPayload` types.

### Test infrastructure
- `tests/race/` — 37 existing race tests (Phase 6/7); Phase 9 adds calibration sweep + replay fixture.
- `tests/test_recovery_calibration.py` (new, per ROADMAP success criterion 4) — K∈{2,3,4,5} sweep across 3 tasks.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- **`Detector(K)` class** (`race/classifier.py`): K is already a constructor arg. HEAT-04 calibration sweep is `Detector(K=k) for k in (2,3,4,5)` over fictional traces — no class change needed.
- **`load_run` + `_validate_run_id`** (`race/replay.py`): replay endpoint wraps these directly. Path-traversal guard already present and tested.
- **`MANAGER` ConnectionManager** (`race/ws.py`): publishes `race_done` events. Cache invalidator registers as a listener (or harness calls invalidator + publish concurrently).
- **`HardnessProfile`** (`race/types.py`): per-task hardness-type set. Heatmap row eligibility = union of all baseline tasks' `HardnessProfile.types`.
- **`fetchRaceReplay` + `RaceReplayPayload`** (`frontend/src/lib/api/client.ts`): Phase 8 stubbed the typed signature; Phase 9 backend implements `/api/race/runs/<run_id>/trace` to satisfy `{run_id, events, schema_version}`.

### Established Patterns
- **Module-level constant for locked config** (Phase 7 D-28 Pydantic validators, Phase 6 D-12 `FaultKind`) — `HEATMAP_BASELINE` follows the same shape.
- **In-process cache + invalidation hook** (Phase 6 ConnectionManager publishes; subscribers consume) — heatmap cache invalidator is a new subscriber on the same primitive.
- **Frontend `fetch*` + `is*Valid` validator + payload type** in `lib/api/client.ts` — Phase 9 adds `fetchRaceHeatmap` + `HeatmapPayload` mirroring `fetchRaceReplay`.

### Integration Points
- **`web.py` route mount** — new routes go alongside `/api/race/ws` (line 857). Both heatmap and replay GETs are FastAPI route decorators.
- **Harness ↔ cache invalidator** — harness emits `race_done` already (Phase 7 D-39); invalidation is a one-liner subscriber on `MANAGER` or a direct callback.
- **`HeatmapScaffold` ↔ `HardnessFailureHeatmap`** — Phase 8 shipped the empty-state grid; Phase 9 either fills it via API data prop or replaces with a sibling component. Either way, `failureTagColor` lookup and `role="gridcell"` markup carry forward (D-46).
- **Footer ↔ baseline payload** — backend ships `{baseline: {model, seed, task_ids}}` alongside `cells: [...]` so the footer is data-driven, not a hardcoded string.

</code_context>

<specifics>
## Specific Ideas

- **Heatmap is data-driven, not stub-filled.** The Phase 8 scaffold renders the grid; Phase 9 ships the cells. The empty-state contract (D-47) is preserved by treating "zero matching baseline runs" as the empty state, **not** by mounting a different component.
- **Replay symmetry is a fixture test, not an architectural debate.** D-33 already mandates by-construction symmetry via `Detector` reuse. The two-layer fixture test asserts: (a) per-run tag snapshot matches the recorded run's tags, (b) `--update-snapshots` regenerates after intentional rule changes.
- **K=3 is locked, calibration sweep proves it.** HEAT-04 doesn't pick K — it asserts that K=3 produces the expected tag for every fictional trace. K∈{2,4,5} cells in the sweep matrix are negative controls demonstrating drift at off-K values.
- **Pinned baseline kills demo drift.** During a 2-week race-demo iteration cycle, devs will run experiments at `seed=99` or `model=claude-haiku-*`. D-55/D-57 ensure those don't pollute the shareable closing artifact.
- **Footer is contract.** "model · seed · pinned task IDs" reads from `HEATMAP_BASELINE` directly. If a future maintainer changes the constant, the footer string changes — the demo never silently lies about what it aggregated.
- **Cache key includes `task_ids_tuple` order-independently.** Sorted tuple (`tuple(sorted(task_ids))`) so `(a, b, c)` and `(c, b, a)` hit the same cache entry. Detail; researcher will spot it.

</specifics>

<deferred>
## Deferred Ideas

- **Per-cell distribution tooltip** — D-53 keeps cell shape minimal. Promote to v1.1 / Phase 11+ when a hover-breakdown UI lands.
- **HTTP-level ETag/Last-Modified caching** — D-54 in-memory dict is sufficient for v1 traffic; layer on top later if profiling surfaces a need.
- **Per-cell drilldown to TraceExplorer** — `sample_run_id` is already on cell shape; UI wiring is Phase 11+ scope.
- **Multi-seed / multi-model heatmap views** — TODO 2 (multi-seed benchmark). Pinned baseline filter (D-55) is the v1 contract; multi-baseline rendering is a v2.1+ feature.
- **Off-baseline run warning surface** — D-57 silently excludes; if dev-cycle confusion arises, promote to a startup audit log or `/api/race/health` channel later.
- **Aggregator persistence to disk** — D-54 in-memory cache is process-local. Persisting `data/race/heatmap.json` is rejected for v1 (dev workflow hits it less than every restart anyway).

### Reviewed Todos (not folded)
None — no other TODOS.md items match Phase 9 scope. (TODO 9 HMAC-signed PNG URLs is Phase 10; TODO 1/2/4/6/7 unrelated.)

</deferred>

---

*Phase: 9-heatmap-replay-k3-calibration*
*Context gathered: 2026-04-29*
