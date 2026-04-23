# Demo Operator Runbook

Use this checklist before a workshop, firm demo, or recording. It keeps the demo deterministic while still letting you switch to hosted remote A2A when the specialist services are running.

## Fast Local Demo

```powershell
py scripts\golden_demo_smoke.py
py serve_ui.py
```

Open `http://127.0.0.1:8008` and run `setup_and_warranty` in `all` mode. This path uses deterministic mock runtime, local A2A, and in-process MCP by default.

## Hosted Remote A2A Demo

Start the three specialist services:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\start_remote_a2a.ps1
py scripts\check_remote_a2a.py
py scripts\golden_demo_smoke.py --include-remote-a2a
```

Then open the React run workspace, select `A2A Transport` -> `Remote HTTP`, and use the health check before running `warranty_return` or `setup_and_warranty`.

## Docker Compose Demo

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\docker_compose_smoke.ps1
```

Use `-KeepRunning` when you want the services left online after the smoke check. The script writes golden run artifacts under `.tmp\compose_smoke_artifacts` by default; pass `-ArtifactRoot <path>` to change that.

The web UI is published at `http://127.0.0.1:8008`, and the remote specialists are published on `9101`, `9102`, and `9103`.

## Reset Generated State

Dry-run first if you want to see what will be removed:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\demo_reset.ps1 -CleanGenerated -DryRun
powershell.exe -ExecutionPolicy Bypass -File scripts\demo_reset.ps1 -CleanGenerated -RegenerateApiTypes
```

`-CleanGenerated` clears generated reports, traces, logs, user artifacts, telemetry, and disposable `.tmp` smoke/test artifact roots. Use `-ClearTmpArtifacts` when you only want to remove `.tmp\test_artifacts` and `.tmp\compose_smoke_artifacts`. It preserves curated docs, examples, source files, and remote registry JSON files.

## Known Demo Failure Modes

- Docker API access denied: rerun the Compose smoke from a shell with Docker Desktop running and permission to access the Docker engine.
- Ports `8008`, `9101`, `9102`, or `9103` already in use: stop the conflicting process or adjust the Compose/remote A2A port mapping before running the hosted demo.
- Remote A2A health is red: run `py scripts\check_remote_a2a.py` to see which specialist Agent Card or task endpoint is failing.
- Web health does not become ready: check `docker compose logs web` and confirm the frontend build exists inside the image.
- Windows sandbox blocks Vite/esbuild or Docker process spawning: rerun the affected `npm` or Docker command with elevated execution in the local shell.
- A live MCP transport falls back: open `/traces` and use the requested/actual transport events as the recovery story rather than treating it as a silent failure.
## Fallbacks

If remote A2A is not running, use local A2A and hybrid modes. The teaching story still works: local A2A shows delegation, MCP shows tool boundaries, and hybrid shows both together.

If frontend build output is missing, either run `npm.cmd --prefix frontend run build` before `py serve_ui.py`, or use Vite dev mode with the FastAPI backend running.

If a live transport fails during MCP demos, the trace records the requested transport and fallback path. Use `/traces` to show the failure and recovery event.

## Best Scenarios

- `setup_and_warranty`: best all-around story for baseline, MCP, A2A, and hybrid comparison.
- `warranty_return`: concise A2A policy/customer-data delegation story.
- `delay_and_billing`: good failure/resilience and cross-domain evidence story.
- `enterprise_setup_replacement`: deeper enterprise-style scenario for longer walkthroughs.

## Non-Goals For Now

This is still a local/demo learning platform. Public hosting hardening, production authentication, tenant-grade isolation, and managed external endpoint administration are intentionally deferred.