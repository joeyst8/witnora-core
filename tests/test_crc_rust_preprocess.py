"""R-003: Rust source-preserving consensus preprocessing gates."""
from __future__ import annotations

import os
import random
import unittest

from scripts.benchmark_crc_equivalent_encodings import equivalent_encoding
from tests.test_crc_cutset_count import brute_models
from witnora_core.crc_rust_preprocess import simplify_source_in_rust
from witnora_core.crc_source import count_signed_cnf_crc


def satisfying_masks(source, n):
    return {
        mask for mask in range(1 << n)
        if all(any(bool(mask & (1 << (abs(lit) - 1))) == (lit > 0)
                   for lit in clause)
               for clause in source)
    }


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Rust native extension installed in dedicated workflow")
class TestRustSourcePreprocessing(unittest.TestCase):
    def test_200_signed_random_full_model_set_equivalences(self):
        rng = random.Random(20031)
        count = 0
        for n in (3, 4, 5, 6, 8):
            for _ in range(40):
                source = []
                for _ in range(rng.randrange(14)):
                    source.append(tuple(
                        v if rng.randrange(2) else -v
                        for v in (rng.randrange(1, n + 1)
                                  for _ in range(rng.randrange(5)))))
                result = simplify_source_in_rust(source, n)
                self.assertIsNotNone(result)
                self.assertEqual(
                    satisfying_masks(source, n),
                    satisfying_masks(result.clauses, n))
                self.assertEqual(brute_models(source, n),
                                 brute_models(result.clauses, n))
                count += 1
        self.assertEqual(count, 200)

    def test_recover_all_entailed_unit_budget_failures(self):
        for n in (8, 16, 32, 64):
            source = equivalent_encoding(n, "pairwise_forcing", "entailed_units")
            simplified = simplify_source_in_rust(source, n)
            self.assertIsNotNone(simplified)
            self.assertEqual(
                simplified.clauses,
                tuple((v,) for v in range(1, n)))
            got = count_signed_cnf_crc(
                source, n, max_inclusion_subsets=2,
                max_coefficient_states=20000,
                source_preprocessor="rust_consensus")
            self.assertIsNotNone(got)
            self.assertEqual(got.models, 2)
            if n >= 16:
                original = count_signed_cnf_crc(
                    source, n, max_inclusion_subsets=2,
                    max_coefficient_states=20000)
                self.assertIsNone(original)

    def test_protection_of_parity_source_counts(self):
        for n in (8, 16, 64):
            source = equivalent_encoding(n, "pairwise_parity", "base")
            base = count_signed_cnf_crc(source, n, max_inclusion_subsets=2)
            rust = count_signed_cnf_crc(
                source, n, max_inclusion_subsets=2,
                source_preprocessor="rust_consensus")
            self.assertEqual(base.models, 2)
            self.assertEqual(rust.models, base.models)

    def test_fail_closed_limits_and_invalid_input(self):
        source = [(1, 2), (1, -2)]
        self.assertIsNone(simplify_source_in_rust(
            source, 2, max_passes=1))
        self.assertIsNone(simplify_source_in_rust(
            source, 2, max_clause_visits=1))
        with self.assertRaises(ValueError):
            simplify_source_in_rust([(3,)], 2)
        with self.assertRaises(ValueError):
            count_signed_cnf_crc(source, 2, source_preprocessor="unknown")
        exact = count_signed_cnf_crc(
            source, 2, source_preprocessor="rust_consensus")
        self.assertEqual(exact.models, 2)


if __name__ == "__main__":
    unittest.main()
