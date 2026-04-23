from __future__ import annotations

import os
from pathlib import Path
import re


DEFAULT_USER_ID = "default"
USER_ID_PATTERN = re.compile(r"[^A-Za-z0-9_.-]+")


def normalize_user_id(value: str | None) -> str:
    raw = (value or DEFAULT_USER_ID).strip() or DEFAULT_USER_ID
    normalized = USER_ID_PATTERN.sub("_", raw)[:64].strip("._-")
    return normalized or DEFAULT_USER_ID


def base_artifact_root(project_root: Path) -> Path:
    override = os.getenv("A2A_VS_MCP_ARTIFACT_ROOT", "").strip()
    if not override:
        return project_root / "artifacts"
    path = Path(override)
    return path if path.is_absolute() else project_root / path


def user_artifact_root(project_root: Path, user_id: str | None) -> Path:
    root = base_artifact_root(project_root)
    normalized = normalize_user_id(user_id)
    if normalized == DEFAULT_USER_ID:
        return root
    return root / "users" / normalized