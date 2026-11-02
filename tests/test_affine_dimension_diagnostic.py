"""Independent finite-oracle checks for affine-space diagnostic branches."""
import random
import unittest
from itertools import product

from scripts.experiment_affine_dimension_diagnostic import (
    disjoint_clause_branches, gf2_dimension, run, synthetic_instance,
)


def holds(rows, bits):
    return all((sum(bits[i] for i in range(len(bits)) if mask & (1 << i)) % 2)
               == rhs for mask, rhs in rows)


class AffineDimensionDiagnosticTests(unittest.TestCase):
    def test_dimension_counts_all_solutions(self):
        rng = random.Random(63123)
        for _ in range(220):
            nvars = rng.randrange(0, 8)
            rows = [(rng.randrange(1 << nvars), rng.randrange(2))
                    for _ in range(rng.randrange(0, 13))]
            dim = gf2_dimension(nvars, rows)
            count = sum(holds(rows, bits) for bits in product((0, 1), repeat=nvars))
            self.assertEqual(count, 0 if dim is None else 1 << dim)

    def test_clause_branches_are_disjoint_and_complete(self):
        rng = random.Random(63124)
        for _ in range(220):
            nvars = rng.randrange(1, 8)
            rows = [(rng.randrange(1 << nvars), rng.randrange(2))
                    for _ in range(rng.randrange(0, 8))]
            variables = rng.sample(range(1, nvars + 1), rng.randrange(1, nvars + 1))
            clause = [v if rng.randrange(2) else -v for v in variables]
            branches = disjoint_clause_branches(nvars, rows, clause)
            for bits in product((0, 1), repeat=nvars):
                hits = sum(holds(new_rows, bits) for new_rows, _ in branches)
                clause_true = any((lit > 0) == bool(bits[abs(lit) - 1])
                                  for lit in clause)
                self.assertEqual(hits, int(holds(rows, bits) and clause_true))

    def test_synthetic_generation_preserves_planted_satisfiability(self):
        for nvars in (16, 32):
            for seed in range(8):
                rows, clauses = synthetic_instance(nvars, seed)
                self.assertIsNotNone(gf2_dimension(nvars, rows))
                self.assertTrue(clauses)
        report = run(seeds=2)
        self.assertEqual(report["status"], "SYNTHETIC_DIAGNOSTIC_NOT_SATLIB_REPRODUCTION")
        self.assertEqual(len(report["records"]), 4)


if __name__ == "__main__":
    unittest.main()
