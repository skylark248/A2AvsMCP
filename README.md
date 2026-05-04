# A2A vs MCP Demo Platform

A comparative learning and demo platform for understanding the difference between:

- **MCP** (Model Context Protocol): how an agent connects to tools and structured external capabilities
- **A2A** (Agent-to-Agent protocol): how multiple specialized agents collaborate and delegate work

Designed for deep personal learning, architecture comparison, and a working demo that shows differences, similarities, pros, and cons.

**v2.0 (shipped 2026-05-04)** adds the **Three-Lane Failure-Shape Race Demo** (`/race`) — Pure-MCP vs Pure-A2A vs Hybrid runners executed in parallel against three deterministic tasks, with a K=3 recovery state machine that classifies how each lane handles injected faults (recovered / gave_up / kept_going_without_noticing / kept_going_to_failure / indeterminate / lane_failed) and a hardness×failure heatmap as the closing artifact. v2.0 also adds the `tool_discovery` scenario with a first-class `DiscoveryPhasePanel`, an annotated trace-diff view, an interactive sequence diagram, and a formalized design system at `.planning/DESIGN.md`.

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
# Backend (352 tests — pytest + pytest-asyncio + httpx async ASGI)
pytest

# Frontend (335 tests — vitest)
cd frontend && npm test && npm run build
```

See [TESTING.md](TESTING.md) for the full test guide, manual UAT checklist, and per-phase verification protocol.

## Learning Path

1. Read [docs/01-mcp-vs-a2a.md](docs/01-mcp-vs-a2a.md) for the core mental model.
2. Run the app and open `/learn` for the guided MCP vs A2A lesson.
3. Run the same scenario in `baseline`, `mcp`, `a2a`, and `hybrid` modes.
4. Open `/traces` to inspect tool calls, A2A messages, retries, failures, and fallback events. Toggle the **Sequence** view in `TraceExplorer` to see the same trace as a sequence diagram (5 fixed lifelines: User / Orchestrator / LLM / Tool / Remote Agent) with click-to-pin.
5. Use the Compare page to see protocol differences side-by-side with swimlane timelines and outcome metrics. Switch to **Annotated diff** mode to see line-by-line alignment between two protocol traces with divergence-point highlights (added/removed/differing steps, role-first labels).
6. Run the `tool_discovery` scenario to see the new `DiscoveryPhasePanel` render the MCP tool catalog and A2A agent cards side-by-side above the trace explorer, with stale-capability-cache + unknown-tool-fallback failure modes exercised on both protocols.
7. Open `/race` for the v2.0 flagship: launch a Pure-MCP vs Pure-A2A vs Hybrid race against any of three v1 tasks (`summarize_repo`, `negotiate_meeting`, `book_travel`), watch live WebSocket events stream into three lanes, and read the closing hardness×failure heatmap. Replay any past run via `/race/<run_id>`.

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
- `src/a2a_vs_mcp/race/` -- **v2.0 race demo backend**: 3 lane runners (`pure_mcp.py`, `pure_a2a.py`, `hybrid.py`), `harness.py` parallel driver, `classifier.py` recovery state machine + `Detector(K=3)`, `failure.py` fault injection (IRON RULE), `heatmap.py` aggregator, `replay.py` deterministic replay + schema migrator, `og.py` Playwright OG/heatmap PNG generation, `ws.py` WebSocket connection manager, `tasks/{summarize_repo,negotiate_meeting,book_travel}/` per-task `task_config.yaml` + scorers
- `frontend/src/` -- React + Material UI application with comparison, trace, presentation, **race**, and **discovery** workspaces

### Frontend Components (v1.0)

- **TraceExplorer** -- Three-tier accordion trace view (summary strip, protocol-level, full trace) with runtime-aware latency badges and LLM Alert banners
- **CompareTracesPanel** -- Side-by-side synchronized dual trace explorers for direct mode comparison
- **ParallelAgentTimeline** -- Swimlane timeline showing parallel A2A agent execution from `parallel_batch_id` events
- **Outcome Metrics** -- Elapsed time, round-trip count, and agent count chips on result cards
- **GlossaryTerm** -- Protocol term popovers (25 terms after v2.0; 17 from v1.0 + 8 new race terms) with dotted-underline hover tooltips and route-scoped first-mention Popover
- **TalkingPointCard** -- Presenter-friendly headline + sentence + callout per scenario
- **Role-first Phrasing** -- "Tool Access Protocol (MCP)", "Agent Coordination Protocol (A2A)" on first mention
- **Event Color System** -- `eventColors.ts` as single source of truth for all trace component colors

### Frontend Components (v2.0)

- **RacePage** (`/race`, `/race/:run_id`) -- Three-lane scoreboard rendering the locked information hierarchy (top bar, status strip, three lanes in 1200px central column, characteristic-failure banner, methodology, heatmap). Handles 12 page states (pre-race / countdown / live n=1 / live n=5 / done / replay / sparse-heatmap / ws-disconnected / ws-reconnecting / indeterminate / lane-failed / heatmap-empty)
- **RaceLaneCard / RaceLaneTicker / FailureStateBadge / ReplayPill** -- Lane-level visual primitives (left-edge protocol stripe, pill-shaped failure-state badge, label-above-value ticker)
- **RaceStatusStrip / CharacteristicFailureBanner / MethodologySection** -- Race page chrome (status pill, banner with 4px primary rule + italic dynamic clause, methodology as flat section — no Paper/Card)
- **HardnessFailureHeatmap** -- Closing artifact: rows = `HardnessType`, columns = lane; cells show dominant_tag color + icon + pattern fill + recovery rate (e.g., `12/15`); 5-pill legend strip + footer with model · seed · pinned task IDs
- **HeatmapScaffold / ReplayScrubber** -- Heatmap CSS Grid (role=grid/gridcell + empty-state overlay) + Slider with 200ms aria-live throttle
- **CopyHeadlineImageButton** -- Client-side `html2canvas` snapshot of the 1200×630 anchor region, copied via `ClipboardItem` with download fallback (lazy import; works even if server OG generation has failed)
- **DiscoveryPhasePanel** -- MCP tool catalog + A2A agent cards side-by-side above the trace explorer, with stale-capability-cache highlight and `a2a_remote_discovery` skill-chip join. Mounts on `TraceWorkspacePage` (event-presence gate per D-73) and `CompareTracesPanel` (single panel above dual column per D-72)
- **AnnotatedDiffView** -- Line-by-line diff between two protocol traces using the pure-TS `alignTraces()` algorithm; reachable via Side-by-side|Annotated-diff toggle on `CompareTracesPanel`
- **SequenceDiagramView** -- Hand-rolled SVG sequence diagram with 5 fixed lifelines (User / Orchestrator / LLM / Tool / Remote Agent), click-to-pin messages, prefers-reduced-motion compliance; reachable via List|Sequence toggle in `TraceExplorer`
- **failureTagColor map** (`eventColors.ts`) -- Single source of truth for race color tokens (5 entries) consumed by both heatmap cells and failure-state badges; color paired with icon + label (never sole information channel)
- **FirstMentionProvider** -- React Context tracking which glossary terms have been first-seen on the current route; switches `GlossaryTerm` from Popover ("Got it" dismiss) to plain Tooltip after dismissal

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
| `tool_discovery` | Discovery: Unknown Product Triage (TICKET-1013, CUST-005) | advanced — v2.0 |

The scenario catalog is also available from `/api/scenarios`. The v2.0 `tool_discovery` scenario exercises stale-capability-cache + unknown-tool-fallback failure modes on both MCP and A2A protocols and renders the `DiscoveryPhasePanel` above the trace explorer.

## Race Tasks (v2.0)

The Race demo runs three lane runners (Pure-MCP / Pure-A2A / Hybrid) in parallel against three deterministic tasks. Each task has a `task_config.yaml` with a failure_script + hybrid_plan + hardness_profile and a per-task scorer (Haiku judge / structural / composite).

| Task | Hardness Coverage | Location |
|------|-------------------|----------|
| `summarize_repo` | LONG_CHAIN, SCHEMA_VARIANCE | `src/a2a_vs_mcp/race/tasks/summarize_repo/` |
| `negotiate_meeting` | RATE_PRESSURE, MULTI_SOURCE_SYNTHESIS | `src/a2a_vs_mcp/race/tasks/negotiate_meeting/` |
| `book_travel` | LONG_CHAIN, RATE_PRESSURE, MULTI_SOURCE_SYNTHESIS | `src/a2a_vs_mcp/race/tasks/book_travel/` |

Each of the four v1 hardness types (`LONG_CHAIN`, `RATE_PRESSURE`, `SCHEMA_VARIANCE`, `MULTI_SOURCE_SYNTHESIS`) appears in at least two of the three v1 tasks, verified by `HardnessProfile` inspection.

The harness runs at `n=5` (demo) or `n=1` (dev) with `model=claude-sonnet-4-6, seed=42, temperature=0, per_run_timeout_s=120`. The recovery state machine in `race/classifier.py` tags each fault as one of `recovered | gave_up | kept_going_without_noticing | kept_going_to_failure | indeterminate` using a K=3 turn window and the locked `agent_msg_acknowledging_fault` regex (with negation guard). K=3 is verified by a K∈{2,3,4,5} calibration sweep at `tests/test_recovery_calibration.py`.

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
| `/race` | **v2.0 flagship** — Three-lane Pure-MCP vs Pure-A2A vs Hybrid race page with live WebSocket streaming, 12 page states, and closing heatmap |
| `/race/{run_id}` | Deterministic race replay (reads `data/runs/<run_id>.json`, no LLM call); recovery-rule state machine produces identical per-run tags to original |
| `/race/{run_id}?og=1` | OG-image render mode (chrome hidden) — used by Playwright to produce `og.png` and `heatmap.png` |
| `/race/{run_id}/og.png` | Server-rendered 1200×630 cropped anchor (3 lanes + banner) for social embeds; cached at `data/og/<run_id>-v<OG_LAYOUT_VERSION>.png` |
| `/race/{run_id}/heatmap.png` | Server-rendered 1200×900 heatmap card with `run_id · model · seed · n · task_ids` annotation strip |
| `/learn` | Guided MCP vs A2A learning workspace |
| `/reports` | Saved report library |
| `/reports/{name}` | Report detail with exports, scorecards, traces |
| `/traces` | Trace workspace with NDJSON import/replay (DiscoveryPhasePanel mounts here for `tool_discovery` runs) |
| `/trends` | Saved-report trend analytics |
| `/presentation` | Presentation mode with keyboard shortcuts |
| `/telemetry` | Telemetry overview |
| `/legacy` | Legacy server-rendered Jinja dashboard |

## API Endpoints

### Demo runs

| Endpoint | Description |
|----------|-------------|
| `GET /api/health` | Backend status, version, profile, transport defaults |
| `GET /api/scenarios` | Scenario catalog with difficulty and tags (13 scenarios — includes `tool_discovery`) |
| `POST /api/run` | Run one or more modes, optionally save report |
| `GET /api/reports` | List saved report summaries |
| `GET /api/reports/{name}` | Load saved report payload (compare-mode reports merge multiple protocol runs since v2.0) |
| `GET /api/reports/trends` | Aggregate saved-report trends |
| `GET /api/mcp/registry` | Remote MCP registry entries |
| `GET /api/a2a/registry` | Remote A2A specialist endpoints |
| `GET /api/a2a/health` | Remote A2A specialist health check |
| `GET /api/telemetry` | Run/report/failure/tool telemetry snapshot |
| `GET /openapi.json` | FastAPI OpenAPI schema |

### Race demo (v2.0)

| Endpoint | Description |
|----------|-------------|
| `POST /api/race/run` | Start a race — generates `run_id`, runs `run_race(ws_emitter=MANAGER.publish)` as background task, returns `{run_id}` (Phase 14-01) |
| `GET /api/race/heatmap` | Hardness×failure heatmap aggregator — returns `{cells, baseline}`. Pinned-baseline filter excludes off-model/off-seed/off-task/missing-run_meta runs |
| `GET /api/race/runs/{run_id}/trace` | Replay trace events for a recorded run (no live LLM); used by `/race/{run_id}` deterministic replay |
| `WS /api/race/ws?run_id={id}` | Live race WebSocket stream — events: `tick`, `tool_call`, `agent_msg`, `fault_injected`, `fault_observed`, `done`, `error`, `race_done` (Phase 14-02 wires `run_id` query param correctly) |

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

### v2.0 Milestone — Race Demo + Discovery + Visualization (shipped 2026-05-04)

Eleven-phase milestone (6-16) — 52 plans, 261 commits, +63,371 / -230 LOC across 330 files in 7 days. All 31 v2.0 requirements complete; backend 352/352 pytest, frontend 335/335 vitest.

| Phase | Description | Status |
|-------|-------------|--------|
| 6. TraceRecorder Schema Gate & Race Foundation | 8 WsEvent dataclasses, IRON RULE atomicity, threading.Lock RunWriter, ws lifecycle | Complete (8/8 plans) |
| 7. Race Backend — Lanes, Harness, Recovery | 3 runner lanes + harness + K=3 recovery state machine + 3 v1 tasks + mock APIs | Complete (11/11 plans) |
| 8. Race Page UI & Visual Contract | Three-lane scoreboard, 12 page states, full a11y + responsive contract | Complete (7/7 plans) |
| 9. Heatmap, Replay & K=3 Calibration | Hardness×failure heatmap, deterministic replay, K∈{2,3,4,5} sweep on 3 v1 tasks | Complete (4/4 plans) |
| 10. OG Image & Sharing | Playwright `/race/<id>/og.png` + `/heatmap.png` with `OG_LAYOUT_VERSION` cache + canvas fallback | Complete (5/5 plans) |
| 11. Tool Discovery Scenario | `tool_discovery` scenario + `DiscoveryPhasePanel` mounted on TraceWorkspace + Compare | Complete (4/4 plans) |
| 12. Comparison Visualization Upgrades | `alignTraces` + `AnnotatedDiffView` + hand-rolled SVG `SequenceDiagramView` | Complete (3/3 plans) |
| 13. Design System Lock | `.planning/DESIGN.md` codifying race-demo tokens (DSGN-01) | Complete (1/1 plan) |
| 14. Race Demo Integration Fix (gap closure) | POST `/api/race/run` + WS `run_id` routing + `heatmap_has_data` wiring + `ReplayScrubber.onScrub` seek | Complete (4/4 plans) |
| 15. Verification & Cleanup (gap closure) | Phase 7 VERIFICATION.md + DiscoveryPhasePanel gate harmonization + Phase 12 code cleanup | Complete (4/4 plans) |
| 16. Discovery UAT (gap closure) | Live human UAT for Phase 11 — DISC-01/02 closed, save_report compare-merge fix landed inline | Complete (1/1 plan) |

Full archive: [.planning/milestones/v2.0-ROADMAP.md](.planning/milestones/v2.0-ROADMAP.md). Audit: [.planning/milestones/v2.0-MILESTONE-AUDIT.md](.planning/milestones/v2.0-MILESTONE-AUDIT.md). Retrospective: [.planning/RETROSPECTIVE.md](.planning/RETROSPECTIVE.md).

### v1.0 Milestone — Demo-Day-Ready Platform (completed 2026-04-27)

Five-phase milestone that deepened the platform from a working prototype into a polished, demo-day-ready comparison tool:

| Phase | Description | Status |
|-------|-------------|--------|
| 1. Demo Stability Foundation | All four modes run reliably without an API key; test harness in place | Complete |
| 2. Backend Trace Enrichment | Trace events carry enriched fields (step_index, parallel_batch_id, timing, phase) | Complete |
| 3. New Scenarios | Multi-step and parallel-agent scenarios expose protocol depth visibly | Complete |
| 4. Comparison UI | Side-by-side visualization with swimlane timelines and outcome metrics | Complete |
| 5. Presentation Polish | Glossary popovers, role-first phrasing, runtime indicators, failure visibility | Complete |

Full archive: [.planning/milestones/v1.0-ROADMAP.md](.planning/milestones/v1.0-ROADMAP.md).

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
| [TESTING.md](TESTING.md) | Setup, run, and test guide with manual UAT checklist |
| [TODOS.md](TODOS.md) | Deferred work backlog with promote conditions (v2.1+ candidates) |
| [.planning/DESIGN.md](.planning/DESIGN.md) | Design system reference — race-demo tokens (failureTagColor, methodology-as-flat, secondary.main, role-first, palette intent) — DSGN-01 deliverable |
| [.planning/MILESTONES.md](.planning/MILESTONES.md) | Historical record of shipped milestones |
| [.planning/RETROSPECTIVE.md](.planning/RETROSPECTIVE.md) | Living retrospective with cross-milestone trends |
| [examples/](examples/) | Curated sample report and trace outputs |

## Knowledge Graph

This project includes a [graphify](https://github.com/safishamsi/graphify) knowledge graph (`graphify-out/`) with **1637 nodes, 4439 edges, and 121 communities** extracted via tree-sitter AST parsing (refreshed 2026-05-05 after v2.0 close — up from 663 nodes / 1665 edges / 22 communities at v1.0). Core abstractions: `DemoPlatform`, `AgentResult`, `A2AMessage`, `A2ABroker`, `TraceRecorder`, `FailureConfig`. v2.0 adds: `RaceHarness`, `Detector`, `RecoveryClassifier`, `HardnessProfile`, `RunWriter`, `OGRenderLock`, `DiscoveryPhasePanel`.

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
