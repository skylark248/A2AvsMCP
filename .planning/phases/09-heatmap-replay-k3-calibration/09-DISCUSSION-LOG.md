# Phase 9 Discussion Log

**Date:** 2026-04-29
**Mode:** discuss (default; no flags)
**Phase:** 09-heatmap-replay-k3-calibration

## Areas Selected by User

User picked 2 of 4 presented areas:
- ☑ Heatmap data API surface
- ☑ Heatmap aggregation scope
- ☐ Replay tag computation — left to Claude's discretion (researcher pick; D-33 already locks symmetry-by-construction)
- ☐ K=3 calibration test shape — left to Claude's discretion (planner ergonomics call)

## Q&A — Heatmap data API surface

### Q1. How should heatmap cells reach the frontend?
- **Options presented:**
  1. GET /api/race/heatmap (Recommended) — dedicated aggregate endpoint
  2. GET /api/race/runs (list) + JS aggregate
  3. Precomputed data/race/heatmap.json
- **User selected:** GET /api/race/heatmap (Recommended)
- **Locked as:** D-52

### Q2. Cell content shape — what does each /api/race/heatmap cell carry?
- **Options presented:**
  1. Minimal — render-ready (Recommended) — `{hardness_type, lane, dominant_tag, recovery_rate, sample_run_id}`
  2. Full distribution — raw tag tally per cell
  3. Minimal + per-cell trace links — array of (run_id, fault_id) per cell
- **User selected:** Minimal — render-ready (Recommended)
- **Locked as:** D-53

### Q3. Cache strategy for /api/race/heatmap?
- **Options presented:**
  1. In-memory dict, invalidate on race_done (Recommended)
  2. Compute-every-request
  3. ETag/Last-Modified on data/runs/ mtime
- **User selected:** In-memory dict, invalidate on race_done (Recommended)
- **Locked as:** D-54

## Q&A — Heatmap aggregation scope

### Q4. Which runs should the heatmap aggregate?
- **Options presented:**
  1. Pinned (model, seed, task_ids) only (Recommended)
  2. Most-recent N race_done batches
  3. All runs in data/runs/
- **User selected:** Pinned (model, seed, task_ids) only (Recommended)
- **Locked as:** D-55

### Q5. Where does the pinned (model, seed, task_ids) baseline live?
- **Options presented:**
  1. Module constant in race/config (Recommended) — `HEATMAP_BASELINE`
  2. Server config env vars
  3. Inline in serve_ui.py route handler
- **User selected:** Module constant in race/config (Recommended)
- **Locked as:** D-56

### Q6. Behavior when a recorded run mismatches the pinned baseline?
- **Options presented:**
  1. Silently exclude from aggregation (Recommended)
  2. Exclude + log warning
  3. Include with visual marker
- **User selected:** Silently exclude from aggregation (Recommended)
- **Locked as:** D-57

## Claude's Discretion (deferred to researcher / planner)

- Replay tag computation (HEAT-03) approach — backend re-run Detector vs JS port vs persisted-tags. D-33 mandates symmetry; researcher picks mechanism. Recommendation surface: backend re-run.
- K=3 calibration fixture format (HEAT-04) — inline parametrize vs YAML vs ndjson; one-test-per-(task,K) vs table-driven sweep.
- Two-layer fixture test plugin choice — `pytest-snapshot`, `syrupy`, or hand-rolled.
- Cache invalidation transport — `MANAGER.publish` listener vs direct harness callback vs file-watcher.
- `HardnessFailureHeatmap.tsx` vs `HeatmapScaffold.tsx` — replace, extend, or wrap.
- Aggregator module location — `race/heatmap.py` vs extending `race/metrics.py` vs serve_ui-local.

## Deferred Ideas Captured

- Per-cell distribution tooltip — Phase 11+
- HTTP ETag/Last-Modified — second-order optimization
- Per-cell TraceExplorer drilldown — Phase 11+
- Multi-seed / multi-model heatmap views — TODO 2 / v2.1+
- Off-baseline run warning surface — promote if dev confusion surfaces
- Aggregator disk persistence — rejected for v1

## Folded Todos

- TODO 8 (K=3 multi-task calibration) — promoted into v2.0 roadmap; closed by HEAT-04 verification.

---

*Discussion duration: ~6 questions across 2 areas. Default mode (no flags).*
