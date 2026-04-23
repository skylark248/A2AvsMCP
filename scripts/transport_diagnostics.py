from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import argparse
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a2a_vs_mcp.platform import DemoPlatform


def parse_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def summarize_transport_events(result: dict[str, Any]) -> dict[str, Any]:
    discovery = [event for event in result["trace"] if event.get("event_type") == "tool_discovery"]
    fallbacks = [event for event in result["trace"] if event.get("event_type") == "tool_transport_fallback"]
    calls = [event for event in result["trace"] if event.get("event_type") == "tool_call"]
    active_transports = sorted({event.get("transport", "") for event in discovery + calls if event.get("transport")})
    requested_transports = sorted({event.get("requested_transport", "") for event in discovery + calls if event.get("requested_transport")})
    return {
        "requested_transports": requested_transports,
        "active_transports": active_transports,
        "tool_discoveries": len(discovery),
        "tool_calls": len(calls),
        "fallbacks": fallbacks,
        "failures": result.get("failures", []),
        "metrics": result["metrics"],
    }


def run_diagnostics(args: argparse.Namespace) -> dict[str, Any]:
    transports = parse_csv(args.transports, ["in_process", "stdio", "http"])
    modes = parse_csv(args.modes, ["mcp", "hybrid"])
    rows = []
    for transport in transports:
        platform = DemoPlatform(PROJECT_ROOT, runtime="mock", mcp_transport=transport, profile_name="dev", export_logs=False)
        ticket = platform.get_ticket(args.scenario, None, None)
        for mode in modes:
            output = platform.run(mode, ticket)
            result = output.to_dict()
            rows.append(
                {
                    "scenario": args.scenario,
                    "mode": mode,
                    "requested_transport": transport,
                    **summarize_transport_events(result),
                }
            )
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scenario": args.scenario,
        "rows": rows,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MCP transport diagnostics across demo modes.")
    parser.add_argument("--scenario", default="setup_error")
    parser.add_argument("--transports", help="Comma-separated transports. Defaults to in_process,stdio,http.")
    parser.add_argument("--modes", help="Comma-separated modes. Defaults to mcp,hybrid.")
    parser.add_argument("--output", type=Path, default=PROJECT_ROOT / "artifacts" / "transport_diagnostics.json")
    args = parser.parse_args()
    payload = run_diagnostics(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved transport diagnostics: {args.output}")
    for row in payload["rows"]:
        fallback_count = len(row["fallbacks"])
        active = ",".join(row["active_transports"]) or "none"
        print(f"{row['mode']} requested={row['requested_transport']} active={active} tool_calls={row['tool_calls']} fallbacks={fallback_count}")
    failures = [row for row in payload["rows"] if row["fallbacks"] or row["failures"]]
    return 1 if failures and args.output is None else 0


if __name__ == "__main__":
    raise SystemExit(main())
