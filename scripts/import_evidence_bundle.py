from __future__ import annotations

from pathlib import Path
import argparse
import json
import zipfile


REQUIRED_MEMBERS = {"manifest.json", "evidence/summary.json", "evidence/scenario.json"}


def inspect_bundle(path: Path, extract_dir: Path | None = None) -> int:
    if not path.exists():
        raise FileNotFoundError(path)
    with zipfile.ZipFile(path, "r") as archive:
        names = set(archive.namelist())
        missing = sorted(REQUIRED_MEMBERS - names)
        if missing:
            raise ValueError(f"Evidence bundle is missing required files: {', '.join(missing)}")
        manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
        summary = json.loads(archive.read("evidence/summary.json").decode("utf-8"))
        scenario = json.loads(archive.read("evidence/scenario.json").decode("utf-8"))
        trace_files = sorted(name for name in names if name.startswith("evidence/traces/") and name.endswith(".json"))
        logs = sorted(name for name in names if name.endswith(".ndjson"))
        print(f"Bundle: {path}")
        print(f"Report: {manifest.get('report_name', '')}")
        print(f"Scenario: {scenario.get('scenario', '')} ({scenario.get('ticket_id', '')})")
        print(f"Recommended mode: {(summary.get('scorecard') or {}).get('recommended_demo_mode', '')}")
        print(f"Trace files: {len(trace_files)}")
        print(f"NDJSON logs: {len(logs)}")
        if extract_dir is not None:
            extract_dir.mkdir(parents=True, exist_ok=True)
            archive.extractall(extract_dir)
            print(f"Extracted to: {extract_dir}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect and optionally extract an A2A vs MCP evidence bundle.")
    parser.add_argument("bundle", type=Path)
    parser.add_argument("--extract-dir", type=Path, help="Optional directory to extract the bundle into.")
    args = parser.parse_args()
    return inspect_bundle(args.bundle, args.extract_dir)


if __name__ == "__main__":
    raise SystemExit(main())
