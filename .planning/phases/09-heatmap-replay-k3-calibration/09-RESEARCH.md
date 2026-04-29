# Phase 9: Heatmap, Replay & K=3 Calibration — Research

**Researched:** 2026-04-29
**Domain:** Race-demo data backend + frontend wiring + recovery-rule calibration
**Confidence:** HIGH (all upstream code already shipped + locked; gap is pure wiring)

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-52** — `GET /api/race/heatmap` is the new dedicated aggregate endpoint. Backend buckets by `(HardnessType, lane)` server-side; frontend renders without recomputation.
- **D-53** — Minimal cell shape: `{hardness_type, lane, dominant_tag, recovery_rate: {num, den}, sample_run_id}`. No tag distribution, no per-fault array.
- **D-54** — In-memory dict cache keyed by `(model, seed, task_ids_tuple)`, invalidated on `race_done`. First post-race GET rebuilds from `data/runs/`.
- **D-55** — Heatmap aggregates only runs matching the pinned baseline: `model=claude-sonnet-4-6`, `seed=42`, `task_ids ∈ {summarize_repo, negotiate_meeting, book_travel}`.
- **D-56** — `HEATMAP_BASELINE` module constant lives in `src/a2a_vs_mcp/race/config.py` (file to be created — see Files section). Single source of truth for baseline tuple.
- **D-57** — Off-baseline runs silently excluded. No log, no visual marker. Replay endpoint still loads them.

### Claude's Discretion (researcher / planner picks — recommendations below)

- Replay tag computation (HEAT-03): re-run `Detector(K=3)` server-side vs ship raw vs persist tags. **Recommendation: backend re-run via `Detector` reuse (D-33 symmetry-by-construction).** See §"Replay tag computation".
- K=3 calibration fixture format (HEAT-04): inline parametrize / YAML / ndjson. **Recommendation: reuse existing `tests/race/fixtures/traces/*.json` fixture format with new `summarize_repo_*`-style fictional traces.** See §"K=3 calibration fixture".
- Two-layer fixture test plugin: `pytest-snapshot` / `syrupy` / hand-rolled. **Recommendation: hand-rolled — no snapshot infra exists today and the fixture file IS the snapshot.** See §"Snapshot test plugin".
- Cache invalidation transport: `MANAGER.publish` listener / direct callback / file-watcher. **Recommendation: direct callback registered by harness OR a tiny `cache.invalidate()` call in `run_race` after the `race_done` emit.** See §"Cache invalidation transport".
- `HardnessFailureHeatmap.tsx` vs `HeatmapScaffold.tsx`: replace / extend / wrap. **Recommendation: NEW thin wrapper `HardnessFailureHeatmap.tsx` that fetches + transforms cells then renders `<HeatmapScaffold cells={...} />`. Phase 8 props shape stays untouched.** See §"Heatmap component upgrade".
- Aggregator module location: `race/heatmap.py` / extend `race/metrics.py` / serve_ui-local. **Recommendation: new `src/a2a_vs_mcp/race/heatmap.py` — heatmap is a distinct subsystem and `metrics.py` is already loaded with per-run aggregation.**

### Deferred Ideas (OUT OF SCOPE)

- Per-cell distribution tooltip — Phase 11+
- HTTP ETag/Last-Modified caching — second-order optimization
- Per-cell drilldown to TraceExplorer — Phase 11+ (`sample_run_id` is on cell shape but no UI wiring)
- Multi-seed / multi-model heatmap views — TODO 2 / v2.1+
- Off-baseline run warning surface — promote only if dev confusion surfaces
- Aggregator persistence to disk — rejected for v1

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| **HEAT-01** | `HardnessFailureHeatmap.tsx` rows=HardnessType cols=lane; cells show dominant_tag color + icon + pattern fill + recovery rate; cells keyboard-focusable; "directional · n=3 tasks · v1" pill in `secondary.main` | §Heatmap component upgrade — wrap `HeatmapScaffold` (already 4-channel A11y compliant); add directional pill above grid |
| **HEAT-02** | Heatmap legend strip always visible (5 inline pills); footer shows model · seed · pinned task IDs | Backend ships `{baseline: {model, seed, task_ids}}` alongside `cells: [...]` in `/api/race/heatmap` payload; footer reads payload, not hardcoded |
| **HEAT-03** | `/race/<run_id>` replay reads `data/runs/<run_id>.json`; recovery-rule state machine produces identical per-run tags; verified by two-layer fixture test (snapshot + `--update-snapshots` flag) | §Replay tag computation + §Replay endpoint shape — re-run `Detector(K=3)` server-side over loaded ndjson; fixture test asserts `replay_tags == record_tags` |
| **HEAT-04** | K∈{2,3,4,5} sweep over §The Assignment fictional traces for all 3 v1 tasks confirms K=3 produces expected tag for every trace | §K=3 calibration fixture — pytest.parametrize over (task, K, expected_tag) tuples driven from `tests/race/fixtures/traces/`; `Detector(K)` is already constructor-arg parametrizable |

</phase_requirements>

## Summary

- **All upstream primitives are already shipped.** `Detector(K=3)`, `load_run()`, `_validate_run_id()`, `MANAGER`, `HeatmapScaffold`, `failureTagColor`, `fetchRaceReplay`/`RaceReplayPayload` types, `RUNS_DIR`, `events_for_lane`. Phase 9 is wiring + 2 tests + 2 routes + 1 module constant + 1 frontend wrapper. Confidence is high precisely because nothing is being invented.
- **`/api/race/runs/{run_id}/trace` does not exist yet** (`web.py` line 857 has only `/api/race/ws`). The frontend `fetchRaceReplay` typed stub already targets that exact path with `RaceReplayPayload = {run_id, events, schema_version}`. Backend handler is ~10 lines: validate run_id, `load_run(run_id, RUNS_DIR)`, return `{run_id, events, schema_version: "1.0"}`.
- **Replay symmetry is by construction, not by snapshot.** Runners already feed events through `Detector(K=3)` (`runners/{pure_mcp,pure_a2a,hybrid}.py:75/95/166`). Replay re-feeds the SAME events through a fresh `Detector(K=3)` — outputs are mathematically identical. The two-layer fixture test asserts this; it does NOT need a snapshot library because the fixture trace files in `tests/race/fixtures/traces/` already carry `expected_terminal_tag`.
- **Heatmap aggregation is bounded and trivial.** Pinned baseline = 3 tasks × 3 lanes × n=5 = 45 runs maximum. In-memory rebuild on `race_done` is microseconds. Cache key = `(model, seed, tuple(sorted(task_ids)))` — order-independent per CONTEXT.md §Specifics.
- **K=3 calibration sweep is parametrize-driven, not snapshot-driven.** `Detector(K)` accepts K as a constructor arg already. Test = `@pytest.mark.parametrize("k,task,expected_tag", [...])`. The 9 existing fixture traces in `tests/race/fixtures/traces/` provide the v1 corpus; the test confirms K=3 hits expected for all 9 and that K∈{2,4,5} drift is observable on at least one fixture per task.
- **No external libraries needed.** No `pytest-snapshot`/`syrupy` install (handrolled `--update-snapshots` flag against fixture file). No new frontend deps. Reuses `pyyaml`, `pydantic`, `fastapi`, `pytest>=8.0`, `pytest-asyncio>=0.24` already in pyproject.toml.

**Primary recommendation:** Plan as 4 plans across 2 waves. W1 lands `race/config.py` constant + `race/heatmap.py` aggregator + replay route + heatmap route in parallel (server-side, all independent). W2 lands `HardnessFailureHeatmap.tsx` (depends on backend route shape) + `tests/test_recovery_calibration.py` + `tests/race/test_replay_symmetry.py` (depends on nothing — can parallelize with W1 if scheduler allows).

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Heatmap cell aggregation | API / Backend (`race/heatmap.py`) | — | Bucketization + baseline filter colocate with classifier; one cache lives server-side (D-52) |
| Heatmap baseline constant | API / Backend (`race/config.py`) | — | D-56 single source of truth; both aggregator filter + footer payload read from it |
| `HEATMAP_BASELINE` cache | API / Backend (in-process dict) | — | Process-local; v1 corpus is small; rebuild on `race_done` boundary (D-54) |
| Replay endpoint (read disk → return events) | API / Backend (`web.py`) | — | Reuses `replay.load_run` + `_validate_run_id`; no live LLM (HEAT-03) |
| `Detector(K=3)` re-firing on replay | API / Backend (`race/classifier.py`) | — | D-33 symmetry-by-construction; replay test re-feeds events into Detector |
| K=3 calibration sweep | Test layer (`tests/test_recovery_calibration.py`) | — | Pure pytest.parametrize over `Detector(K)` constructor; no UI / no API surface |
| Heatmap rendering (grid + 4-channel cells) | Frontend (`HeatmapScaffold` — already shipped) | — | Phase 8 owns grid layout, A11y, focus-visible, color/icon/fraction/sr-only |
| Heatmap data wiring (fetch + transform + footer + legend pill) | Frontend (`HardnessFailureHeatmap.tsx` NEW) | — | Wraps `HeatmapScaffold`; owns API shape → `HeatmapCells` mapping |
| Replay scrubber UI | Frontend (`ReplayScrubber` — already shipped) | — | Phase 8 owns Slider + 200ms throttle aria-live |
| Replay data fetch | Frontend (`useRaceReplay` — already shipped) | — | Phase 8 owns hook + `let active = true` cleanup pattern |

## Per-Requirement Findings

### HEAT-01 — `HardnessFailureHeatmap.tsx`

**Recommendation:** NEW component `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` that wraps the Phase-8-shipped `HeatmapScaffold`. The wrapper owns:

1. `useHeatmap()` data hook (or inline `useEffect` + `fetchRaceHeatmap`) — fetches `/api/race/heatmap`, returns `{cells, baseline, loading, error}`.
2. Transform from API shape `Array<{hardness_type, lane, dominant_tag, recovery_rate, sample_run_id}>` to `HeatmapScaffold`'s `HeatmapCells = Partial<Record<HardnessType, Partial<Record<RaceLane, HeatmapCell>>>>` shape (where `HeatmapCell = {tag, recoveryFraction}`).
3. Recovery fraction derivation: `${recovery_rate.num}/${recovery_rate.den}` (CONTEXT.md D-53 spells `12/15` as the visible token).
4. "directional · n=3 tasks · v1" pill: `<Chip color="secondary" label="directional · n=3 tasks · v1" />` rendered ABOVE the `<HeatmapScaffold>`. UI-SPEC verbatim per ROADMAP success criterion 1.
5. Render `<HeatmapScaffold cells={transformedCells} />`.
6. Footer + legend strip — see HEAT-02.

**Phase 8 contract preserved:** All 4 channels (color/icon/fraction/sr-only label) come from `HeatmapScaffold` unchanged. UIRACE-04 forbids color as sole channel — already enforced (`08-05-SUMMARY.md` line 78-87). HardnessFailureHeatmap MUST NOT bypass `HeatmapScaffold`'s rendering primitive (D-46).

**Pitfall:** `HeatmapScaffold` types its hardness rows as `multi_source_synthesis` (long form) but `race/types.py:26` defines the enum value as `"multi_source"` (short). The mismatch must be resolved in the transform layer — backend ships `"multi_source"` (Python source of truth); the wrapper maps to `"multi_source_synthesis"` (frontend display key) in the fanout. **Confidence: HIGH** — verified by reading both files. **Recommendation:** Either (a) align the frontend constant to `multi_source` in `HeatmapScaffold.tsx` Plan 09 task, or (b) map in the wrapper. Option (b) is lower-blast-radius since Phase 8 is already verified-PASS at `multi_source_synthesis`.

### HEAT-02 — Legend strip + footer

**Legend strip (5 inline pills):** Renders 5 `<Chip>` (one per `FailureTag` from `failureTagColor` map). Each chip uses the tag's `Icon` + `label` + `bg` colour. Always visible — even in empty state. The chips are static (don't read API data); they describe the colour key. **Source:** `frontend/src/lib/trace/eventColors.ts:54` already exports the 5-entry `failureTagColor` map. **Confidence: HIGH.**

**Footer (model · seed · pinned task IDs):** Reads from API payload `{baseline: {model, seed, task_ids}}` shipped alongside `cells`. Renders as a `<Typography variant="caption">` line below the grid. Format: `claude-sonnet-4-6 · 42 · summarize_repo, negotiate_meeting, book_travel` (interpolated from baseline). **Critical: footer must be data-driven, not hardcoded** — CONTEXT.md §Specifics lockdown so `HEATMAP_BASELINE` constant changes propagate visually.

### HEAT-03 — Replay route + state machine symmetry

**Backend route (`web.py`):**

```python
@app.get("/api/race/runs/{run_id}/trace")
async def race_run_trace(run_id: str) -> dict:
    try:
        _validate_run_id(run_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    try:
        events = load_run(run_id, RUNS_DIR)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="run not found")
    return {"run_id": run_id, "events": events, "schema_version": "1.0"}
```

Imports already exist (`web.py:43-44`). Frontend client `fetchRaceReplay` already calls this exact path (`client.ts:160`).

**Replay symmetry mechanism — re-run `Detector` server-side:** D-33 mandates symmetry by construction. The runners (`runners/pure_mcp.py:95`, `pure_a2a.py:166`, `hybrid.py:75`) instantiate `Detector(fault_id, fault_kind, target, fault_inject_turn=event.get("turn_index", 0))` — defaulting K to `K_DEFAULT=3`. **The replay path simply re-instantiates `Detector(...)` with K=3 over the loaded events.** Same code path, same regex, same finalization rules → mathematically identical tags.

**Two-layer fixture test:** Live in `tests/race/test_replay_symmetry.py`. Walk every fixture in `tests/race/fixtures/traces/*.json` (already 9 files, one per (task × tag) crossing). For each:

1. Load fixture → `events`, `expected_terminal_tag`, `score_pass` keys.
2. Find `fault_injected` event(s) → instantiate `Detector(fault_id, fault_kind, target, fault_inject_turn, K=3)`.
3. Feed every subsequent event into `detector.consume(event)` until OBSERVED or `done`.
4. Call `detector.finalize_at_done(score_pass)` → assert `== expected_terminal_tag`.

**Layer 2 (`--update-snapshots` flag):** Hand-rolled. The fixture file IS the snapshot. When the rule changes intentionally, run `pytest tests/race/test_replay_symmetry.py --update-snapshots` and the test (a) computes the actual tag, (b) writes it back to `expected_terminal_tag` in the fixture JSON, (c) skips the assertion. Default mode: assert. Plumbing: `pytest_addoption` in `tests/conftest.py` adds `--update-snapshots` flag; the test reads it via `request.config.getoption("--update-snapshots")`. **No external dependency required.**

### HEAT-04 — K∈{2,3,4,5} calibration sweep

**Recommendation:** `tests/test_recovery_calibration.py` parametrizes `Detector(K=k)` over (task_id × k × fixture_path × expected_tag). The 9 fixtures in `tests/race/fixtures/traces/` are the v1 corpus and are designed per task × terminal-tag. Test asserts:

1. **For k=3:** every fixture's computed terminal_tag matches its `expected_terminal_tag` field (the K=3 lock).
2. **For k∈{2,4,5}:** at least one fixture per task drifts (the calibration claim — K=3 is non-arbitrary). Drift = `Detector(K=k).finalize(...) != Detector(K=3).finalize(...)` on the same fixture. Expressed as a per-task `pytest.mark.xfail`-style assertion or a `set` comparison: `{k: tag(K=k, fixture) for k in [2,3,4,5]} | filter ≠ tag(K=3)` non-empty.

**Test skeleton:**

```python
import json, pathlib, pytest
from a2a_vs_mcp.race.classifier import Detector

FIXTURES = pathlib.Path(__file__).parent / "race" / "fixtures" / "traces"

@pytest.mark.parametrize("fixture_path", sorted(FIXTURES.glob("*.json")))
def test_k3_produces_expected_tag(fixture_path):
    fx = json.loads(fixture_path.read_text())
    tag = _replay_with_k(fx["events"], K=3, score_pass=fx["score_pass"])
    assert tag == fx["expected_terminal_tag"], f"{fixture_path.name} drifted at K=3"

@pytest.mark.parametrize("k", [2, 4, 5])
@pytest.mark.parametrize("task", ["summarize_repo", "negotiate_meeting", "book_travel"])
def test_off_k_drift_observed_per_task(k, task):
    """At least one fixture per task drifts when K≠3 — calibration evidence."""
    drifts = []
    for path in FIXTURES.glob(f"{task}_*.json"):
        fx = json.loads(path.read_text())
        tag_k3 = _replay_with_k(fx["events"], K=3, score_pass=fx["score_pass"])
        tag_kx = _replay_with_k(fx["events"], K=k, score_pass=fx["score_pass"])
        if tag_kx != tag_k3:
            drifts.append((path.name, tag_kx, tag_k3))
    assert drifts, f"No drift at K={k} for {task} — calibration claim unsupported"
```

`_replay_with_k(events, K, score_pass)` is a helper that walks events, finds `fault_injected`, builds `Detector(K=K)`, feeds remaining events, calls `finalize_at_done(score_pass)`. Same helper as the HEAT-03 fixture test — extract to `tests/race/_replay_helpers.py`. **Confidence: HIGH** — verified all 5 terminal-tag fixtures + 9 total fixtures exist (`book_travel_{gave_up,kept_going_to_failure,recovered}.json`, `negotiate_meeting_{indeterminate,kept_going,recovered}.json`, `summarize_repo_{gave_up,kept_going_silent,recovered}.json`).

**Open question:** §The Assignment "fictional traces" referenced in CONTEXT.md may contain MORE traces than the 9 currently in `tests/race/fixtures/traces/`. Read `~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-design-20260427-193227.md` §The Assignment during planning — if more fixtures are listed, add them. Today's 9 are sufficient to satisfy ROADMAP success criterion 4 ("expected tag for every trace") because every existing fixture already has `expected_terminal_tag`.

## Technical Approaches

### 1. Replay tag computation

**Decision: re-run `Detector(K=3)` server-side over the loaded ndjson trace.**

Why this approach wins:

- **D-33 mandates symmetry by construction.** Anything other than reusing the Python `Detector` class introduces a parallel implementation (JS port) or a stored-tag dependency (replay diverges if the tagging rule changes between record and replay) — both violate D-33.
- **Runners already do this exact thing live.** `src/a2a_vs_mcp/race/runners/pure_mcp.py:95` constructs `Detector(fault_id=event["fault_id"], fault_kind=event["fault_kind"], target=event["target"], fault_inject_turn=event.get("turn_index", 0))` — using `K_DEFAULT=3`. Replay just re-runs the same line over `load_run` output. Identical inputs → identical outputs (pure functions; D-33 guarantee).
- **Trace data shape supports it directly.** Verified by reading `data/runs/r-x.json` and the fixture files — events carry `fault_id`, `fault_kind`, `target`, `turn_index` on `fault_injected`; `tool_call`/`agent_msg` events have `turn_index`, `tool_name`, `status`, `content`. All inputs the `Detector.consume()` path needs (`classifier.py:103-133`).

What the replay endpoint does NOT need to do:

- **No tag persistence.** Tags are recomputed; not stored on disk.
- **No JS port.** Frontend doesn't run `Detector` — it just renders the trace. If the UI ever needs per-fault tags inline (Phase 11+ TraceExplorer), the backend can emit them as a derived field on the replay payload.
- **No live LLM.** HEAT-03 explicit: replay reads disk only.

**File: `src/a2a_vs_mcp/race/replay_symmetry.py`** (NEW, optional helper) — extract the `_replay_with_k(events, K, score_pass) -> tag` helper here so both `tests/race/test_replay_symmetry.py` and `tests/test_recovery_calibration.py` import it. Single source of truth for "given trace + K, produce terminal tag". Confidence: HIGH.

### 2. K=3 calibration fixture format

**Decision: reuse the existing `tests/race/fixtures/traces/*.json` format — one file per (task × terminal_tag).**

The 9 fixtures already in `tests/race/fixtures/traces/` ARE the §The Assignment fictional-trace corpus. Schema (verified):

```json
{
  "name": "summarize_repo_recovered",
  "lane": "pure_mcp",
  "task_id": "summarize_repo",
  "expected_terminal_tag": "recovered",
  "score_pass": true,
  "events": [...]
}
```

`expected_terminal_tag` is the assertion target. `score_pass` flows into `Detector.finalize_at_done(score_pass)`. **No format change needed.**

**Why not YAML / inline parametrize / ndjson:**

- YAML adds `pyyaml.safe_load` dependency on tests (already loaded at module level for tasks/loader.py, but adds noise). JSON aligns with the run-files format.
- Inline parametrize would couple the test code to specific event sequences — making a new fixture means editing test code. JSON keeps fixture content separate.
- ndjson loses the `expected_terminal_tag` + `score_pass` envelope keys. Single-object JSON keeps them inline.

**Action items for HEAT-04:**

- If §The Assignment lists fixtures not present in `tests/race/fixtures/traces/`, add them in the same envelope shape during planning.
- Confirm each task has fixtures covering enough terminal tags to make K-drift visible. Today's coverage:
  - `summarize_repo`: gave_up, kept_going_silent, recovered (3)
  - `negotiate_meeting`: indeterminate, kept_going, recovered (3)
  - `book_travel`: gave_up, kept_going_to_failure, recovered (3)

Drift detection requires at least one fixture where the OBSERVED window boundary matters (i.e., `cur_turn - fault_inject_turn ≈ 3`). If existing fixtures don't have such a near-boundary event, plan task SHOULD add a "near-K3-boundary" fixture per task to make K∈{2,4,5} drift observable.

### 3. Snapshot test plugin

**Decision: hand-roll. The fixture JSON file IS the snapshot.**

No snapshot library installed today (`grep snapshot/syrupy/pytest-snapshot` returned empty against pyproject.toml + tests/conftest.py). Adding one for two test files is over-engineering.

**Hand-rolled mechanism:**

`tests/conftest.py`:
```python
def pytest_addoption(parser):
    parser.addoption(
        "--update-snapshots", action="store_true", default=False,
        help="Rewrite expected_terminal_tag in fixture files instead of asserting"
    )
```

`tests/race/test_replay_symmetry.py`:
```python
def test_replay_symmetry(fixture_path, request):
    fx = json.loads(fixture_path.read_text())
    actual = _replay_with_k(fx["events"], K=3, score_pass=fx["score_pass"])
    if request.config.getoption("--update-snapshots"):
        fx["expected_terminal_tag"] = actual
        fixture_path.write_text(json.dumps(fx, indent=2))
        return
    assert actual == fx["expected_terminal_tag"]
```

**Why this beats `pytest-snapshot` / `syrupy`:**

- Zero new deps.
- The "snapshot file" is human-readable JSON with named keys (not opaque `.ambr` or `.snap` files).
- Fixture files double as documentation (event sequences are inline-readable).
- Plays nicely with git diffs — flag-bumped tag changes are reviewable as `expected_terminal_tag: "recovered" → "kept_going_to_failure"` in the JSON.

### 4. Heatmap component upgrade

**Decision: NEW thin wrapper `HardnessFailureHeatmap.tsx` over the Phase-8 `HeatmapScaffold`.**

Phase 8 SUMMARY (`08-05-SUMMARY.md`) explicitly anticipates this composition pattern: "Plan 06 will... wire `cells` from the heatmap data hook (Phase 9 HEAT-01/HEAT-02)" and `HeatmapScaffold` is exported with a `cells: HeatmapCells` prop that's already partial-typed for sparse data.

**Wrapper responsibilities:**

```tsx
// frontend/src/features/race/components/HardnessFailureHeatmap.tsx
import { HeatmapScaffold, type HeatmapCells, type HardnessType } from "./HeatmapScaffold";
import { Chip, Stack, Typography } from "@mui/material";
import { failureTagColor } from "../../../lib/trace/eventColors";
import { useEffect, useState } from "react";

interface HeatmapPayload {
  cells: Array<{
    hardness_type: string;     // "long_chain" | "rate_pressure" | "schema_variance" | "multi_source"
    lane: "pure_mcp" | "pure_a2a" | "hybrid";
    dominant_tag: FailureTag;
    recovery_rate: { num: number; den: number };
    sample_run_id: string;
  }>;
  baseline: { model: string; seed: number; task_ids: string[] };
}

export function HardnessFailureHeatmap() {
  const [data, setData] = useState<HeatmapPayload | null>(null);
  // ... fetch /api/race/heatmap, transform, render scaffold + legend + footer
}
```

**Transform from API to `HeatmapCells`:**

```ts
const cells: HeatmapCells = {};
for (const c of data.cells) {
  const row = c.hardness_type === "multi_source" ? "multi_source_synthesis" : c.hardness_type;
  cells[row as HardnessType] ??= {};
  cells[row as HardnessType]![c.lane] = {
    tag: c.dominant_tag,
    recoveryFraction: `${c.recovery_rate.num}/${c.recovery_rate.den}`,
  };
}
```

**RacePage.tsx integration:** Replace line 177 `<HeatmapScaffold cells={heatmapCells} />` with `<HardnessFailureHeatmap />` (wrapper owns its own cells; RacePage stops hardcoding empty `{}`). Lines 92-110 in RacePage become dead code — remove.

**Confidence: HIGH.** Verified by reading `RacePage.tsx:19,177` and `08-05-SUMMARY.md:140-142`.

### 5. Cache invalidation transport

**Decision: direct callback invoked by `harness.run_race` after the `race_done` ws_emitter call.**

Three options were on the table. Comparison:

| Option | Pros | Cons |
|--------|------|------|
| `MANAGER.publish` listener | Decoupled; cache module subscribes once | `MANAGER.publish` is async + per-(run_id, conn); not designed for module-wide subscriptions. Adds a new pub-sub primitive. |
| **Direct callback in harness** | Zero new primitives; tested by harness test | Harness imports `race/heatmap.py` (one extra module dep) |
| File-watcher on `data/runs/` mtime | Decoupled from harness | Adds inotify/watchdog dep; flaky on macOS/CI; fires on every batch flush, not on `race_done` |

The direct callback wins on simplicity. Implementation:

```python
# src/a2a_vs_mcp/race/harness.py — after the ws_emitter({"event_type": "race_done", ...}) line ~465:
from .heatmap import invalidate_cache
invalidate_cache()
```

`src/a2a_vs_mcp/race/heatmap.py`:
```python
_CACHE: dict[tuple, list[dict]] = {}

def invalidate_cache() -> None:
    _CACHE.clear()

def get_heatmap() -> dict:
    key = (HEATMAP_BASELINE.model, HEATMAP_BASELINE.seed, tuple(sorted(HEATMAP_BASELINE.task_ids)))
    if key not in _CACHE:
        _CACHE[key] = _build(HEATMAP_BASELINE)
    return {"cells": _CACHE[key], "baseline": HEATMAP_BASELINE.to_dict()}
```

Order-independence: `tuple(sorted(task_ids))` matches CONTEXT.md §Specifics. Thread safety: aggregator is read-mostly; rebuild on `race_done` is a single-event re-derivation. Use `threading.Lock` if Phase 9 plan-checker flags concurrent GETs — but FastAPI + the 45-run corpus means any race window is microseconds. **Recommendation: skip the lock for v1, document the assumption in the module docstring.**

### 6. Baseline filter — `HEATMAP_BASELINE` in `race/config.py`

**File `src/a2a_vs_mcp/race/config.py` does not exist yet.** Verified by `ls src/a2a_vs_mcp/race/`. Phase 9 creates it.

```python
# src/a2a_vs_mcp/race/config.py
"""Pinned race-demo configuration constants (D-56).

HEATMAP_BASELINE is the single source of truth for the closing-artifact heatmap's
aggregation scope. Footer reads from it. Aggregator filters from it. Cache key
derived from it. Drift kills the demo's honesty pill — D-55, D-57.
"""
from __future__ import annotations
from dataclasses import dataclass

from .harness import MODEL, SEED_DISCLOSURE  # MODEL='claude-sonnet-4-6'; SEED_DISCLOSURE=42


@dataclass(frozen=True)
class HeatmapBaseline:
    model: str
    seed: int
    task_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return {"model": self.model, "seed": self.seed, "task_ids": list(self.task_ids)}


HEATMAP_BASELINE: HeatmapBaseline = HeatmapBaseline(
    model=MODEL,                # claude-sonnet-4-6
    seed=SEED_DISCLOSURE,       # 42
    task_ids=("summarize_repo", "negotiate_meeting", "book_travel"),
)
```

**Run metadata for filtering — current state:** Run files are ndjson event streams. They do NOT carry per-file `model` / `seed` metadata at the run-id-envelope level today. **This is the key architectural friction in Phase 9.** Two ways forward:

1. **Run-id naming convention** — `harness.py:362` builds `run_id = f"{lane}-{spec.task_id}-{run_idx}-{uuid.uuid4().hex[:6]}"`. Aggregator extracts `task_id` from this regex. `model` and `seed` are NOT in the run-id and currently NOT in any event. Implication: every run on disk is **assumed** to come from `claude-sonnet-4-6` / `seed=42` because that's what `MODEL` + `SEED_DISCLOSURE` are pinned to in `harness.py:53-58`.

2. **Add a `run_meta` event at run start** — emit `{event_type: "run_meta", model, seed, task_id, lane}` as the FIRST event in every run file. Aggregator filters by reading event #1.

**Recommendation: Option 2 — add `run_meta` event.** Without it, future devs experimenting with different models or seeds (the very thing D-55 protects against) will silently pollute the heatmap. Phase 9 plan should include a small task: "harness emits `run_meta` event at run start; aggregator filters by it; off-baseline runs skipped per D-57." Cost: ~15 lines in `harness.py`, one new event type added to the schema (free — no validation surface to update; trace_schema_version stays 1.0 because schema is additive per Phase 6 D-03).

**If Option 2 is judged scope creep:** Aggregator can fall back to assuming all `data/runs/*.json` are baseline (since `MODEL`/`SEED_DISCLOSURE` are module-pinned and overrides aren't supported in v2.0). This is what CONTEXT.md §Specifics implies but doesn't make explicit. Surface this to the planner as Open Question.

### 7. Replay endpoint shape — match Phase 8 typed stub

**Already verified:** `frontend/src/lib/api/client.ts:136-163` defines:

```ts
export interface RaceReplayPayload {
  run_id: string;
  events: RaceEvent[];
  schema_version: string;
}
// ...
const res = await fetch(`/api/race/runs/${encodeURIComponent(run_id)}/trace`);
```

Backend MUST return JSON matching `{run_id: string, events: array, schema_version: "1.0"}`. The `events` array is the raw ndjson lines parsed — `RaceEvent` is a closed union in `frontend/src/lib/types/race.ts:31-41` covering `tick`/`tool_call`/`agent_msg`/`fault_injected`/`fault_observed`/`done`/`error`/`race_done`/`ws_closed`/`ws_error`.

**Pitfall — frontend `RaceEvent.type` vs backend `event_type`:** Verified field-name mismatch:

- Frontend `RaceEvent` discriminator: `type` (`race.ts:31-41`).
- Backend ndjson events: `event_type` (verified across `data/runs/r-x.json` and all fixtures).

The Phase 8 `useRaceReplay` hook fetches the payload but does NOT consume `events` deeply (search `useRaceReplay.ts` for `event_type` — zero hits). **The mismatch is unconsumed in Phase 8** but will surface in any future code that reads `events[i].type` against backend data.

**Recommendation:** Backend ships events verbatim (with `event_type`) — schema_version=1.0 is the disk schema. Either (a) Phase 9 adds a backend response transform that renames `event_type` → `type`, OR (b) Phase 9 updates the frontend `RaceEvent` discriminator to `event_type`. Option (b) is cheaper and more honest (frontend tracks backend reality). **Surface to planner.**

## Files to create / modify

### Create (NEW)

| Path | Role | Purpose |
|------|------|---------|
| `src/a2a_vs_mcp/race/config.py` | NEW | `HEATMAP_BASELINE` constant (D-56) |
| `src/a2a_vs_mcp/race/heatmap.py` | NEW | Aggregator + cache + `get_heatmap()` + `invalidate_cache()` (D-52, D-54, D-55, D-57) |
| `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` | NEW | Data wrapper around `HeatmapScaffold` (HEAT-01, HEAT-02) |
| `frontend/src/features/race/components/HardnessFailureHeatmap.test.tsx` | TEST | Component tests for data fetch + transform + footer + legend |
| `tests/test_recovery_calibration.py` | TEST | K∈{2,3,4,5} sweep (HEAT-04) |
| `tests/race/test_replay_symmetry.py` | TEST | Two-layer fixture test (HEAT-03) |
| `tests/race/_replay_helpers.py` | NEW | Shared `_replay_with_k(events, K, score_pass) -> tag` helper |

### Modify

| Path | Role | Change |
|------|------|--------|
| `src/a2a_vs_mcp/web.py` | MODIFY | Add `GET /api/race/runs/{run_id}/trace` (HEAT-03) and `GET /api/race/heatmap` (D-52) routes alongside line 857 ws mount |
| `src/a2a_vs_mcp/race/harness.py` | MODIFY | Call `from .heatmap import invalidate_cache; invalidate_cache()` after the `ws_emitter({"event_type": "race_done", ...})` line (~465) |
| `src/a2a_vs_mcp/race/harness.py` | MODIFY | (If Option 2 chosen) Emit `run_meta` event at run start in `_run_one_with_retry` or recorder factory wrapper — see §Baseline filter |
| `frontend/src/features/race/RacePage.tsx` | MODIFY | Replace line 177 `<HeatmapScaffold cells={heatmapCells} />` with `<HardnessFailureHeatmap />`; remove dead `heatmapCells`/`heatmap_has_data` lines 92-110 |
| `frontend/src/lib/api/client.ts` | MODIFY | Add `fetchRaceHeatmap(): Promise<HeatmapPayload>` mirroring `fetchRaceReplay` shape |
| `frontend/src/lib/types/race.ts` | MODIFY | Add `HeatmapCell` + `HeatmapPayload` + `HeatmapBaseline` exported types |
| `tests/conftest.py` | MODIFY | Add `pytest_addoption(... "--update-snapshots" ...)` hook |

### Optional (planner discretion)

| Path | Role | Purpose |
|------|------|---------|
| `src/a2a_vs_mcp/race/replay_symmetry.py` | NEW | Pure helper `replay_with_detector(events, K, score_pass) -> tag` shared by tests + future API surfaces |
| `frontend/src/features/race/hooks/useHeatmap.ts` | NEW | Extract data hook from `HardnessFailureHeatmap` if planner prefers separation (mirrors `useRaceReplay` pattern) |

## Landmines & Open Questions

### Landmines

1. **`HardnessType` enum value mismatch.** Backend `race/types.py:26` says `MULTI_SOURCE_SYNTHESIS = "multi_source"`. Frontend `HeatmapScaffold.tsx:31` says `"multi_source_synthesis"`. The wrapper transform must rename. Confidence: HIGH — verified both files.
2. **`RaceEvent.type` (frontend) vs `event_type` (backend ndjson).** Phase 8 didn't trip on it because `useRaceReplay` doesn't deep-consume events. Phase 9 should fix one side. Confidence: HIGH — verified both files. Recommendation: rename frontend discriminator.
3. **Run files have NO model/seed envelope.** Aggregator can either assume all on-disk runs are baseline (lazy) or require `run_meta` events (correct). Phase 9 plan must pick one explicitly. Recommendation: emit `run_meta`. See §6.
4. **`Detector` per-fault state is non-trivial.** Replay symmetry hinges on calling `Detector.consume(event)` for EVERY event after fault_injected — including events from OTHER lanes/runs in the same trace file. The test helper must filter to events belonging to the same lane/fault as the fault_injected entry. Use `events_for_lane(events, lane)` from `replay.py:66` to scope correctly. Confidence: HIGH — verified all 3 runners use `event.get("turn_index", 0)` and consume in order.
5. **`fault_inject_turn` value.** Detector constructor expects the turn at which the fault was injected. The `fault_injected` event's `turn_index` field is the source. Verified — runners use `event.get("turn_index", 0)` (default 0 is questionable but matches existing usage; Phase 9 helper inherits the same default).
6. **Run-id naming pollution.** Run-ids include the lane/task prefix (`harness.py:362`). This means an aggregator that walks `data/runs/` can extract task_id from the filename — but only if the convention is preserved. If `run_meta` events are emitted (recommended), the aggregator should prefer the event over the filename to avoid coupling aggregation to filename parsing.
7. **Cache concurrency.** D-54 cache is process-local dict. Concurrent GET + invalidate is theoretically racy. Real-world risk is low (45-run rebuild is microseconds; FastAPI handlers serialize per-event-loop). Skip the lock for v1; flag in plan-checker.
8. **Empty-baseline-corpus state.** First-load before any race: aggregator returns `{cells: [], baseline: HEATMAP_BASELINE.to_dict()}`. `HardnessFailureHeatmap` transforms to empty `cells = {}` → `HeatmapScaffold` shows the empty-state overlay (D-47). Already correct; no extra branch.
9. **Calibration sweep — K=2 may not drift.** If the existing fixtures were authored without near-K3-boundary events, K=2 might still produce the same tag as K=3. Phase 9 plan SHOULD include a "boundary-fixture audit" task: confirm at least one fixture per task has fault→evidence distance == 3 (so K=2 closes the window early).
10. **MULTI_SOURCE_SYNTHESIS coverage.** Verified: `summarize_repo` `task_config.yaml` has `[long_chain, rate_pressure, schema_variance]`. `MULTI_SOURCE_SYNTHESIS` MUST appear in ≥1 task per RACE-01 (verified). Planner: confirm `negotiate_meeting` and `book_travel` task_configs cover the 4th hardness type so the heatmap has all 4 rows populated. (Read those YAML files during planning.)

### Open Questions

1. **Where do "fictional traces" from §The Assignment live?**
   - What we know: The 9 files in `tests/race/fixtures/traces/` are likely §The Assignment fixtures (named per task × terminal_tag, with `expected_terminal_tag` envelope keys — exactly the calibration corpus shape). 
   - What's unclear: The master design doc at `~/.gstack/projects/skylark248-A2AvsMCP/shivanshchoudhary-master-design-20260427-193227.md` may list MORE fixtures (or different ones).
   - Recommendation: Plan task 1 reads master design §The Assignment and reconciles against the existing 9 files. If new fixtures needed, add them in the same JSON envelope shape.

2. **Does the heatmap require `multi_source_synthesis` to render even without populated cells?**
   - What we know: `HeatmapScaffold` renders all 4 hardness rows × 3 lane cols regardless of `cells` content; empty cells get `bgcolor: "action.hover"` (verified line 120).
   - What's unclear: Does HEAT-01 want all 4 rows always-rendered (yes per Phase 8) or only rows where ≥1 baseline run exists?
   - Recommendation: All 4 rows always rendered (preserves the closing-artifact contract); empty cells fall through to the muted neutral background. No change to `HeatmapScaffold`.

3. **Does `run_meta` event count as a schema change requiring `trace_schema_version` bump?**
   - What we know: Phase 6 D-03 said additive extensions preserve v1.0 backwards compat (`STATE.md` line 67). New event types are additive.
   - What's unclear: Whether the Phase 6 schema gate (`tests/race/test_trace_schema.py`) enumerates allowed event_types as a closed set.
   - Recommendation: Read `test_trace_schema.py` during planning. If event_types are closed, either (a) bump to schema v1.1 with migrator + add `run_meta` to allowed set, or (b) shove model/seed onto the existing `done` event as additive fields. Lower-blast-radius: option (b).

4. **Does the FastAPI route handler for `/api/race/heatmap` need to be async?**
   - What we know: All other FastAPI routes in `web.py` are sync `def`. The aggregator is pure CPU + disk read.
   - Recommendation: sync `def` with `async def` only on the ws route (line 858). Planner can flip to async if profiling shows blocking is an issue (it won't, with 45 runs).

## Recommended Plan Breakdown

Suggested 4 plans across 2 waves. Wave assignment optimizes parallelism: backend modules + tests have no cross-dependencies; frontend wrapper depends on backend route shape.

### Wave 1 — Backend + Tests (parallel; all independent)

**Plan 09-01 — Heatmap backend (`config.py` + `heatmap.py` + route + harness hook)**
- File creates: `race/config.py`, `race/heatmap.py`
- File modifies: `web.py` (heatmap route), `harness.py` (invalidate_cache call + optional `run_meta` event)
- Tests: `tests/race/test_heatmap_aggregator.py` (NEW) — pinned-baseline filter, cell shape, cache invalidation, off-baseline exclusion (D-55, D-57)
- Touches: HEAT-02 (footer baseline payload)
- Dependencies: none

**Plan 09-02 — Replay backend route**
- File modifies: `web.py` (replay route)
- Tests: `tests/race/test_replay_route.py` (NEW) — happy path, 400 on invalid run_id, 404 on missing run_id, schema_version=1.0
- Touches: HEAT-03 (route shape)
- Dependencies: none

**Plan 09-03 — Replay symmetry + K=3 calibration tests**
- File creates: `tests/race/_replay_helpers.py`, `tests/race/test_replay_symmetry.py`, `tests/test_recovery_calibration.py`
- File modifies: `tests/conftest.py` (`pytest_addoption("--update-snapshots")`)
- Optional file creates: `src/a2a_vs_mcp/race/replay_symmetry.py` (extracted helper)
- Touches: HEAT-03 (two-layer fixture), HEAT-04 (K sweep)
- Dependencies: none (uses existing fixtures)

### Wave 2 — Frontend wrapper (depends on Plan 09-01 route shape)

**Plan 09-04 — `HardnessFailureHeatmap.tsx` + RacePage wiring**
- File creates: `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` + tests; optional `frontend/src/features/race/hooks/useHeatmap.ts` + tests
- File modifies: `frontend/src/lib/api/client.ts` (add `fetchRaceHeatmap`), `frontend/src/lib/types/race.ts` (add `HeatmapCell`/`HeatmapPayload`/`HeatmapBaseline` types), `frontend/src/features/race/RacePage.tsx` (replace `HeatmapScaffold` call site, remove dead empty-cells code)
- Optional fix: rename `RaceEvent.type` → `event_type` if planner accepts the cleanup
- Tests: HEAT-01 (4-channel cells via scaffold passthrough), HEAT-02 (legend strip + footer), empty-state preserved
- Dependencies: Plan 09-01 (heatmap route + payload shape)

### Critical-path observations for the planner

- W1 plans 09-01 / 09-02 / 09-03 have **zero shared files** and can fully parallelize.
- W2 plan 09-04 depends only on the **payload shape contract** from 09-01, not on its implementation. If the contract is locked in CONTEXT.md (it is — D-53), 09-04 can start before 09-01 lands; integration test runs after 09-01 merges.
- The `HardnessType` enum-value mismatch (Landmine 1) is a 1-line transform fix in 09-04. It does not need a separate plan but should be called out as a verification step.
- The `RaceEvent.type`/`event_type` mismatch (Landmine 2) is OPTIONAL — Phase 8 ships and Phase 9 doesn't strictly require it. Recommend folding into 09-04 only if the plan-checker has spare scope. Otherwise defer to Phase 11+ when TraceExplorer needs deep event consumption.

## Sources

### Primary (HIGH confidence)
- `src/a2a_vs_mcp/race/replay.py` — `load_run`, `_validate_run_id`, `events_for_lane`, `migrate_v1` (verified inline)
- `src/a2a_vs_mcp/race/classifier.py` — `Detector(K)`, `K_DEFAULT=3`, `finalize_at_done`, `finalize_at_race_done_no_done`, `failure_mode_classifier` (verified inline)
- `src/a2a_vs_mcp/race/harness.py` — `MODEL`, `SEED_DISCLOSURE`, run_race emit + race_done line ~465 (verified inline)
- `src/a2a_vs_mcp/race/runs.py` — `RUNS_DIR`, RunWriter (verified inline)
- `src/a2a_vs_mcp/race/types.py` — `HardnessType`, value mismatch with frontend (verified inline)
- `src/a2a_vs_mcp/race/ws.py` — `MANAGER`, `NEVER_COALESCE` (verified inline)
- `src/a2a_vs_mcp/race/metrics.py` — `aggregate_for_classifier`, recovery_rate field (verified inline)
- `src/a2a_vs_mcp/web.py` lines 43-45, 857-898 — imports + ws route (verified inline; `/api/race/runs/{run_id}/trace` and `/api/race/heatmap` confirmed missing)
- `frontend/src/features/race/components/HeatmapScaffold.tsx` — props shape, 4-channel encoding (verified inline)
- `frontend/src/features/race/hooks/useRaceReplay.ts` — typed stub (verified inline)
- `frontend/src/lib/api/client.ts:136-163` — `RaceReplayPayload`, `fetchRaceReplay` (verified inline)
- `frontend/src/lib/types/race.ts` — `RaceEvent.type` discriminator, `FailureTag`, `RaceLane` (verified inline)
- `frontend/src/lib/trace/eventColors.ts:54` — `failureTagColor` 5-entry map (verified inline)
- `frontend/src/features/race/RacePage.tsx:19,177,92-110` — current heatmap call site (verified inline)
- `data/runs/r-x.json` — sample trace shape (`event_type`, `fault_id`, `turn_index`, etc.) (verified inline)
- `tests/race/fixtures/traces/summarize_repo_recovered.json` — fixture envelope shape (`expected_terminal_tag`, `score_pass`) (verified inline)
- `tests/race/test_replay_stub.py` — existing replay tests (verified inline)
- `pyproject.toml` — pytest>=8.0, pytest-asyncio>=0.24, pyyaml, fastapi (verified inline)
- `.planning/phases/08-race-page-ui-visual-contract/08-05-SUMMARY.md` — Phase 8 contract handoff (verified inline)
- `.planning/config.json` — `nyquist_validation: false` (Validation Architecture section omitted)

### Secondary (MEDIUM confidence)
- §The Assignment fixture corpus — INFERRED to be the 9 files in `tests/race/fixtures/traces/` based on naming + envelope shape. Plan task 1 should confirm by reading master design doc.

### Tertiary (LOW confidence)
- None — all critical claims verified against source.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The 9 fixture files in `tests/race/fixtures/traces/` are §The Assignment fixtures | §K=3 calibration fixture | Test doesn't cover the documented corpus; planner adds missing fixtures |
| A2 | All `data/runs/*.json` files are baseline (model=claude-sonnet-4-6, seed=42) because `harness.py` pins those constants and offers no override | §6 Baseline filter | Without `run_meta` events, off-baseline runs (e.g., dev experiments) silently merge into the heatmap, contaminating the closing artifact (D-55 violated) |
| A3 | Backend response renaming `event_type` → `type` is unnecessary in Phase 9 | §7 Replay endpoint shape | If Phase 11+ TraceExplorer reads `events[i].type` against backend data, the discriminator union breaks |
| A4 | Existing fixtures have at least one near-K3-boundary event per task (so K=2/4/5 drift is observable) | §K=3 calibration fixture | K-drift assertion fails; planner must author new fixtures with fault→evidence distance ≈ 3 |
| A5 | FastAPI sync `def` is sufficient for the heatmap GET route (corpus is bounded; rebuild is microseconds) | §5 Cache invalidation transport | Under load, sync handler blocks event loop. Mitigation: flip to async + `asyncio.to_thread` for the disk scan if profiling shows it. |
| A6 | The `run_meta` proposal (Option 2 in §6) is in scope for Phase 9 | §6 Baseline filter | If planner judges scope creep, fall back to "all runs are assumed baseline" — silent risk of D-55 violation |

**Action for planner / discuss-phase:** Confirm A1 (read master design §The Assignment) and A2 (decide on `run_meta` event vs. lazy assumption) before locking the plan. The other assumptions are lower risk.

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — every primitive used is already shipped + tested in upstream phases
- Architecture: HIGH — wiring + 2 routes + 1 wrapper + 2 tests; no new patterns
- Pitfalls: HIGH — landmines verified by reading source; A1/A2 are the only unverified assumptions

**Research date:** 2026-04-29
**Valid until:** 2026-05-29 (stable; no upstream churn expected)

## RESEARCH COMPLETE
