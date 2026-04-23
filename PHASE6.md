# Phase 6 Completion Record: Hosted Remote A2A

Phase 6 turns the current local A2A-style broker into a hosted remote A2A demo path while keeping the existing local broker as the beginner-friendly learning baseline.

Status: complete for demo scope as of 2026-04-07. Hosted remote A2A backend/frontend, failure simulation, trace visibility, health UI, curated examples, and Docker Compose verification are implemented.

Target outcome: passed for the project scope. SDK-native A2A 1.0 migration is intentionally deferred until the official Python SDK's 1.0-capable line is stable.


## Completed Scope

Phase 6 slices implemented on 2026-04-07:

- `a2a_transport = local | remote` added as a separate transport axis from MCP transport
- local A2A remains the default for profiles and existing demos
- versioned remote A2A compatibility layer added in `src/a2a_vs_mcp/a2a/sdk_compat.py`
- hosted specialist server module added at `src/a2a_vs_mcp/a2a/remote_server.py`
- remote client, broker, registry, and model helpers added under `src/a2a_vs_mcp/a2a/`
- default `REMOTE_A2A_REGISTRY.json` added for local specialist endpoints
- CLI supports `--a2a-transport remote` and remote specialist URL/token overrides
- API supports `a2a_transport` in run requests and exposes `/api/a2a/registry` plus `/api/a2a/health`
- React run workspace includes an A2A transport control and remote specialist URL fields
- remote hybrid promotes hosted specialist MCP tool events into the main trace with `remote_trace=true`
- remote A2A checker and starter scripts added: `scripts/check_remote_a2a.py` and `scripts/start_remote_a2a.ps1`
- regression coverage added for a successful hosted remote A2A run and API schema/registry exposure
- remote A2A failure toggles added for timeout, bad auth, missing capability, malformed response, and task failure
- trace explorer and trace workspace count/filter remote A2A events and remote failure/retry signals
- `docker-compose.yml` added for the web app plus three hosted remote A2A specialists
- Docker Compose smoke verification passed: `docker compose up --build -d`, `py scripts\check_remote_a2a.py`, API `/api/run` remote A2A check, and `docker compose down`
- remote A2A health response typed in OpenAPI and surfaced from the React run workspace
- curated remote A2A bad-auth trace/report examples added under `examples/`


Important implementation note: this slice uses a narrow versioned demo HTTP binding behind `sdk_compat.py`. The optional official SDK dependency is pinned to stable `a2a-sdk[http-server]==0.3.25`, which implements A2A spec `0.3`; SDK-native server/client migration is deferred until the official 1.0-capable line is stable enough for the public wire contract.

## Goal

Phase 6 makes the agent-to-agent protocol boundary concrete:

- local A2A remains available for fast teaching and deterministic tests
- remote A2A runs specialists as separately hosted HTTP services
- the platform can discover remote Agent Cards, route tasks by skill, send messages, receive task status/artifacts, and recover from remote failures
- the UI can show users the difference between "agent collaboration inside one process" and "agent collaboration across a network/protocol boundary"
- Docker Compose can run the web app plus remote specialist agents from a clean public clone

In demo terms, the project should support this story:

```text
Baseline: one agent handles the ticket directly
MCP: one agent calls external tools through MCP
A2A local: agents collaborate through an in-process task lifecycle broker
A2A remote: agents collaborate through hosted A2A HTTP specialist services
Hybrid remote: hosted specialist agents collaborate and use MCP-backed tools for evidence
```

## Protocol Position

Phase 6 pins the optional official A2A Python SDK dependency but keeps the hosted demo path behind `sdk_compat.py`. The current educational trace helpers in `src/a2a_vs_mcp/a2a/protocol.py` normalize trace payloads; they are not treated as a production public wire protocol.

References:

- A2A specification: https://a2a-protocol.org/latest/specification/
- A2A Python server quickstart: https://a2a-protocol.org/latest/tutorials/python/5-start-server/
- A2A discovery docs: https://a2a-protocol.org/latest/topics/agent-discovery/

SDK-native server/client migration is deferred until the official 1.0-capable Python SDK line is stable. Until then, the remote demo binding remains explicitly versioned and binding-aware.

## Starting Point

Already implemented before Phase 6:

- `baseline`, `mcp`, `a2a`, and `hybrid` modes
- local `A2ABroker` with routing, lifecycle trace events, retries, failure events, and timeouts
- A2A-shaped educational trace payloads for Agent Card, message, task status, task snapshot, and artifact update
- official MCP SDK-backed MCP path
- remote MCP registry and `remote_http` transport
- React run workspace, learning workspace, trace workspace, reports, presentation mode, telemetry, and curated examples
- Docker image build and smoke check

## Architecture

Phase 6 adds a remote A2A transport beside the existing local transport.

```text
React UI / CLI
  -> DemoPlatform
    -> TriageAgent
      -> Local A2ABroker              # existing path
      -> RemoteA2ABroker/A2A client   # new path
        -> Agent Card registry
        -> HTTP A2A specialist server: setup
        -> HTTP A2A specialist server: customer data
        -> HTTP A2A specialist server: policy/billing
```

Hybrid remote mode adds MCP inside the remote specialist server:

```text
TriageAgent
  -> remote A2A policy specialist
    -> MCP docs server
  -> remote A2A customer specialist
    -> MCP DB server
```

## Deliverables

### 1. Dependency And SDK Integration

- Keep the optional `remote-a2a` extra pinned to stable `a2a-sdk[http-server]==0.3.25`; revisit SDK-native server/client integration when the official 1.0-capable line is stable.
- Pin or document the supported SDK version.
- Add a small compatibility module, for example `src/a2a_vs_mcp/a2a/sdk_compat.py`, so SDK imports do not leak through the whole codebase.
- Add clear fallback errors if the remote A2A feature is requested without the dependency installed.

Exit criteria:

- `py -m a2a_vs_mcp.a2a.remote_server --help` works in a clean dev environment. Implemented for the demo binding.
- The README and `REMOTE_A2A.md` state how to install remote A2A extras if they are optional.

### 2. Remote Specialist Servers

Add hosted specialist agents that wrap the existing specialist classes instead of duplicating business logic.

Suggested files:

- `src/a2a_vs_mcp/a2a/remote_server.py`
- `src/a2a_vs_mcp/a2a/remote_executor.py`
- `src/a2a_vs_mcp/a2a/remote_models.py`

Each server should:

- expose a public Agent Card at `/.well-known/agent-card.json`
- declare `protocolVersion`, supported interface URL, input/output modes, capabilities, and skills
- handle a task/message request for one specialist capability
- return task status and artifacts in A2A-shaped responses
- support a simple demo bearer token when auth is enabled
- support a deterministic mock runtime by default
- support hybrid specialist mode with MCP client configuration

Required specialists:

- setup specialist
- customer data specialist
- policy/billing specialist

Exit criteria:

- three specialist servers can be started on separate ports
- each server returns a valid Agent Card
- each server can process a representative task and return an artifact

### 3. Remote A2A Client And Broker

Add a remote client path that preserves the current platform API.

Suggested files:

- `src/a2a_vs_mcp/a2a/remote_client.py`
- `src/a2a_vs_mcp/a2a/remote_broker.py`
- `src/a2a_vs_mcp/a2a/registry.py`

The remote broker should:

- fetch Agent Cards from configured URLs
- select agents by skill/capability
- send task messages to the selected remote server
- normalize remote responses into the existing `AgentResult`
- capture remote task IDs, context IDs, status updates, artifacts, and failures in the existing trace format
- support timeouts, retries, and capability-mismatch errors
- emit trace events for `a2a_remote_discovery`, `a2a_remote_send`, `a2a_remote_status`, `a2a_remote_artifact`, `a2a_remote_retry`, and `a2a_remote_failure`

Exit criteria:

- `DemoPlatform` can resolve an `a2a` run using remote specialists.
- `DemoPlatform` can resolve a `hybrid` run using remote specialists plus MCP.
- traces clearly show the remote boundary and Agent Card discovery.

### 4. Platform And API Integration

Add remote A2A transport selection without breaking existing modes.

Recommended model:

```text
mode = baseline | mcp | a2a | hybrid
a2a_transport = local | remote
mcp_transport = in_process | stdio | http | remote_http
```

Backend work:

- extend request/response schemas with `a2a_transport`
- add remote A2A registry configuration
- expose remote A2A health/registry API endpoints
- include requested and active A2A transport in reports, traces, and telemetry
- keep `local` as the default transport for fast clone-and-run demos

Suggested routes:

- `GET /api/a2a/registry`
- `POST /api/a2a/registry/sync`
- `GET /api/a2a/health`

Exit criteria:

- existing API clients still work with the default `local` transport.
- remote transport can be selected from API and CLI.
- report metadata records the selected A2A transport.

### 5. Frontend Integration

Add UI affordances that make remote A2A understandable, not just configurable.

Required UI updates:

- Run workspace: `A2A transport` control with `Local broker` and `Remote HTTP`
- Run workspace: remote Agent Card/health panel when remote transport is selected
- Learning page: new section explaining hosted remote A2A
- Trace workspace: filter/highlight remote A2A events
- Report detail: show requested/active A2A transport
- Telemetry page: count local versus remote A2A runs

Exit criteria:

- a user can run an A2A or hybrid scenario through remote A2A from the UI
- the UI explains why the remote trace differs from the local trace
- failed remote servers produce readable UI errors and trace events

### 6. Demo Scripts And Docker Compose

Add one-command local orchestration for public users and firm demos.

Suggested files:

- `docker-compose.yml`
- `scripts/start_remote_a2a.ps1`
- `scripts/check_remote_a2a.py`
- `REMOTE_A2A.md`
- `REMOTE_A2A_REGISTRY.json`

Docker Compose services:

- `web`
- `a2a-documentation-agent`
- `a2a-customer-agent`
- `a2a-policy-agent`
- optional MCP services if needed by hybrid remote mode

Exit criteria:

- `docker compose up --build -d` starts the web app and remote A2A specialists.
- `py scripts\check_remote_a2a.py` validates Agent Cards and one task call per specialist.
- README includes the shortest possible remote A2A demo path.

### 7. Failure Simulation

Remote A2A should teach real network and protocol failure modes.

Required failure toggles:

- remote server unavailable
- remote timeout
- bad auth token
- missing capability
- malformed response or task failure

Exit criteria:

- remote bad-auth, missing-capability, malformed-response, task-failure, timeout, and unavailable-server paths create readable trace/report failure signals
- local A2A fallback behavior is explicit, not silent

### 8. Tests

Add coverage across the remote A2A path.

Backend tests:

- Agent Card generation
- remote specialist request/response conversion
- remote broker capability routing
- timeout/retry/failure handling
- platform runs for `a2a` + `remote`
- platform runs for `hybrid` + `remote`
- API schema backwards compatibility

Frontend tests:

- A2A transport selection payload
- remote registry/health states
- trace filtering for remote A2A events and run-workspace health state display
- error display for unavailable remote agents

Integration/smoke tests:

- `scripts/check_remote_a2a.py`
- `docker-compose.yml`
- Docker Compose smoke check

Exit criteria:

- backend unit tests pass
- frontend tests pass
- remote A2A smoke check passes
- Docker Compose smoke check passes

## Implementation Order

1. Add SDK dependency/compat layer and a minimal remote server for one specialist.
2. Add remote client/broker and make one CLI/API `a2a` run work through the remote server.
3. Expand to all three specialists and add remote Agent Card registry.
4. Add hybrid remote support with MCP-backed remote specialists.
5. Add UI controls, learning copy, and trace filtering.
6. Add scripts, Docker Compose, and public docs.
7. Add full tests and update example outputs.
8. Mark Phase 6 complete only after the verification checklist passes. Completed on 2026-04-07.

## Verification Checklist

Phase 6 demo scope was marked complete after these checks passed:

```powershell
py scripts\check_remote_a2a.py
py scripts\validate_scenarios.py
py scripts\validate_presets.py
py -m unittest discover -s tests
cd frontend
npm.cmd test
npm.cmd run build
cd ..
docker compose up --build -d
py scripts\check_remote_a2a.py
docker compose down
```

The Docker Compose smoke also confirmed:

- the web app is reachable
- all remote A2A Agent Cards are reachable
- an `a2a` remote run completes
- remote A2A health checks pass for the three hosted specialists
- the web API accepts a remote A2A run through `/api/run`
- at least one remote failure toggle creates an expected trace/report example

## Completion Definition

Phase 6 is complete for demo scope because:

- the remote A2A path is implemented in backend, UI, CLI/scripts, Docker Compose, docs, and tests
- local A2A remains the default and still passes existing tests
- remote A2A traces show discovery, network send, task status, artifact, retry, and failure events
- the learning page explains local A2A versus hosted remote A2A
- README includes a quickstart for the remote A2A demo
- curated example outputs include at least one remote A2A or remote hybrid trace: implemented with `warranty_return_remote_a2a_bad_auth_trace.json`

## Deferred Future Work

These are useful follow-ons but are not required for Phase 6 completion:

- migrate the remote binding to SDK-native A2A 1.0 server/client types after the official Python SDK line is stable
- add more public-demo screenshots or video assets if the project needs a polished external presentation package
- broaden remote health visualization beyond the run workspace if a future demo needs a dedicated operations view

## Out Of Scope For Phase 6

These are production-hosting concerns and should not block the learning/demo goal:

- full multi-tenant authorization
- OAuth deployment and key rotation
- public internet hosting
- signed Agent Cards
- managed external agent marketplace integration
- persistent distributed task queues

Phase 6 includes a simple demo auth option and clear documentation, but it does not need to become a production SaaS platform.

