---
phase: 01-demo-stability-foundation
plan: "01"
subsystem: backend-stability
tags: [dependencies, testing, fake-llm, schema]
dependency_graph:
  requires: []
  provides: [FakeReasoningEngine, mcp_transport-on-RunOutput, pytest-suite, dev-dep-pins]
  affects: [platform.py, schemas.py, reasoning.py, agents/base.py, api_schemas.py]
tech_stack:
  added: [pytest>=8.0, pytest-asyncio>=0.24, httpx>=0.28]
  patterns: [TDD-verify, ASGI-in-process-test, fake-reasoning-stub]
key_files:
  created:
    - tests/conftest.py
    - tests/test_api_async.py
  modified:
    - pyproject.toml
    - src/a2a_vs_mcp/reasoning.py
    - src/a2a_vs_mcp/agents/base.py
    - src/a2a_vs_mcp/schemas.py
    - src/a2a_vs_mcp/platform.py
    - src/a2a_vs_mcp/api_schemas.py
decisions:
  - "Added fake_llm to RuntimeMode Literal in api_schemas.py so API accepts runtime=fake_llm (required for test_api_fake_llm_runtime_returns_canned_answer)"
  - "FakeReasoningEngine subclasses MockReasoner to inherit keyword-based classify() while providing canned summarize() keyed on issue_type"
  - "mcp_transport passed as None for baseline/a2a modes and self.mcp_transport for mcp/hybrid modes in RunOutput construction"
metrics:
  duration: "~15 minutes"
  completed: "2026-04-22T11:38:41Z"
  tasks_completed: 2
  files_changed: 8
---

# Phase 01 Plan 01: Demo Stability Foundation — Backend Stabilisation Summary

**One-liner:** Pinned mcp/a2a-sdk dependencies, added FakeReasoningEngine stub for keyless LLM testing, surfaced mcp_transport on RunOutput, migrated to pytest with asyncio_mode=auto, and added two async ASGI integration tests — all 59 tests pass.

## Tasks Completed

| Task | Name | Commit | Key Files |
|------|------|--------|-----------|
| 1 | Dependency pins, pytest config, FakeReasoningEngine, mcp_transport on RunOutput | 1425eb7 | pyproject.toml, reasoning.py, agents/base.py, schemas.py, platform.py |
| 2 | conftest.py and async integration tests | 5891afc | tests/conftest.py, tests/test_api_async.py, api_schemas.py |

## What Was Built

**Task 1:**
- `pyproject.toml`: Pinned `mcp[cli]>=1.27,<2` (upper bound added), `a2a-sdk[http-server]==0.3.26` (bumped from 0.3.25), added `pytest>=8.0`, `pytest-asyncio>=0.24`, `httpx>=0.28` to dev extras, added `[tool.pytest.ini_options]` with `asyncio_mode = "auto"` and `testpaths = ["tests"]`
- `reasoning.py`: Added `_FAKE_SUMMARIES` dict (4 keys: order_status, billing, troubleshooting, warranty_return) and `FakeReasoningEngine(MockReasoner)` class with canned `summarize()` method
- `agents/base.py`: Updated `build_reasoner()` to return `FakeReasoningEngine()` for `runtime="fake_llm"`
- `schemas.py`: Added `mcp_transport: str | None = None` field to `RunOutput` after `a2a_transport`
- `platform.py`: Updated `RunOutput` construction to pass `mcp_transport=self.mcp_transport if mode in ("mcp", "hybrid") else None`

**Task 2:**
- `tests/conftest.py`: Shared pytest setup — inserts `PROJECT_ROOT/src` onto `sys.path` and sets `A2A_VS_MCP_ARTIFACT_ROOT` to `.tmp/test_artifacts`
- `tests/test_api_async.py`: Two async tests using `httpx.AsyncClient` + `ASGITransport(app=app)` — `test_api_mcp_mode_end_to_end_async` and `test_api_fake_llm_runtime_returns_canned_answer`

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Added fake_llm to RuntimeMode Literal in api_schemas.py**
- **Found during:** Task 2 — `test_api_fake_llm_runtime_returns_canned_answer` returned HTTP 422
- **Issue:** `RuntimeMode = Literal["mock", "llm"]` in `api_schemas.py` rejected `runtime="fake_llm"` before the request reached platform logic
- **Fix:** Changed to `RuntimeMode = Literal["mock", "llm", "fake_llm"]`
- **Files modified:** `src/a2a_vs_mcp/api_schemas.py`
- **Commit:** 5891afc

## Verification Results

```
59 passed in 36.52s
```

- All grep checks pass: mcp[cli]>=1.27,<2, a2a-sdk==0.3.26, class FakeReasoningEngine, fake_llm branch, mcp_transport field
- Both async tests pass without @pytest.mark.asyncio decorators (asyncio_mode=auto handles this)
- No "coroutine was never awaited" or event loop errors
- Existing 57 unittest.TestCase tests continue to pass unchanged

## Known Stubs

None — FakeReasoningEngine returns substantive canned text for all four issue_type values; no placeholder text.

## Threat Flags

None — no new network endpoints, auth paths, or trust boundary changes introduced.

## Self-Check: PASSED

- `d:/A2A vs MCP/tests/conftest.py` — FOUND
- `d:/A2A vs MCP/tests/test_api_async.py` — FOUND
- `d:/A2A vs MCP/src/a2a_vs_mcp/reasoning.py` (FakeReasoningEngine) — FOUND
- `d:/A2A vs MCP/src/a2a_vs_mcp/api_schemas.py` (fake_llm in RuntimeMode) — FOUND
- Commit 1425eb7 — FOUND
- Commit 5891afc — FOUND
