"""Smoke statistics must reject missing or incorrect source verdicts."""

import json
from pathlib import Path
import unittest

from scripts.analyze_w030_smoke import analyze


class SmokeAnalysisTests(unittest.TestCase):
    def test_archived_full_smoke_recomputes_identically(self):
        path = Path("research/results/w030_smoke_solver_measurements.json")
        if not path.exists():
            self.skipTest("full raw evidence only available after smoke archive")
        data = json.loads(path.read_text())
        expected = json.loads(Path("research/results/w030_smoke_analysis.json").read_text())
        self.assertEqual(analyze(data), expected)
        self.assertEqual(expected["timed_invocations"], 72)

    def test_wrong_phase_rejected(self):
        with self.assertRaisesRegex(ValueError, "W030 exploratory"):
            analyze({"study": "W-CROSSDOMAIN-030", "phase": "unfrozen"})


if __name__ == "__main__":
    unittest.main()
