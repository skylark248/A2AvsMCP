# A2A vs MCP Demo Platform

A comparative learning and demo platform for understanding the difference between:

- **MCP** (Model Context Protocol): how an agent connects to tools and structured external capabilities
- **A2A** (Agent-to-Agent protocol): how multiple specialized agents collaborate and delegate work

Designed for deep personal learning, architecture comparison, and a working demo that shows differences, similarities, pros, and cons.

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 18+

### Setup

```bash
# Clone and enter the project
cd A2AvsMCP

# Create and activate Python virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Install backend dependencies
pip install -e ".[dev,remote-a2a]"

# Install and build frontend
cd frontend
npm install
npm run build
cd ..

# Start the app
python serve_ui.py
```

Open **http://127.0.0.1:8008** in your browser. Start with http://127.0.0.1:8008/learn for the guided MCP vs A2A lesson.

### Environment

Copy `.env.example` to `.env`. The app runs fully in **mock mode** with no API keys required. To use the OpenAI-backed runtime:

```bash
export OPENAI_API_KEY="your-key"
python main.py --scenario setup_error --mode all --runtime llm
```

### Run Tests

```bash
# Backend (86 tests)
pytest

# Frontend
cd frontend && npm test && npm run build
```

## Learning Path

1. Read [docs/01-mcp-vs-a2a.md](docs/01-mcp-vs-a2a.md) for the core mental model.
2. Run the app and open `/learn` for the guided MCP vs A2A lesson.
3. Run the same scenario in `baseline`, `mcp`, `a2a`, and `hybrid` modes.
4. Open `/traces` to inspect tool calls, A2A messages, retries, failures, and fallback events.
5. Use the Compare page to see protocol differences side-by-side with swimlane timelines and outcome metrics.

Protocol fidelity note: this project uses official MCP SDK components for the MCP path, an educational local A2A-style broker for agent collaboration concepts, and a hosted remote A2A demo binding behind `sdk_compat.py`. SDK-native A2A 1.0 migration is deferred until the official Python SDK line is stable.

## Architecture

### Runtime Modes

| Mode | Description |
|------|-------------|
| `baseline` | One agent handles the ticket directly, no MCP and no A2A |
| `mcp` | One agent handles the ticket using MCP-backed tools |
| `a2a` | Triage broker delegates to specialist agents without MCP tool usage |
| `hybrid` | Triage delegates to specialists that use MCP-backed tools |

### Key Subsystems

- `main.py` -- CLI entry point
- `serve_ui.py` -- FastAPI UI server (port 8008)
- `src/a2a_vs_mcp/platform.py` -- central orchestration for all modes and MCP transport selection
- `src/a2a_vs_mcp/reasoning.py` -- deterministic mock and OpenAI-backed classification/summarization
- `src/a2a_vs_mcp/a2a/broker.py` -- agent registration, routing, retries, parallel dispatch, and lifecycle events
- `src/a2a_vs_mcp/a2a/protocol.py` -- A2A 1.0-shaped Agent Card, message, task status, and artifact payload helpers
- `src/a2a_vs_mcp/mcp_servers/` -- official `FastMCP` database and docs servers
- `src/a2a_vs_mcp/mcp/client.py` -- in-process, stdio, and HTTP MCP invocation wrapper
- `src/a2a_vs_mcp/web.py` -- FastAPI API routes, React app serving, and legacy Jinja routes
- `src/a2a_vs_mcp/api_schemas.py` -- explicit API request/response contracts
- `frontend/src/` -- React + Material UI application with comparison, trace, and presentation workspaces

### Frontend Components (v1.0 Milestone)

- **TraceExplorer** -- Three-tier accordion trace view (summary strip, protocol-level, full trace) with runtime-aware latency badges and LLM Alert banners
- **CompareTracesPanel** -- Side-by-side synchronized dual trace explorers for direct mode comparison
- **ParallelAgentTimeline** -- Swimlane timeline showing parallel A2A agent execution from `parallel_batch_id` events
- **Outcome Metrics** -- Elapsed time, round-trip count, and agent count chips on result cards
- **GlossaryTerm** -- Protocol term popovers (17 terms) with dotted-underline hover tooltips
- **TalkingPointCard** -- Presenter-friendly headline + sentence + callout per scenario
- **Role-first Phrasing** -- "Tool Access Protocol (MCP)", "Agent Coordination Protocol (A2A)" on first mention
- **Event Color System** -- `eventColors.ts` as single source of truth for all trace component colors

## Built-In Scenarios

| Scenario | Title | Difficulty |
|----------|-------|------------|
| `order_status` | Shipment Status Check | starter |
| `double_charge` | Duplicate Charge Review | starter |
| `setup_error` | Setup Error Triage | starter |
| `warranty_return` | Warranty Return Request | standard |
| `delay_and_billing` | Delay and Billing Escalation | standard |
| `setup_and_warranty` | Setup Failure with Warranty Concern | standard |
| `expired_return_active_warranty` | Expired Return but Active Warranty | standard |
| `enterprise_delay_refund` | Enterprise Delay and Refund | advanced |
| `enterprise_setup_replacement` | Enterprise Setup and Replacement Review | advanced |
| `invoice_and_warranty_followup` | Invoice and Warranty Follow-up | advanced |
| `device_failure_warranty_refund` | Device Failure: Warranty + Refund | advanced |
| `vip_parallel_escalation` | VIP Parallel Escalation | advanced |

The scenario catalog is also available from `/api/scenarios`.

## CLI Usage

```bash
# Run all modes for a scenario
python main.py --scenario order_status --mode all

# Run a multi-step scenario
python main.py --scenario enterprise_setup_replacement --mode hybrid

# Run with MCP transport options
python main.py --scenario setup_error --mode mcp --mcp-transport stdio
python main.py --scenario setup_error --mode mcp --mcp-transport http

# Run with failure toggles
python main.py --scenario warranty_return --mode all --db-down --disable-agent policy_or_billing_agent

# Export reports
python main.py --scenario delay_and_billing --mode all --save-report --export-report-html --export-report-pdf
```

## Failure Simulation

CLI flags: `--db-down`, `--docs-timeout`, `--disable-agent <agent_id>`, `--malformed-task`, `--remote-a2a-timeout`, `--remote-a2a-bad-auth`, `--remote-a2a-missing-capability`, `--remote-a2a-malformed-response`, `--remote-a2a-task-failure`

All failure toggles are also available in the React UI run workspace. Failure outcomes appear as red chips in result cards when the v1.0 presentation polish features are active.

## Frontend Development

```bash
# Vite dev server (proxies /api/* to FastAPI backend on :8008)
cd frontend
npm run dev

# Regenerate TypeScript types after backend schema changes
python scripts/generate_api_types.py
```

## UI Routes

| Route | Description |
|-------|-------------|
| `/` | Run workspace -- execute scenarios, compare modes |
| `/learn` | Guided MCP vs A2A learning workspace |
| `/reports` | Saved report library |
| `/reports/{name}` | Report detail with exports, scorecards, traces |
| `/traces` | Trace workspace with NDJSON import/replay |
| `/trends` | Saved-report trend analytics |
| `/presentation` | Presentation mode with keyboard shortcuts |
| `/telemetry` | Telemetry overview |
| `/legacy` | Legacy server-rendered Jinja dashboard |

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Backend status, version, profile, transport defaults |
| `GET /api/scenarios` | Scenario catalog with difficulty and tags |
| `POST /api/run` | Run one or more modes, optionally save report |
| `GET /api/reports` | List saved report summaries |
| `GET /api/reports/{name}` | Load saved report payload |
| `GET /api/reports/trends` | Aggregate saved-report trends |
| `GET /api/mcp/registry` | Remote MCP registry entries |
| `GET /api/a2a/registry` | Remote A2A specialist endpoints |
| `GET /api/a2a/health` | Remote A2A specialist health check |
| `GET /api/telemetry` | Run/report/failure/tool telemetry snapshot |
| `GET /openapi.json` | FastAPI OpenAPI schema |

## Remote Transports

### Remote MCP

```bash
python main.py --scenario setup_error --mode mcp --mcp-transport remote_http \
  --remote-mcp-db-url http://127.0.0.1:9001/mcp \
  --remote-mcp-docs-url http://127.0.0.1:9002/mcp
```

See [REMOTE_MCP.md](REMOTE_MCP.md) for the required tool contract and readiness check.

### Remote A2A

```bash
# Start hosted specialist services
# (see scripts/ for platform-specific start scripts)

# Check remote Agent Cards
python scripts/check_remote_a2a.py

# Run through remote A2A specialists
python main.py --scenario warranty_return --mode a2a --a2a-transport remote
```

See [REMOTE_A2A.md](REMOTE_A2A.md) for full setup and verification.

### Docker Compose

```bash
docker compose up
```

Starts the web app plus all three hosted A2A specialists.

## Project Status

### v1.0 Milestone (completed 2026-04-27)

Five-phase milestone that deepened the platform from a working prototype into a polished, demo-day-ready comparison tool:

| Phase | Description | Status |
|-------|-------------|--------|
| 1. Demo Stability Foundation | All four modes run reliably without an API key; test harness in place | Complete |
| 2. Backend Trace Enrichment | Trace events carry enriched fields (step_index, parallel_batch_id, timing, phase) | Complete |
| 3. New Scenarios | Multi-step and parallel-agent scenarios expose protocol depth visibly | Complete |
| 4. Comparison UI | Side-by-side visualization with swimlane timelines and outcome metrics | Complete |
| 5. Presentation Polish | Glossary popovers, role-first phrasing, runtime indicators, failure visibility | Complete |

### Pre-Milestone Phases (completed 2026-04-07)

| Phase | Description |
|-------|-------------|
| Phase 1-2 | Core MCP/A2A comparison platform with FastMCP, task lifecycle, retries |
| Phase 3 | Reporting layer, transport realism, trend analytics |
| Phase 4 | React + Material UI frontend, API hardening, OpenAPI types |
| Phase 5 | Demo reliability, scenario authoring, evaluation, remote MCP |
| Phase 6 | Hosted remote A2A with Docker Compose orchestration |

See [Plan.md](Plan.md) for the original project architecture and phase details. Per-phase completion records: [PHASE2.md](PHASE2.md), [PHASE3.md](PHASE3.md), [PHASE4.md](PHASE4.md), [PHASE5.md](PHASE5.md), [PHASE6.md](PHASE6.md).

## Documentation

| Document | Description |
|----------|-------------|
| [docs/01-mcp-vs-a2a.md](docs/01-mcp-vs-a2a.md) | Conceptual MCP vs A2A mental model |
| [docs/02-architecture.md](docs/02-architecture.md) | Codebase and runtime architecture walkthrough |
| [docs/03-demo-script.md](docs/03-demo-script.md) | Five-minute and fifteen-minute demo scripts |
| [docs/04-public-github.md](docs/04-public-github.md) | Public clone-and-run readiness checklist |
| [docs/05-remote-a2a-presentation.md](docs/05-remote-a2a-presentation.md) | Remote A2A presenter cue card |
| [docs/06-demo-runbook.md](docs/06-demo-runbook.md) | Operator checklist, smoke checks, reset flow |
| [SCENARIO_AUTHORING.md](SCENARIO_AUTHORING.md) | Scenario JSON fixture authoring guide |
| [REMOTE_MCP.md](REMOTE_MCP.md) | Remote MCP transport setup |
| [REMOTE_A2A.md](REMOTE_A2A.md) | Remote A2A specialist setup and verification |
| [examples/](examples/) | Curated sample report and trace outputs |

## Knowledge Graph

This project includes a [graphify](https://github.com/safishamsi/graphify) knowledge graph (`graphify-out/`) with 663 nodes, 1665 edges, and 22 communities extracted via tree-sitter AST parsing. Core abstractions identified: `DemoPlatform`, `AgentResult`, `A2AMessage`, `A2ABroker`, `TraceRecorder`, `FailureConfig`.

```bash
# Query the graph
graphify query "how does the broker route messages"
graphify path "DemoPlatform" "A2ABroker"
graphify explain "MCPClient"

# Rebuild after code changes (AST-only, no API cost)
graphify update .
```

See [graphify-out/GRAPH_REPORT.md](graphify-out/GRAPH_REPORT.md) for the full community structure and god nodes.

## License

See [LICENSE](LICENSE).
