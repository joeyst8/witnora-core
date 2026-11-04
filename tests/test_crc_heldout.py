"""W-CRC-016 held-out structured graphs and width rejection controls."""
from __future__ import annotations

import unittest

from scripts.benchmark_crc_heldout import (
    tree_source, ladder_source, bridged_cliques,
)
from tests.test_crc_cutset_count import brute_models
from witnora_core.crc_cutset_count import count_source_by_separator


class TestCRCHeldoutGraphs(unittest.TestCase):
    def test_randomized_tree_admitted_and_exact(self):
        for seed in (16016, 16017, 16018):
            n = 10
            source, left, right = tree_source(n, seed)
            got = count_source_by_separator(
                source, tuple(range(1, n + 1)), left, right,
                (1 << n) - 1, max_separator_size=2,
                component_backend="variable_elimination_indexed",
                max_ve_factor_variables=4)
            self.assertIsNotNone(got)
            self.assertEqual(got.models, brute_models(source, n))

    def test_signed_ladder_admitted_and_exact(self):
        for seed in (16016, 16017, 16018):
            n = 10
            source, left, right = ladder_source(n, seed)
            got = count_source_by_separator(
                source, tuple(range(1, n + 1)), left, right,
                (1 << n) - 1, max_separator_size=2,
                component_backend="variable_elimination_indexed",
                max_ve_factor_variables=4)
            self.assertIsNotNone(got)
            self.assertEqual(got.models, brute_models(source, n))

    def test_bridge_does_not_override_large_clique_factor_width(self):
        source, n, left, right = bridged_cliques(7)
        self.assertIsNone(count_source_by_separator(
            source, tuple(range(1, n + 1)), left, right,
            (1 << n) - 1, max_separator_size=2,
            component_backend="variable_elimination_indexed",
            max_ve_factor_variables=4))
        self.assertIsNotNone(count_source_by_separator(
            source, tuple(range(1, n + 1)), left, right,
            (1 << n) - 1, max_separator_size=2,
            component_backend="variable_elimination_indexed",
            max_ve_factor_variables=7))


if __name__ == "__main__":
    unittest.main()
