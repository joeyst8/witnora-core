"""Offline exact Fourier oracle and source-only parity implication tests."""
import itertools
import unittest

from scripts.experiment_satlib_residual_fourier import (
    benchmark, exact_parity_row_compatibility, source_residual_parity_rows,
)
from witnora_core.xor import canonical_xor_cnf_clauses


def holds(clauses, bits):
    return all(any(bool(bits[abs(lit) - 1]) == (lit > 0) for lit in c)
               for c in clauses)


class ResidualFourierTests(unittest.TestCase):
    def test_exact_fourier_compatibility_count(self):
        residual = [(1, 2)]
        order = [1, 2]
        rows = [((1 << 0) | (1 << 1), 0),
                ((1 << 0) | (1 << 1), 1)]
        for mask, rhs in rows:
            output = exact_parity_row_compatibility(residual, (1, 2), order,
                                                    mask, rhs, total_count=3)
            expected = sum(holds(residual, bits) and (sum(bits) % 2 == rhs)
                           for bits in itertools.product((0, 1), repeat=2))
            self.assertEqual(int(output["satisfied_residual_models"]), expected)

    def test_residual_only_rows_follow_exact_source_xor(self):
        source = sorted(canonical_xor_cnf_clauses((1, 2, 3), 1))
        source += [(1, 4), (2, -4), (-3, 4)]
        _, variables, rows, details = source_residual_parity_rows(source, 4)
        self.assertEqual(details["residual_only_parity_row_count"], 1)
        self.assertEqual(set(variables), {1, 2, 3, 4})
        for bits in itertools.product((0, 1), repeat=4):
            if holds(source, bits):
                for mask, rhs in rows:
                    self.assertEqual(sum(bits[v - 1] for v in range(1, 5)
                                         if mask & (1 << (v - 1))) % 2, rhs)

    def test_locked_holdout_and_invalid_moment_support(self):
        with self.assertRaises(ValueError):
            benchmark(name="par32-2-c.cnf.Z")
        with self.assertRaises(ValueError):
            exact_parity_row_compatibility([(1,)], (1,), [1], 1 << 2, 0)


if __name__ == "__main__":
    unittest.main()
