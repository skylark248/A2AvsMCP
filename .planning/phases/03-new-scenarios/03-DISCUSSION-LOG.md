# Phase 3: New Scenarios - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-23
**Phase:** 03-new-scenarios
**Areas discussed:** Multi-step scenario ticket, Parallel scenario design, Talking-point card format, New agents needed?

---

## Multi-step scenario ticket

| Option | Description | Selected |
|--------|-------------|----------|
| Device failure + warranty + refund | Forces all 3 agents: CustomerData (order+warranty) → Documentation (troubleshooting) → PolicyBilling (refund policy) | ✓ |
| Enterprise onboarding + billing dispute | Data + docs + policy but more niche for audience | |
| Multi-product delayed shipment + return | Multiple data lookups + policy but may not trigger docs agent | |

**User's choice:** Device failure + warranty + refund
**Notes:** Guarantees all 3 specialist agents trigger in A2A, 4 sequential MCP tool calls in MCP mode.

---

## MCP chain depth

| Option | Description | Selected |
|--------|-------------|----------|
| Sequential tools: customer → order → docs → policy | 4 explicit MCP tool calls, clear trace | ✓ |
| Add dedicated get_warranty call | 5 tool calls for extra depth | |
| Claude's discretion | Researcher/planner decide | |

**User's choice:** Sequential tools: customer → order → docs → policy

---

## Parallel scenario design

| Option | Description | Selected |
|--------|-------------|----------|
| All 3 specialists in parallel | CustomerData + Documentation + PolicyBilling via send_tasks_parallel() — maximum visual impact | ✓ |
| 2 in parallel (data + docs), policy after | Partial parallelism, less dramatic | |

**User's choice:** All 3 specialists in parallel

---

## Parallel ticket theme

| Option | Description | Selected |
|--------|-------------|----------|
| High-priority escalation with complete parallel investigation | VIP customer, all departments simultaneously — clear narrative: A2A can parallelize, MCP cannot | ✓ |
| Reuse multi-step scenario with parallel-optimized variant | Linked but may blur distinction | |
| New scenario: product recall | Novel context, requires new seed data | |

**User's choice:** High-priority escalation with complete parallel investigation

---

## Talking-point card data location

| Option | Description | Selected |
|--------|-------------|----------|
| In the scenario seed JSON | Static, deterministic, presenter-controlled; loaded with SupportTicket | ✓ |
| Generated dynamically per run | Non-deterministic — out of scope per requirements | |
| Defined per mode in config | More granular but 4x content to maintain | |

**User's choice:** In the scenario seed JSON

---

## Card UI placement

| Option | Description | Selected |
|--------|-------------|----------|
| Below the trace panel, per run result | Always visible after run without expanding anything | ✓ |
| Pinned above the trace panel | First thing seen but competes with result metrics | |
| Collapsible banner at top of RunWorkspacePage | Simpler but loses per-mode specificity | |

**User's choice:** Below the trace panel, per run result

---

## Card MUI style

| Option | Description | Selected |
|--------|-------------|----------|
| MUI Paper with colored left border | Protocol color accent, headline bold, sentence body, callout as italic/Chip | ✓ |
| MUI Alert (info variant) | Quick to implement but all cards look the same | |
| Claude's discretion | Researcher/planner decide | |

**User's choice:** MUI Paper with colored left border

---

## Talking-point card scope

| Option | Description | Selected |
|--------|-------------|----------|
| All scenarios | Every scenario gets a card — complete presenter experience; PRES-01 calls for this in Phase 5 anyway | ✓ |
| New scenarios only | Strictly SCEN-03 scope; existing scenarios get cards in Phase 5 | |

**User's choice:** All scenarios (deliver PRES-01 card content now)

---

## New specialist agents

| Option | Description | Selected |
|--------|-------------|----------|
| No — reuse existing 3 specialists | CustomerData + Documentation + PolicyBilling cover all required steps | ✓ |
| Yes — add EscalationAgent | Adds trace event types but TriageAgent already handles coordination | |

**User's choice:** No new agent classes — reuse existing 3 specialists

---

## Parallel dispatch trigger

| Option | Description | Selected |
|--------|-------------|----------|
| Unconditional for parallel scenario (tag-based) | Detect "parallel_investigation" tag → always send_tasks_parallel() — deterministic for demo | ✓ |
| Intent-driven detection | More realistic but mock intent may not reliably trigger 3 parallel agents | |

**User's choice:** Unconditional tag-based dispatch — TriageAgent checks `ticket.tags` for `"parallel_investigation"`

---

## Claude's Discretion

- Exact ticket_id, customer_id, query wording for both new scenario seed entries
- Synthetic timing offset values for parallel specialist mock execution
- Exact left-border color values for TalkingPointCard (use existing tokens or introduce eventColors.ts early)
- Whether `talking_point` in API response is a typed `TalkingPointCard` model or plain dict

## Deferred Ideas

- EscalationAgent specialist class — not needed
- Intent-driven parallelism — rejected for demo reliability
- Tool discovery scenario (DISC-01/02) — v2 backlog (confirmed at project init)
