from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a2a_vs_mcp.platform import DemoPlatform


def transport_events(result: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        event
        for event in result["trace"]
        if event.get("event_type") in {"tool_transport_fallback", "tool_discovery", "tool_call"}
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Check explicit remote_http MCP endpoints without accepting local fallback.")
    parser.add_argument("--db-url", required=True, help="Remote DB MCP URL.")
    parser.add_argument("--docs-url", required=True, help="Remote docs MCP URL.")
    parser.add_argument("--scenario", default="setup_error")
    parser.add_argument("--mode", choices=["mcp", "hybrid"], default="mcp")
    args = parser.parse_args()

    platform = DemoPlatform(
        PROJECT_ROOT,
        runtime="mock",
        mcp_transport="remote_http",
        profile_name="dev",
        export_logs=False,
        remote_mcp_urls={"db": args.db_url, "docs": args.docs_url},
    )
    ticket = platform.get_ticket(args.scenario, None, None)
    result = platform.run(args.mode, ticket).to_dict()
    events = transport_events(result)
    fallbacks = [event for event in events if event.get("event_type") == "tool_transport_fallback"]
    active = sorted({event.get("transport", "") for event in events if event.get("transport")})

    if fallbacks:
        print("Remote MCP readiness: FAIL")
        for event in fallbacks:
            server = event.get("server", "unknown")
            error = event.get("error", "unknown error")
            print(f"- {server}: fell back from remote_http ({error})")
        return 1

    if "remote_http" not in active:
        print("Remote MCP readiness: FAIL")
        print(f"- expected active remote_http transport, saw: {', '.join(active) or 'none'}")
        return 1

    print("Remote MCP readiness: PASS")
    print(f"scenario={args.scenario} mode={args.mode} active={','.join(active)} tool_calls={result['metrics']['tool_calls']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
