"""R-142: full bounded variable elimination proof text and cap differential."""
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.xor_drat import _variable_elimination_refutation


class XorVariableEliminationRefutationRustTests(unittest.TestCase):
    def test_seeded_proof_text_and_limits(self):
        rng = random.Random(142)
        for trial in range(155):
            clauses = []
            for _ in range(rng.randrange(0, 9)):
                width = rng.randrange(0, 5)
                support = rng.sample(range(1, 6), width)
                clauses.append([v if rng.randrange(2) else -v for v in support])
            formula = CNFFormula(clauses)
            support = set(clause.literals for clause in formula.clauses
                          if rng.randrange(2))
            if trial % 11 == 0:
                support.add((999,))
            order = rng.sample(range(1, 6), rng.randrange(0, 6))
            options = {"max_proof_clauses": rng.randrange(0, 30),
                       "max_proof_bytes": rng.randrange(0, 250),
                       "timeout_seconds": None}
            with self.subTest(trial=trial):
                self.assertEqual(_variable_elimination_refutation(
                    formula, support, order, **options, backend="rust"),
                    _variable_elimination_refutation(formula, support, order, **options))

    def test_simple_unsat_and_empty_source(self):
        formula = CNFFormula([[1], [-1]])
        self.assertEqual(_variable_elimination_refutation(formula,
                     {(1,), (-1,)}, [1], max_proof_clauses=3,
                     max_proof_bytes=10, timeout_seconds=None, backend="rust"),
                         _variable_elimination_refutation(formula,
                     {(1,), (-1,)}, [1], max_proof_clauses=3,
                     max_proof_bytes=10, timeout_seconds=None))
        empty = CNFFormula([[]])
        self.assertEqual(_variable_elimination_refutation(empty, {()}, [],
                     max_proof_clauses=0, max_proof_bytes=0,
                     timeout_seconds=None, backend="rust"),
                         _variable_elimination_refutation(empty, {()}, [],
                     max_proof_clauses=0, max_proof_bytes=0,
                     timeout_seconds=None))


if __name__ == "__main__":
    unittest.main()
