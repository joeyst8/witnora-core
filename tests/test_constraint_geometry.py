"""Geometric lower-bound controls and non-enumerative parity construction."""
from __future__ import annotations

from dataclasses import replace
from itertools import combinations
import unittest
from unittest.mock import patch

from scripts.generate_glucose_dense_3sat_lean import find_case, random_three_cnf
from witnora_core.constraint_geometry import (
    audit_small_collisions, build_dense_random_sketch, canonical_source,
    row_statistics, singleton_coverage_lower_bound, validate_dense_sketch,
)
from witnora_core.eth_clause_violation_parity import parity_accepts


class ConstraintGeometryTests(unittest.TestCase):
    def test_dense_constructor_never_enumerates_assignments(self) -> None:
        # 96 variables is deliberately outside the finite-audit domain.
        source = random_three_cnf(96, 576, 7321, planted=True)
        with patch("witnora_core.constraint_geometry.violation_mask",
                   side_effect=AssertionError("builder enumerated assignments")):
            sketch = build_dense_random_sketch(source, 96,
                                               security_bits=20, seed=17)
        self.assertEqual(len(sketch.rows), 116)
        self.assertEqual(sketch.clause_count, 576)
        self.assertEqual(sketch, build_dense_random_sketch(
            source, 96, security_bits=20, seed=17))
        self.assertLess(row_statistics(sketch)[0], 576)
        validate_dense_sketch(source, sketch)
        with self.assertRaises(ValueError):
            audit_small_collisions(source, sketch)

    def test_six_frozen_dense_controls_have_no_collisions(self) -> None:
        for nvars, nclauses in ((8, 54), (10, 66), (12, 84)):
            for planted in (False, True):
                with self.subTest(n=nvars, planted=planted):
                    cnf, _ = find_case(nvars, nclauses, planted=planted)
                    sketch = build_dense_random_sketch(
                        cnf, nvars, security_bits=20, seed=73)
                    profile = audit_small_collisions(cnf, sketch)
                    self.assertEqual(profile.assignments, 1 << nvars)
                    self.assertEqual(profile.false_positives, 0)
                    self.assertEqual(profile.source_models > 0, planted)
                    # These are DENSE rows; not a sparse or fast SAT result.
                    self.assertGreater(row_statistics(sketch)[1], nclauses / 3)

    def test_singleton_violation_geometry_obstructs_sparse_compression(self) -> None:
        cnf = [[1], [2], [3], [4], [5]]
        sketch = build_dense_random_sketch(cnf, 5, security_bits=12, seed=1)
        profile = audit_small_collisions(cnf, sketch)
        self.assertEqual(profile.singleton_violation_clause_ids,
                         frozenset(range(5)))
        self.assertEqual(singleton_coverage_lower_bound(
            profile.singleton_violation_clause_ids, 2), 3)
        # Any two rows of width <=2 cover at most 4 of the five singleton
        # witnesses. Exhaustively demonstrate the obstruction in this case.
        candidates = [tuple(x) for width in (1, 2)
                      for x in combinations(range(5), width)]
        for first, second in combinations(candidates, 2):
            self.assertTrue(any(
                parity_accepts(1 << j, (first, second))
                for j in range(5)
            ))

    def test_source_identity_and_bad_indices_rejected(self) -> None:
        source = [[1], [2]]
        sketch = build_dense_random_sketch(source, 2, security_bits=6, seed=0)
        with self.assertRaises(ValueError):
            validate_dense_sketch([[-1], [2]], sketch)
        forged = replace(sketch, rows=sketch.rows[:-1] + ((2,),))
        with self.assertRaises(ValueError):
            validate_dense_sketch(source, forged)
        with self.assertRaises(ValueError):
            build_dense_random_sketch([[0]], 2, seed=0)
        with self.assertRaises(ValueError):
            build_dense_random_sketch([[1]], 0, seed=0)
        with self.assertRaises(ValueError):
            build_dense_random_sketch([[1]], 1, security_bits=-1)
        with self.assertRaises(ValueError):
            singleton_coverage_lower_bound(frozenset({1}), 0)

    def test_independent_uniform_row_parity_is_balanced(self) -> None:
        # Finite check of the combinatorial half/half identity, not a
        # certificate that a particular PRNG seed generated ideal entropy.
        for m in range(1, 6):
            for nonzero in range(1, 1 << m):
                detected = sum((rowmask & nonzero).bit_count() % 2
                               for rowmask in range(1 << m))
                self.assertEqual(detected, 1 << (m - 1))
        self.assertEqual(canonical_source([[1, -2]], 2), ((1, -2),))


if __name__ == "__main__":
    unittest.main()
