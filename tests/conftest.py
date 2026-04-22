"""Shared pytest configuration: sys.path setup and test environment variables."""
from __future__ import annotations

import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"

if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault(
    "A2A_VS_MCP_ARTIFACT_ROOT",
    str(PROJECT_ROOT / ".tmp" / "test_artifacts"),
)
