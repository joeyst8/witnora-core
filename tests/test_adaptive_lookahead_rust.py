"""R-043 native adaptive bounded lookahead, Python parity and SAT controls."""
from __future__ import annotations

import os
import random
import unittest
from itertools import product

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.adaptive_lookahead_prototype import adaptive_pivot, adaptive_pivot_rust


def brute_sat(formula):
    return any(
        formula_satisfied(formula, dict(zip(formula.variables, bits)))
        for bits in product((False, True), repeat=formula.num_vars)
    )


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestNativeAdaptiveLookahead(unittest.TestCase):
    def test_960_randomized_full_details_and_sat_parity(self):
        rng = random.Random(43112026)
        checked = 0
        for n in range(1, 9):
            for case in range(120):
                source = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(14))
                ]
                formula = CNFFormula.from_raw_clauses(source)
                budgets = {
                    "max_pairs": rng.choice((0, 1, 3, 6, 12)),
                    "growth_budget": rng.choice((0, 1, 2, 4)),
                    "beam_width": rng.randrange(1, 9),
                    "expansion_budget": rng.randrange(1, 18),
                    "max_depth": rng.choice((2, 3)),
                    "ambiguity_margin": rng.choice((0.0, 0.2, 1.0, 2.0, 8.0)),
                }
                with self.subTest(n=n, case=case, budgets=budgets):
                    py, py_meta = adaptive_pivot(formula, **budgets)
                    rs, rs_meta = adaptive_pivot_rust(formula, **budgets)
                    self.assertEqual(rs, py)
                    self.assertEqual(rs_meta, py_meta)
                    self.assertEqual(brute_sat(rs), brute_sat(formula))
                checked += 1
        self.assertEqual(checked, 960)

    def test_error_bounds_and_contradictory_source(self):
        cases = (
            {"max_pairs": -1},
            {"growth_budget": -1},
            {"beam_width": 0},
            {"beam_width": 33},
            {"expansion_budget": 0},
            {"expansion_budget": 1001},
            {"max_depth": 1},
            {"max_depth": 4},
            {"ambiguity_margin": -0.1},
        )
        formula = CNFFormula.from_raw_clauses([[1], [-1]])
        for budgets in cases:
            with self.subTest(budgets=budgets):
                for function in (adaptive_pivot, adaptive_pivot_rust):
                    with self.assertRaisesRegex(
                            ValueError, "invalid adaptive lookahead budget"):
                        function(formula, **budgets)
        for source in ([], [[]], [[1], [-1]], [[1, 2], [-1, 3]]):
            formula = CNFFormula.from_raw_clauses(source)
            self.assertEqual(adaptive_pivot_rust(formula), adaptive_pivot(formula))


if __name__ == "__main__":
    unittest.main()
