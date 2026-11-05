"""W-CRC-003 Ganak model-count baseline and adversarial cap controls."""
from __future__ import annotations

import itertools
import unittest

from scripts.benchmark_crc_highcount import independent_ganak, run_case
from scripts.benchmark_crc_scaling import overlapping_parity_source


def brute_count(source, nvars):
    return sum(
        all(any(assignment[abs(lit) - 1] == (lit > 0)
                for lit in clause) for clause in source)
        for assignment in itertools.product((False, True), repeat=nvars)
    )


class TestCRCHighCountBenchmark(unittest.TestCase):
    def test_ganak_counts_free_variables(self):
        got = independent_ganak(((1, 2),), 5, seconds=4)
        self.assertEqual(got["status"], "EXACT")
        self.assertEqual(got["models"], 24)

    def test_ganak_unsat_and_large_count(self):
        unsat = independent_ganak(((1,), (-1,)), 1, seconds=4)
        self.assertEqual(unsat["status"], "EXACT")
        self.assertEqual(unsat["models"], 0)
        large = independent_ganak((), 30, seconds=4)
        self.assertEqual(large["status"], "EXACT")
        self.assertEqual(large["models"], 1 << 30)

    def test_mixed_source_independent_exact(self):
        source, nvars, nonlinear = overlapping_parity_source(
            5, 8900, ratio=1.6,
        )
        independent = independent_ganak(source, nvars, seconds=4)
        self.assertEqual(independent["status"], "EXACT")
        self.assertEqual(independent["models"], brute_count(source, nvars))
        row = run_case(
            "unit_small", source, nvars, nonlinear, tuple(range(1, 6)),
            8900, repeats=1, seconds=4, max_states=10000, max_models=100,
        )
        self.assertEqual(row["crc_shannon"]["status"], "EXACT")
        self.assertEqual(
            row["crc_shannon"]["models"], row["external_ganak_counter"]["models"],
        )

    def test_timeout_budget_validation(self):
        with self.assertRaises(ValueError):
            independent_ganak((), 1, seconds=0)


if __name__ == "__main__":
    unittest.main()
