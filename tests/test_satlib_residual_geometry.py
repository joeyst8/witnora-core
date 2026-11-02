"""Offline checks for residual-geometry exploration and sound SCC equalities."""
import itertools
import unittest

from scripts.experiment_satlib_residual_geometry import (
    _minfill_upper_bound, benchmark, binary_scc_equalities,
    exact_bounded_width_count, residual_structure,
)
from witnora_core.xor import canonical_xor_cnf_clauses


def holds(clauses, bits):
    return all(any(bool(bits[abs(lit) - 1]) == (lit > 0) for lit in c)
               for c in clauses)


class ResidualGeometryTests(unittest.TestCase):
    def test_minfill_width_is_an_upper_bound(self):
        path = _minfill_upper_bound((1, 2, 3), ((1, 2), (2, 3)))
        triangle = _minfill_upper_bound((1, 2, 3), ((1, 2, 3),))
        self.assertEqual(path["minfill_upper_bound_width"], 1)
        self.assertEqual(triangle["minfill_upper_bound_width"], 2)

    def test_binary_scc_equalities_sound_under_exhaustive_assignments(self):
        for clauses in ([(-1, 2), (1, -2)], [(1, 2), (-1, -2)], [(1, 2)]):
            with self.subTest(clauses=clauses):
                equalities, _ = binary_scc_equalities(clauses)
                for bits in itertools.product((0, 1), repeat=2):
                    if holds(clauses, bits):
                        for mask, rhs in equalities:
                            self.assertEqual(((sum(bits[v] for v in range(2)
                                                    if mask & (1 << v))) % 2), rhs)

    def test_source_partition_and_component_sanity(self):
        clauses = sorted(canonical_xor_cnf_clauses((1, 2, 3), 1))
        clauses += [(4, 5)]
        report = residual_structure(clauses, 5)
        self.assertEqual(report["affine_free_dimension"], 4)
        self.assertEqual(report["source_residual_clauses"], 1)
        self.assertEqual(report["residual_component_sizes"], [2])
        self.assertTrue(report["residual_width_certificate_verified"])
        self.assertEqual(report["residual_exact_model_count"], "3")

    def test_exact_integer_model_count_matches_exhaustive_truth_table(self):
        cases = [([(1, 2), (-2, 3)], (1, 2, 3, 4)),
                 ([(1, -2), (2, -3), (1, 3)], (1, 2, 3)),
                 ([()], (1, 2)),
                 ([], (1, 2, 3))]
        for clauses, variables in cases:
            with self.subTest(clauses=clauses):
                order = _minfill_upper_bound(variables,
                                             [tuple(abs(x) for x in c) for c in clauses],
                                             include_order=True)["elimination_order"]
                actual, _ = exact_bounded_width_count(clauses, variables, order)
                expected = sum(holds(clauses, bits)
                               for bits in itertools.product((0, 1), repeat=len(variables)))
                self.assertEqual(actual, expected)
                if variables == tuple(range(1, len(variables) + 1)):
                    for parity in ((), (1,), variables[:2]):
                        signed, _ = exact_bounded_width_count(
                            clauses, variables, order, parity_variables=parity)
                        truth = sum(((-1) ** sum(bits[v - 1] for v in parity))
                                    for bits in itertools.product((0, 1), repeat=len(variables))
                                    if holds(clauses, bits))
                        self.assertEqual(signed, truth)

    def test_local_xor_factor_count_matches_bruteforce(self):
        clauses = [(1, 2), (2, -3), (-3, 4)]
        rows = [((1, 2, 3), 1), ((2, 4), 0)]
        support = [tuple(abs(x) for x in c) for c in clauses]
        support += [variables for variables, _ in rows]
        order = _minfill_upper_bound((1, 2, 3, 4), support,
                                     include_order=True)["elimination_order"]
        count, scope = exact_bounded_width_count(
            clauses, (1, 2, 3, 4), order, parity_equations=rows)
        expected = sum(holds(clauses, bits) and
                       all(sum(bits[v - 1] for v in vars_) % 2 == rhs for vars_, rhs in rows)
                       for bits in itertools.product((0, 1), repeat=4))
        self.assertEqual(count, expected)
        self.assertLessEqual(scope, 4)

    def test_holdout_is_locked_before_network(self):
        with self.assertRaises(ValueError):
            benchmark("par32-2-c.cnf.Z")


if __name__ == "__main__":
    unittest.main()
