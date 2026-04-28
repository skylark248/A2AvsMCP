---
phase: 07-race-backend-lanes-harness-recovery
plan: 07
subsystem: mcp-server
tags: [mcp-server, fastmcp, transport, contextvars, race]

# Dependency graph
requires:
  - phase: 07
    provides: race/mocks/{github,calendar,travel}.py (Plan 03) + race/failure.inject_fault chokepoint (Plan 06-04)
provides:
  - 3 race MCP servers (race_github, race_calendar, race_travel) wrapping mocks via FastMCP
  - mcp_servers/race_context.py contextvars helper (recorder + run_id propagation)
  - SERVER_BUILDERS registry entries for in_process construction by Plan 09 runners
affects: [07-09-pure-mcp-runner, 07-10-hybrid-runner, 07-11-chokepoint-tests]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "FastMCP @mcp.tool() decorator (single-file server, build_server() factory)"
    - "contextvars.ContextVar for in-process recorder/run_id propagation across MCP tool fns"
    - "Lambda-with-**_-kwargs SERVER_BUILDERS entries to absorb path-arg-free builders"

key-files:
  created:
    - src/a2a_vs_mcp/mcp_servers/race_context.py
    - src/a2a_vs_mcp/mcp_servers/race_github.py
    - src/a2a_vs_mcp/mcp_servers/race_calendar.py
    - src/a2a_vs_mcp/mcp_servers/race_travel.py
  modified:
    - src/a2a_vs_mcp/mcp/client.py

key-decisions:
  - "in_process transport selected for race lanes — stdio runs subprocess and contextvars do not cross process boundaries (RESEARCH §5)"
  - "current_run_id() raises RuntimeError when contextvar unset, surfacing stray non-race callers loudly instead of silently generating UUIDs"
  - "_build_server dispatch extended with race branch — existing endswith chain only handled db_server/docs_server (Rule 3 deviation, blocking issue)"
  - "Tool functions hold a single delegating call into race.mocks.<module> — no duplication of inject_fault logic preserves D-25 chokepoint discipline"

patterns-established:
  - "Race MCP server shape: build_server() factory + 3-arg argparse main() + import-from-mocks pattern"
  - "Runner-side wrap: set_mcp_tool_context(recorder=..., run_id=...) ... try: client.call(...) finally: MCP_TOOL_CONTEXT.reset(tok)"

requirements-completed: [RACE-02, RACE-07]

# Metrics
duration: ~14min
completed: 2026-04-29
---

# Phase 7 Plan 07: Race MCP Server Adapters Summary

**Three FastMCP servers (race_github / race_calendar / race_travel) wrapping the Plan 03 mocks, plus a contextvars helper that propagates TraceRecorder + run_id from runner into tool function bodies — enabling Plan 09 pure_mcp/hybrid lanes to call race tools via the real MCPClient without bypassing D-25's single fault chokepoint.**

## Performance

- **Duration:** ~14 min
- **Started:** 2026-04-29T02:25:00+05:30
- **Completed:** 2026-04-29T02:39:00+05:30
- **Tasks:** 5
- **Files modified:** 5 (4 created, 1 modified)

## Accomplishments

- 3 FastMCP servers up — `race_github` (3 tools), `race_calendar` (2 tools), `race_travel` (3 tools), all delegating into `race.mocks.<module>` so D-25 chokepoint stays single-source.
- New `mcp_servers/race_context.py` contextvars module — runner sets `(recorder, run_id)` before `client.call()`, tool fns read at invoke time. Loud-fail when unset.
- All 3 race builders registered in `SERVER_BUILDERS` and reachable through `MCPClient(server_module=..., transport="in_process")`. End-to-end smoke test confirmed: `read_file` round-trip via in_process transport returns synthetic content.
- All 37 race tests still green; all 109 v1 tests still green — no regression.

## Task Commits

1. **Task 1: race_context contextvars helper** — `5d4716d` (feat)
2. **Task 2: race_github MCP server (3 tools)** — `61b03c0` (feat)
3. **Task 3: race_calendar MCP server (2 tools)** — `ed2ed7c` (feat)
4. **Task 4: race_travel MCP server (3 tools)** — `cabc276` (feat)
5. **Task 5: SERVER_BUILDERS wiring + _build_server race branch** — `336b5aa` (feat)

## Files Created/Modified

- `src/a2a_vs_mcp/mcp_servers/race_context.py` — ContextVar-backed propagation of recorder/run_id; set_mcp_tool_context / current_recorder / current_run_id
- `src/a2a_vs_mcp/mcp_servers/race_github.py` — FastMCP server with get_repo_metadata, list_files, read_file (delegate to race.mocks.github)
- `src/a2a_vs_mcp/mcp_servers/race_calendar.py` — FastMCP server with get_free_busy, propose_time (delegate to race.mocks.calendar)
- `src/a2a_vs_mcp/mcp_servers/race_travel.py` — FastMCP server with search_flights, search_hotels, book_itinerary (delegate to race.mocks.travel)
- `src/a2a_vs_mcp/mcp/client.py` — added 3 SERVER_BUILDERS entries; extended _build_server() dispatch with race branch (no path args; reads contextvars)

## Decisions Made

- **in_process over stdio for race lanes** — stdio runs MCP server in a subprocess, and contextvars do not cross process boundaries. Since runner-set recorder/run_id must reach tool fns, in_process (same Python process) is the only viable transport for race. RESEARCH §5 confirmed.
- **Loud-fail on missing contextvar** — `current_run_id()` raises `RuntimeError` rather than auto-generating a UUID. A stray non-race caller produces an immediate, visible error instead of silently corrupting downstream traces.
- **No shared base for race servers** — each server is a verbatim copy of the db_server.py shape (build_server() + main() argparse). RESEARCH §10 Q1 explicitly recommended no abstraction; ~50 LOC each, 3 files, total < 200 LOC.
- **Lambda absorbers for race builders in SERVER_BUILDERS** — race builders take no kwargs (they read contextvars), but the in_process build path must remain compatible with v1 builders that take Path args. `lambda **_: race_x.build_server()` absorbs unused kwargs cleanly without touching v1 entries.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Extended `_build_server` dispatch to handle race servers**
- **Found during:** Task 5 (SERVER_BUILDERS wiring)
- **Issue:** `MCPClient._build_server` (mcp/client.py line 234-239) had hardcoded `endswith("db_server")` / fallback `endswith("docs_server")` dispatch, requiring `db-path` or `docs-dir` kwargs. Adding race builders to SERVER_BUILDERS alone would not make them reachable via `transport='in_process'` — the dispatch would call them with a missing-key `Path(normalized_args["docs-dir"])` lookup and KeyError.
- **Fix:** Made `docs_server` an explicit branch and added a fallthrough `return builder(**normalized_args)` for race servers (or any future no-path server). Race lambdas accept `**_` so the empty-kwargs call goes through cleanly.
- **Files modified:** `src/a2a_vs_mcp/mcp/client.py`
- **Verification:** End-to-end smoke test (MCPClient → race_github → read_file) returns synthetic content; 37 race tests + 109 v1 tests green.
- **Committed in:** `336b5aa` (Task 5 commit)

**2. [Rule 1 - Bug-style] Reworded docstring to avoid chokepoint-grep false positive**
- **Found during:** Task 2 (race_github acceptance criteria)
- **Issue:** Acceptance criteria required `grep -c "inject_fault\|raise RuntimeError" race_github.py` to output `0` (Plan 11 will codify this as the chokepoint test). The original docstring contained the literal string `race.failure.inject_fault` as an explanatory reference, which matched the grep.
- **Fix:** Reworded the comment to `race.failure module's chokepoint` while preserving the educational intent. Applied the same wording to race_calendar.py and race_travel.py for consistency.
- **Files modified:** `race_github.py`, `race_calendar.py`, `race_travel.py`
- **Verification:** `grep -c "inject_fault\|raise RuntimeError" race_github.py` outputs `0`.
- **Committed in:** Folded into the Task 2/3/4 commits (no separate commit; written before commit).

---

**Total deviations:** 2 auto-fixed (1 Rule 3 blocking, 1 Rule 1 bug-style preflight)
**Impact on plan:** Both fixes essential — without the dispatch extension, Plan 09 runners cannot construct race servers via in_process. The grep wording is a chokepoint discipline guard for Plan 11. No scope creep.

## Issues Encountered

None substantive. The two items above were caught at verification time and resolved inline.

## Verification Results

| Check | Result |
|-------|--------|
| `grep -c "@mcp.tool()" race_github.py` | 3 ✓ |
| `grep -c "@mcp.tool()" race_calendar.py` | 2 ✓ |
| `grep -c "@mcp.tool()" race_travel.py` | 3 ✓ |
| `grep -c "github_mock\\." race_github.py` | 3 ✓ |
| `grep -c "calendar_mock\\." race_calendar.py` | 2 ✓ |
| `grep -c "travel_mock\\." race_travel.py` | 3 ✓ |
| `grep -c "inject_fault\\|raise RuntimeError" race_github.py` | 0 ✓ |
| All 3 builders registered in SERVER_BUILDERS | ✓ |
| `pytest tests/race/ -x -q` | 37 passed |
| `pytest tests/ -x -q --ignore=tests/race` | 109 passed, 4 subtests passed |
| End-to-end smoke (MCPClient → race_github → read_file) | OK |
| LOC: race_github=62, race_calendar=51, race_travel=58, race_context=46 | meets min_lines (50/40/60) |

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- **Plan 09 (pure_mcp + hybrid runners) unblocked.** Runners construct via:
  ```python
  client = MCPClient(server_module="a2a_vs_mcp.mcp_servers.race_github", trace=rec, project_root=root, transport="in_process")
  tok = set_mcp_tool_context(recorder=rec, run_id=run_id)
  try:
      client.call("get_repo_metadata", {"repo_id": "demo-org/api-gateway"})
  finally:
      MCP_TOOL_CONTEXT.reset(tok)
  ```
- **Plan 11 chokepoint grep test** can extend Phase 6 D-13 enforcement to `mcp_servers/race_*.py` — these files contain ZERO direct `inject_fault` / `raise RuntimeError` references in tool bodies.
- **Plan 08 (task configs + registries)** can independently reference these tool names in TARGETS arrays.

## Self-Check: PASSED

All 4 created files exist on disk; all 5 task commits found in git log.

---
*Phase: 07-race-backend-lanes-harness-recovery*
*Completed: 2026-04-29*
