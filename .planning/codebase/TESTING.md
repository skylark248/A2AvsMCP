# Testing
_Last updated: 2026-04-21_

## Summary
The project has a modest but meaningful test suite split across Python backend tests (pytest) and React frontend tests (Vitest + Testing Library). No CI configuration was found; tests appear to be run manually. Coverage tooling is not configured in pyproject.toml.

## Backend Tests

**Location:** `tests/`

**Framework:** Python `unittest` (compatible with pytest runner)

**Files:**
- `tests/test_demo_modes.py` — core platform logic tests
- `tests/test_web_ui.py` — FastAPI HTTP endpoint tests via `TestClient`

**Runner:** `pytest` (implied; no explicit pytest section in pyproject.toml)

**What is tested:**
- All 4 demo modes (`baseline`, `mcp`, `a2a`, `hybrid`) produce final answers
- Artifact root override via env var
- MCP mode uses tool calls
- A2A broker retry behavior with a `FlakyHandler`
- Web UI index, `/learn`, and `/legacy` pages return 200
- Trace/report API endpoints
- ZIP download of report artifacts

**Mocking approach:**
- `unittest.mock.patch` for env vars and filesystem paths
- `DemoPlatform(runtime="mock")` to avoid LLM calls
- Deterministic mock runtime available project-wide (no OPENAI_API_KEY needed)

## Frontend Tests

**Location:** `frontend/src/**/*.test.tsx`

**Framework:** Vitest + `@testing-library/react` + `@testing-library/user-event`

**Config:** `frontend/vite.config.ts` — `test.environment: "jsdom"`, `globals: true`, `setupFiles: ./src/test/setup.ts`

**Setup utilities:**
- `frontend/src/test/setup.ts` — jest-dom matchers, clipboard and URL.createObjectURL mocks
- `frontend/src/test/renderWithProviders.tsx` — wraps components in `ThemeProvider + AppUiProvider + MemoryRouter`

**Test files found:**
- `src/app/routes.test.tsx`
- `src/components/charts/MetricBarsCard.test.tsx`
- `src/features/presentation/PresentationPage.test.tsx`
- `src/features/reports/ReportsPage.test.tsx`
- `src/features/run-workspace/RunWorkspacePage.test.tsx`

**What is tested:**
- Route rendering
- Chart component rendering
- Key page-level interactions (run demo, load report, presentation mode)
- API client is mocked via `vi.mock("../../lib/api/client")`

## Coverage

No coverage tooling configured (no `pytest-cov`, no `c8`/`istanbul` in frontend). Coverage is unmeasured.

## What is NOT tested

- A2A broker full remote transport (only local/mock mode tested)
- MCP `stdio` and `streamable-http` transport variants
- Trace recorder output format fidelity
- Error boundary / 500 handling in the UI
- `reasoning.py` OpenAI integration (requires real API key; no mock exists)
- Dataset/DemoRepository edge cases

## Running Tests

```bash
# Backend
pytest tests/

# Frontend
cd frontend && npm test
```
