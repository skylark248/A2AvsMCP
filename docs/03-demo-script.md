# Demo Script

Use this script for a firm walkthrough or for recording a short public demo.

## Five-Minute Walkthrough

1. Open `/learn`.
2. State the core distinction: MCP is tool access; A2A is agent collaboration.
3. Run the `baseline` lesson and point out the low protocol activity.
4. Run the `mcp` lesson and point out `tool_discovery` and `tool_call` trace counts.
5. Run the `a2a` lesson and point out task routing, status, and specialist collaboration.
6. Run the `hybrid` lesson and point out that both tool calls and agent messages appear.
7. Move to `/` and run all modes for `setup_and_warranty` or `enterprise_setup_replacement`.
8. Open the saved report detail and show scorecards, trace evidence, HTML export, PDF export, and evidence bundle export.

## Fifteen-Minute Workshop

1. Start with `/learn` and the comparison table.
2. Ask the audience what they expect to change between the four modes.
3. Run the same scenario in each lesson mode.
4. Open `/traces` and compare event categories.
5. Return to `/` and enable one failure toggle:
   - `db_down` for MCP resilience
   - `docs_timeout` for documentation-tool fallback
   - disabled specialist for A2A routing and failure visibility
6. Save a report and open `/reports`.
7. Use `/trends` after a few saved runs to show how repeated demos accumulate evidence.
8. Use `/presentation` when the audience needs a cleaner story flow.
9. Use `/telemetry` to show durable activity across users and modes.

## Remote A2A Add-On

Use this after the local comparison when the audience is ready for the hosted protocol boundary.

1. Start the hosted stack:

```powershell
docker compose up --build -d
py scripts\check_remote_a2a.py
```

2. Open `/`, choose `warranty_return` or `setup_and_warranty`, and set `A2A Transport` to `Remote HTTP`.
3. Use `Registry Health` to show that the three hosted specialists expose reachable Agent Cards.
4. Run `a2a`, then run `hybrid`.
5. Open `/traces` and point out remote discovery, remote sends, task status, artifacts, and promoted MCP tool events in hybrid mode.
6. For a failure moment, enable bad auth or use:

```powershell
py main.py --scenario warranty_return --mode a2a --a2a-transport remote --remote-a2a-bad-auth
```

7. Stop the hosted stack when the walkthrough is done:

```powershell
docker compose down
```

The shorter remote presenter cue card lives in [05-remote-a2a-presentation.md](05-remote-a2a-presentation.md).

## Recommended Scenarios

| Scenario | Use It For |
| --- | --- |
| `order_status` | Fast, simple opener. |
| `setup_error` | Clear docs-tool MCP story. |
| `warranty_return` | Policy and customer-data combination. |
| `setup_and_warranty` | Good learning-mode scenario because it needs docs and policy. |
| `enterprise_setup_replacement` | Strong firm-demo scenario with enterprise flavor. |
| `invoice_and_warranty_followup` | Good multi-concern follow-up story. |

## Presenter Notes

Use plain language:

- MCP: "The agent knows how to use tools through a standard contract."
- A2A: "Agents know how to hand work to each other and report status."
- Hybrid: "Specialist agents collaborate, and each specialist uses tools through MCP."

Avoid overselling A2A in this repo as a production SDK-native A2A 1.0 deployment. The project uses an educational local A2A-style broker for visible lifecycle learning and a hosted remote A2A demo binding behind `sdk_compat.py`; SDK-native A2A 1.0 migration is deferred until the official Python SDK line is stable.
