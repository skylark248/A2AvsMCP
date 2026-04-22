from __future__ import annotations

import time
import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

from ..schemas import A2AMessage, AgentCard, AgentResult
from ..trace import TraceRecorder
from .protocol import (
    A2A_METHOD_GET_TASK,
    A2A_METHOD_SEND_MESSAGE,
    A2A_PROTOCOL_VERSION,
    A2A_TRANSPORT,
    STATE_COMPLETED,
    STATE_FAILED,
    STATE_SUBMITTED,
    STATE_WORKING,
    agent_card_payload,
    artifact_update_event,
    message_payload,
    status_update_event,
    task_snapshot,
)


class A2ABroker:
    def __init__(self, trace: TraceRecorder, max_retries: int = 1, timeout_ms: int = 5000) -> None:
        self.trace = trace
        self.cards: dict[str, AgentCard] = {}
        self.handlers: dict[str, object] = {}
        self.max_retries = max_retries
        self.timeout_ms = timeout_ms

    def register(self, card: AgentCard, handler: object) -> None:
        self.cards[card.agent_id] = card
        self.handlers[card.agent_id] = handler
        a2a_card = agent_card_payload(card)
        self.trace.record(
            "a2a_message",
            message_type="agent_register",
            sender=card.agent_id,
            capabilities=card.capabilities,
            a2a_protocol_version=A2A_PROTOCOL_VERSION,
            a2a_agent_card=a2a_card,
        )
        self.trace.record(
            "a2a_message",
            message_type="capability_advertise",
            sender=card.agent_id,
            capabilities=card.capabilities,
            a2a_protocol_version=A2A_PROTOCOL_VERSION,
            a2a_agent_card=a2a_card,
        )

    def find_by_capability(self, capability: str) -> AgentCard:
        for card in self.cards.values():
            if capability in card.capabilities:
                return card
        raise KeyError(f"No agent registered for capability '{capability}'")

    def send_task(self, message: A2AMessage) -> AgentResult:
        handler, resolved_target = self._resolve_handler(message)
        timeout_ms = int(message.context.get("timeout_ms", self.timeout_ms))
        attempt = 0
        last_error: Exception | None = None
        while attempt <= self.max_retries:
            attempt += 1
            message.attempt = attempt
            protocol_message = message_payload(message)
            self.trace.record(
                "a2a_message",
                message_type=message.message_type,
                sender=message.sender_agent,
                target=resolved_target,
                capability=message.capability,
                attempt=attempt,
                a2a_protocol_version=A2A_PROTOCOL_VERSION,
                a2a_method=A2A_METHOD_SEND_MESSAGE,
                a2a_transport=A2A_TRANSPORT,
                a2a_message=protocol_message,
            )
            self._record_task_status(message, resolved_target, "queued", STATE_SUBMITTED, attempt, "Task submitted to specialist.")
            self.trace.record(
                "a2a_message",
                message_type="task_accept",
                sender=resolved_target,
                target=message.sender_agent,
                attempt=attempt,
                a2a_protocol_version=A2A_PROTOCOL_VERSION,
                a2a_method=A2A_METHOD_GET_TASK,
            )
            self._record_task_status(message, resolved_target, "accepted", STATE_WORKING, attempt, "Specialist accepted the task.")
            self.trace.record(
                "a2a_message",
                message_type="task_progress",
                sender=resolved_target,
                target=message.sender_agent,
                state="in_progress",
                attempt=attempt,
                a2a_protocol_version=A2A_PROTOCOL_VERSION,
            )
            self._record_task_status(message, resolved_target, "in_progress", STATE_WORKING, attempt, "Specialist is working on the task.")
            try:
                result = self._execute_with_timeout(handler, message, timeout_ms)
                self._record_task_status(message, resolved_target, "completed", STATE_COMPLETED, attempt, "Specialist completed the task.", final=True)
                artifact_event = artifact_update_event(message, result)
                self.trace.record(
                    "a2a_message",
                    message_type="task_result",
                    sender=resolved_target,
                    target=message.sender_agent,
                    attempt=attempt,
                    a2a_protocol_version=A2A_PROTOCOL_VERSION,
                    a2a_artifact_event=artifact_event,
                    a2a_task=task_snapshot(message, STATE_COMPLETED, result=result),
                )
                self.trace.record("a2a_task_artifact", task_id=message.task_id, target=resolved_target, attempt=attempt, a2a_artifact_event=artifact_event)
                return result
            except Exception as exc:
                last_error = exc
                self.trace.record(
                    "a2a_message",
                    message_type="task_error",
                    sender=resolved_target,
                    target=message.sender_agent,
                    attempt=attempt,
                    error=str(exc),
                    a2a_protocol_version=A2A_PROTOCOL_VERSION,
                )
                self._record_task_status(message, resolved_target, "failed", STATE_FAILED, attempt, str(exc), final=True, error=str(exc))
                if attempt <= self.max_retries:
                    self.trace.record(
                        "a2a_message",
                        message_type="task_retry",
                        sender=message.sender_agent,
                        target=resolved_target,
                        attempt=attempt + 1,
                        a2a_protocol_version=A2A_PROTOCOL_VERSION,
                    )
                    continue
                raise RuntimeError(f"Task {message.task_id} failed after {attempt} attempts: {exc}") from exc
        raise RuntimeError(f"Task {message.task_id} failed: {last_error}")

    def send_tasks_parallel(self, messages: list[A2AMessage]) -> list[AgentResult]:
        """Dispatch all messages concurrently. Returns results in submission order (per D-07)."""
        if not messages:
            return []
        batch_id = uuid.uuid4().hex[:12]
        futures = []
        with ThreadPoolExecutor(max_workers=len(messages)) as executor:
            for message in messages:
                started_at = round(time.time() * 1000)
                self.trace.record(
                    "task_submit",
                    task_id=message.task_id,
                    target=message.target_agent,
                    capability=message.capability,
                    parallel_batch_id=batch_id,
                    started_at=started_at,
                )
                futures.append(
                    executor.submit(self._run_parallel_task, message, batch_id, started_at)
                )
            return [f.result() for f in futures]  # preserves submission order

    def _run_parallel_task(self, message: A2AMessage, batch_id: str, started_at: int) -> AgentResult:
        """Worker: execute one task and record its completion timing."""
        result = self.send_task(message)
        completed_at = round(time.time() * 1000)
        self.trace.record(
            "task_complete",
            task_id=message.task_id,
            target=message.target_agent,
            parallel_batch_id=batch_id,
            started_at=started_at,
            completed_at=completed_at,
            status="completed",
        )
        return result

    def _record_task_status(
        self,
        message: A2AMessage,
        target: str,
        status: str,
        a2a_state: str,
        attempt: int,
        note: str,
        *,
        final: bool = False,
        error: str | None = None,
    ) -> None:
        self.trace.record(
            "task_status",
            task_id=message.task_id,
            status=status,
            a2a_state=a2a_state,
            target=target,
            attempt=attempt,
            error=error,
            a2a_protocol_version=A2A_PROTOCOL_VERSION,
            a2a_task_event=status_update_event(message, a2a_state, final=final, note=note),
            a2a_task=task_snapshot(message, a2a_state, error=error),
        )

    def _resolve_handler(self, message: A2AMessage) -> tuple[object, str]:
        handler = self.handlers.get(message.target_agent)
        if handler is not None:
            return handler, message.target_agent
        fallback_capability = message.context.get("fallback_capability")
        if fallback_capability:
            fallback_card = self.find_by_capability(fallback_capability)
            self.trace.record(
                "a2a_message",
                message_type="task_redirect",
                sender=message.sender_agent,
                target=fallback_card.agent_id,
                capability=fallback_capability,
                a2a_protocol_version=A2A_PROTOCOL_VERSION,
            )
            return self.handlers[fallback_card.agent_id], fallback_card.agent_id
        raise KeyError(f"No handler registered for agent '{message.target_agent}'")

    def _execute_with_timeout(self, handler: object, message: A2AMessage, timeout_ms: int) -> AgentResult:
        with ThreadPoolExecutor(max_workers=1) as executor:
            future = executor.submit(handler.handle_task, message)
            try:
                return future.result(timeout=timeout_ms / 1000)
            except FuturesTimeoutError as exc:
                future.cancel()
                raise TimeoutError(f"Task timed out after {timeout_ms} ms") from exc
