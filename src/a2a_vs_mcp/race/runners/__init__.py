"""Race runners — three lanes (pure_mcp, pure_a2a, hybrid).

Each runner consumes a TaskSpec + failure_script and returns a RaceResult of
identical shape. Detector(K=3) is wired inline per fault_injected event so
runners are replay-symmetric with classifier.py by construction (D-32, D-33).
"""
from __future__ import annotations

from .pure_mcp import run_pure_mcp
from .pure_a2a import run_pure_a2a
from .hybrid import run_hybrid

__all__ = ["run_pure_mcp", "run_pure_a2a", "run_hybrid"]
