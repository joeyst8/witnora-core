"""Deterministic differential and adversarial tests of G5 and G14 internals.

No proof of arbitrary Python execution: finite randomized coverage plus
independent Glucose3 SAT decisions and exhaustive branch evaluations.
"""
from __future__ import annotations

from itertools import product
from random import Random
import unittest

from pysat.solvers import Solver

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.operator_genesis import gaussian_eliminate_gf2
from witnora_core.separator_affine_family_theorem import (
    _all_assignments,
    _component_dicts,
    _condition_by_separator,
)
from witnora_core.xor import canonical_xor_cnf_clauses


def sat_by_glucose(clauses):
    with Solver(name="glucose3", bootstrap_with=clauses) as solver:
        return solver.solve()


def all_assignments(variables):
    return (dict(zip(variables, values))
            for values in product((False, True), repeat=len(variables)))


class DifferentialTest(unittest.TestCase):
    def test_g5_random_affine_systems_against_glucose3(self):
        rng = Random(20261029)
        count = 0
        for _ in range(240):
            n = rng.randrange(1, 11)
            rows = []
            clauses = []
            for _ in range(rng.randrange(0, 13)):
                arity = rng.randrange(1, min(n, 5) + 1)
                variables = sorted(rng.sample(range(1, n + 1), arity))
                parity = rng.randrange(2)
                rows.append({"variables": variables, "parity_bit": parity})
                clauses.extend(canonical_xor_cnf_clauses(variables, parity))
            result = gaussian_eliminate_gf2(rows)
            oracle_sat = sat_by_glucose(clauses)
            self.assertIn(result["status"], ("SAT", "UNSAT"))
            self.assertEqual(result["status"] == "SAT", oracle_sat,
                             f"disagreement on rows {rows}")
            count += 1
        print(f"G5_GLUCOSE3_RANDOM_AGREEMENT: {count}")

    def test_g5_adversarial_cancellation_and_contradiction(self):
        for variables in ([1], [1, 2], [1, 2, 3, 4, 5]):
            for parity in (0, 1):
                rows = [{"variables": variables, "parity_bit": parity}] * 3
                sat = gaussian_eliminate_gf2(rows)
                self.assertEqual(sat["status"], "SAT")
                contradicted = rows + [
                    {"variables": variables, "parity_bit": 1 - parity}
                ]
                unsat = gaussian_eliminate_gf2(contradicted)
                self.assertEqual(unsat["status"], "UNSAT")

    def test_g14_random_conditioning_exactness(self):
        rng = Random(6302026)
        tested = 0
        for _ in range(120):
            n = rng.randrange(2, 8)
            formula = CNFFormula.from_raw_clauses([
                [rng.choice((-1, 1)) * v
                 for v in rng.sample(range(1, n + 1), rng.randrange(1, min(n, 4) + 1))]
                for _ in range(rng.randrange(1, 14))
            ])
            separator = sorted(rng.sample(range(1, n + 1), rng.randrange(1, min(n, 3) + 1)))
            components = _component_dicts(formula, separator)
            for fixed in _all_assignments(separator):
                residual, parts, errors = _condition_by_separator(formula, fixed, components)
                for free in all_assignments(sorted(set(formula.variables) - set(fixed))):
                    assignment = {**free, **fixed}
                    original = formula_satisfied(formula, assignment)
                    reduced = formula_satisfied(residual, free)
                    self.assertEqual(original, reduced,
                                     f"conditioning mismatch: {formula.to_clause_lists()}, {fixed}")
                    if not errors:
                        composed = all(formula_satisfied(part, free)
                                       for part in parts.values())
                        self.assertEqual(reduced, composed,
                                         f"component mismatch: {formula.to_clause_lists()}, {fixed}")
                    tested += 1
        print(f"G14_RANDOM_ASSIGNMENT_AGREEMENT: {tested}")


if __name__ == "__main__":
    unittest.main()
