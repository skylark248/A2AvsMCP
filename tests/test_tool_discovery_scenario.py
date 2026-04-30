"""Phase 11 — DISC-01: tool_discovery scenario coverage.

Verifies that the new TICKET-1013 scenario:
1. Loads from seeds/scenarios.json via DemoRepository.
2. Emits at least one `tool_discovery` event when run in mcp mode.
3. Falls back to `search_docs` for the unknown NebulaSync Hub SKU
   (D-68: data-driven failure mode — no FailureConfig toggle).
"""

import os
import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault(
    "A2A_VS_MCP_ARTIFACT_ROOT", str(PROJECT_ROOT / ".tmp" / "test_artifacts")
)
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from a2a_vs_mcp.dataset import DemoRepository  # noqa: E402
from a2a_vs_mcp.platform import DemoPlatform  # noqa: E402


class ToolDiscoveryScenarioTests(unittest.TestCase):
    def setUp(self) -> None:
        self.platform = DemoPlatform(PROJECT_ROOT, runtime="mock")

    def test_tool_discovery_scenario_loads(self) -> None:
        repo = DemoRepository(PROJECT_ROOT)
        scenarios = repo.load_scenarios()
        self.assertIn("tool_discovery", scenarios)
        ticket = scenarios["tool_discovery"]
        self.assertEqual(ticket.ticket_id, "TICKET-1013")
        self.assertEqual(ticket.customer_id, "CUST-005")
        self.assertEqual(ticket.difficulty, "advanced")
        self.assertIn("discovery", ticket.tags)
        self.assertIn("fallback", ticket.tags)

    def test_tool_discovery_scenario_emits_discovery_event_in_mcp_mode(self) -> None:
        ticket = self.platform.get_ticket("tool_discovery", None, None)
        result = self.platform.run("mcp", ticket)
        # Per RESEARCH Pitfall #1: filter on event_type, NOT on event.phase
        # (TraceRecorder._PHASE_MAP does not tag tool_discovery as "discovery").
        discovery_events = [
            e for e in result.trace if e.get("event_type") == "tool_discovery"
        ]
        self.assertGreater(
            len(discovery_events),
            0,
            f"Expected at least 1 tool_discovery event; got trace event_types: "
            f"{[e.get('event_type') for e in result.trace]}",
        )

    def test_tool_discovery_scenario_falls_back_for_unknown_sku(self) -> None:
        # NebulaSync Hub is intentionally NOT in warranties.json or orders.json.
        # This forces the agent to discover tools, find no match, and pivot to
        # search_docs — exercising both stale-capability-cache and
        # unknown-tool-fallback naturally per D-68.
        ticket = self.platform.get_ticket("tool_discovery", None, None)
        result = self.platform.run("mcp", ticket)
        self.assertIn(
            "search_docs",
            result.tools_used,
            f"Expected search_docs fallback for unknown SKU; got tools_used: "
            f"{result.tools_used}",
        )


if __name__ == "__main__":
    unittest.main()
