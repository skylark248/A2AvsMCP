"""IRON RULE D-25: every public mock callable goes through inject_fault().

Extends Phase 6 D-13 grep gate from race/failure.py to race/mocks/* and
mcp_servers/race_*.py — single fault chokepoint enforced by source grep.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path


_REPO_ROOT = Path(__file__).resolve().parents[2]


def _public_def_bodies(src: str) -> list[tuple[str, str]]:
    """Return [(name, body_text)] for every top-level public def in src.

    Top-level = no leading whitespace on the `def` line.
    Public    = name does not start with underscore.
    """
    out: list[tuple[str, str]] = []
    lines = src.splitlines()
    i = 0
    while i < len(lines):
        m = re.match(r"^def ([a-zA-Z_][a-zA-Z0-9_]*)\(", lines[i])
        if m and not m.group(1).startswith("_"):
            start = i
            i += 1
            while i < len(lines) and (
                lines[i].startswith(" ") or lines[i].startswith("\t") or lines[i].strip() == ""
            ):
                i += 1
            out.append((m.group(1), "\n".join(lines[start:i])))
            continue
        i += 1
    return out


class TestMocksChokepoint(unittest.TestCase):
    """Every public callable in race/mocks/{github,calendar,travel}.py
    must contain `inject_fault(` somewhere in its body — IRON RULE D-25."""

    MOCK_FILES = [
        "src/a2a_vs_mcp/race/mocks/github.py",
        "src/a2a_vs_mcp/race/mocks/calendar.py",
        "src/a2a_vs_mcp/race/mocks/travel.py",
    ]

    def test_every_public_mock_callable_calls_inject_fault(self) -> None:
        for rel in self.MOCK_FILES:
            src = (_REPO_ROOT / rel).read_text()
            defs = _public_def_bodies(src)
            self.assertGreater(len(defs), 0, f"{rel}: expected >=1 public callable")
            for name, body in defs:
                self.assertIn(
                    "inject_fault(", body,
                    f"{rel}::{name} missing inject_fault() call — IRON RULE D-25 breach",
                )

    def test_each_mock_module_imports_failure_module(self) -> None:
        for rel in self.MOCK_FILES:
            src = (_REPO_ROOT / rel).read_text()
            self.assertRegex(
                src, r"from\s+\.{1,3}failure\s+import\s+inject_fault",
                f"{rel} must import inject_fault from race.failure",
            )


class TestMcpServersRouteThroughMocks(unittest.TestCase):
    """Every @mcp.tool() in mcp_servers/race_*.py imports + calls into race.mocks.*."""

    SERVER_FILES = [
        "src/a2a_vs_mcp/mcp_servers/race_github.py",
        "src/a2a_vs_mcp/mcp_servers/race_calendar.py",
        "src/a2a_vs_mcp/mcp_servers/race_travel.py",
    ]

    def test_each_server_imports_race_mocks(self) -> None:
        """The server file must reference the race.mocks package somehow."""
        for rel in self.SERVER_FILES:
            src = (_REPO_ROOT / rel).read_text()
            self.assertRegex(
                src, r"a2a_vs_mcp\.race\.mocks|race\.mocks",
                f"{rel} must import from race.mocks",
            )

    def test_each_server_has_at_least_one_mcp_tool(self) -> None:
        for rel in self.SERVER_FILES:
            src = (_REPO_ROOT / rel).read_text()
            tools = re.findall(r"@mcp\.tool\(\)", src)
            self.assertGreater(
                len(tools), 0, f"{rel}: expected >=1 @mcp.tool() decorator",
            )

    def test_each_mcp_tool_routes_through_mock_module(self) -> None:
        """For every @mcp.tool() function body, the body must reference the
        corresponding race.mocks.<module> (or imported alias) — NOT direct
        fixture access."""
        for rel in self.SERVER_FILES:
            src = (_REPO_ROOT / rel).read_text()
            module_name = Path(rel).stem.replace("race_", "")
            # Permitted patterns: `<module>_mock.<fn>(`, `<module>.<fn>(`,
            # or any reference to `race.mocks.<module>`.
            patterns = [
                rf"\b{module_name}_mock\b",
                rf"\brace\.mocks\.{module_name}\b",
                rf"a2a_vs_mcp\.race\.mocks\.{module_name}\b",
                rf"from a2a_vs_mcp\.race\.mocks import {module_name}",
                rf"from \.\.race\.mocks import {module_name}",
            ]
            self.assertTrue(
                any(re.search(p, src) for p in patterns),
                f"{rel}: tools must route through race.mocks.{module_name}",
            )


class TestNoDirectFixtureAccessInServers(unittest.TestCase):
    """Negative gate: race_*.py servers must NOT load fixtures directly.

    Fixture file access (json.load, open, Path/.read_text on fixtures dirs)
    belongs in race.mocks.* — NOT in mcp_servers/race_*.py. This is the
    counter-image of the chokepoint rule.
    """

    SERVER_FILES = [
        "src/a2a_vs_mcp/mcp_servers/race_github.py",
        "src/a2a_vs_mcp/mcp_servers/race_calendar.py",
        "src/a2a_vs_mcp/mcp_servers/race_travel.py",
    ]

    def test_servers_do_not_open_fixture_files_directly(self) -> None:
        for rel in self.SERVER_FILES:
            src = (_REPO_ROOT / rel).read_text()
            non_comment = "\n".join(
                line for line in src.splitlines() if not line.lstrip().startswith("#")
            )
            # No json.load on a fixtures path.
            self.assertNotIn("json.load(", non_comment, f"{rel}: server must not load fixtures directly")
            # No fixtures path string.
            self.assertNotIn("fixtures/", non_comment, f"{rel}: server must not reference fixtures path")


if __name__ == "__main__":
    unittest.main()
