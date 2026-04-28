"""D-13 CI grep — enforces IRON RULE record-before-mutate across src/a2a_vs_mcp/race/."""
from __future__ import annotations

import re
import unittest
from pathlib import Path

RACE_DIR = Path(__file__).resolve().parents[2] / "src" / "a2a_vs_mcp" / "race"


class IronRuleGrepTests(unittest.TestCase):
    def test_failure_module_docstring_states_iron_rule(self) -> None:
        text = (RACE_DIR / "failure.py").read_text(encoding="utf-8")
        self.assertIn("IRON RULE", text,
                      "failure.py module docstring must contain 'IRON RULE' (D-13)")

    def test_inject_fault_defined_only_in_failure_module(self) -> None:
        # Any file in race/ that defines `def inject_fault` other than failure.py
        # would be a violation — multiple injection paths defeat atomicity.
        offenders: list[Path] = []
        for path in RACE_DIR.glob("*.py"):
            if path.name == "failure.py":
                continue
            if re.search(r"^def\s+inject_fault\b", path.read_text(encoding="utf-8"),
                         flags=re.MULTILINE):
                offenders.append(path)
        self.assertEqual(offenders, [],
                         f"inject_fault must only be defined in race/failure.py; "
                         f"found in: {offenders}")

    def test_apply_mutation_defined_only_in_failure_module(self) -> None:
        offenders: list[Path] = []
        for path in RACE_DIR.glob("*.py"):
            if path.name == "failure.py":
                continue
            if re.search(r"^def\s+_apply_mutation\b", path.read_text(encoding="utf-8"),
                         flags=re.MULTILINE):
                offenders.append(path)
        self.assertEqual(offenders, [],
                         f"_apply_mutation must only be defined in race/failure.py; "
                         f"found in: {offenders}")


if __name__ == "__main__":
    unittest.main()
