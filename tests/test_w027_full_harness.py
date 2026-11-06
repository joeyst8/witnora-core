"""Independent cheap preflight for full W027 frozen decoys/aggregation."""

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import unittest

from scripts.w027_full_decoys import SPECS, clauses_for_spec, dimacs_bytes, freeze_manifest
from scripts.benchmark_w027_full import ARMS, CAP_SECONDS, summarize


class W027FullPreflight(unittest.TestCase):
    def test_frozen_hashes_and_no_exact_tetrahedron(self):
        pinned = json.loads(Path("research/results/w027_full_decoy_manifest.json").read_text())
        self.assertEqual(freeze_manifest(), pinned)
        for spec, item in zip(SPECS, pinned["entries"]):
            clauses = clauses_for_spec(spec)
            with self.subTest(case=spec[0]):
                self.assertEqual(item["cnf_sha256"], hashlib.sha256(dimacs_bytes(clauses)).hexdigest())
                signed = defaultdict(set)
                for clause in clauses:
                    self.assertTrue(any(lit < 0 for lit in clause))  # all-false SAT model
                    key = tuple(sorted(map(abs, clause)))
                    mask = sum(1 << j for j, v in enumerate(key)
                               if next(lit for lit in clause if abs(lit) == v) < 0)
                    signed[key].add(mask)
                for signs in signed.values():
                    for parity in (0, 1):
                        self.assertFalse({c for c in range(8) if c.bit_count() % 2 == parity}.issubset(signs))

    def test_full_protocol_dimensions_and_censoring(self):
        self.assertEqual(CAP_SECONDS, 30)
        self.assertEqual(len(ARMS), 3)
        rows = []
        for case in ("solved", "censored"):
            for arm in ARMS:
                for repeat in range(3):
                    verdict = "TIMEOUT" if case == "censored" and arm != "kissat" else "SAT"
                    rows.append({"case_id": case, "stratum": "test", "arm": arm,
                                 "verdict": verdict, "repeat": repeat,
                                 "full_pipeline_wall_ns": 3_000_000 if arm == "kissat" else 2_000_000})
        medians, agg = summarize(rows, list(ARMS))
        self.assertEqual(len(medians), 6)
        self.assertEqual(agg[0]["paired_complete_cases"], 1)
        self.assertEqual(agg[0]["median_kissat_over_witnora_ratio"], 1.5)
        self.assertEqual(agg[0]["by_arm"]["witnora_plus_kissat"]["timeouts"], 3)
        self.assertEqual(agg[0]["by_arm"]["cryptominisat"]["timeouts"], 3)


if __name__ == "__main__":
    unittest.main()
