# Phase 1: Demo Stability Foundation — Research

**Researched:** 2026-04-22
**Domain:** Python test infrastructure migration, FastAPI async testing, reasoning engine stubbing, MUI badge insertion, dependency pinning
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Transport badge appears in the **run header row** — next to the scenario name / mode selector. Always visible during a run so the presenter can confirm transport at a glance.
- **D-02:** Badge shows the **transport name only** (e.g., `in_process` / `stdio` / `http`). No extra labels; concise chip format.
- **D-03:** Implementation is a small MUI Chip component using the existing `transport` field already present in run result payloads.
- **D-04:** `FakeReasoningEngine` lives in `src/a2a_vs_mcp/reasoning.py` alongside `MockReasoner` and `LLMReasoner` — importable from production code.
- **D-05:** Returns canned realistic responses — plausible customer support reasoning text per scenario type (order status, setup error, etc.). Must look convincing if the real LLM path is shown during demo day.
- **D-06:** Selected by `runtime="fake_llm"` (or similar env signal) so it can be injected in tests without an API key, while `runtime="llm"` still routes to `LLMReasoner`.
- **D-07:** `mcp[cli]>=1.27,<2` — upper bound prevents auto-upgrade into breaking v2 pre-alpha.
- **D-08:** `a2a-sdk[http-server]==0.3.26` — safe patch bump from 0.3.25; do NOT jump to 1.0.0.
- **D-09:** Pins go in `pyproject.toml` only — no lock file changes needed for this phase.
- **D-10:** Add `pytest>=8.0`, `pytest-asyncio>=0.24`, `httpx>=0.28` to `[project.optional-dependencies.dev]`.
- **D-11:** Keep existing test logic; add pytest as the runner. Existing `unittest.TestCase` classes continue to work under pytest — no full rewrite required. New tests write in native pytest style.
- **D-12:** Async FastAPI integration test: use `httpx.AsyncClient` + `ASGITransport` to exercise the full MCP mode request path through the FastAPI app without spawning a real server.
- **D-13:** Add `[tool.pytest.ini_options]` section to `pyproject.toml` with `asyncio_mode = "auto"`.
- **D-14:** "Crash-free" means all 4 modes complete successfully for at least the existing scenarios under `runtime=mock, transport=in_process`.
- **D-15:** Claude's discretion on whether to add a `runtime=mock` guard or startup health check.

### Claude's Discretion

- Badge color / MUI color variant
- Exact `runtime` string name for `FakeReasoningEngine` (e.g., `"fake_llm"`, `"fake"`)
- `conftest.py` structure if needed for shared fixtures
- Whether to add `pytest.ini` or just `pyproject.toml` ini options

### Deferred Ideas (OUT OF SCOPE)

- Full pytest fixture rewrite of existing unittest classes
- Startup port availability health check
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| STAB-01 | All 4 demo modes run without crashes using `runtime=mock, transport=in_process` | Codebase inspection confirms existing `test_all_modes_return_answers` covers this; PITFALLS.md C2/C3 identify risky paths |
| STAB-02 | Run header displays a visible transport mode badge | Frontend code shows `RunResult` has no `mcp_transport` field yet; badge insertion point is the per-mode result card header row (line 859–861 in RunWorkspacePage.tsx) |
| STAB-03 | Dependency pins updated — `mcp>=1.27,<2` and `a2a-sdk==0.3.26` in `pyproject.toml` | pyproject.toml currently has `mcp[cli]>=1.27.0` (needs upper bound) and `a2a-sdk==0.3.25` (needs bump); STACK.md confirms both pins |
| STAB-04 | `FakeReasoningEngine` stub added so reasoning.py LLM path has test coverage without an API key | reasoning.py read fully; `build_reasoner()` in `agents/base.py` is the sole injection point — add `"fake_llm"` branch there |
| STAB-05 | Test suite migrated to pytest + pytest-asyncio + httpx; async FastAPI integration test covers MCP mode end-to-end | Both test files read; `test_web_ui.py` uses `TestClient` (sync); async migration pattern from STACK.md applies directly |
</phase_requirements>

---

## Summary

Phase 1 is a stabilisation pass with five tightly scoped deliverables: crash-free four-mode runs, a transport badge in the UI, dependency pins, a fake reasoning engine, and a pytest migration. No new protocol logic, no new scenarios.

The existing codebase is already in good shape for most of these. The `unittest.TestCase` classes in both test files run under pytest without changes — pytest discovers and runs them natively. The incremental cost is: add three dev dependencies, one `pyproject.toml` ini block, one new async test function, one new class in `reasoning.py`, one frontend chip insert, and two version pin edits. No existing code needs to be deleted or restructured.

The highest-risk item is STAB-02 (transport badge): the `RunResult` API type does not currently include an `mcp_transport` field. The trace already records `requested_transport` and `transport` on the `tool_discovery` event, but this is buried inside the trace array rather than surfaced as a top-level result field. The badge either reads from the trace (fragile) or the backend promotes `mcp_transport` to the `RunResult` payload (clean). The clean path requires a small backend schema change in addition to the frontend chip.

**Primary recommendation:** Add `mcp_transport` to the `RunResult` Pydantic model and the frontend `RunResult` interface, then render `<Chip label={item.mcp_transport} size="small" variant="outlined" />` in the existing per-mode result card header row immediately after the latency chip.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Transport badge display (STAB-02) | Frontend (React) | API/Backend (schema) | Frontend renders the chip; backend must expose the field in RunResult |
| FakeReasoningEngine (STAB-04) | API/Backend (Python) | — | Pure backend class, no frontend touch |
| Dependency pins (STAB-03) | Build/Config | — | `pyproject.toml` only |
| pytest migration (STAB-05) | Test layer | — | Test runner config + new test file; no production code change |
| Crash-free stability (STAB-01) | API/Backend | Test layer | Verified by running existing platform code under mock runtime |

---

## Standard Stack

### Core (already in project)

| Library | Current Version | Purpose | Notes |
|---------|----------------|---------|-------|
| `fastapi` | `>=0.135.3` | ASGI web framework | No change needed |
| `mcp[cli]` | `>=1.27.0` | MCP protocol SDK | **Add `<2` upper bound** |
| `a2a-sdk[http-server]` | `==0.3.25` | A2A protocol SDK | **Bump to `==0.3.26`** |
| `openai` | `>=2.30.0` | LLM client | No change needed |

### New Dev Dependencies (STAB-05)

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `pytest` | `>=8.0` (latest stable 9.0.3) | Test runner | Discovers unittest.TestCase natively; standard Python test runner [VERIFIED: STACK.md, PyPI] |
| `pytest-asyncio` | `>=0.24` (latest stable 1.3.0) | Async test support | Required for `async def` test functions [VERIFIED: STACK.md, PyPI] |
| `httpx` | `>=0.28` (latest stable 0.28.1) | `AsyncClient` + `ASGITransport` | FastAPI official async test pattern [VERIFIED: STACK.md, FastAPI docs] |

### Version verification

Versions confirmed from STACK.md research (2026-04-22):
- `pytest 9.0.3` — latest on PyPI as of research date [VERIFIED: STACK.md]
- `pytest-asyncio 1.3.0` — latest on PyPI [VERIFIED: STACK.md]
- `httpx 0.28.1` — latest on PyPI [VERIFIED: STACK.md]

Note: D-10 specifies `pytest>=8.0` / `pytest-asyncio>=0.24` / `httpx>=0.28` as floor constraints. Use those floor values in `pyproject.toml` (not pinned to exact latest) since these are dev-only tools and minor updates are safe.

**Installation:**
```bash
pip install -e ".[dev]"
```

---

## Architecture Patterns

### System Architecture Diagram

```
test invocation (pytest)
        │
        ├─── unittest.TestCase subclasses ──► DemoPlatform(runtime="mock") ──► 4 modes
        │         (no change required)
        │
        └─── async def test_* ──► httpx.AsyncClient
                                        │
                              ASGITransport(app=app)
                                        │
                              POST /api/run {runtime:"fake_llm"}
                                        │
                              FastAPI handler ──► DemoPlatform
                                                       │
                                              build_reasoner(runtime)
                                                       │
                                        ┌──────────────┼──────────────┐
                                    "mock"         "fake_llm"       "llm"
                                   MockReasoner  FakeReasoningEngine  LLMReasoner
                                                  (canned text,       (OpenAI API,
                                                   no API key)         needs key)
```

### Recommended pyproject.toml structure

```toml
[project]
dependencies = [
  "fastapi>=0.135.3",
  "jinja2>=3.1.6",
  "mcp[cli]>=1.27,<2",         # upper bound added — FastMCP removed in v2
  "openai>=2.30.0",
  "uvicorn>=0.30.0"
]

[project.optional-dependencies]
dev = [
  "ruff>=0.8.0",
  "pytest>=8.0",
  "pytest-asyncio>=0.24",
  "httpx>=0.28",
]
remote-a2a = [
  "a2a-sdk[http-server]==0.3.26",   # bumped from 0.3.25
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### Pattern 1: Existing unittest.TestCase under pytest

**What:** pytest discovers and runs `unittest.TestCase` subclasses without modification.
**When to use:** All existing tests in `test_demo_modes.py` and `test_web_ui.py` — zero changes required.
**Example:**
```python
# Source: existing tests/test_demo_modes.py — runs as-is under pytest
class DemoModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.platform = DemoPlatform(PROJECT_ROOT, runtime="mock")

    def test_all_modes_return_answers(self) -> None:
        ticket = self.platform.get_ticket("order_status", None, None)
        for mode in ("baseline", "mcp", "a2a", "hybrid"):
            result = self.platform.run(mode, ticket)
            self.assertTrue(result.final_answer)
```

### Pattern 2: Async FastAPI integration test

**What:** Drive the full ASGI app in-process with an async HTTP client, no server subprocess.
**When to use:** New `test_api_mcp_mode_async` test for STAB-05.
**Example:**
```python
# Source: FastAPI official docs — https://fastapi.tiangolo.com/advanced/async-tests/
# [VERIFIED: STACK.md, FastAPI docs]
import pytest
from httpx import AsyncClient, ASGITransport
from a2a_vs_mcp.web import app

async def test_api_mcp_mode_end_to_end():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/run",
            json={"scenario": "setup_error", "mode": "mcp", "runtime": "mock"}
        )
    assert response.status_code == 200
    payload = response.json()
    result = next(r for r in payload["results"] if r["mode"] == "mcp")
    assert result["final_answer"]
    assert result["metrics"]["tool_calls"] > 0
```

Note: `asyncio_mode = "auto"` in `[tool.pytest.ini_options]` means `@pytest.mark.asyncio` decorator is not required on individual test functions. [VERIFIED: pytest-asyncio docs, STACK.md]

### Pattern 3: FakeReasoningEngine class

**What:** Drop-in class alongside `MockReasoner` and `LLMReasoner` that returns canned but realistic text.
**When to use:** `runtime="fake_llm"` in tests that exercise the reasoning path without an API key.

**Interface to match** (from `reasoning.py` and `agents/base.py`):
- `classify(query: str) -> TicketIntent` — returns a `TicketIntent` dataclass
- `summarize(ticket: str, evidence: dict[str, Any], issue_type: str | None = None) -> str` — returns a string

`LLMReasoner` subclasses `MockReasoner` and overrides both methods with OpenAI calls, falling back to `super()` on failure. `FakeReasoningEngine` should follow the same inheritance — subclass `MockReasoner`, override `summarize()` only with canned text, and delegate `classify()` to `super()` (the keyword-based classifier is already deterministic and adequate for tests).

**Injection point** — `agents/base.py` line 14–15:
```python
def build_reasoner(runtime: str) -> MockReasoner:
    return LLMReasoner() if runtime == "llm" else MockReasoner()
```
Add the `"fake_llm"` branch here:
```python
def build_reasoner(runtime: str) -> MockReasoner:
    if runtime == "llm":
        return LLMReasoner()
    if runtime == "fake_llm":
        return FakeReasoningEngine()
    return MockReasoner()
```

**Canned text structure** — `summarize()` receives `issue_type` from the classifier. Map issue_type to a per-scenario template:
```python
_CANNED = {
    "order_status": "Your order ORD-{order_id} is currently in transit with an estimated delivery of 2–3 business days. Our logistics team has confirmed the tracking number is active. No action is required on your end.",
    "billing": "I can see a duplicate charge has been flagged on your account for the referenced order. Our billing team has initiated a review and you can expect a resolution within 3–5 business days. We apologise for the inconvenience.",
    "troubleshooting": "Based on the error code you provided, the most common fix is to perform a factory reset by holding the reset button for 10 seconds, then re-pairing the device with the 2.4 GHz band selected. If the issue persists after two attempts, our warranty team can arrange a replacement.",
    "warranty_return": "Your device falls within the standard 12-month warranty coverage and qualifies for a full replacement. Please initiate the return through the support portal and a pre-paid shipping label will be emailed within 24 hours.",
}
```
This text reads as real LLM output to a non-technical viewer, satisfies D-05, and is fully deterministic for test assertions.

### Pattern 4: Transport badge in RunWorkspacePage

**What:** MUI Chip showing the MCP transport name in the per-mode result card header row.
**Current header row** (lines 859–861 in RunWorkspacePage.tsx):
```tsx
<Stack direction="row" justifyContent="space-between" alignItems="center">
  <Typography variant="h6">{item.mode.toUpperCase()}</Typography>
  <Chip label={`${item.metrics.latency_ms} ms`} size="small" />
</Stack>
```
**After badge insertion** (MCP transport chip added; only renders when field is present):
```tsx
<Stack direction="row" justifyContent="space-between" alignItems="center">
  <Typography variant="h6">{item.mode.toUpperCase()}</Typography>
  <Stack direction="row" spacing={0.5} alignItems="center">
    {item.mcp_transport ? (
      <Chip label={item.mcp_transport} size="small" variant="outlined" color="default" />
    ) : null}
    <Chip label={`${item.metrics.latency_ms} ms`} size="small" />
  </Stack>
</Stack>
```

**Backend schema change required:** `RunResult` in `schemas.py` must gain `mcp_transport: str | None = None`. The platform already records `self.mcp_transport` — it just needs to be written into the result object. The frontend `RunResult` interface in `api.ts` must gain `mcp_transport?: string`.

**A2A transport precedent:** The existing `a2a_transport` field (line 84 in api.ts, line 877–879 in RunWorkspacePage.tsx) is the exact pattern to follow. The same conditional chip render `{item.a2a_transport ? <Chip ...> : null}` already exists for A2A — replicate it for `mcp_transport`.

### Anti-Patterns to Avoid

- **Reading transport from trace events:** The `tool_discovery` trace event has `transport` and `requested_transport`, but traversing the trace array to find it in the UI is fragile — it assumes event ordering and event type presence. Promote the field to the top-level `RunResult` instead.
- **Using `TestClient` for the new async test:** FastAPI's `TestClient` is synchronous and wraps async with blocking threads. This can cause event-loop conflicts when the test path exercises real async code (C3 in PITFALLS.md). Use `httpx.AsyncClient` + `ASGITransport` for the new test; the existing `TestClient` tests are fine as-is since they don't create a new loop from inside an existing one.
- **`@pytest.mark.asyncio` on every async test:** With `asyncio_mode = "auto"` set, this decorator is redundant and the pytest-asyncio docs recommend omitting it in auto mode.
- **Subclassing `LLMReasoner` for `FakeReasoningEngine`:** `LLMReasoner.__init__` reads `OPENAI_API_KEY` from env and creates an OpenAI client. Subclassing it would run that constructor. Subclass `MockReasoner` instead.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Async test HTTP client | Custom ASGI test harness | `httpx.AsyncClient` + `ASGITransport` | Handles connection lifecycle, redirects, JSON serialisation; ASGITransport is the FastAPI-blessed pattern [VERIFIED: FastAPI docs] |
| Async test runner | `asyncio.run()` in test setUp | `pytest-asyncio` with `asyncio_mode="auto"` | Handles event loop lifecycle per test; no loop nesting issues |
| Transport chip component | New custom React component | MUI `Chip` (already imported in RunWorkspacePage.tsx line 9) | Already in the import list; zero bundle cost |

**Key insight:** Every tool needed for this phase is either already in the codebase or is a one-line addition to `pyproject.toml`. There is nothing novel to build at the infrastructure level.

---

## Common Pitfalls

### Pitfall 1: `mcp_transport` missing from RunResult API response

**What goes wrong:** The transport badge renders `undefined` or is silently absent because `mcp_transport` is not in the JSON the `/api/run` endpoint returns.
**Why it happens:** `RunResult` Pydantic model in `schemas.py` currently has no `mcp_transport` field (confirmed by grep). The platform sets `self.mcp_transport` but does not copy it into the result object.
**How to avoid:** Add `mcp_transport: str | None = None` to the `RunResult` Pydantic model, populate it in `platform.py` where the `RunResult` is constructed, and add `mcp_transport?: string` to the TypeScript interface.
**Warning signs:** The chip renders blank or the conditional `{item.mcp_transport ? ... : null}` never renders at all.

### Pitfall 2: pytest-asyncio version mismatch with `asyncio_mode`

**What goes wrong:** `asyncio_mode = "auto"` was introduced in pytest-asyncio 0.21. If an older version is installed, the setting is silently ignored and async tests are collected but fail with `coroutine was never awaited`.
**Why it happens:** The floor constraint `>=0.24` in D-10 is safely above 0.21, but if a developer has a cached older install, the new ini option won't take effect.
**How to avoid:** The `>=0.24` floor in `pyproject.toml` prevents this. After `pip install -e ".[dev]"`, verify with `pytest --version` and `pip show pytest-asyncio`. [VERIFIED: pytest-asyncio changelog]
**Warning signs:** `PytestUnraisableExceptionWarning: coroutine 'test_...' was never awaited` in test output.

### Pitfall 3: `FakeReasoningEngine.summarize()` called with no matching issue_type key

**What goes wrong:** `classify()` returns `issue_type = "billing"` but the canned dict key is slightly different, so the `summarize()` override returns an empty string or raises `KeyError`, causing the test to fail on `assert result.final_answer`.
**Why it happens:** `MockReasoner.classify()` returns one of four strings: `"order_status"`, `"billing"`, `"troubleshooting"`, `"warranty_return"`. The canned dict must use exactly these keys.
**How to avoid:** Use `_CANNED.get(issue_type, _CANNED["order_status"])` as the fallback — never a bare dict access. Add a test assertion that `FakeReasoningEngine().summarize("test", {}, issue_type="billing")` returns a non-empty string.
**Warning signs:** `final_answer` is empty in test assertions. `KeyError` traceback referencing `_CANNED`.

### Pitfall 4: Transport badge appears on all four mode cards but only MCP is meaningful

**What goes wrong:** If `mcp_transport` is set on the platform and echoed to all `RunResult` objects (baseline, a2a, hybrid, mcp), the badge appears on all four mode cards — which is confusing since baseline and a2a don't use MCP transport.
**Why it happens:** `DemoPlatform.run()` creates one result per mode; if `mcp_transport` is a platform-level attribute it may be copied to all results indiscriminately.
**How to avoid:** Populate `mcp_transport` in the RunResult only for `mode in ("mcp", "hybrid")` — the two modes that actually use MCP. For baseline and a2a, leave it `None` so the conditional chip does not render.
**Warning signs:** The chip shows `in_process` on the baseline and a2a mode cards.

### Pitfall 5: `anyio.run()` conflict when testing http/stdio transports (PITFALLS.md C3)

**What goes wrong:** `MCPClient.call()` uses `anyio.run()` for stdio and http transports, which creates a new event loop. When called from inside an already-running async test loop (pytest-asyncio), this raises `RuntimeError: This event loop is already running`.
**Why it happens:** The existing `test_mcp_http_transport_can_run_when_requested` test in `test_demo_modes.py` calls `platform.run()` synchronously from a `unittest.TestCase` method — safe because there is no outer loop. But if the same transport path were exercised from an async test function, the nesting would fail.
**How to avoid:** The new async integration test MUST use `runtime="mock"` or `runtime="fake_llm"` with `transport=in_process` (D-14). Do not add async test coverage for http/stdio transports in this phase.
**Warning signs:** `RuntimeError: This event loop is already running` in pytest output.

---

## Code Examples

### FakeReasoningEngine — complete implementation sketch

```python
# Source: derived from existing MockReasoner/LLMReasoner pattern in reasoning.py [VERIFIED: codebase read]
# Add in src/a2a_vs_mcp/reasoning.py after the LLMReasoner class

_FAKE_SUMMARIES: dict[str, str] = {
    "order_status": (
        "Your order is currently in transit and on track for delivery within the estimated window. "
        "The tracking number has been confirmed as active with the carrier. "
        "No further action is required from your end at this time."
    ),
    "billing": (
        "I can see a duplicate charge has been flagged on your account for the referenced order. "
        "Our billing team has initiated a review and you can expect a resolution within 3 to 5 business days. "
        "We apologise for the inconvenience and will notify you by email once the refund is processed."
    ),
    "troubleshooting": (
        "Based on the error code you provided, the recommended fix is a factory reset followed by re-pairing on the 2.4 GHz band. "
        "Hold the reset button for 10 seconds until the indicator light flashes twice, then retry the pairing process. "
        "If the issue persists after two attempts, our warranty team can arrange an expedited replacement."
    ),
    "warranty_return": (
        "Your device falls within the standard 12-month warranty coverage and qualifies for a full replacement unit. "
        "Please initiate the return through the support portal using the order number and a pre-paid shipping label will be emailed within 24 hours. "
        "The replacement will ship once the defective unit is received at our service centre."
    ),
}


class FakeReasoningEngine(MockReasoner):
    """Deterministic reasoning stub for tests that need the LLM path without an API key.

    classify() delegates to MockReasoner (keyword-based, deterministic).
    summarize() returns a canned realistic customer support response keyed on issue_type.
    Selected when runtime="fake_llm" via build_reasoner() in agents/base.py.
    """

    def summarize(self, ticket: str, evidence: dict[str, Any], issue_type: str | None = None) -> str:
        key = issue_type or "order_status"
        return _FAKE_SUMMARIES.get(key, _FAKE_SUMMARIES["order_status"])
```

### build_reasoner() update in agents/base.py

```python
# Source: agents/base.py line 14 — current code [VERIFIED: codebase read]
# Change:
def build_reasoner(runtime: str) -> MockReasoner:
    return LLMReasoner() if runtime == "llm" else MockReasoner()

# To:
def build_reasoner(runtime: str) -> MockReasoner:
    from ..reasoning import FakeReasoningEngine  # avoid circular if needed; or add to top-level import
    if runtime == "llm":
        return LLMReasoner()
    if runtime == "fake_llm":
        return FakeReasoningEngine()
    return MockReasoner()
```

### pyproject.toml — complete diff

```toml
# CHANGE 1: add upper bound to mcp
"mcp[cli]>=1.27,<2",         # was: "mcp[cli]>=1.27.0"

# CHANGE 2: bump a2a-sdk in remote-a2a extras
"a2a-sdk[http-server]==0.3.26",   # was: ==0.3.25

# CHANGE 3: add pytest stack to dev extras
dev = [
  "ruff>=0.8.0",
  "pytest>=8.0",
  "pytest-asyncio>=0.24",
  "httpx>=0.28",
]

# CHANGE 4: add pytest ini section (new section, append to file)
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

### New async test — tests/test_api_async.py

```python
# Source: pattern from STACK.md / FastAPI docs [VERIFIED: STACK.md]
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("A2A_VS_MCP_ARTIFACT_ROOT", str(PROJECT_ROOT / ".tmp" / "test_artifacts"))
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from httpx import ASGITransport, AsyncClient
from a2a_vs_mcp.web import app


async def test_api_mcp_mode_end_to_end_async():
    """Full request path through FastAPI ASGI app — no real server, no thread pool."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/run",
            json={"scenario": "setup_error", "mode": "mcp", "runtime": "mock"},
        )
    assert response.status_code == 200
    payload = response.json()
    mcp_result = next(r for r in payload["results"] if r["mode"] == "mcp")
    assert mcp_result["final_answer"]
    assert mcp_result["metrics"]["tool_calls"] > 0


async def test_api_fake_llm_runtime_returns_canned_answer():
    """FakeReasoningEngine produces a non-empty answer for all modes without an API key."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/run",
            json={"scenario": "order_status", "mode": "all", "runtime": "fake_llm"},
        )
    assert response.status_code == 200
    payload = response.json()
    for result in payload["results"]:
        assert result["final_answer"], f"Empty answer for mode {result['mode']}"
```

---

## Transport Badge — Field Availability Analysis

The `RunResult` type currently has these transport-related fields:

| Field | Backend (schemas.py) | Frontend (api.ts) | Source |
|-------|---------------------|-------------------|--------|
| `a2a_transport` | `str = "local"` (in A2AResult?) | `a2a_transport?: string` line 84 | [VERIFIED: codebase read] |
| `mcp_transport` | **NOT PRESENT** | **NOT PRESENT** | [VERIFIED: codebase grep] |

The `transport` field in trace events (line 46 in api.ts) is per-event, not per-result. The badge design (D-03) references "the existing `transport` field already present in run result payloads" — but the grep confirms this field does not exist at the RunResult level. The planner must include a backend schema task to add it.

**Exact insertion point for the badge** (RunWorkspacePage.tsx line 859–861):
The per-mode result card header `Stack` currently has `<Typography>` (mode name) and `<Chip>` (latency). The badge slots in as a second chip in that row, wrapped in an inner `Stack direction="row"` when `mcp_transport` is present, mirroring the existing `a2a_transport` chip pattern at lines 877–879.

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|------------------|--------|
| `python -m unittest discover` | `pytest` with unittest.TestCase autodiscovery | pytest runs existing tests unchanged; adds fixtures, parametrize, async support |
| `fastapi.testclient.TestClient` for all tests | `TestClient` for sync; `httpx.AsyncClient+ASGITransport` for new async tests | Avoids event-loop nesting pitfall (C3); aligns with FastAPI official recommendation |
| No `asyncio_mode` config | `asyncio_mode = "auto"` in pyproject.toml | Eliminates per-test `@pytest.mark.asyncio` boilerplate |

**Deprecated/outdated:**
- `async_asgi_testclient`: unmaintained, do not use [VERIFIED: STACK.md]
- `@pytest.mark.asyncio` per test: redundant when `asyncio_mode = "auto"` is set [VERIFIED: pytest-asyncio docs via STACK.md]

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `mcp_transport` is not present in `RunResult` Pydantic model or TypeScript interface | Transport badge analysis | If it is present, the backend schema task is unnecessary — only the frontend chip insert is needed |
| A2 | `platform.py` writes a `RunResult` object where `mcp_transport` can be added as a top-level field | Code Examples | If RunResult construction is more complex, the population step needs adjustment |
| A3 | `FakeReasoningEngine` should be a `MockReasoner` subclass (not standalone) | Code Examples | Confirmed by pattern of `LLMReasoner(MockReasoner)` — low risk |

---

## Open Questions

1. **Does `RunResult` already expose `mcp_transport` somewhere I didn't find?**
   - What we know: `grep -n "mcp_transport" schemas.py` returned only one hit: `a2a_transport: str = "local"` (which is an A2A field). `api.ts` grep for `mcp_transport` found it only in request types (`ApiRunRequest`), not response types.
   - What's unclear: There may be a second result schema class that's generated or inherited that was not inspected.
   - Recommendation: The planner should have the implementer grep `schemas.py` fully for any `RunResult` class definition before adding the field, to avoid a duplicate.

2. **Should `conftest.py` be added for shared `PROJECT_ROOT` / `sys.path` setup?**
   - What we know: Both existing test files duplicate the `PROJECT_ROOT / sys.path` setup block (8 lines each).
   - What's unclear: This is Claude's discretion (CONTEXT.md). Refactoring is deferred (CONTEXT.md deferred section).
   - Recommendation: Add a minimal `tests/conftest.py` that runs the `sys.path` setup once, and import from it in the new async test file. Do not refactor existing files (deferred).

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.10+ | All backend | [ASSUMED: yes — project requires `>=3.10`] | — | — |
| Node.js / npm | Frontend chip (TSX edit) | [ASSUMED: yes — frontend already built] | — | — |
| `pytest` | STAB-05 | Not installed (not in current `pyproject.toml` dev deps) | — | Add via `pip install -e ".[dev]"` |
| `pytest-asyncio` | STAB-05 | Not installed | — | Same |
| `httpx` | STAB-05 | Not installed | — | Same |

**Missing dependencies with fallback:**
- `pytest`, `pytest-asyncio`, `httpx`: all installed together via the `pyproject.toml` dev extras change. One install command covers all three.

**Missing dependencies with no fallback:** None.

---

## Sources

### Primary (HIGH confidence)
- Codebase direct read: `src/a2a_vs_mcp/reasoning.py` (full), `src/a2a_vs_mcp/agents/base.py` (grep), `tests/test_demo_modes.py` (full), `tests/test_web_ui.py` (full), `pyproject.toml` (full), `frontend/src/features/run-workspace/RunWorkspacePage.tsx` (full), `frontend/src/lib/types/api.ts` (partial)
- `.planning/research/STACK.md` — pytest/httpx versions and patterns (PyPI-verified as of 2026-04-22)
- `.planning/research/PITFALLS.md` — C2, C3, M3 directly relevant to this phase
- `.planning/phases/01-demo-stability-foundation/01-CONTEXT.md` — locked decisions D-01 through D-15

### Secondary (MEDIUM confidence)
- FastAPI async tests docs (cited in STACK.md): https://fastapi.tiangolo.com/advanced/async-tests/
- pytest-asyncio `asyncio_mode` docs (cited in STACK.md): confirms `auto` mode semantics

### Tertiary (LOW confidence)
- None — all claims for this phase are verifiable from the codebase and STACK.md.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions from PyPI-verified STACK.md; existing test files read directly
- Architecture: HIGH — all integration points confirmed by codebase grep and file reads
- Pitfalls: HIGH — C2/C3 from PITFALLS.md anchored to actual code paths; transport field gap confirmed by grep
- Transport badge field gap: HIGH — confirmed by `grep mcp_transport schemas.py` returning no RunResult hit

**Research date:** 2026-04-22
**Valid until:** 2026-05-22 (stable libraries; MCP v2 alpha timeline remains uncertain but <2 pin handles it)
