"""Independent truth checks for matched-core parity ablations."""
import unittest
from random import Random

from pysat.solvers import Minisat22
from witnora_core.cnf import CNFFormula
from witnora_core.xor import canonical_xor_cnf_clauses

from scripts.experiment_cross_support_ablation import benchmark, timed_solve
from scripts.experiment_cross_support_propagation import extract_rows, derive_small_rows


class MatchedAblationTests(unittest.TestCase):
    def test_random_instances_match_oracle_all_modes(self):
        for seed in range(120):
            rng = Random(11191 + seed)
            clauses = []
            for _ in range(3):
                support = rng.sample(range(1, 9), 3)
                clauses.extend(canonical_xor_cnf_clauses(support, rng.randrange(2)))
            for _ in range(8):
                support = rng.sample(range(1, 9), 3)
                clauses.append(tuple(v if rng.randrange(2) else -v for v in support))
            f = CNFFormula.from_raw_clauses(clauses)
            with Minisat22(bootstrap_with=f.to_clause_lists()) as oracle:
                expected = oracle.solve()
            for mode in ("none", "source", "derived"):
                self.assertEqual(timed_solve(f, mode)["sat"], expected, (seed, mode))

    def test_derived_rows_are_logical_consequences(self):
        for seed in range(30):
            rng = Random(5521 + seed)
            clauses = []
            for _ in range(3):
                support = rng.sample(range(1, 7), 3)
                clauses.extend(canonical_xor_cnf_clauses(support, rng.randrange(2)))
            f = CNFFormula.from_raw_clauses(clauses)
            rows = derive_small_rows(extract_rows(f))
            for assignment in range(1 << 6):
                values = {v: bool(assignment & (1 << (v - 1))) for v in range(1, 7)}
                satisfies_cnf = all(any(values[abs(lit)] == (lit > 0)
                                        for lit in clause) for clause in f.to_clause_lists())
                if satisfies_cnf:
                    for mask, rhs in rows:
                        parity = sum(values[v] for v in range(1, 7)
                                     if mask & (1 << (v - 1))) % 2
                        self.assertEqual(parity, rhs)

    def test_smoke_and_node_reduction(self):
        result = benchmark(seeds=2, repeats=2)
        self.assertEqual(result["summary"]["cases"], 20)
        self.assertTrue(result["summary"]["all_answers_agree_minisat"])
        self.assertGreater(result["summary"]["derived_vs_source_node_wins"], 0)


if __name__ == "__main__":
    unittest.main()
