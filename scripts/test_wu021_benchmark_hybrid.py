"""WU-021 fails closed on missing selective-fallback accounting."""

import unittest

from scripts import wu019_benchmark_wide as pilot
from scripts.wu021_benchmark_hybrid import HYBRID_METRICS


class TestHybridProfiler(unittest.TestCase):
    def setUp(self):
        self.original = pilot.METRICS
        pilot.METRICS = (*self.original, *HYBRID_METRICS)

    def tearDown(self):
        pilot.METRICS = self.original

    def test_hybrid_counters_complete(self):
        values = {name: i+1 for i, name in enumerate(pilot.METRICS)}
        trace = "WU018_DUAL stage=snapshot " + " ".join(
            f"{key}={value}" for key, value in values.items())
        row = pilot.profile(trace)
        self.assertEqual(row["hybrid_seed_checks"], values["hybrid_seed_checks"])
        self.assertEqual(row["hybrid_seed_skips"], values["hybrid_seed_skips"])

    def test_missing_hybrid_stats_rejected(self):
        original = "WU018_DUAL stage=snapshot " + " ".join(
            f"{key}=0" for key in self.original)
        with self.assertRaises(ValueError):
            pilot.profile(original)


if __name__ == "__main__":
    unittest.main()
