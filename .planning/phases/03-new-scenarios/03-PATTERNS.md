# Phase 3: New Scenarios — Pattern Map

**Mapped:** 2026-04-23
**Files analyzed:** 9 (6 backend, 2 frontend, 1 test)
**Analogs found:** 9 / 9

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `src/a2a_vs_mcp/schemas.py` | model | transform | `src/a2a_vs_mcp/schemas.py` (existing `SupportTicket`) | self — field addition |
| `src/a2a_vs_mcp/api_schemas.py` | model | request-response | `src/a2a_vs_mcp/api_schemas.py` (existing `TraceEventResponse` Phase 2 additions) | self — model addition + field addition |
| `src/a2a_vs_mcp/dataset.py` | service | CRUD | `src/a2a_vs_mcp/dataset.py` (`load_scenarios()` existing body) | self — one-line constructor extension |
| `src/a2a_vs_mcp/agents/triage.py` | service | request-response | `src/a2a_vs_mcp/agents/triage.py` (`_request_specialist()` method) | self — new parallel method + branch |
| `src/a2a_vs_mcp/data/seeds/scenarios.json` | config | batch | `src/a2a_vs_mcp/data/seeds/scenarios.json` (existing 10 entries) | self — append + field addition |
| `src/a2a_vs_mcp/data/seeds/warranties.json` | config | batch | `src/a2a_vs_mcp/data/seeds/warranties.json` (existing 3 entries) | self — append one record |
| `frontend/src/lib/types/api.generated.ts` | model | transform | `frontend/src/lib/types/api.generated.ts` (`TraceEventResponse` Phase 2 patch) | self — interface addition + field addition |
| `frontend/src/features/run-workspace/RunWorkspacePage.tsx` | component | request-response | `frontend/src/features/run-workspace/RunWorkspacePage.tsx` (result card map) | self — import addition + JSX insertion |
| `tests/test_demo_modes.py` | test | CRUD | `tests/test_demo_modes.py` (`test_send_tasks_parallel_emits_batch_fields`, `test_multi_step_scenario_mentions_multiple_concerns`) | self — new test methods |

---

## Pattern Assignments

### `src/a2a_vs_mcp/schemas.py` — add `talking_point` to `SupportTicket`

**Analog:** `src/a2a_vs_mcp/schemas.py`, lines 17–26 (existing `SupportTicket` dataclass)

**Existing field pattern to extend** (lines 17–26):
```python
@dataclass
class SupportTicket:
    ticket_id: str
    customer_id: str
    query: str
    scenario: str = "custom"
    title: str = ""
    difficulty: str = "standard"
    tags: list[str] = field(default_factory=list)
```

**Change:** Append one field after `tags`. Fields with defaults must follow positional fields — `tags` already satisfies that. Use `None` default (not `field(default_factory=...)`), since `dict | None` does not need a factory:
```python
    tags: list[str] = field(default_factory=list)
    talking_point: dict | None = None
```

**Note:** `dataclasses.asdict()` passes plain `dict` through unchanged — no nested-dataclass recursion risk. `RunOutput` holds `ticket: SupportTicket`, so `talking_point` propagates automatically through `asdict(run_output)` calls.

---

### `src/a2a_vs_mcp/api_schemas.py` — add `TalkingPointResponse` model + field to `TicketResponse`

**Analog:** `src/a2a_vs_mcp/api_schemas.py`, lines 38–61 (Phase 2 `TraceEventResponse` additions) and lines 28–35 (`TicketResponse`)

**Pattern for adding a new typed Pydantic model before a dependent model** (lines 38–61 as precedent):
```python
class TraceEventResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    index: int
    event_type: str
    # ...optional typed fields with | None = None...
    step_index: int | None = None
    phase: str | None = None
    parallel_batch_id: str | None = None
    started_at: int | None = None
    completed_at: int | None = None
```

**New model to insert before `TicketResponse`** (lines 28–35):
```python
class TalkingPointResponse(BaseModel):
    headline: str
    sentence: str
    callout: str
```

**Existing `TicketResponse`** (lines 28–35):
```python
class TicketResponse(BaseModel):
    ticket_id: str
    customer_id: str
    query: str
    scenario: str
    title: str | None = ""
    difficulty: str | None = "standard"
    tags: list[str] = Field(default_factory=list)
```

**Field to append to `TicketResponse`:**
```python
    tags: list[str] = Field(default_factory=list)
    talking_point: TalkingPointResponse | None = None
```

**Note:** `RunResultResponse` (lines 77–89) already contains `ticket: TicketResponse` — no top-level field needed on `RunResultResponse`. The field reaches the frontend via `ticket.talking_point`.

---

### `src/a2a_vs_mcp/dataset.py` — extend `load_scenarios()` with `talking_point`

**Analog:** `src/a2a_vs_mcp/dataset.py`, lines 105–118 (existing `load_scenarios()`)

**Existing constructor call** (lines 107–117):
```python
return {
    item["scenario"]: SupportTicket(
        ticket_id=item["ticket_id"],
        customer_id=item["customer_id"],
        query=item["query"],
        scenario=item["scenario"],
        title=item.get("title", item["scenario"].replace("_", " ").title()),
        difficulty=item.get("difficulty", "standard"),
        tags=item.get("tags", []),
    )
    for item in payload
}
```

**Change:** Add one keyword argument after `tags=`:
```python
        tags=item.get("tags", []),
        talking_point=item.get("talking_point"),
```

**Pattern note:** All optional seed fields use `item.get(key)` — not `item.get(key, default)` — when `None` is the correct default (matches new `SupportTicket.talking_point: dict | None = None`).

---

### `src/a2a_vs_mcp/agents/triage.py` — parallel dispatch branch + `_resolve_parallel()`

**Analog:** `src/a2a_vs_mcp/agents/triage.py` — full file (98 lines)

**Tag-check branch insertion point** — top of `resolve_with_broker()`, BEFORE `intent = self.classify(ticket)` (line 17):
```python
def resolve_with_broker(self, ticket: SupportTicket, broker: A2ABroker) -> AgentResult:
    if "parallel_investigation" in ticket.tags:
        return self._resolve_parallel(ticket, broker)
    intent = self.classify(ticket)
    # ... existing sequential flow unchanged ...
```

**`_request_specialist()` as structural template for `_resolve_parallel()`** (lines 43–59):
```python
def _request_specialist(self, ticket: SupportTicket, broker: A2ABroker, capability: str) -> AgentResult | None:
    try:
        card = broker.find_by_capability(capability)
        payload = {"ticket": asdict(ticket)}
        if self.context.failure_config.malformed_task and capability == "policy_billing":
            payload = {"broken": True}
        return broker.send_task(
            self.new_task_message(card.agent_id, capability, payload, task_id=ticket.ticket_id)
        )
    except Exception as exc:
        self.context.trace.record(
            "triage_warning",
            capability=capability,
            error=str(exc),
            ticket_id=ticket.ticket_id,
        )
        return None
```

**`triage_merge` trace.record pattern** (lines 35–40) — reused in `_resolve_parallel()`:
```python
self.context.trace.record(
    "triage_merge",
    ticket_id=ticket.ticket_id,
    contributors=[result.agent_id for result in results],
    final_answer=final_answer,
)
```

**New `_resolve_parallel()` method — copy from `_request_specialist()` structure, calling `broker.send_tasks_parallel()` instead of `broker.send_task()`:**
```python
def _resolve_parallel(self, ticket: SupportTicket, broker: A2ABroker) -> AgentResult:
    self.context.trace.record("agent_reasoning", agent=self.agent_id, issue_type="parallel_investigation")
    capabilities = ["customer_data", "documentation", "policy_billing"]
    messages = [
        self.new_task_message(
            broker.find_by_capability(cap).agent_id, cap,
            {"ticket": asdict(ticket)}, task_id=ticket.ticket_id
        )
        for cap in capabilities
    ]
    results = broker.send_tasks_parallel(messages)
    merged_details = {r.agent_id: r.details for r in results}
    final_answer = self._merge(ticket, results, "parallel_investigation")
    self.context.trace.record(
        "triage_merge",
        ticket_id=ticket.ticket_id,
        contributors=[r.agent_id for r in results],
        final_answer=final_answer,
    )
    return AgentResult(agent_id=self.agent_id, summary=final_answer, details=merged_details)
```

**Imports already present** (lines 1–8) — `asdict` is already imported; no new imports needed:
```python
from __future__ import annotations

from dataclasses import asdict
from typing import Any

from ..a2a.broker import A2ABroker
from ..schemas import AgentResult, SupportTicket
from .base import BaseAgent
```

---

### `src/a2a_vs_mcp/data/seeds/scenarios.json` — add 2 entries + `talking_point` on all 12

**Analog:** `src/a2a_vs_mcp/data/seeds/scenarios.json`, lines 1–60 (existing entries)

**Existing entry shape** (lines 38–46, `delay_and_billing` as multi-step example):
```json
{
  "scenario": "delay_and_billing",
  "ticket_id": "TICKET-1005",
  "customer_id": "CUST-002",
  "title": "Delay and Billing Escalation",
  "difficulty": "standard",
  "tags": ["billing", "delivery", "multi-step"],
  "query": "My order ORD-1002 was delayed and I was charged twice. I need both the payment review and delivery explanation."
}
```

**New field pattern** — add `talking_point` object to every entry:
```json
{
  "scenario": "order_status",
  "ticket_id": "TICKET-1001",
  "customer_id": "CUST-001",
  "title": "Shipment Status Check",
  "difficulty": "starter",
  "tags": ["order", "status"],
  "query": "Where is my order ORD-1001? I need the latest delivery status.",
  "talking_point": {
    "headline": "...",
    "sentence": "...",
    "callout": "..."
  }
}
```

**New TICKET-1011** (SCEN-01 — `device_failure_warranty_refund`, CUST-001, advanced, multi-step, no `parallel_investigation` tag):
```json
{
  "scenario": "device_failure_warranty_refund",
  "ticket_id": "TICKET-1011",
  "customer_id": "CUST-001",
  "title": "Device Failure: Warranty + Refund",
  "difficulty": "advanced",
  "tags": ["warranty", "troubleshooting", "policy", "multi-step"],
  "query": "My SmartHome Hub failed after 6 months — it's still under warranty but I want a refund, not a replacement. Can you check my order history, find the troubleshooting steps, and confirm what your return policy covers?",
  "talking_point": {
    "headline": "Three agents, one chained investigation",
    "sentence": "MCP makes 4 sequential tool calls; A2A hands off across 3 specialists — same result, visible protocol difference.",
    "callout": "Watch step_index climb in the trace."
  }
}
```

**New TICKET-1012** (SCEN-02 — `vip_parallel_escalation`, CUST-003, advanced, `parallel_investigation` tag triggers new branch):
```json
{
  "scenario": "vip_parallel_escalation",
  "ticket_id": "TICKET-1012",
  "customer_id": "CUST-003",
  "title": "VIP Parallel Escalation",
  "difficulty": "advanced",
  "tags": ["enterprise", "parallel_investigation", "escalation"],
  "query": "This is an urgent VIP escalation. Our enterprise account is experiencing a critical issue — I need an immediate full investigation across order status, documentation, and billing simultaneously. Please escalate to all specialists at once.",
  "talking_point": {
    "headline": "Three specialists, one simultaneous dispatch",
    "sentence": "A2A sends all three specialists at once; MCP calls tools one by one — the swimlane shows the difference instantly.",
    "callout": "Overlapping timestamps in the trace = parallel execution."
  }
}
```

**DB rebuild:** `DemoRepository._ensure_sqlite()` uses SHA-256 of all seed files — adding entries triggers automatic rebuild on next run. No migration needed.

---

### `src/a2a_vs_mcp/data/seeds/warranties.json` — add WAR-7004

**Analog:** `src/a2a_vs_mcp/data/seeds/warranties.json`, lines 1–22 (existing 3 records)

**Existing entry shape** (lines 2–8):
```json
{
  "warranty_id": "WAR-7001",
  "customer_id": "CUST-002",
  "product": "HomeSensor Pro",
  "expires_on": "2027-03-29",
  "coverage": "standard"
}
```

**New entry to append** (WAR-7004 for CUST-001 / SmartHub Mini — required for SCEN-01 warranty lookup):
```json
{
  "warranty_id": "WAR-7004",
  "customer_id": "CUST-001",
  "product": "SmartHub Mini",
  "expires_on": "2027-04-01",
  "coverage": "premium"
}
```

---

### `frontend/src/lib/types/api.generated.ts` — add `TalkingPointCard` interface + field to `TicketResponse`

**Analog:** `frontend/src/lib/types/api.generated.ts`, lines 283–305 (`TraceEventResponse` Phase 2 manual patch)

**Phase 2 manual-patch comment pattern** (lines 297–305):
```typescript
  // Phase 2 enrichment fields (manually patched — re-running generator will also include these after api_schemas.py is updated)
  step_index?: number | null;
  phase?: "discovery" | "execution" | null;
  parallel_batch_id?: string | null;
  started_at?: number | null;
  completed_at?: number | null;
  [key: string]: unknown;
```

**Existing `TicketResponse`** (lines 273–281):
```typescript
export interface TicketResponse {
  ticket_id: string;
  customer_id: string;
  query: string;
  scenario: string;
  title?: string | null;
  difficulty?: string | null;
  tags?: Array<string>;
}
```

**New interface to insert before `TicketResponse`** (follow same placement as model ordering in `api_schemas.py`):
```typescript
export interface TalkingPointCard {
  headline: string;
  sentence: string;
  callout: string;
}
```

**Field to append to `TicketResponse`** (Phase 3 manual patch, same comment style as Phase 2):
```typescript
export interface TicketResponse {
  ticket_id: string;
  customer_id: string;
  query: string;
  scenario: string;
  title?: string | null;
  difficulty?: string | null;
  tags?: Array<string>;
  // Phase 3: per-scenario talking point for presenter card (manually patched)
  talking_point?: TalkingPointCard | null;
}
```

**`RunResultResponse`** (lines 235–247) already contains `ticket: TicketResponse` — no change needed there.

---

### `frontend/src/features/run-workspace/RunWorkspacePage.tsx` — `Paper` import + TalkingPointCard render

**Analog:** `frontend/src/features/run-workspace/RunWorkspacePage.tsx`

**Existing MUI import block** (lines 1–21) — `Paper` is NOT present:
```tsx
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControl,
  FormControlLabel,
  Grid,
  InputLabel,
  MenuItem,
  Select,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
```

**Change:** Add `Paper` to this import block (alphabetical order, between `MenuItem` and `Select`):
```tsx
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  Divider,
  FormControl,
  FormControlLabel,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Stack,
  Switch,
  TextField,
  Typography,
} from "@mui/material";
```

**Existing result card map** (lines 854–886) — TalkingPointCard inserts inside `<Stack spacing={1.25}>` after the metric chips `<Stack>` (after line 885), before `</Stack>` closing `spacing={1.25}`:
```tsx
{result.results.map((item) => (
  <Grid key={item.mode} size={{ xs: 12, md: 6 }}>
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Stack spacing={1.25}>
          {/* ... mode header, final_answer, Divider ... */}
          <Stack direction="row" spacing={1} useFlexGap flexWrap="wrap">
            {/* metric chips */}
          </Stack>
          {/* INSERT TalkingPointCard HERE */}
        </Stack>
      </CardContent>
    </Card>
  </Grid>
))}
```

**Protocol color map** — define as a `const` above (or inside) the component. No external import needed:
```tsx
const protocolColor: Record<string, string> = {
  mcp: "#1976d2",
  a2a: "#7b1fa2",
  hybrid: "#2e7d32",
  baseline: "#757575",
};
```

**TalkingPointCard JSX to insert** (uses `Paper elevation={0}` to visually distinguish from outer `Card variant="outlined"`):
```tsx
{item.ticket.talking_point ? (
  <Paper
    elevation={0}
    sx={{
      borderLeft: `4px solid ${protocolColor[item.mode] ?? "#757575"}`,
      bgcolor: "action.hover",
      p: 1.5,
    }}
  >
    <Typography variant="subtitle2" fontWeight="bold">
      {item.ticket.talking_point.headline}
    </Typography>
    <Typography variant="body2" sx={{ mt: 0.5 }}>
      {item.ticket.talking_point.sentence}
    </Typography>
    <Typography variant="body2" sx={{ mt: 0.5, fontStyle: "italic", color: "text.secondary" }}>
      {item.ticket.talking_point.callout}
    </Typography>
  </Paper>
) : null}
```

**`Paper` usage reference** — the only existing `Paper` usage in the frontend is in `frontend/src/components/traces/ProtocolEnvelopeDrawer.tsx`, which does NOT import `Paper` (it uses `Box`, `Stack`, `Chip`, etc.). There is no existing `Paper` import pattern to copy from — add fresh per the MUI import convention in RunWorkspacePage.tsx.

---

### `tests/test_demo_modes.py` — SCEN-01, SCEN-02, SCEN-03 test methods

**Analog:** `tests/test_demo_modes.py`

**Class setup pattern** (lines 38–41) — tests use `self.platform` via `setUp`:
```python
class DemoModeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.platform = DemoPlatform(PROJECT_ROOT, runtime="mock")
```

**`get_ticket()` + `run()` pattern** (lines 52–57):
```python
def test_all_modes_return_answers(self) -> None:
    ticket = self.platform.get_ticket("order_status", None, None)
    for mode in ("baseline", "mcp", "a2a", "hybrid"):
        result = self.platform.run(mode, ticket)
        self.assertTrue(result.final_answer)
        self.assertEqual(result.metrics.mode, mode)
```

**Trace event filtering pattern** (lines 206–207):
```python
tool_call_events = [e for e in result.trace if e["event_type"] == "tool_call"]
self.assertGreater(len(tool_call_events), 0, "Expected at least one tool_call event in mcp mode")
```

**Parallel batch_id assertion pattern** (lines 266–273 from `test_send_tasks_parallel_emits_batch_fields`):
```python
submit_events = [e for e in trace.events if e["event_type"] == "task_submit"]
batch_ids = {e["parallel_batch_id"] for e in submit_events}
self.assertEqual(len(batch_ids), 1, "All task_submit events must share the same parallel_batch_id")
batch_id = batch_ids.pop()
self.assertEqual(len(batch_id), 12, f"parallel_batch_id must be 12 hex chars, got: {batch_id!r}")
```

**Multi-step scenario pattern** (lines 317–322):
```python
def test_multi_step_scenario_mentions_multiple_concerns(self) -> None:
    ticket = self.platform.get_ticket("delay_and_billing", None, None)
    result = self.platform.run("hybrid", ticket)
    self.assertIn("duplicate-charge", result.final_answer)
```

**New test methods to add** — all go inside `DemoModeTests`, following the existing method conventions. Use `self.platform.get_ticket()` + `self.platform.run()` (not a separate `platform` local — stays consistent with the class pattern):

```python
# SCEN-01: multi-step — all 3 specialists called sequentially (a2a mode)
def test_scen01_multi_step_triggers_all_specialists(self) -> None:
    ticket = self.platform.get_ticket("device_failure_warranty_refund", None, None)
    result = self.platform.run("a2a", ticket)
    task_submits = [e for e in result.trace if e["event_type"] == "task_submit"]
    self.assertGreaterEqual(len(task_submits), 3)

# SCEN-01: MCP mode makes 4+ sequential tool calls
def test_scen01_mcp_mode_makes_sequential_tool_calls(self) -> None:
    ticket = self.platform.get_ticket("device_failure_warranty_refund", None, None)
    result = self.platform.run("mcp", ticket)
    tool_calls = [e for e in result.trace if e["event_type"] == "tool_call"]
    self.assertGreaterEqual(len(tool_calls), 4)

# SCEN-02: parallel — all task_submit events share one batch_id
def test_scen02_parallel_emits_shared_batch_id(self) -> None:
    ticket = self.platform.get_ticket("vip_parallel_escalation", None, None)
    result = self.platform.run("a2a", ticket)
    submits = [e for e in result.trace if e["event_type"] == "task_submit"]
    batch_ids = {e.get("parallel_batch_id") for e in submits}
    self.assertEqual(len(batch_ids), 1)
    self.assertIsNotNone(list(batch_ids)[0])

# SCEN-02: no task_failed events under mock runtime
def test_scen02_parallel_produces_no_failures(self) -> None:
    ticket = self.platform.get_ticket("vip_parallel_escalation", None, None)
    result = self.platform.run("a2a", ticket)
    failures = [e for e in result.trace if e["event_type"] == "task_failed"]
    self.assertEqual(len(failures), 0)

# SCEN-03: talking_point loaded from seed onto ticket object
def test_scen03_talking_point_on_ticket(self) -> None:
    ticket = self.platform.get_ticket("device_failure_warranty_refund", None, None)
    self.assertIsNotNone(ticket.talking_point)
    self.assertIn("headline", ticket.talking_point)
    self.assertIn("sentence", ticket.talking_point)
    self.assertIn("callout", ticket.talking_point)
```

**Note on `get_ticket()` vs `load_scenarios()`:** Tests use `self.platform.get_ticket(scenario, None, None)` — this resolves to `DemoRepository.load_scenarios()` internally. The SCEN-03 test can also directly check `self.platform.repo.load_scenarios()["device_failure_warranty_refund"].talking_point` if `get_ticket()` does not expose the raw `SupportTicket`. Confirm which surface `get_ticket()` returns.

---

## Shared Patterns

### Dataclass field-with-default ordering
**Source:** `src/a2a_vs_mcp/schemas.py`, lines 17–26
**Apply to:** `schemas.py` change
All fields with defaults (`scenario`, `title`, `difficulty`, `tags`) must follow the three positional fields (`ticket_id`, `customer_id`, `query`). New `talking_point: dict | None = None` appends safely after `tags`.

### Pydantic `BaseModel` with `Field(default_factory=list)` for collections, `| None = None` for optionals
**Source:** `src/a2a_vs_mcp/api_schemas.py`, lines 28–35 and 64–89
**Apply to:** `TalkingPointResponse` (no optional fields — all required `str`) and `TicketResponse` addition (`talking_point: TalkingPointResponse | None = None`)

### `item.get(key)` for optional seed fields in `load_scenarios()`
**Source:** `src/a2a_vs_mcp/dataset.py`, lines 112–116
**Apply to:** `dataset.py` change — use `item.get("talking_point")` (returns `None` if absent, matching the field default)

### Trace event filtering with list comprehension
**Source:** `tests/test_demo_modes.py`, lines 206–207, 266–267
**Apply to:** All new test methods — filter `result.trace` (list of dicts) by `e["event_type"]` key

### Manual TypeScript patch comment
**Source:** `frontend/src/lib/types/api.generated.ts`, line 298
**Apply to:** `api.generated.ts` change — annotate new fields with `// Phase 3: ...` comment matching Phase 2 style

### MUI import block — alphabetical, single `from "@mui/material"` import
**Source:** `frontend/src/features/run-workspace/RunWorkspacePage.tsx`, lines 3–21
**Apply to:** `Paper` insertion — slot between `MenuItem` and `Select` alphabetically

---

## No Analog Found

All 9 files have direct analogs in the codebase. No file requires falling back to RESEARCH.md patterns only.

| File | Note |
|------|------|
| `frontend/src/features/run-workspace/RunWorkspacePage.tsx` (`Paper`) | `Paper` is not imported anywhere in the frontend currently — use MUI docs default (`elevation={0}`) as specified in RESEARCH.md §2f |

---

## Metadata

**Analog search scope:** `src/a2a_vs_mcp/`, `tests/`, `frontend/src/`
**Files scanned:** 9 source files read directly; `ProtocolEnvelopeDrawer.tsx` scanned for Paper usage
**Pattern extraction date:** 2026-04-23
