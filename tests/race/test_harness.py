"""Harness tests — D-38 IRON RULE + Semaphore + per-run timeout (RACE-03).

Asserts:
- Semaphore(8) caps concurrent in-flight runs to 8.
- InjectedFaultError NEVER caught by retry classifier (bubbles up).
- anthropic.RateLimitError IS retried up to 3 attempts.
- anthropic.APIConnectionError IS retried.
- ValueError (unknown exception) propagates without retry.
- Per-run timeout produces lane_failed/timeout ScoreCard.
- race_done event emitted exactly once at end of run_race.
- Each (lane, task) pair gets a non-empty headline.
"""
from __future__ import annotations

import asyncio
import time
import unittest
from typing import Any
from unittest.mock import patch

import anthropic

from a2a_vs_mcp.race import harness as harness_mod
from a2a_vs_mcp.race.failure import InjectedFaultError
from a2a_vs_mcp.race.types import (
    HardnessProfile,
    HardnessType,
    RaceResult,
    ScoreCard,
    TaskSpec,
)
from a2a_vs_mcp.trace import TraceRecorder


def _make_spec(task_id: str = "summarize_repo") -> TaskSpec:
    return TaskSpec(
        task_id=task_id,
        prompt="",
        allowed_tools=[],
        expected_shape={},
        hardness_profile=HardnessProfile(types=[HardnessType.LONG_CHAIN]),
    )


def _good_result(lane: str, task_id: str, run_id: str) -> RaceResult:
    return RaceResult(
        run_id=run_id,
        lane=lane,
        task_id=task_id,
        hardness_profile=HardnessProfile(types=[HardnessType.LONG_CHAIN]),
        score_card=ScoreCard(
            success=True, ttff_ms=10, recovered=True,
            wasted_tokens_before_detection=0,
            failure_mode="success", cost_usd=0.0, latency_ms=10,
        ),
        trace_id=run_id,
    )


class TestHarnessSemaphoreCap(unittest.TestCase):
    """D-38: concurrent in-flight cap = 8."""

    def test_concurrent_in_flight_capped_at_eight(self) -> None:
        in_flight: list[int] = []
        max_seen: list[int] = [0]
        active = 0
        lock = asyncio.Lock() if False else None  # not needed — single-threaded asyncio

        async def fake_runner(task_spec, run_id, recorder, failure_script, sonnet_client, **kw) -> RaceResult:
            nonlocal active
            active += 1
            in_flight.append(active)
            if active > max_seen[0]:
                max_seen[0] = active
            await asyncio.sleep(0.05)
            active -= 1
            return _good_result(task_spec.hardness_profile.types[0].value, task_spec.task_id, run_id)

        # Patch all 3 runners to fake.
        with patch.dict(harness_mod._RUNNERS, {
            "pure_mcp": fake_runner,
            "pure_a2a": fake_runner,
            "hybrid": fake_runner,
        }):
            specs = [_make_spec("summarize_repo")]
            ws_events: list[dict] = []

            def factory(*, run_id, lane, task_id):
                return TraceRecorder(mode=lane, runtime="mock", task_id=task_id)

            asyncio.run(harness_mod.run_race(
                specs, ["pure_mcp"], n=16,
                recorder_factory=factory,
                ws_emitter=lambda ev: ws_events.append(ev),
            ))
        # 16 runs total; semaphore caps in_flight at 8.
        self.assertLessEqual(max_seen[0], 8, f"saw {max_seen[0]} concurrent in-flight; cap is 8")


class TestHarnessRetryClassifier(unittest.TestCase):
    """D-38: closed-tuple TRANSIENT_RETRY_TYPES; injected faults NEVER retried."""

    def test_injected_fault_propagates_without_retry(self) -> None:
        """InjectedFaultError MUST bubble up through retry classifier — IRON RULE."""
        call_count = [0]

        async def fake_runner(*args, **kw):
            call_count[0] += 1
            raise InjectedFaultError("test injected fault")

        with patch.dict(harness_mod._RUNNERS, {"pure_mcp": fake_runner}):
            specs = [_make_spec()]

            def factory(*, run_id, lane, task_id):
                return TraceRecorder(mode=lane, runtime="mock", task_id=task_id)

            with self.assertRaises(InjectedFaultError):
                asyncio.run(harness_mod.run_race(
                    specs, ["pure_mcp"], n=1,
                    recorder_factory=factory,
                    ws_emitter=lambda ev: None,
                ))
        # Runner called exactly once: NO retry attempted.
        self.assertEqual(call_count[0], 1)

    def test_rate_limit_error_retried_up_to_3_attempts(self) -> None:
        call_count = [0]

        async def fake_runner(task_spec, run_id, *args, **kw):
            call_count[0] += 1
            if call_count[0] < 3:
                # anthropic.RateLimitError construction: (message, response, body).
                # We use a minimal stub that satisfies isinstance check.
                raise anthropic.RateLimitError(
                    "rate limited",
                    response=_FakeResponse(status_code=429),
                    body=None,
                )
            return _good_result("pure_mcp", task_spec.task_id, run_id)

        with patch.dict(harness_mod._RUNNERS, {"pure_mcp": fake_runner}):
            specs = [_make_spec()]

            def factory(*, run_id, lane, task_id):
                return TraceRecorder(mode=lane, runtime="mock", task_id=task_id)

            # Patch sleep to make retries instant.
            with patch.object(harness_mod.asyncio, "sleep", new=_no_sleep):
                grouped = asyncio.run(harness_mod.run_race(
                    specs, ["pure_mcp"], n=1,
                    recorder_factory=factory,
                    ws_emitter=lambda ev: None,
                ))
        # Exactly 3 invocations: 2 retried errors + 1 success.
        self.assertEqual(call_count[0], 3)
        # And the result was successful.
        result = grouped[("pure_mcp", "summarize_repo")][0]
        self.assertTrue(result.score_card.success)

    def test_connection_error_retried(self) -> None:
        call_count = [0]

        async def fake_runner(task_spec, run_id, *args, **kw):
            call_count[0] += 1
            if call_count[0] < 2:
                raise anthropic.APIConnectionError(request=_FakeRequest())
            return _good_result("pure_mcp", task_spec.task_id, run_id)

        with patch.dict(harness_mod._RUNNERS, {"pure_mcp": fake_runner}):
            specs = [_make_spec()]

            def factory(*, run_id, lane, task_id):
                return TraceRecorder(mode=lane, runtime="mock", task_id=task_id)

            with patch.object(harness_mod.asyncio, "sleep", new=_no_sleep):
                asyncio.run(harness_mod.run_race(
                    specs, ["pure_mcp"], n=1,
                    recorder_factory=factory,
                    ws_emitter=lambda ev: None,
                ))
        self.assertEqual(call_count[0], 2)

    def test_unknown_exception_propagates_without_retry(self) -> None:
        """ValueError (not in TRANSIENT_RETRY_TYPES) must bubble immediately."""
        call_count = [0]

        async def fake_runner(*args, **kw):
            call_count[0] += 1
            raise ValueError("not a transient")

        with patch.dict(harness_mod._RUNNERS, {"pure_mcp": fake_runner}):
            specs = [_make_spec()]

            def factory(*, run_id, lane, task_id):
                return TraceRecorder(mode=lane, runtime="mock", task_id=task_id)

            with self.assertRaises(ValueError):
                asyncio.run(harness_mod.run_race(
                    specs, ["pure_mcp"], n=1,
                    recorder_factory=factory,
                    ws_emitter=lambda ev: None,
                ))
        self.assertEqual(call_count[0], 1)


class TestHarnessTimeout(unittest.TestCase):
    """Per-run asyncio.wait_for(PER_RUN_TIMEOUT_S) -> lane_failed/timeout."""

    def test_per_run_timeout_produces_lane_failed_timeout_score(self) -> None:
        async def slow_runner(*args, **kw):
            await asyncio.sleep(10.0)
            return _good_result("pure_mcp", "summarize_repo", "x")

        with patch.dict(harness_mod._RUNNERS, {"pure_mcp": slow_runner}):
            with patch.object(harness_mod, "PER_RUN_TIMEOUT_S", 0.05):
                specs = [_make_spec()]

                def factory(*, run_id, lane, task_id):
                    return TraceRecorder(mode=lane, runtime="mock", task_id=task_id)

                grouped = asyncio.run(harness_mod.run_race(
                    specs, ["pure_mcp"], n=1,
                    recorder_factory=factory,
                    ws_emitter=lambda ev: None,
                ))
        result = grouped[("pure_mcp", "summarize_repo")][0]
        self.assertEqual(result.score_card.failure_mode, "lane_failed")
        self.assertEqual(getattr(result.score_card, "lane_failed_reason", None), "timeout")


class TestHarnessRaceDoneEmission(unittest.TestCase):
    """D-39: exactly one race_done event per run_race call."""

    def test_race_done_emitted_once_after_all_runs(self) -> None:
        async def fake_runner(task_spec, run_id, *args, **kw):
            return _good_result("pure_mcp", task_spec.task_id, run_id)

        ws_events: list[dict] = []

        with patch.dict(harness_mod._RUNNERS, {"pure_mcp": fake_runner}):
            specs = [_make_spec()]

            def factory(*, run_id, lane, task_id):
                return TraceRecorder(mode=lane, runtime="mock", task_id=task_id)

            asyncio.run(harness_mod.run_race(
                specs, ["pure_mcp"], n=3,
                recorder_factory=factory,
                ws_emitter=lambda ev: ws_events.append(ev),
            ))

        race_done_events = [ev for ev in ws_events if ev.get("event_type") == "race_done"]
        self.assertEqual(len(race_done_events), 1)
        rd = race_done_events[0]
        self.assertEqual(rd["total_runs"], 3)
        self.assertIn("t_end_ms", rd)
        self.assertIn("headlines", rd)
        self.assertIn("lane_failed_reasons", rd)


class TestHarnessHeadlineGenerated(unittest.TestCase):
    """Each (lane, task) pair yields a non-empty headline string."""

    def test_headline_present_per_lane_task_pair(self) -> None:
        async def fake_runner(task_spec, run_id, *args, **kw):
            lane = "pure_mcp"  # constant lane label for the fake; the harness sets the actual lane
            return _good_result(lane, task_spec.task_id, run_id)

        ws_events: list[dict] = []

        with patch.dict(harness_mod._RUNNERS, {
            "pure_mcp": fake_runner,
            "pure_a2a": fake_runner,
            "hybrid": fake_runner,
        }):
            specs = [_make_spec("summarize_repo"), _make_spec("book_travel")]

            def factory(*, run_id, lane, task_id):
                return TraceRecorder(mode=lane, runtime="mock", task_id=task_id)

            asyncio.run(harness_mod.run_race(
                specs, ["pure_mcp", "pure_a2a", "hybrid"], n=1,
                recorder_factory=factory,
                ws_emitter=lambda ev: ws_events.append(ev),
            ))

        race_done = [ev for ev in ws_events if ev.get("event_type") == "race_done"][0]
        headlines = race_done["headlines"]
        # 3 lanes * 2 tasks = 6 cells; each must have a non-empty headline.
        self.assertEqual(len(headlines), 6)
        for key, headline in headlines.items():
            self.assertIsInstance(headline, str, key)
            self.assertGreater(len(headline), 0, key)


# ---------------------------------------------------------------------------
# Stub helpers for anthropic exception construction (constructors require
# response/request objects — easier to fake than to mock the full SDK).
# ---------------------------------------------------------------------------


class _FakeResponse:
    """Minimal Response-shaped stub for anthropic.RateLimitError construction."""

    def __init__(self, status_code: int = 429) -> None:
        self.status_code = status_code
        self.headers: dict[str, str] = {}
        self.request = _FakeRequest()


class _FakeRequest:
    method = "POST"
    url = "https://api.anthropic.com/v1/messages"


async def _no_sleep(*_args, **_kwargs) -> None:
    """Stand-in for asyncio.sleep that returns immediately during retry tests."""
    return None


if __name__ == "__main__":
    unittest.main()
