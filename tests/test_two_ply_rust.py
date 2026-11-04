"""R-042 two-ply Davis-Putnam lookahead: exact parity and semantic controls."""
from __future__ import annotations

import os
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.lookahead_pivot_prototype import (
    elimination_options, elimination_options_rust,
    two_ply_pivot, two_ply_pivot_rust,
)


def satisfiable_brute(formula):
    variables = formula.variables
    return any(
        formula_satisfied(formula, dict(zip(variables, values)))
        for values in product((False, True), repeat=len(variables))
    )


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestTwoPlyNative(unittest.TestCase):
    def test_1200_random_sources_full_options_and_decision_parity(self):
        rng = random.Random(42112026)
        checked = 0
        for n in range(1, 9):
            for case in range(150):
                source = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(12))
                ]
                formula = CNFFormula.from_raw_clauses(source)
                pairs = rng.choice((0, 1, 2, 4, 8, 12, 20))
                growth = rng.choice((0, 1, 2, 4))
                beam = rng.randrange(1, 9)
                with self.subTest(n=n, case=case):
                    py_options = elimination_options(
                        formula, max_pairs=pairs, growth_budget=growth)
                    rs_options = elimination_options_rust(
                        formula, max_pairs=pairs, growth_budget=growth)
                    self.assertEqual(rs_options, py_options)
                    for _, reduced in rs_options:
                        self.assertEqual(
                            satisfiable_brute(formula),
                            satisfiable_brute(reduced))
                    py = two_ply_pivot(
                        formula, max_pairs=pairs, growth_budget=growth,
                        beam_width=beam)
                    rs = two_ply_pivot_rust(
                        formula, max_pairs=pairs, growth_budget=growth,
                        beam_width=beam)
                    self.assertEqual(rs, py)
                    self.assertEqual(
                        satisfiable_brute(formula), satisfiable_brute(rs))
                checked += 1
        self.assertEqual(checked, 1200)

    def test_small_bounds_contradiction_and_tautological_resolvent(self):
        cases = (
            [[1], [-1]],
            [[1, 2], [-1, -2]],
            [[1, 2], [-1, 2]],
            [[1, 2], [-1, -2], [3]],
            [],
            [[]],
        )
        for source in cases:
            formula = CNFFormula.from_raw_clauses(source)
            for pairs in (0, 1, 8):
                self.assertEqual(
                    elimination_options_rust(formula, max_pairs=pairs),
                    elimination_options(formula, max_pairs=pairs))
                self.assertEqual(
                    two_ply_pivot_rust(formula, max_pairs=pairs),
                    two_ply_pivot(formula, max_pairs=pairs))
        formula = CNFFormula.from_raw_clauses([[1], [-1]])
        for params in (
            {"max_pairs": -1},
            {"growth_budget": -1},
            {"beam_width": 0},
            {"beam_width": 33},
        ):
            with self.subTest(params=params):
                with self.assertRaisesRegex(
                        ValueError, "invalid bounded lookahead budget"):
                    two_ply_pivot_rust(formula, **params)
                with self.assertRaisesRegex(
                        ValueError, "invalid bounded lookahead budget"):
                    two_ply_pivot(formula, **params)


if __name__ == "__main__":
    unittest.main()
