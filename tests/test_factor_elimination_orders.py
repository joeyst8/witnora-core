"""Tests of frozen elimination orders and independently replayed widths."""
from __future__ import annotations

import unittest

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from witnora_core.aux_violation_tensors import auxiliary_factor_scopes
from witnora_core.factor_elimination_orders import (
    elimination_order, replay_elimination_width,
)
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.sparse_parity_checks import min_degree_elimination_width


class FactorEliminationOrdersTests(unittest.TestCase):
    def test_modes_replay_on_small_graph_with_unused_vertices(self) -> None:
        scopes = [{1, 2, 3}, {3, 4}, {4, 5}, {2, 5}, {1, 6}]
        for mode in ("min_degree", "source_first", "aux_first", "beam_fill"):
            with self.subTest(mode=mode):
                r = elimination_order(scopes, 7, nsource=3, mode=mode)
                self.assertEqual(len(r.order), 7)
                self.assertEqual(r.induced_width,
                                 replay_elimination_width(scopes, 7, r.order))
                self.assertGreaterEqual(r.added_fill_edges, 0)
        min_degree = elimination_order(scopes, 7, nsource=3)
        self.assertEqual(min_degree.induced_width,
                         min_degree_elimination_width(scopes, 7))

    def test_source_and_aux_block_orders_are_disjoint_in_sequence(self) -> None:
        scopes = [{1, 2, 4}, {2, 3, 5}, {4, 5, 6}]
        a = elimination_order(scopes, 6, nsource=3, mode="source_first")
        b = elimination_order(scopes, 6, nsource=3, mode="aux_first")
        self.assertTrue(all(v <= 3 for v in a.order[:3]))
        self.assertTrue(all(v > 3 for v in a.order[3:]))
        self.assertTrue(all(v > 3 for v in b.order[:3]))
        self.assertTrue(all(v <= 3 for v in b.order[3:]))

    def test_frozen_32_variable_auxiliary_graph(self) -> None:
        n, m = 32, 224
        source = random_three_cnf(n, m, 630032, planted=True)
        sketch = geometry_aware_sparse_sketch(source, n)
        scopes = auxiliary_factor_scopes(source, sketch)
        baseline = min_degree_elimination_width(scopes, n + m)
        for mode in ("min_degree", "source_first", "aux_first", "beam_fill"):
            with self.subTest(mode=mode):
                r = elimination_order(scopes, n + m, nsource=n, mode=mode)
                self.assertEqual(r.induced_width,
                                 replay_elimination_width(
                                     scopes, n + m, r.order))
                if mode == "min_degree":
                    self.assertEqual(r.induced_width, baseline)

    def test_validation(self) -> None:
        with self.assertRaises(ValueError):
            elimination_order([{1}], 1, nsource=2)
        with self.assertRaises(ValueError):
            elimination_order([{4}], 3, nsource=1)
        with self.assertRaises(ValueError):
            elimination_order([], 3, nsource=1, mode="bad")
        with self.assertRaises(ValueError):
            elimination_order([], 3, nsource=1, mode="beam_fill", beam=0)
        with self.assertRaises(ValueError):
            replay_elimination_width([{1}], 3, (1, 1, 2))


if __name__ == "__main__":
    unittest.main()
