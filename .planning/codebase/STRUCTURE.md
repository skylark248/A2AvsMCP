# Codebase Structure

_Last updated: 2026-04-21_

## Summary

The project separates a Python backend package (`src/a2a_vs_mcp/`) from a React frontend (`frontend/src/`), with both served from a single FastAPI process. Runtime artifacts (traces, reports, logs, SQLite DB) are written to `artifacts/`. Scripts, seed data, and documentation live at the root level.

## Directory Layout

```
A2A vs MCP/
├── main.py                          # CLI entry point
├── serve_ui.py                      # FastAPI server entry point
├── pyproject.toml                   # Python package config and dependencies
├── docker-compose.yml               # Multi-service Docker orchestration
├── Dockerfile                       # Single-container build
├── .env.example                     # Environment variable reference
├── DEMO_PRESETS.json                # Preset run configurations for demo mode
├── REMOTE_A2A_REGISTRY.json         # Remote A2A agent endpoint registry
├── REMOTE_MCP_REGISTRY.json         # Remote MCP server registry
├── src/
│   └── a2a_vs_mcp/                  # Main Python package
│       ├── platform.py              # Central orchestrator (DemoPlatform)
│       ├── web.py                   # FastAPI app, all routes, SPA serving
│       ├── api_schemas.py           # Pydantic request/response contracts
│       ├── cli.py                   # argparse CLI (scenario, mode, profile flags)
│       ├── config.py                # ProfileConfig and named profiles (dev/demo/llm)
│       ├── trace.py                 # TraceRecorder — event logging across all layers
│       ├── schemas.py               # Core domain dataclasses (SupportTicket, AgentCard, etc.)
│       ├── reasoning.py             # Mock and LLM reasoning backends
│       ├── reporting.py             # ReportService — save, load, scorecard, trends, export
│       ├── persistence.py           # PlatformStore — SQLite telemetry and registry state
│       ├── dataset.py               # DemoRepository — SQLite seed DB and scenario loader
│       ├── evidence.py              # Low-level SQLite query helpers for MCP servers
│       ├── identity.py              # User ID normalization and artifact path helpers
│       ├── remote_registry.py       # Remote MCP registry loader
│       ├── agents/
│       │   ├── base.py              # BaseAgent — shared classify, reasoner, task message builder
│       │   ├── single_agent.py      # SingleSupportAgent (baseline + mcp modes)
│       │   ├── triage.py            # TriageAgent — capability routing and result merging
│       │   ├── specialists.py       # A2A-only specialists (no MCP)
│       │   └── hybrid_specialists.py # MCP-equipped specialists (hybrid mode)
│       ├── a2a/
│       │   ├── broker.py            # A2ABroker — local registry, routing, retries, lifecycle
│       │   ├── protocol.py          # A2A 1.0 payload helpers and state constants
│       │   ├── registry.py          # RemoteA2ARegistry — loads REMOTE_A2A_REGISTRY.json
│       │   ├── remote_broker.py     # RemoteA2ABroker — HTTP-based remote agent dispatch
│       │   ├── remote_client.py     # HTTP client for remote A2A endpoints
│       │   ├── remote_server.py     # FastAPI remote specialist server (hosted demo)
│       │   ├── remote_models.py     # Pydantic models for remote A2A wire protocol
│       │   └── sdk_compat.py        # Adapter: educational broker ↔ a2a-sdk binding
│       ├── mcp/
│       │   ├── client.py            # MCPClient — in_process/stdio/http/remote_http transports
│       │   └── protocol.py          # MCP protocol helpers
│       ├── mcp_servers/
│       │   ├── db_server.py         # FastMCP server: customer/order/warranty/payment tools + resources
│       │   └── docs_server.py       # FastMCP server: policy/docs search tools + resources
│       ├── data/seeds/              # JSON seed data loaded into SQLite at startup
│       │   ├── customers.json
│       │   ├── orders.json
│       │   ├── payments.json
│       │   ├── scenarios.json       # Scenario definitions with difficulty and tags
│       │   ├── tickets.json
│       │   └── warranties.json
│       ├── templates/               # Jinja2 templates for legacy /legacy dashboard
│       │   ├── base.html
│       │   ├── index.html
│       │   ├── _control_panel.html
│       │   └── _results.html
│       └── static/
│           └── style.css            # Legacy dashboard CSS
├── frontend/
│   ├── src/
│   │   ├── main.tsx                 # React app entry point (ReactDOM.createRoot)
│   │   ├── app/
│   │   │   ├── routes.tsx           # React Router v6 route definitions
│   │   │   ├── theme.ts             # Material UI theme
│   │   │   └── ui/AppUiProvider.tsx # MUI ThemeProvider + Router wrapper
│   │   ├── components/
│   │   │   ├── charts/MetricBarsCard.tsx      # Bar chart for mode comparison metrics
│   │   │   ├── layout/AppShell.tsx            # Top nav + outlet shell
│   │   │   ├── loading/LoadingSkeletons.tsx   # Skeleton placeholders
│   │   │   └── traces/
│   │   │       ├── TraceExplorer.tsx          # Trace event list with filtering
│   │   │       └── ProtocolEnvelopeDrawer.tsx # Side drawer showing raw A2A/MCP payloads
│   │   ├── features/
│   │   │   ├── run-workspace/RunWorkspacePage.tsx   # Main run UI (scenario, mode, transport, failures)
│   │   │   ├── learn/LearningPage.tsx               # Guided MCP vs A2A learning workspace
│   │   │   ├── traces/TraceWorkspacePage.tsx        # Trace viewer with multi-run comparison
│   │   │   ├── reports/
│   │   │   │   ├── ReportsPage.tsx                  # Saved report list
│   │   │   │   └── ReportDetailPage.tsx             # Single report detail with exports
│   │   │   ├── trends/TrendsPage.tsx                # Aggregated run analytics
│   │   │   ├── presentation/PresentationPage.tsx    # Presentation/slideshow mode
│   │   │   ├── telemetry/TelemetryPage.tsx          # Platform telemetry snapshot
│   │   │   └── compare/ComparePage.tsx              # Side-by-side mode comparison
│   │   ├── lib/
│   │   │   ├── api/client.ts                        # All API calls to FastAPI backend
│   │   │   ├── types/
│   │   │   │   ├── api.generated.ts                 # Auto-generated from FastAPI OpenAPI schema
│   │   │   │   └── api.ts                           # UI-facing type aliases and normalized shapes
│   │   │   ├── trace/utils.ts                       # Trace event filtering and formatting helpers
│   │   │   └── demo/presets.ts                      # Demo preset configurations (from DEMO_PRESETS.json)
│   │   └── test/
│   │       ├── setup.ts                             # Vitest setup (MSW, jest-dom)
│   │       └── renderWithProviders.tsx              # Test utility with full provider tree
│   └── dist/                                        # Built frontend (served by FastAPI)
├── artifacts/
│   ├── platform_state.db            # SQLite: run metadata, telemetry, remote registry state
│   ├── traces/                      # Per-run JSON trace files ({task_id}_{mode}.json)
│   ├── logs/                        # NDJSON external log exports
│   ├── reports/                     # Saved run report JSON files
│   ├── evals/                       # Evaluation outputs
│   ├── evidence/                    # Evidence bundle exports
│   └── users/
│       └── <user_id>/               # Per-user scoped artifact mirror (traces/logs/reports)
├── data/
│   └── docs/                        # Markdown policy/docs files served by docs_server
├── docs/
│   ├── media/                       # SVG diagrams for README
│   └── 01-mcp-vs-a2a.md            # Core MCP vs A2A conceptual guide
├── examples/                        # Curated sample trace and report outputs
├── scripts/
│   └── generate_api_types.py        # OpenAPI → TypeScript type generator
└── tests/                           # Python backend tests
```

## Key File Locations

**Entry Points:**
- `main.py` — CLI runner; adds `src/` to path, calls `a2a_vs_mcp.cli.main()`
- `serve_ui.py` — Imports `app` from `web.py`; run with `uvicorn serve_ui:app`
- `frontend/src/main.tsx` — React entry; mounts `<RouterProvider>` with `router` from `routes.tsx`

**Configuration:**
- `src/a2a_vs_mcp/config.py` — Named profiles (`dev`, `demo`, `llm`) with runtime/transport/persistence defaults
- `.env.example` — Documents all supported environment variables
- `DEMO_PRESETS.json` — Frontend preset run configurations
- `REMOTE_A2A_REGISTRY.json` — Remote A2A agent URLs (loaded by `RemoteA2ARegistry`)
- `REMOTE_MCP_REGISTRY.json` — Remote MCP server URLs (loaded by `RemoteMCPRegistry`)

**Core Logic:**
- `src/a2a_vs_mcp/platform.py` — `DemoPlatform`: the single class that runs everything
- `src/a2a_vs_mcp/web.py` — All FastAPI routes; primary integration point for frontend and CLI
- `src/a2a_vs_mcp/api_schemas.py` — Single source of truth for all API contracts
- `src/a2a_vs_mcp/a2a/broker.py` — Local A2A task lifecycle with retry and trace events
- `src/a2a_vs_mcp/mcp/client.py` — MCP transport abstraction (in-process/stdio/http/remote)

**Testing:**
- `tests/` — Python backend test suite
- `frontend/src/**/*.test.tsx` — Co-located Vitest component tests
- `frontend/src/test/setup.ts` — Global test setup
- `frontend/src/test/renderWithProviders.tsx` — Shared test wrapper

**Generated Files (do not edit manually):**
- `frontend/src/lib/types/api.generated.ts` — Regenerated by `scripts/generate_api_types.py` from live FastAPI OpenAPI output

## Naming Conventions

**Python files:** `snake_case.py` matching the class or module they contain (e.g., `remote_broker.py` → `RemoteA2ABroker`)

**TypeScript files:** `PascalCase.tsx` for React components and pages; `camelCase.ts` for utilities and libraries

**Directories:** `kebab-case` for frontend features (`run-workspace/`, `features/`); `snake_case` for Python subpackages (`mcp_servers/`, `hybrid_specialists.py`)

**Artifacts:** `{task_id}_{mode}.json` for trace files; `{report_name}.json` for saved reports

## Where to Add New Code

**New execution mode:**
- Add `_run_<mode>()` method to `DemoPlatform` in `src/a2a_vs_mcp/platform.py`
- Add mode literal to `DemoMode` in `src/a2a_vs_mcp/api_schemas.py`
- Handle mode in `DemoPlatform.run()` dispatch block

**New agent type:**
- Add class extending `BaseAgent` in `src/a2a_vs_mcp/agents/`
- Register with `A2ABroker` in the relevant `_run_*` method in `platform.py`

**New MCP tool:**
- Add `@mcp.tool()` decorated function in `src/a2a_vs_mcp/mcp_servers/db_server.py` or `docs_server.py`
- Tool will be auto-discovered by `MCPClient` on next run

**New API endpoint:**
- Add route to `src/a2a_vs_mcp/web.py`
- Add Pydantic request/response models to `src/a2a_vs_mcp/api_schemas.py`
- Re-run `scripts/generate_api_types.py` to update `frontend/src/lib/types/api.generated.ts`
- Add fetch call to `frontend/src/lib/api/client.ts`

**New frontend page:**
- Create feature folder under `frontend/src/features/<feature-name>/`
- Add lazy-loaded route in `frontend/src/app/routes.tsx`
- Add nav link in `frontend/src/components/layout/AppShell.tsx`

**New scenario:**
- Add entry to `src/a2a_vs_mcp/data/seeds/scenarios.json`
- Scenarios are loaded by `DemoRepository` and served via `/api/scenarios`

## Special Directories

**`artifacts/`:**
- Purpose: All runtime outputs — SQLite DB, traces, reports, logs, evidence bundles
- Generated: Yes (at runtime)
- Committed: Sample outputs only; `artifacts/platform_state.db` is gitignored

**`frontend/dist/`:**
- Purpose: Vite production build output served by FastAPI
- Generated: Yes (`npm run build` inside `frontend/`)
- Committed: No (gitignored)

**`frontend/node_modules/`:**
- Generated: Yes
- Committed: No

**`src/a2a_vs_mcp/__pycache__/` and `src/a2a_vs_mcp/a2a/__pycache__/`:**
- Generated: Yes (Python bytecode)
- Committed: No

**`.tmp/`:**
- Purpose: Temporary test artifacts and smoke check outputs
- Generated: Yes (by test runs)
- Committed: No

**`examples/`:**
- Purpose: Curated hand-picked sample trace and report outputs for documentation and demos
- Generated: Manually selected
- Committed: Yes

---

_Structure analysis: 2026-04-21_
