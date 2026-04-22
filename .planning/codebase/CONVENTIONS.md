# Coding Conventions
_Last updated: 2026-04-21_

## Summary

The project is a Python/TypeScript monorepo. Backend Python code is linted with Ruff (E9/F rules, 160-char line length) and every source module opens with `from __future__ import annotations`. The React/TypeScript frontend is formatted with Prettier and linted with typescript-eslint. Both layers follow consistent naming and structural conventions documented below.

---

## Python — Naming Patterns

**Files/modules:**
- `snake_case.py` throughout — e.g. `remote_broker.py`, `hybrid_specialists.py`, `api_schemas.py`
- MCP server modules suffixed `_server`: `db_server.py`, `docs_server.py`
- Sub-packages group related concerns: `a2a/`, `agents/`, `mcp/`, `mcp_servers/`

**Classes:**
- `PascalCase` — e.g. `DemoPlatform`, `A2ABroker`, `AgentContext`, `ProfileConfig`, `TraceRecorder`
- Dataclasses used for all plain data containers (`@dataclass`)

**Functions and methods:**
- `snake_case` — e.g. `get_ticket`, `send_task`, `find_by_capability`, `close_mcp_clients`
- Private helpers prefixed with `_` — e.g. `_resolve_handler`, `_execute_with_timeout`, `_record_task_status`
- Properties decorated with `@property` — e.g. `card`, `latency_ms`

**Variables:**
- `snake_case` for local variables and instance attributes
- Module-level constants in `UPPER_SNAKE_CASE` — e.g. `PROJECT_ROOT`, `PROFILES`, `TEMPLATES`, `DEFAULT_TREND_SORTING`

**Type annotations:**
- Used on all function signatures and dataclass fields
- Union syntax uses `X | Y` (PEP 604, enabled via `from __future__ import annotations` in all 31 source files)
- `dict[str, Any]`, `list[str]`, `tuple[str, ...]` — lowercase generics throughout (not `Dict`, `List`, `Tuple`)
- Optional parameters annotated as `X | None` — e.g. `profile_name: str | None = None`

---

## Python — Code Style

**Linter:**
- Ruff `>=0.8.0`, config in `pyproject.toml`
- Rules: `E9` (runtime errors), `F` (pyflakes) — minimal rule set, no style enforcement beyond basics
- Line length: **160** characters
- Target: Python 3.10+
- Excluded paths: `artifacts/`, `frontend/dist/`, `frontend/node_modules/`, `.tmp/`, `.venv/`

**Formatting:**
- No dedicated formatter configured (no Black, no `ruff format` in CI). Ruff lint only.
- 4-space indentation (Python standard)

**Future annotations:**
- `from __future__ import annotations` is the first statement in every source file — applied universally

---

## Python — Import Organization

**Order within a file (consistent pattern observed):**
1. `from __future__ import annotations`
2. Standard library imports (alphabetical within group)
3. Third-party imports (FastAPI, Pydantic, etc.)
4. Local package imports using relative paths (`from ..schemas import ...`, `from .protocol import ...`)

**Path style:**
- Relative imports used exclusively within the `a2a_vs_mcp` package — e.g. `from ..schemas import`, `from .broker import`
- No path aliases or `src/` prefix in imports (package installed in editable mode via `pip install -e .`)

**Deferred imports:**
- Occasionally used inside methods to avoid circularity — e.g. `from ..mcp.client import MCPClient` inside `AgentContext.get_mcp_client()`

---

## Python — Error Handling

**Domain layer** (`broker.py`, `reporting.py`, `remote_registry.py`):
- Raises typed built-in exceptions: `KeyError`, `ValueError`, `RuntimeError`, `FileNotFoundError`, `TimeoutError`
- Error messages are descriptive with context: `f"No agent registered for capability '{capability}'"`
- Chained exceptions used: `raise RuntimeError(...) from exc`

**API layer** (`web.py`, `a2a/remote_server.py`):
- Catches domain exceptions and converts to `HTTPException` with appropriate status codes
- Pattern: `except FileNotFoundError as exc: raise HTTPException(status_code=404, ...) from exc`
- HTTP 400 for `ValueError`, 404 for `FileNotFoundError`/`KeyError`, 401/503/500 for remote failures

**Transient failures:**
- Retry logic in `A2ABroker.send_task()` — bare `except Exception as exc` catches all handler errors, records trace events, and re-raises after `max_retries` exhausted

**Silent fallbacks:**
- `json.JSONDecodeError` silently skipped in `dataset.py` and `persistence.py` when reading corrupt/missing files

---

## Python — Comments and Documentation

**Docstrings:** Not used in this codebase — functions and classes have no docstrings.

**Inline comments:** Rare; logic is expressed through descriptive naming rather than comments.

**Type hints serve as documentation** — all public method signatures fully annotated, making intent clear without prose.

---

## TypeScript/React — Naming Patterns

**Files:**
- `PascalCase.tsx` for React components and pages — e.g. `RunWorkspacePage.tsx`, `AppShell.tsx`, `MetricBarsCard.tsx`
- `camelCase.ts` for non-component modules — e.g. `client.ts`, `presets.ts`, `utils.ts`
- Test files co-located, suffixed `.test.tsx` / `.test.ts` — e.g. `RunWorkspacePage.test.tsx`

**Components:**
- Named exports for all components and pages — e.g. `export function RunWorkspacePage()`
- Feature-based directory grouping under `frontend/src/features/`

**Functions and variables:**
- `camelCase` for functions, hooks, and variables
- `UPPER_SNAKE_CASE` for module-level constants — e.g. `API_BASE_URL`

**Types/interfaces:**
- Imported from generated API types at `frontend/src/lib/types/api.generated.ts` (script: `scripts/generate_api_types.py`)
- Hand-authored types in `frontend/src/lib/types/api.ts`

---

## TypeScript — Code Style

**Formatter:** Prettier `>=3.8.1` — enforced in CI via `npm run format:check`

**Linter:** ESLint `>=9.x` with `typescript-eslint` recommended rules
- Config: `frontend/eslint.config.js`
- `@typescript-eslint/no-explicit-any`: **off** — `any` is freely used
- `react-refresh/only-export-components`: **off**
- `react-hooks` rules: recommended set enabled

**TypeScript:**
- `strict` mode via `tsconfig.app.json`
- Target: ES2022, module: ESNext
- Type-checked in CI via `npm run typecheck` (`tsc -b --pretty false`)

---

## TypeScript — Import Organization

**Order observed:**
1. Third-party library imports (`@mui/material`, `react-router-dom`, `vitest`)
2. Internal app-layer imports (absolute-style, from `../../app/...`)
3. Local feature/sibling imports

**No barrel files (`index.ts`)** observed — each module imported directly by path.

---

## TypeScript — Error Handling

**API client** (`frontend/src/lib/api/client.ts`):
- `requestJson<T>()` central fetch wrapper — non-`ok` responses throw `Error` with normalized message
- `stringifyApiDetail()` helper handles string, array, and object FastAPI error shapes
- Errors propagate to UI consumers as thrown `Error` instances

---

## Shared Conventions

**Return type annotations:** All Python functions annotate return type — including `-> None` for procedures.

**Keyword-only arguments:** Python helpers use `*` separator to force keyword-only args where ambiguity risk exists — e.g. `_record_task_status(..., *, final: bool = False, error: str | None = None)`

**Dataclasses over dicts:** Structured data always uses `@dataclass` in Python rather than untyped dicts. `asdict()` used at serialization boundaries.

**`to_dict()` pattern:** Domain objects expose a `to_dict() -> dict[str, Any]` method using `asdict()` — e.g. `FailureConfig.to_dict()`, `ProfileConfig.to_dict()`.
