"""Offline exact source-to-native-XOR tests for CryptoMiniSat comparison."""
import itertools
import unittest

from scripts.experiment_satlib_cryptominisat_gate import (
    benchmark, bounded_cms, native_xor_source,
)
from witnora_core.xor import canonical_xor_cnf_clauses


class CryptoMiniSatGateTests(unittest.TestCase):
    def test_known_sat_original_model_is_verified_in_all_three_modes(self):
        clauses = sorted(canonical_xor_cnf_clauses((1, 2, 3), 1))
        clauses += sorted(canonical_xor_cnf_clauses((3, 4, 5), 0))
        clauses += [(1, 4), (-2, -5)]
        for mode in ("raw_cnf", "native_xor", "affine_quotient"):
            with self.subTest(mode=mode):
                result = bounded_cms(clauses, 5, mode, timeout_s=2)
                self.assertEqual(result["status"], "SAT", result)
                self.assertTrue(result["verified_original_model"])

    def test_verified_partition_preserves_truth_on_every_assignment(self):
        clauses = sorted(canonical_xor_cnf_clauses((1, 2, 3), 1))
        clauses += [(1, 4), (2, -4)]
        residual, rows, info = native_xor_source(clauses)
        self.assertEqual(info["source_bound_xor_rows"], 1)
        self.assertEqual(info["removed_exact_encoding_clauses"], 4)
        self.assertEqual(info["residual_clauses"], 2)
        for bits in itertools.product((0, 1), repeat=4):
            original = all(any(bool(bits[abs(lit) - 1]) == (lit > 0) for lit in c)
                           for c in clauses)
            partition = (all(any(bool(bits[abs(lit) - 1]) == (lit > 0) for lit in c)
                             for c in residual) and
                         all((sum(bits[v - 1] for v in vars_) % 2) == int(rhs)
                             for vars_, rhs in rows))
            self.assertEqual(original, partition)

    def test_holdout_rejected_before_fetch(self):
        with self.assertRaises(ValueError):
            benchmark(name="par32-2-c.cnf.Z")


if __name__ == "__main__":
    unittest.main()
