"""R-018 exact blocked clause elimination witnesses and proof digests."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.bce import blocked_clause_proof, find_first_blocked_clause


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustBce(unittest.TestCase):
    def test_1000_seeded_exact_first_witness_and_all_pivots(self):
        rng = random.Random(18182026)
        for n in range(1, 11):
            for _ in range(100):
                clauses = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(14))
                ]
                formula = CNFFormula(clauses)
                with self.subTest(n=n, source=clauses):
                    self.assertEqual(
                        find_first_blocked_clause(formula, backend="rust"),
                        find_first_blocked_clause(formula))
                    for clause in formula.clauses:
                        for pivot in clause.literals:
                            self.assertEqual(
                                blocked_clause_proof(formula, clause, pivot,
                                                     backend="rust"),
                                blocked_clause_proof(formula, clause, pivot))

    def test_structured_blocked_and_unblocked(self):
        for clauses in (
            [[1, 2], [-1, -2]],
            [[1, 2], [-1, 3]],
            [[1]], [[]], [],
        ):
            formula = CNFFormula(clauses)
            self.assertEqual(
                find_first_blocked_clause(formula, backend="rust"),
                find_first_blocked_clause(formula))

    def test_unknown_backend(self):
        with self.assertRaises(ValueError):
            find_first_blocked_clause(CNFFormula(), backend="not-rust")


if __name__ == "__main__":
    unittest.main()
