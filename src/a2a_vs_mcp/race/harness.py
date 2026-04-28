"""Race harness — concurrency, retry classifier, race_done emitter, headlines.

Owns:

  * D-38 ``asyncio.Semaphore(8)`` concurrency cap (env-overridable via
    ``RACE_HARNESS_CONCURRENCY``) so all in-flight (lane × task × run_idx)
    coroutines share one budget instead of stampeding the Anthropic Tier-1
    rate cap.
  * Closed-tuple retry classifier ``TRANSIENT_RETRY_TYPES`` — only the four
    Anthropic transient infra exceptions are retried; the injected-fault
    exception type from race/failure.py is NEVER caught here. Adding it would
    silently mask the very faults the race demo is testing.
  * Per-run ``asyncio.wait_for(..., PER_RUN_TIMEOUT_S)`` so a wedged runner
    cannot deadlock the harness.
  * D-39 ``race_done`` event emission (single per ``run_race`` call) with
    ``t_end_ms``, ``total_runs``, ``lane_failed_reasons``, and the per-(lane,
    task) headline sentence produced by ``failure_mode_classifier``
    (RACE-06).
  * D-41 + Phase 6 D-08 NEVER_COALESCE preservation: ``fault_observed``
    events are forwarded by recorders inside runners; the harness does not
    filter, coalesce, or re-emit them.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import sys
import time
import uuid
from typing import Any, Awaitable, Callable

import anthropic

from ..trace import TraceRecorder
from .classifier import failure_mode_classifier
# NOTE: race/failure.py exports the injected-fault exception type; it is
# DELIBERATELY not imported here. Including it in TRANSIENT_RETRY_TYPES (or
# referencing it in any except arm) would mask the faults under test.
from .failure import FailureScriptEntry  # typing only
from .metrics import aggregate_for_classifier
from .runners import run_hybrid, run_pure_a2a, run_pure_mcp
from .tasks import TASK_CONFIGS
from .types import HardnessProfile, HardnessType, RaceResult, ScoreCard, TaskSpec


# ---------------------------------------------------------------------------
# Module constants — pinned at load time per RESEARCH §2 + master design.
# ---------------------------------------------------------------------------

MODEL = "claude-sonnet-4-6"
# SEED_DISCLOSURE: Anthropic's chat-completion SDK has NO seed parameter
# (RESEARCH §3). This constant is a methodology-disclosure token only —
# documented in the README as part of the harness reproducibility statement
# alongside temperature=0 and the locked failure_script.
SEED_DISCLOSURE = 42
TEMPERATURE = 0.0
PER_RUN_TIMEOUT_S = 120

# D-38: Tier-1 sized default; envvar override allowed for power users.
_CONC: int = int(os.getenv("RACE_HARNESS_CONCURRENCY", "8"))
_SEMAPHORE: asyncio.Semaphore = asyncio.Semaphore(_CONC)

# Closed tuple — no Exception fallback, no broad catch. If a new transient
# Anthropic type appears, the harness fails loudly so we add it explicitly.
TRANSIENT_RETRY_TYPES: tuple[type[BaseException], ...] = (
    anthropic.APIConnectionError,
    anthropic.APITimeoutError,
    anthropic.InternalServerError,
    anthropic.RateLimitError,
)


# Runner registry — keyed by lane string. Imported once at module load so the
# closed set is a structural constant.
_RUNNERS: dict[str, Callable[..., Awaitable[RaceResult]]] = {
    "pure_mcp": run_pure_mcp,
    "pure_a2a": run_pure_a2a,
    "hybrid": run_hybrid,
}


__all__ = [
    "run_race",
    "MODEL",
    "TEMPERATURE",
    "PER_RUN_TIMEOUT_S",
    "SEED_DISCLOSURE",
    "TRANSIENT_RETRY_TYPES",
]


# ---------------------------------------------------------------------------
# run_race stub — filled in Task 3.
# ---------------------------------------------------------------------------

async def run_race(
    task_specs: list[TaskSpec],
    lanes: list[str],
    n: int,
    *,
    recorder_factory: Callable[..., TraceRecorder],
    ws_emitter: Callable[[dict[str, Any]], None],
    hybrid_plans: dict[str, Any] | None = None,
) -> dict[tuple[str, str], list[RaceResult]]:
    """Fan out (lane × task × run_idx) tuples under ``_SEMAPHORE``.

    Filled in Task 3.
    """
    raise NotImplementedError("filled in Task 3")
