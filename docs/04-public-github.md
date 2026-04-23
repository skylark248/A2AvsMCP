# Public GitHub Readiness

This checklist keeps the project useful for people who clone it without context.

## What Should Be Committed

Commit source, docs, seed data, scripts, tests, and small configuration files.

Do not commit generated runtime output:

- `artifacts/`
- `frontend/node_modules/`
- `frontend/dist/`
- `__pycache__/`
- `*.pyc`
- local `.env` files

A tiny curated sample evidence bundle can be added later under a dedicated `examples/` directory if it helps the README, but default runtime artifacts should stay out of git.
Curated report and trace examples are safe to keep under `examples/`, including the remote A2A bad-auth trace/report used for presentation. Lightweight documentation media can live under `docs/media/`, such as the remote A2A topology SVG.

## Clone-To-Learn Flow

Recommended public README path:

1. Read the MCP vs A2A mental model.
2. Install Python and frontend dependencies.
3. Run backend tests.
4. Build the frontend.
5. Start `py serve_ui.py`.
6. Open `/learn`.
7. Run the guided lessons.
8. Move to the run workspace and experiment with failure toggles.
9. For hosted remote A2A, run `docker compose up --build -d`, then `py scripts\check_remote_a2a.py`, and set `A2A Transport` to `Remote HTTP` in the run workspace.

## CI Expectations

The CI workflow should run:

- backend unit tests
- scenario validation
- preset validation
- frontend test suite
- frontend production build

## Security And Scope Notes

This is a local educational/demo platform. Before hosting it publicly as a service, add authentication, authorization, remote MCP/A2A credential management, stronger multi-tenant isolation, artifact retention policy, and deployment hardening.

For local clone-and-run usage, the current bounded user-scoped artifacts are enough for demos and workshops.

## Public Positioning

Use this phrasing in the README and talks:

"This project uses official MCP SDK components for the MCP path, an educational local A2A-style broker for agent collaboration concepts, and a hosted remote A2A demo binding behind `sdk_compat.py`."

That is accurate, clear, and fair to learners.
