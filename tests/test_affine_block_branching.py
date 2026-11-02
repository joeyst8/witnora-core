"""Independent finite-oracle controls for two-clause affine branching."""
import random
import unittest
from itertools import product

from scripts.experiment_affine_block_branching import (
    measure_candidate, run, two_clause_branches,
)
from scripts.experiment_affine_dimension_diagnostic import (
    disjoint_clause_branches,
)


def holds(rows, bits):
    return all(sum(bits[v] for v in range(len(bits)) if mask & (1 << v)) % 2
               == rhs for mask, rhs in rows)


def clause_true(clause, bits):
    return any((lit > 0) == bool(bits[abs(lit) - 1]) for lit in clause)


class AffineBlockBranchingTests(unittest.TestCase):
    def test_two_clause_branches_are_disjoint_and_complete(self):
        rng = random.Random(63125)
        for _ in range(220):
            nvars = rng.randrange(1, 8)
            rows = [(rng.randrange(1 << nvars), rng.randrange(2))
                    for _ in range(rng.randrange(0, 8))]
            variables = list(range(1, nvars + 1))
            clauses = []
            for _ in range(2):
                vs = rng.sample(variables, rng.randrange(1, nvars + 1))
                clauses.append([v if rng.randrange(2) else -v for v in vs])
            branches = two_clause_branches(nvars, rows, *clauses)
            for bits in product((0, 1), repeat=nvars):
                hits = sum(holds(new_rows, bits) for new_rows, _ in branches)
                expected = int(holds(rows, bits) and all(
                    clause_true(clause, bits) for clause in clauses))
                self.assertEqual(hits, expected)

    def test_pair_operator_reduces_or_preserves_model_count(self):
        rows = ((0b0011, 0), (0b1100, 1))
        clauses = ((1, 2), (-1, 3), (2, -4), (1, -3))
        single = measure_candidate(4, rows, clauses)
        paired = measure_candidate(4, rows, clauses, pair=True)
        self.assertIsNotNone(single)
        self.assertIsNotNone(paired)
        self.assertLessEqual(paired["surviving_models"], single["surviving_models"])

    def test_report_is_explicitly_synthetic(self):
        report = run(seeds=2, repeats=2)
        self.assertEqual(report["status"], "SYNTHETIC_OPERATOR_COST_TEST_NOT_SATLIB")
        self.assertEqual(len(report["records"]), 4)


if __name__ == "__main__":
    unittest.main()
