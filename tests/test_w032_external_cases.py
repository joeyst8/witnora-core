"""W032 source list and claim-scope controls, no network required."""

import json
from pathlib import Path
import unittest

from scripts.w032_external_cases import manifest


class W032ExternalCasesTests(unittest.TestCase):
    def test_manifest_exact_and_labels_locked(self):
        frozen = json.loads(Path("research/results/w032_case_manifest.json").read_text())
        self.assertEqual(manifest(), frozen)
        entries = frozen["entries"]
        self.assertEqual(len(entries), 14)
        self.assertEqual(sum(e["stratum"] == "official_external_vlsat2" for e in entries), 8)
        self.assertEqual(sum(e["stratum"] == "frozen_adversarial_sat_decoy" for e in entries), 4)
        self.assertEqual(sum(e["stratum"] == "synthetic_sanity_only" for e in entries), 2)
        self.assertEqual(sum(e["expected"] == "SAT" for e in entries), 7)
        self.assertEqual(sum(e["expected"] == "UNSAT" for e in entries), 7)


if __name__ == "__main__":
    unittest.main()
