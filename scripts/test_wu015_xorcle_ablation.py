"""Unit tests for WU-015's extraction of upstream, unmodified solver counters."""

import unittest

from scripts.wu015_xorcle_ablation import collect_counters, VARIANTS


class TestXorcleAblation(unittest.TestCase):
    def test_counters_extracted(self):
        stdout = ("c Conflicts: 7\n"
                  "c Propagations: 20\n"
                  "c Attempted propagations: 40\n"
                  "c Watch updates: 9\n"
                  "c Learned clauses: 6\n"
                  "c Decisions: 4\n")
        counters = collect_counters(stdout)
        self.assertEqual(counters["conflicts"], 7)
        self.assertEqual(counters["attempted_propagations"], 40)

    def test_exact_variants(self):
        self.assertEqual(VARIANTS["default"], ())
        self.assertEqual(VARIANTS["watchlist"], ("--selection=leading_term_watchlist",))
        self.assertEqual(VARIANTS["no_compaction"], ("--compact=false",))


if __name__ == "__main__":
    unittest.main()
