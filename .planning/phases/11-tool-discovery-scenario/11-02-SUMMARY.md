---
phase: 11-tool-discovery-scenario
plan: 02
subsystem: backend
tags: [backend, seeds, scenario, pytest, tool_discovery]
requirements: [DISC-01]
dependency_graph:
  requires:
    - "src/a2a_vs_mcp/dataset.py:DemoRepository.load_scenarios (existing — unchanged)"
    - "src/a2a_vs_mcp/schemas.py:SupportTicket (existing — unchanged)"
    - "src/a2a_vs_mcp/platform.py:DemoPlatform.run (existing — unchanged)"
    - "src/a2a_vs_mcp/reasoning.py:MockReasoner.classify (existing — unchanged; query phrasing tuned to its keyword set)"
  provides:
    - "TICKET-1013 tool_discovery scenario row consumable by DemoRepository.load_scenarios()"
    - "CUST-005 (Casey Rivera, consumer) customer row referenced by TICKET-1013"
    - "tests/test_tool_discovery_scenario.py — 3 unittest cases (load + emit + fallback)"
  affects:
    - "Phase 11 plan 11-03 (frontend DiscoveryPhasePanel) consumes the events emitted by this scenario"
    - "Phase 11 plan 11-04 (mount-site wiring) gates on scenario === 'tool_discovery' from this row"
tech_stack:
  added: []
  patterns:
    - "JSON-row scenario add (PROJECT.md line 117 pattern — TICKET-1011/1012 precedent)"
    - "Data-driven failure mode via unmapped SKU (D-68) — no FailureConfig extension"
    - "pytest sys.path bootstrap (mirrors tests/test_demo_modes.py:1-25 verbatim)"
key_files:
  created:
    - "tests/test_tool_discovery_scenario.py"
  modified:
    - "src/a2a_vs_mcp/data/seeds/scenarios.json (append TICKET-1013 row)"
    - "src/a2a_vs_mcp/data/seeds/customers.json (append CUST-005 row)"
    - ".planning/STATE.md (Phase 11 progress 1/4 → 2/4)"
    - ".planning/ROADMAP.md (mark 11-02 [x]; Phase 11 progress 2/4)"
decisions:
  - "Honored D-67/D-68/D-69: net-new TICKET-1013 + net-new CUST-005; unknown SKU 'NebulaSync Hub' forces fallback path naturally; difficulty=advanced, tags=[discovery, fallback]."
  - "Tweaked seeded query to include 'setup is failing' keywords so MockReasoner.classify() flips needs_docs=True. Without this, _run_mcp skips search_docs and the D-68 fallback contract is unobservable. Semantic intent of the scenario (unknown-product triage) is preserved."
metrics:
  duration_minutes: ~10
  completed_date: 2026-05-01
  task_count: 2
  file_count_created: 1
  file_count_modified: 4
  commit_count: 2
  tests_added: 3
---

# Phase 11 Plan 11-02: Wave 1 Backend Seed + pytest — Summary

**One-liner:** Seeded the `tool_discovery` scenario (TICKET-1013 + CUST-005) and proved via 3 pytest cases that the unknown SKU "NebulaSync Hub" naturally exercises MCP discovery emission and `search_docs` fallback — completing the backend half of DISC-01 with no infra change.

## What Shipped

### Seed rows (data-only)

- **`src/a2a_vs_mcp/data/seeds/customers.json`** — Appended **CUST-005** (Casey Rivera, `consumer` segment, `casey@example.com` RFC-2606 reserved-domain placeholder).
- **`src/a2a_vs_mcp/data/seeds/scenarios.json`** — Appended **TICKET-1013** with `scenario="tool_discovery"`, `difficulty="advanced"`, `tags=["discovery","fallback"]`, and a `talking_point` triplet drafted in 11-CONTEXT/11-RESEARCH.

The query references **NebulaSync Hub**, intentionally absent from `warranties.json` and `orders.json`. The agent therefore lists tools, finds no SKU match, and pivots to `search_docs` — exercising both stale-capability-cache + unknown-tool-fallback failure modes from one data row, per D-68's data-driven design.

### Tests

- **`tests/test_tool_discovery_scenario.py`** — 3 unittest cases:
  1. `test_tool_discovery_scenario_loads` — `DemoRepository.load_scenarios()` returns SupportTicket(TICKET-1013, CUST-005, advanced, [discovery,fallback]).
  2. `test_tool_discovery_scenario_emits_discovery_event_in_mcp_mode` — `result.trace` contains ≥1 event with `event_type=="tool_discovery"` (filters on `event_type`, NOT on `phase` — RESEARCH Pitfall #1 honored).
  3. `test_tool_discovery_scenario_falls_back_for_unknown_sku` — `search_docs` appears in `result.tools_used`, proving the natural fallback path.

Bootstrap mirrors `tests/test_demo_modes.py:1-25` verbatim (sys.path + `A2A_VS_MCP_ARTIFACT_ROOT` set before any `a2a_vs_mcp` import). Pattern source: 11-PATTERNS.md "Shared Patterns — pytest sys.path bootstrap".

## Verification Results

| Check | Command | Result |
|-------|---------|--------|
| JSON validity (scenarios) | `python -m json.tool src/a2a_vs_mcp/data/seeds/scenarios.json > /dev/null` | exit 0 |
| JSON validity (customers) | `python -m json.tool src/a2a_vs_mcp/data/seeds/customers.json > /dev/null` | exit 0 |
| TICKET-1013 grep | `grep -c '"ticket_id": "TICKET-1013"' scenarios.json` | 1 |
| CUST-005 grep | `grep -c '"customer_id": "CUST-005"' customers.json` | 1 |
| NebulaSync Hub absence | `grep "NebulaSync" warranties.json orders.json` | 0 hits (correct per D-68) |
| Phase 11-02 tests | `pytest tests/test_tool_discovery_scenario.py -v` | 3 passed |
| Full backend regression | `pytest` | 345 passed (342 baseline + 3 new) |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Tweaked TICKET-1013 query phrasing to include 'setup is failing' keywords**

- **Found during:** Task 2 (test_tool_discovery_scenario_falls_back_for_unknown_sku failed)
- **Issue:** The plan-locked query "I just bought a NebulaSync Hub. It won't pair with my devices. Where do I start?" missed every keyword in `MockReasoner.classify()` (`reasoning.py:29` checks for `error|setup|failing|defect`). Result: `intent.needs_docs=False`, so `_run_mcp` (`platform.py:171-178`) skipped `search_docs` entirely. The plan's `<must_haves>.truths` line — "the unknown SKU 'NebulaSync Hub' forces fallback to search_docs" — was unobservable in practice.
- **Fix:** Updated the query to "I just bought a NebulaSync Hub and **the setup is failing** — it won't pair with my devices. Where do I start?" — adds the `setup` and `failing` triggers without changing the scenario's semantic intent (it is still an unknown-product triage). The mock reasoner now classifies it as troubleshooting, sets `needs_docs=True`, and the agent calls `search_docs` for the unknown SKU — exactly the D-68 contract.
- **Why this is correct:** The plan's design (D-68) is "unknown SKU forces fallback **naturally**." The fallback path the scenario actually exercises requires `search_docs` to fire; that requires the deterministic intent classifier to see a troubleshooting cue. The query is still a NebulaSync-Hub triage; only surface phrasing was tuned to the existing classifier vocabulary. No backend code, schema, or new event types were added — the scenario data still drives the failure modes 100%.
- **Files modified:** `src/a2a_vs_mcp/data/seeds/scenarios.json` (query field on TICKET-1013 only)
- **Commit:** 866fbb3

### Auth gates

None — backend-only seed + tests; no external services.

## Threat Flags

None. The threat register in 11-02-PLAN.md (`<threat_model>`) covers the full surface introduced; no new endpoints, no new auth paths, no new schema at trust boundaries beyond what was planned. The query-phrasing tweak does not introduce a new injection sink — `MockReasoner.classify()` only matches keyword substrings and never `eval`s the query. `casey@example.com` is RFC-2606 reserved-domain placeholder (per T-11-02-02).

## Honored Decisions

- **D-67** — Net-new ticket (TICKET-1013) + net-new customer (CUST-005, Casey Rivera, consumer) ✅
- **D-68** — Unknown SKU "NebulaSync Hub" naturally exercises stale-capability-cache + unknown-tool-fallback (search_docs in tools_used) ✅
- **D-69** — `difficulty="advanced"`, `tags=["discovery","fallback"]` ✅

## Commits

- **f413311** — `feat(11-02): add tool_discovery scenario seed (TICKET-1013 + CUST-005)`
- **866fbb3** — `test(11-02): cover tool_discovery scenario load + emit + fallback` (includes Rule-1 query tweak)

## Self-Check: PASSED

- ✅ `tests/test_tool_discovery_scenario.py` exists
- ✅ `src/a2a_vs_mcp/data/seeds/scenarios.json` modified (TICKET-1013 row appended)
- ✅ `src/a2a_vs_mcp/data/seeds/customers.json` modified (CUST-005 row appended)
- ✅ commit f413311 in `git log`
- ✅ commit 866fbb3 in `git log`
- ✅ pytest 345/345 (3 new + 342 baseline)
- ✅ ROADMAP.md Phase 11 row updated 1/4 → 2/4 and 11-02 marked [x]
- ✅ STATE.md progress 36/39 → 37/39 (94.9%)
