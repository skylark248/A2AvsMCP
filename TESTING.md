# A2A vs MCP Demo Platform — Setup, Run & Test Guide

Everything you need to install, start, and verify the platform.

---

## 1. Prerequisites

- Python 3.10+
- Node.js 18+ / npm
- (Optional) Playwright for OG image generation

---

## 2. Install

```bash
# Python backend
pip install -e ".[dev]"

# For OG image generation (optional)
pip install -e ".[og]"
playwright install chromium

# For remote A2A server (optional)
pip install -e ".[remote-a2a]"

# Frontend
cd frontend && npm install && cd ..
```

---

## 3. Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `A2A_VS_MCP_PROFILE` | `dev` | Runtime profile: `dev`, `demo`, `llm` |
| `ANTHROPIC_API_KEY` | — | Required for `llm` profile + Haiku judge scoring |
| `OPENAI_API_KEY` | — | Required for OpenAI runtime |
| `OPENAI_MODEL` | `gpt-4o-mini` | OpenAI model override |
| `MCP_TRANSPORT` | `in_process` | MCP transport: `in_process`, `http` |
| `A2A_TRANSPORT` | `local` | A2A transport: `local`, `http` |
| `RACE_HARNESS_CONCURRENCY` | `8` | Parallel race lane concurrency |
| `A2A_VS_MCP_ALLOW_EXTERNAL_REMOTE_URLS` | `""` | Allow external remote URLs |
| `REMOTE_MCP_DB_URL` | `""` | Remote MCP DB server URL |
| `REMOTE_MCP_DOCS_URL` | `""` | Remote MCP Docs server URL |
| `REMOTE_A2A_CUSTOMER_URL` | `""` | Remote A2A customer agent URL |
| `REMOTE_A2A_DOCUMENTATION_URL` | `""` | Remote A2A documentation agent URL |
| `REMOTE_A2A_POLICY_URL` | `""` | Remote A2A policy/billing agent URL |
| `REMOTE_A2A_TOKEN` | `""` | Bearer token for remote A2A auth |

### Profiles

| Profile | Runtime | MCP Transport | A2A Transport | Reports Saved |
|---|---|---|---|---|
| `dev` | mock | in_process | local | No |
| `demo` | mock | http | local | Yes |
| `llm` | real LLM | http | local | Yes |

```bash
# Use demo profile
A2A_VS_MCP_PROFILE=demo python serve_ui.py
```

---

## 4. Start the App

### Full app (backend + serves built frontend)

```bash
python serve_ui.py
# Opens on http://localhost:8008
```

### Frontend dev server (hot reload)

```bash
# Terminal 1 — backend
python serve_ui.py

# Terminal 2 — frontend dev
cd frontend && npm run dev
# Opens on http://localhost:5173
```

### CLI entry point

```bash
python main.py --help
```

---

## 5. Backend Tests

### Run all tests

```bash
pytest
# Expected: 345 passing
```

### Run specific test files

```bash
# API and web routes
pytest tests/test_api_async.py
pytest tests/test_web_ui.py

# Demo mode scenarios
pytest tests/test_demo_modes.py

# Race schema + turn system
pytest tests/test_race_schemas.py
pytest tests/test_race_turn.py

# Race WebSocket lifecycle
pytest tests/test_race_ws.py

# Recovery calibration K=3 sweep
pytest tests/test_recovery_calibration.py

# Tool discovery scenario
pytest tests/test_tool_discovery_scenario.py

# Race module tests
pytest tests/race/test_classifier_detector.py
pytest tests/race/test_classifier_regex.py
pytest tests/race/test_failure_mode_classifier.py
pytest tests/race/test_haiku_judge.py
pytest tests/race/test_hardness_coverage.py
pytest tests/race/test_harness.py
pytest tests/race/test_heatmap_aggregator.py
pytest tests/race/test_inject_fault.py
pytest tests/race/test_iron_rule_grep.py
pytest tests/race/test_metrics.py
pytest tests/race/test_mocks_chokepoint.py
pytest tests/race/test_og_cache.py
pytest tests/race/test_og_routes.py
pytest tests/race/test_replay_route.py
pytest tests/race/test_replay_stub.py
pytest tests/race/test_replay_symmetry.py
pytest tests/race/test_run_meta_event.py
pytest tests/race/test_runner_hybrid.py
pytest tests/race/test_runner_pure_a2a.py
pytest tests/race/test_runner_pure_mcp.py
pytest tests/race/test_task_registries.py
pytest tests/race/test_trace_schema.py
pytest tests/race/test_ws_lifecycle.py
pytest tests/race/test_ws_schema.py
```

### Run with verbose output

```bash
pytest -v
```

### Run specific test by name

```bash
pytest -k "test_inject_fault"
pytest -k "recovery"
```

---

## 6. Frontend Tests

```bash
cd frontend

# Run all tests (326 passing)
npm test

# Watch mode
npx vitest

# Type check
npm run typecheck

# Lint
npm run lint
```

---

## 7. Build Frontend (for production)

```bash
cd frontend && npm run build
# Output: frontend/dist/ (served by serve_ui.py automatically)
```

---

## 8. All API Endpoints

Base URL: `http://localhost:8008`

### Health & Info

| Method | Path | Description |
|---|---|---|
| GET | `/api/health` | Health check — returns `{status: "ok"}` |
| GET | `/api/scenarios` | List all 13 demo scenarios |
| GET | `/api/telemetry` | Telemetry snapshot |

### Demo Runs

| Method | Path | Description |
|---|---|---|
| POST | `/api/run` | Trigger a demo run `{scenario, mode: "mcp"|"a2a"|"hybrid"}` |
| GET | `/api/reports` | List all saved reports |
| GET | `/api/reports/trends` | Trends across all reports |
| GET | `/api/reports/{report_name}` | Single report detail |
| GET | `/reports/{report_name}/export` | Export report |
| GET | `/reports/{report_name}/export.pdf` | PDF export |
| GET | `/reports/{report_name}/evidence.zip` | Evidence bundle zip |

### Race

| Method | Path | Description |
|---|---|---|
| GET | `/api/race/heatmap` | Hardness × failure heatmap data |
| GET | `/api/race/runs/{run_id}/trace` | Replay trace events for a run |
| WS | `/api/race/ws?run_id={id}` | WebSocket stream for live race events |

### OG / Sharing

| Method | Path | Description |
|---|---|---|
| GET | `/race/{run_id}/og.png` | 1200×630 OG image (Playwright — needs `[og]` extra) |
| GET | `/race/{run_id}/heatmap.png` | 1200×900 heatmap card image |

### MCP / A2A Registry

| Method | Path | Description |
|---|---|---|
| GET | `/api/mcp/registry` | Remote MCP server registry |
| POST | `/api/mcp/registry/sync` | Sync remote MCP registry |
| GET | `/api/a2a/registry` | Remote A2A agent registry |
| GET | `/api/a2a/health` | Remote A2A health check |

### Pages (HTML)

| Path | Description |
|---|---|
| `/` | Home / run launcher |
| `/race` | Race page — three-lane Pure-MCP vs Pure-A2A vs Hybrid |
| `/race/{run_id}` | Race replay for a specific run |
| `/race/{run_id}?og=1` | OG screenshot mode (chrome hidden) |
| `/traces` | Trace explorer |
| `/reports` | Reports list |
| `/trends` | Trends dashboard |
| `/learn` | Learning page |
| `/presentation` | Presentation mode |
| `/legacy` | Legacy UI |

---

## 9. Demo Scenarios

All scenarios run via POST `/api/run` with `{scenario, mode}` or via the UI at `/`.

| Scenario ID | Ticket | Difficulty | Title |
|---|---|---|---|
| `order_status` | TICKET-1001 | starter | Shipment Status Check |
| `double_charge` | TICKET-1002 | starter | Duplicate Charge Review |
| `setup_error` | TICKET-1003 | starter | Setup Error Triage |
| `warranty_return` | TICKET-1004 | standard | Warranty Return Request |
| `delay_and_billing` | TICKET-1005 | standard | Delay and Billing Escalation |
| `setup_and_warranty` | TICKET-1006 | standard | Setup Failure with Warranty Concern |
| `expired_return_active_warranty` | TICKET-1007 | standard | Expired Return but Active Warranty |
| `enterprise_delay_refund` | TICKET-1008 | advanced | Enterprise Delay and Refund |
| `enterprise_setup_replacement` | TICKET-1009 | advanced | Enterprise Setup and Replacement Review |
| `invoice_and_warranty_followup` | TICKET-1010 | advanced | Invoice and Warranty Follow-up |
| `device_failure_warranty_refund` | TICKET-1011 | advanced | Device Failure: Warranty + Refund |
| `vip_parallel_escalation` | TICKET-1012 | advanced | VIP Parallel Escalation |
| `tool_discovery` | TICKET-1013 | advanced | Discovery: Unknown Product Triage |

### Run a scenario (API)

```bash
curl -X POST http://localhost:8008/api/run \
  -H "Content-Type: application/json" \
  -d '{"scenario": "order_status", "mode": "mcp"}'
```

---

## 10. Race Tasks

Race runs at `/race`. Three lane runners (pure_mcp, pure_a2a, hybrid) compete on these tasks:

| Task | Location |
|---|---|
| `summarize_repo` | `src/a2a_vs_mcp/race/tasks/summarize_repo/` |
| `negotiate_meeting` | `src/a2a_vs_mcp/race/tasks/negotiate_meeting/` |
| `book_travel` | `src/a2a_vs_mcp/race/tasks/book_travel/` |

### Start a race (WebSocket)

Connect: `ws://localhost:8008/api/race/ws?run_id=<id>`

Events streamed: `tick`, `tool_call`, `agent_msg`, `fault_injected`, `fault_observed`, `done`, `error`, `race_done`

---

## 11. Manual UAT Checklist

Start the app (`python serve_ui.py`) before testing. Mark each item `[x]` as you verify it.

### Phase 1-5: Core Demo Features

- [ ] **Transport badge** — Run a demo in MCP or hybrid mode. Transport chip badge (e.g., `in_process`) appears in the run card header.
- [ ] **Trace events** — Inspect any trace: every event has `phase` field (`discovery`/`execution`), tool_call events have sequential `step_index`, parallel task_submit events share a `parallel_batch_id`.
- [ ] **TraceExplorer accordion** — Open trace explorer. Summary Strip is always visible. Protocol Events and Full Trace tabs collapse/expand on click.
- [ ] **Talking-point card** — Run `device_failure_warranty_refund` or `vip_parallel_escalation`. A colored Paper card below the metric chips shows headline, sentence, and callout.
- [ ] **Outcome metric chips** — View any run card. Three chips: elapsed time (protocol-colored), round-trips count, agent count. No old granular chips.
- [ ] **ParallelAgentTimeline** — Run `vip_parallel_escalation`. Horizontal swimlane timeline appears between metrics and talking-point, one bar per agent.
- [ ] **CompareTracesPanel** — Open Compare page with two runs. Mode A/B dropdowns at top. Left and right trace explorers with synced scroll.
- [ ] **Glossary first-mention Popover** — First visit to Run/Compare page: hover a glossary term → Popover with "Got it" button. After clicking "Got it": plain Tooltip on hover.
- [ ] **Role-first phrasing on cards** — Run card header shows expanded phrasing (e.g., "Tool Access Protocol (MCP)") with dotted-underline. "Mock Runtime" chip visible.
- [ ] **Failure summary chips** — Run with failures. Error-colored Chips below talking-point show failure descriptions.

### Phase 6-7: Race Backend

- [ ] **Race WebSocket connects** — Navigate to `/race`. Start a race. No 400/401 errors; events stream live.
- [ ] **failure_mode_classifier headline** — Complete a race. Each lane shows one of: "recovered", "gave up", "kept going without noticing", "kept going to failure", "indeterminate", "lane_failed".

### Phase 8: Race Page UI

- [ ] **RacePage pre-race state** — Navigate to `/race`. "Start Race" button visible. No lane cards yet.
- [ ] **RacePage live race** — Start a race. Three lane cards appear (pure_mcp, pure_a2a, hybrid), updating live. Status strip shows "Running".
- [ ] **RacePage done state** — After race completes: all lanes show final state, characteristic failure banner appears, heatmap renders at bottom.
- [ ] **Mobile fallback** — Resize browser to <480px on `/race/<run_id>`. Three-lane layout replaced with OG PNG img or graceful fallback.

### Phase 9: Heatmap & Replay

- [ ] **GET /api/race/heatmap** — Call `http://localhost:8008/api/race/heatmap`. Response contains `cells` array with `hardness_type`, `lane`, `dominant_tag`, `recovery_rate`, and `baseline` footer.
- [ ] **Race replay loads** — Navigate to `/race/<run_id>` for a known run. Page loads from recorded data (no LLM call). ReplayScrubber appears.
- [ ] **Heatmap cell styling** — View heatmap on `/race`. Each cell shows protocol-color background, icon, recovery fraction (e.g., `12/15`).

### Phase 10: OG Image & Sharing

- [ ] **OG PNG endpoint** — Open `http://localhost:8008/race/<run_id>/og.png` (requires `[og]` install + Playwright). 1200×630 PNG renders. Second request returns cached file.
- [ ] **OG mode hides chrome** — Navigate to `/race/<run_id>?og=1`. Status strip, scrubber, and methodology section are hidden.
- [ ] **Copy headline image button** — On a completed race replay, click "Copy headline image" beside the banner. PNG copied to clipboard or downloaded as `race-<runId>.png`.

### Phase 11: Tool Discovery

- [ ] **DiscoveryPhasePanel** — Run `tool_discovery` scenario. In TraceExplorer, a two-column accordion panel appears ABOVE the trace list. Left: MCP tool catalog. Right: A2A agent cards with skill chips.
- [ ] **Unknown SKU fallback** — Run `tool_discovery`. "NebulaSync Hub" triggers `search_docs` fallback. Affected tool card shows warning border + warning icon.

### Phase 12: Comparison Visualization

- [ ] **SequenceDiagramView** — Open any trace. Toggle to "Sequence" view. SVG with 5 vertical lifelines (User, Orchestrator, LLM, Tool, Remote Agent) and message arrows renders.
- [ ] **List/Sequence toggle** — In TraceExplorer, toggle between "List" and "Sequence" views. Both render without errors.
- [ ] **AnnotatedDiffView** — On Compare page, switch to "Annotated diff" mode. Divergent rows show color tinting (green/pink/orange) with "+"/"-"/"≠" glyphs in gutter.
- [ ] **Side-by-side / Annotated diff toggle** — Toggle between views on Compare page. Both render correctly.

### Phase 13: Design System

- [ ] **DESIGN.md completeness** — Open `.planning/DESIGN.md`. Confirm 5 sections: failureTagColor map (5 entries), methodology-as-flat rule, secondary.main replay-pill, role-first contract, palette intent.

### Cold Start Smoke Test

- [ ] **Cold start** — Kill any running server. Run `python serve_ui.py`. Server starts on port 8008 without errors. Navigate to `http://localhost:8008` — app loads with nav visible. Trigger one demo run (any scenario, any mode).

---

## 12. Key Source Files

| File | Purpose |
|---|---|
| `serve_ui.py` | FastAPI server entry point (port 8008) |
| `main.py` | CLI entry point |
| `src/a2a_vs_mcp/web.py` | All HTTP routes + FastAPI app |
| `src/a2a_vs_mcp/platform.py` | Core demo run orchestration |
| `src/a2a_vs_mcp/config.py` | Profiles + env var config |
| `src/a2a_vs_mcp/trace.py` | TraceRecorder |
| `src/a2a_vs_mcp/race/harness.py` | Race harness (3-lane parallel runner) |
| `src/a2a_vs_mcp/race/ws.py` | WebSocket connection manager |
| `src/a2a_vs_mcp/race/failure.py` | Fault injection (IRON RULE) |
| `src/a2a_vs_mcp/race/classifier.py` | Recovery state machine + Detector(K=3) |
| `src/a2a_vs_mcp/race/heatmap.py` | Hardness×failure heatmap aggregator |
| `src/a2a_vs_mcp/race/replay.py` | Trace replay + schema migrator |
| `src/a2a_vs_mcp/race/og.py` | Playwright OG/heatmap PNG generation |
| `src/a2a_vs_mcp/data/seeds/scenarios.json` | All 13 scenario definitions |
| `frontend/src/app/routes.tsx` | React router config |
| `frontend/src/features/race/` | Race page components |
| `frontend/src/features/compare/` | Compare page + AnnotatedDiffView |
| `frontend/src/features/traces/` | TraceExplorer + SequenceDiagramView |
| `frontend/src/lib/trace/utils.ts` | traceLabel() + role-first helpers |
| `frontend/src/components/traces/diffAlign.ts` | alignTraces pure function (VIZ-01) |
| `.planning/DESIGN.md` | Design system reference (DSGN-01) |

---

## 13. Quick Smoke Test (30 seconds)

```bash
# 1. Start
python serve_ui.py &

# 2. Health check
curl http://localhost:8008/api/health
# Expected: {"status":"ok",...}

# 3. List scenarios
curl http://localhost:8008/api/scenarios | python3 -m json.tool | grep scenario_id

# 4. Backend tests
pytest --tb=short -q
# Expected: 345 passed

# 5. Frontend tests
cd frontend && npm test -- --reporter=verbose 2>&1 | tail -5
# Expected: 326 passed
```
