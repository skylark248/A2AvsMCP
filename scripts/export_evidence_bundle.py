from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import argparse
import json
import sys
import zipfile


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a2a_vs_mcp.reporting import ReportService


def safe_arcname(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:
        return path.name


def load_report(report_name: str) -> tuple[ReportService, list[dict[str, Any]]]:
    service = ReportService(PROJECT_ROOT)
    return service, service.load_report(report_name)


def collect_existing_file(path_value: str | None) -> Path | None:
    if not path_value:
        return None
    path = Path(path_value)
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if path.exists() and path.is_file():
        return path
    return None


def bundle_report(report_name: str, output_dir: Path) -> Path:
    service, payload = load_report(report_name)
    summary = service.summarize(report_name, payload).to_dict()
    first = payload[0] if payload else {}
    ticket = first.get("ticket", {})
    generated_at = datetime.now(timezone.utc).isoformat()
    manifest = {
        "bundle_type": "a2a_vs_mcp_evidence_bundle",
        "generated_at": generated_at,
        "report_name": report_name,
        "scenario": ticket.get("scenario", ""),
        "ticket_id": ticket.get("ticket_id", ""),
        "runtime": first.get("runtime", ""),
        "modes": [item.get("mode", "") for item in payload],
        "files": [],
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = output_dir / f"{Path(report_name).stem}_evidence_bundle.zip"
    report_path = service.resolve_report_path(report_name)
    with zipfile.ZipFile(bundle_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.write(report_path, safe_arcname(report_path))
        manifest["files"].append(safe_arcname(report_path))

        summary_bytes = json.dumps(summary, indent=2).encode("utf-8")
        archive.writestr("evidence/summary.json", summary_bytes)
        manifest["files"].append("evidence/summary.json")

        scenario_bytes = json.dumps(ticket, indent=2).encode("utf-8")
        archive.writestr("evidence/scenario.json", scenario_bytes)
        manifest["files"].append("evidence/scenario.json")

        for item in payload:
            mode = item.get("mode", "unknown")
            trace_name = f"evidence/traces/{mode}.json"
            archive.writestr(trace_name, json.dumps(item.get("trace", []), indent=2).encode("utf-8"))
            manifest["files"].append(trace_name)

            log_path = collect_existing_file(item.get("external_log_path"))
            if log_path is not None:
                arcname = safe_arcname(log_path)
                archive.write(log_path, arcname)
                manifest["files"].append(arcname)

            trace_file = None
            for event in item.get("trace", []):
                if event.get("event_type") == "comparison_report":
                    trace_file = collect_existing_file(event.get("trace_file"))
                    break
            if trace_file is not None:
                arcname = safe_arcname(trace_file)
                if arcname not in manifest["files"]:
                    archive.write(trace_file, arcname)
                    manifest["files"].append(arcname)

        archive.writestr("manifest.json", json.dumps(manifest, indent=2).encode("utf-8"))
    return bundle_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Export a saved report as a self-contained evidence bundle.")
    parser.add_argument("report_name", help="Saved report filename, for example TICKET-1001_report.json")
    parser.add_argument("--output-dir", type=Path, default=PROJECT_ROOT / "artifacts" / "evidence")
    args = parser.parse_args()
    bundle_path = bundle_report(args.report_name, args.output_dir)
    print(f"Saved evidence bundle: {bundle_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
