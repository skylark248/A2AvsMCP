# Domain Pitfalls

**Domain:** Educational protocol comparison demo platform (MCP vs A2A, mixed live audience)
**Researched:** 2026-04-22
**Codebase anchor:** `d:/A2A vs MCP/` — Python/FastAPI + React/MUI, four demo modes, mock runtime

---

## Critical Pitfalls

Mistakes in this category cause demo failure, audience confusion, or code rewrites.

---

### Pitfall C1: The "Same Ticket, Invisible Difference" Trap

**What goes wrong:** All four modes process the same customer support ticket and produce the same correct answer. Non-technical viewers watch the UI cycle through four runs and conclude: "These are all doing the same thing — why does the protocol choice matter?" The structural differences (tool calls vs task delegation) are buried inside the trace panel, which non-technical viewers never open.

**Why it happens:** The platform was designed for correctness parity across modes — a valid technical goal — but the demo scenario never made the *cost* of that parity visible. MCP's sequential `tool_call` chain and A2A's parallel specialist dispatch both resolve the ticket; nothing forces the audience to see that A2A did it differently at the coordination level.

**Consequences:** The entire point of the comparison is lost for the decision-maker half of the audience. Engineers see the trace; executives see "four identical results." Comparison clarity improvements (active requirement) fail to land.

**Prevention:**
- Design the new multi-step and parallel scenarios so the difference is visible *in the outcome surface*, not only in the trace. Concretely: show elapsed time, number of round-trips, or number of agents involved as first-class UI metrics on the result card — not buried in a collapsible panel.
- The parallel agent scenario is the highest-leverage fix: if A2A runs three specialists simultaneously and MCP runs three tool calls sequentially, a wall-clock timer on the result card makes the difference self-evident without any trace reading.
- Talking-point cards (active requirement) must call out the mechanism difference explicitly: "MCP called 3 tools in sequence. A2A dispatched 3 agents in parallel." — surfaced on the result, not only on a slide.

**Warning signs:** A presenter rehearsing the demo says "so here you can see... they all give the same answer." That sentence is the failure signal.

**Phase:** Comparison clarity improvements phase. Address before any other UI work.

---

### Pitfall C2: Transport Fallback Silently Undermines the Demo Narrative

**What goes wrong:** `MCPClient.__init__` catches any exception from `http` or `stdio` transport startup and silently falls back to `in_process`, recording a `tool_transport_fallback` trace event. During the demo, the presenter says "and here MCP is communicating over HTTP" while the system is actually running in-process. The trace shows `transport: "in_process"` and `requested_transport: "http"` — invisible to anyone not reading it.

**Why it happens:** The fallback is intentional and correct for development resilience. The problem is that `demo` profile uses `http` transport (per `config.py` profile definitions), and if the subprocess-spawned HTTP server fails to start (port conflict, Windows path issue, slow startup), the fallback fires with no UI indication.

**Consequences:** The transport comparison in the tool discovery scenario becomes a lie. A technically curious engineer in the audience checks the trace, sees `in_process`, and loses trust in the whole demo.

**Prevention:**
- In the demo stability pass phase: add a startup health check that verifies HTTP server readiness before the run begins (not just catching the exception mid-init). Surface transport status in the UI run header (a small "MCP transport: HTTP" badge is enough).
- If HTTP server startup fails, surface a visible warning to the presenter (toast or status bar), not a silent fallback.
- For demo day: use `runtime=mock, transport=in_process` as the locked-in profile. Only demonstrate transport variety as an explicit opt-in, not default.

**Warning signs:** The trace shows `tool_transport_fallback` events. The UI shows no indication of transport mode. The `demo` profile is being used without subprocess startup validation.

**Phase:** Demo stability pass. Also relevant to transport comparison scenario design.

---

### Pitfall C3: `anyio.run()` Called from Inside FastAPI's Running Event Loop

**What goes wrong:** `MCPClient.call()` uses `anyio.run(self._call_once_stdio, ...)` and `anyio.run(self._call_once_http, ...)` for stdio and HTTP transports. FastAPI runs on an async event loop (via uvicorn). Calling `anyio.run()` — which creates a *new* event loop — from within a thread that is already inside a running event loop causes a `RuntimeError: This event loop is already running` on some platforms/configurations, or deadlock when the thread pool and the event loop interact.

**Why it happens:** The `in_process` transport is used in tests and dev, which avoids this. The `http` and `stdio` paths are exercised less frequently (per TESTING.md: "only `in_process` exercised in tests"). The bug is dormant in dev but can surface under the `demo` profile with HTTP transport, which is exactly the profile used on demo day.

**Consequences:** The demo crashes or hangs mid-run when HTTP or stdio transport is active. This is a demo-day-killing failure with no graceful recovery path.

**Prevention:**
- For new parallel scenarios: all MCP tool calls must go through `in_process` transport or be wrapped in `asyncio.to_thread()` / a dedicated thread pool that owns its own event loop lifecycle, not raw `anyio.run()` from a FastAPI handler thread.
- In the demo stability pass: add an explicit integration test that runs `mcp` mode with `transport=http` through the FastAPI `TestClient` (which exercises the real request path, not just `DemoPlatform` directly).
- The safest demo-day posture is `transport=in_process` locked in the mock profile.

**Warning signs:** `RuntimeError: This event loop is already running` in server logs. Test coverage of `http`/`stdio` transport is zero (confirmed in TESTING.md).

**Phase:** Demo stability pass (detect and fix). New scenario implementation (avoid introducing the pattern again).

---

### Pitfall C4: Trace Volume Explosion in Multi-Step and Parallel Scenarios

**What goes wrong:** `TraceRecorder` is an append-only in-memory list saved as a single JSON file. The existing single-ticket scenario produces ~15–25 events per mode. A multi-step scenario (3+ chained tool calls or agent handoffs) and a parallel agent scenario (3 concurrent A2A specialists, each emitting `agent_register`, `capability_advertise`, `task_submit`, `task_queued`, `task_accept`, `task_working`, `task_progress`, `task_completed`, `task_result`) will produce 60–120+ events per mode. The trace explorer UI will render an undifferentiated wall of JSON rows.

**Why it happens:** The trace system was designed for the current single-scenario depth. No pagination, grouping, filtering, or truncation exists (confirmed in CONCERNS.md). The frontend trace explorer has no progressive disclosure mechanism for large traces.

**Consequences:** The educational value of the trace — the thing that makes protocol differences *visible* — disappears under volume. Non-technical viewers are lost immediately. Technical viewers have to scroll through noise to find the signal. The trace becomes a liability rather than an asset.

**Prevention:**
- Before building new scenarios, define trace *view tiers*: (1) summary strip (event count, latency, agent/tool names), (2) protocol-level view (only `tool_call`, `task_submit`, `task_completed` events), (3) full trace (current behavior). The new scenarios must be designed with view tier 2 as the demo-facing view.
- Group A2A task lifecycle events (`task_queued → task_accept → task_working → task_progress → task_completed`) into a single collapsible "task" row in the UI. Each row should expand to show the sub-events, not list them all at root level.
- Set a soft trace rendering cap (e.g., 150 events max rendered) with a "show full trace" escape hatch. This prevents UI jank during live presentation.

**Warning signs:** A new scenario run produces more than 40 events in the trace panel. The frontend slows down noticeably while rendering the trace.

**Phase:** Architecture decision needed before new scenario implementation. Trace UI work belongs in the comparison clarity phase.

---

## Moderate Pitfalls

Mistakes in this category degrade the demo quality or create maintenance burden, but do not cause outright failure.

---

### Pitfall M1: False Equivalence in the Comparison Scenario Design

**What goes wrong:** The comparison scenario is designed to show A2A as "better than" MCP rather than "complementary to and different from" MCP. This is structurally dishonest and sophisticated viewers — the engineers in the room — will call it out. Alternatively, the scenario picks a problem that genuinely fits both protocols equally well, making the comparison feel arbitrary.

**Why it happens:** It is tempting to design the parallel scenario to make A2A win on wall-clock time (it will) and use that as the primary narrative. But MCP's sequential tool-call model is not a flaw — it is the correct model for single-agent tool grounding. A2A's task delegation model is correct for multi-agent coordination. Designing the scenario to favor one is a false equivalence in reverse.

**Prevention:**
- Each new scenario must have a clear *fit statement*: "This scenario fits A2A because [multi-party coordination requirement]. MCP in this scenario is a deliberate mismatch to show where it strains." The talking-point card for that scenario must say this explicitly.
- The tool discovery scenario is the right place to show MCP at its best (clean server-announces-capabilities model). The parallel agent scenario is the right place to show A2A at its best. Do not use the same scenario for both claims.
- Use the hybrid mode as the "correct answer" narrative: MCP for tool access, A2A for agent coordination — they are not competitors.

**Warning signs:** A presenter script that says "A2A is better because..." without a corresponding "MCP is better when...". Scenario design docs that only describe the A2A advantage.

**Phase:** New scenario design (before implementation). Slide-companion content creation.

---

### Pitfall M2: Talking-Point Cards That Compete With the Live Trace

**What goes wrong:** Talking-point cards are embedded in the UI per mode (active requirement). If these cards contain more than 2–3 sentences, or if they appear in the same visual zone as the trace output, the presenter's audience splits attention between the card text, the trace panel, and the presenter's speech. For non-technical viewers, text-heavy cards become a reading task that pulls them away from listening.

**Why it happens:** The instinct when writing talking-point cards is to be comprehensive — to explain the protocol, the tradeoff, and the recommendation in one panel. This is the slide-deck authoring instinct applied to a UI widget, and it produces walls of text that viewers read instead of listening.

**Prevention:**
- Each talking-point card must have a strict budget: one headline (8 words max), one sentence of context, and one "why it matters" callout. No more.
- Cards must be visually subordinate to the trace/result output — sidebar or footer placement, never overlaid on the primary content area.
- Draft the card text from the presenter script outward: what would the presenter say out loud at this moment? The card reinforces that sentence; it does not replace it.

**Warning signs:** A talking-point card draft that requires scrolling to read. Card text that is a paragraph rather than a bullet. Cards placed above or overlaid on the trace panel.

**Phase:** Slide-companion content implementation.

---

### Pitfall M3: OpenAI Runtime Path Left Untested Until Demo Day

**What goes wrong:** The `reasoning.py` OpenAI integration has no mock and no test coverage (confirmed in CONCERNS.md and TESTING.md). The "Real LLM visibility" requirement (active) calls for making the OpenAI path easy to activate and clearly surfaced. If the first time this path is exercised in the demo environment is during the actual presentation, any API key expiry, rate limit, latency spike, or prompt format regression will fail live.

**Why it happens:** The mock runtime is the safe default and correctly so. The LLM path requires a real API key, making it naturally excluded from automated tests. This exclusion compounds: the longer it goes untested, the higher the chance of silent drift between what the demo expects and what the OpenAI API returns.

**Consequences:** A "watch real AI think through this" moment fails live. The presenter has to explain that the demo is "in mock mode for reliability" — which undercuts the whole "Real LLM visibility" feature value.

**Prevention:**
- Add a `FakeReasoningEngine` (recommended in CONCERNS.md) that returns canned but realistic-looking responses. This enables CI coverage of the LLM path's request/response shape without a real API key.
- Run a live smoke test of the OpenAI path at least one week before demo day, capturing the actual trace output. Lock the prompts and expected event structure after that smoke test so regressions are detectable.
- The UI toggle for OpenAI mode should show latency expectations to the presenter ("LLM mode: ~3–8s per agent call") so they can pace the walkthrough.

**Warning signs:** No test in `tests/` touches `reasoning.py`. The `llm` profile has never been run against the new multi-step scenarios. `OPENAI_API_KEY` is only set in one person's local environment.

**Phase:** Demo stability pass (FakeReasoningEngine). Real LLM visibility feature work.

---

### Pitfall M4: Non-Technical Audience Anchors on Protocol Names, Not Concepts

**What goes wrong:** Presenters introduce "MCP" and "A2A" as the primary labels before the audience understands what problem each solves. Non-technical viewers hear two acronyms and spend cognitive energy trying to remember which is which, rather than understanding the conceptual difference (tool access vs agent delegation). Every subsequent explanation that uses these names without re-anchoring the concept loses them further.

**Why it happens:** The protocol names are technically correct labels and the natural vocabulary for engineers. Slides and UI labels were designed by engineers for engineers.

**Consequences:** At Q&A, non-technical viewers ask "so which one should we use?" rather than "so for our [specific use case], which model fits?" — indicating they retained the name comparison but not the conceptual framework.

**Prevention:**
- Every UI label and talking-point card for a non-technical mode must lead with the role, not the acronym. "Tool Access Protocol (MCP)" and "Agent Coordination Protocol (A2A)" the first time each appears.
- The learning page already exists — the demo walkthrough should reference it explicitly as "for deeper explanation, the Learning tab has this." This offloads the explanation burden from the live demo.
- The baseline mode is the most underused educational asset: "here is the AI with no protocols" makes MCP's contribution immediately visible by contrast. Ensure the comparison UI always shows baseline alongside protocol modes.

**Warning signs:** UI mode labels are "MCP" and "A2A" with no subtitle. The presenter script does not include a one-sentence plain-English role description for each protocol before the first demo run. Non-technical pilot audience members cannot explain the difference after a rehearsal.

**Phase:** Comparison clarity improvements. Slide-companion content.

---

### Pitfall M5: `A2ABroker` Timeout Too Short for Parallel Scenario Under Load

**What goes wrong:** `A2ABroker` initializes with `timeout_ms=1500` (1.5 seconds per task). The broker uses `ThreadPoolExecutor` with that timeout. In the current single-scenario, three sequential specialist calls each have 1.5s — sufficient for mock execution. A new parallel scenario that dispatches multiple agents concurrently via `concurrent.futures` or `asyncio.gather` may hit the timeout if the thread pool queue backs up, even though the mock handlers complete instantly — because thread scheduling overhead under load can consume the timeout budget.

**Why it happens:** 1.5s was tuned for the current single-ticket sequential flow with mock runtime. Parallel dispatch changes the concurrency model and the thread pool contention profile.

**Consequences:** Parallel demo scenario intermittently times out on broker tasks, recording `task_failed` and `task_retry` events — which would look like A2A is unreliable, directly undermining the demo narrative.

**Prevention:**
- For parallel scenarios, either increase `timeout_ms` (e.g., 5000ms for mock) or move parallel dispatch to `asyncio.gather` (native async) rather than `ThreadPoolExecutor` so timeouts are wall-clock rather than per-thread-scheduler.
- Add a dedicated test for the parallel scenario that asserts no `task_failed` events appear in the trace under mock runtime.
- Expose `timeout_ms` in the broker constructor call in `platform.py` so it can be tuned per scenario without changing the broker default.

**Warning signs:** Parallel scenario traces contain `task_failed` or `task_retry` events when run against mock runtime. Demo runs occasionally succeed but sometimes fail without code changes.

**Phase:** New parallel agent scenario implementation.

---

## Minor Pitfalls

Mistakes in this category create friction or minor confusion but are recoverable during the demo.

---

### Pitfall m1: Hardcoded Port Defaults Cause Silent Conflict on Demo Machine

**What goes wrong:** `a2a/registry.py` and `mcp/client.py` hardcode `127.0.0.1` port defaults (91xx range, flagged in CONCERNS.md). On the presenter's machine, another process (another dev server, a prior run that didn't clean up, Docker) may occupy those ports. The MCP HTTP server subprocess fails to bind; the fallback fires silently (see C2 above); the demo proceeds on `in_process` transport without the presenter knowing.

**Prevention:** Extract all port defaults to a single `_defaults.py` constant (already recommended in CONCERNS.md). Add a port availability check at server startup and surface conflicts as a visible warning before the run begins, not a mid-run exception.

**Warning signs:** `tool_transport_fallback` events in the trace. MCP subprocess logs (captured to a tempfile in `client.py`) show "address already in use."

**Phase:** Demo stability pass.

---

### Pitfall m2: "Mode: all" Run Intermixes Trace Events Across Modes

**What goes wrong:** `mode=all` runs all four modes in sequence via a single API call. Each mode creates its own `TraceRecorder` instance. If the UI presents all four traces in a combined view without clear mode-labeling on every event row, a viewer looking at the combined trace cannot tell which events belong to which protocol. This is particularly confusing for the A2A events (which have many sub-events per task) mixed with MCP tool calls.

**Prevention:** The trace explorer must make `mode` a first-class filter, not a secondary label. For comparison demos, default to side-by-side mode view rather than combined view. Each trace event row must include the mode badge.

**Warning signs:** The trace UI shows events from multiple modes in a single flat list without a mode column. A user running `mode=all` cannot filter to see only A2A events.

**Phase:** Comparison clarity improvements.

---

### Pitfall m3: Scenario JSON Drift Between Backend and Frontend Display

**What goes wrong:** New scenarios are added as `DemoRepository` entries (JSON/dataclass). The frontend scenario selector and any scenario-specific talking-point cards must be kept in sync with the backend registry. If a new scenario is added backend-side but the frontend is not updated, the scenario appears in the selector but has no companion context card — leaving a blank panel during the demo.

**Prevention:** When adding a new scenario, treat the frontend talking-point card as a required artifact, not an optional enhancement. Define the card content in the same PR as the scenario JSON. Add a simple test that asserts every scenario key returned by `GET /api/scenarios` has a corresponding frontend card entry.

**Warning signs:** A scenario key exists in `DemoRepository` but no matching `ScenarioCard` component exists in the frontend. The "scenario description" area is empty for newly added scenarios.

**Phase:** New scenario implementation phases.

---

### Pitfall m4: PDF/HTML Export Breaks on New Scenario Trace Shapes

**What goes wrong:** `ReportService` generates HTML and PDF exports. If new scenarios produce new trace event types (e.g., `parallel_dispatch_start`, `agent_merge`, `tool_chain_step`) that the report template does not handle, those events render as raw JSON blobs in the exported report. During a post-demo review meeting where stakeholders look at the exported report, this looks broken.

**Prevention:** When defining new trace event types for new scenarios, add a corresponding display handler in the report template in the same implementation task. Follow the existing event type → display label mapping pattern established for `tool_call`, `a2a_message`, etc.

**Warning signs:** New scenario trace events do not appear in the event-type legend of the existing report UI. Raw `event_type` keys appear in generated HTML reports.

**Phase:** New scenario implementation phases (each scenario).

---

## Phase-Specific Warnings

| Phase Topic | Likely Pitfall | Mitigation |
|---|---|---|
| Multi-step workflow scenario | C4 (trace volume explosion), m4 (new event types in reports) | Define trace view tiers and report display handlers before coding the scenario |
| Parallel agent scenario | C4, M5 (broker timeout), C3 (anyio event loop) | Use in_process transport; tune timeout_ms; add parallel-run integration test |
| Tool discovery scenario | C2 (transport fallback), M1 (false equivalence) | Lock transport to in_process for demo day; write explicit fit statement for the scenario |
| Comparison clarity UI | C1 (same-answer invisibility), M2 (card competes with trace), Pitfall m2 (mixed-mode trace) | Lead with outcome metrics (time, agents, round-trips), not trace depth; strict card budget |
| Real LLM visibility | M3 (untested OpenAI path) | Add FakeReasoningEngine; smoke test one week before demo day |
| Slide-companion content | M4 (non-technical anchoring on names), M2 (text-heavy cards) | Role-first labels; 8-word headline budget per card; presenter-script-first drafting |
| Demo stability pass | C2, C3, Pitfall m1 (port conflicts) | Run mock profile end-to-end on the actual demo machine; add port availability check |

---

## Sources

- Codebase direct inspection: `src/a2a_vs_mcp/mcp/client.py`, `a2a/broker.py`, `platform.py`, `trace.py`
- `.planning/codebase/CONCERNS.md` — technical debt inventory (hardcoded ports, missing coverage, subprocess reliability)
- `.planning/codebase/TESTING.md` — confirmed untested paths (stdio, http, reasoning.py)
- `.planning/codebase/ARCHITECTURE.md` — event flow, transport fallback behavior, trace system design
- A2A Protocol streaming spec: https://a2a-protocol.org/latest/topics/streaming-and-async/
- MCP multi-step tool call context window pitfalls: https://workos.com/blog/mcp-2025-11-25-spec-update
- MCP subprocess transport reliability (in-memory testing consensus): https://mcpcat.io/guides/writing-unit-tests-mcp-servers/
- Agent demo failure patterns: https://www.guideflow.com/blog/live-demos-guide
- A2A vs MCP conceptual confusion sources: https://www.digitalocean.com/community/tutorials/a2a-vs-mcp-ai-agent-protocols, https://www.stride.build/blog/agent-to-agent-a2a-vs-model-context-protocol-mcp-when-to-use-which
- Trace/dashboard information overload: https://www.uxpin.com/studio/blog/dashboard-design-principles/, https://www.owox.com/blog/articles/bad-data-visualization-examples
- MCP token/context overhead when loading tools: https://techcommunity.microsoft.com/blog/azuredevcommunityblog/mcp-vs-mcp-cli-dynamic-tool-discovery-for-token-efficient-ai-agents/4494272
