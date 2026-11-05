"""Geometry-aware clause grouping: source graph containment and frontier."""
from __future__ import annotations

from itertools import combinations
import unittest

from scripts.generate_glucose_dense_3sat_lean import find_case, random_three_cnf
from witnora_core.geometry_aware_parity import (
    geometry_aware_sparse_sketch, source_primal_pairs,
)
from witnora_core.sparse_parity_checks import (
    audit_sparse_small, build_sparse_odd_sketch, low_weight_collisions,
    min_degree_elimination_width, validate_sparse_odd_sketch,
)


def factor_primal_pairs(source: list[list[int]],
                        rows: tuple[tuple[int, ...], ...]) -> set[tuple[int, int]]:
    all_pairs: set[tuple[int, int]] = set()
    for row in rows:
        scope = sorted({abs(lit) for j in row for lit in source[j]})
        all_pairs.update(combinations(scope, 2))
    return all_pairs


def induced_width(source: list[list[int]],
                  rows: tuple[tuple[int, ...], ...], nvars: int) -> int:
    scopes = [{abs(lit) for j in row for lit in source[j]} for row in rows]
    return min_degree_elimination_width(scopes, nvars)


class GeometryAwareParityTests(unittest.TestCase):
    def test_all_six_small_dense_sources_have_no_false_positives(self) -> None:
        for nvars, nclauses in ((8, 54), (10, 66), (12, 84)):
            for planted in (False, True):
                with self.subTest(nvars=nvars, planted=planted):
                    source, _ = find_case(nvars, nclauses, planted=planted)
                    sketch = geometry_aware_sparse_sketch(source, nvars)
                    validate_sparse_odd_sketch(source, sketch)
                    self.assertEqual(low_weight_collisions(sketch), 0)
                    self.assertTrue(all(len(row) <= 5 for row in sketch.rows))
                    self.assertEqual(audit_sparse_small(
                        source, sketch).false_positives, 0)
                    self.assertTrue(
                        source_primal_pairs(tuple(tuple(c) for c in source))
                        <= factor_primal_pairs(source, sketch.rows))

    def test_row_width_one_preserves_original_primal_graph_exactly(self) -> None:
        source = random_three_cnf(32, 224, 630032, planted=True)
        sketch = geometry_aware_sparse_sketch(source, 32, max_row_width=1)
        self.assertEqual(len(sketch.rows), 3 * len(source))
        self.assertEqual(
            source_primal_pairs(tuple(tuple(c) for c in source)),
            factor_primal_pairs(source, sketch.rows))
        self.assertEqual(low_weight_collisions(sketch), 0)

    def test_local_grouping_frozen_96_var_width_better_than_random(self) -> None:
        source = random_three_cnf(96, 576, 630096, planted=True)
        local = geometry_aware_sparse_sketch(source, 96)
        random = build_sparse_odd_sketch(source, 96)
        self.assertLess(induced_width(source, local.rows, 96),
                        induced_width(source, random.rows, 96))
        self.assertLessEqual(max(len(row) for row in local.rows), 5)
        # No 2**96 assignment enumeration can occur in this test.

    def test_duplicate_variable_triples_receive_distinct_column_signatures(self) -> None:
        source = [[1, 2, 3], [1, -2, 3], [-1, 2, 3]]
        sketch = geometry_aware_sparse_sketch(source, 3, max_row_width=3)
        validate_sparse_odd_sketch(source, sketch)
        self.assertEqual(low_weight_collisions(sketch), 0)
        self.assertTrue(all(len(row) <= 3 for row in sketch.rows))

    def test_non_three_cnf_rejected(self) -> None:
        with self.assertRaises(ValueError):
            geometry_aware_sparse_sketch([[1, 2]], 2)
        with self.assertRaises(ValueError):
            geometry_aware_sparse_sketch([[1, 1, 2]], 2)
        with self.assertRaises(ValueError):
            geometry_aware_sparse_sketch([[1, 2, 3]], 3, max_row_width=0)


if __name__ == "__main__":
    unittest.main()
