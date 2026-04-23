# Project Plan: A2A vs MCP Comparative Demo Platform

## Goal
Build a practical, learning-focused and firm-demo-ready platform that contrasts MCP and A2A using realistic support-ticket workflows.

The project shows:

- where MCP is strongest
- where A2A is strongest
- where they complement each other
- how the same business problem looks under different architectures
- how transport, tracing, reporting, and presentation concerns change across architectures

## Current Progress

Current snapshot as of 2026-04-07: all phases through Phase 6 are functionally complete for the current local/demo and hosted remote A2A demo scope.

### Phase 1
Complete.

### Phase 2
Complete.

Delivered:

- official MCP SDK server definitions using `FastMCP`
- MCP-backed tool execution in runtime
- richer A2A lifecycle with retries and failure events
- resilience toggles for outages and malformed tasks
- OpenAI-backed `llm` runtime with safe fallback
- FastAPI/Jinja demo UI with trace and report views
- advanced multi-step scenarios
- improved multi-step answer synthesis

### Phase 3
Complete for the backend, reporting, transport, and original dashboard scope.

Delivered:

- structured report service for save, load, summary, HTML export, and PDF export
- richer report scorecards with per-mode scoring and presentation recommendations
- trend analytics across saved reports, including filters, active chips, drill-down navigation, and sorting
- API endpoints for reports, report trends, and scenario metadata
- explicit MCP transport selection with `in_process`, `stdio`, and `http`
- transport fallback tracing when live transport is unavailable
- local streamable HTTP MCP server support for stronger transport realism
- expanded seed data, deeper scenarios, difficulty tags, and deterministic seed refresh
- FastAPI/Jinja UI polish for reports, trends, exports, and saved-run exploration
- named config profiles for `dev`, `demo`, and `llm`
- structured external log export for downstream analysis

### Phase 4
Complete for the React frontend and backend-hardening scope.

Delivered:

- React + Material UI frontend under `frontend/`
- React frontend as the primary FastAPI-served UI
- legacy Jinja dashboard retained under `/legacy`
- typed API client wrappers and routed app shell
- generated TypeScript API types from FastAPI OpenAPI
- explicit FastAPI request/response schemas in `api_schemas.py`
- enum validation for API requests
- `/api/health` status endpoint
- path-safe report lookup and clean missing report/scenario errors
- run workspace with shareable URL-driven setup state
- reports library with filters, sorting, and report detail pages
- trends workspace with visual analytics and shareable filters
- dedicated trace workspace with cross-mode comparison
- NDJSON log import and replay
- presentation presets, fullscreen-friendly live demo layout, and keyboard shortcuts
- downloadable chart snapshots and shareable chart anchors
- shared toast system and loading skeletons
- hybrid MCP client pooling for HTTP transport efficiency
- frontend test coverage for URL state, route workflows, and demo interactions
- backend contract and regression tests for API and pooling behavior

Still left:

- nothing required for the current demo scope
- optional follow-on polish only; Phase 5 later implemented the demo hardening, durable state, telemetry, remote MCP registry, and bounded user-scoped artifact work


### Phase 5
Complete for the local/demo platform hardening scope.

Delivered:

- demo readiness, reset, and startup scripts
- scenario and preset validation
- scenario authoring docs and curated demo presets
- repeatable evaluation runner across modes and transports
- evidence bundle export/import and React report-detail evidence downloads
- MCP transport diagnostics and remote MCP readiness checks
- `remote_http` endpoint selection through CLI, API, and UI
- remote MCP registry/discovery through `REMOTE_MCP_REGISTRY.json`, `/api/mcp/registry`, `/api/mcp/registry/sync`, and the React registry picker
- bounded durable SQLite state in `artifacts/platform_state.db`
- optional user-scoped reports, traces, logs, exports, and trends under `artifacts/users/<user>/`
- telemetry persistence, `/api/telemetry`, and the React `/telemetry` page
- platform state inspection through `scripts/inspect_platform_state.py`

Still deferred by design:

- authentication and authorization
- hosted deployment packaging
- CI/CD pipeline
- managed remote MCP credentials or marketplace integration
- full secure multi-tenant isolation


### Phase 6
Complete for demo scope.

Delivered:

- separate `a2a_transport = local | remote` axis while keeping local as the default
- hosted remote A2A specialist server module
- remote A2A registry, client, broker, and Agent Card helpers
- CLI/API/React run workspace controls for remote A2A
- remote hybrid trace promotion for MCP tool activity inside hosted specialists
- remote A2A start/check scripts and `REMOTE_A2A.md`
- regression coverage for a hosted remote A2A run, remote failure request schema, and API schema exposure
- remote A2A failure toggles and trace filtering updates
- Docker Compose orchestration for web plus hosted A2A specialists
- Docker Compose smoke verification for the web app plus hosted A2A specialists
- remote A2A health UI in the run workspace
- curated remote A2A bad-auth trace/report examples
- remote A2A presentation cue card

Deferred future work:

- SDK-native A2A 1.0 adapter replacement after the official 1.0-capable SDK line is stable
- richer UI health-panel polish beyond the run workspace, if a future demo needs it
- production hosting hardening, signed Agent Cards, and stronger auth if the project moves beyond demo scope

## Current Architecture

```text
/
|-- README.md
|-- Plan.md
|-- PHASE2.md
|-- PHASE3.md
|-- PHASE4.md
|-- PHASE5.md
|-- main.py
|-- serve_ui.py
|-- pyproject.toml
|-- docker-compose.yml
|-- REMOTE_A2A.md
|-- REMOTE_A2A_REGISTRY.json
|-- scripts/
|   |-- demo_check.ps1
|   |-- demo_reset.ps1
|   |-- demo_start.ps1
|   |-- eval_demo.py
|   |-- export_evidence_bundle.py
|   |-- import_evidence_bundle.py
|   |-- inspect_platform_state.py
|   |-- transport_diagnostics.py
|   |-- validate_presets.py
|   |-- validate_scenarios.py
|   |-- check_remote_a2a.py
|   |-- start_remote_a2a.ps1
|   `-- generate_api_types.py
|-- frontend/
|   |-- package.json
|   |-- vite.config.ts
|   `-- src/
|       |-- app/
|       |-- components/
|       |-- features/
|       |-- lib/
|       |   `-- types/
|       |       |-- api.generated.ts
|       |       `-- api.ts
|       `-- test/
|-- data/
|   `-- docs/
|-- src/
|   `-- a2a_vs_mcp/
|       |-- api_schemas.py
|       |-- cli.py
|       |-- dataset.py
|       |-- platform.py
|       |-- reasoning.py
|       |-- reporting.py
|       |-- persistence.py
|       |-- identity.py
|       |-- remote_registry.py
|       |-- schemas.py
|       |-- trace.py
|       |-- web.py
|       |-- a2a/
|       |   |-- broker.py
|       |   |-- protocol.py
|       |   |-- remote_broker.py
|       |   |-- remote_client.py
|       |   |-- remote_models.py
|       |   |-- remote_server.py
|       |   |-- registry.py
|       |   `-- sdk_compat.py
|       |-- agents/
|       |   |-- base.py
|       |   |-- single_agent.py
|       |   |-- specialists.py
|       |   |-- hybrid_specialists.py
|       |   `-- triage.py
|       |-- mcp/
|       |   |-- client.py
|       |   `-- protocol.py
|       |-- mcp_servers/
|       |   |-- db_server.py
|       |   `-- docs_server.py
|       |-- static/
|       |   `-- style.css
|       |-- templates/
|       |   |-- base.html
|       |   |-- index.html
|       |   `-- _results.html
|       `-- data/
|           `-- seeds/
|-- tests/
|   |-- test_demo_modes.py
|   `-- test_web_ui.py
`-- artifacts/
    |-- platform_state.db
    |-- support_demo.db
    |-- traces/
    |-- logs/
    |-- reports/
    `-- users/
```

## Current Verification

The current verified baseline is:

```text
py scripts\validate_scenarios.py
py scripts\validate_presets.py
py scripts\inspect_platform_state.py

py -m unittest discover -s tests
Ran 54 tests - OK

npm.cmd test
5 test files passed, 10 tests passed

npm.cmd run build
built successfully

powershell.exe -ExecutionPolicy Bypass -File scripts\demo_check.ps1 -Profile demo -Transport in_process -SkipTransportRun
passed

docker compose up --build -d
py scripts\check_remote_a2a.py
remote A2A specialists passed readiness checks
web API remote A2A run passed
docker compose down
```

## Current Direction

The platform is feature-complete for its intended comparative demo, Phase 5 hardening scope, and Phase 6 hosted remote A2A demo scope.

That means the current direction is:

- keep backend APIs, generated OpenAPI types, and transports stable
- keep the React frontend as the primary UI
- keep the legacy dashboard available under `/legacy` as a fallback/reference UI
- treat SDK-native A2A 1.0 migration and broader hosted SaaS hardening as productization rather than missing core architecture

## Optional Future Work

Phase 5 and Phase 6 are complete for demo scope. See [PHASE5_COMPLETE.md](PHASE5_COMPLETE.md), [PHASE6.md](PHASE6.md), and [docs/05-remote-a2a-presentation.md](docs/05-remote-a2a-presentation.md). Future productization should be tracked separately if SDK-native A2A 1.0 migration, authentication, hosted deployment, managed remote credentials, CI/CD, or full secure multi-tenant isolation become necessary.

## Reference Docs

- [README.md](README.md): current feature overview and quick-start guide
- [PHASE2.md](PHASE2.md): Phase 2 completion summary in current context
- [PHASE3.md](PHASE3.md): Phase 3 completion status in current context
- [PHASE4.md](PHASE4.md): Phase 4 completion status and optional follow-on work
- [PHASE5.md](PHASE5.md): Phase 5 implementation record and retained planning context
- [PHASE5_COMPLETE.md](PHASE5_COMPLETE.md): Phase 5 completion checklist and verification commands
- [PHASE6.md](PHASE6.md): hosted remote A2A implementation record and completion criteria
- [docs/05-remote-a2a-presentation.md](docs/05-remote-a2a-presentation.md): remote A2A presenter cue card













