# Connecting Claude Desktop to This MCP Server

This project runs real MCP servers using the official Python MCP SDK. You can point
Claude Desktop (or any MCP-compatible client) at these servers to use them outside
the demo UI — which demonstrates that MCP is a genuine interoperability protocol,
not just an internal abstraction.

## What you get

The **Support Docs MCP** server exposes:
- **Tool** `search_docs` — keyword search over the local documentation corpus
- **Tool** `get_policy` — fetch refund or warranty policy by type
- **Resource** `policy://refund` — full refund policy text at a stable URI
- **Resource** `policy://warranty` — full warranty rules text at a stable URI
- **Prompt** `support_triage` — reusable triage prompt template (args: `ticket_query`, `customer_id`)

The **Support Database MCP** server exposes:
- **Tool** `get_customer_profile` — look up a customer record
- **Tool** `get_order_history` — list all orders for a customer
- **Tool** `get_payment_issues` — find payment issues for a customer or order
- **Tool** `get_ticket_history` — list prior support tickets
- **Tool** `get_warranty` — fetch warranty records
- **Resource** `customer://{customer_id}` — customer profile at a parameterised URI

## Claude Desktop config (stdio transport)

Add the following to your `claude_desktop_config.json`
(`%APPDATA%\Claude\claude_desktop_config.json` on Windows,
`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "a2a-vs-mcp-docs": {
      "command": "py",
      "args": [
        "-m", "a2a_vs_mcp.mcp_servers.docs_server",
        "--docs-dir", "D:\\A2A vs MCP\\data\\docs"
      ],
      "cwd": "D:\\A2A vs MCP",
      "env": {
        "PYTHONPATH": "D:\\A2A vs MCP\\src"
      }
    },
    "a2a-vs-mcp-db": {
      "command": "py",
      "args": [
        "-m", "a2a_vs_mcp.mcp_servers.db_server",
        "--db-path", "D:\\A2A vs MCP\\artifacts\\platform_state.db"
      ],
      "cwd": "D:\\A2A vs MCP",
      "env": {
        "PYTHONPATH": "D:\\A2A vs MCP\\src"
      }
    }
  }
}
```

Adjust `D:\\A2A vs MCP` to match your actual clone path.

## Verify the connection

After restarting Claude Desktop, open a new conversation and ask:

> "What tools do you have available?"

You should see `search_docs`, `get_policy`, `get_customer_profile`, and the other
tools listed above. This proves the MCP server is a real protocol endpoint — the
same server the demo platform uses internally is now serving Claude Desktop.

To test a resource:

> "Read the resource policy://warranty"

To invoke the prompt template:

> "Use the support_triage prompt for ticket_query='My order is delayed' and customer_id='C001'"

## HTTP transport (for remote or multi-client use)

Start the servers with `--transport streamable-http`:

```powershell
py -m a2a_vs_mcp.mcp_servers.docs_server --docs-dir data\docs --transport streamable-http --port 9002
py -m a2a_vs_mcp.mcp_servers.db_server --db-path artifacts\platform_state.db --transport streamable-http --port 9001
```

Then configure Claude Desktop with `"url": "http://127.0.0.1:9002/mcp"` instead of
`command`/`args`. This is the same HTTP transport the demo platform uses when you
select **MCP Transport: http** or **remote_http** in the Runs workspace.

## What this teaches

Running the same MCP server from both the demo platform and Claude Desktop makes the
protocol boundary concrete: the server does not care which client is calling it.
This is the core MCP promise — standardised capability exposure that any conformant
client can consume.
