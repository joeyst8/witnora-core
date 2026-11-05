"""R-113: native algebra in source/row violation polynomial generation."""
import unittest

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.gf2_sparse_row_basis import build_sparse_parity_basis
from witnora_core.violation_image_anf import (
    analyze_parity_anf, clause_violation_polynomial,
    source_violation_polynomials, row_violation_polynomials,
)


class AnfSourcePipelineRustTests(unittest.TestCase):
    def test_seeded_cnf_and_parity_rows(self):
        for n in range(3, 9):
            for index in range(12):
                source = random_three_cnf(n, n+3, 20261121+n*100+index,
                                          planted=True)
                sketch = geometry_aware_sparse_sketch(source, n)
                basis = build_sparse_parity_basis(sketch)
                with self.subTest(n=n, index=index):
                    for clause in source:
                        self.assertEqual(clause_violation_polynomial(
                            clause, backend="rust"),
                            clause_violation_polynomial(clause))
                    self.assertEqual(source_violation_polynomials(
                        source, n, backend="rust"),
                        source_violation_polynomials(source, n))
                    self.assertEqual(row_violation_polynomials(
                        source, sketch, backend="rust"),
                        row_violation_polynomials(source, sketch))
                    self.assertEqual(row_violation_polynomials(
                        source, sketch, basis=basis, backend="rust"),
                        row_violation_polynomials(source, sketch, basis=basis))
                    self.assertEqual(analyze_parity_anf(
                        source, sketch, backend="rust"),
                        analyze_parity_anf(source, sketch))


if __name__ == "__main__":
    unittest.main()
