"""R-057 full native sparse-odd sketch -> GF2 basis -> finite acceptance gate."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.constraint_geometry import canonical_source
from witnora_core.eth_clause_violation_parity import violation_mask
from witnora_core.sparse_parity_checks import (
    build_sparse_odd_sketch, build_sparse_odd_sketch_rust,
    low_weight_collisions_rust,
    audit_sparse_small, audit_sparse_small_rust,
)
from witnora_core.gf2_sparse_row_basis import (
    build_sparse_parity_basis, build_sparse_parity_basis_rust,
    verify_sparse_parity_basis_rust,
    accepts_masks, accepts_masks_rust,
)


def independent_rank(rows):
    """Separate binary elimination over ORIGINAL row signatures."""
    basis = {}
    for row in rows:
        value = sum(1 << j for j in row)
        while value:
            pivot = value.bit_length()-1
            if pivot not in basis:
                basis[pivot] = value
                break
            value ^= basis[pivot]
    return len(basis)


def direct_violation_vector(source, assignment, nvars):
    values = [(assignment >> j) & 1 for j in range(nvars)]
    mask = 0
    for j, clause in enumerate(source):
        satisfied = any(
            (values[abs(lit)-1] == (lit > 0)) for lit in clause
        )
        if not satisfied:
            mask |= 1 << j
    return mask


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 extension installed in dedicated Rust CI")
class TestNativeSparsePipeline(unittest.TestCase):
    def test_250_source_to_sparse_basis_to_parity_audits(self):
        rng = random.Random(57112026)
        for case in range(250):
            nvars = rng.randrange(1, 8)
            clauses = [
                [rng.randrange(1, nvars+1) * rng.choice((-1, 1))
                 for _ in range(rng.randrange(0, 5))]
                for _ in range(rng.randrange(0, 10))
            ]
            max_width = rng.randrange(3, 8)
            seed = rng.randrange(1000000)
            with self.subTest(case=case):
                native_sketch = build_sparse_odd_sketch_rust(
                    clauses, nvars, max_row_width=max_width, seed=seed
                )
                py_sketch = build_sparse_odd_sketch(
                    clauses, nvars, max_row_width=max_width, seed=seed
                )
                self.assertEqual(native_sketch, py_sketch)
                self.assertEqual(low_weight_collisions_rust(native_sketch), 0)
                source = canonical_source(clauses, nvars)
                for ordering in ("shortest_first", "source_order"):
                    py_basis = build_sparse_parity_basis(
                        py_sketch, ordering=ordering
                    )
                    native_basis = build_sparse_parity_basis_rust(
                        native_sketch, ordering=ordering
                    )
                    self.assertEqual(native_basis, py_basis)
                    verify_sparse_parity_basis_rust(native_sketch, native_basis)
                    self.assertEqual(native_basis.rank,
                                     independent_rank(native_sketch.rows))
                    # A parity basis must have EXACTLY the same accepted
                    # violation vectors, not merely source-assignment parity.
                    for mask in range(1 << len(clauses)):
                        expected = accepts_masks(mask, py_sketch.rows)
                        self.assertEqual(accepts_masks_rust(mask,
                                         native_basis.rows), expected)
                    for assignment in range(1 << nvars):
                        expected = direct_violation_vector(
                            source, assignment, nvars
                        )
                        self.assertEqual(
                            violation_mask(source, assignment), expected
                        )
                        self.assertEqual(
                            accepts_masks_rust(expected, native_basis.rows),
                            accepts_masks(expected, py_sketch.rows)
                        )
                self.assertEqual(
                    audit_sparse_small_rust(clauses, native_sketch),
                    audit_sparse_small(clauses, py_sketch)
                )

    def test_more_than_128_selected_original_rows_survive_native_pipeline(self):
        # A synthetic parity-row collection with 136 independent rows
        # stresses arbitrary precision. It is NOT a valid degree-three
        # sketch; the certificate is checked at row-space level only.
        from witnora_core.sparse_parity_checks import SparseOddSketch
        from witnora_core.gf2_sparse_row_basis import (
            build_sparse_parity_basis_rust, verify_sparse_parity_basis_rust
        )
        rows = tuple((j,) for j in range(136)) + (
            (0, 135), (1, 134), (), (0, 135)
        )
        sketch = SparseOddSketch(0, 140, "synthetic", 2, rows)
        native = build_sparse_parity_basis_rust(sketch)
        self.assertEqual(native.rank, 136)
        self.assertGreater(max(native.expansions), 1 << 128)
        verify_sparse_parity_basis_rust(sketch, native)


if __name__ == "__main__":
    unittest.main()
