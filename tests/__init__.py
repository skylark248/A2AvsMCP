"""Test root package — enables ``tests.race._replay_helpers`` imports.

Created Phase 9 Plan 03 (HEAT-03 + HEAT-04): the shared replay helper at
``tests/race/_replay_helpers.py`` is consumed by both
``tests/race/test_replay_symmetry.py`` and ``tests/test_recovery_calibration.py``,
which requires ``tests`` to be a Python package.
"""
