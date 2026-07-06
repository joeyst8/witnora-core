import unittest

from witnora_core.hierarchy_formalization import gap_analysis_records


class GapAnalysisTest(unittest.TestCase):
    def test_gap_analysis(self):
        records = gap_analysis_records()
        gaps = {row.gap for row in records}
        self.assertIn("random 3-SAT", gaps)
        self.assertIn("general circuit-SAT", gaps)
        self.assertIn("arbitrary PB encodings", gaps)
        self.assertIn("realistic SAT competition formulas", gaps)
        self.assertTrue(all(row.v2_9_recommendation for row in records))
        print("GAP_ANALYSIS_PASS")


if __name__ == "__main__":
    unittest.main()

