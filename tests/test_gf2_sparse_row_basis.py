"""GF(2) sparse-basis witness checks and exact polynomial equivalence."""
from __future__ import annotations

from dataclasses import replace
import unittest

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from tests.test_exact_tensor_counting import collision_sketch
from witnora_core.aux_violation_tensors import auxiliary_weight_profile_small
from witnora_core.exact_tensor_counting import (
    count_auxiliary_weight_polynomial,
)
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.gf2_sparse_row_basis import (
    accepts_masks, build_sparse_parity_basis, verify_sparse_parity_basis,
)


class Gf2SparseRowBasisTests(unittest.TestCase):
    def test_collision_reduces_six_rows_to_three_without_changing_kernel(self) -> None:
        source, sketch = collision_sketch()
        cert = build_sparse_parity_basis(sketch)
        self.assertEqual(len(sketch.rows), 6)
        self.assertEqual(cert.rank, 3)
        self.assertEqual(cert.nullity, 1)
        self.assertEqual(max(map(len, cert.rows)), 2)
        for mask in range(1 << 4):
            self.assertEqual(accepts_masks(mask, sketch.rows),
                             accepts_masks(mask, cert.rows))
        before = count_auxiliary_weight_polynomial(source, sketch)
        after = count_auxiliary_weight_polynomial(source, sketch, basis=cert)
        self.assertEqual(before.coefficients, (1, 0, 0, 0, 1))
        self.assertEqual(after.coefficients, before.coefficients)
        self.assertEqual(after.coefficients[0], 1)

    def test_all_masks_small_random_and_both_orderings(self) -> None:
        source = random_three_cnf(4, 5, 730004, planted=True)
        sketch = geometry_aware_sparse_sketch(source, 4)
        for ordering in ("shortest_first", "source_order"):
            with self.subTest(ordering=ordering):
                cert = build_sparse_parity_basis(sketch, ordering=ordering)
                verify_sparse_parity_basis(sketch, cert)
                self.assertLessEqual(cert.rank, len(sketch.rows))
                for mask in range(1 << len(source)):
                    self.assertEqual(accepts_masks(mask, sketch.rows),
                                     accepts_masks(mask, cert.rows))
                exact = count_auxiliary_weight_polynomial(
                    source, sketch, basis=cert)
                profile = auxiliary_weight_profile_small(source, sketch)
                self.assertEqual(
                    exact.coefficients + (0,) *
                        (len(profile.coefficients) - len(exact.coefficients)),
                    profile.coefficients)

    def test_reconstruction_witness_tamper_rejected(self) -> None:
        source, sketch = collision_sketch()
        cert = build_sparse_parity_basis(sketch)
        corrupted = list(cert.expansions)
        corrupted[0] ^= 1
        with self.assertRaises(ValueError):
            verify_sparse_parity_basis(
                sketch, replace(cert, expansions=tuple(corrupted)))
        with self.assertRaises(ValueError):
            count_auxiliary_weight_polynomial(
                source, sketch,
                basis=replace(cert, expansions=tuple(corrupted)))

    def test_large_rank_construction_without_sat_enumeration(self) -> None:
        source = random_three_cnf(96, 576, 630096, planted=True)
        sketch = geometry_aware_sparse_sketch(source, 96)
        cert = build_sparse_parity_basis(sketch)
        self.assertEqual(cert.clause_count, 576)
        self.assertLessEqual(cert.rank, len(sketch.rows))
        self.assertTrue(all(len(row) <= sketch.max_row_width
                            for row in cert.rows))
        verify_sparse_parity_basis(sketch, cert)
        # The test intentionally does not enumerate any of 2**96 assignments.

    def test_validation(self) -> None:
        _, sketch = collision_sketch()
        with self.assertRaises(ValueError):
            build_sparse_parity_basis(sketch, ordering="unknown")


if __name__ == "__main__":
    unittest.main()
