---
phase: 07-race-backend-lanes-harness-recovery
plan: 03
subsystem: race/mocks
tags: [mocks, fixtures, fault-chokepoint, contextvars, wave-1]
requires:
  - 07-01  # InjectedFaultError + race/failure.inject_fault chokepoint
  - phase-06  # FaultKind enum, TraceRecorder (race-mode), inject_fault contract
provides:
  - "race/mocks package with ContextVar-based ACTIVE_FAULTS registry"
  - "github fixture mock (3 callables) routed through inject_fault"
  - "calendar fixture mock (2 callables) routed through inject_fault"
  - "travel fixture mock (3 callables) routed through inject_fault"
  - "data/race/fixtures/{github,calendar,travel}/*.json read-only fixtures"
affects:
  - "Plan 07-05 (mcp_servers/race_*.py): wraps these mocks behind real MCP transport"
  - "Plan 07-09 (pure_a2a runner): registers fixture-backed agents that call into these mocks"
  - "Plan 07-11 (CI grep test): extends D-13 IRON RULE enforcement to these files"
tech-stack:
  added:
    - "contextvars.ContextVar (stdlib) for per-run fault registry"
  patterns:
    - "single fault chokepoint (D-25): every mutation flows through race.failure.inject_fault"
    - "lazy fixture load via Path(__file__).resolve().parents[4]"
    - "module-level helper functions (no class) — matches src/a2a_vs_mcp/evidence.py idiom"
key-files:
  created:
    - src/a2a_vs_mcp/race/mocks/__init__.py
    - src/a2a_vs_mcp/race/mocks/github.py
    - src/a2a_vs_mcp/race/mocks/calendar.py
    - src/a2a_vs_mcp/race/mocks/travel.py
    - data/race/fixtures/github/repos.json
    - data/race/fixtures/calendar/calendars.json
    - data/race/fixtures/travel/inventory.json
  modified:
    - .gitignore  # surgical un-ignore of /data/race/fixtures/** (Rule 3)
decisions:
  - "ACTIVE_FAULTS lives at package level (mocks/__init__.py) so all three mock modules share the same ContextVar — no per-module state desync."
  - "set_active_faults always copies the dict (`dict(faults)`) so two runs cannot share dict identity even by accident."
  - "FIXTURES_PATH uses Path(__file__).resolve().parents[4] for repo-root anchoring; verified at runtime in worktree."
  - "Fixture data was constructed so the 3 calendars share exactly one mutual 60-min window at 2026-05-04T17:00 UTC; propose_time returns this deterministic slot."
  - "book_itinerary derives confirmation_id from run_id[:8] for replay determinism."
metrics:
  duration: ~10 minutes
  completed: 2026-04-28
  tasks: 5
  files_created: 7
  files_modified: 1
  commits: 5
---

# Phase 07 Plan 03: race-backend-lanes-harness-recovery — Mocks + Fixtures Summary

Wave-1 mocks landed: three fault-chokepointed mock modules (github / calendar / travel) plus their JSON fixtures, all routing every mutation through the Phase 6 `inject_fault()` IRON RULE chokepoint.

## What Shipped

- `src/a2a_vs_mcp/race/mocks/__init__.py` — package marker with `ACTIVE_FAULTS: ContextVar[dict[str, ActiveFault]]` for per-run fault arming. Helpers: `set_active_faults()` (returns Token, dict-copies for identity safety), `get_active_fault(target)`. Per RESEARCH §10 Q2 — contextvars guarantee per-task isolation in asyncio + per-thread isolation in sync.
- `src/a2a_vs_mcp/race/mocks/github.py` — 3 callables: `get_repo_metadata`, `list_files`, `read_file`. Each loads `data/race/fixtures/github/repos.json`, looks up the active fault for its target string, and routes mutation through `inject_fault()`.
- `src/a2a_vs_mcp/race/mocks/calendar.py` — 2 callables: `get_free_busy(owner)`, `propose_time(owners, duration_min)`. `propose_time` returns the canonical mutual 60-min slot at `2026-05-04T17:00:00+00:00` (constructed-by-fixture-design).
- `src/a2a_vs_mcp/race/mocks/travel.py` — 3 callables: `search_flights`, `search_hotels`, `book_itinerary`. Booking math: `sum(flight prices) + hotel.nightly_usd * nights`. Confirmation id is deterministic on `run_id[:8]`.
- `data/race/fixtures/github/repos.json` — 5 repo records (`demo-org/{api-gateway,event-pipeline,cli-tools,web-dashboard,ml-inference}`), each with ≥3 modules + entry_point + files + stars.
- `data/race/fixtures/calendar/calendars.json` — 3 calendars (alice@LA, bob@NY, carol@London) with overlapping free windows engineered around the mutual 17:00Z slot.
- `data/race/fixtures/travel/inventory.json` — 5 SFO↔JFK flights + 3 NYC hotels.

## must_haves Verified

| Truth | Status |
|-------|--------|
| `race/mocks/github.py` exposes get_repo_metadata, list_files, read_file routed through inject_fault() | yes |
| `race/mocks/calendar.py` exposes get_free_busy, propose_time routed through inject_fault() | yes |
| `race/mocks/travel.py` exposes search_flights, search_hotels, book_itinerary routed through inject_fault() | yes |
| `race/mocks/__init__.py` declares ACTIVE_FAULTS as contextvars.ContextVar | yes |
| `data/race/fixtures/github/repos.json` contains exactly 5 repo records with stable ids | yes (5) |
| `data/race/fixtures/calendar/calendars.json` contains exactly 3 calendar records with overlapping free windows | yes (3) |
| `data/race/fixtures/travel/inventory.json` contains flights and hotels arrays | yes (5 flights, 3 hotels) |

## Verification Run

```
PYTHONPATH=src python3 -c "from a2a_vs_mcp.race.mocks import github, calendar, travel; print('OK')"
# OK

python3 -c "import json; g=json.load(open('data/race/fixtures/github/repos.json')); ..."
# github_repos=5 calendars=3 flights=5 hotels=3 -- OK

PYTHONPATH=src python3 -m pytest tests/race/ -q
# 37 passed in 0.49s   (Phase 6 regression — green)
```

Per-mock chokepoint count (`grep -c '^        return inject_fault' <file>`):
- github.py — 3 (matches 3 public callables)
- calendar.py — 2 (matches 2 public callables)
- travel.py — 3 (matches 3 public callables)

Total = 8 chokepointed returns across 8 public callables. **Every public method routes through `inject_fault()` — no bypass paths.**

## Decisions Made

1. **ACTIVE_FAULTS at package scope** — putting the ContextVar in `mocks/__init__.py` (rather than each per-mock module) means every mock module reads the same registry; no per-module state desync.
2. **Identity-safe `set_active_faults()`** — always pass `dict(faults)` to `ContextVar.set()` so two runs cannot accidentally share the same dict object even if a caller passes the same literal twice.
3. **Calendar fixtures engineered for a single mutual window** — `propose_time` is a deterministic stub returning `2026-05-04T17:00:00+00:00` (10:00 PT / 13:00 ET / 18:00 BT). The fixture free/busy data was authored so this is the only mutually-free 60-min slot, which keeps the (Plan 08) structural test trivial.
4. **`book_itinerary` confirmation_id derived from `run_id[:8]`** — same run_id ⇒ same confirmation_id; replay-safe by construction.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 — Blocking] `.gitignore` blocked fixture commits**
- **Found during:** Task 2 (`git add data/race/fixtures/...` failed with "ignored by .gitignore")
- **Issue:** Existing `.gitignore` had a broad `data/` rule plus `/data/runs/`, but the plan requires checking in `data/race/fixtures/**` JSON.
- **Fix:** Added a surgical un-ignore block re-allowing only `/data/race/fixtures/**` while keeping `/data/*` and `/data/race/*` ignored (so `data/runs/`, `data/seeds/`, etc. stay ignored). Verified with `git check-ignore -v` before committing.
- **Files modified:** `.gitignore`
- **Commit:** `f537705`

### Plan-text observations (not deviations)

The plan's Task 3/4/5 acceptance criterion `grep -c "inject_fault(" <mock>.py` outputs `N` (one per public function) under-counts: the plan-mandated docstring text contains the string `inject_fault()`, so the actual grep total is `N + docstring_mentions` (4–5 instead of 3, etc.). The functional intent — each public callable routes through `inject_fault()` — is satisfied; verified instead via `grep -c '^        return inject_fault' <file>` which counts only the call-site at the chokepoint indentation. No code change needed; flagged for plan author.

## Threat Surface

No new surface introduced beyond the plan's `<threat_model>`. Mitigations enforced:
- T-07-03-01 (mutation outside chokepoint) — `grep -c '^        return inject_fault'` matches the public function count exactly; no direct `response[...] =` mutation found.
- T-07-03-02 (path traversal) — `FIXTURES_PATH` is a hard-coded `Path(__file__).resolve().parents[4] / ...`; no user input touches the path.
- T-07-03-03 (deserialization) — all 3 fixture loads use `json.loads()` (safe by spec).
- T-07-03-04 (cross-run pollution) — `ACTIVE_FAULTS` is a `ContextVar` and `set_active_faults()` always passes a fresh dict copy.

## Known Stubs

None — all functions return live fixture-derived data. `read_file` returns synthetic content (`# {repo_id}::{file_path}\n# (synthetic content for mock)\n`) by design; this is the plan's intended behavior since real file content is not shipped, and the downstream `summarize_repo` rubric scores against fixture metadata, not file content.

## Commits

| Task | Commit | Subject |
|------|--------|---------|
| 1 | `e5eb21d` | feat(07-03): add race/mocks package with ContextVar fault registry |
| 2 | `f537705` | feat(07-03): add race fixture JSONs for 3 v1 tasks |
| 3 | `7c46ed1` | feat(07-03): add race github mock with 3 chokepointed callables |
| 4 | `b95f653` | feat(07-03): add race calendar mock with chokepointed get_free_busy + propose_time |
| 5 | `07c21fe` | feat(07-03): add race travel mock with chokepointed search + book |

## Self-Check: PASSED

- All 7 created files exist on disk.
- All 5 task commits resolvable via `git log --oneline`.
- Phase 6 regression suite: 37/37 passing.
- Top-level mock import works.
- Fixture record counts (5/3/5+3) match must_haves.
- 8 chokepointed `return inject_fault` lines for 8 public callables — no bypass paths.
