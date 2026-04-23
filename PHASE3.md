# Phase 3 Status

## Goal
Phase 3 focused on backend polish, presentation readiness, transport realism, richer demo coverage, and API groundwork for the React frontend built in Phase 4.

## Current Status
Phase 3 is complete for the backend, reporting, transport, and original FastAPI/Jinja dashboard scope.

Phase 4 has since built on this foundation and is now also functionally complete for the current demo scope.

## What Phase 3 Delivered

### 1. Report export layer
Implemented:

- structured report service for saving, loading, and summarizing runs
- exportable HTML presentation reports
- exportable PDF reports via a self-contained PDF generator
- presentation talking points derived from actual run metrics
- richer per-mode scorecards and report-level recommendations
- denser presentation and print polish for exported reports

### 2. Report APIs and trend analysis
Implemented:

- `/api/reports` for saved report summaries
- `/api/reports/{report_name}` for detailed report payloads
- `/api/reports/trends` for saved-report trend analysis
- dedicated trend UI view in the original server-rendered results panel
- filtered trend analysis by scenario, runtime, and recommended mode
- active filter chips and drill-down flows in the original UI
- sortable trend analysis and sortable saved-report views

### 3. Real MCP transport foundation
Implemented:

- explicit MCP transport selection with `in_process`, `stdio`, and `http`
- CLI, API, dashboard, and runtime support for choosing transport
- local streamable HTTP MCP server path for stronger transport realism
- safe fallback to in-process execution when stdio or another live transport is unavailable in the environment
- requested versus active transport captured in traces

Later Phase 4 hardening added hybrid per-run MCP client pooling so HTTP mode avoids duplicate subprocess startup across hybrid specialists.

### 4. Deeper scenarios and data
Implemented:

- broader seed data for customers, orders, payments, tickets, and warranties
- more advanced built-in scenarios with difficulty and tags
- enterprise and multi-intent scenarios for stronger hybrid demos
- deterministic seed refresh when fixtures change

### 5. UI polish in the original stack
Implemented:

- saved report loading and export links in the FastAPI/Jinja UI
- report scorecard and recommendation views
- saved-report trend view in the main panel
- trend filters, active filter chips, and drill-down navigation
- clearer report and trend workflows without replacing the original stack
- sortable trend tables, sortable saved-report views, and stronger visual score presentation

The original FastAPI/Jinja UI is now preserved under `/legacy`; the React frontend is the primary UI.

### 6. Operational demo ergonomics
Implemented:

- named config profiles for `dev`, `demo`, and `llm`
- profile-aware CLI and dashboard controls with explicit overrides
- structured NDJSON external log export for downstream analysis

## Removed From Phase 3 Scope

- dashboard auth

That item is intentionally out of scope for this local/demo project phase and was never required for Phase 3 completion.

## Relationship To Phase 4
Phase 4 built on the APIs and observability groundwork from Phase 3 rather than replacing it.

That includes:

- React reports library and report detail workflows over the existing report APIs
- React trend analytics over the existing trend endpoints
- React trace exploration over existing run/report payloads and NDJSON exports
- presentation mode on top of the scorecard, reporting, and trace foundations delivered in Phase 3
- backend contract hardening with explicit schemas, OpenAPI-generated TypeScript types, `/api/health`, safe report lookup, and API contract tests

## Phase 3 Summary
Phase 3 is complete.

The major UI work that was deferred to Phase 4 has now been delivered in the React frontend, with the original dashboard retained under `/legacy`.

See [PHASE4.md](PHASE4.md) for the current frontend and backend-hardening status.
