"""Adversarial tests for invariant discovery: never promote unchecked claims."""
from itertools import product
import random
import unittest

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.spoke_collapse import make_spoke_family
from witnora_core.spoke_discovery import discover_parity_spoke_conflicts


def brute_sat(formula):
    variables = sorted(formula.variables)
    return any(formula_satisfied(formula, dict(zip(variables, values)))
               for values in product((False, True), repeat=len(variables)))


class ParitySpokeDiscoveryTest(unittest.TestCase):
    def test_detects_without_supplied_spoke_annotations(self):
        formula, _ = make_spoke_family(5, contradictory=True)
        found = discover_parity_spoke_conflicts(formula)
        self.assertTrue(found)
        self.assertTrue(any(c["endpoints"] == [1, 2] for c in found))
        self.assertTrue(all(c["formal_status"] == "NOT_LEAN_VERIFIED" for c in found))
        self.assertFalse(brute_sat(formula))

    def test_missing_clause_cannot_be_used_as_equation(self):
        formula, _ = make_spoke_family(2, contradictory=True)
        all_clauses = formula.to_clause_lists()
        for idx in range(len(all_clauses)):
            weakened = CNFFormula.from_raw_clauses(
                c for j, c in enumerate(all_clauses) if j != idx)
            self.assertFalse(discover_parity_spoke_conflicts(weakened))
            self.assertTrue(brute_sat(weakened))

    def test_extra_clauses_do_not_invalidate_implied_equations(self):
        formula, _ = make_spoke_family(2, contradictory=True)
        with_decoy = CNFFormula.from_raw_clauses(
            formula.to_clause_lists() + [[50, -51], [-50, 51]])
        found = discover_parity_spoke_conflicts(with_decoy)
        self.assertTrue(found)
        self.assertFalse(brute_sat(formula))

    def test_randomized_sat_formulas_produce_no_false_conflicts(self):
        rng = random.Random(7831)
        for _ in range(100):
            # Every generated clause is satisfied by a designated model.
            bits = {i: bool(rng.randrange(2)) for i in range(1, 7)}
            clauses = []
            for _ in range(15):
                u, v = rng.sample(range(1, 7), 2)
                clause = [u if rng.randrange(2) else -u,
                          v if rng.randrange(2) else -v]
                if not any((bits[abs(lit)] if lit > 0 else not bits[abs(lit)])
                           for lit in clause):
                    clause[0] = -clause[0]
                clauses.append(clause)
            formula = CNFFormula.from_raw_clauses(clauses)
            self.assertTrue(formula_satisfied(formula, bits))
            self.assertFalse(discover_parity_spoke_conflicts(formula))

    def test_no_unchecked_promotion(self):
        formula, _ = make_spoke_family(3, contradictory=True)
        for candidate in discover_parity_spoke_conflicts(formula):
            self.assertNotIn("verified", candidate)
            self.assertEqual(candidate["status"], "UNVERIFIED_STRUCTURAL_CANDIDATE")


if __name__ == "__main__":
    unittest.main()
