# Remote MCP Endpoint Mode

`remote_http` lets the demo call explicit remote MCP endpoints instead of the local in-process DB/docs servers.

This is intentionally not remote service discovery. The user provides the endpoint URLs, and the demo expects those endpoints to expose the same tool contracts as the local demo MCP servers.

## When To Use It

Use `remote_http` when you want to show that MCP tools can live outside the local process or machine:

```powershell
py main.py --scenario setup_error --mode mcp --mcp-transport remote_http --remote-mcp-db-url http://127.0.0.1:9001/mcp --remote-mcp-docs-url http://127.0.0.1:9002/mcp
```

In the React UI, choose `remote_http` from the MCP transport control. The remote DB and docs URL fields appear only for that transport.

You can also choose a configured registry entry in the React run workspace. Registry entries live in [REMOTE_MCP_REGISTRY.json](REMOTE_MCP_REGISTRY.json) and are synced into the durable SQLite state store.

## Required Tool Contracts

The remote DB endpoint should expose the same tool names used by the local database server:

- `get_customer_profile`
- `get_order_history`
- `get_payment_issues`
- `get_ticket_history`
- `get_warranty`

The remote docs endpoint should expose the same tool names used by the local documentation server:

- `search_docs`
- `get_policy`

The demo passes the same argument shapes that the local MCP servers receive. Keep remote responses JSON-serializable and close to the local server responses if you want reports and traces to remain comparable.

## Fallback Behavior

If a remote URL is missing or unavailable, the MCP client falls back to local in-process MCP. The trace records the requested transport and active transport so the report can show what happened.

This fallback is useful for live demos: a remote endpoint outage should not break the comparison story. For readiness checks, use explicit URLs so a missing remote configuration is caught before presenting.

## Environment Variables

The backend can also read remote URLs from environment variables:

```powershell
$env:REMOTE_MCP_DB_URL="http://127.0.0.1:9001/mcp"
$env:REMOTE_MCP_DOCS_URL="http://127.0.0.1:9002/mcp"
```

## Readiness Check

Use the demo readiness script when validating remote endpoints:

```powershell
powershell.exe -ExecutionPolicy Bypass -File scripts\demo_check.ps1 -Profile demo -Transport remote_http -RemoteDbUrl http://127.0.0.1:9001/mcp -RemoteDocsUrl http://127.0.0.1:9002/mcp
```

If you do not provide `-RemoteDbUrl` or `-RemoteDocsUrl`, the script reads `REMOTE_MCP_DB_URL` and `REMOTE_MCP_DOCS_URL`.

For the smallest possible check, run the Python helper directly:

```powershell
py scripts\check_remote_mcp.py --db-url http://127.0.0.1:9001/mcp --docs-url http://127.0.0.1:9002/mcp
```

This helper fails if the remote endpoints fall back to local in-process MCP.

## Registry API

List registry entries:

```powershell
curl.exe http://127.0.0.1:8008/api/mcp/registry
```

Sync `REMOTE_MCP_REGISTRY.json` into the durable registry table:

```powershell
curl.exe -X POST http://127.0.0.1:8008/api/mcp/registry/sync
```

## What This Does Not Do

This project does not include a marketplace, auth flow, or managed remote endpoint credentials. The registry is intentionally a small configured endpoint catalog for demos.
