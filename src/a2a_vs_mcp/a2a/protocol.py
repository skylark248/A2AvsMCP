from __future__ import annotations

from typing import Any

from ..schemas import A2AMessage, AgentCard, AgentResult, new_id, utc_now

A2A_PROTOCOL_VERSION = "1.0"
A2A_TRANSPORT = "JSONRPC"
A2A_METHOD_SEND_MESSAGE = "message/send"
A2A_METHOD_GET_TASK = "tasks/get"

STATE_SUBMITTED = "submitted"
STATE_WORKING = "working"
STATE_COMPLETED = "completed"
STATE_FAILED = "failed"
STATE_CANCELED = "canceled"


def a2a_skill_id(capability: str) -> str:
    return capability.replace("_", "-")


def agent_card_payload(card: AgentCard) -> dict[str, Any]:
    return {
        "protocolVersion": A2A_PROTOCOL_VERSION,
        "name": card.name,
        "description": card.description,
        "url": f"local://agents/{card.agent_id}",
        "preferredTransport": A2A_TRANSPORT,
        "capabilities": {
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": True,
        },
        "defaultInputModes": ["text/plain", "application/json"],
        "defaultOutputModes": ["text/plain", "application/json"],
        "skills": [
            {
                "id": a2a_skill_id(capability),
                "name": capability.replace("_", " ").title(),
                "description": f"Handles {capability.replace('_', ' ')} tasks.",
                "tags": [capability],
            }
            for capability in card.capabilities
        ],
        "metadata": {
            "agentId": card.agent_id,
            "demoScope": "educational-a2a-style-broker",
        },
    }


def message_payload(message: A2AMessage) -> dict[str, Any]:
    return {
        "messageId": message.message_id,
        "role": "ROLE_USER",
        "taskId": message.task_id,
        "contextId": message.task_id,
        "parts": [
            {
                "kind": "data",
                "data": message.payload,
            }
        ],
        "metadata": {
            "senderAgent": message.sender_agent,
            "targetAgent": message.target_agent,
            "capability": message.capability,
            "attempt": message.attempt,
            "messageType": message.message_type,
        },
    }


def status_update_event(message: A2AMessage, state: str, *, final: bool = False, note: str = "") -> dict[str, Any]:
    status_message = {
        "messageId": new_id("msg"),
        "role": "ROLE_AGENT",
        "taskId": message.task_id,
        "contextId": message.task_id,
        "parts": [{"kind": "text", "text": note or f"Task is {state}."}],
        "metadata": {
            "senderAgent": message.target_agent,
            "capability": message.capability,
            "attempt": message.attempt,
        },
    }
    return {
        "kind": "status-update",
        "taskId": message.task_id,
        "contextId": message.task_id,
        "status": {
            "state": state,
            "timestamp": utc_now(),
            "message": status_message,
        },
        "final": final,
        "metadata": {
            "protocolVersion": A2A_PROTOCOL_VERSION,
            "transport": A2A_TRANSPORT,
        },
    }


def artifact_update_event(message: A2AMessage, result: AgentResult) -> dict[str, Any]:
    return {
        "kind": "artifact-update",
        "taskId": message.task_id,
        "contextId": message.task_id,
        "artifact": {
            "artifactId": new_id("artifact"),
            "name": f"{result.agent_id} result",
            "description": f"Specialist result returned by {result.agent_id}.",
            "parts": [
                {"kind": "text", "text": result.summary},
                {"kind": "data", "data": result.details},
            ],
            "metadata": {
                "agentId": result.agent_id,
                "confidence": result.confidence,
                "status": result.status,
            },
        },
        "append": False,
        "lastChunk": True,
        "metadata": {
            "protocolVersion": A2A_PROTOCOL_VERSION,
            "transport": A2A_TRANSPORT,
        },
    }


def task_snapshot(message: A2AMessage, state: str, result: AgentResult | None = None, error: str | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": message.task_id,
        "contextId": message.task_id,
        "status": {
            "state": state,
            "timestamp": utc_now(),
        },
        "metadata": {
            "protocolVersion": A2A_PROTOCOL_VERSION,
            "transport": A2A_TRANSPORT,
            "capability": message.capability,
            "senderAgent": message.sender_agent,
            "targetAgent": message.target_agent,
            "attempt": message.attempt,
        },
    }
    if result is not None:
        payload["artifacts"] = [artifact_update_event(message, result)["artifact"]]
    if error:
        payload["status"]["message"] = {
            "messageId": new_id("msg"),
            "role": "ROLE_AGENT",
            "taskId": message.task_id,
            "contextId": message.task_id,
            "parts": [{"kind": "text", "text": error}],
        }
    return payload
