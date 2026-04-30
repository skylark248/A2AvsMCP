# Phase 9: Heatmap, Replay & K=3 Calibration — Pattern Map

**Mapped:** 2026-04-29
**Files analyzed:** 13 (7 NEW + 6 MODIFY)
**Analogs found:** 13 / 13

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `src/a2a_vs_mcp/race/heatmap.py` | service / aggregator | batch (read disk → bucket → cache) | `src/a2a_vs_mcp/race/metrics.py` | role-match (pure function aggregator) |
| `src/a2a_vs_mcp/race/config.py` | config / module-constants | static | `src/a2a_vs_mcp/race/runs.py` (RUNS_DIR module-constant pattern), `src/a2a_vs_mcp/race/types.py` (frozen dataclass) | role+flow exact |
| `src/a2a_vs_mcp/web.py` (heatmap route) | controller / route handler | request-response | `src/a2a_vs_mcp/web.py` lines 824-854 (`api_remote_a2a_health`) | exact (sync `def` GET in same file) |
| `src/a2a_vs_mcp/web.py` (replay route) | controller / route handler | request-response | `src/a2a_vs_mcp/web.py` lines 857-868 (`race_ws` validate→load_run pattern) | exact (same module reuses same imports) |
| `src/a2a_vs_mcp/race/harness.py` (race_done invalidate) | event-driven hook | pub-sub (direct callback) | `src/a2a_vs_mcp/race/harness.py:465-474` (existing `ws_emitter` race_done call) | exact |
| `src/a2a_vs_mcp/race/harness.py` (run_meta emit) | event emitter | streaming (ndjson append) | `src/a2a_vs_mcp/race/harness.py:465` ws_emitter pattern + recorder factory | role-match |
| `src/a2a_vs_mcp/race/replay.py` | service / loader | file I/O | itself — already shipped; Phase 9 reuses unchanged | exact (no edit) |
| `tests/test_recovery_calibration.py` | test (unit, parametrized) | batch | `tests/race/test_classifier_detector.py` + `tests/race/test_failure_mode_classifier.py` | role-match |
| `tests/race/test_replay_symmetry.py` | test (snapshot-style fixture sweep) | file I/O + assertion | `tests/race/test_replay_stub.py` (fixture-loop pattern) | role-match |
| `tests/race/_replay_helpers.py` | test utility / shared helper | pure function | `src/a2a_vs_mcp/race/metrics.py` private helpers `_find_fault_injected` | role-match |
| `tests/conftest.py` (`pytest_addoption`) | config / pytest hook | static | itself (existing sys.path bootstrap) | extension of same file |
| `frontend/src/features/race/hooks/useRaceHeatmap.ts` | hook / data fetcher | request-response | `frontend/src/features/race/hooks/useRaceReplay.ts` | exact (same shape, same lifecycle) |
| `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` | component / data wrapper | request-response (consume hook) | `frontend/src/features/race/components/HeatmapScaffold.tsx` | role+flow (wraps it) |
| `frontend/src/lib/api/client.ts` (`fetchRaceHeatmap`) | api client | request-response | `client.ts:136-163` (`fetchRaceReplay`/`RaceReplayPayload`) | exact |
| `frontend/src/lib/types/race.ts` (HeatmapCell/Payload) | types | static | `race.ts:5-10` (`FailureTag` union), `race.ts:43-53` (interface block) | exact |
| `frontend/src/features/race/RacePage.tsx` (slot wire) | page / orchestrator | composition | `RacePage.tsx:177` (existing `<HeatmapScaffold cells={heatmapCells} />` slot) | exact (one-line replace) |

---

## Pattern Assignments

### `src/a2a_vs_mcp/race/config.py` (config, static module-constants)

**Analog:** `src/a2a_vs_mcp/race/runs.py` (module-level `RUNS_DIR` constant) + `src/a2a_vs_mcp/race/types.py` (`@dataclass`).
**Why analog:** Both files own a single locked constant module that downstream code imports verbatim. Phase 9 mirrors the shape with a `frozen=True` dataclass + module-level singleton instance.

**Imports pattern** (mirror `runs.py:1-19` + `types.py:1-26`):
```python
"""Pinned race-demo configuration constants (D-56).

HEATMAP_BASELINE is the single source of truth for the closing-artifact heatmap's
aggregation scope. Footer reads from it. Aggregator filters from it. Cache key
derived from it. D-55 / D-57.
"""
from __future__ import annotations
from dataclasses import dataclass

from .harness import MODEL, SEED_DISCLOSURE  # MODEL='claude-sonnet-4-6'; SEED=42
```

**Frozen dataclass + to_dict pattern** (lift from `types.py:29-37` HardnessProfile shape):
```python
@dataclass(frozen=True)
class HeatmapBaseline:
    model: str
    seed: int
    task_ids: tuple[str, ...]

    def to_dict(self) -> dict:
        return {"model": self.model, "seed": self.seed, "task_ids": list(self.task_ids)}


HEATMAP_BASELINE: HeatmapBaseline = HeatmapBaseline(
    model=MODEL,
    seed=SEED_DISCLOSURE,
    task_ids=("summarize_repo", "negotiate_meeting", "book_travel"),
)
```

**Key pattern notes:**
- `from __future__ import annotations` is universal in `src/a2a_vs_mcp/race/*` (verified across `harness.py:23`, `types.py:13`, `runs.py:13`, `replay.py:10`, `metrics.py:14`).
- Module docstring with the controlling decision IDs (D-55/D-56/D-57) — mirrors `runs.py:1-12` (D-01/D-04/D-05) and `metrics.py:1-13` (D-37/D-40).
- Singleton `HEATMAP_BASELINE` is a module-level binding, not a class attribute. Imports look like `from .config import HEATMAP_BASELINE`.

---

### `src/a2a_vs_mcp/race/heatmap.py` (service / aggregator, batch)

**Analog:** `src/a2a_vs_mcp/race/metrics.py` (pure-function aggregator over event lists, `aggregate_for_classifier`).
**Why analog:** Both modules walk a list of trace events, bucket by per-fault attributes, and return a structured dict consumed by callers. No I/O ownership in the aggregator core; disk reading is a thin wrapper.

**Imports + module docstring pattern** (lift from `metrics.py:1-18`):
```python
"""Heatmap aggregator + in-process cache (D-52, D-54, D-55, D-57).

get_heatmap() reads data/runs/*.json, filters to runs matching HEATMAP_BASELINE
(model, seed, task_ids), buckets cells by (HardnessType, lane), and returns
{cells: [...], baseline: {...}}. Cache invalidated on race_done by harness.

NO live LLM. NO network. Pure ndjson scan + bucket.
"""
from __future__ import annotations

import json
from collections import Counter
from typing import Any

from .config import HEATMAP_BASELINE
from .replay import load_run
from .runs import RUNS_DIR
from .types import HardnessType
```

**Aggregator core pattern** (mirror `metrics.py:120-178` `aggregate_for_classifier`):
```python
_CACHE: dict[tuple, list[dict]] = {}


def invalidate_cache() -> None:
    """Called by harness after race_done emit (D-54)."""
    _CACHE.clear()


def get_heatmap() -> dict[str, Any]:
    """Return {cells: [...], baseline: {...}}. Rebuilds from disk on cache miss."""
    key = (HEATMAP_BASELINE.model, HEATMAP_BASELINE.seed,
           tuple(sorted(HEATMAP_BASELINE.task_ids)))
    if key not in _CACHE:
        _CACHE[key] = _build_cells(HEATMAP_BASELINE)
    return {"cells": _CACHE[key], "baseline": HEATMAP_BASELINE.to_dict()}


def _build_cells(baseline) -> list[dict[str, Any]]:
    """Walk RUNS_DIR; filter by run_meta event match against baseline; bucket
    per (HardnessType, lane); pick dominant_tag; compute recovery_rate."""
    cells_by_key: dict[tuple[str, str], dict] = {}
    for path in sorted(RUNS_DIR.glob("*.json")):
        run_id = path.stem
        try:
            events = load_run(run_id, RUNS_DIR)
        except (FileNotFoundError, ValueError):
            continue
        meta = next((e for e in events if e.get("event_type") == "run_meta"), None)
        if not _matches_baseline(meta, baseline):
            continue  # D-57 silent exclusion
        # ... bucket per (hardness_type, lane), accumulate tags + score_pass
    return list(cells_by_key.values())
```

**Helper pattern — find event by type** (mirror `metrics.py:20-25`):
```python
def _find_fault_injected(events: list[dict], fault_id: str) -> dict | None:
    return next(
        (e for e in events
         if e.get("event_type") == "fault_injected" and e.get("fault_id") == fault_id),
        None,
    )
```
Use the **same `next(generator, None)` idiom** for `run_meta`, `done`, etc. lookups in heatmap.py.

**No-side-effect docstring discipline** (mirror `metrics.py:13` "Counts are NEVER stored; recomputed from the trace as needed."): document the in-process cache + `invalidate_cache()` contract in module docstring.

---

### `src/a2a_vs_mcp/web.py` — heatmap route (controller, request-response)

**Analog:** `web.py:824-854` `api_remote_a2a_health` (sync `def`, GET, returns Pydantic-typed response, raises HTTPException) **and** `web.py:857-868` `race_ws` (validate run_id then load disk pattern).

**Import pattern** (already in `web.py:43-45`):
```python
from .race.replay import load_run, _validate_run_id
from .race.runs import RUNS_DIR
from .race.ws import MANAGER, HEARTBEAT_S
```
**ADD** for Plan 09-01 (heatmap route):
```python
from .race.heatmap import get_heatmap
```

**Sync GET handler pattern** (lift shape from `web.py:824-854`):
```python
@app.get("/api/race/heatmap")
def api_race_heatmap() -> dict:
    return get_heatmap()
```
Note: Phase 9 routes return raw `dict` (not Pydantic models) because the heatmap payload schema is locked client-side via `HeatmapPayload` TS type, mirroring the `RaceReplayPayload`-as-dict approach.

**Decorator + handler placement:** Insert **alongside** the ws mount at line 857 — Phase 9 routes co-locate with the ws route per CONTEXT.md §Integration Points.

---

### `src/a2a_vs_mcp/web.py` — replay route (controller, request-response)

**Analog:** `web.py:857-868` (`race_ws` validate→load_run pattern) — uses the same imports and same path-traversal guard.

**Validate-then-load pattern** (lift verbatim from `web.py:863-868` validation prologue):
```python
@app.get("/api/race/runs/{run_id}/trace")
def api_race_run_trace(run_id: str) -> dict:
    # Path-traversal guard FIRST — before any file resolution.
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

**Why this exact shape:**
- `_validate_run_id` raises `ValueError`; HTTPException 400 mirrors the ws route's close code 4400 contract (`web.py:867`).
- `load_run` raises `FileNotFoundError` on missing run (verified `tests/race/test_replay_stub.py:84-87`).
- Response shape `{run_id, events, schema_version}` matches `frontend/src/lib/api/client.ts:136-140` `RaceReplayPayload` exactly.
- Sync `def` matches `api_remote_a2a_health` style (`web.py:825`); async only on the ws route.

---

### `src/a2a_vs_mcp/race/harness.py` — invalidate_cache + run_meta emission (event-driven)

**Analog (cache invalidation):** `harness.py:465-474` (the existing `ws_emitter({"event_type": "race_done", ...})` call site).

**Existing race_done emit** (verbatim, `harness.py:462-474`):
```python
# D-39: emit the single race_done event. Tuple keys flattened to
# 'lane|task_id' since tuples aren't JSON-serializable across the
# ws bus (Phase 6 ws.py expects dict[str, Any]).
ws_emitter({
    "event_type": "race_done",
    "t_end_ms": int(time.time() * 1000),
    "total_runs": len(results),
    "lane_failed_reasons": lane_failed_reasons,
    "headlines": {
        f"{lane}|{task_id}": h
        for (lane, task_id), h in headlines.items()
    },
})
```

**Modification pattern (Plan 09-01):** add directly after the `ws_emitter(...)` call at `harness.py:474`:
```python
from .heatmap import invalidate_cache  # late import to avoid module-load order trip
invalidate_cache()
```
**Or** import at module top in the import block (`harness.py:43-46`) — preferred for consistency.

**Analog (run_meta emit, D-58):** `harness.py:361-367` — recorder construction site (per-run loop) is where `run_meta` must fire as the FIRST event:
```python
for run_idx in range(n):
    run_id = f"{lane}-{spec.task_id}-{run_idx}-{uuid.uuid4().hex[:6]}"
    recorder = recorder_factory(run_id=run_id, lane=lane, task_id=spec.task_id)
    schedule.append((lane, spec, run_id, recorder))
```

**run_meta emission pattern** (lift event-dict shape from existing `ws_emitter` call):
```python
recorder.record({
    "event_type": "run_meta",
    "trace_schema_version": "1.0",
    "model": MODEL,
    "seed": SEED_DISCLOSURE,
    "task_id": spec.task_id,
    "lane": lane,
    "run_id": run_id,
})
```
**Pitfall:** `runs.py:25` `FORCED_FLUSH_EVENTS` is a frozenset — adding `run_meta` to it ensures the meta event flushes immediately, but is optional (run won't proceed without subsequent forced-flush events anyway). Document this as a planner decision point.

**Pattern verification — every event needs `trace_schema_version`:** `replay.py:39-44` `migrate_v1` rejects events missing this key. The first event must carry it; subsequent events inherit through the migrator's permissive policy (only first event is checked).

---

### `tests/race/_replay_helpers.py` (test utility, pure function)

**Analog:** `metrics.py:20-25` (private helpers on event lists) + `harness.py` `_per_run_tag` (per-run finalize pattern).

**Helper pattern — feed Detector over events** (lifted from runners + classifier):
```python
"""Shared helper: feed Detector(K) over a fixture trace, return terminal tag.

Single source of truth for replay-symmetric tag computation in tests
(HEAT-03 + HEAT-04). Mirrors the runners' Detector usage at
race/runners/pure_mcp.py:95 / pure_a2a.py:166 / hybrid.py:75.
"""
from __future__ import annotations

from a2a_vs_mcp.race.classifier import Detector


def replay_with_k(events: list[dict], K: int, score_pass: bool) -> str:
    """Replay a fixture trace through Detector(K). Return terminal tag.

    1. Find the first fault_injected event → instantiate Detector with K.
    2. Feed every subsequent event into detector.consume().
    3. On `done` event arrival, call finalize_at_done(score_pass).
    """
    fi = next((e for e in events if e.get("event_type") == "fault_injected"), None)
    if fi is None:
        raise ValueError("fixture has no fault_injected event")
    detector = Detector(
        fault_id=fi["fault_id"],
        fault_kind=fi["fault_kind"],
        target=fi["target"],
        fault_inject_turn=fi.get("turn_index", 0),
        K=K,
    )
    fi_idx = events.index(fi)
    for ev in events[fi_idx + 1:]:
        if ev.get("event_type") == "done":
            return detector.finalize_at_done(score_pass)
        detector.consume(ev)
    return detector.finalize_at_done(score_pass)
```

**Detector constructor signature** (verified `classifier.py:82-101`):
```python
@dataclass
class Detector:
    fault_id: str
    fault_kind: str
    target: str
    fault_inject_turn: int
    K: int = K_DEFAULT  # K_DEFAULT = 3
```

**Fixture envelope shape** (verified `tests/race/fixtures/traces/summarize_repo_recovered.json`):
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

---

### `tests/race/test_replay_symmetry.py` (test, snapshot-style fixture sweep)

**Analog:** `tests/race/test_replay_stub.py` (fixture-loading + path traversal test classes) + the `FIXTURES = Path(__file__).resolve().parent / "fixtures"` constant pattern.

**Fixture path constant pattern** (lift from `test_replay_stub.py:16`):
```python
FIXTURES = Path(__file__).resolve().parent / "fixtures" / "traces"
```

**Parametrize over fixtures pattern** (RESEARCH-recommended, no analog in current test corpus but matches pytest convention):
```python
import json
import pathlib
import pytest

from tests.race._replay_helpers import replay_with_k

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "traces"


@pytest.mark.parametrize("fixture_path", sorted(FIXTURES.glob("*.json")), ids=lambda p: p.stem)
def test_replay_symmetry(fixture_path, request):
    fx = json.loads(fixture_path.read_text())
    actual = replay_with_k(fx["events"], K=3, score_pass=fx["score_pass"])

    if request.config.getoption("--update-snapshots"):
        fx["expected_terminal_tag"] = actual
        fixture_path.write_text(json.dumps(fx, indent=2) + "\n")
        return

    assert actual == fx["expected_terminal_tag"], (
        f"{fixture_path.name}: replay produced {actual!r}, "
        f"fixture expects {fx['expected_terminal_tag']!r}"
    )
```

**Snapshot-flag pattern** (lift from RESEARCH §3 hand-rolled mechanism):
- Plumbing in `tests/conftest.py` via `pytest_addoption` (see conftest section below).
- Test reads via `request.config.getoption("--update-snapshots")`.
- No external dep (`pytest-snapshot`/`syrupy`) — fixture file IS the snapshot.

---

### `tests/test_recovery_calibration.py` (test, parametrized K-sweep)

**Analog:** `tests/race/test_classifier_detector.py` (Detector unit tests — same K=3 calibration domain) + `test_failure_mode_classifier.py` (parametrize-driven harness).

**Test skeleton pattern** (from RESEARCH §K=3 calibration fixture):
```python
import json
import pathlib
import pytest

from tests.race._replay_helpers import replay_with_k

FIXTURES = pathlib.Path(__file__).parent / "race" / "fixtures" / "traces"


@pytest.mark.parametrize(
    "fixture_path",
    sorted(FIXTURES.glob("*.json")),
    ids=lambda p: p.stem,
)
def test_k3_produces_expected_tag(fixture_path):
    """HEAT-04 lock: K=3 produces expected_terminal_tag for every fixture."""
    fx = json.loads(fixture_path.read_text())
    tag = replay_with_k(fx["events"], K=3, score_pass=fx["score_pass"])
    assert tag == fx["expected_terminal_tag"], (
        f"{fixture_path.name} drifted at K=3"
    )


@pytest.mark.parametrize("k", [2, 4, 5])
@pytest.mark.parametrize("task", ["summarize_repo", "negotiate_meeting", "book_travel"])
def test_off_k_drift_observed_per_task(k, task):
    """HEAT-04 calibration claim: at least one fixture per task drifts when K!=3."""
    drifts = []
    for path in FIXTURES.glob(f"{task}_*.json"):
        fx = json.loads(path.read_text())
        tag_k3 = replay_with_k(fx["events"], K=3, score_pass=fx["score_pass"])
        tag_kx = replay_with_k(fx["events"], K=k, score_pass=fx["score_pass"])
        if tag_kx != tag_k3:
            drifts.append((path.name, tag_kx, tag_k3))
    assert drifts, f"No K={k} drift for task={task} — calibration claim unsupported"
```

**Why test lives at `tests/test_recovery_calibration.py` (not under `tests/race/`):** ROADMAP success criterion 4 names this exact path. Cross-cutting evidence ("locks K=3") sits at the `tests/` root tier alongside other top-level demos.

---

### `tests/conftest.py` (pytest config, hook addition)

**Analog:** `tests/conftest.py` (existing file — sys.path bootstrap; add pytest_addoption alongside).

**Existing content** (verbatim, `tests/conftest.py:1-18`):
```python
"""Shared pytest configuration: sys.path setup and test environment variables."""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault(
    "A2A_VS_MCP_ARTIFACT_ROOT",
    str(PROJECT_ROOT / ".tmp" / "test_artifacts"),
)
```

**Addition pattern (Plan 09-03):** append `pytest_addoption` hook after the existing block:
```python
def pytest_addoption(parser):
    """Register --update-snapshots flag for hand-rolled fixture-snapshot tests
    (HEAT-03 two-layer fixture). When set, replay_symmetry test rewrites
    expected_terminal_tag in fixture JSON instead of asserting."""
    parser.addoption(
        "--update-snapshots",
        action="store_true",
        default=False,
        help="Rewrite expected_terminal_tag in fixture files instead of asserting",
    )
```

**Why hand-rolled, not `pytest-snapshot`/`syrupy`:** Verified zero snapshot-lib deps in `pyproject.toml`. RESEARCH §3 confirms fixture JSON files double as the snapshot — adding a lib for two test files is over-engineering.

---

### `frontend/src/features/race/hooks/useRaceHeatmap.ts` (hook, request-response)

**Analog:** `frontend/src/features/race/hooks/useRaceReplay.ts` (verbatim — same lifecycle, same `let active = true` cleanup, same shape).

**Imports pattern** (lift shape from `useRaceReplay.ts:12-13`):
```ts
import { useEffect, useState } from "react";
import { fetchRaceHeatmap, type HeatmapPayload } from "../../../lib/api/client";
```

**Hook signature pattern** (mirror `useRaceReplay.ts:15-19`):
```ts
export interface UseRaceHeatmapResult {
  data: HeatmapPayload | null;
  loading: boolean;
  error: string | null;
}

export function useRaceHeatmap(): UseRaceHeatmapResult {
  const [data, setData] = useState<HeatmapPayload | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
```

**Cleanup-pattern body** (lift verbatim from `useRaceReplay.ts:43-67`):
```ts
useEffect(() => {
  let active = true;
  setLoading(true);
  setError(null);

  void fetchRaceHeatmap()
    .then((payload) => {
      if (active) {
        setData(payload);
        setError(null);
      }
    })
    .catch((err: unknown) => {
      if (active) {
        setData(null);
        setError(err instanceof Error ? err.message : "Failed to load heatmap.");
      }
    })
    .finally(() => {
      if (active) setLoading(false);
    });

  return () => {
    active = false; // Cancel stale state writes on unmount
  };
}, []);

return { data, loading, error };
}
```

**Differences from useRaceReplay:** No `run_id` argument, no `isValidRunId` validation (heatmap is a singleton endpoint), empty deps array (fetch once on mount). All other patterns identical.

**Test pattern:** `useRaceReplay.test.ts:1-80` (vitest + `vi.stubGlobal('fetch', mockFetch)` + `renderHook` + `waitFor`) is the exact analog for `useRaceHeatmap.test.ts`. Lift the `makeMockFetch` helper verbatim.

---

### `frontend/src/features/race/components/HardnessFailureHeatmap.tsx` (component, data wrapper)

**Analog:** `frontend/src/features/race/components/HeatmapScaffold.tsx` (rendering primitive — wrapper consumes its props shape).

**Wrapper imports pattern** (mirror `HeatmapScaffold.tsx:15-20`):
```tsx
import { Box, Chip, Stack, Typography } from "@mui/material";
import { HeatmapScaffold, type HeatmapCells, type HardnessType } from "./HeatmapScaffold";
import { useRaceHeatmap } from "../hooks/useRaceHeatmap";
import { failureTagColor } from "../../../lib/trace/eventColors";
import type { FailureTag, RaceLane } from "../../../lib/types/race";
```

**HardnessType enum-value mismatch transform** (LANDMINE 1 — lift from RESEARCH §4):
- Backend ships `"multi_source"` (verified `race/types.py:26` `MULTI_SOURCE_SYNTHESIS = "multi_source"`).
- Frontend expects `"multi_source_synthesis"` (verified `HeatmapScaffold.tsx:31`).
- Transform map at top of wrapper:
```tsx
const HARDNESS_BACKEND_TO_FRONTEND: Record<string, HardnessType> = {
  long_chain: "long_chain",
  rate_pressure: "rate_pressure",
  schema_variance: "schema_variance",
  multi_source: "multi_source_synthesis",
};
```

**API → HeatmapCells transform** (lift from RESEARCH §4 with the rename baked in):
```tsx
function toHeatmapCells(payload: HeatmapPayload): HeatmapCells {
  const cells: HeatmapCells = {};
  for (const c of payload.cells) {
    const row = HARDNESS_BACKEND_TO_FRONTEND[c.hardness_type];
    if (!row) continue;
    cells[row] ??= {};
    cells[row]![c.lane] = {
      tag: c.dominant_tag,
      recoveryFraction: `${c.recovery_rate.num}/${c.recovery_rate.den}`,
    };
  }
  return cells;
}
```

**Component skeleton — "directional" pill + scaffold + legend strip + footer:**
```tsx
export function HardnessFailureHeatmap() {
  const { data, loading, error } = useRaceHeatmap();
  const cells = data ? toHeatmapCells(data) : {};

  return (
    <Box>
      {/* Directional pill — UI-SPEC + ROADMAP success criterion 1 */}
      <Chip
        color="secondary"
        label="directional · n=3 tasks · v1"
        sx={{ mb: 2 }}
      />

      {/* Phase 8 scaffold — D-46 + D-47 preserved (CSS Grid + role=gridcell) */}
      <HeatmapScaffold cells={cells} />

      {/* Legend strip — 5 inline pills, always visible (HEAT-02) */}
      <Stack direction="row" spacing={1} sx={{ mt: 2 }} flexWrap="wrap">
        {(Object.keys(failureTagColor) as FailureTag[]).map((tag) => {
          const cfg = failureTagColor[tag];
          const Icon = cfg.Icon;
          return (
            <Chip
              key={tag}
              icon={<Icon />}
              label={cfg.label}
              sx={{ bgcolor: cfg.bg, color: cfg.text }}
            />
          );
        })}
      </Stack>

      {/* Footer — data-driven from baseline payload (HEAT-02 contract) */}
      {data ? (
        <Typography variant="caption" sx={{ color: "text.secondary", display: "block", mt: 1 }}>
          {data.baseline.model} · {data.baseline.seed} · {data.baseline.task_ids.join(", ")}
        </Typography>
      ) : null}
    </Box>
  );
}
```

**Phase 8 contract preservation** (D-46/D-47 — verified `HeatmapScaffold.tsx:65-198`):
- `<HeatmapScaffold>` rendering primitive untouched. Empty `cells = {}` falls through to the `heatmap-empty-overlay` (lines 173-195) automatically.
- Wrapper does NOT bypass the scaffold's role=gridcell + 4-channel encoding.

**failureTagColor reuse** (verified `eventColors.ts:54-60`): 5-entry map already provides `{bg, text, Icon, label}` per FailureTag. Legend pills consume it directly — no new constant needed.

---

### `frontend/src/lib/api/client.ts` — `fetchRaceHeatmap` (api client)

**Analog:** `client.ts:134-163` (`fetchRaceReplay` block — exact mirror).

**Existing fetchRaceReplay pattern** (verbatim, `client.ts:136-163`):
```ts
// ---- Race Replay -----------------------------------------------------------

export interface RaceReplayPayload {
  run_id: string;
  events: RaceEvent[];
  schema_version: string;
}

const RUN_ID_REGEX = /^[a-zA-Z0-9_-]{1,64}$/;

export function isValidRunId(run_id: string): boolean {
  return RUN_ID_REGEX.test(run_id);
}

export async function fetchRaceReplay(run_id: string): Promise<RaceReplayPayload> {
  if (!isValidRunId(run_id)) {
    throw new Error("Invalid run_id");
  }
  const res = await fetch(`/api/race/runs/${encodeURIComponent(run_id)}/trace`);
  if (!res.ok) throw new Error(`Replay fetch failed: ${res.status}`);
  return (await res.json()) as RaceReplayPayload;
}
```

**Phase 9 addition pattern (Plan 09-04):** append after `fetchRaceReplay`:
```ts
// ---- Race Heatmap ---------------------------------------------------------

export interface HeatmapBaseline {
  model: string;
  seed: number;
  task_ids: string[];
}

export interface HeatmapCellPayload {
  hardness_type: "long_chain" | "rate_pressure" | "schema_variance" | "multi_source";
  lane: RaceLane;
  dominant_tag: FailureTag;
  recovery_rate: { num: number; den: number };
  sample_run_id: string;
}

export interface HeatmapPayload {
  cells: HeatmapCellPayload[];
  baseline: HeatmapBaseline;
}

export async function fetchRaceHeatmap(): Promise<HeatmapPayload> {
  const res = await fetch(`/api/race/heatmap`);
  if (!res.ok) throw new Error(`Heatmap fetch failed: ${res.status}`);
  return (await res.json()) as HeatmapPayload;
}
```

**Imports update needed at top of file** (`client.ts:13`): add `FailureTag`, `RaceLane` to existing import:
```ts
import type { RaceEvent, FailureTag, RaceLane } from "../types/race";
```

**Pattern notes:**
- `requestJson<T>` wrapper (`client.ts:41-65`) is NOT used for race endpoints — `fetchRaceReplay` uses bare `fetch` for path-construction security (T-08-04 belt-and-suspenders). `fetchRaceHeatmap` follows the same convention for consistency, even though no path param escapes.
- Backend ships `"multi_source"` (not `"multi_source_synthesis"`) — type union spelled accordingly.

---

### `frontend/src/lib/types/race.ts` — Heatmap types (type definitions)

**Analog:** `race.ts:5-10` (`FailureTag` union) + `race.ts:43-53` (`LaneState` interface block).

**Existing type-block pattern** (verbatim, `race.ts:5-12`):
```ts
export type FailureTag =
  | "recovered"
  | "gave_up"
  | "kept_going_without_noticing"
  | "kept_going_to_failure"
  | "indeterminate";

export type RaceLane = "pure_mcp" | "pure_a2a" | "hybrid";
```

**Phase 9 addition pattern (Plan 09-04):** append closed-set unions + interfaces:
```ts
// HEAT-01 / HEAT-02 cell + payload types. Backend HardnessType uses "multi_source"
// (matches race/types.py:26); HeatmapScaffold uses "multi_source_synthesis" — the
// HardnessFailureHeatmap wrapper renames at the transform boundary.
export type HardnessTypeBackend =
  | "long_chain"
  | "rate_pressure"
  | "schema_variance"
  | "multi_source";

export interface HeatmapCellPayload {
  hardness_type: HardnessTypeBackend;
  lane: RaceLane;
  dominant_tag: FailureTag;
  recovery_rate: { num: number; den: number };
  sample_run_id: string;
}

export interface HeatmapBaseline {
  model: string;
  seed: number;
  task_ids: string[];
}

export interface HeatmapPayload {
  cells: HeatmapCellPayload[];
  baseline: HeatmapBaseline;
}
```

**Note on RunMetaEvent (D-58):** Optional addition to the `RaceEvent` discriminated union. Phase 9 D-59 explicitly DEFERS the `type`/`event_type` normalization — frontend `useRaceReplay` doesn't deep-consume events, so `RunMetaEvent` need NOT be added to the union in Phase 9. If planner adds it, mirror the existing closed-union shape:
```ts
| { type: "run_meta"; lane?: RaceLane; model: string; seed: number; task_id: string; run_id: string }
```

---

### `frontend/src/features/race/RacePage.tsx` — heatmap slot wire (page composition)

**Analog:** `RacePage.tsx:177` (current `<HeatmapScaffold cells={heatmapCells} />` slot — one-line replace).

**Existing slot** (verbatim, `RacePage.tsx:108-110, 177`):
```tsx
// Heatmap cells — empty in Phase 8; HeatmapScaffold renders heatmap-empty overlay (D-47).
// Phase 9 wires actual cells from the heatmap data API.
const heatmapCells = {};
// ...
<HeatmapScaffold cells={heatmapCells} />
```

**Phase 9 modification pattern (Plan 09-04):**
1. Replace import on line 19:
   ```tsx
   // BEFORE:
   import { HeatmapScaffold } from "./components/HeatmapScaffold";
   // AFTER:
   import { HardnessFailureHeatmap } from "./components/HardnessFailureHeatmap";
   ```
2. Delete the dead `heatmapCells` constant + comment (lines 108-110).
3. Update the `derivePageState` call: `heatmap_has_data` is no longer hardcoded `false` — it should derive from a future `data?.cells.length > 0` check. **For Plan 09-04 simplicity**, planner may keep `heatmap_has_data = false` (Phase 9 verification gates `heatmap-empty` page-state through the wrapper's empty-state pass-through to `HeatmapScaffold`).
4. Replace line 177:
   ```tsx
   // BEFORE:
   <HeatmapScaffold cells={heatmapCells} />
   // AFTER:
   <HardnessFailureHeatmap />
   ```

**Key contract preservation:** `HardnessFailureHeatmap` owns its own data fetch + transform → HeatmapScaffold composition. RacePage stops hardcoding empty `cells` (the empty-state overlay still surfaces correctly when the API returns `{cells: []}` because the wrapper passes `{}` to the scaffold).

---

## Shared Patterns

### Pattern 1: Module-level constant + frozen dataclass (D-12, D-28, D-56)

**Source:** `src/a2a_vs_mcp/race/runs.py:22-25`, `src/a2a_vs_mcp/race/types.py:22-37`, `src/a2a_vs_mcp/race/harness.py:53-58`.
**Apply to:** `src/a2a_vs_mcp/race/config.py` (NEW).
**Pattern:**
- Module-level singleton constant binding (e.g., `RUNS_DIR`, `MODEL`, `SEED_DISCLOSURE`, `HEATMAP_BASELINE`).
- For composite values, use `@dataclass(frozen=True)` + `to_dict()` method.
- All-caps constant name. Type annotation on the binding.
- Module docstring opens with the controlling decision IDs.
```python
HEATMAP_BASELINE: HeatmapBaseline = HeatmapBaseline(...)
```

### Pattern 2: Validate-then-load route prologue (Security V12)

**Source:** `src/a2a_vs_mcp/web.py:863-868` (race_ws prologue) + `src/a2a_vs_mcp/race/replay.py:48-63` (`load_run`).
**Apply to:** Both new routes in `web.py` (replay route especially; heatmap route doesn't take a path param so only handler structure applies).
**Pattern:**
- Path-traversal guard via `_validate_run_id` BEFORE any path resolution.
- `ValueError` → HTTPException 400 (or ws close 4400).
- `FileNotFoundError` → HTTPException 404.
- Imports already shipped in `web.py:43-44`.

### Pattern 3: Pure functional aggregator over event lists (D-37)

**Source:** `src/a2a_vs_mcp/race/metrics.py` entire module.
**Apply to:** `src/a2a_vs_mcp/race/heatmap.py` aggregator core.
**Pattern:**
- No I/O in the aggregator function itself; caller passes pre-loaded events.
- `next((e for e in events if e.get("event_type") == "X"), None)` idiom for typed event lookup.
- Return `dict[str, Any]` with stable key shape.
- Module docstring states: "Counts are NEVER stored; they're recomputed."
- Cache, if any, lives at module-level (`_CACHE: dict[tuple, ...] = {}`); invalidated by external caller.

### Pattern 4: React hook with `let active = true` cleanup (T-08-05)

**Source:** `frontend/src/features/race/hooks/useRaceReplay.ts:43-67`.
**Apply to:** `frontend/src/features/race/hooks/useRaceHeatmap.ts`.
**Pattern:**
- `let active = true` flag at the top of `useEffect`.
- All `setState` writes guarded by `if (active)`.
- Cleanup function returns `() => { active = false; }`.
- `void fetchX().then().catch().finally()` chain.
- Distinguishes mount-time error from cleanup-time stale write.

### Pattern 5: Frontend data wrapper around rendering primitive (D-46, D-47)

**Source:** Phase 8 `RaceLaneCard` consumes `LaneState` from `useRaceStream`; new `HardnessFailureHeatmap` mirrors this for `HeatmapScaffold` consumption.
**Apply to:** `frontend/src/features/race/components/HardnessFailureHeatmap.tsx`.
**Pattern:**
- Wrapper owns: data fetch (via hook) + transform + non-grid surfaces (legend, footer, pill).
- Rendering primitive (HeatmapScaffold) stays UNTOUCHED — Phase 8 contract intact.
- Empty cells `{}` automatically trigger HeatmapScaffold's `heatmap-empty-overlay` (D-47).

### Pattern 6: Pytest parametrize over fixture file glob

**Source:** `tests/race/test_replay_stub.py:16, 41-50` (FIXTURES path constant + JSON read pattern).
**Apply to:** `tests/race/test_replay_symmetry.py`, `tests/test_recovery_calibration.py`.
**Pattern:**
```python
FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "traces"

@pytest.mark.parametrize(
    "fixture_path",
    sorted(FIXTURES.glob("*.json")),
    ids=lambda p: p.stem,
)
def test_X(fixture_path):
    fx = json.loads(fixture_path.read_text())
    # assert against fx["expected_terminal_tag"] / fx["score_pass"]
```

### Pattern 7: Direct callback wiring (D-39, D-54)

**Source:** `src/a2a_vs_mcp/race/harness.py:465-474` (ws_emitter direct call).
**Apply to:** `src/a2a_vs_mcp/race/harness.py` (post-race_done invalidate_cache call).
**Pattern:**
- No new pub-sub primitive; harness imports the callable from the cache module.
- Single line at the post-race_done emission point.
- Module-load-order safety via top-level import (preferred over inline import).

---

## No Analog Found

| File | Role | Reason |
|---|---|---|
| (none) | — | Every Phase 9 file has a strong existing analog. The codebase ALREADY ships every primitive Phase 9 needs (Detector, load_run, _validate_run_id, MANAGER, HeatmapScaffold, useRaceReplay, fetchRaceReplay, FailureTagColor, RUNS_DIR, RunWriter). Phase 9 is wiring + 2 routes + 2 tests + 1 wrapper + 1 module constant. RESEARCH.md "all upstream primitives are already shipped" claim verified. |

---

## Metadata

**Analog search scope:**
- `src/a2a_vs_mcp/race/` (full module)
- `src/a2a_vs_mcp/web.py` (lines 1-80 imports, 820-898 race-route block)
- `frontend/src/features/race/` (components, hooks, page)
- `frontend/src/lib/api/client.ts`
- `frontend/src/lib/types/race.ts`
- `frontend/src/lib/trace/eventColors.ts`
- `tests/race/` (fixtures + tests)
- `tests/conftest.py`

**Files scanned:** 14 source files + 1 fixture for envelope verification.
**Pattern extraction date:** 2026-04-29
**Confidence:** HIGH — every analog verified inline; line numbers and signatures accurate at time of mapping.

---

## PATTERN MAPPING COMPLETE
