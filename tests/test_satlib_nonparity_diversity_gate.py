"""Offline trust and fail-closed checks for preregistered non-parity trials."""
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from scripts.experiment_satlib_nonparity_diversity_gate import (
    FROZEN_NONPARITY_SOURCES, _assert_completed_truth, benchmark,
    classify_and_fallback, compact_benchmark, fetch_frozen_source,
    plain_general_cms,
)


class NonparityDiversityGateTests(unittest.TestCase):
    def test_frozen_allowlist_and_holdout_lock(self):
        self.assertEqual(tuple(FROZEN_NONPARITY_SOURCES), (
            "hole8.cnf.Z", "dubois20.cnf.Z",
            "aim-50-1_6-yes1-1.cnf.Z", "aim-50-1_6-no-1.cnf.Z"))
        with patch("scripts.experiment_satlib_nonparity_diversity_gate.fetch_frozen_source",
                   side_effect=AssertionError("forbidden fetch")):
            with self.assertRaises(ValueError):
                benchmark(names=("par32-2-c.cnf.Z",))
        with self.assertRaises(ValueError):
            fetch_frozen_source("par32-2-c.cnf.Z")

    def test_source_pin_rejects_replaced_file_before_solver(self):
        response = MagicMock()
        response.__enter__.return_value.read.return_value = b"safe-size-archive"
        with patch("scripts.experiment_satlib_nonparity_diversity_gate.urlopen",
                   return_value=response), patch(
                   "scripts.experiment_satlib_nonparity_diversity_gate.run",
                   return_value=SimpleNamespace(stdout=b"p cnf 1 1\n1 0\n")):
            with self.assertRaises(AssertionError):
                fetch_frozen_source("hole8.cnf.Z")

    def test_unsupported_structure_falls_back_to_full_source_sat_check(self):
        result = classify_and_fallback([[1]], 1, budget_s=2)
        self.assertEqual(result["status"], "SAT_VERIFIED_BACKEND")
        self.assertFalse(result["operator_used"])
        self.assertEqual(result["structural_status"], "UNSUPPORTED_SOURCE_STRUCTURE")
        self.assertTrue(result["verified_original_model"])
        self.assertGreaterEqual(result["full_worker_ms"], result["structural_ms"])

    def test_unsat_is_only_complete_backend_claim_not_symbolic_proof(self):
        result = classify_and_fallback([[1], [-1]], 1, budget_s=2)
        self.assertEqual(result["status"], "UNSAT_BACKEND")
        self.assertFalse(result["operator_used"])
        self.assertEqual(result["structural_status"], "UNSUPPORTED_SOURCE_STRUCTURE")
        self.assertFalse(result["verified_original_model"])

    def test_plain_comparator_accepts_verified_sat_and_backend_unsat(self):
        self.assertEqual(plain_general_cms([[1]], 1)["status"],
                         "SAT_VERIFIED_BACKEND")
        self.assertEqual(plain_general_cms([[1], [-1]], 1)["status"],
                         "UNSAT_BACKEND")

    def test_xor_contradiction_diagnostic_still_requires_backend(self):
        with patch("scripts.experiment_satlib_nonparity_diversity_gate.cross_instance_symbolic_search",
                   side_effect=AssertionError("contradictory exact source XOR system")):
            result = classify_and_fallback([[1], [-1]], 1, budget_s=2)
        self.assertEqual(result["structural_status"],
                         "POTENTIAL_UNAUDITED_XOR_CONTRADICTION")
        self.assertEqual(result["status"], "UNSAT_BACKEND")
        self.assertFalse(result["operator_used"])

    def test_truth_disagreement_and_extra_trial_rejected(self):
        with self.assertRaises(AssertionError):
            _assert_completed_truth({"status": "UNSAT_BACKEND"}, True, "sat_fixture")
        with self.assertRaises(AssertionError):
            _assert_completed_truth({"status": "SAT_VERIFIED_BACKEND"}, False,
                                    "unsat_fixture")
        with self.assertRaises(ValueError):
            benchmark(repeats=3)

    def test_compact_result_keeps_unknown_without_unsat_claim(self):
        record = {"protocol": "frozen", "sealed_holdout_untouched": True,
                  "results": [{"source": "fixture", "family": "AIM", "sha256": "x",
                               "expected_sat": False,
                               "trials": [{"trial": 1,
                                           "portfolio": {"status": "UNKNOWN_TIMEOUT"},
                                           "raw_cms": {"status": "UNSAT_BACKEND",
                                                       "worker_ms": 1.0}}]}]}
        compact = compact_benchmark(record)
        trial = compact["results"][0]["trials"][0]
        self.assertEqual(trial["portfolio_status"], "UNKNOWN_TIMEOUT")
        self.assertEqual(trial["raw_status"], "UNSAT_BACKEND")
        self.assertIsNone(trial["portfolio_ms"])


if __name__ == "__main__":
    unittest.main()
