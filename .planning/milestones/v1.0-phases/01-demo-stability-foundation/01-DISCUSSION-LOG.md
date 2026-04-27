# Phase 1: Demo Stability Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-22
**Phase:** 1 - Demo Stability Foundation
**Areas discussed:** Transport badge, FakeReasoningEngine design

---

## Transport Badge

| Option | Description | Selected |
|--------|-------------|----------|
| Run header row | Next to scenario name / mode selector — always visible during a run | ✓ |
| Results panel only | Shows after run completes, alongside elapsed time and metadata | |
| Settings / config panel | Visible in pre-run configuration area only | |

**User's choice:** Run header row

---

| Option | Description | Selected |
|--------|-------------|----------|
| Transport name only | e.g. "in_process" / "stdio" / "http" — terse, fits in a chip | ✓ |
| Transport + runtime | e.g. "mock · in_process" — shows both AI engine and MCP transport | |
| Full label for non-technical viewers | e.g. "Local mode (no API key)" — more readable | |

**User's choice:** Transport name only

---

## FakeReasoningEngine Design

| Option | Description | Selected |
|--------|-------------|----------|
| In reasoning.py alongside MockReasoner | Keeps all reasoning implementations in one file | ✓ |
| In a test conftest.py only | Test-only fixture, not importable from production code | |

**User's choice:** In reasoning.py alongside MockReasoner

---

| Option | Description | Selected |
|--------|-------------|----------|
| Canned realistic responses | Returns plausible customer support reasoning text per scenario | ✓ |
| Minimal stub (empty/placeholder) | Returns fixed string like '[LLM reasoning skipped]' | |
| Echo the input | Returns a summary of what was sent to it | |

**User's choice:** Canned realistic responses

---

## Claude's Discretion

- pytest migration depth (not discussed — existing unittest.TestCase classes kept as-is)
- Stability pass scope (not discussed — verified by tests passing, not a full matrix)
- Badge color / MUI color variant
- Exact runtime string name for FakeReasoningEngine
- conftest.py structure
- Startup port health check (deferred)

## Deferred Ideas

- Full pytest fixture rewrite — not needed for Phase 1
- Startup port availability health check — Phase 2 or standalone
