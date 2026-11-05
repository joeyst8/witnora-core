"""Independent bounded checks for the experimental spoke-collapse operator."""
from itertools import product
import random
import unittest

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.spoke_collapse import (
    ParitySpoke, collapse_spokes, make_spoke_family, spoke_cnf,
)


def brute_sat(formula):
    variables = sorted(formula.variables)
    return any(formula_satisfied(formula, dict(zip(variables, bits)))
               for bits in product((False, True), repeat=len(variables)))


class SpokeCollapseTest(unittest.TestCase):
    def test_infinite_family_finite_oracle_samples(self):
        for n in range(2, 8):
            for contradictory in (False, True):
                with self.subTest(n=n, contradictory=contradictory):
                    formula, spokes = make_spoke_family(n, contradictory=contradictory)
                    verdict = collapse_spokes(formula, spokes)
                    self.assertEqual(brute_sat(formula), not contradictory)
                    if contradictory:
                        self.assertEqual(verdict["status"], "UNSAT_BY_SPOKE_SYNDROME")
                        self.assertNotEqual(*verdict["syndromes"])
                    else:
                        self.assertEqual(verdict["status"], "SAT_WITH_WITNESS")
                        self.assertTrue(formula_satisfied(formula, verdict["assignment"]))

    def test_random_spokes_against_independent_oracle(self):
        rng = random.Random(0x5147)
        for _ in range(70):
            n = rng.randint(2, 6)
            spokes = tuple(ParitySpoke(i + 3, rng.randrange(2), rng.randrange(2))
                           for i in range(n))
            formula = spoke_cnf(spokes)
            verdict = collapse_spokes(formula, spokes)
            sat = brute_sat(formula)
            self.assertEqual(sat, verdict["status"] == "SAT_WITH_WITNESS")
            if sat:
                self.assertTrue(formula_satisfied(formula, verdict["assignment"]))

    def test_rejects_nonexact_cnf_and_duplicate_intermediates(self):
        formula, spokes = make_spoke_family(3, contradictory=True)
        altered = CNFFormula.from_raw_clauses(formula.to_clause_lists() + [[10]])
        self.assertEqual(collapse_spokes(altered, spokes)["status"], "UNSUPPORTED")
        duplicate = (spokes[0], spokes[0])
        self.assertEqual(collapse_spokes(formula, duplicate)["status"], "UNSUPPORTED")

    def test_large_family_reduces_without_model_enumeration(self):
        formula, spokes = make_spoke_family(500, contradictory=True)
        result = collapse_spokes(formula, spokes)
        self.assertEqual(result["status"], "UNSAT_BY_SPOKE_SYNDROME")
        self.assertEqual(formula.num_clauses, 2000)


if __name__ == "__main__":
    unittest.main()
