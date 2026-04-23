# Remote A2A Demo Mode

Phase 6 adds a hosted remote A2A path beside the existing local educational broker.

Current implementation status: complete for demo scope. The hosted remote A2A path has CLI/API/UI controls, health checks, failure toggles, trace filtering support, curated examples, and Docker Compose orchestration. The backend supports `a2a_transport=remote` for `a2a` and `hybrid` runs, using separately hosted HTTP specialist services and a versioned demo JSON-RPC binding behind `sdk_compat.py`.

## SDK Position

The project keeps the remote wire boundary behind `src/a2a_vs_mcp/a2a/sdk_compat.py`.

Decision as of 2026-04-07: pin the optional `remote-a2a` extra to the current stable official Python SDK release, `a2a-sdk[http-server]==0.3.25`, which implements A2A spec `0.3`. The repo still keeps the runtime remote demo behind `sdk_compat.py` because its teaching traces are A2A `1.0`-shaped, and the official 1.0-capable SDK line is still alpha/dev. The migration target is SDK-native server/client types once official 1.0 support is stable enough for the public wire contract.

Optional install path:

```powershell
py -m pip install -e ".[remote-a2a]"
```

The implemented remote path works without that optional extra because it uses the local demo binding and FastAPI.

## Start Specialist Servers

Start each remote specialist in a separate terminal:

```powershell
$env:PYTHONPATH="src"
py -m a2a_vs_mcp.a2a.remote_server --role customer_data --port 9101
py -m a2a_vs_mcp.a2a.remote_server --role documentation --port 9102
py -m a2a_vs_mcp.a2a.remote_server --role policy_billing --port 9103
```

Or start all three with the helper script. The script prints the process IDs so you can stop the demo services when you are done:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\start_remote_a2a.ps1
```

## Verify Remote A2A

```powershell
py scripts\check_remote_a2a.py
```

Then run a remote A2A scenario:

```powershell
py main.py --scenario warranty_return --mode a2a --a2a-transport remote
```

Run remote hybrid with MCP-backed hosted specialists:

```powershell
py main.py --scenario setup_and_warranty --mode hybrid --a2a-transport remote --mcp-transport in_process
```

The trace records remote Agent Card discovery, remote sends, remote status updates, remote artifacts, retries, failures, and promoted remote MCP tool events for hybrid runs.

## Docker Compose

Run the web app plus all three hosted specialists from one clean clone:

```powershell
docker compose up --build -d
py scripts\check_remote_a2a.py
docker compose down
```

The compose file publishes the web UI on `http://127.0.0.1:8008` and the specialists on ports `9101`, `9102`, and `9103`. Inside the compose network, Agent Cards advertise container DNS names such as `http://a2a-customer-agent:9101` while the host ports remain available for the checker script.

## Registry

Default local remote A2A endpoints live in `REMOTE_A2A_REGISTRY.json`:

```json
{
  "agents": {
    "customer_data": "http://127.0.0.1:9101",
    "documentation": "http://127.0.0.1:9102",
    "policy_billing": "http://127.0.0.1:9103"
  }
}
```

The backend exposes this through:

- `GET /api/a2a/registry`
- `GET /api/a2a/health`

The React run workspace can select `Remote HTTP` under `A2A Transport`, check the configured specialist health, and edit the three specialist URLs.

By default, API-submitted remote MCP/A2A URLs are limited to local, private-network, and Docker Compose-style hosts. To intentionally call external hosted endpoints in a trusted deployment, set `A2A_VS_MCP_ALLOW_EXTERNAL_REMOTE_URLS=true`.

For a presenter-friendly walkthrough, see [docs/05-remote-a2a-presentation.md](docs/05-remote-a2a-presentation.md).

## Demo Auth

Each remote specialist can require a simple bearer token:

```powershell
$env:REMOTE_A2A_TOKEN="demo-token"
py -m a2a_vs_mcp.a2a.remote_server --role customer_data --port 9101
```

Then provide the same token from the React run workspace or CLI:

```powershell
py main.py --scenario warranty_return --mode a2a --a2a-transport remote --remote-a2a-auth-token demo-token
```

This is a demo control only. It is not production authentication.

## Failure Toggles

Remote A2A failure simulation is available from the CLI/API and React run workspace:

```powershell
py main.py --scenario warranty_return --mode a2a --a2a-transport remote --remote-a2a-bad-auth
py main.py --scenario setup_and_warranty --mode hybrid --a2a-transport remote --remote-a2a-malformed-response
py main.py --scenario setup_and_warranty --mode hybrid --a2a-transport remote --remote-a2a-task-failure
```

The supported flags are `--remote-a2a-timeout`, `--remote-a2a-bad-auth`, `--remote-a2a-missing-capability`, `--remote-a2a-malformed-response`, and `--remote-a2a-task-failure`. Each path records remote A2A failure/retry/status events rather than silently falling back to local A2A.

## Deferred Future Work

These are not required for Phase 6 demo completion:

- migrate to SDK-native A2A 1.0 server/client types when that official line is stable
- keep Docker Compose smoke outputs current when the container image changes
- broaden health visualization beyond the run workspace if a future demo needs a dedicated operations view
- expand remote failure screenshots or video assets if the project needs a polished public launch package

