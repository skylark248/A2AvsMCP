from __future__ import annotations

from pathlib import Path
from typing import Any
import json


DEFAULT_REMOTE_A2A_REGISTRY = {
    "customer_data": "http://127.0.0.1:9101",
    "documentation": "http://127.0.0.1:9102",
    "policy_billing": "http://127.0.0.1:9103",
}


class RemoteA2ARegistry:
    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self.registry_path = project_root / "REMOTE_A2A_REGISTRY.json"

    def load(self) -> dict[str, str]:
        if not self.registry_path.exists():
            return dict(DEFAULT_REMOTE_A2A_REGISTRY)
        payload = json.loads(self.registry_path.read_text(encoding="utf-8-sig"))
        endpoints = payload.get("agents", payload)
        return {
            str(role): str(url).rstrip("/")
            for role, url in endpoints.items()
            if str(url).strip()
        }

    def list_agents(self) -> list[dict[str, Any]]:
        endpoints = self.load()
        return [
            {"role": role, "url": url, "enabled": True}
            for role, url in sorted(endpoints.items())
        ]

