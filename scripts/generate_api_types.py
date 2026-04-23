from __future__ import annotations

import keyword
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from a2a_vs_mcp.web import app
OUTPUT = ROOT / "frontend" / "src" / "lib" / "types" / "api.generated.ts"


def ts_name(name: str) -> str:
    return name if name.isidentifier() and not keyword.iskeyword(name) else f'"{name}"'


def ref_name(ref: str) -> str:
    return ref.rsplit("/", 1)[-1]


def literal(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return repr(str(value)).replace("'", '"')


def schema_type(schema: dict[str, Any] | bool | None, components: dict[str, Any]) -> str:
    if schema is None or schema is True:
        return "unknown"
    if schema is False:
        return "never"
    if "$ref" in schema:
        return ref_name(schema["$ref"])
    if "const" in schema:
        return literal(schema["const"])
    if "enum" in schema:
        return " | ".join(literal(item) for item in schema["enum"])
    if "anyOf" in schema or "oneOf" in schema:
        variants = schema.get("anyOf") or schema.get("oneOf") or []
        return " | ".join(schema_type(item, components) for item in variants)
    if "allOf" in schema:
        variants = schema.get("allOf") or []
        return " & ".join(schema_type(item, components) for item in variants)

    schema_type_value = schema.get("type")
    if isinstance(schema_type_value, list):
        return " | ".join(schema_type({**schema, "type": item}, components) for item in schema_type_value)
    if schema_type_value == "string":
        return "string"
    if schema_type_value in {"integer", "number"}:
        return "number"
    if schema_type_value == "boolean":
        return "boolean"
    if schema_type_value == "null":
        return "null"
    if schema_type_value == "array":
        item_type = schema_type(schema.get("items", {}), components)
        return f"Array<{item_type}>"
    if schema_type_value == "object" or "properties" in schema:
        if "properties" in schema:
            return inline_object(schema, components)
        additional = schema.get("additionalProperties")
        if isinstance(additional, dict):
            return f"Record<string, {schema_type(additional, components)}>"
        return "Record<string, unknown>"
    return "unknown"


def inline_object(schema: dict[str, Any], components: dict[str, Any]) -> str:
    props = schema.get("properties", {})
    required = set(schema.get("required", []))
    lines = ["{"]
    for name, prop_schema in props.items():
        optional = "" if name in required else "?"
        lines.append(f"  {ts_name(name)}{optional}: {schema_type(prop_schema, components)};")
    if schema.get("additionalProperties") is True:
        lines.append("  [key: string]: unknown;")
    lines.append("}")
    return "\n".join(lines)


def emit_component(name: str, schema: dict[str, Any], components: dict[str, Any]) -> str:
    if schema.get("type") == "object" or "properties" in schema:
        props = schema.get("properties", {})
        required = set(schema.get("required", []))
        lines = [f"export interface {name} {{"]
        for prop_name, prop_schema in props.items():
            optional = "" if prop_name in required else "?"
            lines.append(f"  {ts_name(prop_name)}{optional}: {schema_type(prop_schema, components)};")
        if schema.get("additionalProperties") is True:
            lines.append("  [key: string]: unknown;")
        lines.append("}")
        return "\n".join(lines)
    return f"export type {name} = {schema_type(schema, components)};"


def main() -> None:
    openapi = app.openapi()
    components = openapi.get("components", {}).get("schemas", {})
    lines = [
        "// Generated from FastAPI OpenAPI by scripts/generate_api_types.py.",
        "// Do not edit by hand; update backend schemas and rerun the generator.",
        "",
    ]
    for name in sorted(components):
        if name.startswith("HTTPValidationError") or name == "ValidationError":
            continue
        lines.append(emit_component(name, components[name], components))
        lines.append("")
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()

