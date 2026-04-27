# Phase 3: New Scenarios — Research

**Written:** 2026-04-23
**Phase:** 3 — New Scenarios
**Requirements:** SCEN-01, SCEN-02, SCEN-03

---

## 1. Current State Analysis

### TriageAgent (`src/a2a_vs_mcp/agents/triage.py`)

`resolve_with_broker()` uses intent-based sequential routing. Key structure:

```python
def resolve_with_broker(self, ticket: SupportTicket, broker: A2ABroker) -> AgentResult:
    intent = self.classify(ticket)
    results: list[AgentResult] = []
    if intent.needs_data or intent.issue_type in {"order_status", "billing", "warranty_return"}:
        result = self._request_specialist(ticket, broker, "customer_data")
        ...
    if intent.needs_docs:
        result = self._request_specialist(ticket, broker, "documentation")
        ...
    if intent.needs_policy or intent.issue_type in {"billing", "warranty_return"}:
        result = self._request_specialist(ticket, broker, "policy_billing")
        ...
    return AgentResult(...)
```

**Parallel branch insertion point:** Add a tag check at the top of `resolve_with_broker()`, BEFORE the intent classification block. If `"parallel_investigation"` in `ticket.tags`, call `send_tasks_parallel()` with all 3 capability messages and return. Otherwise fall through to existing sequential flow unchanged.

### A2ABroker.send_tasks_parallel() (`src/a2a_vs_mcp/a2a/broker.py`)

Already implemented in Phase 2. Signature:

```python
def send_tasks_parallel(self, messages: list[A2AMessage]) -> list[AgentResult]:
```

- Takes a list of `A2AMessage` objects
- Dispatches via `ThreadPoolExecutor(max_workers=len(messages))`
- Records `task_submit` event per message with `parallel_batch_id`, `started_at`
- Returns `list[AgentResult]` in submission order
- Worker `_run_parallel_task()` records `task_complete` with `completed_at`

**To construct messages:** TriageAgent already has `self.new_task_message(card.agent_id, capability, payload, task_id=ticket.ticket_id)`. The parallel branch needs to build 3 messages (one per specialist) and pass them to `send_tasks_parallel()`.

### SupportTicket and RunOutput (`src/a2a_vs_mcp/schemas.py`)

Current `SupportTicket` fields:
```python
ticket_id: str
customer_id: str
query: str
scenario: str = "custom"
title: str = ""
difficulty: str = "standard"
tags: list[str] = field(default_factory=list)
```

**No `talking_point` field yet.** Must add `talking_point: dict | None = None`.

`RunOutput` does NOT embed `SupportTicket` fields directly — it holds `ticket: SupportTicket`. So `talking_point` on `SupportTicket` propagates through `RunOutput.ticket.talking_point` automatically via `asdict()`.

### API Schemas (`src/a2a_vs_mcp/api_schemas.py`)

`TicketResponse` (nested in `RunResultResponse`):
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

`RunResultResponse` fields: `mode`, `runtime`, `ticket: TicketResponse`, `final_answer`, `metrics`, `tools_used`, `agents_used`, `failures`, `trace`, `external_log_path`, `a2a_transport`, `mcp_transport`.

**No `talking_point` field yet.** Must add to both `TicketResponse` and/or `RunResultResponse`.

**Design choice (Claude's discretion per CONTEXT.md):** Add `talking_point: dict | None = None` to `TicketResponse` (since it comes from the ticket seed). This flows through the existing `ticket` field in `RunResultResponse` without requiring a new top-level field. Alternatively a typed `TalkingPointResponse` model avoids raw `dict`.

### DemoRepository.load_scenarios() (`src/a2a_vs_mcp/dataset.py`)

```python
def load_scenarios(self) -> dict[str, SupportTicket]:
    payload = self._load_seed("scenarios")
    return {
        item["scenario"]: SupportTicket(
            ticket_id=item["ticket_id"],
            customer_id=item["customer_id"],
            query=item["query"],
            scenario=item["scenario"],
            title=item.get("title", ...),
            difficulty=item.get("difficulty", "standard"),
            tags=item.get("tags", []),
        )
        for item in payload
    }
```

**Extension:** Add `talking_point=item.get("talking_point")` to the `SupportTicket(...)` constructor call. One-line change.

### scenarios.json — 10 Existing Scenarios

All entries have: `scenario`, `ticket_id`, `customer_id`, `title`, `difficulty`, `tags`, `query`. **None have `talking_point` yet.**

| scenario | ticket_id | customer_id | difficulty | key tags |
|----------|-----------|-------------|------------|----------|
| order_status | TICKET-1001 | CUST-001 | starter | order, status |
| double_charge | TICKET-1002 | CUST-002 | starter | billing, payments |
| setup_error | TICKET-1003 | CUST-001 | starter | troubleshooting, docs |
| warranty_return | TICKET-1004 | CUST-002 | standard | warranty, policy |
| delay_and_billing | TICKET-1005 | CUST-002 | standard | billing, delivery, multi-step |
| setup_and_warranty | TICKET-1006 | CUST-002 | standard | troubleshooting, warranty, multi-step |
| expired_return_active_warranty | TICKET-1007 | CUST-002 | standard | policy, warranty, edge-case |
| enterprise_delay_refund | TICKET-1008 | CUST-003 | advanced | delivery, billing, enterprise |
| enterprise_setup_replacement | TICKET-1009 | CUST-003 | advanced | troubleshooting, warranty, enterprise |
| invoice_and_warranty_followup | TICKET-1010 | CUST-004 | advanced | billing, warranty, history |

Next available ticket IDs: **TICKET-1011** (SCEN-01) and **TICKET-1012** (SCEN-02).

### Frontend — RunWorkspacePage.tsx (918 lines)

Result rendering at lines 854–890:
```tsx
{result.results.map((item) => (
  <Grid key={item.mode} size={{ xs: 12, md: 6 }}>
    <Card variant="outlined" sx={{ height: "100%" }}>
      <CardContent>
        <Stack spacing={1.25}>
          <Stack direction="row" ...>
            <Typography variant="h6">{item.mode.toUpperCase()}</Typography>
            <Chip label={`${item.metrics.latency_ms} ms`} .../>
          </Stack>
          <Typography variant="body2">{item.final_answer}</Typography>
          <Divider />
          <Stack direction="row" ...> {/* metric chips */} </Stack>
        </Stack>
      </CardContent>
    </Card>
  </Grid>
))}
```

**TalkingPointCard insertion point:** Inside the `<Stack spacing={1.25}>` AFTER the metric chips `<Stack>`, still inside `<CardContent>`. If `item.ticket.talking_point` is non-null, render the card. Uses `Paper` (not `Card`) to visually distinguish from the outer card.

`Paper` is NOT currently imported in RunWorkspacePage.tsx — must add it to the MUI import block.

### api.generated.ts — RunResultResponse (line 235)

```typescript
export interface RunResultResponse {
  mode: string;
  runtime: string;
  ticket: TicketResponse;  // <-- talking_point goes here
  final_answer: string;
  metrics: ComparisonMetricsResponse;
  tools_used: Array<string>;
  agents_used: Array<string>;
  failures?: Array<string>;
  trace: Array<TraceEventResponse>;
  external_log_path?: string | null;
  a2a_transport?: string;
  // mcp_transport missing — also needs addition
}
```

`TicketResponse` (lines approx 160–170) needs `talking_point?: TalkingPointCard | null`.

New interface needed:
```typescript
export interface TalkingPointCard {
  headline: string;
  sentence: string;
  callout: string;
}
```

---

## 2. Integration Points

### 2a. TriageAgent parallel dispatch branch

**File:** `src/a2a_vs_mcp/agents/triage.py`
**Method:** `resolve_with_broker()`
**Insertion:** At top, before `intent = self.classify(ticket)`:

```python
if "parallel_investigation" in ticket.tags:
    return self._resolve_parallel(ticket, broker)
```

**New private method** `_resolve_parallel(ticket, broker)`:
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

### 2b. SupportTicket schema extension

**File:** `src/a2a_vs_mcp/schemas.py`
**Change:** Add one field to `SupportTicket`:
```python
talking_point: dict | None = None
```
Must come after `tags` (fields with defaults must follow fields without defaults, but all existing fields already have defaults except `ticket_id`, `customer_id`, `query`).

### 2c. scenarios.json additions

**Two new entries** (append after TICKET-1010):

**TICKET-1011** (SCEN-01 — multi-step):
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

Note: CUST-001 (Aisha Verma, premium) has ORD-1001 (SmartHub Mini, In transit). No warranty for CUST-001 yet — **need a new warranty seed entry** for this scenario to fully exercise the warranty lookup path. Add `WAR-7004` for CUST-001/SmartHub Mini.

**TICKET-1012** (SCEN-02 — parallel):
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

CUST-003 (Mina Patel, enterprise) has ORD-1003 (delayed SmartHub Mini) and ORD-1004 (delivered HomeSensor Pro), warranty WAR-7002. Rich existing data — no new seed records needed.

**All 10 existing entries** also need `talking_point` objects added. These are editorial content (non-blocking for core function).

### 2d. DemoRepository.load_scenarios() extension

**File:** `src/a2a_vs_mcp/dataset.py`
**Change:** One line in the `SupportTicket(...)` constructor:
```python
talking_point=item.get("talking_point"),
```

### 2e. api_schemas.py extension

**File:** `src/a2a_vs_mcp/api_schemas.py`
**Changes:**
1. Add new Pydantic model (before `TicketResponse`):
```python
class TalkingPointResponse(BaseModel):
    headline: str
    sentence: str
    callout: str
```
2. Add field to `TicketResponse`:
```python
talking_point: TalkingPointResponse | None = None
```

`RunResultResponse` gets `talking_point` for free via `ticket.talking_point` — no top-level field needed.

### 2f. Frontend RunWorkspacePage.tsx — TalkingPointCard

**File:** `frontend/src/features/run-workspace/RunWorkspacePage.tsx`
**Changes:**
1. Add `Paper` to MUI imports (line 2–21 import block)
2. Define `TalkingPointCard` component inline above the main component, or inline JSX inside the map:

Protocol color map (hardcode for now — Phase 4 introduces `eventColors.ts`):
```tsx
const protocolColor: Record<string, string> = {
  mcp: "#1976d2",      // MUI blue
  a2a: "#7b1fa2",      // MUI purple
  hybrid: "#2e7d32",   // MUI green
  baseline: "#757575", // MUI grey
};
```

**Insertion inside the `result.results.map()` block**, after the metric chips `<Stack>` (after line 885, before `</Stack>` closing `spacing={1.25}`):
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

### 2g. api.generated.ts extension

**File:** `frontend/src/lib/types/api.generated.ts`
**Changes:**
1. Add new interface (near `TicketResponse`):
```typescript
export interface TalkingPointCard {
  headline: string;
  sentence: string;
  callout: string;
}
```
2. Add field to `TicketResponse`:
```typescript
talking_point?: TalkingPointCard | null;
```

`RunResultResponse` already has `ticket: TicketResponse` — no change needed there.

---

## 3. Data Layer

### SQLite Seed Coverage for New Scenarios

**SCEN-01 (CUST-001 / device_failure_warranty_refund):**
- Customer: CUST-001 (Aisha Verma, premium) ✓ exists
- Order: ORD-1001 (SmartHub Mini) ✓ exists
- Warranty: **MISSING** — no warranty for CUST-001 in `warranties.json`
- Fix: Add `WAR-7004` entry: `{ "warranty_id": "WAR-7004", "customer_id": "CUST-001", "product": "SmartHub Mini", "expires_on": "2027-04-01", "coverage": "premium" }`

**SCEN-02 (CUST-003 / vip_parallel_escalation):**
- Customer: CUST-003 (Mina Patel, enterprise) ✓ exists
- Orders: ORD-1003 (delayed), ORD-1004 (delivered) ✓ exist
- Warranty: WAR-7002 (HomeSensor Pro, premium) ✓ exists
- No new seed records needed.

### DB Rebuild Trigger
`DemoRepository._ensure_sqlite()` uses SHA-256 hashes of all seed files to detect changes. Adding records to `warranties.json` and `scenarios.json` will trigger automatic DB rebuild on next run — no manual migration needed.

---

## 4. Test Patterns

From `tests/test_demo_modes.py`, existing scenario tests follow this pattern:

```python
def test_multi_step_scenario_mentions_multiple_concerns(self) -> None:
    platform = DemoPlatform(self.repo, failure_config=FailureConfig())
    results = platform.run(self.tickets["delay_and_billing"], modes=["a2a"])
    self.assertIn("a2a", results)
    self.assertGreater(len(results["a2a"].trace), 0)
```

**New tests for Phase 3:**

```python
# SCEN-01: Multi-step — all 3 specialists called sequentially
def test_scen01_multi_step_triggers_all_specialists(self) -> None:
    results = platform.run(self.tickets["device_failure_warranty_refund"], modes=["a2a"])
    task_submits = [e for e in results["a2a"].trace if e["event_type"] == "task_submit"]
    self.assertGreaterEqual(len(task_submits), 3)

# SCEN-01: MCP mode 4 sequential tool calls
def test_scen01_mcp_mode_makes_sequential_tool_calls(self) -> None:
    results = platform.run(self.tickets["device_failure_warranty_refund"], modes=["mcp"])
    tool_calls = [e for e in results["mcp"].trace if e["event_type"] == "tool_call"]
    self.assertGreaterEqual(len(tool_calls), 4)

# SCEN-02: Parallel — batch_id shared across all 3 task_submit events
def test_scen02_parallel_emits_shared_batch_id(self) -> None:
    results = platform.run(self.tickets["vip_parallel_escalation"], modes=["a2a"])
    submits = [e for e in results["a2a"].trace if e["event_type"] == "task_submit"]
    batch_ids = {e.get("parallel_batch_id") for e in submits}
    self.assertEqual(len(batch_ids), 1)
    self.assertIsNotNone(list(batch_ids)[0])

# SCEN-02: No task_failed events under mock
def test_scen02_parallel_produces_no_failures(self) -> None:
    results = platform.run(self.tickets["vip_parallel_escalation"], modes=["a2a"])
    failures = [e for e in results["a2a"].trace if e["event_type"] == "task_failed"]
    self.assertEqual(len(failures), 0)

# SCEN-03: talking_point on ticket
def test_scen03_talking_point_on_ticket(self) -> None:
    ticket = self.tickets["device_failure_warranty_refund"]
    self.assertIsNotNone(ticket.talking_point)
    self.assertIn("headline", ticket.talking_point)
    self.assertIn("sentence", ticket.talking_point)
    self.assertIn("callout", ticket.talking_point)
```

Test fixture setup — `self.tickets` is loaded once from `DemoRepository.load_scenarios()`:
```python
@classmethod
def setUpClass(cls) -> None:
    cls.repo = DemoRepository(PROJECT_ROOT)
    cls.tickets = cls.repo.load_scenarios()
```

---

## 5. Implementation Wave Grouping

### Wave 1 — Backend (can run fully in parallel: 3 independent plans)

**Plan 03-01:** Seed data + schema extensions
- Add `talking_point` to `SupportTicket` dataclass (`schemas.py`)
- Add `TalkingPointResponse` model + field to `TicketResponse` (`api_schemas.py`)
- Extend `DemoRepository.load_scenarios()` with `talking_point` (`dataset.py`)
- Add WAR-7004 to `warranties.json`
- Add TICKET-1011 and TICKET-1012 to `scenarios.json` (with `talking_point` objects)
- Add `talking_point` objects to all 10 existing scenario entries
- Write pytest tests for SCEN-03 (talking_point presence)

**Plan 03-02:** TriageAgent parallel dispatch (SCEN-02 backend)
- Add `_resolve_parallel()` method to `TriageAgent`
- Add tag-check branch in `resolve_with_broker()`
- Write pytest tests for SCEN-02 (batch_id shared, no failures, parallel emits timing)

**Plan 03-03:** SCEN-01 pytest validation
- Write pytest tests for SCEN-01 (3+ task_submit in a2a, 4+ tool_calls in mcp)
- These tests verify the existing multi-step routing works for the new ticket without code changes (multi-step routing already exists; device_failure ticket just exercises all 3 intent branches)

### Wave 2 — Frontend (depends on Wave 1 backend changes being present)

**Plan 03-04:** Frontend types + TalkingPointCard UI
- Add `TalkingPointCard` interface + `talking_point` field to `TicketResponse` in `api.generated.ts`
- Add `Paper` to MUI imports in `RunWorkspacePage.tsx`
- Add `protocolColor` map and `TalkingPointCard` render inside `result.results.map()`

---

## 6. Risks and Landmines

### Risk 1: SCEN-01 multi-step routing may not trigger all 3 specialists
The device_failure_warranty_refund ticket needs `needs_data`, `needs_docs`, AND `needs_policy` all true from `TriageAgent.classify()`. The `issue_type` must land on `"warranty_return"` which explicitly triggers `customer_data` and `policy_billing`. The `needs_docs` flag depends on the reasoner's classification of the query. **Under mock runtime**, `MockReasoner` returns canned intent — check if it returns `needs_docs=True`. If not, add `"troubleshooting"` or `"docs"` to the ticket tags to force it, or adjust the query wording.

### Risk 2: `asdict(ticket)` with `talking_point=dict` serialization
`dataclasses.asdict()` recursively converts nested dataclasses. Since `talking_point` is a plain `dict` (not a dataclass), `asdict()` will pass it through unchanged — this is correct behavior. No risk here, but verify that Pydantic's `TicketResponse` accepts `dict` input for `talking_point` when constructing from the `RunOutput.to_dict()` payload.

### Risk 3: DB rebuild on seed change may fail if stale .tmp file exists
`_ensure_sqlite()` tries to remove a stale `.tmp` file if present. The `finally` block handles cleanup. Safe — no action needed.

### Risk 4: `api.generated.ts` is manually patched (not auto-generated)
Per STATE.md decision 02-02, this file is manually maintained with a comment documenting the regeneration path. Adding `TalkingPointCard` interface and `talking_point` field follows the same manual-patch pattern. Note that `mcp_transport` is also absent from `RunResultResponse` in `api.generated.ts` even though it's in `api_schemas.py` — Phase 3 only needs to add `talking_point`; leave `mcp_transport` as-is.

### Risk 5: `send_tasks_parallel()` uses real threads — mock runtime must be thread-safe
Phase 2 already verified this works (test `test_send_tasks_parallel_emits_batch_fields` passes). Mock handlers are stateless per call. No additional thread-safety risk for Phase 3.

### Risk 6: `Paper` import missing from RunWorkspacePage.tsx
`Paper` is not in the current MUI import block. Forgetting to add it causes a runtime crash. Include in plan's `acceptance_criteria` that `Paper` appears in the import statement.

### Risk 7: Protocol color for `"all"` mode
When `mode="all"`, results will contain individual mode results (baseline, mcp, a2a, hybrid) — each with its own mode string. The `protocolColor` map covers all four. `"all"` mode itself never appears as `item.mode` in `result.results` — safe.

---

## RESEARCH COMPLETE
