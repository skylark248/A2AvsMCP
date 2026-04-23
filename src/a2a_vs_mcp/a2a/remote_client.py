from __future__ import annotations

from typing import Any
from urllib import error, request
import json

from ..schemas import A2AMessage


class RemoteA2AClient:
    def __init__(self, base_url: str, *, timeout_s: float = 5.0, token: str | None = None) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_s = timeout_s
        self.token = token

    def fetch_agent_card(self) -> dict[str, Any]:
        return self._get_json("/.well-known/agent-card.json")

    def health(self) -> dict[str, Any]:
        return self._get_json("/health")

    def send_task(
        self,
        message: A2AMessage,
        *,
        runtime: str,
        use_mcp: bool,
        mcp_transport: str,
        remote_mcp_urls: dict[str, str],
        failure_config: dict[str, Any],
    ) -> dict[str, Any]:
        return self._post_json(
            "/a2a/tasks",
            {
                "message": message.to_dict(),
                "runtime": runtime,
                "use_mcp": use_mcp,
                "mcp_transport": mcp_transport,
                "remote_mcp_urls": remote_mcp_urls,
                "failure_config": failure_config,
            },
        )

    def _get_json(self, path: str) -> dict[str, Any]:
        req = request.Request(self.base_url + path, headers=self._headers(), method="GET")
        return self._send(req)

    def _post_json(self, path: str, payload: dict[str, Any]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        headers = {**self._headers(), "Content-Type": "application/json"}
        req = request.Request(self.base_url + path, data=body, headers=headers, method="POST")
        return self._send(req)

    def _headers(self) -> dict[str, str]:
        headers = {"Accept": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers

    def _send(self, req: request.Request) -> dict[str, Any]:
        try:
            with request.urlopen(req, timeout=self.timeout_s) as response:
                data = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:800]
            raise RuntimeError(f"Remote A2A HTTP {exc.code}: {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Remote A2A request failed: {exc.reason}") from exc
        return json.loads(data or "{}")
