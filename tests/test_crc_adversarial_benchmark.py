"""W-CRC-013 independent exact and fail-closed family guards."""
from __future__ import annotations

import unittest

from scripts.benchmark_crc_adversarial import (
    block_source, chain_source, ring_source,
)
from tests.test_crc_cutset_count import brute_models
from witnora_core.crc_cutset_count import count_source_by_separator


class TestCRCAdversarialBenchmark(unittest.TestCase):
    def test_signed_three_variable_blocks_have_analytic_product(self):
        for k in (2, 3):
            source, n, expected = block_source(k)
            result = count_source_by_separator(
                source, tuple(range(1, n + 1)),
                (1,), (4,), (1 << n) - 1,
                max_separator_size=2, max_component_variables=8)
            self.assertIsNotNone(result)
            self.assertEqual(result.models, expected)
            self.assertEqual(result.models, brute_models(source, n))

    def test_chain_and_ring_rejected_on_large_residual_components(self):
        for family in (chain_source, ring_source):
            n = 32
            source = family(n)
            self.assertIsNone(count_source_by_separator(
                source, tuple(range(1, n + 1)), (1,), (n,),
                (1 << n) - 1, max_separator_size=2,
                max_component_variables=8))


if __name__ == "__main__":
    unittest.main()
