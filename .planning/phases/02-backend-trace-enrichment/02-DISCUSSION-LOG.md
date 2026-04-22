# Phase 2: Backend Trace Enrichment - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 02-backend-trace-enrichment
**Areas discussed:** step_index counting scope, Phase tagging logic, Trace tier UI

---

## step_index counting scope

| Option | Description | Selected |
|--------|-------------|----------|
| Per-run global sequence | Counter increments across all tool_call and task_submit in the entire run | ✓ |
| Per-agent sequence | Resets to 1 for each agent | |
| Per-mode phase sequence | Resets at discovery/execution boundary | |

**User's choice:** Per-run global sequence
**Notes:** Easiest for the timeline to sort by; unambiguous ordering across all agents.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Only tool_call + task_submit | Exactly what TRACE-01 specifies — action events at protocol boundaries | ✓ |
| All events get step_index | Every event indexed — redundant with existing `index` field | |
| All 'action' events | Broader set including tool_error, a2a_message subtypes | |

**User's choice:** Only tool_call + task_submit

---

## Phase tagging logic

| Option | Description | Selected |
|--------|-------------|----------|
| Fixed event-type map | Hardcoded mapping in trace.py, applied in TraceRecorder.record() | ✓ |
| Broker/client state flag | Stateful current_phase attribute on each subsystem | |
| Caller annotates explicitly | Every trace.record() call site passes phase= | |

**User's choice:** Fixed event-type map
**Notes:** Zero changes to call sites; single place to maintain.

---

| Option | Description | Selected |
|--------|-------------|----------|
| In TraceRecorder.record() | Private constant in trace.py; auto-applied to every event | ✓ |
| In a2a/protocol.py or mcp/client.py | Distributed per-subsystem | |
| Post-processing in platform.py | Injected after run completes | |

**User's choice:** In TraceRecorder.record()

---

## Trace tier UI (TRACE-05)

| Option | Description | Selected |
|--------|-------------|----------|
| Metric counts + protocol | Total events, tool_call count, A2A count, phase breakdown | ✓ |
| Timeline bar only | Compressed horizontal density bar | |
| Outcome headline | Mode + status + latency one-liner | |

**User's choice:** Metric counts + protocol (summary strip)

---

| Option | Description | Selected |
|--------|-------------|----------|
| Accordion / expand-in-place | Summary always visible; protocol and full tiers expand below | ✓ |
| Tabs | Three tabs replacing content | |
| Segmented toggle buttons | Button group controls single panel | |

**User's choice:** Accordion / expand-in-place

---

| Option | Description | Selected |
|--------|-------------|----------|
| Group by task_id, collapsed by default | Parent row per task; expand to see lifecycle | ✓ |
| Group by message_type category | Group registration/lifecycle/artifact events | |
| All sub-events visible, no grouping | Every A2A event as individual row | |

**User's choice:** Group by task_id, collapsed by default
**Notes:** Keeps protocol-level tier to ~3 rows for A2A mode instead of 18-24 rows.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Show warning banner, truncate to 150 | Render 150, banner with "Showing X of N" | ✓ |
| Virtual scroll, no cap | All events with virtualised list | |
| Paginate at 150 | Load more button | |

**User's choice:** Show warning banner, truncate to 150

---

## Claude's Discretion

- Exact synthetic timing offset values for parallel mock dispatch
- `parallel_batch_id` generation method (uuid4 vs incrementing token)
- `conftest.py` additions for Phase 2 test fixtures

## Deferred Ideas

- Virtual scroll for large traces — defer until Phase 3 scenarios prove the need
- DiscoveryPhasePanel for discovery-phase events — v2 backlog (DISC-02)
- Scenario-config-driven synthetic timing — overkill for Phase 2
