"""HEAT-03: replay symmetry — Detector(K=3) over recorded ndjson reproduces the
expected terminal tag for every fixture (D-33 symmetry-by-construction).

Two-layer fixture test:
- Layer 1: assert replay tag == fixture["expected_terminal_tag"].
- Layer 2: --update-snapshots rewrites expected_terminal_tag with actual.
"""
from __future__ import annotations

import json
import pathlib

import pytest

from tests.race._replay_helpers import replay_with_k

FIXTURES = pathlib.Path(__file__).resolve().parent / "fixtures" / "traces"


@pytest.mark.parametrize(
    "fixture_path",
    sorted(FIXTURES.glob("*.json")),
    ids=lambda p: p.stem,
)
def test_replay_symmetry(fixture_path, request):
    fx = json.loads(fixture_path.read_text())
    actual = replay_with_k(fx["events"], K=3, score_pass=fx["score_pass"])

    if request.config.getoption("--update-snapshots"):
        fx["expected_terminal_tag"] = actual
        fixture_path.write_text(json.dumps(fx, indent=2) + "\n")
        return

    assert actual == fx["expected_terminal_tag"], (
        f"{fixture_path.name}: replay produced {actual!r}, "
        f"fixture expects {fx['expected_terminal_tag']!r}"
    )
