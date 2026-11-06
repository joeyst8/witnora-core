"""W031 source freezing, permutation equality, and label-blind controls."""

import json
from pathlib import Path
import unittest

from scripts.w031_order_cases import ORDERS, REPLICATES, NOISE, cases, manifest, permutation


class W031OrderCasesTests(unittest.TestCase):
    def test_manifest_byte_exact(self):
        frozen = json.loads(Path("research/results/w031_order_case_manifest.json").read_text())
        self.assertEqual(manifest(), frozen)
        self.assertEqual(len(frozen["entries"]), 16 * 3 * 2 + 4)

    def test_truth_pair_shares_positions_and_multiset(self):
        prepared = cases()
        lookup = {c["case_id"]: c for c in prepared}
        for replicate in range(REPLICATES):
            for order in ORDERS:
                stem = f"w031_d{NOISE}_r{replicate}_"
                a = lookup[stem + "sat_" + order]
                b = lookup[stem + "unsat_" + order]
                self.assertEqual(a["first_core_position_zero_based"], b["first_core_position_zero_based"])
                self.assertEqual(a["last_core_position_zero_based"], b["last_core_position_zero_based"])
                self.assertEqual(len(a["clauses"]), NOISE + 20)
                self.assertEqual(len(b["clauses"]), NOISE + 20)
                if order == "corefirst":
                    self.assertEqual(sorted(map(tuple, a["clauses"][20:])),
                                     sorted(map(tuple, b["clauses"][20:])))

    def test_permutations_preserve_full_source_indices(self):
        for replicate in range(REPLICATES):
            for order in ORDERS:
                perm = permutation(replicate, order)
                self.assertEqual(sorted(perm), list(range(NOISE + 20)))
                if order == "corefirst":
                    self.assertEqual(perm[:20], list(range(20)))
                elif order == "corelast":
                    self.assertEqual(perm[-20:], list(range(20)))

    def test_sat_decoys_preserve_planted_model(self):
        self.assertEqual(sum(c["stratum"] == "adversarial_sat_decoy" for c in cases()), 4)
        for case in cases():
            if case["stratum"] == "adversarial_sat_decoy":
                self.assertTrue(all(any(lit < 0 for lit in row) for row in case["clauses"]))


if __name__ == "__main__":
    unittest.main()
