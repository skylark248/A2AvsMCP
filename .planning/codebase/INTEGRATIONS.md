# External Integrations
_Last updated: 2026-04-21_

## Summary

The platform integrates two AI-protocol SDKs (MCP and A2A) and one external LLM API (OpenAI). All other data storage is local: a SQLite file for telemetry and JSON files for seed data and reports. There are no third-party auth providers, cloud storage services, or external databases.

---

## Protocol Integrations

### Model Context Protocol (MCP)

- **SDK:** `mcp[cli]>=1.27.0` (Anthropic MCP Python SDK)
- **Client:** `src/a2a_vs_mcp/mcp/client.py` — `MCPClient` class
- **Servers:** `src/a2a_vs_mcp/mcp_servers/db_server.py`, `src/a2a_vs_mcp/mcp_servers/docs_server.py`
- **Transport modes** (selectable per run or profile):
  - `in_process` — server runs in the same Python process (default `dev` profile)
  - `stdio` — server launched as a subprocess via `StdioServerParameters`
  - `http` — server launched as a local HTTP subprocess via `streamable_http_client`; URL auto-assigned
  - `remote_http` — points `streamable_http_client` at an externally hosted MCP server URL
- **Session API used:** `mcp.ClientSession`, `mcp.client.stdio.stdio_client`, `mcp.client.streamable_http.streamable_http_client`
- **Registry:** `REMOTE_MCP_REGISTRY.json` at project root — pre-configured remote MCP server entries; loaded/synced by `src/a2a_vs_mcp/remote_registry.py` and exposed via `/api/mcp/registry`

### Agent-to-Agent Protocol (A2A)

- **SDK (optional):** `a2a-sdk[http-server]==0.3.25` — installed via `pip install -e ".[remote-a2a]"`; spec version 0.3
- **Compatibility shim:** `src/a2a_vs_mcp/a2a/sdk_compat.py` — all remote A2A calls route through `sdk_compat` regardless of whether the official SDK is installed; exposes `remote_binding_metadata()`
- **Local broker:** `src/a2a_vs_mcp/a2a/broker.py` — `A2ABroker` dispatches tasks in-process between registered specialist agents
- **Remote broker:** `src/a2a_vs_mcp/a2a/remote_broker.py` — routes tasks over HTTP to standalone agent services
- **Remote client:** `src/a2a_vs_mcp/a2a/remote_client.py` — `RemoteA2AClient` with configurable timeout; used for health checks and task dispatch
- **Remote server:** `src/a2a_vs_mcp/a2a/remote_server.py` — FastAPI app per specialist role (`customer_data`, `documentation`, `policy_billing`); exposes:
  - `GET /health`
  - `GET /.well-known/agent-card.json`
  - `POST /a2a/tasks`
- **Transport modes:**
  - `local` — in-process broker (default)
  - `remote` — HTTP calls to standalone specialist containers (Docker Compose services on ports 9101/9102/9103)
- **Auth:** optional Bearer token (`Authorization` header); set via `remote_a2a_auth_token` in run requests or `AUTH_TOKEN` env var on agent servers
- **Registry:** `REMOTE_A2A_REGISTRY.json` at project root; loaded by `src/a2a_vs_mcp/a2a/registry.py`; exposed via `/api/a2a/registry` and health-checked via `/api/a2a/health`
- **Wire format:** custom JSON-RPC-like binding (`a2a-vs-mcp-demo-jsonrpc`, binding version `1`); A2A protocol version `1.0`

---

## LLM / AI

### OpenAI API

- **SDK:** `openai>=2.30.0`
- **Usage:** `src/a2a_vs_mcp/reasoning.py` — `LLMReasoner` class; loaded lazily only when `OPENAI_API_KEY` is set
- **Calls:** `client.responses.create()` for ticket classification (returns structured JSON) and answer summarization
- **Default model:** `gpt-4o-mini` (overridable via `OPENAI_MODEL` env var)
- **Fallback:** when `OPENAI_API_KEY` is absent, `MockReasoner` handles all classification and summarization without any API calls — the entire platform runs offline in `mock` runtime

---

## Data Storage

### SQLite (telemetry & run events)

- **Library:** Python stdlib `sqlite3`
- **Implementation:** `src/a2a_vs_mcp/persistence.py` — `PlatformStore`
- **Location:** `artifacts/platform_state.db` (inside mounted Docker volume `./artifacts`)
- **Stores:** run events, report metadata, per-user telemetry snapshots
- **No ORM** — raw SQL via `sqlite3.connect`

### JSON file storage (reports & seed data)

- **Reports:** saved to `artifacts/` as JSON files; managed by `src/a2a_vs_mcp/reporting.py` — `ReportService`
- **Seed data:** `src/a2a_vs_mcp/data/seeds/` — `customers.json`, `orders.json`, `payments.json`, `tickets.json`, `scenarios.json`, `warranties.json`
- **Demo presets:** `DEMO_PRESETS.json` at project root
- **Artifact traces:** `artifacts/traces/` — JSON trace files per run

### No external database

There is no PostgreSQL, MySQL, Redis, or cloud database. All persistence is local files.

---

## API Surface (self-hosted)

The platform exposes its own REST API at port 8008, consumed by the React frontend:

| Endpoint | Purpose |
|----------|---------|
| `POST /api/run` | Execute a demo run (one or all modes) |
| `GET /api/scenarios` | List available scenarios |
| `GET /api/reports` | List saved reports |
| `GET /api/reports/{name}` | Report detail |
| `GET /api/reports/trends` | Aggregated trend view |
| `GET /api/health` | Platform health + version |
| `GET /api/telemetry` | Usage telemetry snapshot |
| `GET /api/mcp/registry` | Remote MCP server registry |
| `POST /api/mcp/registry/sync` | Reload MCP registry from file |
| `GET /api/a2a/registry` | Remote A2A agent registry |
| `GET /api/a2a/health` | Health-check remote A2A agents |

Legacy server-rendered routes exist under `/legacy/*` (Jinja2 templates).

---

## Export / Output Integrations

- **HTML export:** `GET /reports/{name}/export` — full standalone HTML report
- **PDF export:** `GET /reports/{name}/export.pdf` — PDF bytes generated server-side by `ReportService.export_pdf_bytes()`
- **Evidence bundle:** `GET /reports/{name}/evidence.zip` — ZIP archive containing report JSON, traces, scenario, summary manifest

---

## Authentication & Security

- **No external auth provider** — the platform has no user login system
- **User isolation:** lightweight `X-Demo-User` request header or `user_id` query param; normalized by `src/a2a_vs_mcp/identity.py`; used for per-user artifact directories and telemetry
- **Remote URL validation:** `web.py:validate_remote_url()` — blocks non-local hostnames unless `A2A_VS_MCP_ALLOW_EXTERNAL_REMOTE_URLS=true`
- **Remote A2A bearer token:** optional; checked in `src/a2a_vs_mcp/a2a/remote_server.py:require_auth()`

---

## CI/CD & Deployment

- **Containerization:** `Dockerfile` (multi-stage) + `docker-compose.yml`
- **Docker Compose services:** `web` (port 8008) + three A2A specialist agents (`a2a-customer-agent:9101`, `a2a-documentation-agent:9102`, `a2a-policy-agent:9103`)
- **Health checks:** each specialist container polls its own `/health` endpoint
- **No CI pipeline detected** (no `.github/workflows/`, no CircleCI/GitLab CI config found)

---

## Environment Variables Reference

| Variable | Required | Default | Purpose |
|----------|----------|---------|---------|
| `OPENAI_API_KEY` | For `llm` runtime | — | Enables `LLMReasoner`; omit for fully offline mock mode |
| `OPENAI_MODEL` | No | `gpt-4o-mini` | OpenAI model to use |
| `A2A_VS_MCP_PROFILE` | No | `dev` | Active profile (`dev`, `demo`, `llm`) |
| `A2A_TRANSPORT` | No | `local` | Override A2A transport |
| `MCP_TRANSPORT` | No | `in_process` | Override MCP transport |
| `REMOTE_A2A_CUSTOMER_URL` | Remote A2A mode | — | URL of customer data specialist |
| `REMOTE_A2A_DOCUMENTATION_URL` | Remote A2A mode | — | URL of documentation specialist |
| `REMOTE_A2A_POLICY_URL` | Remote A2A mode | — | URL of policy/billing specialist |
| `A2A_VS_MCP_ALLOW_EXTERNAL_REMOTE_URLS` | No | `false` | Permit non-local remote URLs |
