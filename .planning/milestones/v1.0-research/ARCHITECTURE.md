# Architecture Patterns

**Domain:** MCP/A2A educational demo platform — milestone extension
**Researched:** 2026-04-22
**Confidence:** HIGH (grounded in existing codebase analysis) / MEDIUM (UI patterns from observability ecosystem)

---

## Existing Architecture Summary

The platform already has a clean, well-defined component model. The four central abstractions are:

| Component | File | Role |
|-----------|------|------|
| `DemoPlatform` | `platform.py` | Central orchestrator — dispatches all run modes, owns full run lifecycle |
| `DemoRepository` | `dataset.py` | Scenario loader — reads `scenarios.json` seed data, serves via `/api/scenarios` |
| `TraceRecorder` | `trace.py` | Append-only event log — threaded through every layer via `AgentContext` |
| `MCPClient` | `mcp/client.py` | MCP protocol client — multi-transport, tool/resource/prompt discovery |
| `A2ABroker` | `a2a/broker.py` | A2A task router — in-process registry, lifecycle state machine, retry logic |

New work extends this structure. Nothing needs to be restructured; all four questions below describe how to add into existing extension points.

---

## Recommended Architecture for New Scenarios

### Pattern: Scenario as a First-Class Trace Shape

Each new scenario is not just a different ticket. It is a **protocol depth profile** — a recipe for which trace events must fire and in what order for the scenario to be educationally valid. This distinction matters for design:

- Scenarios are defined in `scenarios.json` (loaded by `DemoRepository`)
- `DemoPlatform` dispatches by `mode`, not by scenario — the scenario provides the ticket; the mode provides the execution path
- New scenarios should be designed so their complexity *only becomes visible through the trace* — the UI observes traces, not scenario definitions

**Implication for new scenarios:** Each new scenario should document its "expected trace shape" — the ordered sequence of trace event types that prove the protocol depth is being exercised. This is the validation contract between `DemoRepository` and `DemoPlatform`.

---

## Component Boundaries

### What Talks to What

```
                      ┌─────────────────────────────────────────┐
                      │            web.py (FastAPI)             │
                      │  POST /api/run   GET /api/scenarios      │
                      └────────────────┬────────────────────────┘
                                       │
                                       ▼
                      ┌─────────────────────────────────────────┐
                      │           DemoPlatform                  │
                      │  _run_mcp()  _run_a2a()  _run_hybrid()  │
                      └──┬───────────────┬────────────────┬─────┘
                         │               │                │
              ┌──────────▼──┐    ┌───────▼───────┐  ┌────▼──────────┐
              │  MCPClient  │    │   A2ABroker    │  │ TraceRecorder │
              │ (tool calls)│    │ (task routing) │  │ (all events)  │
              └──────┬──────┘    └───────┬────────┘  └───────────────┘
                     │                   │
              ┌──────▼──────┐    ┌───────▼────────┐
              │  MCP Servers│    │ Specialist      │
              │ db_server   │    │ Agents          │
              │ docs_server │    │ (specialists.py)│
              └─────────────┘    └────────────────┘
```

**Rules that must not be violated:**
1. `TraceRecorder` is write-only from agents/brokers/clients — it never feeds back into execution decisions
2. `DemoRepository` is read-only during a run — scenario data is loaded once at startup
3. `MCPClient` and `A2ABroker` never call each other directly — `DemoPlatform` coordinates them
4. The frontend communicates exclusively through `web.py` — no direct imports of backend modules

---

## Question 1: Multi-Step Workflow Scenarios

### Goal
Show protocol depth: MCP emits a chain of `tool_call` events; A2A emits a chain of `task_submit` → `task_completed` delegations. The difference must be *visible in the trace* without requiring code inspection.

### Recommended Structure

**Scenario design contract in `scenarios.json`:**
```json
{
  "id": "multi_step_warranty_escalation",
  "title": "Warranty Escalation",
  "description": "Customer with expired warranty claims damage — requires lookup, policy check, and billing review",
  "tags": ["multi-step", "chaining"],
  "expected_steps": {
    "mcp": ["tool_discovery", "tool_call:get_customer", "tool_call:get_warranty", "tool_call:search_policy", "tool_call:get_payment_history"],
    "a2a": ["agent_register×3", "task_submit:customer_data", "task_submit:documentation", "task_submit:policy_billing"]
  }
}
```

The `expected_steps` field is documentation, not runtime logic. It communicates intent to developers maintaining the scenario.

**Trace visibility rule:** Every intermediate step must emit its own `TraceRecorder` event. No bundling multiple tool calls into one event. The trace is the product.

**MCP chain execution pattern (in `_run_mcp`):**
```python
# Each call is a discrete trace event — never batch
result_1 = await self._safe_tool_call(client, "get_customer", ...)
result_2 = await self._safe_tool_call(client, "get_warranty", ...)
result_3 = await self._safe_tool_call(client, "search_policy", ...)
# Each _safe_tool_call records tool_call event with step index
```

**A2A chain execution pattern (in `_run_a2a`):**
Sequential delegation through `TriageAgent` already emits the right events. The multi-step scenario just needs a ticket that triggers all three specialist capabilities, ensuring the full `task_submit → task_working → task_completed` lifecycle fires three times.

**Trace event enhancement needed:** Add a `step_index` field to `tool_call` and `task_submit` events so the UI can number the steps: "Step 1 of 4: get_customer". This is a one-line change to `TraceRecorder.record()` call sites.

### Data Flow for Multi-Step Scenarios

```
Ticket arrives → DemoPlatform dispatches by mode
  MCP path:
    MCPClient.discover() → [tool_discovery event]
    for each required capability:
      MCPClient.call(tool) → [tool_call event with step_index]
    SingleSupportAgent.summarize() → [agent_reasoning event]

  A2A path:
    A2ABroker registers 3 agents → [agent_register × 3 events]
    TriageAgent classifies → routes to each needed specialist
    for each specialist:
      broker.send_task() → [task_submit → task_working → task_completed events]
    TriageAgent.merge() → [triage_merge event]
```

---

## Question 2: Parallel Agent Execution in A2A

### Goal
Show A2A's coordination advantage: multiple specialists can work simultaneously. Contrast with MCP's inherently sequential tool call chain.

### Recommended Instrumentation Change

The current `A2ABroker` sends tasks sequentially (one `ThreadPoolExecutor` call per task). For the parallel scenario, tasks should be dispatched concurrently and the trace must capture real start/end timestamps per agent.

**Add `parallel_batch_id` to trace events:**

When a batch of tasks is dispatched in parallel, all constituent `task_submit` events should carry the same `parallel_batch_id` UUID. This single field enables the UI to group them into a swimlane visualization without any other changes.

```python
# In A2ABroker — new parallel dispatch method
import concurrent.futures, uuid

def send_tasks_parallel(self, tasks: list[TaskRequest], trace: TraceRecorder):
    batch_id = str(uuid.uuid4())
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(self._dispatch_one, task, batch_id, trace): task
            for task in tasks
        }
        return [f.result() for f in concurrent.futures.as_completed(futures)]

def _dispatch_one(self, task, batch_id, trace):
    # existing send_task logic, but record events with:
    trace.record("task_submit", ..., parallel_batch_id=batch_id, started_at=time.time())
    result = agent.execute(task)
    trace.record("task_completed", ..., parallel_batch_id=batch_id, completed_at=time.time())
    return result
```

**No new event types needed.** The existing `task_submit` and `task_completed` events gain two fields: `parallel_batch_id` and wall-clock timestamps (`started_at`, `completed_at`). `TraceRecorder` already timestamps every event, but wall-clock floats are needed for duration math.

### UI Display: Swimlane Timeline

The recommended pattern for parallel visualization is a **swimlane (horizontal track) layout**, not a nested tree. Each agent gets one horizontal track. Events within that track are positioned proportionally on a shared timeline axis.

**Component boundary:** This is a new React component — call it `ParallelAgentTimeline.tsx` — located at `frontend/src/components/traces/ParallelAgentTimeline.tsx`. It consumes trace events already returned by the existing API; no new API endpoint is needed.

**Rendering logic:**
1. Filter trace events where `parallel_batch_id` is present
2. Group by `agent_id`
3. Normalize timestamps: `x_offset = (event.started_at - batch_start) / batch_duration`
4. Render each agent as a MUI `Box` row; use `LinearProgress` or a plain `div` with percentage width as the execution bar
5. Overlay `task_submit` / `task_working` / `task_completed` state transitions as color segments on the bar

**MUI implementation:** Use `Box` + `Typography` for swimlane rows, `Chip` components for state labels, and `Tooltip` for raw event payloads on hover. No external charting library needed. MUI's layout primitives are sufficient.

**Data flow for parallel display:**
```
TraceExplorer (existing) detects parallel_batch_id in events
  → renders ParallelAgentTimeline component inline
  → ParallelAgentTimeline groups events by agent_id
  → renders swimlane rows with duration bars
  → each bar click opens existing ProtocolEnvelopeDrawer
```

The `ProtocolEnvelopeDrawer` already exists and shows raw A2A payloads — it can be reused without modification by passing the event reference.

---

## Question 3: Side-by-Side Protocol Trace Visualization

### Goal
Make A2A vs MCP differences unmissable for a non-technical viewer during a live walkthrough.

### Pattern from Observability Ecosystem

The dominant pattern in LLM observability tools (LangSmith, Arize Phoenix) is a **span waterfall tree** — nested, indented rows ordered by start time. This is correct for debugging but wrong for *educational comparison*, because it hides the structural difference between protocols.

**The right pattern for this platform is a columnar diff layout:**

```
┌─────────────────────────┬─────────────────────────┐
│        MCP Path         │        A2A Path          │
│  [tool_discovery]       │  [agent_register: cust]  │
│  [tool_call: customer]  │  [agent_register: docs]  │
│  [tool_call: warranty]  │  [agent_register: policy]│
│  [tool_call: policy]    │  [task_submit: cust]     │
│  [agent_reasoning]      │  [task_working: cust]    │
│                         │  [task_submit: docs]     │
│                         │  [task_working: docs]    │
│                         │  [task_completed: cust]  │
│                         │  [task_completed: docs]  │
│                         │  [triage_merge]          │
└─────────────────────────┴─────────────────────────┘
```

Each column is the filtered trace for one mode from the same scenario run. The viewer immediately sees: MCP is a flat sequence of tool calls; A2A is a registry + delegation graph.

**Component boundary:** `CompareTracesPanel.tsx` — a new component in `frontend/src/components/traces/` that takes two trace arrays (one per mode) and renders them in synchronized, scrollable columns.

**Integration point:** The existing `ComparePage.tsx` (`frontend/src/features/compare/`) is the natural home for this panel. It already exists as a side-by-side mode comparison page. Extend it to include trace columns below the existing metrics comparison.

**Existing `TraceExplorer.tsx` reuse:** `CompareTracesPanel` should NOT duplicate `TraceExplorer` logic. Instead, it should accept a `filterFn` prop that the parent passes to two `TraceExplorer` instances rendered side by side. `TraceExplorer` already supports filtering.

**Synchronized scroll:** Implement with a shared `scrollTop` ref. When one column scrolls, mirror the offset to the other. Use `useRef` + `onScroll` handler — no library needed.

**Color-coded event types:** Assign a consistent color palette to event type families:
- Tool discovery events: blue
- Tool call events: teal
- Agent registration events: purple
- Task lifecycle events (submit/working/completed): orange → yellow → green gradient
- Error events: red

These colors must be defined once in a shared constant (`frontend/src/lib/trace/eventColors.ts`) and consumed by both `TraceExplorer` and `CompareTracesPanel`.

**Data flow for side-by-side comparison:**
```
User runs mode="all" (existing feature)
  → RunResponse contains separate trace arrays per mode
  → ComparePage fetches both trace files
  → CompareTracesPanel renders two TraceExplorer instances
  → User sees structural difference without reading event details
```

---

## Question 4: Tool Discovery Scenario Design

### Goal
Show the architectural distinction between MCP's vertical/pull-based capability announcement and A2A's horizontal/push-based agent card registry. This is the single highest-value educational moment in the platform.

### The Core Difference to Make Visible

**MCP discovery flow:**
1. `MCPClient` connects to a server
2. Server returns its full tool list in response to `list_tools()` — a synchronous pull
3. The client (via the LLM) then decides which tools to call
4. The "capability announcement" is reactive: tools are revealed when the client asks

**A2A discovery flow:**
1. Agents self-register with the broker at startup — a proactive push
2. Each agent publishes an `AgentCard` with skills, accepted data formats, and metadata
3. The triage agent queries the registry to find suitable agents — a lookup by capability
4. The "registry" persists independently of any particular task

**What to make visible:** The `tool_discovery` and `mcp_capability_discovery` trace events already exist for MCP. For A2A, `agent_register` and `capability_advertise` events already fire. The gap is that no UI component presents these two flows as a *named, staged discovery phase* before the task execution phase.

### Recommended Architecture for Discovery Scenario

**New scenario in `scenarios.json`:**
```json
{
  "id": "tool_discovery",
  "title": "Tool Discovery",
  "description": "A simple lookup ticket — complexity is in showing how each protocol discovers what capabilities are available before answering",
  "tags": ["discovery", "capability-announcement"],
  "highlight_phase": "discovery"
}
```

The ticket itself can be the simplest possible (e.g., "What is my order status?") — the educational value is in the *pre-execution discovery phase*, not the answer.

**Trace phase segmentation:** Add a `phase` field to trace events — `"phase": "discovery"` or `"phase": "execution"`. This is a metadata tag; it does not affect execution logic.

For MCP: `tool_discovery` and `mcp_capability_discovery` events get `"phase": "discovery"`. All subsequent `tool_call` events get `"phase": "execution"`.

For A2A: `agent_register` and `capability_advertise` events get `"phase": "discovery"`. All `task_submit` and subsequent events get `"phase": "execution"`.

**UI component:** `DiscoveryPhasePanel.tsx` — renders the discovery phase events for MCP and A2A side by side in a condensed "before you start" view. Shows:
- MCP column: the list of tools announced by the server (extracted from `mcp_capability_discovery` event payload)
- A2A column: the agent cards registered (extracted from `capability_advertise` event payloads)

This component reads from the existing trace data. No new API endpoints needed.

**Agent card display:** The `capability_advertise` events already carry A2A 1.0-shaped payloads (built by `a2a/protocol.py`'s `agent_card_payload()`). Render these as MUI `Card` components with the agent name, skills list, and accepted input formats. This is purely a frontend rendering concern — the backend data is already there.

**MCP tools display:** The `mcp_capability_discovery` event payload contains the tool list returned by `MCPClient` after `list_tools()`. Render as a similar MUI `Card` list with tool name and description. The visual symmetry of two `Card` lists (one per protocol) makes the registry vs. announcement distinction immediately legible.

---

## Suggested Build Order

Dependencies flow in this order. Build lower-numbered items before higher-numbered ones.

### 1. Backend: Trace event enrichment (no new endpoints)
**Files:** `platform.py`, `a2a/broker.py`, `trace.py`
**Changes:**
- Add `step_index` to `tool_call` and `task_submit` events
- Add `parallel_batch_id`, `started_at`, `completed_at` to parallel task events
- Add `phase` field (`"discovery"` or `"execution"`) to all existing event types
**Why first:** Every frontend component depends on these fields. These are additive fields — they cannot break existing trace consumers.

### 2. Backend: New scenarios in `scenarios.json`
**Files:** `data/seeds/scenarios.json`
**Changes:**
- Add `multi_step_warranty_escalation` scenario
- Add `parallel_agents` scenario
- Add `tool_discovery` scenario
**Why second:** Scenarios load at startup. Frontend can immediately select them. No platform.py changes needed until the parallel dispatch method is added.

### 3. Backend: Parallel dispatch in `A2ABroker`
**Files:** `a2a/broker.py`, `platform.py` (new `_run_a2a_parallel()` method or flag)
**Changes:**
- Add `send_tasks_parallel()` to `A2ABroker`
- Add `parallel=True` flag to `DemoPlatform._run_a2a()` or a new `_run_a2a_parallel()` method
**Why third:** Depends on trace enrichment (step 1) for `parallel_batch_id` events to be useful.

### 4. Frontend: Shared trace color constants
**Files:** `frontend/src/lib/trace/eventColors.ts` (new file)
**Changes:** Define event type → color mapping used by all trace components
**Why fourth:** All new trace components depend on this. Define it once before building any visual component.

### 5. Frontend: `ParallelAgentTimeline.tsx`
**Files:** `frontend/src/components/traces/ParallelAgentTimeline.tsx` (new)
**Changes:** Swimlane timeline rendering for parallel batch events
**Why fifth:** Depends on `parallel_batch_id` events (step 1, 3) and color constants (step 4).

### 6. Frontend: `CompareTracesPanel.tsx`
**Files:** `frontend/src/components/traces/CompareTracesPanel.tsx` (new)
**Changes:** Two-column synchronized `TraceExplorer` instances
**Why sixth:** Depends on color constants (step 4). Integrates into existing `ComparePage.tsx`.

### 7. Frontend: `DiscoveryPhasePanel.tsx`
**Files:** `frontend/src/components/traces/DiscoveryPhasePanel.tsx` (new)
**Changes:** Two-column agent card / tool list display from discovery-phase events
**Why seventh:** Depends on `phase` field in events (step 1) and color constants (step 4).

### 8. Integration: Wire new components into existing pages
**Files:** `ComparePage.tsx`, `TraceWorkspacePage.tsx`, `RunWorkspacePage.tsx`
**Changes:** Add `ParallelAgentTimeline` to trace view when parallel events detected; add `CompareTracesPanel` to compare page; add `DiscoveryPhasePanel` to run workspace for discovery scenario
**Why last:** Depends on all components being built and tested in isolation first.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: New API endpoints for trace visualization
**What goes wrong:** Adding `GET /api/traces/parallel` or `GET /api/traces/discovery-phase` creates parallel data paths that drift out of sync with the main trace format.
**Instead:** All visualization components read from the existing trace event arrays returned by `GET /api/runs/{id}` and `GET /api/traces/{task_id}`. Add fields to existing events; do not create new endpoint shapes.

### Anti-Pattern 2: Baking scenario logic into `DemoPlatform`
**What goes wrong:** Special-casing `if scenario_id == "parallel_agents": ...` inside `_run_a2a()` makes platform.py a growing switch statement.
**Instead:** Scenarios control the ticket content and tags. `DemoPlatform` dispatches by mode only. A `parallel=True` flag on the run request (or a scenario tag read at dispatch time) is the maximum coupling allowed.

### Anti-Pattern 3: Duplicating `TraceExplorer` logic
**What goes wrong:** Building `CompareTracesPanel` with its own event rendering creates two implementations that diverge.
**Instead:** `CompareTracesPanel` renders two `TraceExplorer` instances with a `filterFn` prop. All event rendering logic lives in one place.

### Anti-Pattern 4: Wall-clock timestamps in mock mode
**What goes wrong:** Parallel timing visualization requires real duration data, but mock mode executes synchronously and all timestamps collapse to the same millisecond.
**Instead:** In mock mode, inject synthetic `started_at` / `completed_at` offsets per agent (e.g., agent 1: +0ms, agent 2: +50ms, agent 3: +100ms) to produce a realistic-looking timeline. Document this as mock behavior in the event payload.

### Anti-Pattern 5: Protocol-specific React components
**What goes wrong:** `MCPToolCard.tsx` and `A2AAgentCard.tsx` as separate components create asymmetry in the comparison UI and double the maintenance surface.
**Instead:** `CapabilityCard.tsx` — a single component that accepts a normalized shape with `name`, `description`, `capabilities: string[]`, `protocol: "mcp" | "a2a"`, and applies protocol-specific color theming via `eventColors.ts`.

---

## Scalability Considerations

This is a single-presenter demo tool. Scalability concerns are limited to demo day reliability.

| Concern | At demo scale (1 user) | Risk |
|---------|------------------------|------|
| Trace file size | Multi-step scenario adds ~20-40 events per run | Negligible — JSON files under 50KB |
| Parallel thread execution | 3 concurrent agents in `ThreadPoolExecutor` | No risk — all in-process, mock runtime |
| Frontend render performance | 3 swimlane rows × ~10 events each | Negligible — no virtualization needed |
| Mock timing injection | Synthetic offsets in `TraceRecorder` | Low — clearly documented as mock behavior |

---

## Sources

- Existing codebase: `src/a2a_vs_mcp/platform.py`, `a2a/broker.py`, `trace.py`, `a2a/protocol.py` — HIGH confidence (direct analysis)
- Parallel agent instrumentation patterns: [Augment Code — Debug Parallel AI Agents](https://www.augmentcode.com/guides/debug-parallel-ai-agents) — MEDIUM confidence
- Google ADK parallel agent model: [ADK Parallel Agents](https://adk.dev/agents/workflow-agents/parallel-agents/) — MEDIUM confidence
- MCP vs A2A discovery mechanisms: [Clarifai MCP vs A2A](https://www.clarifai.com/blog/mcp-vs-a2a-clearly-explained) — MEDIUM confidence (corroborated by multiple sources)
- LangSmith span waterfall patterns: [Advanced LangSmith Tracing 2025](https://sparkco.ai/blog/advanced-langsmith-tracing-techniques-in-2025) — MEDIUM confidence
- A2A agent card spec: [Agent-to-Agent Protocol announcement, April 2025](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/) — HIGH confidence (official)

---

_Architecture analysis: 2026-04-22_
