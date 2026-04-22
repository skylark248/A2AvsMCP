# Technology Stack Research
**Project:** A2A vs MCP Demo Platform (Milestone extension)
**Researched:** 2026-04-22
**Mode:** Ecosystem — what to adopt/upgrade for better demo quality

---

## Context: What Already Exists

The platform is Python 3.12 / FastAPI / Uvicorn on the backend and React 19 / TypeScript / MUI 7 on the frontend. The active protocol SDKs are `mcp[cli]>=1.27.0` (pinned at latest stable) and `a2a-sdk[http-server]==0.3.25` (pinned at a specific stable release). This research answers: what to adopt, upgrade, or avoid for the new milestone work.

---

## SDK Version Landscape

### MCP Python SDK (`mcp`)

| What | Detail |
|------|--------|
| Currently pinned | `>=1.27.0` |
| Latest stable | `1.27.0` (released 2026-04-02) — already at latest |
| V2 status | Pre-alpha on `main` branch; no released alpha as of 2026-04-22. Q1 2026 target passed without a Python v2 alpha. FastMCP is removed in v2, replaced by `McpServer`. |
| Recommendation | **Stay on `>=1.27.0` (already correct).** Do NOT attempt to track v2 pre-alpha for a demo platform. The breaking `FastMCP` → `McpServer` rename will require a non-trivial migration. Pin `mcp>=1.27,<2` to avoid being auto-upgraded into a breaking pre-release if/when v2 alpha lands on PyPI. |

**Confidence:** HIGH — verified via PyPI and GitHub releases.

### A2A Python SDK (`a2a-sdk`)

| What | Detail |
|------|--------|
| Currently pinned | `==0.3.25` |
| Latest 0.3.x stable | `0.3.26` (released 2026-04-09) — one patch behind |
| Latest overall | `1.0.0` (released 2026-04-20) — major breaking release |
| V1.0.0 breaking changes | Removed `ClientTaskManager`/`Consumers`, renamed `ClientFactory` API, renamed "callback" → "push_notification_config", Starlette route-based server instead of Application wrappers, proto-based Part types, SCREAMING_SNAKE_CASE enums. Official migration guide at `docs/migrations/v1_0/README.md`. |

**Recommendation:** Two-part decision:

1. **Immediately safe:** Bump `a2a-sdk[http-server]` to `==0.3.26` to pick up the patch. The existing `sdk_compat.py` compatibility layer absorbs API differences in 0.3.x so this is low risk.
2. **Migration to 1.0 is a Phase-level decision, not a quick bump.** The proto-based Part types and renamed client API touch `src/a2a_vs_mcp/a2a/` directly. Budget dedicated time (see PITFALLS.md). For the current milestone — educational scenario work and UI clarity — stay on `0.3.26` and add the migration as a separate tracked item.

**Confidence:** HIGH — verified via PyPI, GitHub releases page, and official migration guide presence.

### OpenAI Python SDK (`openai`)

| What | Detail |
|------|--------|
| Currently pinned | `>=2.30.0` |
| Latest stable | `2.32.0` (released 2026-04-15) |
| Recommendation | **Stay on `>=2.30.0` (already correct).** The SDK follows a rolling release; the constraint already tracks current. No breaking changes in 2.30–2.32 range. |

**Confidence:** HIGH — verified via PyPI.

---

## New Backend Libraries to Adopt

### 1. `pytest` + `pytest-asyncio` — Replace `unittest` for backend tests

**Why:** The current backend uses Python `unittest`. FastAPI + async MCP/A2A code is genuinely async; `unittest` cannot run async test functions natively. The recommended pattern for FastAPI in 2025–2026 is `pytest` with `httpx.AsyncClient` + `ASGITransport` — this lets you drive the full ASGI app in-process, async, without starting a server.

| Library | Version | Purpose |
|---------|---------|---------|
| `pytest` | `>=9.0.0` | Test runner (latest stable: 9.0.3) |
| `pytest-asyncio` | `>=1.3.0` | Async test support (latest stable: 1.3.0, released 2025-11-10) |
| `httpx` | `>=0.28.0` | AsyncClient + ASGITransport for in-process FastAPI testing (latest stable: 0.28.1) |

**Usage pattern:**
```python
@pytest.mark.asyncio
async def test_run_demo():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/run", json={...})
    assert response.status_code == 200
```

**What NOT to use:** FastAPI's `TestClient` (synchronous, wraps async with blocking threads — leads to subtle event-loop conflicts when testing MCP/A2A async paths). Avoid `async_asgi_testclient` — unmaintained.

**Add to `pyproject.toml`:**
```toml
[project.optional-dependencies]
dev = [
  "ruff>=0.8.0",
  "pytest>=9.0.0",
  "pytest-asyncio>=1.3.0",
  "httpx>=0.28.0",
]
```

**Confidence:** HIGH — pattern recommended by FastAPI official docs and community consensus 2025–2026.

### 2. `httpx` — Already needed for testing; also useful for outbound HTTP in demos

`httpx` has zero overlap with `requests` (which is not in the current stack). It provides async-native HTTP both for test transport and for any demo scenario needing to call the MCP streamable-HTTP endpoint or A2A agent cards over HTTP in test fixtures.

**Do not add to core `dependencies`** — it belongs in `dev` extras only unless a non-test scenario needs it.

**Confidence:** HIGH.

---

## New Frontend Libraries to Adopt

### 1. `@xyflow/react` — Agent/protocol flow diagrams

**Why:** The "Tool Discovery" scenario needs a side-by-side visualization of MCP's tool-listing vs A2A's agent-card registry. ReactFlow (now packaged as `@xyflow/react`) is the de-facto standard for interactive node-graph UIs in React. It's been updated for React 19 and Tailwind CSS 4. The showcase explicitly includes AI agent workflow visualizers.

| Library | Version | Purpose |
|---------|---------|---------|
| `@xyflow/react` | `^12.10.2` | Interactive node graphs showing protocol topology |

**What it gives you:** Nodes representing MCP tools or A2A agents, edges showing capability discovery/invocation paths, zoom/pan, mini-map, custom node components. Custom node components can render MUI cards with tool metadata inline.

**What NOT to use:** Mermaid.js for React — the wrapper ecosystem is fragmented (official `mermaid-js/react-wrapper` exists but is thin; community wrappers are unmaintained). Mermaid is appropriate for static diagrams in docs, not interactive runtime visualizations.

**Confidence:** HIGH — version verified via npm, React 19 compatibility confirmed.

### 2. `recharts` — Timeline/event frequency charts

**Why:** The platform already emits structured trace events. Recharts is the dominant React + D3 chart library (3.8.1, released 2026-03-25), lightweight, TypeScript-native since v2.5+, and composable with MUI layouts. Adding a simple timeline/bar chart of event counts by protocol type would make the trace data visually scannable at a glance for non-technical viewers.

| Library | Version | Purpose |
|---------|---------|---------|
| `recharts` | `^3.8.0` | Event timeline charts, protocol comparison bar charts |

**What NOT to use:** Chart.js / react-chartjs-2 — heavier, less composable with React patterns, no built-in TypeScript types. Nivo — excellent but heavyweight (pulls in D3 tree-shaking is complex); overkill for 2–3 chart views. Google Charts — external CDN dependency, not suitable for an offline demo.

**Confidence:** HIGH — version verified via npm.

### 3. `react-syntax-highlighter` — Code and JSON payload display

**Why:** The trace explorer shows raw protocol messages (MCP tool-call JSON, A2A task payloads). Rendering these as plain `<pre>` blocks is hard to read. `react-syntax-highlighter` with the Prism light build adds syntax coloring with zero styling conflicts (use `useInlineStyles={false}` for className-based output that respects MUI theme).

| Library | Version | Purpose |
|---------|---------|---------|
| `react-syntax-highlighter` | `^15.x` | JSON/Python syntax coloring in trace viewer |
| `@types/react-syntax-highlighter` | `^15.x` | TypeScript types |

**What NOT to use:** `shiki` — powerful but requires async loading and WASM; adds complexity for a demo. `highlight.js` directly — more setup than the React wrapper provides.

**Confidence:** MEDIUM — version from npm (package is actively maintained as of Feb 2026 per search results; exact latest minor not verified against npm directly).

### 4. `motion` (formerly `framer-motion`) — Micro-animations for comparison clarity

**Why:** The active milestone requirement "Comparison clarity improvements — UI enhancements that make A2A vs MCP differences unmissable" is inherently about motion. `motion` (the rebrand of framer-motion, v12 as of 2026) animates protocol state changes: a tool invocation lighting up, an agent card appearing in the registry, task state transitions. The library is 30M monthly downloads, React 19 compatible.

| Library | Version | Purpose |
|---------|---------|---------|
| `motion` | `^12.x` | Animate trace events, highlight active protocol steps |

**Important:** The package name changed from `framer-motion` to `motion`. If `framer-motion` is already in `package.json` (it is not, per current stack), migrate to `motion`. Import from `motion/react`.

**What NOT to use:** CSS transitions alone — they cannot drive data-driven animations (e.g., "highlight when this trace event fires"). React Spring — valid alternative but more complex API for the same use cases here.

**Confidence:** MEDIUM — version from web search; React 19 compatibility confirmed per library docs.

---

## Libraries to Explicitly NOT Adopt

| Library | Why Not |
|---------|---------|
| `@evilmartians/agent-prism` | Alpha-only, requires Tailwind CSS (platform uses MUI), Radix UI deps conflict with MUI. Pulls in its own full component system. Not appropriate to layer on an existing MUI app. |
| `openai-agents` (OpenAI Agents SDK) | Adds a second agent orchestration framework on top of the existing MCP/A2A stack. The demo's educational value is showing MCP and A2A directly — adding a third framework muddies the narrative. Use the existing `openai` SDK directly. |
| `a2a-sdk==1.0.0` (now) | Breaking migration that touches the A2A broker core. Not justified in a milestone focused on scenario depth and UI clarity. Defer to a dedicated migration phase. |
| `mcp` v2 pre-alpha | No released Python v2 alpha exists. FastMCP removal is a breaking change. Pin `<2`. |
| `zustand` | The existing React app likely manages state through component-local state + React Router. Adding a global store for a demo-day platform adds complexity with no user-facing benefit. Only adopt if profiling reveals prop-drilling pain in the new scenarios. |
| Gantt/Syncfusion timeline libraries | Vendor lock-in, heavyweight. Recharts LineChart with event timestamps achieves the visualization goal. |

---

## Recommended `pyproject.toml` Changes

```toml
[project]
dependencies = [
  "fastapi>=0.135.3",
  "jinja2>=3.1.6",
  "mcp[cli]>=1.27,<2",         # pin below v2 to avoid FastMCP removal surprise
  "openai>=2.30.0",
  "uvicorn>=0.30.0"
]

[project.optional-dependencies]
dev = [
  "ruff>=0.8.0",
  "pytest>=9.0.0",
  "pytest-asyncio>=1.3.0",
  "httpx>=0.28.0",
]
remote-a2a = [
  "a2a-sdk[http-server]==0.3.26",  # bump from 0.3.25 — safe patch
]
```

---

## Recommended `package.json` Additions

```json
{
  "dependencies": {
    "@xyflow/react": "^12.10.2",
    "recharts": "^3.8.0",
    "react-syntax-highlighter": "^15.6.1",
    "motion": "^12.0.0"
  },
  "devDependencies": {
    "@types/react-syntax-highlighter": "^15.5.13"
  }
}
```

---

## Confidence Summary

| Area | Confidence | Basis |
|------|------------|-------|
| MCP SDK version | HIGH | PyPI verified, GitHub releases checked |
| A2A SDK version + v1.0 risk | HIGH | PyPI verified, migration guide existence confirmed |
| OpenAI SDK version | HIGH | PyPI verified |
| pytest/pytest-asyncio/httpx | HIGH | PyPI verified, FastAPI official docs align |
| @xyflow/react | HIGH | npm verified, React 19 compat confirmed |
| recharts | HIGH | npm verified, active maintenance confirmed |
| react-syntax-highlighter version | MEDIUM | Package confirmed active; exact latest minor not re-fetched from npm |
| motion version | MEDIUM | Web search confirms v12 as of 2026; not fetched from npm directly |
| agent-prism rejection | HIGH | Official README confirms Tailwind + Radix UI deps, alpha status |
| a2a-sdk 1.0 migration risk | HIGH | Breaking changes documented and confirmed |

---

## Sources

- [mcp on PyPI](https://pypi.org/project/mcp/) — version 1.27.0 confirmed
- [a2a-sdk on PyPI](https://pypi.org/project/a2a-sdk/) — versions 0.3.25/0.3.26/1.0.0 confirmed
- [a2a-python GitHub](https://github.com/a2aproject/a2a-python) — migration guide and breaking changes
- [openai on PyPI](https://pypi.org/project/openai/) — version 2.32.0 latest
- [pytest on PyPI](https://pypi.org/project/pytest/) — version 9.0.3 latest
- [pytest-asyncio on PyPI](https://pypi.org/project/pytest-asyncio/) — version 1.3.0 latest
- [httpx on PyPI](https://pypi.org/project/httpx/) — version 0.28.1 latest
- [FastAPI async tests docs](https://fastapi.tiangolo.com/advanced/async-tests/) — ASGITransport pattern
- [@xyflow/react on npm](https://www.npmjs.com/package/@xyflow/react) — version 12.10.2
- [recharts on npm](https://www.npmjs.com/package/recharts) — version 3.8.1
- [agent-prism GitHub](https://github.com/evilmartians/agent-prism) — alpha status, Tailwind/Radix deps
- [motion.dev](https://motion.dev/docs/react) — React 19 compatible, v12
- [MCP v2 migration article](https://medium.com/the-ai-language/mcp-is-migrating-from-version-1-to-version-2-07f4cc7624fb) — FastMCP removal confirmed
- [MCP protocol transports spec 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/transports) — Streamable HTTP canonical
