---
status: partial
phase: 11-tool-discovery-scenario
source: [11-VERIFICATION.md]
started: 2026-05-01T10:58:00.000Z
updated: 2026-05-01T10:58:00.000Z
---

## Current Test

[awaiting human testing]

## Tests

### 1. A2A protocol live run of tool_discovery scenario
expected: Running TICKET-1013 in a2a mode emits at least one `tool_discovery` event AND at least one `a2a_remote_discovery` event; A2A column of DiscoveryPhasePanel populates with agent-card chips joined to remote_agent.
result: [pending]

### 2. Discovery-before-execution visual ordering
expected: When viewing TraceWorkspacePage for the tool_discovery scenario, the DiscoveryPhasePanel appears above the existing TraceExplorer Grid block, and discovery events visually precede any execution-phase events (per ROADMAP success criterion #2 "before any execution-phase events").
result: [pending]

### 3. D-72 single full-width panel layout in Compare mode
expected: When viewing CompareTracesPanel for two runs of the tool_discovery scenario, exactly ONE DiscoveryPhasePanel renders full-width above the dual-column TraceExplorer Grid (NOT one panel per column). Presence-gate confirms no panel renders for non-discovery scenarios.
result: [pending]

### 4. Stale-cache warning UX clarity
expected: When the unknown SKU "NebulaSync Hub" forces fallback, the affected tool card renders a 2px left warning border + WarningAmberRoundedIcon with a tooltip that reads clearly to a demo operator (D-68 / RESEARCH Pitfall #2 — reuses existing tool_transport_fallback event).
result: [pending]

## Summary

total: 4
passed: 0
issues: 0
pending: 4
skipped: 0
blocked: 0

## Gaps
