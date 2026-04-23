from __future__ import annotations

from contextlib import closing
from pathlib import Path
from typing import Any
import argparse
import json
import sqlite3
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a2a_vs_mcp.persistence import PlatformStore


def rows(conn: sqlite3.Connection, query: str, params: tuple[Any, ...] = ()) -> list[dict[str, Any]]:
    return [dict(row) for row in conn.execute(query, params)]


def inspect_state(user_id: str | None = None) -> dict[str, Any]:
    store = PlatformStore(PROJECT_ROOT)
    where = " where user_id = ?" if user_id else ""
    params: tuple[Any, ...] = (user_id,) if user_id else ()
    with closing(store.connect()) as conn:
        return {
            "db_path": str(store.db_path),
            "telemetry": store.telemetry_snapshot(user_id).to_dict(),
            "users": rows(
                conn,
                "select user_id, count(*) as telemetry_events from telemetry_events group by user_id order by user_id",
            ),
            "reports": rows(
                conn,
                f"select user_id, report_name, scenario, runtime, generated_at, total_tool_calls, total_a2a_messages, total_failures, report_path from report_runs{where} order by generated_at desc",
                params,
            ),
            "remote_mcp_registry": rows(
                conn,
                "select id, label, db_url, docs_url, enabled, updated_at from remote_mcp_registry order by label",
            ),
        }


def print_human(payload: dict[str, Any]) -> None:
    telemetry = payload["telemetry"]
    print(f"Platform state: {payload['db_path']}")
    print(
        "Telemetry: "
        f"runs={telemetry['total_runs']} reports={telemetry['total_reports']} failures={telemetry['total_failures']} "
        f"avg_latency_ms={telemetry['avg_latency_ms']} tools={telemetry['tool_calls']} a2a={telemetry['a2a_messages']}"
    )
    print(f"Users: {', '.join(telemetry['users']) or 'none'}")
    print(f"Mode counts: {json.dumps(telemetry['mode_counts'], sort_keys=True)}")

    print("\nReports:")
    if not payload["reports"]:
        print("- none")
    for report in payload["reports"]:
        print(
            f"- {report['user_id']} | {report['report_name']} | {report['scenario']} | {report['runtime']} | "
            f"tools={report['total_tool_calls']} a2a={report['total_a2a_messages']} failures={report['total_failures']}"
        )

    print("\nRemote MCP Registry:")
    if not payload["remote_mcp_registry"]:
        print("- none")
    for server in payload["remote_mcp_registry"]:
        status = "enabled" if int(server["enabled"]) else "disabled"
        print(f"- {server['id']} | {server['label']} | {status} | db={server['db_url']} docs={server['docs_url']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect durable Phase 5 platform state.")
    parser.add_argument("--user-id", help="Filter report and telemetry totals to one user.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a compact text summary.")
    args = parser.parse_args()

    payload = inspect_state(args.user_id)
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print_human(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
