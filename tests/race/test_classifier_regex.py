"""is_acknowledging_fault regex tests over the 50-sample corpus (D-36, RACE-04).

Asserts:
- FP rate on the 25 non-ack samples < 10% (D-36 contract).
- Negation guard suppresses 'I do not retry' and 'without any timeout'
  patterns even though they contain ack-fault tokens.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

from a2a_vs_mcp.race.classifier import is_acknowledging_fault


_CORPUS_PATH = Path(__file__).parent / "fixtures" / "regex_corpus.json"


def _load_corpus() -> dict:
    return json.loads(_CORPUS_PATH.read_text())


class TestAckRegexCorpus(unittest.TestCase):
    """50-sample corpus FP rate gate (D-36)."""

    def test_corpus_shape_25_acks_25_nonacks(self) -> None:
        d = _load_corpus()
        self.assertEqual(d["fp_target"], 0.10)
        self.assertEqual(len(d["samples"]), 50)
        acks = [s for s in d["samples"] if s["is_ack"]]
        nonacks = [s for s in d["samples"] if not s["is_ack"]]
        self.assertEqual(len(acks), 25)
        self.assertEqual(len(nonacks), 25)

    def test_corpus_fp_rate_below_10pct(self) -> None:
        d = _load_corpus()
        nonacks = [s for s in d["samples"] if not s["is_ack"]]
        fp = sum(1 for s in nonacks if is_acknowledging_fault(s["text"]))
        fp_rate = fp / len(nonacks)
        self.assertLess(
            fp_rate, d["fp_target"],
            f"FP rate {fp_rate:.2%} exceeds target {d['fp_target']:.2%}; "
            f"D-36 contract violated",
        )

    def test_corpus_recall_above_50pct(self) -> None:
        """Sanity bound: regex must accept at least half of the ack samples
        (the corpus is curated to be regex-detectable; recall < 50% means a
        regex regression)."""
        d = _load_corpus()
        acks = [s for s in d["samples"] if s["is_ack"]]
        tp = sum(1 for s in acks if is_acknowledging_fault(s["text"]))
        self.assertGreater(tp / len(acks), 0.5)


class TestNegationGuard(unittest.TestCase):
    """D-36 negation guard explicit cases."""

    def test_negation_guard_blocks_i_do_not_retry(self) -> None:
        # Has both negation token ('not') and fault token ('retry'), so the
        # sentence is suppressed even though the ack regex matches 'retry'.
        self.assertFalse(is_acknowledging_fault("I do not retry — moving on."))

    def test_negation_guard_blocks_without_any_timeout(self) -> None:
        self.assertFalse(is_acknowledging_fault("This call ran without any timeout."))

    def test_negation_guard_does_not_block_real_acks(self) -> None:
        # No negation in the same sentence -> normal ack path fires.
        self.assertTrue(is_acknowledging_fault("I hit a rate limit. Retrying."))
        self.assertTrue(is_acknowledging_fault("Got an HTTP 429. Backing off."))


if __name__ == "__main__":
    unittest.main()
