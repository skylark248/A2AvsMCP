# A2A vs MCP Demo Platform

## Project Overview

A comparative learning and demo platform for MCP (Model Context Protocol) vs A2A (Agent-to-Agent protocol). Python/FastAPI backend with React + Material UI frontend.

## Key Paths

- `src/a2a_vs_mcp/` -- Python backend (platform, broker, MCP servers, web routes)
- `frontend/src/` -- React frontend
- `serve_ui.py` -- FastAPI UI server (port 8008)
- `main.py` -- CLI entry point

## Commands

- Backend tests: `pytest`
- Frontend tests: `cd frontend && npm test`
- Frontend dev: `cd frontend && npm run dev`
- Start app: `python serve_ui.py`

## gstack

Use the `/browse` skill from gstack for all web browsing. Never use `mcp__claude-in-chrome__*` tools.

### Available Skills

/office-hours, /plan-ceo-review, /plan-eng-review, /plan-design-review, /design-consultation, /design-shotgun, /design-html, /review, /ship, /land-and-deploy, /canary, /benchmark, /browse, /connect-chrome, /qa, /qa-only, /design-review, /setup-browser-cookies, /setup-deploy, /setup-gbrain, /retro, /investigate, /document-release, /codex, /cso, /autoplan, /plan-devex-review, /devex-review, /careful, /freeze, /guard, /unfreeze, /gstack-upgrade, /learn

## claude mem

This project has memories stored in claude mem (running at http://localhost:37701).

Rules:
- Use `/mem-search` or query `GET /api/search` to recall project context before starting new work
- Save significant architectural decisions, gotchas, and session learnings via `POST /api/memory/save` with `project: "A2AvsMCP"`
- Existing memories: project overview (#7), architecture and key files (#9), scenarios/routes/API (#11)

## graphify

This project has a graphify knowledge graph at graphify-out/.

Rules:
- Before answering architecture or codebase questions, read graphify-out/GRAPH_REPORT.md for god nodes and community structure
- If graphify-out/wiki/index.md exists, navigate it instead of reading raw files
- For cross-module "how does X relate to Y" questions, prefer `graphify query "<question>"`, `graphify path "<A>" "<B>"`, or `graphify explain "<concept>"` over grep — these traverse the graph's EXTRACTED + INFERRED edges instead of scanning files
- After modifying code files in this session, run `graphify update .` to keep the graph current (AST-only, no API cost)
