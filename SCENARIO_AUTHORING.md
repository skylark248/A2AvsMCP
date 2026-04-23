# Scenario Authoring

Scenarios are designed to be safe to add without editing orchestration code. The runtime loads scenarios from `src/a2a_vs_mcp/data/seeds/scenarios.json`, while supporting customer, order, payment, ticket, and warranty fixtures live beside it.

## Required Fields

Each scenario entry must include:

- `scenario`: stable snake_case ID, for example `enterprise_setup_replacement`
- `ticket_id`: stable demo ticket ID, for example `TICKET-1011`
- `customer_id`: existing customer from `customers.json`
- `title`: human-readable UI label
- `difficulty`: one of `starter`, `standard`, or `advanced`
- `tags`: non-empty list of short labels
- `query`: customer-facing support request

## Fixture Rules

- If the query mentions an `ORD-####` order, that order must exist in `orders.json`.
- The referenced order must belong to the scenario customer.
- If the query asks about warranty behavior, mention a known product when possible.
- If the query mentions warranty for a known product, add or verify a matching warranty fixture for that customer.
- Use tags that make demo filtering useful: `billing`, `delivery`, `warranty`, `troubleshooting`, `enterprise`, `multi-step`, `edge-case`, or similar.

## Validation

Run:

```powershell
py scripts\validate_scenarios.py
```

For machine-readable output:

```powershell
py scripts\validate_scenarios.py --json
```

The validator checks required metadata, ID formats, duplicate IDs, customer references, order references, difficulty values, tags, and warranty/product fixture warnings.

## Authoring Checklist

1. Add or reuse customer, order, payment, ticket, and warranty fixtures.
2. Add the scenario entry to `scenarios.json`.
3. Run `py scripts\validate_scenarios.py`.
4. Smoke test at least `baseline` and the most relevant protocol mode:

```powershell
py main.py --scenario your_scenario --mode baseline
py main.py --scenario your_scenario --mode hybrid
```

5. If the scenario is presentation-worthy, add it to `DEMO_PRESETS.json`.
