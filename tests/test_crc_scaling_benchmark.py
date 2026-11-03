"""W-CRC-002 benchmark harness correctness and failure-label controls."""
from __future__ import annotations

import itertools
import unittest

from scripts.benchmark_crc_scaling import (
    benchmark_case, independent_pysat, interaction_density,
    measured, overlapping_parity_source,
)


def holds(cnf, bits):
    return all(any(bool(bits & (1 << (abs(lit) - 1))) == (lit > 0)
                   for lit in clause) for clause in cnf)


class TestCRCScalingBenchmark(unittest.TestCase):
    def test_parity_chain_source_exactness(self):
        for k in (3, 4, 5):
            source, nvars, nonlinear = overlapping_parity_source(
                k, 710 + k, ratio=0,
            )
            self.assertEqual(nonlinear, ())
            self.assertEqual(nvars, 2 * k - 2)
            for boundary_bits in range(1 << k):
                internal_completions = sum(
                    holds(source, boundary_bits | (extras << k))
                    for extras in range(1 << (nvars - k))
                )
                self.assertEqual(
                    internal_completions, int(boundary_bits.bit_count() % 2 == 0),
                )

    def test_boundary_interaction_density(self):
        self.assertEqual(
            interaction_density(((1, 2, 3), (-1, 2, 3)), (1, 2, 3)), 1,
        )
        self.assertEqual(interaction_density((), (1, 2, 3)), 0)

    def test_pysat_independent_sat_and_count(self):
        source = ((1,), (-2, 3))
        decision, counted = independent_pysat(
            source, 3, max_models=20, seconds=2,
        )
        self.assertEqual(decision["status"], "EXACT")
        self.assertEqual(decision["models"], 1)
        self.assertEqual(counted["models"], 3)
        _, capped = independent_pysat(
            source, 3, max_models=1, seconds=2,
        )
        self.assertEqual(capped["status"], "MODEL_CAP_REACHED")

    def test_small_integrated_crosscheck(self):
        source, nvars, nonlinear = overlapping_parity_source(
            5, 300, ratio=2.4,
        )
        row = benchmark_case(
            "test", source, nvars, nonlinear,
            (1, 2, 3, 4, 5), 300,
            repeats=1, seconds=2, max_states=3000, max_models=100,
        )
        self.assertEqual(row["crc_shannon"]["status"], "EXACT")
        self.assertEqual(row["structured_anf"]["status"], "EXACT")
        self.assertEqual(
            row["crc_shannon"]["models"],
            row["external_pysat_model_enumeration"]["models"],
        )


if __name__ == "__main__":
    unittest.main()
