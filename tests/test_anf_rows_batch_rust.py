"""R-117: batch native parity-row ANF compilation."""
import unittest

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.gf2_sparse_row_basis import build_sparse_parity_basis
from witnora_core.violation_image_anf import row_violation_polynomials


class AnfRowsBatchRustTests(unittest.TestCase):
    def test_seeded_sketches_and_basis_rows(self):
        for n in range(3, 12):
            for index in range(18):
                source = random_three_cnf(n, n+2, 20261128+n*100+index,
                                          planted=index % 2 == 0)
                sketch = geometry_aware_sparse_sketch(source, n)
                basis = build_sparse_parity_basis(sketch)
                with self.subTest(n=n, index=index):
                    self.assertEqual(row_violation_polynomials(
                        source, sketch, backend="rust"),
                        row_violation_polynomials(source, sketch))
                    self.assertEqual(row_violation_polynomials(
                        source, sketch, basis=basis, backend="rust"),
                        row_violation_polynomials(source, sketch, basis=basis))


if __name__ == "__main__":
    unittest.main()
