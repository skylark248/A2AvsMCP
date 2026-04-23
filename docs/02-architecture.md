# Architecture Walkthrough

This walkthrough maps the learning goal to the codebase.

## Runtime Spine

`DemoPlatform` is the central orchestrator. It receives a ticket, selects the mode, records a trace, runs the matching path, saves artifacts, and builds comparison metrics.

Key file: `src/a2a_vs_mcp/platform.py`

Mode handlers:

- `_run_baseline`: single support agent, no MCP and no A2A messages
- `_run_mcp`: single support agent plus MCP tool clients
- `_run_a2a`: triage agent plus local or hosted remote specialist agents
- `_run_hybrid`: triage agent plus local or hosted remote MCP-enabled specialist agents

## MCP Path

The MCP path lives in three areas:

- `src/a2a_vs_mcp/mcp_servers/db_server.py`
- `src/a2a_vs_mcp/mcp_servers/docs_server.py`
- `src/a2a_vs_mcp/mcp/client.py`

The client discovers tools before calling them. If a requested live transport cannot start or connect, the trace records the requested transport, the active fallback transport, and the error.

Hybrid mode pools MCP clients through `AgentContext` so HTTP server subprocesses are reused per run instead of restarted for every specialist task.

## A2A-Style Path

The A2A-style collaboration path lives in:

- `src/a2a_vs_mcp/a2a/broker.py`
- `src/a2a_vs_mcp/agents/triage.py`
- `src/a2a_vs_mcp/agents/specialists.py`
- `src/a2a_vs_mcp/agents/hybrid_specialists.py`

The broker models:

- agent registration
- capability lookup
- task request
- accepted, in progress, completed, and failed status events
- retry on transient failure
- timeout handling
- fallback routing by capability when configured

## Hosted Remote A2A Path

Phase 6 adds an explicit hosted transport beside the local broker:

- `src/a2a_vs_mcp/a2a/sdk_compat.py`: versioned demo binding and SDK decision metadata
- `src/a2a_vs_mcp/a2a/remote_server.py`: hosted specialist server entry point
- `src/a2a_vs_mcp/a2a/remote_client.py`: remote HTTP client
- `src/a2a_vs_mcp/a2a/remote_broker.py`: remote discovery, routing, task send, and response normalization
- `src/a2a_vs_mcp/a2a/registry.py`: configured remote specialist endpoints
- `REMOTE_A2A_REGISTRY.json`: default local remote specialist registry
- `docker-compose.yml`: web app plus three hosted specialist services

The remote path records Agent Card discovery, remote sends, task status, artifacts, retries, failures, and promoted MCP tool events for hybrid remote runs. SDK-native A2A 1.0 migration is deferred until the official Python SDK line is stable.

## UI Surfaces

The React app is the primary UI.

- `/learn`: guided protocol lesson
- `/`: run workspace for hands-on experiments
- `/reports`: saved report library
- `/reports/:reportName`: report detail, exports, scorecards, traces
- `/traces`: trace exploration and log replay
- `/trends`: cross-report analytics
- `/presentation`: firm-demo presentation flow
- `/telemetry`: durable run/report activity snapshot

The legacy server-rendered dashboard remains under `/legacy` for comparison and fallback.

## Persistence And Artifacts

Generated artifacts are intentionally local and ignored by git by default.

- `artifacts/support_demo.db`: deterministic seed database
- `artifacts/reports`: saved report JSON
- `artifacts/traces`: trace JSON
- `artifacts/logs`: NDJSON export logs
- `artifacts/platform_state.db`: durable telemetry and registry state
- `artifacts/users/<user>`: optional user-scoped artifacts
- `A2A_VS_MCP_ARTIFACT_ROOT`: optional override for tests or throwaway demo artifact trees

## Contract Boundaries

The public API is declared with Pydantic schemas in `src/a2a_vs_mcp/api_schemas.py`. Frontend TypeScript types are generated into `frontend/src/lib/types/api.generated.ts` with `scripts/generate_api_types.py`.

When backend response shapes change, regenerate the frontend API types and run both backend and frontend tests.
