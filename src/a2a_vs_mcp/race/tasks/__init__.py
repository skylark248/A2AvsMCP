"""Race tasks package - startup validation hook (D-28 + RESEARCH §7).

V1_TASK_IDS lists the 3 v1 tasks. The TASK_CONFIGS module-level dict-comp
runs at first import; any typo in any task_config.yaml -> ValidationError at
import time -> pytest --collect-only fails noisy.
"""
from __future__ import annotations

from .loader import load_task_config


V1_TASK_IDS: list[str] = ["summarize_repo", "negotiate_meeting", "book_travel"]

# Module-load validation: triggers loader cross-validation for all 3 tasks.
TASK_CONFIGS: dict[str, tuple] = {tid: load_task_config(tid) for tid in V1_TASK_IDS}
