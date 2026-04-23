from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a2a_vs_mcp.platform import DemoPlatform
from a2a_vs_mcp.reporting import ReportService
from a2a_vs_mcp.schemas import FailureConfig


EXPECTED_EVENTS = {
    "baseline": set(),
    "mcp": {"tool_call"},
    "a2a": {"a2a_message"},
    "hybrid": {"tool_call", "a2a_message"},
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the golden local demo path and validate protocol trace shape.")
    parser.add_argument("--scenario", default="setup_and_warranty")
    parser.add_argument("--profile", default="demo")
    parser.add_argument("--mcp-transport", default="in_process", choices=["in_process", "stdio", "http", "remote_http"])
    parser.add_argument("--include-remote-a2a", action="store_true", help="Also run an A2A smoke through configured remote specialists.")
    parser.add_argument("--remote-a2a-token", default="")
    parser.add_argument("--skip-exports", action="store_true", help="Skip HTML/PDF report export checks.")
    parser.add_argument("--artifact-root", type=Path, default=None, help="Write generated smoke artifacts under this root instead of artifacts/.")
    return parser


def event_types(result: dict[str, Any]) -> set[str]:
    return {event.get("event_type", "") for event in result.get("trace", [])}


def assert_expected_trace(result: dict[str, Any]) -> None:
    mode = result["mode"]
    missing = EXPECTED_EVENTS.get(mode, set()) - event_types(result)
    if missing:
        raise AssertionError(f"{mode} trace missing expected events: {sorted(missing)}")
    if not result.get("final_answer"):
        raise AssertionError(f"{mode} did not produce a final answer")


def run_local_golden(args: argparse.Namespace) -> tuple[list[dict[str, Any]], Path]:
    platform = DemoPlatform(
        ROOT,
        profile_name=args.profile,
        runtime="mock",
        mcp_transport=args.mcp_transport,
        a2a_transport="local",
        export_logs=True,
    )
    ticket = platform.get_ticket(args.scenario, None, None)
    reports: list[dict[str, Any]] = []
    for mode in ("baseline", "mcp", "a2a", "hybrid"):
        output = platform.run(mode, ticket, FailureConfig())
        payload = output.to_dict()
        assert_expected_trace(payload)
        reports.append(payload)
        print(f"ok local {mode}: tools={payload['metrics']['tool_calls']} a2a={payload['metrics']['a2a_messages']} failures={payload['metrics']['failures']}")

    service = ReportService(ROOT)
    report_path = service.save_report(ticket, reports)
    print(f"ok saved report: {report_path}")
    if not args.skip_exports:
        html_path = report_path.with_suffix(".html")
        html_path.write_text(service.export_html(report_path.name, reports), encoding="utf-8")
        pdf_path = service.export_pdf(report_path.name, reports)
        if not html_path.exists() or not pdf_path.exists():
            raise AssertionError("Report exports were not created")
        print(f"ok exports: {html_path.name}, {pdf_path.name}")
    return reports, report_path


def run_remote_a2a_golden(args: argparse.Namespace) -> None:
    platform = DemoPlatform(
        ROOT,
        profile_name=args.profile,
        runtime="mock",
        mcp_transport="in_process",
        a2a_transport="remote",
        remote_a2a_auth_token=args.remote_a2a_token or None,
    )
    ticket = platform.get_ticket("warranty_return", None, None)
    output = platform.run("a2a", ticket, FailureConfig())
    payload = output.to_dict()
    types = event_types(payload)
    for expected in ("a2a_remote_discovery", "a2a_remote_send", "a2a_remote_artifact"):
        if expected not in types:
            raise AssertionError(f"remote A2A trace missing {expected}")
    if payload.get("failures"):
        raise AssertionError(f"remote A2A run recorded failures: {payload['failures']}")
    print(f"ok remote a2a: agents={len(payload['agents_used'])} a2a={payload['metrics']['a2a_messages']}")


def main() -> int:
    args = build_parser().parse_args()
    if args.artifact_root is not None:
        artifact_root = args.artifact_root if args.artifact_root.is_absolute() else ROOT / args.artifact_root
        artifact_root.mkdir(parents=True, exist_ok=True)
        os.environ["A2A_VS_MCP_ARTIFACT_ROOT"] = str(artifact_root)
    run_local_golden(args)
    if args.include_remote_a2a:
        run_remote_a2a_golden(args)
    print("golden demo smoke: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())