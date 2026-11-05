"""R-116: batch native source-to-clause-violation compilation."""
import unittest

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from witnora_core.violation_image_anf import source_violation_polynomials


class AnfSourceBatchRustTests(unittest.TestCase):
    def test_empty_and_small_sources(self):
        for source, nvars in (([], 0), ([[]], 0), ([[1, -1]], 1),
                              ([[1], [-1]], 1), ([[1, 2], [-1, 2]], 2)):
            with self.subTest(source=source):
                self.assertEqual(source_violation_polynomials(
                    source, nvars, backend="rust"),
                    source_violation_polynomials(source, nvars))

    def test_seeded_source_formulas(self):
        for n in range(3, 14):
            for index in range(20):
                source = random_three_cnf(n, n+5, 20261127+n*100+index,
                                          planted=index % 2 == 0)
                with self.subTest(n=n, index=index):
                    self.assertEqual(source_violation_polynomials(
                        source, n, backend="rust"),
                        source_violation_polynomials(source, n))


if __name__ == "__main__":
    unittest.main()
