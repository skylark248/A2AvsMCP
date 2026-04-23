from __future__ import annotations

from contextlib import closing
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json
import sqlite3

from .identity import base_artifact_root


@dataclass
class TelemetrySnapshot:
    total_runs: int
    total_reports: int
    total_failures: int
    avg_latency_ms: float
    tool_calls: int
    a2a_messages: int
    users: list[str]
    mode_counts: dict[str, int]
    a2a_transport_counts: dict[str, int]

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_runs": self.total_runs,
            "total_reports": self.total_reports,
            "total_failures": self.total_failures,
            "avg_latency_ms": self.avg_latency_ms,
            "tool_calls": self.tool_calls,
            "a2a_messages": self.a2a_messages,
            "users": self.users,
            "mode_counts": self.mode_counts,
            "a2a_transport_counts": self.a2a_transport_counts,
        }


class PlatformStore:
    def __init__(self, project_root: Path) -> None:
        self.db_path = base_artifact_root(project_root) / "platform_state.db"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_schema(self) -> None:
        with closing(self.connect()) as conn, conn:
            conn.executescript(
                """
                create table if not exists report_runs (
                    id integer primary key autoincrement,
                    user_id text not null,
                    report_name text not null,
                    report_path text not null,
                    scenario text not null,
                    runtime text not null,
                    modes_json text not null,
                    generated_at text not null,
                    total_tool_calls integer not null,
                    total_a2a_messages integer not null,
                    total_failures integer not null,
                    unique(user_id, report_name)
                );
                create table if not exists telemetry_events (
                    id integer primary key autoincrement,
                    user_id text not null,
                    event_type text not null,
                    mode text,
                    scenario text,
                    runtime text,
                    latency_ms real not null default 0,
                    tool_calls integer not null default 0,
                    a2a_messages integer not null default 0,
                    failures integer not null default 0,
                    created_at text not null,
                    metadata_json text not null default '{}'
                );
                create table if not exists remote_mcp_registry (
                    id text primary key,
                    label text not null,
                    db_url text not null,
                    docs_url text not null,
                    enabled integer not null default 1,
                    created_at text not null,
                    updated_at text not null
                );
                """
            )

    def record_report(self, *, user_id: str, report_name: str, report_path: Path, summary: dict[str, Any], modes: list[str]) -> None:
        with closing(self.connect()) as conn, conn:
            conn.execute(
                """
                insert into report_runs(user_id, report_name, report_path, scenario, runtime, modes_json, generated_at, total_tool_calls, total_a2a_messages, total_failures)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(user_id, report_name) do update set
                    report_path=excluded.report_path,
                    scenario=excluded.scenario,
                    runtime=excluded.runtime,
                    modes_json=excluded.modes_json,
                    generated_at=excluded.generated_at,
                    total_tool_calls=excluded.total_tool_calls,
                    total_a2a_messages=excluded.total_a2a_messages,
                    total_failures=excluded.total_failures
                """,
                (
                    user_id,
                    report_name,
                    str(report_path),
                    summary.get("scenario", "custom"),
                    summary.get("runtime", "mock"),
                    json.dumps(modes),
                    summary.get("generated_at", datetime.now(timezone.utc).isoformat()),
                    int(summary.get("total_tool_calls", 0)),
                    int(summary.get("total_a2a_messages", 0)),
                    int(summary.get("total_failures", 0)),
                ),
            )

    def record_run_event(self, *, user_id: str, event_type: str, mode: str, scenario: str, runtime: str, metrics: dict[str, Any], metadata: dict[str, Any] | None = None) -> None:
        with closing(self.connect()) as conn, conn:
            conn.execute(
                """
                insert into telemetry_events(user_id, event_type, mode, scenario, runtime, latency_ms, tool_calls, a2a_messages, failures, created_at, metadata_json)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    user_id,
                    event_type,
                    mode,
                    scenario,
                    runtime,
                    float(metrics.get("latency_ms", 0.0)),
                    int(metrics.get("tool_calls", 0)),
                    int(metrics.get("a2a_messages", 0)),
                    int(metrics.get("failures", 0)),
                    datetime.now(timezone.utc).isoformat(),
                    json.dumps(metadata or {}),
                ),
            )

    def telemetry_snapshot(self, user_id: str | None = None) -> TelemetrySnapshot:
        where = " where user_id = ?" if user_id else ""
        params: tuple[str, ...] = (user_id,) if user_id else ()
        with closing(self.connect()) as conn, conn:
            totals = conn.execute(
                f"select count(*) as runs, coalesce(sum(failures), 0) as failures, coalesce(avg(latency_ms), 0) as latency, coalesce(sum(tool_calls), 0) as tools, coalesce(sum(a2a_messages), 0) as a2a from telemetry_events{where}",
                params,
            ).fetchone()
            report_count = conn.execute(f"select count(*) as reports from report_runs{where}", params).fetchone()["reports"]
            users = [row["user_id"] for row in conn.execute("select distinct user_id from telemetry_events order by user_id")]
            mode_counts = {
                row["mode"] or "unknown": int(row["count"])
                for row in conn.execute(f"select mode, count(*) as count from telemetry_events{where} group by mode", params)
            }
            a2a_transport_counts: dict[str, int] = {}
            for row in conn.execute(f"select metadata_json from telemetry_events{where}", params):
                try:
                    metadata = json.loads(row["metadata_json"] or "{}")
                except json.JSONDecodeError:
                    metadata = {}
                transport = str(metadata.get("a2a_transport") or "local")
                a2a_transport_counts[transport] = a2a_transport_counts.get(transport, 0) + 1
        return TelemetrySnapshot(
            total_runs=int(totals["runs"]),
            total_reports=int(report_count),
            total_failures=int(totals["failures"]),
            avg_latency_ms=round(float(totals["latency"]), 3),
            tool_calls=int(totals["tools"]),
            a2a_messages=int(totals["a2a"]),
            users=users,
            mode_counts=mode_counts,
            a2a_transport_counts=a2a_transport_counts,
        )

    def list_remote_mcp_servers(self) -> list[dict[str, Any]]:
        with closing(self.connect()) as conn, conn:
            return [dict(row) for row in conn.execute("select id, label, db_url, docs_url, enabled, updated_at from remote_mcp_registry order by label")]

    def upsert_remote_mcp_server(self, *, server_id: str, label: str, db_url: str, docs_url: str, enabled: bool = True) -> dict[str, Any]:
        now = datetime.now(timezone.utc).isoformat()
        with closing(self.connect()) as conn, conn:
            conn.execute(
                """
                insert into remote_mcp_registry(id, label, db_url, docs_url, enabled, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?)
                on conflict(id) do update set label=excluded.label, db_url=excluded.db_url, docs_url=excluded.docs_url, enabled=excluded.enabled, updated_at=excluded.updated_at
                """,
                (server_id, label, db_url, docs_url, 1 if enabled else 0, now, now),
            )
        return {"id": server_id, "label": label, "db_url": db_url, "docs_url": docs_url, "enabled": enabled, "updated_at": now}

