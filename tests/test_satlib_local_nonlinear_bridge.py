"""Offline checks for exact local XOR/nonlinear factor composition."""
import itertools
import unittest

from scripts.experiment_satlib_local_nonlinear_bridge import (
    benchmark, local_bridge, syndrome_cut_rank, syndrome_frontier,
)
from witnora_core.xor import canonical_xor_cnf_clauses


class LocalBridgeTests(unittest.TestCase):
    def test_exact_combined_count_matches_full_source(self):
        source = sorted(canonical_xor_cnf_clauses((1, 2, 3), 1))
        source += [(1, 4), (2, -4), (-3, 4)]
        result = local_bridge(source, 4)
        self.assertEqual(result["status"], "EXACT_LOCAL_COUNT")
        self.assertEqual(result["source_derived_local_xor_rows"], 1)
        self.assertEqual(result["unprocessed_global_xor_rows"], 0)
        self.assertTrue(result["width_certificate_verified"])
        expected = sum(all(any(bool(bits[abs(lit) - 1]) == (lit > 0)
                               for lit in c) for c in source)
                       for bits in itertools.product((0, 1), repeat=4))
        self.assertEqual(int(result["exact_residual_plus_local_models"]), expected)

    def test_holdout_and_tuning_closed(self):
        with self.assertRaises(ValueError):
            benchmark("par32-2-c.cnf.Z")
        with self.assertRaises(ValueError):
            local_bridge([], 4, max_local_width=6)

    def test_exact_syndrome_frontier_boundaries(self):
        result = syndrome_frontier((1, 2, 3, 4), [((1, 3), 0), ((2, 4), 1)])
        self.assertEqual(result["maximum_active_global_rows"], 2)
        self.assertEqual(result["mean_active_global_rows"], 1.333)
        with self.assertRaises(ValueError):
            syndrome_frontier((1, 2), [((1, 3), 0)])

    def test_syndrome_cut_rank_invariant_under_row_xor(self):
        order = (1, 2, 3, 4)
        original = [((1, 3), 0), ((2, 4), 1)]
        combined = [((1, 3), 0), ((1, 2, 3, 4), 1)]
        a = syndrome_cut_rank(order, original)
        b = syndrome_cut_rank(order, combined)
        self.assertEqual(a["global_row_rank"], 2)
        self.assertEqual(a["maximum_cut_connectivity_rank"], 2)
        self.assertEqual(a, b)


if __name__ == "__main__":
    unittest.main()
