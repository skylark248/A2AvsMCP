# Architecture

_Last updated: 2026-04-21_

## Summary

A2A vs MCP is a full-stack comparative demo platform built to illustrate the difference between the MCP (Model Context Protocol) and A2A (Agent-to-Agent) protocols in a realistic customer support scenario. The backend is a Python FastAPI application that runs the same support ticket through four distinct execution modes and emits structured trace events at every protocol boundary. A React + Material UI frontend consumes a REST/JSON API to drive run execution, trace inspection, report management, trend analytics, and educational guided learning.

## Pattern Overview

**Overall:** Mode-dispatched orchestration platform with full protocol instrumentation

**Key Characteristics:**
- A single `DemoPlatform` class (`src/a2a_vs_mcp/platform.py`) is the central orchestrator — it selects the right execution path based on `mode` and `transport` settings and owns the full run lifecycle
- All four modes emit structured `TraceRecorder` events throughout execution, enabling side-by-side comparison of MCP tool calls vs A2A task messages
- The MCP path uses the official `mcp[cli]` SDK (`FastMCP`, `ClientSession`) for real protocol fidelity; the A2A path uses an educational local broker that emits A2A 1.0-shaped payloads
- FastAPI serves both the React SPA and JSON API from a single process (`serve_ui.py` → `src/a2a_vs_mcp/web.py`)
- All API shapes are defined as explicit Pydantic models in `src/a2a_vs_mcp/api_schemas.py` and exported to TypeScript via `scripts/generate_api_types.py`

## Runtime Modes

The four modes are dispatched in `DemoPlatform.run()`:

| Mode | Description | Protocol path |
|------|-------------|---------------|
| `baseline` | Single agent, no tools, no delegation | Direct reasoning only |
| `mcp` | Single agent calls MCP-backed tools | `MCPClient` → `db_server` / `docs_server` |
| `a2a` | Triage delegates to specialist agents, no MCP | `A2ABroker` or `RemoteA2ABroker` |
| `hybrid` | Triage delegates to MCP-equipped specialists | `A2ABroker` + `MCPClient` per specialist |

All four modes can be run in sequence in a single API call using `mode: "all"`.

## Layers

**Entry Points:**
- Purpose: CLI and HTTP server bootstrapping
- Location: `main.py` (CLI), `serve_ui.py` (FastAPI server)
- `main.py` injects `src/` into `sys.path` and delegates to `src/a2a_vs_mcp/cli.py`
- `serve_ui.py` imports and exposes the `app` FastAPI instance from `src/a2a_vs_mcp/web.py`

**Web / API Layer:**
- Purpose: HTTP routing, request validation, response serialization, React SPA serving
- Location: `src/a2a_vs_mcp/web.py`
- Contains: FastAPI route handlers, legacy Jinja2 routes under `/legacy`, static file mounting, report export (HTML, PDF, ZIP evidence bundles)
- Depends on: `DemoPlatform`, `ReportService`, `PlatformStore`, `api_schemas.py`
- Key instantiation: `app = FastAPI(...)` mounts `/static`, `/assets`, and the React SPA's `index.html` as a catch-all

**Platform / Orchestration Layer:**
- Purpose: Mode dispatch, transport selection, artifact output
- Location: `src/a2a_vs_mcp/platform.py`
- Contains: `DemoPlatform` class with `_run_baseline`, `_run_mcp`, `_run_a2a`, `_run_hybrid` methods
- Depends on: all agent classes, `MCPClient`, `A2ABroker`, `RemoteA2ABroker`, `TraceRecorder`, `DemoRepository`
- Used by: `web.py` (via API), `cli.py` (via CLI)

**Agent Layer:**
- Purpose: Domain reasoning and protocol interaction for each mode
- Location: `src/a2a_vs_mcp/agents/`
- `base.py` — `BaseAgent` with shared `classify()`, `reasoner`, and task message helpers
- `single_agent.py` — `SingleSupportAgent` used by baseline and mcp modes
- `triage.py` — `TriageAgent` that routes to specialists and merges results
- `specialists.py` — `CustomerDataAgent`, `DocumentationAgent`, `PolicyBillingAgent` (A2A mode, no MCP)
- `hybrid_specialists.py` — `MCPDataAgent`, `MCPDocumentationAgent`, `MCPPolicyBillingAgent` (hybrid mode, uses MCP)

**MCP Subsystem:**
- Purpose: Official SDK-based tool invocation with three transport options
- Location: `src/a2a_vs_mcp/mcp/`
- `client.py` — `MCPClient` wraps `FastMCP`, `stdio_client`, and `streamable_http_client`; supports `in_process`, `stdio`, `http`, and `remote_http` transports; falls back safely to `in_process` on unavailability
- `protocol.py` — MCP protocol helpers
- MCP servers: `src/a2a_vs_mcp/mcp_servers/db_server.py` (customer/order/warranty data tools + resources + prompts), `src/a2a_vs_mcp/mcp_servers/docs_server.py` (policy/docs search tools)

**A2A Subsystem:**
- Purpose: Educational agent-to-agent task routing with A2A 1.0-shaped trace payloads
- Location: `src/a2a_vs_mcp/a2a/`
- `broker.py` — `A2ABroker`: in-process agent registry, capability routing, task dispatch with retries, A2A lifecycle state machine (`submitted → working → completed/failed`)
- `protocol.py` — A2A payload helpers: `agent_card_payload`, `message_payload`, `task_snapshot`, `status_update_event`, `artifact_update_event`; constants for `A2A_PROTOCOL_VERSION = "1.0"` and `A2A_TRANSPORT = "JSONRPC"`
- `registry.py` — `RemoteA2ARegistry`: loads remote agent URLs from `REMOTE_A2A_REGISTRY.json`
- `remote_broker.py` — `RemoteA2ABroker`: HTTP-based broker for `a2a_transport=remote`; discovers agents via `/agent-card`, sends tasks via `RemoteA2AClient`
- `remote_client.py` — HTTP client for remote A2A endpoints
- `remote_server.py` — FastAPI-based remote specialist server (hosted demo)
- `sdk_compat.py` — Adapter binding between the educational broker and the `a2a-sdk` package

**Persistence Layer:**
- Purpose: Durable multi-user run metadata, telemetry, and remote registry state
- Location: `src/a2a_vs_mcp/persistence.py`
- `PlatformStore`: SQLite at `artifacts/platform_state.db`; tables for `report_runs`, telemetry events, and remote MCP registry state

**Reporting Layer:**
- Purpose: Report save/load, scorecards, trend analysis, export
- Location: `src/a2a_vs_mcp/reporting.py`
- `ReportService`: saves run outputs as JSON, computes mode scorecards, generates trend analytics, supports HTML and PDF export

**Trace System:**
- Purpose: Fine-grained, timestamped event recording for every protocol boundary
- Location: `src/a2a_vs_mcp/trace.py`
- `TraceRecorder`: append-only list of dicts; saved as `{task_id}_{mode}.json` in `artifacts/traces/`; exportable as NDJSON for external analysis
- Event types include: `ticket_received`, `tool_discovery`, `mcp_capability_discovery`, `tool_call`, `tool_error`, `tool_transport_fallback`, `a2a_message` (with `message_type`: `agent_register`, `capability_advertise`, `task_submit`, `task_status`, etc.), `agent_reasoning`, `triage_merge`, `comparison_report`

**Configuration:**
- Location: `src/a2a_vs_mcp/config.py`
- Three named profiles: `dev` (mock runtime, in_process transport, no persistence), `demo` (mock runtime, http transport, saves reports), `llm` (OpenAI runtime, http transport, saves reports)
- Profile resolved from `A2A_VS_MCP_PROFILE` env var; individual fields overridable at runtime

**Frontend:**
- Purpose: React SPA for all user-facing demo and learning workflows
- Location: `frontend/src/`
- Built with Vite; served from `frontend/dist/` by FastAPI at `/assets`
- Communicates with backend exclusively via `frontend/src/lib/api/client.ts`
- TypeScript API types generated from FastAPI OpenAPI schema at `frontend/src/lib/types/api.generated.ts`

## Data Flow

**Standard run (MCP mode):**

1. UI posts `POST /api/run` with `ApiRunRequest` (scenario, mode, profile, failure flags, transport)
2. `web.py` constructs `DemoPlatform` and calls `platform.run(mode, ticket, failure_config)`
3. `DemoPlatform._run_mcp()` creates `MCPClient` instances for `db_server` and `docs_server`
4. `MCPClient` discovers tools, resources, and prompts; records `tool_discovery` and `mcp_capability_discovery` trace events
5. `SingleSupportAgent` classifies the ticket intent; MCP tools are invoked per intent flags
6. Each `client.call()` records a `tool_call` trace event; failures record `tool_error`
7. `reasoner.summarize()` generates the final answer
8. `TraceRecorder.save()` writes JSON to `artifacts/traces/`; `ReportService` persists the run
9. `RunOutput` → `RunResponse` (Pydantic) → JSON response

**Standard run (A2A mode):**

1. Same API entry as above; `DemoPlatform._run_a2a()` is dispatched
2. `A2ABroker` is created; three specialist agents are registered — each registration emits `agent_register` and `capability_advertise` A2A trace events
3. `TriageAgent.resolve_with_broker()` classifies ticket, then calls `broker.send_task()` for each needed capability
4. Broker resolves the target agent, emits `task_submit` → `task_queued` → `task_working` → `task_completed` A2A trace events with full A2A 1.0-shaped payloads
5. Specialist agent executes; result returned as `AgentResult`
6. Triage merges results and generates final answer via `reasoner.summarize()`
7. Same trace save and report persistence path as MCP mode

**Remote A2A flow:**

1. `a2a_transport=remote` causes `DemoPlatform` to create `RemoteA2ABroker` instead of `A2ABroker`
2. `RemoteA2ABroker.discover()` fetches `/agent-card` from each registered remote endpoint
3. Tasks are sent via `RemoteA2AClient` over HTTP; failure simulation flags (bad auth, timeout, malformed response) are injected before dispatch

## Error Handling

**Strategy:** Failures are simulated for educational purposes and always surface in the trace

**Patterns:**
- `MCPClient._simulate_failure()` raises `RuntimeError` (db down) or `TimeoutError` (docs timeout) before tool invocation
- `DemoPlatform._safe_tool_call()` catches all MCP tool exceptions, records `tool_error` event, and returns a safe default
- `MCPClient.__init__` catches transport startup failure and falls back to `in_process`, recording `tool_transport_fallback`
- `A2ABroker.send_task()` retries up to `max_retries` with `ThreadPoolExecutor` timeout; records `task_failed` and re-raises on exhaustion
- `TriageAgent._request_specialist()` catches all broker exceptions and records `triage_warning`, allowing partial results
- `RemoteA2ABroker` injects failure modes (bad auth, missing capability, malformed response, task failure) per `FailureConfig`
- All HTTP 404/400 errors in `web.py` are raised as `HTTPException` with descriptive detail strings

## Cross-Cutting Concerns

**Trace Recording:** Every protocol event is recorded via `TraceRecorder.record()` — this is the primary observability mechanism and is threaded through every layer via `AgentContext`

**User Isolation:** `src/a2a_vs_mcp/identity.py` normalizes user IDs; all artifacts are scoped under `artifacts/users/<user_id>/` when a user is provided, falling back to the shared `artifacts/` root

**URL Security:** `web.py` validates all remote URLs against an allowlist of local/private hosts; external URLs require `A2A_VS_MCP_ALLOW_EXTERNAL_REMOTE_URLS=true`

**Reasoning:** `src/a2a_vs_mcp/reasoning.py` provides `mock` (deterministic, no external calls) and `llm` (OpenAI-backed) runtime implementations behind a shared interface used by all agents

---

_Architecture analysis: 2026-04-21_
