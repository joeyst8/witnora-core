"""W-CRC-019 mathematical equivalence and encoding sensitivity controls."""
from __future__ import annotations

import unittest

from scripts.benchmark_crc_scaling import interaction_density
from scripts.benchmark_crc_matched_semantics import semantic_profile
from scripts.benchmark_crc_equivalent_encodings import (
    FAMILIES, equivalent_encoding, model_masks,
)


class TestCRCEquivalentEncodings(unittest.TestCase):
    def test_every_variant_has_identical_source_solution_set(self):
        for n in (6, 8, 10):
            for family, variants in FAMILIES.items():
                expected = model_masks(equivalent_encoding(n, family, "base"), n)
                self.assertEqual(len(expected), 2)
                for variant in variants:
                    with self.subTest(n=n, family=family, variant=variant):
                        got = model_masks(equivalent_encoding(n, family, variant), n)
                        self.assertEqual(got, expected)

    def test_syntactic_graph_is_preserved_except_consensus_reduced(self):
        n = 8
        boundary = tuple(range(1, n + 1))
        for family, variants in FAMILIES.items():
            for variant in variants:
                density = interaction_density(
                    equivalent_encoding(n, family, variant), boundary)
                expected = 0.0 if variant == "consensus_reduced" else 1.0
                self.assertEqual(density, expected)

    def test_solution_profiles_are_exactly_encoding_invariant(self):
        for family in FAMILIES:
            source = equivalent_encoding(8, family, "base")
            expected = semantic_profile(source, 8)
            for variant in FAMILIES[family]:
                self.assertEqual(
                    semantic_profile(equivalent_encoding(8, family, variant), 8),
                    expected)

    def test_invalid_variant_and_exhaustive_cap(self):
        with self.assertRaises(ValueError):
            equivalent_encoding(8, "pairwise_forcing", "not_a_variant")
        with self.assertRaises(ValueError):
            model_masks([], 12)


if __name__ == "__main__":
    unittest.main()
