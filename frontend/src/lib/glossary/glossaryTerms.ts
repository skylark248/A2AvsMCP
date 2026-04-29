/**
 * Static glossary of protocol terms used across the comparison UI.
 * Follows the FIELD_ANNOTATIONS pattern from ProtocolEnvelopeDrawer.tsx:
 * module-level Record<string, string>, no function wrappers, no imports.
 */
export const glossaryTerms: Record<string, string> = {
  mcp: "Model Context Protocol -- a standard that lets an LLM call server-hosted tools via a structured request/response contract.",
  a2a: "Agent-to-Agent protocol -- a Google-led standard where agents advertise capabilities via Agent Cards and delegate tasks to peer agents.",
  tool_call:
    "A discrete request from an LLM to invoke a named function exposed by an MCP server.",
  task_submit:
    "An A2A operation where one agent sends a unit of work to a specialist agent for asynchronous handling.",
  agent_card:
    "A JSON manifest that describes an A2A agent's identity, capabilities, and endpoint -- the discovery document for peer agents.",
  transport:
    "The channel over which protocol messages travel -- in-process (same process), stdio (subprocess pipe), HTTP, or remote HTTP.",
  broker:
    "The A2A orchestrator that receives a ticket, classifies intent, and dispatches tasks to the right specialist agents.",
  specialist_agent:
    "An A2A agent focused on a single domain (e.g., billing, documentation) that handles delegated tasks from the broker.",
  parallel_dispatch:
    "An A2A pattern where the broker sends tasks to multiple specialists simultaneously rather than sequentially.",
  step_index:
    "A monotonically increasing counter on trace events that shows the depth of sequential tool calls within a single run.",
  parallel_batch_id:
    "A shared identifier on events that belong to the same parallel dispatch batch, enabling swimlane grouping.",
  discovery_phase:
    "The initial portion of an A2A run where agents register and the broker resolves which specialists to contact.",
  execution_phase:
    "The portion of a run where tools are called (MCP) or tasks are dispatched (A2A) to produce the final answer.",
  mock_runtime:
    "A fully deterministic in-process execution path that requires no API keys and produces consistent trace data.",
  llm_runtime:
    "The OpenAI GPT-4o-mini execution path where real LLM calls are made -- latency reflects live API response times.",
  baseline:
    "The single-agent execution mode where one LLM handles the ticket without MCP tools or A2A coordination.",
  hybrid:
    "A mode that combines MCP tool access with A2A agent coordination -- both protocols active in the same run.",
  // Race page terms — UIRACE-07 / 08-UI-SPEC.md Glossary Extension table (verbatim)
  ttff: "Time to first fault — the elapsed milliseconds from run start until the first injected fault event lands in the trace.",
  recovery_rate: "The fraction of runs in which the agent fully recovered from an injected fault, expressed as a count (e.g. 12/15).",
  hardness_profile: "A structured description of the difficulty characteristics of a task — which hardness types apply and at what intensity.",
  recovered: "A fault classification tag: the agent detected the fault and returned to a correct execution path within K=3 turns.",
  gave_up: "A fault classification tag: the agent detected the fault and abandoned the task rather than attempting recovery.",
  kept_going_without_noticing: "A fault classification tag: the agent did not acknowledge the fault and continued executing as if nothing had changed.",
  kept_going_to_failure: "A fault classification tag: the agent continued past the fault point and ultimately produced an incorrect or failed result.",
  indeterminate: "A fault classification tag: the available trace evidence was insufficient to assign any of the four primary recovery tags.",
};
