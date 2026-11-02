"""EQUI-satisfiability oracle for source-verified symmetry representative units."""
import unittest
from random import Random

from pysat.solvers import Minisat22
from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses

from scripts.experiment_flip_orbit_cdcl_gate import (
    benchmark, representative_units, solve_once, transformed_clauses,
)
from scripts.experiment_verified_flip_orbits import discover, make_case, satisfies


class SymmetryCDCLGateTests(unittest.TestCase):
    def test_gated_negative_control(self):
        formula = CNFFormula.from_raw_clauses([(1, 2, 3), (-1, 2, 4), (1, -3, 4)])
        info = discover(formula, require_source_rows=True)
        self.assertEqual(info["rank"], 0)
        self.assertEqual(info["candidate_span_tested"], 0)

    def test_randomized_equisatisfiability_and_original_witness(self):
        for seed in range(150):
            rng = Random(729500 + seed)
            n = rng.randrange(5, 11)
            clauses = []
            for _ in range(rng.randrange(1, 5)):
                support = rng.sample(range(1, n + 1), 3)
                clauses.extend(canonical_xor_cnf_clauses(support, rng.randrange(2)))
            for _ in range(rng.randrange(0, 7)):
                support = rng.sample(range(1, n + 1), 3)
                clauses.append(tuple(v if rng.randrange(2) else -v for v in support))
            f = CNFFormula.from_raw_clauses(clauses)
            info = discover(f, require_source_rows=True)
            augmented = transformed_clauses(f, info)
            with Minisat22(bootstrap_with=f.to_clause_lists()) as base:
                expected = base.solve()
            with Minisat22(bootstrap_with=augmented) as strengthened:
                actual = strengthened.solve()
                if actual:
                    model = strengthened.get_model()
                    assignment = sum(1 << (abs(l) - 1) for l in model if l > 0)
                    self.assertTrue(satisfies(f, assignment))
                    self.assertTrue(all(not (assignment & (1 << pivot))
                                        for pivot in info["pivots"]))
            self.assertEqual(actual, expected, seed)
            self.assertEqual(solve_once(f, "python_cdcl", quotient=True)["sat"], expected)

    def test_exhaustive_small_quotient_equisatisfiable(self):
        for n in (6, 8):
            for seed in range(8):
                for kind in ("xor_sat", "xor_unsat", "partially_broken", "random_3sat"):
                    f = make_case(n, seed, kind)
                    info = discover(f, require_source_rows=True)
                    units = representative_units(info["pivots"])
                    plain_models = []
                    representative_models = []
                    for x in range(1 << f.max_var):
                        if satisfies(f, x):
                            plain_models.append(x)
                            if all(not (x & (1 << (abs(c[0]) - 1))) for c in units):
                                representative_models.append(x)
                    self.assertEqual(bool(plain_models), bool(representative_models),
                                     (n, seed, kind))

    def test_benchmark_smoke(self):
        report = benchmark(seeds=1, repeats=1)
        self.assertEqual(report["summary"]["cases"], 15)
        self.assertTrue(report["summary"]["all_answers_match"])


if __name__ == "__main__":
    unittest.main()
