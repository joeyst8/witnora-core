"""W-CRC-018 matched syntactic invariants and exact semantic controls."""
from __future__ import annotations

import random
import unittest
from math import comb

from scripts.benchmark_crc_scaling import interaction_density
from scripts.benchmark_crc_matched_semantics import (
    matched_source, semantic_profile, triple_parity_source,
)
from tests.test_crc_cutset_count import brute_models


class TestCRCMatchedSemantics(unittest.TestCase):
    def test_graph_clauses_and_count_match_but_dependencies_do_not(self):
        for n in (4, 8, 10):
            cases = {}
            for family in ("pairwise_parity", "pairwise_forcing"):
                source = matched_source(n, family)
                self.assertEqual(len(source), n * (n - 1))
                self.assertEqual(interaction_density(
                    source, tuple(range(1, n + 1))), 1.0)
                self.assertEqual(brute_models(source, n), 2)
                cases[family] = semantic_profile(source, n)
            self.assertEqual(cases["pairwise_parity"]["live_variables"], n)
            self.assertEqual(cases["pairwise_parity"][
                "pairwise_dependent_edges"], comb(n, 2))
            self.assertEqual(cases["pairwise_forcing"]["live_variables"], 1)
            self.assertEqual(cases["pairwise_forcing"][
                "pairwise_dependent_edges"], 0)

    def test_three_way_parity_disproves_pairwise_completeness(self):
        source = triple_parity_source()
        self.assertEqual(len(source), 4)
        self.assertEqual(interaction_density(source, (1, 2, 3)), 1.0)
        profile = semantic_profile(source, 3)
        self.assertEqual(profile["models"], 4)
        self.assertEqual(profile["live_variables"], 3)
        self.assertEqual(profile["pairwise_dependent_edges"], 0)
        self.assertEqual(abs(profile["triple_123_walsh_sum"]), 4)

    def test_semantic_profile_ignores_clause_order_and_duplicates(self):
        source = matched_source(8, "pairwise_forcing")
        expected = semantic_profile(source, 8)
        rng = random.Random(18018)
        rng.shuffle(source)
        self.assertEqual(semantic_profile(source + source[:10], 8), expected)

    def test_unsat_and_diagnostic_limit_are_explicit(self):
        self.assertEqual(semantic_profile([(1,), (-1,)], 3)["status"],
                         "UNSAT_NO_DISTRIBUTION")
        with self.assertRaises(ValueError):
            semantic_profile([], 15)


if __name__ == "__main__":
    unittest.main()
