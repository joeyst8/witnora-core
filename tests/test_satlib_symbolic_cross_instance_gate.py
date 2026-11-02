"""Fail-closed source-lock and orchestration gates for public parity instances."""
import unittest
from unittest.mock import patch

from scripts.experiment_satlib_symbolic_cross_instance_gate import (
    FROZEN_VALIDATION_SOURCES, benchmark, compact_benchmark,
    cross_instance_symbolic_search, fetch_validation_source,
)


class SymbolicCrossInstanceGateTests(unittest.TestCase):
    def test_holdout_is_rejected_without_fetch(self):
        with patch("scripts.experiment_satlib_symbolic_cross_instance_gate.fetch_validation_source",
                   side_effect=AssertionError("holdout source was fetched")):
            with self.assertRaises(ValueError):
                benchmark(names=("par32-2-c.cnf.Z",))
        with self.assertRaises(ValueError):
            fetch_validation_source("par32-2-c.cnf.Z")

    def test_source_allowlist_is_frozen_to_three_public_validation_cases(self):
        self.assertEqual(set(FROZEN_VALIDATION_SOURCES),
                         {"par16-1-c.cnf.Z", "par16-2-c.cnf.Z", "par32-3-c.cnf.Z"})
        self.assertTrue(all(len(digest) == 64 for digest
                            in FROZEN_VALIDATION_SOURCES.values()))
        with self.assertRaises(ValueError):
            benchmark(names=("par32-1-c.cnf.Z",))

    def test_hash_mismatch_aborts_before_any_solver_runs(self):
        with patch("scripts.experiment_satlib_symbolic_cross_instance_gate.fetch_validation_source",
                   return_value={"dimacs_sha256": "not-the-official-source"}):
            with self.assertRaises(AssertionError):
                benchmark(names=("par16-1-c.cnf.Z",), repeats=1)

    def test_unsupported_structure_does_not_infer_unsat(self):
        result = cross_instance_symbolic_search([[1]], 1, budget_s=2)
        self.assertEqual(result["status"], "UNSUPPORTED_SOURCE_STRUCTURE")
        self.assertNotEqual(result["status"], "UNSAT")

    def test_resource_budget_is_strict(self):
        with self.assertRaises(ValueError):
            cross_instance_symbolic_search([[1]], 1, budget_s=100)

    def test_compact_reporting_does_not_erase_unknown_results(self):
        report = {"sealed_holdout_untouched": True,
                  "results": [{"source": "test", "sha256": "fixture",
                               "trials": [{"trial": 1,
                                           "symbolic": {"status": "UNKNOWN_TIMEOUT",
                                                        "no_unsat_inference": True},
                                           "raw_cms": {"status": "SAT",
                                                       "total_worker_ms": 3.0}}]}]}
        compact = compact_benchmark(report)
        row = compact["results"][0]["trials"][0]
        self.assertEqual(row["symbolic_status"], "UNKNOWN_TIMEOUT")
        self.assertIsNone(row["symbolic_ms"])
        self.assertEqual(row["cms_ms"], 3.0)


if __name__ == "__main__":
    unittest.main()
