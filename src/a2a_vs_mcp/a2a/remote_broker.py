from __future__ import annotations

from typing import Any

from ..schemas import A2AMessage, AgentCard, AgentResult, FailureConfig
from ..trace import TraceRecorder
from .protocol import (
    A2A_METHOD_SEND_MESSAGE,
    A2A_PROTOCOL_VERSION,
    STATE_COMPLETED,
    STATE_FAILED,
    STATE_SUBMITTED,
    STATE_WORKING,
    artifact_update_event,
    message_payload,
    status_update_event,
    task_snapshot,
)
from .remote_client import RemoteA2AClient
from .remote_models import agent_card_from_payload
from .sdk_compat import REMOTE_A2A_BINDING, remote_binding_metadata


class RemoteA2ABroker:
    def __init__(
        self,
        trace: TraceRecorder,
        *,
        endpoints: dict[str, str],
        runtime: str,
        mcp_transport: str,
        project_root,
        failure_config: FailureConfig,
        remote_mcp_urls: dict[str, str] | None = None,
        use_mcp: bool = False,
        max_retries: int = 1,
        timeout_ms: int = 5000,
        auth_token: str | None = None,
    ) -> None:
        self.trace = trace
        self.endpoints = {role: url.rstrip("/") for role, url in endpoints.items() if url}
        self.runtime = runtime
        self.mcp_transport = mcp_transport
        self.project_root = project_root
        self.failure_config = failure_config
        self.remote_mcp_urls = remote_mcp_urls or {}
        self.use_mcp = use_mcp
        self.max_retries = max_retries
        self.timeout_ms = timeout_ms
        self.auth_token = auth_token
        self.cards: dict[str, AgentCard] = {}
        self.clients: dict[str, RemoteA2AClient] = {}
        self.card_payloads: dict[str, dict[str, Any]] = {}
        self._discovered = False

    def discover(self) -> None:
        if self._discovered:
            return
        self._discovered = True
        for role, endpoint in self.endpoints.items():
            if self.failure_config.remote_a2a_bad_auth:
                self.trace.record(
                    "a2a_remote_failure",
                    role=role,
                    endpoint=endpoint,
                    error="Simulated remote A2A authentication failure.",
                    stage="auth",
                    **remote_binding_metadata(),
                )
                continue
            client = RemoteA2AClient(endpoint, timeout_s=self.timeout_ms / 1000, token=self.auth_token)
            try:
                payload = client.fetch_agent_card()
                card = agent_card_from_payload(payload)
                if self.failure_config.remote_a2a_missing_capability and role == "policy_billing":
                    self.trace.record(
                        "a2a_remote_failure",
                        role=role,
                        endpoint=endpoint,
                        agent=card.agent_id,
                        error="Simulated remote Agent Card missing policy_billing capability.",
                        stage="capability",
                        **remote_binding_metadata(),
                    )
                    card.capabilities = [capability for capability in card.capabilities if capability != "policy_billing"]
                    payload["skills"] = [skill for skill in payload.get("skills", []) if "policy_billing" not in (skill.get("tags") or [])]
                self.cards[card.agent_id] = card
                self.clients[card.agent_id] = client
                self.card_payloads[card.agent_id] = payload
                self.trace.record(
                    "a2a_remote_discovery",
                    role=role,
                    endpoint=endpoint,
                    agent=card.agent_id,
                    capabilities=card.capabilities,
                    a2a_protocol_version=payload.get("protocolVersion", A2A_PROTOCOL_VERSION),
                    a2a_binding=payload.get("metadata", {}).get("binding", REMOTE_A2A_BINDING),
                    a2a_agent_card=payload,
                )
                self.trace.record(
                    "a2a_message",
                    message_type="remote_agent_register",
                    sender=card.agent_id,
                    capabilities=card.capabilities,
                    a2a_protocol_version=payload.get("protocolVersion", A2A_PROTOCOL_VERSION),
                    a2a_binding=payload.get("metadata", {}).get("binding", REMOTE_A2A_BINDING),
                    a2a_agent_card=payload,
                )
            except Exception as exc:
                self.trace.record(
                    "a2a_remote_failure",
                    role=role,
                    endpoint=endpoint,
                    error=str(exc),
                    stage="discovery",
                    **remote_binding_metadata(),
                )

    def find_by_capability(self, capability: str) -> AgentCard:
        self.discover()
        for card in self.cards.values():
            if capability in card.capabilities:
                return card
        raise KeyError(f"No remote agent registered for capability '{capability}'")

    def send_task(self, message: A2AMessage) -> AgentResult:
        self.discover()
        card = self.cards.get(message.target_agent)
        client = self.clients.get(message.target_agent)
        if card is None or client is None:
            fallback_capability = message.context.get("fallback_capability")
            if fallback_capability:
                card = self.find_by_capability(str(fallback_capability))
                client = self.clients[card.agent_id]
                message.target_agent = card.agent_id
            else:
                raise KeyError(f"No remote handler registered for agent '{message.target_agent}'")

        attempt = 0
        last_error: Exception | None = None
        while attempt <= self.max_retries:
            attempt += 1
            message.attempt = attempt
            protocol_message = message_payload(message)
            self.trace.record(
                "a2a_remote_send",
                sender=message.sender_agent,
                target=card.agent_id,
                capability=message.capability,
                attempt=attempt,
                endpoint=client.base_url,
                a2a_method=A2A_METHOD_SEND_MESSAGE,
                a2a_binding=REMOTE_A2A_BINDING,
                a2a_message=protocol_message,
            )
            self.trace.record(
                "a2a_message",
                message_type="remote_task_request",
                sender=message.sender_agent,
                target=card.agent_id,
                capability=message.capability,
                attempt=attempt,
                a2a_method=A2A_METHOD_SEND_MESSAGE,
                a2a_binding=REMOTE_A2A_BINDING,
                a2a_message=protocol_message,
            )
            self._record_remote_status(message, card.agent_id, STATE_SUBMITTED, attempt, "Task submitted to remote specialist.")
            self._record_remote_status(message, card.agent_id, STATE_WORKING, attempt, "Remote specialist accepted the task.")
            try:
                payload = client.send_task(
                    message,
                    runtime=self.runtime,
                    use_mcp=self.use_mcp,
                    mcp_transport=self.mcp_transport,
                    remote_mcp_urls=self.remote_mcp_urls,
                    failure_config=self.failure_config.to_dict(),
                )
                self._record_remote_server_events(card.agent_id, payload.get("trace") or [])
                result_payload = payload.get("result")
                if not isinstance(result_payload, dict) or "summary" not in result_payload or "details" not in result_payload:
                    raise ValueError("Malformed remote A2A response: missing result summary/details.")
                result = AgentResult(
                    agent_id=str(result_payload.get("agent_id") or card.agent_id),
                    summary=str(result_payload.get("summary") or ""),
                    details=dict(result_payload.get("details") or {}),
                    confidence=float(result_payload.get("confidence", 0.95)),
                    status=str(result_payload.get("status") or "completed"),
                )
                self._record_remote_status(message, card.agent_id, STATE_COMPLETED, attempt, "Remote specialist completed the task.", final=True)
                artifact_event = artifact_update_event(message, result)
                self.trace.record(
                    "a2a_remote_artifact",
                    sender=card.agent_id,
                    target=message.sender_agent,
                    attempt=attempt,
                    remote_task_id=payload.get("remote_task_id"),
                    a2a_artifact_event=artifact_event,
                    a2a_task=task_snapshot(message, STATE_COMPLETED, result=result),
                )
                self.trace.record("a2a_task_artifact", task_id=message.task_id, target=card.agent_id, attempt=attempt, a2a_artifact_event=artifact_event)
                return result
            except Exception as exc:
                last_error = exc
                self.trace.record(
                    "a2a_remote_failure",
                    sender=card.agent_id,
                    target=message.sender_agent,
                    attempt=attempt,
                    endpoint=client.base_url,
                    error=str(exc),
                    stage="task",
                    a2a_task=task_snapshot(message, STATE_FAILED, error=str(exc)),
                )
                self._record_remote_status(message, card.agent_id, STATE_FAILED, attempt, str(exc), final=True, error=str(exc))
                if attempt <= self.max_retries:
                    self.trace.record(
                        "a2a_remote_retry",
                        sender=message.sender_agent,
                        target=card.agent_id,
                        attempt=attempt + 1,
                        endpoint=client.base_url,
                    )
                    self.trace.record(
                        "a2a_message",
                        message_type="remote_task_retry",
                        sender=message.sender_agent,
                        target=card.agent_id,
                        attempt=attempt + 1,
                    )
                    continue
                raise RuntimeError(f"Remote task {message.task_id} failed after {attempt} attempts: {exc}") from exc
        raise RuntimeError(f"Remote task {message.task_id} failed: {last_error}")

    def _record_remote_server_events(self, agent_id: str, events: list[dict[str, Any]]) -> None:
        for event in events:
            event_type = event.get("event_type")
            if event_type in {"tool_discovery", "tool_call", "tool_error", "tool_transport_fallback"}:
                copied = {key: value for key, value in event.items() if key not in {"index", "timestamp_ms", "event_type"}}
                self.trace.record(
                    event_type,
                    **copied,
                    remote_agent=agent_id,
                    remote_trace=True,
                )
            elif event_type in {"a2a_remote_task_received", "a2a_remote_task_failed", "a2a_remote_task_completed"}:
                copied = {key: value for key, value in event.items() if key not in {"index", "timestamp_ms", "event_type"}}
                self.trace.record(
                    "a2a_remote_server_event",
                    remote_agent=agent_id,
                    remote_event_type=event_type,
                    **copied,
                )
    def _record_remote_status(
        self,
        message: A2AMessage,
        target: str,
        state: str,
        attempt: int,
        note: str,
        *,
        final: bool = False,
        error: str | None = None,
    ) -> None:
        event = status_update_event(message, state, final=final, note=note)
        self.trace.record(
            "a2a_remote_status",
            task_id=message.task_id,
            a2a_state=state,
            target=target,
            attempt=attempt,
            error=error,
            a2a_task_event=event,
            a2a_task=task_snapshot(message, state, error=error),
        )
        self.trace.record(
            "task_status",
            task_id=message.task_id,
            status=f"remote_{state}",
            a2a_state=state,
            target=target,
            attempt=attempt,
            error=error,
            a2a_task_event=event,
            a2a_task=task_snapshot(message, state, error=error),
        )




