from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .persistence import PlatformStore


DEFAULT_REGISTRY = [
    {
        "id": "local_example",
        "label": "Local example endpoints",
        "db_url": "http://127.0.0.1:9001/mcp",
        "docs_url": "http://127.0.0.1:9002/mcp",
        "enabled": True,
    }
]


class RemoteMCPRegistry:
    def __init__(self, project_root: Path, store: PlatformStore) -> None:
        self.project_root = project_root
        self.store = store
        self.registry_path = project_root / "REMOTE_MCP_REGISTRY.json"
        self.ensure_seeded()

    def ensure_seeded(self) -> None:
        if not self.registry_path.exists():
            self.registry_path.write_text(json.dumps(DEFAULT_REGISTRY, indent=2), encoding="utf-8")
        if not self.store.list_remote_mcp_servers():
            for entry in self.load_file_entries():
                self.store.upsert_remote_mcp_server(
                    server_id=entry["id"],
                    label=entry["label"],
                    db_url=entry["db_url"],
                    docs_url=entry["docs_url"],
                    enabled=bool(entry.get("enabled", True)),
                )

    def load_file_entries(self) -> list[dict[str, Any]]:
        payload = json.loads(self.registry_path.read_text(encoding="utf-8-sig"))
        if not isinstance(payload, list):
            raise ValueError("REMOTE_MCP_REGISTRY.json must contain a JSON array")
        entries: list[dict[str, Any]] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("Remote MCP registry entries must be objects")
            entry = {
                "id": str(item.get("id", "")).strip(),
                "label": str(item.get("label", "")).strip(),
                "db_url": str(item.get("db_url", "")).strip(),
                "docs_url": str(item.get("docs_url", "")).strip(),
                "enabled": bool(item.get("enabled", True)),
            }
            if not entry["id"] or not entry["label"] or not entry["db_url"] or not entry["docs_url"]:
                raise ValueError("Remote MCP registry entries require id, label, db_url, and docs_url")
            entries.append(entry)
        return entries

    def list_servers(self, enabled_only: bool = True) -> list[dict[str, Any]]:
        servers = self.store.list_remote_mcp_servers()
        if enabled_only:
            servers = [server for server in servers if int(server.get("enabled", 0)) == 1]
        return servers

    def discover(self, server_id: str) -> dict[str, str]:
        for server in self.list_servers(enabled_only=True):
            if server["id"] == server_id:
                return {"db": server["db_url"], "docs": server["docs_url"]}
        raise KeyError(server_id)

    def sync_from_file(self) -> list[dict[str, Any]]:
        entries = self.load_file_entries()
        synced = []
        for entry in entries:
            synced.append(self.store.upsert_remote_mcp_server(server_id=entry["id"], label=entry["label"], db_url=entry["db_url"], docs_url=entry["docs_url"], enabled=entry["enabled"]))
        return synced


