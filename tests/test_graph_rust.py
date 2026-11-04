"""R-016 graph topology and exact incidence components in Rust."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.components import connected_components, component_details
from witnora_core.primal import primal_graph


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustGraphAndComponents(unittest.TestCase):
    def test_1200_random_graph_component_and_hash_differentials(self):
        rng = random.Random(16162026)
        for n in range(1, 13):
            for _ in range(100):
                source = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(6))]
                    for _ in range(rng.randrange(14))
                ]
                formula = CNFFormula.from_raw_clauses(source)
                with self.subTest(n=n, source=source):
                    self.assertEqual(
                        primal_graph(formula, backend="rust"),
                        primal_graph(formula, backend="python"))
                    self.assertEqual(
                        connected_components(formula, backend="rust"),
                        connected_components(formula, backend="python"))
                    self.assertEqual(
                        component_details(formula, backend="rust"),
                        component_details(formula, backend="python"))

    def test_empty_and_disconnected_empty_clause_components(self):
        for raw in (
            [], [[]], [[1], [2]], [[], [1], [2]],
            [[1, 2, 3], [-3, 4], [7], []],
        ):
            formula = CNFFormula(raw)
            self.assertEqual(
                connected_components(formula, backend="rust"),
                connected_components(formula))
            self.assertEqual(
                primal_graph(formula, backend="rust"),
                primal_graph(formula))

    def test_unknown_graph_backends(self):
        with self.assertRaises(ValueError):
            primal_graph(CNFFormula(), backend="invalid")
        with self.assertRaises(ValueError):
            connected_components(CNFFormula(), backend="invalid")


if __name__ == "__main__":
    unittest.main()
