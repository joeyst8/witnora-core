"""Zero-variable XOR encoding must distinguish tautology from contradiction."""
import unittest
from itertools import product
from random import Random

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.xor import XorEquation, canonical_xor_cnf_clauses


class EmptyXorEncodingTest(unittest.TestCase):
    def test_seeded_noncontiguous_and_repeated_variable_encodings(self):
        rng = Random(20261029)
        pool = [1, 3, 5, 8, 11]
        for _ in range(180):
            variables = [rng.choice(pool) for _ in range(rng.randrange(0, 11))]
            rhs = rng.randrange(2)
            formula = CNFFormula.from_raw_clauses(
                canonical_xor_cnf_clauses(variables, rhs)
            )
            for values in product((False, True), repeat=len(pool)):
                assignment = dict(zip(pool, values))
                xor_true = (sum(bool(assignment[v]) for v in variables) % 2) == rhs
                self.assertEqual(
                    formula_satisfied(formula, assignment), xor_true,
                    f"raw_vars={variables} rhs={rhs} assignment={assignment}",
                )

    def test_empty_even_equation_is_tautology(self):
        self.assertEqual(canonical_xor_cnf_clauses([], 0), set())
        self.assertEqual(CNFFormula.from_raw_clauses(
            canonical_xor_cnf_clauses([], 0)).num_clauses, 0)
        self.assertTrue(XorEquation([], 0).is_tautology)

    def test_repeated_xor_variables_cancel_mod_two(self):
        self.assertEqual(canonical_xor_cnf_clauses([1, 1], 0), set())
        self.assertEqual(canonical_xor_cnf_clauses([1, 1], 1), {()})
        self.assertEqual(canonical_xor_cnf_clauses([1, 1, 2], 1), {(2,)})
        self.assertEqual(canonical_xor_cnf_clauses([1, 2, 1], 0), {(-2,)})

    def test_empty_odd_equation_is_contradiction(self):
        self.assertEqual(canonical_xor_cnf_clauses([], 1), {()})
        formula = CNFFormula.from_raw_clauses(canonical_xor_cnf_clauses([], 1))
        self.assertTrue(formula.contains_empty_clause)
        self.assertTrue(XorEquation([], 1).is_contradiction)


if __name__ == "__main__":
    unittest.main()
