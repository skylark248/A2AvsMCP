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

    _PHASE_MAP: ClassVar[dict[str, str]] = {
        "agent_register": "discovery",
        "capability_advertise": "discovery",
    }

    def record(self, event_type: str, **payload: Any) -> None:
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
        }
        if step_index is not None:
            event["step_index"] = step_index
        event.update(payload)
        self.events.append(event)

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
