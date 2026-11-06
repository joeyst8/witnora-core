"""Frozen eight-case W030 smoke manifest and negative-control checks."""

import json
from pathlib import Path
import unittest

from scripts.w030_smoke_cases import cases, manifest


class W030SmokeHarnessTests(unittest.TestCase):
    def test_manifest_is_exactly_frozen(self):
        source = json.loads(Path("research/results/w030_smoke_case_manifest.json").read_text())
        self.assertEqual(manifest(), source)
        self.assertEqual(len(source["entries"]), 8)
        self.assertEqual(sum(e["expected"] == "UNSAT" for e in source["entries"]), 3)

    def test_reordering_does_not_change_clause_multiset(self):
        all_cases = cases()
        first = next(x for x in all_cases if x["case_id"] == "w030_d8192_r0_unsat_corefirst")
        last = next(x for x in all_cases if x["case_id"] == "w030_d8192_r0_unsat_corelast")
        self.assertEqual(sorted(map(tuple, first["clauses"])), sorted(map(tuple, last["clauses"])))

    def test_planted_decoys_are_sat_under_all_false_assignment(self):
        for case in cases():
            if case["stratum"] == "near_xor_decoy":
                self.assertTrue(all(any(lit < 0 for lit in clause) for clause in case["clauses"]))


if __name__ == "__main__":
    unittest.main()
