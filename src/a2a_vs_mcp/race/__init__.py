"""Race subsystem: trace schema v1.0, ndjson durability, websocket fan-out, fault helpers."""
from __future__ import annotations

from .failure import InjectedFaultError

__all__ = ["InjectedFaultError"]
