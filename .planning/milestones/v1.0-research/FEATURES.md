# Feature Landscape

**Domain:** Protocol comparison educational demo platform (MCP vs A2A)
**Researched:** 2026-04-22
**Context:** Extending an existing platform — 4 modes, 2-3 scenarios, trace explorer, learning page, slideshow mode already exist

---

## Table Stakes

Features without which the demo fails for one or both audience segments. Non-negotiable before demo day.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **Mock runtime stability** — all 4 modes run without API keys | Demo day reliability; any crash destroys credibility with both audiences | Low | Existing; needs a dedicated stability pass, not a rewrite |
| **Multi-step workflow scenario** — a ticket requiring 3+ chained tool calls or agent handoffs | Single-hop scenario doesn't make protocol depth visible; engineers won't believe MCP vs A2A matters without seeing it | Medium | New `DemoRepository` entry; fits existing dispatch pattern |
| **Parallel agent execution scenario** — multiple A2A specialists run simultaneously | The single clearest A2A advantage over MCP is parallelism; without it the comparison lacks its strongest proof point | Medium | Requires showing concurrent task dispatch + merge; trace already emits per-specialist events |
| **Comparison clarity at a glance** — non-technical viewers must grasp the difference without reading trace JSON | Decision-makers in the audience will disengage if insight requires reading code or trace payloads | Medium | See UI patterns below; the gap between current and needed is moderate, not a rewrite |
| **Mode navigation that survives a live walkthrough** — step-through across modes is fluid, not error-prone | Presenter panic during live mode-switching kills momentum | Low | Slideshow mode exists; this is a hardening requirement, not a new feature |
| **Talking-point cards per mode/scenario** — embedded in the UI, visible during walkthrough | Mixed audience needs narration cues; non-technical viewers need anchor text; presenters need prompts | Medium | New component; content must be written not just built |
| **Real-LLM path clearly surfaced** — OpenAI runtime activatable and visually distinct in trace | Engineers will ask "is this real AI?"; if the answer is "yes but you can't tell" the demo loses the technical audience | Low | Feature exists; needs visual callout in trace explorer and a toggle affordance in run UI |

---

## Differentiators

Features that elevate the demo from "it works" to "this is the clearest explanation of these protocols I've seen." Not expected, but these are what people remember.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **Tool discovery scenario** — side-by-side showing MCP's dynamic tool listing vs A2A's agent card registry | Exposes the architectural difference that matters most to engineers: how capabilities are advertised and consumed | High | A2A agent cards are already emitting `capability_advertise` events; MCP `tool_discovery` events exist; the scenario needs to make the contrast legible, not just present |
| **Live sequence diagram** — animated message-flow visualization rendered from trace events as they arrive | The single most powerful UI pattern for making protocol message sequences visible to non-technical viewers; replaces walls of JSON with a story | High | No existing component; would require building a lightweight sequence renderer driven by `TraceRecorder` events; see dependency note below |
| **Annotated diff view** — after running two modes, show what changed and why (number of round-trips, agents involved, parallelism) | Decision-makers need a scorecard, not a log; this converts trace data into a business-readable summary | Medium | Partial infrastructure exists in `ReportService` scorecards; needs a presentation-oriented rendering layer |
| **Failure mode walkthrough** — deliberately trigger a tool error or agent timeout and show how each protocol handles it | Error paths are where protocol design choices become most visible; engineers respect demos that don't hide failures | Low | `FailureConfig` and `_simulate_failure` already exist; this is a UI feature to make failure paths prominent, not infrastructure work |
| **"Why this matters" callout panels** — contextual overlays tied to specific trace events (e.g., "This is where A2A's task state machine prevents data loss") | Bridges technical trace events to business-language explanations; serves both audiences simultaneously | Low | Content-heavy; requires a content model and authoring pass, not complex engineering |
| **Protocol glossary popover** — hover on any protocol term (agent card, tool_call, task_submit) to get a one-sentence definition | Non-technical viewers encounter jargon they don't know; a lightweight popover removes friction without breaking flow | Low | Frontend-only; content is the hard part |
| **Run comparison table** — after running all 4 modes, a structured table comparing round-trips, agent hops, latency (mock), and outcome confidence | Gives decision-makers a single artifact they can share or screenshot; converts the demo into a deliverable | Medium | `ReportService` has the data; needs a purpose-built comparison component distinct from the full report UI |

---

## Anti-Features

Things to explicitly not build, with rationale.

| Anti-Feature | Why Avoid | What to Do Instead |
|--------------|-----------|-------------------|
| **Real-time websocket streaming of trace events** | Adds backend and frontend complexity (websocket lifecycle, reconnect logic, partial-event rendering) with marginal gain over a completed-run trace display; mock runs complete in under a second | Load full trace on run completion; animate playback client-side from the completed trace JSON |
| **User accounts / authentication** | Out of scope per PROJECT.md; adds infra complexity that serves zero demo value; this is a single-presenter tool | Stay session-based; all artifacts scoped to `artifacts/` root |
| **LLM-generated slide content** | Dynamic generation of talking points introduces non-determinism into a demo that must be rehearsable; presenter loses confidence in what the slide will say | Hard-code talking-point cards per mode and scenario; keep content under version control |
| **A2A remote transport as a demo path** | Remote transport adds infra dependency (network, remote server health) that can fail during a live demo; local transport already demonstrates the protocol faithfully | Keep remote transport available for CLI exploration; lock demo mode to local transport |
| **Editable scenarios via UI** | Scenario editor complexity (form validation, backend persistence, hot-reload) is out of proportion to the value for a single-presenter demo | Add scenarios via `DemoRepository` code entries; deploy a new version when content changes |
| **Custom theming or white-labeling** | No audience for it; adds CSS complexity | Keep MUI defaults with minor brand color touches if requested |
| **OpenTelemetry / Jaeger / Zipkin export** | External observability infra is irrelevant for a self-contained demo; adds setup burden on demo day | The native `TraceRecorder` JSON export is sufficient; if engineers want to inspect raw traces, ZIP export already exists |
| **Automated test coverage tooling** | PROJECT.md explicitly accepts no CI/coverage for this demo; adding it mid-milestone burns scope | Do a manual stability pass instead: run all modes, all scenarios, with mock runtime, verify no crashes |

---

## Feature Dependencies

```
Mock runtime stability
  └── required before: all demo scenarios run cleanly

Multi-step workflow scenario
  └── required before: comparison clarity improvements (need richer trace data to compare)
  └── required before: annotated diff view (diff is only interesting with multi-step depth)

Parallel agent execution scenario
  └── required before: live sequence diagram (parallel lanes only make sense with parallel agents)
  └── required before: run comparison table (parallelism delta is the key metric to surface)

Talking-point cards per mode
  └── requires: content authoring per scenario (not just the component)
  └── required before: "Why this matters" callout panels (cards are the container; callouts are the content)

Live sequence diagram
  └── requires: parallel agent execution scenario (otherwise diagram is linear, low value)
  └── requires: trace event schema stability (animating from TraceRecorder events; schema must not shift)

Annotated diff view
  └── requires: multi-step workflow scenario
  └── depends on: ReportService scorecard data (partial infrastructure already exists)

Real-LLM path surfaced
  └── independent of new scenarios; can ship any time

Failure mode walkthrough
  └── independent; FailureConfig exists; this is a UI surface change only

Protocol glossary popover
  └── independent; pure frontend + content
```

---

## MVP Recommendation

For a demo 1-2 months out, prioritize in this order:

**Ship first (demo breaks without these):**
1. Mock runtime stability pass — every mode, every scenario, no crashes
2. Multi-step workflow scenario — the depth that makes MCP vs A2A comparison credible
3. Parallel agent execution scenario — the single strongest proof point for A2A
4. Talking-point cards per mode — presenter needs them; audience needs them
5. Comparison clarity UI improvements — non-technical audience loses without this

**Ship if time allows (demo is better, not broken without these):**
6. Real-LLM path clearly surfaced — engineers will ask; easy to add
7. Failure mode walkthrough UI prominence — strong for technical credibility
8. Annotated diff / run comparison table — decision-maker artifact
9. Protocol glossary popovers — removes non-technical friction cheaply

**Defer or cut:**
- Live sequence diagram — high complexity, high value, but too risky for demo timeline
- Tool discovery scenario — compelling but highest complexity; defer to a future milestone unless the parallel agent scenario ships early with time to spare

---

## Scenario Design Notes

Three scenario archetypes map cleanly to the protocol distinctions worth demonstrating:

**Scenario 1 (existing, extend): Multi-step customer support**
Best illustrates: MCP tool chaining depth vs A2A delegation depth
Key trace contrast: `tool_call` chain (MCP) vs `task_submit` → `task_working` → `task_completed` per specialist (A2A)
Non-technical narration: "MCP is like one expert using many tools; A2A is like a manager routing to a team"

**Scenario 2 (new): Parallel specialist resolution**
Best illustrates: A2A's parallelism advantage; MCP's sequential constraint
Key trace contrast: overlapping A2A task timestamps vs sequential MCP tool_call chain
Non-technical narration: "A2A solved it in parallel; MCP had to wait for each answer before asking the next question"

**Scenario 3 (new): Capability discovery**
Best illustrates: MCP's dynamic tool listing (server announces what it can do) vs A2A's agent card registry (agents self-describe their skills)
Key trace contrast: `mcp_capability_discovery` event (server-pushed tool list) vs `agent_register` + `capability_advertise` (agent-initiated registry)
Non-technical narration: "MCP is like browsing a restaurant menu; A2A is like consultants submitting their CVs"
Note: highest build complexity; best as a third scenario if bandwidth allows

---

## Confidence Assessment

| Area | Confidence | Basis |
|------|------------|-------|
| Table stakes completeness | HIGH | Derived directly from PROJECT.md active requirements and demo format constraints |
| Differentiator value | MEDIUM | Grounded in research on technical demo best practices and observability tool UI patterns (LangSmith, Spectacle); no direct precedent for MCP/A2A comparison demo specifically |
| Anti-feature rationale | HIGH | Based on PROJECT.md out-of-scope decisions and engineering complexity analysis of existing architecture |
| Scenario archetypes | HIGH | Protocol differences are well-documented in A2A spec and MCP/A2A comparison literature; the narration framing is inferred |
| UI pattern recommendations | MEDIUM | Based on general protocol visualization and demo best practices research; no existing MCP/A2A demo UI to reference directly |

---

## Sources

- A2A Protocol official spec, agent discovery: https://a2a-protocol.org/latest/topics/agent-discovery/
- Clarifai MCP vs A2A clearly explained: https://www.clarifai.com/blog/mcp-vs-a2a-clearly-explained
- Stride MCP vs A2A when to use which: https://www.stride.build/blog/agent-to-agent-a2a-vs-model-context-protocol-mcp-when-to-use-which
- LangSmith trace visualization patterns: https://ravjot03.medium.com/langsmith-for-agent-observability-tracing-langgraph-tool-calling-end-to-end-2a97d0024dfb
- Interactive demo best practices 2026: https://www.navattic.com/blog/interactive-demos
- Developer-focused demo creation: https://business.daily.dev/resources/create-developer-focused-demos/
- Multi-agent orchestration patterns: https://www.digitalapplied.com/blog/multi-agent-orchestration-patterns-producer-consumer
