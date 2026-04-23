from __future__ import annotations

from contextlib import closing
from pathlib import Path
from typing import Any
import sqlite3


def fetchone(db_path: Path, query: str, params: tuple[Any, ...]) -> dict[str, Any] | None:
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        row = conn.execute(query, params).fetchone()
        return dict(row) if row else None


def fetchall(db_path: Path, query: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:
    with closing(sqlite3.connect(db_path)) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(query, params).fetchall()
        return [dict(row) for row in rows]


def get_customer_profile(db_path: Path, customer_id: str) -> dict[str, Any] | None:
    return fetchone(db_path, "SELECT * FROM customers WHERE customer_id = ?", (customer_id,))


def get_order_history(db_path: Path, customer_id: str) -> list[dict[str, Any]]:
    return fetchall(db_path, "SELECT * FROM orders WHERE customer_id = ?", (customer_id,))


def get_order(db_path: Path, order_id: str) -> dict[str, Any] | None:
    return fetchone(db_path, "SELECT * FROM orders WHERE order_id = ?", (order_id,))


def get_payment_issues(db_path: Path, customer_id: str, order_id: str | None = None) -> list[dict[str, Any]]:
    if order_id:
        return fetchall(
            db_path,
            "SELECT * FROM payments WHERE customer_id = ? AND order_id = ?",
            (customer_id, order_id),
        )
    return fetchall(db_path, "SELECT * FROM payments WHERE customer_id = ?", (customer_id,))


def get_ticket_history(db_path: Path, customer_id: str) -> list[dict[str, Any]]:
    return fetchall(db_path, "SELECT * FROM tickets WHERE customer_id = ?", (customer_id,))


def get_warranty(db_path: Path, customer_id: str, product: str | None = None) -> list[dict[str, Any]]:
    if product:
        return fetchall(
            db_path,
            "SELECT * FROM warranties WHERE customer_id = ? AND product = ?",
            (customer_id, product),
        )
    return fetchall(db_path, "SELECT * FROM warranties WHERE customer_id = ?", (customer_id,))


def search_docs(docs_dir: Path, query: str, product: str | None = None, error_code: str | None = None) -> list[dict[str, Any]]:
    lowered_query = query.lower()
    terms = [token.lower() for token in query.replace("?", "").split() if len(token) > 2]
    if product:
        terms.append(product.lower())
    if error_code:
        terms.append(error_code.lower())
    troubleshooting_query = any(term in lowered_query for term in ("setup", "error", "failing", "defect", "pairing"))
    warranty_query = any(term in lowered_query for term in ("warranty", "replacement", "return"))
    results: list[dict[str, Any]] = []
    for path in sorted(docs_dir.glob("*.md")):
        content = path.read_text(encoding="utf-8")
        haystack = content.lower()
        score = sum(1 for term in terms if term in haystack)
        filename = path.name.lower()
        if troubleshooting_query and filename in {"setup_guide.md", "troubleshooting_kb.md"}:
            score += 5
        if warranty_query and filename in {"refund_policy.md", "warranty_rules.md"}:
            score += 1
        if score:
            results.append(
                {
                    "document": path.name,
                    "score": score,
                    "excerpt": content.splitlines()[0:6],
                }
            )
    return sorted(results, key=lambda item: item["score"], reverse=True)


def get_policy(docs_dir: Path, policy_type: str) -> dict[str, Any]:
    lookup = {
        "refund": docs_dir / "refund_policy.md",
        "return": docs_dir / "refund_policy.md",
        "warranty": docs_dir / "warranty_rules.md",
    }
    path = lookup.get(policy_type, docs_dir / "refund_policy.md")
    return {
        "policy_type": policy_type,
        "document": path.name,
        "content": path.read_text(encoding="utf-8"),
    }