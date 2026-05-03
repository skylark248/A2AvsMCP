"""Tests for POST /api/race/run endpoint (B1 gap closure, Phase 14)."""
from __future__ import annotations

import re
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from a2a_vs_mcp.web import app
from a2a_vs_mcp.race.replay import _validate_run_id

RUN_ID_RE = re.compile(r"[A-Za-z0-9_-]{1,64}")
VALID_BODY = {
    "task_ids": ["summarize_repo"],
    "lanes": ["pure_mcp"],
    "n": 1,
}


class TestRaceRunEndpoint(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.client = TestClient(app)

    def _post(self, body: dict) -> ...:
        return self.client.post("/api/race/run", json=body)

    def test_happy_path_returns_200_and_run_id(self) -> None:
        """Valid body returns 200 with a run_id string."""
        with patch("a2a_vs_mcp.web.asyncio.create_task") as mock_ct:
            resp = self._post(VALID_BODY)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn("run_id", data)
        run_id = data["run_id"]
        self.assertIsInstance(run_id, str)
        self.assertRegex(run_id, r"^[A-Za-z0-9_-]{1,64}$")
        # Passes the canonical _validate_run_id guard without raising.
        _validate_run_id(run_id)  # raises ValueError on bad id

    def test_background_task_created(self) -> None:
        """asyncio.create_task is called once per POST."""
        with patch("a2a_vs_mcp.web.asyncio.create_task") as mock_ct:
            self._post(VALID_BODY)
        mock_ct.assert_called_once()

    def test_invalid_lane_returns_422(self) -> None:
        resp = self._post({**VALID_BODY, "lanes": ["bad_lane"]})
        self.assertEqual(resp.status_code, 422)

    def test_n_zero_returns_422(self) -> None:
        resp = self._post({**VALID_BODY, "n": 0})
        self.assertEqual(resp.status_code, 422)

    def test_unknown_task_id_returns_422(self) -> None:
        resp = self._post({**VALID_BODY, "task_ids": ["nonexistent_task_xyz"]})
        self.assertEqual(resp.status_code, 422)

    def test_missing_task_ids_returns_422(self) -> None:
        resp = self._post({"lanes": ["pure_mcp"], "n": 1})
        self.assertEqual(resp.status_code, 422)

    def test_all_three_lanes_accepted(self) -> None:
        with patch("a2a_vs_mcp.web.asyncio.create_task"):
            resp = self._post({
                "task_ids": ["summarize_repo"],
                "lanes": ["pure_mcp", "pure_a2a", "hybrid"],
                "n": 1,
            })
        self.assertEqual(resp.status_code, 200)


if __name__ == "__main__":
    unittest.main()
