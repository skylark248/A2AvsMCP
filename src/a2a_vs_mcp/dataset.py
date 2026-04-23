from __future__ import annotations

from pathlib import Path
from typing import Any
import hashlib
import json
import sqlite3

from . import evidence
from .identity import base_artifact_root
from .schemas import SupportTicket


SEED_DIR = Path(__file__).resolve().parent / "data" / "seeds"


class DemoRepository:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.docs_dir = project_root / "data" / "docs"
        artifact_root = base_artifact_root(project_root)
        self.db_path = artifact_root / "support_demo.db"
        self.seed_manifest_path = artifact_root / "seed_manifest.json"
        self._ensure_sqlite()

    def _load_seed(self, name: str) -> list[dict[str, Any]]:
        path = SEED_DIR / f"{name}.json"
        return json.loads(path.read_text(encoding="utf-8"))

    def _seed_signature(self) -> dict[str, str]:
        signature: dict[str, str] = {}
        for path in sorted(SEED_DIR.glob("*.json")):
            signature[path.name] = hashlib.sha256(path.read_bytes()).hexdigest()
        return signature

    def _needs_rebuild(self) -> bool:
        if not self.db_path.exists() or not self.seed_manifest_path.exists():
            return True
        try:
            stored = json.loads(self.seed_manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return True
        return stored != self._seed_signature()

    def _ensure_sqlite(self) -> None:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._needs_rebuild():
            return
        temp_path = self.db_path.with_name(f"{self.db_path.name}.tmp")
        if temp_path.exists():
            temp_path.unlink()
        try:
            self._rebuild_sqlite(temp_path)
            temp_path.replace(self.db_path)
            self.seed_manifest_path.write_text(json.dumps(self._seed_signature(), indent=2), encoding="utf-8")
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def _rebuild_sqlite(self, db_path: Path | None = None) -> None:
        conn = sqlite3.connect(db_path or self.db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE customers (customer_id TEXT PRIMARY KEY, name TEXT, email TEXT, segment TEXT)")
        cur.execute("CREATE TABLE orders (order_id TEXT PRIMARY KEY, customer_id TEXT, product TEXT, status TEXT, tracking_id TEXT, eta TEXT)")
        cur.execute("CREATE TABLE payments (payment_id TEXT PRIMARY KEY, customer_id TEXT, order_id TEXT, issue_type TEXT, amount REAL, status TEXT)")
        cur.execute("CREATE TABLE tickets (ticket_id TEXT PRIMARY KEY, customer_id TEXT, summary TEXT, status TEXT)")
        cur.execute("CREATE TABLE warranties (warranty_id TEXT PRIMARY KEY, customer_id TEXT, product TEXT, expires_on TEXT, coverage TEXT)")
        for table in ("customers", "orders", "payments", "tickets", "warranties"):
            rows = self._load_seed(table)
            columns = list(rows[0].keys()) if rows else []
            if not columns:
                continue
            placeholders = ",".join("?" for _ in columns)
            cur.executemany(
                f"INSERT INTO {table} ({','.join(columns)}) VALUES ({placeholders})",
                [tuple(row[column] for column in columns) for row in rows],
            )
        conn.commit()
        conn.close()

    def get_customer_profile(self, customer_id: str) -> dict[str, Any] | None:
        return evidence.get_customer_profile(self.db_path, customer_id)

    def get_order_history(self, customer_id: str) -> list[dict[str, Any]]:
        return evidence.get_order_history(self.db_path, customer_id)

    def get_order(self, order_id: str) -> dict[str, Any] | None:
        return evidence.get_order(self.db_path, order_id)

    def get_payment_issues(self, customer_id: str, order_id: str | None = None) -> list[dict[str, Any]]:
        return evidence.get_payment_issues(self.db_path, customer_id, order_id)

    def get_ticket_history(self, customer_id: str) -> list[dict[str, Any]]:
        return evidence.get_ticket_history(self.db_path, customer_id)

    def get_warranty(self, customer_id: str, product: str | None = None) -> list[dict[str, Any]]:
        return evidence.get_warranty(self.db_path, customer_id, product)

    def search_docs(self, query: str, product: str | None = None, error_code: str | None = None) -> list[dict[str, Any]]:
        return evidence.search_docs(self.docs_dir, query, product, error_code)

    def get_policy(self, policy_type: str) -> dict[str, Any]:
        return evidence.get_policy(self.docs_dir, policy_type)

    def load_scenarios(self) -> dict[str, SupportTicket]:
        payload = self._load_seed("scenarios")
        return {
            item["scenario"]: SupportTicket(
                ticket_id=item["ticket_id"],
                customer_id=item["customer_id"],
                query=item["query"],
                scenario=item["scenario"],
                title=item.get("title", item["scenario"].replace("_", " ").title()),
                difficulty=item.get("difficulty", "standard"),
                tags=item.get("tags", []),
                talking_point=item.get("talking_point"),
            )
            for item in payload
        }

