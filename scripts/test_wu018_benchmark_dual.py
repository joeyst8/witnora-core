"""The WU-018 reproducibility data parser rejects corrupted gate records."""

import unittest

from scripts.wu018_benchmark_dual import parse_dual_profile


class DualProfileParserTests(unittest.TestCase):
    def test_latest_complete_snapshot(self):
        text = ("WU018_DUAL stage=snapshot attempts=100 eligible=90 skipped=72 "
                "rebuilds=5 row_visits=50\n"
                "WU018_DUAL stage=end attempts=200 eligible=180 skipped=143 "
                "rebuilds=12 row_visits=110\n")
        d = parse_dual_profile(text)
        self.assertEqual(d["attempts"], 200)
        self.assertEqual(d["skipped"], 143)
        self.assertEqual(d["dual_stage"], "end")

    def test_missing_count_fails_closed(self):
        with self.assertRaises(ValueError):
            parse_dual_profile("WU018_DUAL stage=snapshot attempts=1 eligible=1 skipped=0")

    def test_absent_output_is_not_zero(self):
        self.assertIsNone(parse_dual_profile("other diagnostics"))


if __name__ == "__main__":
    unittest.main()
