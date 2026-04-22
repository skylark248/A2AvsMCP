# Roadmap: A2A vs MCP Demo Platform

## Overview

This milestone deepens the demo platform from a working prototype into a polished, demo-day-ready comparison tool. Starting with a stability foundation (all four modes run flawlessly without an API key), the work progresses through backend trace enrichment, new protocol-depth scenarios, a comparison-clarity UI overhaul, and finally presentation polish. Each phase delivers a coherent, independently testable increment — a presenter can stop after any phase and have a more capable demo than before.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Demo Stability Foundation** - All four modes run reliably without an API key; test harness in place
- [ ] **Phase 2: Backend Trace Enrichment** - Trace events carry the data contract all frontend components require
- [ ] **Phase 3: New Scenarios** - Multi-step and parallel-agent scenarios expose protocol depth visibly
- [ ] **Phase 4: Comparison UI** - Side-by-side visualization makes protocol differences unmissable at a glance
- [ ] **Phase 5: Presentation Polish** - Talking-point cards, glossary popovers, and failure-mode walkthrough complete demo day readiness

## Phase Details

### Phase 1: Demo Stability Foundation
**Goal**: All four demo modes run without crashes using mock runtime, the test suite is trustworthy, and dependency versions are pinned for the milestone
**Depends on**: Nothing (first phase)
**Requirements**: STAB-01, STAB-02, STAB-03, STAB-04, STAB-05
**Success Criteria** (what must be TRUE):
  1. Running baseline, mcp, a2a, and hybrid modes with `runtime=mock, transport=in_process` completes without any crash or error
  2. The run header always shows a visible transport mode badge so the presenter can confirm what transport is active
  3. `pyproject.toml` pins `mcp>=1.27,<2` and `a2a-sdk==0.3.26`; `pip install` succeeds cleanly
  4. `pytest` suite passes including at least one async FastAPI integration test that exercises the MCP mode end-to-end without an API key
  5. `FakeReasoningEngine` exists so the LLM code path can be exercised in tests without `OPENAI_API_KEY`
**Plans**: 2 plans
Plans:
- [x] 01-PLAN-01.md — Backend: dependency pins, FakeReasoningEngine, mcp_transport schema field, pytest migration + conftest, async integration tests
- [x] 01-PLAN-02.md — Frontend: mcp_transport in RunResult TS interface + transport badge Chip in run header row

### Phase 2: Backend Trace Enrichment
**Goal**: All trace events carry the enriched fields (`step_index`, `parallel_batch_id`, timing offsets, `phase`) that downstream UI components depend on, and the broker supports parallel task dispatch
**Depends on**: Phase 1
**Requirements**: TRACE-01, TRACE-02, TRACE-03, TRACE-04, TRACE-05
**Success Criteria** (what must be TRUE):
  1. Every `tool_call` and `task_submit` trace event includes a `step_index` field
  2. Parallel task events carry `parallel_batch_id`, `started_at`, and `completed_at`; mock mode injects deterministic synthetic timing offsets
  3. All trace event types include a `phase` field with value `"discovery"` or `"execution"`
  4. `A2ABroker` has a working `send_tasks_parallel()` method and `timeout_ms` is raised to 5000ms for parallel scenarios
  5. The trace view renders in three tiers — summary strip, protocol-level, full trace — with A2A sub-events collapsible and a 150-event soft render cap
**Plans**: TBD

### Phase 3: New Scenarios
**Goal**: The multi-step workflow and parallel-agent scenarios are runnable from the UI, producing rich traces that make protocol depth immediately visible
**Depends on**: Phase 2
**Requirements**: SCEN-01, SCEN-02, SCEN-03
**Success Criteria** (what must be TRUE):
  1. The multi-step workflow scenario runs all four modes and produces a trace showing 3+ chained tool calls (MCP) or agent handoffs (A2A)
  2. The parallel-agent scenario trace shows overlapping execution timestamps for A2A specialists vs sequential execution for MCP
  3. Both new scenarios display a talking-point card (8-word headline, one sentence, one callout) in the run UI
  4. The parallel scenario produces zero `task_failed` events under mock runtime
**Plans**: TBD

### Phase 4: Comparison UI
**Goal**: The comparison UI exposes protocol differences as first-class visual elements — outcome metrics, swimlane timelines, and side-by-side trace panels — without requiring the viewer to read raw trace JSON
**Depends on**: Phase 3
**Requirements**: UI-01, UI-02, UI-03, UI-04, UI-05
**Success Criteria** (what must be TRUE):
  1. The result card displays elapsed time, round-trip count, and agent count as visible metrics without opening the trace panel
  2. A swimlane timeline (`ParallelAgentTimeline`) renders parallel A2A agent execution from `parallel_batch_id` events
  3. A side-by-side panel (`CompareTracesPanel`) shows two synchronized trace explorer instances so a viewer can compare modes directly
  4. All trace components use `eventColors.ts` as a single source of truth — no hardcoded color values elsewhere
  5. Frontend dependencies (`@xyflow/react`, `recharts`, `react-syntax-highlighter`, `motion`) are installed and the app still builds
**UI hint**: yes
**Plans**: TBD

### Phase 5: Presentation Polish
**Goal**: The demo is ready for a mixed audience — talking-point cards guide narration, glossary popovers remove jargon friction, the real-LLM path is clearly surfaced, and failure modes are selectable for a deeper technical walkthrough
**Depends on**: Phase 4
**Requirements**: PRES-01, PRES-02, PRES-03, PRES-04
**Success Criteria** (what must be TRUE):
  1. All modes and new scenarios show talking-point cards; every protocol label uses role-first phrasing ("Tool Access Protocol (MCP)", "Agent Coordination Protocol (A2A)") on first use
  2. Hovering any protocol term in the UI shows a one-sentence glossary popover definition
  3. The real-LLM toggle is visually prominent and the trace explorer shows a latency expectation badge when OpenAI runtime is active
  4. `FailureConfig` failure paths are selectable in the UI and their outcomes appear visibly in the trace, enabling a failure-mode walkthrough without code changes
**UI hint**: yes
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Demo Stability Foundation | 0/2 | Not started | - |
| 2. Backend Trace Enrichment | 0/TBD | Not started | - |
| 3. New Scenarios | 0/TBD | Not started | - |
| 4. Comparison UI | 0/TBD | Not started | - |
| 5. Presentation Polish | 0/TBD | Not started | - |
