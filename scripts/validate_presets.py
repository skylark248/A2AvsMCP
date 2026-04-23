from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PRESETS_PATH = PROJECT_ROOT / "DEMO_PRESETS.json"
SCENARIOS_PATH = PROJECT_ROOT / "src" / "a2a_vs_mcp" / "data" / "seeds" / "scenarios.json"

ALLOWED_MODES = {"baseline", "mcp", "a2a", "hybrid", "all"}
ALLOWED_PROFILES = {"dev", "demo", "llm"}
ALLOWED_RUNTIMES = {"mock", "llm"}
ALLOWED_TRANSPORTS = {"in_process", "stdio", "http", "remote_http"}
ALLOWED_FAILURE_TOGGLES = {"db_down", "docs_timeout", "malformed_task"}
REQUIRED_FIELDS = {
    "id",
    "title",
    "description",
    "scenario",
    "mode",
    "profile",
    "runtime",
    "mcp_transport",
    "failure_toggles",
}
ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Missing file: {path}") from None
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc


def validate_presets() -> tuple[list[str], list[str], dict[str, Any]]:
    presets = load_json(PRESETS_PATH)
    scenarios = load_json(SCENARIOS_PATH)
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(presets, list):
        return ["DEMO_PRESETS.json must contain a JSON array."], warnings, {"preset_count": 0}
    if not isinstance(scenarios, list):
        return ["scenarios.json must contain a JSON array."], warnings, {"preset_count": len(presets)}

    scenario_ids = {item.get("scenario") for item in scenarios if isinstance(item, dict)}
    seen_ids: set[str] = set()

    for index, preset in enumerate(presets):
        label = f"preset[{index}]"
        if not isinstance(preset, dict):
            errors.append(f"{label}: expected an object.")
            continue

        preset_id = str(preset.get("id", "")).strip()
        label = preset_id or label
        missing = sorted(REQUIRED_FIELDS - preset.keys())
        if missing:
            errors.append(f"{label}: missing required fields: {', '.join(missing)}")

        if not preset_id:
            errors.append(f"{label}: id is required.")
        elif not ID_PATTERN.fullmatch(preset_id):
            errors.append(f"{label}: id must be lowercase snake_case.")
        elif preset_id in seen_ids:
            errors.append(f"{label}: duplicate preset id.")
        else:
            seen_ids.add(preset_id)

        for field in ("title", "description"):
            if not isinstance(preset.get(field), str) or not preset.get(field, "").strip():
                errors.append(f"{label}: {field} must be a non-empty string.")

        scenario = preset.get("scenario")
        if scenario not in scenario_ids:
            errors.append(f"{label}: scenario {scenario!r} does not exist in scenarios.json.")

        if preset.get("mode") not in ALLOWED_MODES:
            errors.append(f"{label}: mode must be one of {sorted(ALLOWED_MODES)}.")
        if preset.get("profile") not in ALLOWED_PROFILES:
            errors.append(f"{label}: profile must be one of {sorted(ALLOWED_PROFILES)}.")
        if preset.get("runtime") not in ALLOWED_RUNTIMES:
            errors.append(f"{label}: runtime must be one of {sorted(ALLOWED_RUNTIMES)}.")
        if preset.get("mcp_transport") not in ALLOWED_TRANSPORTS:
            errors.append(f"{label}: mcp_transport must be one of {sorted(ALLOWED_TRANSPORTS)}.")

        toggles = preset.get("failure_toggles")
        if not isinstance(toggles, list):
            errors.append(f"{label}: failure_toggles must be a list.")
        else:
            unknown_toggles = [item for item in toggles if item not in ALLOWED_FAILURE_TOGGLES]
            if unknown_toggles:
                errors.append(f"{label}: unknown failure toggles: {', '.join(map(str, unknown_toggles))}")
            if len(toggles) != len(set(toggles)):
                warnings.append(f"{label}: duplicate failure toggles will be ignored by the UI.")

        if preset.get("mcp_transport") == "remote_http":
            warnings.append(f"{label}: remote_http presets need user-provided remote MCP URLs at run time.")

    summary = {
        "preset_count": len(presets),
        "scenario_count": len(scenario_ids),
        "validated_file": str(PRESETS_PATH),
    }
    return errors, warnings, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate DEMO_PRESETS.json against the local scenario catalog.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable validation output.")
    args = parser.parse_args()

    errors, warnings, summary = validate_presets()
    if args.json:
        print(json.dumps({"ok": not errors, "summary": summary, "warnings": warnings, "errors": errors}, indent=2))
    else:
        print(f"Validated {summary['preset_count']} demo presets against {summary['scenario_count']} scenarios.")
        for warning in warnings:
            print(f"WARNING: {warning}")
        for error in errors:
            print(f"ERROR: {error}")

    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
