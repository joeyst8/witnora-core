"""R-301–R-320: shortest inconsistent GF(2) subsystem, bounded and exact."""

from __future__ import annotations

import os
import unittest

from scripts.benchmark_xor_syndrome_frontier import (
    evaluate_hypergraph, exhaustive_inconsistent_subset,
    parity_hypergraph, shortest_inconsistent_subset,
)
from scripts.benchmark_xor_frontier import exhaustive_sat
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor import XorEquation


def eq(variables, rhs):
    return XorEquation(variables, rhs)


class XorSyndromeResearchTests(unittest.TestCase):
    def test_r301_empty_system_has_no_contradiction(self):
        self.assertEqual(shortest_inconsistent_subset([])[0], None)

    def test_r302_consistent_unary_system(self):
        rows = [eq([1], 0), eq([2], 1)]
        self.assertIsNone(shortest_inconsistent_subset(rows)[0])

    def test_r303_opposite_unary_pair_is_two_row_witness(self):
        rows = [eq([1], 0), eq([1], 1)]
        self.assertEqual(shortest_inconsistent_subset(rows)[0], (0, 1))

    def test_r304_mixed_ternary_chain_requires_three_rows(self):
        rows = [eq([1, 2, 3], 0), eq([3, 4], 0), eq([1, 2, 4], 1)]
        self.assertEqual(shortest_inconsistent_subset(rows)[0], (0, 1, 2))

    def test_r305_mixed_four_variable_dependency(self):
        rows = [eq([1, 2, 3, 4], 0), eq([3, 4, 5], 0), eq([1, 2, 5], 1)]
        self.assertEqual(shortest_inconsistent_subset(rows)[0], (0, 1, 2))

    def test_r306_independent_combinations_oracle(self):
        for seed in range(306000, 306064):
            try:
                _, rows = parity_hypergraph(seed)
            except ValueError:
                continue
            self.assertEqual(shortest_inconsistent_subset(rows)[0],
                             exhaustive_inconsistent_subset(rows))

    def test_r307_deterministic_lexicographic_tie(self):
        rows = [eq([1], 0), eq([1], 1), eq([2], 0), eq([2], 1)]
        self.assertEqual(shortest_inconsistent_subset(rows)[0], (0, 1))

    def test_r308_sparse_variable_relabel_invariant(self):
        rows = [eq([1, 2, 3], 0), eq([3, 4], 0), eq([1, 2, 4], 1)]
        renamed = [eq([v * 1001 for v in row.variables], row.rhs) for row in rows]
        self.assertEqual(shortest_inconsistent_subset(rows)[0],
                         shortest_inconsistent_subset(renamed)[0])

    def test_r309_row_permutation_preserves_optimal_witness_size(self):
        rows = [eq([1], 0), eq([1, 2], 0), eq([2], 1), eq([3], 0)]
        first, _ = shortest_inconsistent_subset(rows)
        reverse, _ = shortest_inconsistent_subset(list(reversed(rows)))
        self.assertEqual(len(first), len(reverse))

    def test_r310_syndrome_state_cap_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "state cap"):
            shortest_inconsistent_subset([eq([1], 0)], max_states=1)

    def test_r311_variable_cap_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "variable cap"):
            shortest_inconsistent_subset([eq(range(1, 18), 0)])

    def test_r312_row_cap_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "row cap"):
            shortest_inconsistent_subset([eq([1], 0)] * 4, max_rows=3)

    def test_r313_exhaustive_oracle_row_cap_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "row cap"):
            exhaustive_inconsistent_subset([eq([1], 0)] * 17)

    def test_r314_independent_rows_explore_eight_states(self):
        witness, stats = shortest_inconsistent_subset([eq([1], 0), eq([2], 0), eq([3], 0)])
        self.assertIsNone(witness)
        self.assertEqual(stats["reachable_states"], 8)

    def test_r315_consistent_duplicate_does_not_double_state_space(self):
        _, stats = shortest_inconsistent_subset([eq([1], 0), eq([1], 0)])
        self.assertEqual(stats["reachable_states"], 2)

    def test_r316_inconsistent_duplicate_exposes_parity_dimension(self):
        witness, stats = shortest_inconsistent_subset([eq([1], 0), eq([1], 1)])
        self.assertEqual(witness, (0, 1))
        self.assertEqual(stats["reachable_states"], 4)

    def test_r317_consistent_planted_hypergraph_sat_control(self):
        formula, rows = parity_hypergraph(317, contradictory=False)
        self.assertTrue(exhaustive_sat(formula))
        self.assertIsNone(shortest_inconsistent_subset(rows)[0])

    def test_r318_contradictory_hypergraph_original_cnf_unsat(self):
        formula, rows = parity_hypergraph(318, contradictory=True)
        self.assertFalse(exhaustive_sat(formula))
        self.assertIsNotNone(shortest_inconsistent_subset(rows)[0])

    def test_r319_python_proof_candidate_original_cnf_rup(self):
        for seed in range(319000, 319016):
            self.assertGreater(evaluate_hypergraph(seed)["proof_clauses"], 0)

    def test_r320_syndrome_experimental_status_without_external_claim(self):
        result = evaluate_hypergraph(320)
        self.assertFalse(result["external_drat_verified"])
        self.assertFalse(result["native_differential"])


@unittest.skipUnless(find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
                     "external drat-trim unavailable")
class XorSyndromeExternalTests(unittest.TestCase):
    def test_r301_r320_externally_accepted_hypergraph_proofs(self):
        checker = find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))
        self.assertTrue(all(evaluate_hypergraph(seed,
            external_checker=checker)["external_drat_verified"]
            for seed in range(301000, 301024)))


class XorSyndromeNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("native extension absent; focused CI checks Rust")

    def test_r301_r320_hypergraph_rust_differential(self):
        for seed in range(301000, 301024):
            self.assertTrue(evaluate_hypergraph(seed, compare_rust=True)["native_differential"])


if __name__ == "__main__":
    unittest.main()
