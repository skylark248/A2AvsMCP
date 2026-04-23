from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import argparse
import csv
import json
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a2a_vs_mcp.config import resolve_profile
from a2a_vs_mcp.platform import DemoPlatform
from a2a_vs_mcp.reporting import ReportService


ALL_MODES = ["baseline", "mcp", "a2a", "hybrid"]
DEFAULT_SCENARIOS = ["order_status", "double_charge", "setup_error", "warranty_return"]
DEFAULT_TRANSPORTS = ["in_process"]


def parse_csv(value: str | None, default: list[str]) -> list[str]:
    if not value:
        return default
    return [item.strip() for item in value.split(",") if item.strip()]


def expected_checks(mode: str, result: dict[str, Any]) -> list[dict[str, Any]]:
    metrics = result["metrics"]
    checks = [
        {"name": "answer_present", "passed": bool(result.get("final_answer"))},
        {"name": "no_failures", "passed": int(metrics.get("failures", 0)) == 0},
    ]
    if mode == "mcp":
        checks.append({"name": "mcp_uses_tools", "passed": int(metrics.get("tool_calls", 0)) > 0})
        checks.append({"name": "mcp_has_no_a2a_messages", "passed": int(metrics.get("a2a_messages", 0)) == 0})
    if mode == "a2a":
        checks.append({"name": "a2a_uses_messages", "passed": int(metrics.get("a2a_messages", 0)) > 0})
        checks.append({"name": "a2a_has_no_tools", "passed": int(metrics.get("tool_calls", 0)) == 0})
    if mode == "hybrid":
        checks.append({"name": "hybrid_uses_tools", "passed": int(metrics.get("tool_calls", 0)) > 0})
        checks.append({"name": "hybrid_uses_messages", "passed": int(metrics.get("a2a_messages", 0)) > 0})
    return checks


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "scenario",
        "title",
        "mode",
        "transport",
        "runtime",
        "latency_ms",
        "tool_calls",
        "a2a_messages",
        "retries",
        "failures",
        "checks_passed",
        "checks_failed",
        "recommended_mode",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows({key: row.get(key, "") for key in fieldnames} for row in rows)


def write_html(path: Path, payload: dict[str, Any]) -> None:
    rows = []
    for row in payload["rows"]:
        tone = "fail" if row["checks_failed"] else "pass"
        rows.append(
            "<tr>"
            f"<td>{row['scenario']}</td>"
            f"<td>{row['mode']}</td>"
            f"<td>{row['transport']}</td>"
            f"<td>{row['latency_ms']}</td>"
            f"<td>{row['tool_calls']}</td>"
            f"<td>{row['a2a_messages']}</td>"
            f"<td>{row['failures']}</td>"
            f"<td class=\"{tone}\">{row['checks_passed']} passed / {row['checks_failed']} failed</td>"
            f"<td>{row['recommended_mode']}</td>"
            "</tr>"
        )
    path.write_text(
        """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>A2A vs MCP Evaluation</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 32px; color: #172033; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #d5dbe3; padding: 8px; text-align: left; }
    th { background: #edf2f7; }
    .pass { color: #0f6b3d; font-weight: 700; }
    .fail { color: #a01818; font-weight: 700; }
  </style>
</head>
<body>
  <h1>A2A vs MCP Evaluation</h1>
  <p>Generated at: GENERATED_AT</p>
  <p>Scenarios: SCENARIO_COUNT | Rows: ROW_COUNT</p>
  <table>
    <thead><tr><th>Scenario</th><th>Mode</th><th>Transport</th><th>Latency</th><th>Tools</th><th>A2A</th><th>Failures</th><th>Checks</th><th>Recommended</th></tr></thead>
    <tbody>ROWS</tbody>
  </table>
</body>
</html>""".replace("GENERATED_AT", payload["generated_at"])
        .replace("SCENARIO_COUNT", str(len(payload["scenarios"])))
        .replace("ROW_COUNT", str(len(payload["rows"])))
        .replace("ROWS", "\n".join(rows)),
        encoding="utf-8",
    )


def run_eval(args: argparse.Namespace) -> dict[str, Any]:
    scenarios = parse_csv(args.scenarios, DEFAULT_SCENARIOS)
    modes = parse_csv(args.modes, ALL_MODES)
    transports = parse_csv(args.transports, DEFAULT_TRANSPORTS)
    profile = resolve_profile(args.profile, runtime=args.runtime, save_report=args.save_reports, export_logs=args.export_logs)
    report_service = ReportService(PROJECT_ROOT)
    rows: list[dict[str, Any]] = []
    reports: list[dict[str, Any]] = []

    for transport in transports:
        platform = DemoPlatform(PROJECT_ROOT, runtime=profile.runtime, mcp_transport=transport, profile_name=profile.name, export_logs=profile.export_logs)
        for scenario in scenarios:
            ticket = platform.get_ticket(scenario, None, None)
            scenario_reports = []
            for mode in modes:
                output = platform.run(mode, ticket)
                result = output.to_dict()
                scenario_reports.append(result)
                checks = expected_checks(mode, result)
                failed = [check for check in checks if not check["passed"]]
                metrics = result["metrics"]
                rows.append(
                    {
                        "scenario": scenario,
                        "title": ticket.title,
                        "mode": mode,
                        "transport": transport,
                        "runtime": result["runtime"],
                        "latency_ms": metrics["latency_ms"],
                        "tool_calls": metrics["tool_calls"],
                        "a2a_messages": metrics["a2a_messages"],
                        "retries": metrics["retries"],
                        "failures": metrics["failures"],
                        "checks": checks,
                        "checks_passed": len(checks) - len(failed),
                        "checks_failed": len(failed),
                        "recommended_mode": "",
                    }
                )
            summary = report_service.summarize(f"{ticket.ticket_id}_eval.json", scenario_reports)
            for row in rows:
                if row["scenario"] == scenario and row["transport"] == transport:
                    row["recommended_mode"] = summary.scorecard.recommended_demo_mode if summary.scorecard else ""
            if args.save_reports:
                report_name = report_service.save_report(ticket, scenario_reports).name
            else:
                report_name = ""
            reports.append({"scenario": scenario, "transport": transport, "report_name": report_name, "summary": summary.to_dict()})

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "profile": profile.to_dict(),
        "scenarios": scenarios,
        "modes": modes,
        "transports": transports,
        "rows": rows,
        "reports": reports,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run repeatable evaluations across A2A vs MCP demo modes.")
    parser.add_argument("--profile", default="dev", choices=["dev", "demo", "llm"])
    parser.add_argument("--runtime", choices=["mock", "llm"], default="mock")
    parser.add_argument("--scenarios", help="Comma-separated scenario IDs.")
    parser.add_argument("--modes", help="Comma-separated modes. Defaults to all four modes.")
    parser.add_argument("--transports", help="Comma-separated MCP transports. Defaults to in_process.")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "artifacts" / "evals")
    parser.add_argument("--name", default="eval", help="Output filename prefix.")
    parser.add_argument("--save-reports", action="store_true", help="Also save normal report JSON for each scenario.")
    parser.add_argument("--export-logs", action="store_true", help="Export NDJSON traces during evaluation.")
    parser.add_argument("--html", action="store_true", help="Write a simple HTML summary next to JSON/CSV.")
    args = parser.parse_args()

    payload = run_eval(args)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    output_base = args.output_dir / f"{args.name}_{stamp}"
    json_path = output_base.with_suffix(".json")
    csv_path = output_base.with_suffix(".csv")
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    write_csv(csv_path, payload["rows"])
    if args.html:
        write_html(output_base.with_suffix(".html"), payload)
    failures = sum(int(row["checks_failed"]) for row in payload["rows"])
    print(f"Saved eval JSON: {json_path}")
    print(f"Saved eval CSV: {csv_path}")
    if args.html:
        print(f"Saved eval HTML: {output_base.with_suffix('.html')}")
    print(f"Evaluation rows: {len(payload['rows'])}; failed checks: {failures}")
    return 0 if failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
