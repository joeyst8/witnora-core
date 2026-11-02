"""Offline exactness checks for affine quotient, including both pivot orders."""
import itertools
import unittest

from pysat.solvers import Minisat22

from scripts.experiment_satlib_affine_quotient import project_source, rename_source
from witnora_core.xor import canonical_xor_cnf_clauses


def holds(clauses, bits):
    return all(any(bool(bits[abs(lit) - 1]) == (lit > 0) for lit in c)
               for c in clauses)


class AffineQuotientTests(unittest.TestCase):
    def test_sat_assignment_bijection_on_complete_xor_encodings(self):
        clauses = sorted(canonical_xor_cnf_clauses((1, 2, 3), 1))
        clauses += sorted(canonical_xor_cnf_clauses((3, 4, 5), 0))
        clauses += [(1, 4), (-2, -5), (2, -4, 5)]
        expected = sum(holds(clauses, x) for x in itertools.product((0, 1), repeat=5))
        for order in ("natural", "residual_first", "reverse"):
            with self.subTest(order=order):
                quotient, decode, info = project_source(clauses, 5, order=order)
                self.assertEqual(info["free_dimension"], 3)
                self.assertEqual(info["independent_xor_rank"], 2)
                count = 0
                with Minisat22(bootstrap_with=quotient) as solver:
                    for bits in itertools.product((False, True), repeat=3):
                        assumptions = [i + 1 if b else -(i + 1) for i, b in enumerate(bits)]
                        if solver.solve(assumptions=assumptions):
                            model = decode(solver.get_model())
                            self.assertTrue(all(any(model[abs(lit)] == (lit > 0)
                                                    for lit in clause) for clause in clauses))
                            count += 1
                self.assertEqual(count, expected)

    def test_no_xor_equations_keeps_exact_satisfiability(self):
        clauses = [(1, -2), (-1, 3), (2, -3)]
        expected = sum(holds(clauses, x) for x in itertools.product((0, 1), repeat=3))
        quotient, _, info = project_source(clauses, 3, order="residual_first")
        self.assertEqual(info["free_dimension"], 3)
        count = sum(holds(quotient, x) for x in itertools.product((0, 1), repeat=3))
        self.assertEqual(count, expected)

    def test_rejects_unsupported_pivot_order(self):
        with self.assertRaises(ValueError):
            project_source([(1,)], 1, order="invalid")

    def test_numbering_controls_are_strict_bijections(self):
        clauses = [(1, -2), (2, 3), (-4, 1, 3)]
        for mode in ("reverse", "random_1729"):
            renamed, perm = rename_source(clauses, 4, mode)
            self.assertEqual(sorted(perm), [1, 2, 3, 4])
            self.assertEqual([len(c) for c in renamed], [len(c) for c in clauses])
            for bits in itertools.product((0, 1), repeat=4):
                remapped_bits = [0] * 4
                for old_id, new_id in enumerate(perm):
                    remapped_bits[new_id - 1] = bits[old_id]
                self.assertEqual(holds(clauses, bits), holds(renamed, remapped_bits))


if __name__ == "__main__":
    unittest.main()
