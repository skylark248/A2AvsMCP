# Improvement Log

## 2026-04-07 Phase 6 Remote A2A Implementation Slice

Added:

- separate `a2a_transport` axis with `local` as the default and `remote` as an explicit hosted path
- versioned remote A2A compatibility layer plus stable optional SDK pin while avoiding local trace labels as the public wire contract
- hosted remote specialist server for customer data, setup/documentation, and policy/billing roles
- remote A2A client, broker, registry, and Agent Card helpers
- remote A2A registry file and API endpoints under `/api/a2a/registry` and `/api/a2a/health`
- CLI and React run workspace controls for hosted remote A2A
- remote hybrid trace promotion for MCP tool events produced inside hosted specialists
- remote A2A check/start scripts and setup documentation in `REMOTE_A2A.md`
- regression coverage for hosted remote A2A execution and OpenAPI schema updates
- remote A2A failure toggles for timeout, bad auth, missing capability, malformed response, and task failure
- trace filtering/counting updates for remote A2A events
- Docker Compose orchestration for web plus three hosted A2A specialists
- typed remote A2A health endpoint plus run-workspace health check UI
- curated remote A2A bad-auth trace/report examples
- remote A2A presenter cue card in `docs/05-remote-a2a-presentation.md`
- remote A2A topology SVG in `docs/media/remote-a2a-topology.svg`

Deferred future work:

- SDK-native A2A 1.0 adapter replacement after the official 1.0-capable SDK line is stable
- richer UI health panels beyond the run workspace, if a future demo needs a dedicated operations view
- additional screenshots or video assets if the project needs a polished public launch package

## 2026-04-07 Learning And Public Readiness Pass

Added:

- guided `/learn` UI for MCP vs A2A concepts
- protocol-fidelity note in the learning surface
- conceptual MCP vs A2A documentation
- architecture walkthrough documentation
- firm-demo and workshop script
- public GitHub readiness checklist
- CI workflow for backend, frontend, validation, and build checks
- `.env.example`, Dockerfile, and Docker ignore defaults
- license file for public reuse

Also hardened earlier:

- evidence bundles now use the active report service for user-scoped reports
- HTTP MCP server startup failures include captured stderr without subprocess pipe backpressure
- seed database rebuilds use a temporary database and replace only after a successful rebuild

## 2026-04-07 Deeper A2A Fidelity Pass

Added:

- A2A protocol helper module with 1.0-shaped Agent Card, message, task status update, task snapshot, and artifact update payloads
- broker trace events that include `a2a_protocol_version`, `a2a_method`, `a2a_message`, `a2a_task_event`, `a2a_task`, and `a2a_artifact_event`
- regression coverage for A2A-shaped payloads
- README media assets and curated example outputs

Scope note: this improves protocol fidelity for learning and trace inspection. It does not yet expose specialists as remote A2A HTTP services.

## 2026-04-07 Phase 6 Remote A2A Planning

Added:

- `PHASE6.md` as the implementation contract for hosted remote A2A
- README phase status and documentation links for the planned Phase 6 work
- learning-doc note that hosted remote A2A is the next protocol-boundary expansion

Planned Phase 6 scope:

- hosted remote A2A specialist servers
- remote Agent Card discovery and health checks
- remote A2A client/broker transport
- local versus remote A2A UI controls
- remote A2A traces, failures, scripts, Docker Compose, docs, and tests

