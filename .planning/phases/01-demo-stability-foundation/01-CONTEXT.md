# Phase 1: Demo Stability Foundation - Context

**Gathered:** 2026-04-22
**Status:** Ready for planning

<domain>
## Phase Boundary

Make all four demo modes (baseline, mcp, a2a, hybrid) run without crashes using `runtime=mock, transport=in_process`. Update dependency pins in `pyproject.toml`. Add a `FakeReasoningEngine` stub. Add a visible transport mode badge to the run header. Migrate the test suite from `unittest` to `pytest` + `pytest-asyncio` + `httpx` and add an async FastAPI integration test for MCP mode.

This phase does NOT add new scenarios, modify trace events, or touch comparison UI — that begins in Phase 2+.

</domain>

<decisions>
## Implementation Decisions

### Transport Badge (STAB-02)
- **D-01:** Badge appears in the **run header row** — next to the scenario name / mode selector. Always visible during a run so the presenter can confirm transport at a glance.
- **D-02:** Badge shows the **transport name only** (e.g., `in_process` / `stdio` / `http`). No extra labels; concise chip format.
- **D-03:** Implementation is a small MUI Chip component using the existing `transport` field already present in run result payloads.

### FakeReasoningEngine (STAB-04)
- **D-04:** Lives in `src/a2a_vs_mcp/reasoning.py` **alongside `MockReasoner` and `OpenAIReasoner`** — consistent with the existing pattern; importable from production code.
- **D-05:** Returns **canned realistic responses** — plausible customer support reasoning text per scenario type (order status, setup error, etc.). Must look convincing if the real LLM path is shown during demo day.
- **D-06:** Selected by `runtime="fake_llm"` (or similar env signal) so it can be injected in tests without an API key, while `runtime="llm"` still routes to `OpenAIReasoner`.

### Dependency Pins (STAB-03)
- **D-07:** `mcp[cli]>=1.27,<2` — upper bound prevents auto-upgrade into breaking v2 pre-alpha (`FastMCP` → `McpServer` rename).
- **D-08:** `a2a-sdk[http-server]==0.3.26` — safe patch bump from 0.3.25; do NOT jump to 1.0.0 (major breaking release).
- **D-09:** Pins go in `pyproject.toml` only — no lock file changes needed for this phase.

### Pytest Migration (STAB-05)
- **D-10:** Add `pytest>=8.0`, `pytest-asyncio>=0.24`, `httpx>=0.28` to `[project.optional-dependencies.dev]`.
- **D-11:** Migration style: **keep existing test logic**, add `pytest` as the runner. Existing `unittest.TestCase` classes continue to work under pytest — no full rewrite required. New tests write in native pytest style.
- **D-12:** Async FastAPI integration test: use `httpx.AsyncClient` + `ASGITransport` to exercise the full MCP mode request path through the FastAPI app (`POST /api/run` or equivalent) without spawning a real server.
- **D-13:** Add a `[tool.pytest.ini_options]` section to `pyproject.toml` with `asyncio_mode = "auto"`.

### Stability Pass (STAB-01)
- **D-14:** "Crash-free" means all 4 modes complete successfully for at least the existing scenarios under `runtime=mock, transport=in_process`. Verified by existing + new pytest tests passing cleanly.
- **D-15:** Claude's discretion on whether to add a `runtime=mock` guard or startup health check — not user-specified.

### Claude's Discretion
- Badge color / MUI color variant
- Exact `runtime` string name for `FakeReasoningEngine` (e.g., `"fake_llm"`, `"fake"`)
- `conftest.py` structure if needed for shared fixtures
- Whether to add `pytest.ini` or just `pyproject.toml` ini options

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project requirements
- `.planning/PROJECT.md` — Core value, constraints, out-of-scope boundaries
- `.planning/REQUIREMENTS.md` — STAB-01 through STAB-05 acceptance criteria

### Existing code (must read before implementing)
- `src/a2a_vs_mcp/reasoning.py` — Existing `MockReasoner` and `OpenAIReasoner` patterns; `FakeReasoningEngine` follows same structure
- `pyproject.toml` — Current dependency versions; update in-place
- `tests/test_demo_modes.py` — Existing unittest suite to migrate/extend
- `tests/test_web_ui.py` — Existing FastAPI test using `TestClient`; async integration test follows similar shape
- `frontend/src/features/run-workspace/RunWorkspacePage.tsx` — Run header location for transport badge

### Research
- `.planning/research/STACK.md` — pytest/httpx recommendations with rationale
- `.planning/research/PITFALLS.md` — C2 (transport fallback) and C3 (anyio loop nesting) context for stability pass

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `src/a2a_vs_mcp/reasoning.py` — `MockReasoner` class is the direct pattern for `FakeReasoningEngine`; add the new class in the same file following the same interface
- `frontend/src/features/run-workspace/RunWorkspacePage.tsx` — existing run header; MUI `Chip` component from the same MUI version is already in use in the project
- `tests/test_demo_modes.py` — existing `DemoPlatform(runtime="mock")` pattern reusable as-is under pytest

### Established Patterns
- All runtime variants (`mock`, `llm`) are selected at `DemoPlatform` construction time via the `runtime` parameter
- `TestClient` (synchronous) is used in `test_web_ui.py`; the async integration test should use `httpx.AsyncClient(app=app, transport=ASGITransport(app=app))`
- MUI Chip is already used in the frontend — no new component library needed for the badge

### Integration Points
- `pyproject.toml` `[project.optional-dependencies.dev]` — where pytest/httpx are added
- `frontend/src/features/run-workspace/RunWorkspacePage.tsx` run header section — where the Chip badge is inserted
- `src/a2a_vs_mcp/reasoning.py` — where `FakeReasoningEngine` class is added

</code_context>

<specifics>
## Specific Ideas

- Transport badge as a concise MUI Chip (e.g., `<Chip label="in_process" size="small" />`) in the run header row — same row as scenario/mode selectors
- `FakeReasoningEngine` should return per-scenario canned text plausible enough that if a non-technical viewer sees it in a trace it reads as real AI reasoning

</specifics>

<deferred>
## Deferred Ideas

- Full pytest fixture rewrite of existing unittest classes — deferred; not required for Phase 1 goal, existing tests work under pytest as-is
- Startup port availability health check (mentioned in PITFALLS.md m1) — useful but not required for Phase 1 crash-free goal; can be added in Phase 2 or as a standalone fix

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-demo-stability-foundation*
*Context gathered: 2026-04-22*
