"""W-CRC-017 complete primal graph is not enough to fix #SAT behavior."""
from __future__ import annotations

import unittest

from scripts.benchmark_crc_scaling import interaction_density
from scripts.benchmark_crc_dense_semantics import dense_source
from tests.test_crc_cutset_count import brute_models
from witnora_core.crc_source import count_signed_cnf_crc


class TestCRCDenseSemantics(unittest.TestCase):
    def test_same_complete_graph_has_2_zero_or_n_plus_one_models(self):
        for n in (5, 8):
            for family, expected in (
                ("parity_consistent", 2),
                ("parity_inconsistent", 0),
                ("positive_or", n + 1),
            ):
                source = dense_source(n, family)
                self.assertEqual(interaction_density(
                    source, tuple(range(1, n + 1))), 1.0)
                self.assertEqual(brute_models(source, n), expected)
                result = count_signed_cnf_crc(
                    source, n, max_inclusion_subsets=2,
                    enable_orbit_oracle=True)
                self.assertIsNotNone(result)
                self.assertEqual(result.models, expected)

    def test_mixed_sign_source_keeps_same_graph_and_exactness(self):
        n = 8
        source = dense_source(n, "signed_or")
        self.assertEqual(interaction_density(
            source, tuple(range(1, n + 1))), 1.0)
        expected = brute_models(source, n)
        result = count_signed_cnf_crc(
            source, n, max_inclusion_subsets=2,
            max_coefficient_states=20000,
            enable_orbit_oracle=True)
        self.assertIsNotNone(result)
        self.assertEqual(result.models, expected)


if __name__ == "__main__":
    unittest.main()
