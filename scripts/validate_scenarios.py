from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import argparse
import json
import re


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SEED_DIR = PROJECT_ROOT / "src" / "a2a_vs_mcp" / "data" / "seeds"
ALLOWED_DIFFICULTIES = {"starter", "standard", "advanced"}
SCENARIO_ID_RE = re.compile(r"^[a-z][a-z0-9_]*$")
TICKET_ID_RE = re.compile(r"^TICKET-\d+$")
ORDER_ID_RE = re.compile(r"\bORD-\d+\b")


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    scenario_count: int = 0

    @property
    def ok(self) -> bool:
        return not self.errors


def load_seed(name: str, seed_dir: Path) -> list[dict[str, Any]]:
    path = seed_dir / f"{name}.json"
    return json.loads(path.read_text(encoding="utf-8"))


def validate(seed_dir: Path) -> ValidationResult:
    result = ValidationResult()
    scenarios = load_seed("scenarios", seed_dir)
    customers = {item["customer_id"] for item in load_seed("customers", seed_dir)}
    orders = {item["order_id"]: item for item in load_seed("orders", seed_dir)}
    products = {item["product"] for item in orders.values()}
    warranties = load_seed("warranties", seed_dir)
    warranty_products_by_customer: dict[str, set[str]] = {}
    for warranty in warranties:
        warranty_products_by_customer.setdefault(warranty["customer_id"], set()).add(warranty["product"])

    seen_scenarios: set[str] = set()
    seen_tickets: set[str] = set()
    result.scenario_count = len(scenarios)

    for index, scenario in enumerate(scenarios, start=1):
        label = str(scenario.get("scenario") or f"scenario[{index}]")
        for field_name in ("scenario", "ticket_id", "customer_id", "title", "difficulty", "tags", "query"):
            if field_name not in scenario or scenario[field_name] in ("", None):
                result.errors.append(f"{label}: missing required field '{field_name}'")

        scenario_id = str(scenario.get("scenario", ""))
        ticket_id = str(scenario.get("ticket_id", ""))
        customer_id = str(scenario.get("customer_id", ""))
        query = str(scenario.get("query", ""))
        tags = scenario.get("tags", [])
        difficulty = scenario.get("difficulty", "")

        if scenario_id:
            if scenario_id in seen_scenarios:
                result.errors.append(f"{label}: duplicate scenario id '{scenario_id}'")
            seen_scenarios.add(scenario_id)
            if not SCENARIO_ID_RE.match(scenario_id):
                result.errors.append(f"{label}: scenario id must be snake_case")

        if ticket_id:
            if ticket_id in seen_tickets:
                result.errors.append(f"{label}: duplicate ticket id '{ticket_id}'")
            seen_tickets.add(ticket_id)
            if not TICKET_ID_RE.match(ticket_id):
                result.errors.append(f"{label}: ticket_id must look like TICKET-1001")

        if customer_id and customer_id not in customers:
            result.errors.append(f"{label}: customer_id '{customer_id}' does not exist in customers.json")

        if difficulty and difficulty not in ALLOWED_DIFFICULTIES:
            result.errors.append(f"{label}: difficulty must be one of {', '.join(sorted(ALLOWED_DIFFICULTIES))}")

        if not isinstance(tags, list) or not tags or not all(isinstance(tag, str) and tag for tag in tags):
            result.errors.append(f"{label}: tags must be a non-empty list of strings")

        for order_id in ORDER_ID_RE.findall(query):
            order = orders.get(order_id)
            if order is None:
                result.errors.append(f"{label}: query references unknown order '{order_id}'")
            elif customer_id and order["customer_id"] != customer_id:
                result.errors.append(f"{label}: query references order '{order_id}' for customer '{order['customer_id']}', not '{customer_id}'")

        product_mentions = [product for product in products if product.lower() in query.lower()]
        if "warranty" in query.lower() and customer_id and not product_mentions:
            result.warnings.append(f"{label}: warranty scenario does not mention a known product")
        for product in product_mentions:
            if "warranty" in query.lower() and customer_id and product not in warranty_products_by_customer.get(customer_id, set()):
                result.warnings.append(f"{label}: mentions warranty for '{product}', but no matching warranty fixture exists for '{customer_id}'")

    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate scenario fixtures for the A2A vs MCP demo.")
    parser.add_argument("--seed-dir", type=Path, default=SEED_DIR)
    parser.add_argument("--json", action="store_true", help="Print machine-readable validation results.")
    args = parser.parse_args()
    result = validate(args.seed_dir)
    if args.json:
        print(json.dumps({"ok": result.ok, "scenario_count": result.scenario_count, "errors": result.errors, "warnings": result.warnings}, indent=2))
    else:
        status = "PASS" if result.ok else "FAIL"
        print(f"Scenario validation: {status} ({result.scenario_count} scenarios)")
        for warning in result.warnings:
            print(f"WARN: {warning}")
        for error in result.errors:
            print(f"ERROR: {error}")
    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
