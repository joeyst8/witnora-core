"""Fail-closed regression for source-bound same-support pair-screen redundancy."""
import unittest

from scripts.experiment_source_bound_pair_redundancy import (
    instance, run, source_bound_screen,
)


class SourceBoundPairRedundancyTests(unittest.TestCase):
    def test_source_bound_patterns_produce_no_independent_pair_conflict(self):
        for n in (8, 16, 32):
            for seed in range(8):
                for kind in ("xor_only", "blocked", "random"):
                    with self.subTest(n=n, seed=seed, kind=kind):
                        screen, rows = source_bound_screen(instance(n, seed, kind))
                        self.assertEqual(len(rows), 2)
                        self.assertEqual(screen["status"], "UNKNOWN")

    def test_smoke_benchmark_never_claims_screen_win(self):
        report = run(seeds=2, repeats=1)
        self.assertEqual(report["summary"]["cases"], 12)
        self.assertEqual(report["summary"]["source_bound_pair_conflicts"], 0)


if __name__ == "__main__":
    unittest.main()
