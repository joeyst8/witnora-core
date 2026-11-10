"""WU-019 wide-XNF source and measurement integrity regression tests."""

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from scripts.wu019_benchmark_wide import parse_xnf, profile, validates_model


class WideBenchmarkTests(unittest.TestCase):
    def test_wide_native_xnf_accepts_unit_and_binary_clauses(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "wide.xnf"
            path.write_text("p xnf 65 2\n-1+65 0\n-1+65 2+65 0\n")
            n, clauses = parse_xnf(path)
            self.assertEqual(n, 65)
            self.assertTrue(validates_model(n, clauses, [0] * n))
            assignment = [0] * n
            assignment[0] = 1
            self.assertFalse(validates_model(n, clauses, assignment))

    def test_corrupt_wide_snapshot_rejected(self):
        with self.assertRaises(ValueError):
            profile("WU018_DUAL stage=end attempts=2 skipped=2")

    def test_wide_snapshot_keeps_censored_counts(self):
        line = ("WU018_DUAL stage=snapshot attempts=100 eligible=90 skipped=77 "
                "rebuilds=9 row_visits=42 wide_eligible=90 wide_skipped=77 "
                "wide_rebuilds=9 wide_row_words=300")
        self.assertEqual(profile(line)["wide_skipped"], 77)
        self.assertEqual(profile(line)["profile_stage"], "snapshot")


if __name__ == "__main__":
    unittest.main()
