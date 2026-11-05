"""R-053 sparse GF(2) original-row subset basis: exact parity and finite oracles."""
from __future__ import annotations

from dataclasses import replace
from itertools import product
import os
import random
import unittest

from witnora_core.sparse_parity_checks import SparseOddSketch
from witnora_core.gf2_sparse_row_basis import (
    row_mask, row_mask_rust,
    build_sparse_parity_basis, build_sparse_parity_basis_rust,
    verify_sparse_parity_basis, verify_sparse_parity_basis_rust,
    accepts_masks, accepts_masks_rust,
)


def parity_oracle(mask, rows):
    """Independent direct parity sum on each retained ORIGINAL row."""
    return all(sum((mask >> col) & 1 for col in row) % 2 == 0
               for row in rows)


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "PyO3 extension installed in dedicated native CI")
class TestNativeSparseBasis(unittest.TestCase):
    def test_600_random_sketches_exact_certificates_and_model_equivalence(self):
        rng = random.Random(53112026)
        count = 0
        for clause_count in range(12):
            for sample in range(50):
                row_count = rng.randrange(0, 18)
                max_width = rng.randrange(1, 6)
                rows = tuple(
                    tuple(sorted(rng.sample(range(clause_count),
                        rng.randrange(min(max_width, clause_count) + 1))))
                    for _ in range(row_count)
                )
                sketch = SparseOddSketch(
                    0, clause_count, "synthetic-not-source-verified",
                    max_width, rows,
                )
                for ordering in ("shortest_first", "source_order"):
                    with self.subTest(m=clause_count, sample=sample,
                                      ordering=ordering):
                        py = build_sparse_parity_basis(sketch, ordering=ordering)
                        rust = build_sparse_parity_basis_rust(
                            sketch, ordering=ordering
                        )
                        self.assertEqual(rust, py)
                        self.assertEqual(rust.rank, len(rust.selected_indices))
                        self.assertEqual(rust.nullity, clause_count-rust.rank)
                        verify_sparse_parity_basis_rust(sketch, rust)
                        verify_sparse_parity_basis(sketch, rust)
                        self.assertTrue(all(
                            rust.rows[j] == rows[source_index]
                            for j, source_index in enumerate(rust.selected_indices)
                        ))
                        for mask in (
                            range(1 << clause_count) if clause_count <= 8
                            else (rng.getrandbits(clause_count) for _ in range(24))
                        ):
                            expected = parity_oracle(mask, rows)
                            self.assertEqual(accepts_masks(mask, py.rows), expected)
                            self.assertEqual(accepts_masks_rust(mask, rust.rows),
                                             expected)
                        for row in rows:
                            self.assertEqual(row_mask_rust(row), row_mask(row))
                count += 1
        self.assertEqual(count, 600)

    def test_over_128_independent_rows_exercise_unbounded_bitsets(self):
        rows = tuple((j,) for j in range(130)) + ((0, 129), (), (0, 129))
        sketch = SparseOddSketch(0, 150, "synthetic", 2, rows)
        for ordering in ("source_order", "shortest_first"):
            with self.subTest(ordering=ordering):
                py = build_sparse_parity_basis(sketch, ordering=ordering)
                rust = build_sparse_parity_basis_rust(sketch, ordering=ordering)
                self.assertEqual(rust, py)
                self.assertEqual(rust.rank, 130)
                self.assertGreater(max(rust.expansions), 1 << 64)
                verify_sparse_parity_basis_rust(sketch, rust)
                for mask in (0, 1, 1 << 129, (1 << 149) + 3):
                    self.assertEqual(accepts_masks_rust(mask, rust.rows),
                                     parity_oracle(mask, rows))
        self.assertEqual(row_mask_rust((129, 149)), (1 << 129) | (1 << 149))

    def test_tampered_basis_certificates_are_rejected(self):
        sketch = SparseOddSketch(0, 3, "synthetic", 2,
                                 ((0, 1), (1, 2), (0, 2), (), (0, 1)))
        cert = build_sparse_parity_basis_rust(sketch, ordering="source_order")
        for bad in (
            replace(cert, clause_count=4),
            replace(cert, original_row_count=4),
            replace(cert, ordering="invalid"),
            replace(cert, selected_indices=(0, 0)),
            replace(cert, rows=((0, 2), (1, 2))),
            replace(cert, expansions=(0,)+cert.expansions[1:]),
            replace(cert, expansions=cert.expansions[:-1]+(1 << 300,)),
        ):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    verify_sparse_parity_basis_rust(sketch, bad)
                with self.assertRaises(ValueError):
                    verify_sparse_parity_basis(sketch, bad)

    def test_malformed_source_rows_and_ordering_fail_closed(self):
        for rows, m, width in (
            (((0, 0),), 2, 2),
            (((1, 0),), 2, 2),
            (((2,),), 2, 2),
            (((0, 1, 2),), 3, 2),
            (((-1,),), 3, 2),
        ):
            sketch = SparseOddSketch(0, m, "synthetic", width, rows)
            with self.subTest(rows=rows):
                with self.assertRaises(ValueError):
                    build_sparse_parity_basis_rust(sketch)
                with self.assertRaises(ValueError):
                    build_sparse_parity_basis(sketch)
        sketch = SparseOddSketch(0, 2, "synthetic", 2, ((0,),))
        with self.assertRaises(ValueError):
            build_sparse_parity_basis_rust(sketch, ordering="unknown")
        with self.assertRaises(ValueError):
            build_sparse_parity_basis(sketch, ordering="unknown")


if __name__ == "__main__":
    unittest.main()
