from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, ClassVar
import json
import time


@dataclass
class TraceRecorder:
    mode: str
    runtime: str
    task_id: str
    started_at: float = field(default_factory=time.perf_counter)
    events: list[dict[str, Any]] = field(default_factory=list)
    _step_counter: int = field(default=0, init=False, repr=False)
    run_id: str | None = None
    lane: str | None = None
    started_unix_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    _turn_index: int = field(default=0, init=False, repr=False)
    _writer: Any = field(default=None, init=False, repr=False)  # RunWriter | None — lazy

    _PHASE_MAP: ClassVar[dict[str, str]] = {
        "agent_register": "discovery",
        "capability_advertise": "discovery",
    }

    trace_schema_version: ClassVar[str] = "1.0"

    def __post_init__(self) -> None:
        if self.run_id and self.lane:
            from .race.runs import get_writer  # lazy: avoid circular import
            self._writer = get_writer(self.run_id)

    def record(self, event_type: str, **payload: Any) -> None:
        # Per-lane turn-index bump (D-15, D-16, D-17). Lazy import to avoid
        # bootstrap dependency on race/turn at module-import time.
        if self.lane:
            from .race.turn import is_turn_defining
            if is_turn_defining(self.lane, event_type):
                self._turn_index += 1

        step_index: int | None = None
        if event_type in {"tool_call", "task_submit"}:
            self._step_counter += 1
            step_index = self._step_counter
        phase = self._PHASE_MAP.get(event_type, "execution")
        event: dict[str, Any] = {
            "index": len(self.events) + 1,
            "event_type": event_type,
            "timestamp_ms": round((time.perf_counter() - self.started_at) * 1000, 3),
            "phase": phase,
            "trace_schema_version": self.trace_schema_version,  # TRC-02: stamped on EVERY event
        }
        if step_index is not None:
            event["step_index"] = step_index
        if self.lane is not None:
            event["lane"] = self.lane
            event["turn_index"] = self._turn_index
        if self.run_id is not None:
            event["run_id"] = self.run_id
        event.update(payload)
        self.events.append(event)

        # D-04 ndjson durability hook — only when in race mode (run_id + lane set)
        if self._writer is not None:
            self._writer.append(
                event,
                force_flush=event_type in {"fault_injected", "fault_observed", "done"},
            )

    def latency_ms(self) -> float:
        return round((time.perf_counter() - self.started_at) * 1000, 3)

    def save(self, output_dir: Path) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{self.task_id}_{self.mode}.json"
        path.write_text(json.dumps(self.events, indent=2), encoding="utf-8")
        return path

    def export_external(self, output_dir: Path, **metadata: Any) -> Path:
        output_dir.mkdir(parents=True, exist_ok=True)
        path = output_dir / f"{self.task_id}_{self.mode}.ndjson"
        with path.open("w", encoding="utf-8") as handle:
            for event in self.events:
                record = {
                    "run": {
                        "task_id": self.task_id,
                        "mode": self.mode,
                        "runtime": self.runtime,
                        **metadata,
                    },
                    "event": event,
                }
                handle.write(json.dumps(record) + "\n")
        return path
