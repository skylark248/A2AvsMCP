"""HEAT-04: K=3 multi-task calibration sweep.

K=3 produces the expected tag for every fictional-trace fixture across the 3
v1 tasks (the lock). For each task, K∈{2,4,5} produces drift on at least one
fixture (the calibration claim — K=3 is non-arbitrary).

Test file path is named in ROADMAP success criterion 4.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from tests.race._replay_helpers import replay_with_k

FIXTURES = pathlib.Path(__file__).parent / "race" / "fixtures" / "traces"


@pytest.mark.parametrize(
    "fixture_path",
    sorted(FIXTURES.glob("*.json")),
    ids=lambda p: p.stem,
)
def test_k3_produces_expected_tag(fixture_path):
    """HEAT-04 lock: K=3 produces expected_terminal_tag for every fixture."""
    fx = json.loads(fixture_path.read_text())
    tag = replay_with_k(fx["events"], K=3, score_pass=fx["score_pass"])
    assert tag == fx["expected_terminal_tag"], (
        f"{fixture_path.name} drifted at K=3: got {tag!r}, "
        f"expected {fx['expected_terminal_tag']!r}"
    )


@pytest.mark.parametrize("k", [2, 4, 5])
@pytest.mark.parametrize("task", ["summarize_repo", "negotiate_meeting", "book_travel"])
def test_off_k_drift_observed_per_task(k, task):
    """HEAT-04 calibration claim: at least one fixture per task drifts when K!=3."""
    drifts = []
    for path in sorted(FIXTURES.glob(f"{task}_*.json")):
        fx = json.loads(path.read_text())
        tag_k3 = replay_with_k(fx["events"], K=3, score_pass=fx["score_pass"])
        tag_kx = replay_with_k(fx["events"], K=k, score_pass=fx["score_pass"])
        if tag_kx != tag_k3:
            drifts.append((path.name, tag_kx, tag_k3))
    assert drifts, f"No K={k} drift for task={task} — calibration claim unsupported"
