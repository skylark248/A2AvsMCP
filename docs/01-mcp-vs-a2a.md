# MCP vs A2A: The Mental Model

This project teaches MCP and A2A by running the same support ticket through four modes: baseline, MCP, A2A-style collaboration, and hybrid.

## Short Version

MCP answers: how does an agent connect to tools, data, and external capabilities?

A2A answers: how do agents assign work, collaborate, report status, recover from failures, and merge results?

Hybrid answers: what happens when specialist agents collaborate with each other and use MCP-backed tools to do their part of the work?

## MCP In This Project

MCP is implemented with official MCP SDK servers and clients.

The demo includes two local MCP servers:

- database server: customer, order, payment, ticket, and warranty data
- documentation server: setup, troubleshooting, refund, warranty, and transport guidance

The MCP client supports these transport choices:

- `in_process`: fastest local learning path
- `stdio`: subprocess boundary that resembles command-based MCP server usage
- `http`: local streamable HTTP MCP server subprocesses
- `remote_http`: remote endpoint contract with safe fallback to local in-process tools

When you run MCP mode, watch for these trace events:

- `tool_discovery`
- `tool_call`
- `tool_error`
- `tool_transport_fallback`

## A2A In This Project

The A2A side is an educational A2A-style task lifecycle model. It is intentionally explicit so learners can see routing, delegation, retries, status events, and result merging.

The core actors are:

- `triage_agent`: classifies the ticket and coordinates work
- `customer_data_agent`: handles customer and order evidence
- `documentation_agent`: handles documentation and troubleshooting evidence
- `policy_or_billing_agent`: handles billing, warranty, refund, and return policy evidence

When you run A2A mode, watch for these trace events:

- `agent_register`
- `capability_advertise`
- `task_request`
- `task_accept`
- `task_progress`
- `task_status`
- `task_result`
- `task_retry`
- `task_error`
- `triage_merge`

## Why The Four Modes Matter

| Mode | What It Teaches | What To Watch |
| --- | --- | --- |
| `baseline` | One agent owns the whole answer. | Minimal protocol activity. |
| `mcp` | One agent uses structured external tools. | MCP discovery, tool calls, transport choice. |
| `a2a` | Multiple specialists collaborate. | Task routing, status events, retries, merge. |
| `hybrid` | Specialists collaborate and use MCP tools. | Both A2A messages and MCP tool calls. |

## Real-Life Analogy

Imagine a customer asks: "My setup is failing, and I also need to know whether this product is under warranty."

- Baseline: one support rep answers directly.
- MCP: one support rep opens the order system and knowledge base through standard tools.
- A2A: a triage rep asks setup, customer data, and policy specialists for help.
- Hybrid: those specialists coordinate through tasks and each specialist uses standard tools for the evidence they need.

That is the architectural difference this repo is built to make visible.

## A2A Fidelity Note

The broker now emits A2A 1.0-shaped educational trace payloads alongside the readable demo events:

- Agent Cards use `protocolVersion`, `preferredTransport`, `capabilities`, `defaultInputModes`, `defaultOutputModes`, `skills`, and `metadata`.
- Task requests include a `message/send` method label, `ROLE_USER`, `taskId`, `contextId`, and message `parts`.
- Task lifecycle events include `status-update` payloads with `submitted`, `working`, `completed`, and `failed` states.
- Specialist results include `artifact-update` payloads with text and data parts.

For the default local transport, this is still a local educational broker. The purpose is to make the protocol architecture visible in traces before adding any hosted server boundary.

Phase 6 adds that remote boundary as an explicit demo path: separately hosted A2A specialist servers, Agent Card discovery, remote task/message exchange, remote task status/artifacts, health checks, failure toggles, and UI controls for choosing local versus remote A2A transport. The remote path uses a versioned demo HTTP binding behind `sdk_compat.py`; SDK-native A2A 1.0 migration is deferred until the official Python SDK line is stable. See [PHASE6.md](../PHASE6.md) and [REMOTE_A2A.md](../REMOTE_A2A.md).
