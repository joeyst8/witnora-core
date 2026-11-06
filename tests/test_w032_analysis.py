"""The W032 analyzer must distinguish timeouts from actual answers."""

import unittest
from scripts.analyze_w032_external import analyze


class W032AnalysisTests(unittest.TestCase):
    def test_wrong_phase_rejected(self):
        with self.assertRaisesRegex(ValueError,"only W032"):
            analyze({"study":"W-CROSSDOMAIN-032","phase":"pilot_smoke"})

    def test_incomplete_original_cases_rejected(self):
        with self.assertRaisesRegex(ValueError,"frozen case"):
            analyze({"study":"W-CROSSDOMAIN-032","phase":"frozen_external_domain_pilot",
                     "case_count":8,"external_case_count":8})


if __name__ == "__main__":
    unittest.main()
