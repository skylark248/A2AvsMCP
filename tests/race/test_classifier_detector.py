"""Detector(K=3) state machine tests over fixture traces (RACE-04, D-31..D-34).

Asserts:
- Each fixture's expected_terminal_tag matches Detector finalization.
- K=3 window-close logic (no observation past K turns -> kept_going_without_noticing).
- D-33 replay symmetry: replaying the same events produces identical terminal tag.
"""
from __future__ import annotations

import glob
import json
import unittest
from pathlib import Path

from a2a_vs_mcp.race.classifier import Detector


_FIXTURES_DIR = Path(__file__).parent / "fixtures" / "traces"


def _load_fixture(name: str) -> dict:
    return json.loads((_FIXTURES_DIR / f"{name}.json").read_text())


def _replay(events: list[dict], score_pass: bool | None) -> str:
    """Replay events through a single Detector (first fault_injected event).

    If a `race_done` event appears without a `done` event, finalize via
    `finalize_at_race_done_no_done()`; otherwise via `finalize_at_done(score_pass)`.
    """
    detector: Detector | None = None
    saw_race_done = False
    saw_done = False
    for ev in events:
        et = ev.get("event_type")
        if et == "fault_injected" and detector is None:
            detector = Detector(
                fault_id=ev["fault_id"],
                fault_kind=ev.get("fault_kind", ""),
                target=ev.get("target", ""),
                fault_inject_turn=ev.get("turn_index", 0),
            )
            continue
        if detector is not None and detector.state.value != "observed":
            detector.consume(ev)
        if et == "race_done":
            saw_race_done = True
        if et == "done":
            saw_done = True
    assert detector is not None, "fixture missing fault_injected"
    if saw_race_done and not saw_done:
        return detector.finalize_at_race_done_no_done()
    return detector.finalize_at_done(bool(score_pass))


class TestDetectorOnFixtures(unittest.TestCase):
    """One method per trace fixture — terminal tag must match expected."""

    def test_terminal_tag_matches_fixture_summarize_repo_recovered(self) -> None:
        fx = _load_fixture("summarize_repo_recovered")
        self.assertEqual(_replay(fx["events"], fx.get("score_pass")), fx["expected_terminal_tag"])

    def test_terminal_tag_matches_fixture_summarize_repo_gave_up(self) -> None:
        fx = _load_fixture("summarize_repo_gave_up")
        self.assertEqual(_replay(fx["events"], fx.get("score_pass")), fx["expected_terminal_tag"])

    def test_terminal_tag_matches_fixture_summarize_repo_kept_going_silent(self) -> None:
        fx = _load_fixture("summarize_repo_kept_going_silent")
        self.assertEqual(_replay(fx["events"], fx.get("score_pass")), fx["expected_terminal_tag"])

    def test_terminal_tag_matches_fixture_negotiate_meeting_recovered(self) -> None:
        fx = _load_fixture("negotiate_meeting_recovered")
        self.assertEqual(_replay(fx["events"], fx.get("score_pass")), fx["expected_terminal_tag"])

    def test_terminal_tag_matches_fixture_negotiate_meeting_kept_going(self) -> None:
        fx = _load_fixture("negotiate_meeting_kept_going")
        self.assertEqual(_replay(fx["events"], fx.get("score_pass")), fx["expected_terminal_tag"])

    def test_terminal_tag_matches_fixture_negotiate_meeting_indeterminate(self) -> None:
        fx = _load_fixture("negotiate_meeting_indeterminate")
        self.assertEqual(_replay(fx["events"], fx.get("score_pass")), fx["expected_terminal_tag"])

    def test_terminal_tag_matches_fixture_book_travel_recovered(self) -> None:
        fx = _load_fixture("book_travel_recovered")
        self.assertEqual(_replay(fx["events"], fx.get("score_pass")), fx["expected_terminal_tag"])

    def test_terminal_tag_matches_fixture_book_travel_gave_up(self) -> None:
        fx = _load_fixture("book_travel_gave_up")
        self.assertEqual(_replay(fx["events"], fx.get("score_pass")), fx["expected_terminal_tag"])

    def test_terminal_tag_matches_fixture_book_travel_kept_going_to_failure(self) -> None:
        fx = _load_fixture("book_travel_kept_going_to_failure")
        self.assertEqual(_replay(fx["events"], fx.get("score_pass")), fx["expected_terminal_tag"])

    def test_all_nine_fixtures_present(self) -> None:
        # §The Assignment corpus: 9 fictional task × terminal-tag fixtures.
        # Phase 9 Plan 03 (HEAT-04) added 9 additional `*_near_k3_boundary_d{3,4,5}`
        # boundary fixtures to make K∈{2,4,5} drift observable for the calibration
        # sweep — these are NOT part of §The Assignment and are filtered here.
        files = sorted(
            f for f in glob.glob(str(_FIXTURES_DIR / "*.json"))
            if "near_k3_boundary" not in Path(f).name
        )
        self.assertEqual(len(files), 9, "expected 9 fictional fault trace fixtures")


class TestDetectorK3Window(unittest.TestCase):
    """Synthetic K=3 window-close path: no observation within K turns -> silent miss."""

    def test_consume_no_observation_within_k3_returns_kept_going_silent(self) -> None:
        det = Detector(
            fault_id="f1",
            fault_kind="rate_limit_429",
            target="github_api.list_files",
            fault_inject_turn=2,
            K=3,
        )
        # Feed 4 turn-defining events with no acknowledgment, all past K.
        events = [
            {"event_type": "agent_msg", "content": "Reading the next file.", "turn_index": 3},
            {"event_type": "agent_msg", "content": "Drafting summary.", "turn_index": 4},
            {"event_type": "agent_msg", "content": "Final answer.", "turn_index": 5},
            {"event_type": "agent_msg", "content": "Continuing.", "turn_index": 6},
        ]
        for ev in events:
            det.consume(ev)
        self.assertEqual(det.state.value, "awaiting_observation")
        # done with score_pass=True => kept_going_without_noticing
        self.assertEqual(det.finalize_at_done(True), "kept_going_without_noticing")

    def test_observation_inside_k3_window_recovers(self) -> None:
        det = Detector(
            fault_id="f1",
            fault_kind="rate_limit_429",
            target="github_api.list_files",
            fault_inject_turn=2,
            K=3,
        )
        # turn 3 is inside the K=3 window (3 - 2 = 1 <= 3).
        det.consume({
            "event_type": "agent_msg",
            "content": "Hit a rate limit. Retrying.",
            "turn_index": 3,
        })
        self.assertEqual(det.state.value, "observed")
        self.assertEqual(det.finalize_at_done(True), "recovered")

    def test_observation_outside_k3_window_dropped(self) -> None:
        det = Detector(
            fault_id="f1",
            fault_kind="rate_limit_429",
            target="github_api.list_files",
            fault_inject_turn=2,
            K=3,
        )
        # turn 6 - inject_turn 2 = 4 > K=3; observation refused.
        det.consume({
            "event_type": "agent_msg",
            "content": "Got an error response. Retrying.",
            "turn_index": 6,
        })
        self.assertEqual(det.state.value, "awaiting_observation")


class TestDetectorReplaySymmetry(unittest.TestCase):
    """D-33: live consumption and replay over the same event list yield identical tags."""

    def test_replay_yields_same_tag_as_live(self) -> None:
        # Use the recovered fixture for a deterministic, observed trace.
        fx = _load_fixture("summarize_repo_recovered")
        events = fx["events"]
        score_pass = fx["score_pass"]

        # Live path: feed events one at a time as they arrive.
        live_det = None
        for ev in events:
            if ev.get("event_type") == "fault_injected" and live_det is None:
                live_det = Detector(
                    fault_id=ev["fault_id"],
                    fault_kind=ev.get("fault_kind", ""),
                    target=ev.get("target", ""),
                    fault_inject_turn=ev.get("turn_index", 0),
                )
                continue
            if live_det is not None and live_det.state.value != "observed":
                live_det.consume(ev)
        live_tag = live_det.finalize_at_done(bool(score_pass))

        # Replay path: identical iteration over a list copy.
        replay_det = None
        for ev in list(events):
            if ev.get("event_type") == "fault_injected" and replay_det is None:
                replay_det = Detector(
                    fault_id=ev["fault_id"],
                    fault_kind=ev.get("fault_kind", ""),
                    target=ev.get("target", ""),
                    fault_inject_turn=ev.get("turn_index", 0),
                )
                continue
            if replay_det is not None and replay_det.state.value != "observed":
                replay_det.consume(ev)
        replay_tag = replay_det.finalize_at_done(bool(score_pass))

        self.assertEqual(live_tag, replay_tag)
        self.assertEqual(live_tag, fx["expected_terminal_tag"])

    def test_replay_symmetric_across_all_fixtures(self) -> None:
        """Repeat the live-vs-replay check for every fixture in the corpus."""
        for path in sorted(_FIXTURES_DIR.glob("*.json")):
            fx = json.loads(path.read_text())
            tag1 = _replay(fx["events"], fx.get("score_pass"))
            tag2 = _replay(list(fx["events"]), fx.get("score_pass"))
            self.assertEqual(
                tag1, tag2,
                f"replay symmetry broke for {fx['name']}: {tag1} != {tag2}",
            )


if __name__ == "__main__":
    unittest.main()
