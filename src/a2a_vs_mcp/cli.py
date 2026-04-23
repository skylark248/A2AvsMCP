from __future__ import annotations

import argparse
from pathlib import Path

from .config import PROFILES, resolve_profile
from .platform import DemoPlatform
from .reporting import ReportService
from .schemas import FailureConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the A2A vs MCP support demo.")
    parser.add_argument("--profile", choices=sorted(PROFILES.keys()), help="Apply a named runtime profile before explicit overrides.")
    parser.add_argument("--mode", choices=["baseline", "mcp", "a2a", "hybrid", "all"], default="all")
    parser.add_argument("--scenario", default="order_status")
    parser.add_argument("--query", help="Custom support query. Overrides --scenario when provided.")
    parser.add_argument("--customer-id", help="Customer for custom queries.")
    parser.add_argument("--runtime", choices=["mock", "llm"], default=None)
    parser.add_argument("--mcp-transport", choices=["in_process", "stdio", "http", "remote_http"], default=None)
    parser.add_argument("--a2a-transport", choices=["local", "remote"], default=None)
    parser.add_argument("--save-report", action=argparse.BooleanOptionalAction, default=None, help="Persist JSON outputs under artifacts/reports.")
    parser.add_argument("--export-logs", action=argparse.BooleanOptionalAction, default=None, help="Export NDJSON structured logs under artifacts/logs.")
    parser.add_argument("--remote-mcp-db-url", help="Remote streamable HTTP MCP URL for the database server role.")
    parser.add_argument("--remote-mcp-docs-url", help="Remote streamable HTTP MCP URL for the docs server role.")
    parser.add_argument("--remote-a2a-customer-url", help="Remote A2A customer-data specialist base URL.")
    parser.add_argument("--remote-a2a-documentation-url", help="Remote A2A setup/documentation specialist base URL.")
    parser.add_argument("--remote-a2a-policy-url", help="Remote A2A policy/billing specialist base URL.")
    parser.add_argument("--remote-a2a-auth-token", help="Optional demo bearer token for remote A2A specialist servers.")
    parser.add_argument("--export-report-html", action="store_true", help="Render a presentation-friendly HTML report after the run.")
    parser.add_argument("--export-report-pdf", action="store_true", help="Render a presentation-friendly PDF report after the run.")
    parser.add_argument("--db-down", action="store_true", help="Simulate a database outage for MCP-backed flows.")
    parser.add_argument("--docs-timeout", action="store_true", help="Simulate a docs timeout for MCP-backed flows.")
    parser.add_argument("--disable-agent", action="append", choices=["customer_data_agent", "documentation_agent", "policy_or_billing_agent"], default=[], help="Simulate an unavailable specialist agent.")
    parser.add_argument("--malformed-task", action="store_true", help="Send a malformed policy/billing task in A2A modes.")
    parser.add_argument("--remote-a2a-timeout", action="store_true", help="Simulate a hosted remote A2A specialist timeout.")
    parser.add_argument("--remote-a2a-bad-auth", action="store_true", help="Simulate a remote A2A authentication failure.")
    parser.add_argument("--remote-a2a-missing-capability", action="store_true", help="Simulate a remote Agent Card missing a required capability.")
    parser.add_argument("--remote-a2a-malformed-response", action="store_true", help="Simulate a malformed hosted remote A2A response.")
    parser.add_argument("--remote-a2a-task-failure", action="store_true", help="Simulate a hosted remote A2A task failure.")
    return parser


def render_output(result: dict) -> str:
    metrics = result["metrics"]
    lines = [
        f"Mode: {result['mode']}",
        f"Scenario: {result['ticket']['scenario']}",
        f"Answer: {result['final_answer']}",
        f"Agents: {', '.join(result['agents_used'])}",
        f"Tools: {', '.join(result['tools_used']) if result['tools_used'] else 'None'}",
        f"Latency: {metrics['latency_ms']} ms",
        f"A2A messages: {metrics['a2a_messages']}",
        f"Tool calls: {metrics['tool_calls']}",
        f"Retries: {metrics['retries']}",
        f"Failures: {metrics['failures']}",
        f"Strengths: {', '.join(metrics['strengths'])}",
        f"Weaknesses: {', '.join(metrics['weaknesses'])}",
    ]
    if result.get("failures"):
        lines.append(f"Failure details: {' | '.join(result['failures'])}")
    if result.get("external_log_path"):
        lines.append(f"External log: {result['external_log_path']}")
    return "\n".join(lines)


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    project_root = Path(__file__).resolve().parents[2]
    report_service = ReportService(project_root)
    profile = resolve_profile(
        args.profile,
        runtime=args.runtime,
        mcp_transport=args.mcp_transport,
        a2a_transport=args.a2a_transport,
        save_report=args.save_report,
        export_logs=args.export_logs,
    )
    platform = DemoPlatform(
        project_root,
        runtime=profile.runtime,
        mcp_transport=profile.mcp_transport,
        a2a_transport=profile.a2a_transport,
        profile_name=profile.name,
        export_logs=profile.export_logs,
        remote_mcp_urls={"db": args.remote_mcp_db_url or "", "docs": args.remote_mcp_docs_url or ""},
        remote_a2a_urls={
            "customer_data": args.remote_a2a_customer_url or "",
            "documentation": args.remote_a2a_documentation_url or "",
            "policy_billing": args.remote_a2a_policy_url or "",
        } if args.remote_a2a_customer_url or args.remote_a2a_documentation_url or args.remote_a2a_policy_url else None,
        remote_a2a_auth_token=args.remote_a2a_auth_token,
    )
    ticket = platform.get_ticket(None if args.query else args.scenario, args.query, args.customer_id)
    failure_config = FailureConfig(
        db_down=args.db_down,
        docs_timeout=args.docs_timeout,
        unavailable_agents=args.disable_agent,
        malformed_task=args.malformed_task,
        remote_a2a_timeout=args.remote_a2a_timeout,
        remote_a2a_bad_auth=args.remote_a2a_bad_auth,
        remote_a2a_missing_capability=args.remote_a2a_missing_capability,
        remote_a2a_malformed_response=args.remote_a2a_malformed_response,
        remote_a2a_task_failure=args.remote_a2a_task_failure,
    )
    print(f"Profile: {profile.name} | runtime={profile.runtime} | mcp_transport={profile.mcp_transport} | a2a_transport={profile.a2a_transport} | save_report={profile.save_report} | export_logs={profile.export_logs}")
    modes = ["baseline", "mcp", "a2a", "hybrid"] if args.mode == "all" else [args.mode]
    reports = []
    for mode in modes:
        output = platform.run(mode, ticket, failure_config=failure_config)
        payload = output.to_dict()
        reports.append(payload)
        print(render_output(payload))
        print("-" * 60)
    report_path = None
    if profile.save_report or args.export_report_html or args.export_report_pdf:
        report_path = report_service.save_report(ticket, reports)
        if profile.save_report:
            print(f"Saved report to {report_path}")
    if args.export_report_html:
        report_name = report_path.name if report_path else f"{ticket.ticket_id}_report.json"
        export_path = report_service.report_dir / f"{ticket.ticket_id}_report.html"
        export_path.write_text(report_service.export_html(report_name, reports), encoding="utf-8")
        print(f"Exported HTML report to {export_path}")
    if args.export_report_pdf:
        report_name = report_path.name if report_path else f"{ticket.ticket_id}_report.json"
        export_path = report_service.export_pdf(report_name, reports)
        print(f"Exported PDF report to {export_path}")
    return 0




