"""W031 analyzer rejects any unverified or censored seed."""

import unittest
from scripts.analyze_w031_order import analyze


class W031OrderAnalysisTests(unittest.TestCase):
    def test_unfrozen_report_rejected(self):
        with self.assertRaisesRegex(ValueError,"only frozen W031"):
            analyze({"study":"W-CROSSDOMAIN-031","phase":"exploratory"})

    def test_missing_cases_rejected(self):
        with self.assertRaisesRegex(ValueError,"case count incomplete"):
            analyze({"study":"W-CROSSDOMAIN-031","phase":"preregistered_order_robustness",
                     "case_count":1,"rows":[]})


if __name__ == "__main__":
    unittest.main()
