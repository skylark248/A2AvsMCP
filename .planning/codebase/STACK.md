# Technology Stack
_Last updated: 2026-04-21_

## Summary

A2A vs MCP is a full-stack comparative learning platform with a Python 3.12 backend and a React 19 + TypeScript frontend. The backend is a FastAPI application served by Uvicorn, with the frontend compiled as a static dist and served from the same process. The project is containerized via Docker with a multi-stage build.

---

## Languages

**Primary:**
- Python 3.12 (runtime in Docker; requires >=3.10 per `pyproject.toml`) — all backend logic
- TypeScript 5.9 — entire React frontend under `frontend/src/`

**Secondary:**
- HTML/Jinja2 — legacy server-side templates in `src/a2a_vs_mcp/templates/`

---

## Runtime

**Backend:**
- Python 3.12-slim (Docker image: `python:3.12-slim`)
- Package manager: `pip` with `setuptools>=68` + `wheel` build backend
- No `requirements.txt` — all deps declared in `pyproject.toml`

**Frontend (build-time only):**
- Node 22-alpine (Docker build stage: `node:22-alpine`)
- Package manager: `npm` with `package-lock.json` lockfile present

---

## Frameworks

**Backend Core:**
- `fastapi>=0.135.3` — REST API and HTML route serving (`src/a2a_vs_mcp/web.py`)
- `uvicorn>=0.30.0` — ASGI server; default entry point `a2a_vs_mcp.web:app` on port 8008
- `jinja2>=3.1.6` — legacy template rendering (`src/a2a_vs_mcp/templates/`)

**Protocol Integrations:**
- `mcp[cli]>=1.27.0` — Model Context Protocol SDK; used in `src/a2a_vs_mcp/mcp/client.py` via `mcp.ClientSession`, `mcp.client.stdio`, `mcp.client.streamable_http`
- `a2a-sdk[http-server]==0.3.25` — official Google A2A SDK (optional extra `remote-a2a`); compatibility layer in `src/a2a_vs_mcp/a2a/sdk_compat.py`

**LLM:**
- `openai>=2.30.0` — used lazily in `src/a2a_vs_mcp/reasoning.py` via `LLMReasoner`; only loaded when `OPENAI_API_KEY` is set

**Frontend Core:**
- React 19.2
- React Router DOM 7.9
- MUI (Material UI) 7.3 with `@emotion/react` and `@emotion/styled`

**Frontend Build:**
- Vite 7.1 with `@vitejs/plugin-react`
- TypeScript compiler (`tsc -b`) runs before `vite build`

---

## Key Dependencies

**Critical Backend:**
- `fastapi` — entire API surface and UI serving (`src/a2a_vs_mcp/web.py`)
- `mcp[cli]` — MCP transport modes: `in_process`, `stdio`, `http`, `remote_http`
- `openai` — LLM runtime mode (`llm` profile); requires `OPENAI_API_KEY` env var

**Critical Frontend:**
- `@mui/material` 7.3 + `@mui/icons-material` 7.3 — UI component library
- `react-router-dom` 7.9 — SPA routing for `/`, `/learn`, `/reports`, `/traces`, `/presentation`, `/trends`

**Infrastructure:**
- `sqlite3` (stdlib) — telemetry and run-event storage via `PlatformStore` (`src/a2a_vs_mcp/persistence.py`); DB at `artifacts/platform_state.db`
- `anyio` — async I/O used in `src/a2a_vs_mcp/mcp/client.py`

---

## Dev Dependencies

**Backend:**
- `ruff>=0.8.0` — linter/formatter; configured in `pyproject.toml` with `line-length=160`, `target-version=py310`, selects `E9,F` rules

**Frontend:**
- `vitest 4.1` — test runner (`npm run test` → `vitest run`)
- `@testing-library/react 16.3` + `@testing-library/jest-dom 6.9` + `@testing-library/user-event 14.6`
- `eslint 9.39` + `typescript-eslint 8.58` + `eslint-plugin-react-hooks` + `eslint-plugin-react-refresh`
- `prettier 3.8` — formatting (`npm run format`)
- `jsdom 29` — DOM environment for Vitest

---

## Build

**Production container:** `docker-compose.yml` / `Dockerfile`
- Stage 1: `node:22-alpine` builds frontend (`npm ci && npm run build`)
- Stage 2: `python:3.12-slim` installs Python deps (`pip install .`), copies built frontend dist
- Final image exposes port 8008; CMD: `uvicorn a2a_vs_mcp.web:app --host 0.0.0.0 --port 8008`

**Local dev (backend):**
```bash
pip install -e .                  # core
pip install -e ".[dev]"           # + ruff
pip install -e ".[remote-a2a]"    # + a2a-sdk for remote A2A mode
python -m uvicorn a2a_vs_mcp.web:app --reload
```

**Local dev (frontend):**
```bash
cd frontend && npm install && npm run dev   # Vite dev server
```

---

## Configuration

**Environment variables (backend):**
- `A2A_VS_MCP_PROFILE` — active profile (`dev` | `demo` | `llm`); default `dev`
- `A2A_TRANSPORT` — override A2A transport (`local` | `remote`)
- `MCP_TRANSPORT` — override MCP transport (`in_process` | `stdio` | `http` | `remote_http`)
- `OPENAI_API_KEY` — enables `LLMReasoner`; without it the platform falls back to `MockReasoner`
- `OPENAI_MODEL` — model name; default `gpt-4o-mini`
- `A2A_VS_MCP_ALLOW_EXTERNAL_REMOTE_URLS` — set `true` to permit non-local remote URLs
- Remote A2A agent URLs (Docker Compose): `REMOTE_A2A_CUSTOMER_URL`, `REMOTE_A2A_DOCUMENTATION_URL`, `REMOTE_A2A_POLICY_URL`

**Config source:** `src/a2a_vs_mcp/config.py` — three named profiles (`dev`, `demo`, `llm`) each fixing runtime, MCP transport, save-report, and export-logs defaults.

---

## Platform Requirements

**Development:**
- Python >=3.10 (3.12 recommended to match Docker image)
- Node 22 (matches Docker build stage)

**Production:**
- Docker + Docker Compose (see `docker-compose.yml`)
- Port 8008 (main web), 9101/9102/9103 (remote A2A specialist agents)
