from __future__ import annotations

import argparse
import os
import time
from pathlib import Path
from typing import Any

import uvicorn
from fastapi import FastAPI, Header, HTTPException

from ..agents.base import AgentContext
from ..dataset import DemoRepository
from ..schemas import A2AMessage, FailureConfig
from ..trace import TraceRecorder
from .remote_models import agent_class_for_role, remote_agent_card_payload, supported_specialist_roles
from .sdk_compat import remote_binding_metadata


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def create_app(
    *,
    role: str,
    project_root: Path = PROJECT_ROOT,
    host: str = "127.0.0.1",
    port: int = 9101,
    auth_token: str | None = None,
    public_url: str | None = None,
) -> FastAPI:
    if role not in supported_specialist_roles():
        raise ValueError(f"Unsupported remote A2A role: {role}")

    base_url = (public_url or f"http://{host}:{port}").rstrip("/")
    app = FastAPI(title=f"A2A Remote Specialist - {role}")

    def require_auth(authorization: str | None) -> None:
        if not auth_token:
            return
        expected = f"Bearer {auth_token}"
        if authorization != expected:
            raise HTTPException(status_code=401, detail="Invalid remote A2A bearer token")

    @app.get("/health")
    def health() -> dict[str, Any]:
        return {
            "status": "ok",
            "role": role,
            "service_url": base_url,
            **remote_binding_metadata(),
        }

    @app.get("/.well-known/agent-card.json")
    def agent_card(authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_auth(authorization)
        return remote_agent_card_payload(role, base_url)

    @app.post("/a2a/tasks")
    def run_task(payload: dict[str, Any], authorization: str | None = Header(default=None)) -> dict[str, Any]:
        require_auth(authorization)
        message_payload = payload.get("message") or {}
        message = A2AMessage(**message_payload)
        failure_config = FailureConfig(**(payload.get("failure_config") or {}))
        agent_id = remote_agent_card_payload(role, base_url)["metadata"]["agentId"]
        if agent_id in failure_config.unavailable_agents:
            raise HTTPException(status_code=503, detail=f"Remote A2A agent unavailable: {agent_id}")
        if failure_config.remote_a2a_timeout and role == "documentation":
            time.sleep(10)
        if failure_config.remote_a2a_task_failure and role == "policy_billing":
            raise HTTPException(status_code=500, detail="Simulated remote A2A task failure.")
        if failure_config.remote_a2a_malformed_response and role == "policy_billing":
            return {
                "remote_task_id": message.task_id,
                "context_id": message.task_id,
                "status": "completed",
                "malformed": True,
                **remote_binding_metadata(),
            }

        trace = TraceRecorder(mode="remote_a2a_specialist", runtime=str(payload.get("runtime") or "mock"), task_id=message.task_id)
        trace.record(
            "a2a_remote_task_received",
            role=role,
            agent=agent_id,
            task_id=message.task_id,
            capability=message.capability,
            use_mcp=bool(payload.get("use_mcp")),
            mcp_transport=str(payload.get("mcp_transport") or "in_process"),
        )
        repo = DemoRepository(project_root)
        context = AgentContext(
            repo,
            trace,
            str(payload.get("runtime") or "mock"),
            str(payload.get("mcp_transport") or "in_process"),
            project_root,
            failure_config,
            remote_mcp_urls=dict(payload.get("remote_mcp_urls") or {}),
        )
        agent_class = agent_class_for_role(role, use_mcp=bool(payload.get("use_mcp")))
        agent = agent_class(context)
        try:
            result = agent.handle_task(message)
        except Exception as exc:
            trace.record("a2a_remote_task_failed", role=role, agent=agent_id, error=str(exc))
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        finally:
            context.close_mcp_clients()
        trace.record("a2a_remote_task_completed", role=role, agent=agent_id, task_id=message.task_id)
        return {
            "remote_task_id": message.task_id,
            "context_id": message.task_id,
            "status": "completed",
            "result": result.to_dict(),
            "trace": trace.events,
            **remote_binding_metadata(),
        }

    return app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a hosted remote A2A specialist demo server.")
    parser.add_argument("--role", choices=supported_specialist_roles(), required=True, help="Specialist role hosted by this process.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=9101)
    parser.add_argument("--auth-token", default=os.getenv("REMOTE_A2A_TOKEN"), help="Optional demo bearer token. Do not use for production auth.")
    parser.add_argument("--project-root", default=str(PROJECT_ROOT))
    parser.add_argument("--public-url", default="", help="Optional URL advertised in the Agent Card when the bind host is not externally reachable.")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    app = create_app(role=args.role, project_root=Path(args.project_root), host=args.host, port=args.port, auth_token=args.auth_token, public_url=args.public_url or None)
    uvicorn.run(app, host=args.host, port=args.port)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
