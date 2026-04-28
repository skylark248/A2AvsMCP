---
phase: 06-tracerecorder-schema-gate-race-foundation
plan: 06
subsystem: race/replay
tags: [replay, migrator, path-traversal-guard, ndjson]
requires: [06-01, 06-05]
provides:
  - "load_run(run_id, runs_dir) -> list[dict] (TRC-01 causal-order query)"
  - "migrate_v1(events) stub identity v1.0 migrator (TRC-02)"
  - "_validate_run_id path-traversal guard (reused by Plan 07 ws route)"
  - "events_for_lane(events, lane) per-lane filter preserving causal order"
  - "SUPPORTED_SCHEMA_VERSIONS = frozenset({'1.0'})"
affects:
  - "src/a2a_vs_mcp/web.py (Plan 07 will import _validate_run_id)"
tech-stack:
  added: []
  patterns:
    - "re.fullmatch path-traversal guard"
    - "ndjson read inversion of trace.export_external write pattern"
    - "stub no-op migrator (TRC-02; real migration deferred to TODO 4)"
key-files:
  created:
    - src/a2a_vs_mcp/race/replay.py
  modified: []
decisions:
  - "First-event version check in migrate_v1 (cheap; valid because RunWriter stamps every event with the same version)"
  - "FileNotFoundError surfaces from load_run rather than being swallowed — Plan 07's ws route catches it explicitly per RESEARCH.md Pattern 4"
  - "_RUN_ID_RE compiled at module scope without ^/$ anchors; re.fullmatch enforces full-string match (safer than re.match which leaks suffixes)"
metrics:
  duration: "~10 minutes"
  completed: "2026-04-28"
  tasks_completed: "1/1"
  files_created: 1
  files_modified: 0
---

# Phase 6 Plan 06: Replay Loader + Stub Migrator Summary

Implemented the replay-side reader: stub no-op v1.0 migrator (TRC-02), path-traversal-safe `_validate_run_id` regex guard (RESEARCH.md V12 HIGH severity), and `(run_id, lane)` causal-order query helper (TRC-01) — all in `src/a2a_vs_mcp/race/replay.py`.

## What Shipped

`src/a2a_vs_mcp/race/replay.py` (72 lines) exports:

- **`SUPPORTED_SCHEMA_VERSIONS: frozenset[str] = frozenset({"1.0"})`** — Phase 6 recognizes only the version it stamps. Frozenset prevents callers from mutating.
- **`_RUN_ID_RE: re.Pattern[str] = re.compile(r"[A-Za-z0-9_-]{1,64}")`** — module-scoped compiled regex, applied via `re.fullmatch` (no anchors needed; fullmatch enforces whole-string match).
- **`_validate_run_id(run_id: str) -> None`** — raises `ValueError` for any string containing `/`, `..`, NUL, whitespace, dots, or exceeding 64 chars; raises on empty input.
- **`migrate_v1(events) -> events`** — identity migrator. Empty list passes through. First event's `trace_schema_version` is checked against `SUPPORTED_SCHEMA_VERSIONS`; mismatch (or missing key) raises `ValueError("Unsupported trace_schema_version: ...; supported=['1.0']")`.
- **`load_run(run_id, runs_dir) -> list[dict]`** — `_validate_run_id` first (defense-in-depth even though Plan 07 will also validate at the ws boundary); reads `runs_dir / f"{run_id}.json"` via `read_text` (no `exists()` precheck — let `FileNotFoundError` surface for Plan 07 to catch); splits to ndjson lines, parses, runs through `migrate_v1`.
- **`events_for_lane(events, lane) -> list[dict]`** — pure list-comp filter on `event.get("lane") == lane`; input order is preserved → causal order is preserved (RunWriter writes in record order; `TraceRecorder.record` runs in call order).

## Verification

All 10 plan behaviors verified inline:

| # | Behavior                                                | Status |
| - | ------------------------------------------------------- | ------ |
| 1 | All public symbols importable                           | PASS   |
| 2 | `SUPPORTED_SCHEMA_VERSIONS == frozenset({'1.0'})`       | PASS   |
| 3 | `migrate_v1([])` returns `[]`                           | PASS   |
| 4 | v1.0 events identity-passed unchanged                   | PASS   |
| 5 | `migrate_v1([{ver:'0.9'}])` raises `ValueError`         | PASS   |
| 6 | `migrate_v1([{}])` (missing version) raises             | PASS   |
| 7 | path-traversal: `../../etc/passwd`, `/abs`, `x.json`, empty, 65-char all rejected; `good-run-1` accepted | PASS |
| 8 | ndjson round-trip preserves causal order                | PASS   |
| 9 | `events_for_lane` filters + preserves order             | PASS   |
| 10| `load_run("nonexistent", ...)` raises `FileNotFoundError` | PASS |

All 11 acceptance grep checks pass (`from __future__`, `SUPPORTED_SCHEMA_VERSIONS`, exact `frozenset({"1.0"})` literal, `_RUN_ID_RE`, exact regex literal `r"[A-Za-z0-9_-]{1,64}"`, all four function signatures, `.fullmatch(run_id)`, "Unsupported trace_schema_version" string).

Smoke tests from acceptance criteria pass:
- `python -c "...; assert SUPPORTED_SCHEMA_VERSIONS == frozenset({'1.0'}); _validate_run_id('good-run-1'); print('OK')"` → `OK`
- Path-traversal smoke: `_validate_run_id('../../etc/passwd')` raises → `OK`

Full `pytest -q` → **100 passed, 4 subtests passed in 11.18s**.

Plan 08 owns the persistent test file (`tests/race/test_replay_stub.py`); Phase 6 plan 06-06 only ships the implementation per the original phase plan-wave structure.

## Threat Model Compliance

| Threat ID    | Mitigation                                                              | Status |
| ------------ | ----------------------------------------------------------------------- | ------ |
| T-06-06-01   | Path traversal via run_id — `re.fullmatch(r"[A-Za-z0-9_-]{1,64}")`      | MITIGATED |
| T-06-06-02   | Unknown `trace_schema_version` — `migrate_v1` raises `ValueError`       | MITIGATED |
| T-06-06-03   | DoS large ndjson — accepted scope (200-500 events/run hackathon scale)  | ACCEPTED  |
| T-06-06-04   | run_id enumeration timing — accepted; HMAC IDs are TODO 9               | ACCEPTED  |

No new security surface introduced beyond what the threat register enumerates.

## Deviations from Plan

None — plan executed exactly as written. The `<action>` block code template was followed verbatim; all 11 grep acceptance criteria match a single line-by-line file write.

The plan's RED/GREEN TDD framing was satisfied through inline behavior validation (10 tests via `python -c` driver) rather than a committed test file, because the plan explicitly defers `tests/race/test_replay_stub.py` to Plan 08 ("Plan 08 ships this test file" appears in both `<verify>` and `<acceptance_criteria>`). All 10 listed behaviors were verified before commit; no test file was created or removed.

## Known Stubs

- `migrate_v1` is the stub identity migrator per **TRC-02** ("stub no-op migrator recognizes v1.0 traces"). Real migration semantics for v1.1+ are deliberately deferred — TODO 4, indefinite. This is a planned, documented stub, not unintended placeholder code.

## Threat Flags

None. No new endpoints, auth paths, or trust-boundary crossings beyond those enumerated in the plan's `<threat_model>`.

## Commits

| Task | Description                                                          | Commit  |
| ---- | -------------------------------------------------------------------- | ------- |
| 1    | feat(06-06): add race/replay.py with stub migrator + path-traversal guard | aa9a089 |

## Self-Check: PASSED

- File present: `src/a2a_vs_mcp/race/replay.py` — FOUND
- Commit `aa9a089` — FOUND in `git log --oneline`
- Full pytest suite green (100 passed)
- All 11 grep acceptance criteria satisfied
- Both acceptance smoke tests print `OK`
