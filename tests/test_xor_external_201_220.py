"""R-201–R-220: real independent drat-trim and boundary controls."""

from __future__ import annotations

import os
import sys
import unittest

from scripts.benchmark_xor_frontier import (
    _external_check, build_case, exercise_case, exhaustive_sat, run_suite,
)
from witnora_core.cnf import CNFFormula
from witnora_core.drat_trim import find_drat_trim, run_drat_trim
from witnora_core.xor_drat import _row_trace_refutation


OPTIONS = dict(max_proof_clauses=2000, max_proof_bytes=40000,
               timeout_seconds=None)


def sample(width=3, **config):
    formula, equations, trace = build_case(201220, width=width,
        contradictory=True, overlap=config.get("overlap", False),
        shuffle=config.get("shuffle", False), sparse_ids=config.get("sparse_ids", False))
    proof, error, stats = _row_trace_refutation(formula, equations, trace, **OPTIONS)
    assert error is None and proof is not None
    return formula, equations, trace, proof, stats


@unittest.skipUnless(find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
                     "an explicit or PATH drat-trim executable is required")
class XorRealExternalProofTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.checker = find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))

    def test_r201_width1_external_acceptance(self):
        formula, _, _, proof, _ = sample(1)
        self.assertTrue(_external_check(formula, proof, self.checker))

    def test_r202_width2_external_acceptance(self):
        formula, _, _, proof, _ = sample(2)
        self.assertTrue(_external_check(formula, proof, self.checker))

    def test_r203_width3_external_acceptance(self):
        formula, _, _, proof, _ = sample(3)
        self.assertTrue(_external_check(formula, proof, self.checker))

    def test_r204_sparse_labels_external_acceptance(self):
        formula, _, _, proof, _ = sample(sparse_ids=True)
        self.assertTrue(_external_check(formula, proof, self.checker))

    def test_r205_overlapping_background_external_acceptance(self):
        formula, _, _, proof, _ = sample(overlap=True)
        self.assertTrue(_external_check(formula, proof, self.checker))

    def test_r206_shuffled_duplicated_external_acceptance(self):
        formula, _, _, proof, _ = sample(shuffle=True)
        self.assertTrue(_external_check(formula, proof, self.checker))

    def test_r207_heldout_external_seed_batch(self):
        for seed in range(207000, 207012):
            result = exercise_case(seed, width=3, contradictory=True,
                overlap=seed % 2 == 0, shuffle=seed % 3 == 0,
                sparse_ids=seed % 5 == 0, external_checker=self.checker)
            self.assertTrue(result["external_drat_verified"])

    def test_r208_incomplete_early_prefix_rejected(self):
        formula, _, _, proof, _ = sample()
        # A proof without its final empty line may nevertheless contain a
        # conflicting pair of unit clauses; truncate before that conflict.
        self.assertFalse(_external_check(formula,
            "\n".join(proof.splitlines()[:2]) + "\n", self.checker))

    def test_r209_weakened_satisfiable_original_rejects_proof(self):
        formula, equations, _, proof, _ = sample()
        target = min(equations[1].source_clauses)
        weakened = CNFFormula(c for c in formula.to_clause_lists() if tuple(c) != target)
        self.assertTrue(exhaustive_sat(weakened))
        self.assertFalse(_external_check(weakened, proof, self.checker))

    def test_r210_forced_empty_clause_on_sat_rejected(self):
        self.assertFalse(_external_check(CNFFormula([[1, 2], [-1, 2]]),
                                         "0\n", self.checker))

    def test_r211_empty_proof_not_certification(self):
        formula, _, _, _, _ = sample()
        self.assertFalse(_external_check(formula, "", self.checker))

    def test_r212_no_checker_returns_not_run(self):
        result = run_drat_trim("nonexistent.cnf", "nonexistent.drat", None)
        self.assertFalse(result["external_checker_ran"])
        self.assertFalse(result["external_checker_verified"])
        self.assertEqual(result["external_checker"], "NOT_RUN")

    def test_r213_invalid_checker_does_not_claim_success(self):
        result = run_drat_trim("nonexistent.cnf", "nonexistent.drat",
                               "/nonexistent/drat-trim")
        self.assertFalse(result["external_checker_verified"])
        self.assertIsNotNone(result["error"])

    def test_r214_unrelated_executable_not_external_proof(self):
        result = run_drat_trim("nonexistent.cnf", "nonexistent.drat",
                               sys.executable)
        self.assertFalse(result["external_checker_verified"])

    def test_r215_exact_clause_cap_minus_one_rejects(self):
        formula, equations, trace, _, stats = sample()
        proof, error, _ = _row_trace_refutation(formula, equations, trace,
            **{**OPTIONS, "max_proof_clauses": stats["proof_clause_count_actual"] - 1})
        self.assertIsNone(proof)
        self.assertEqual(error, "SKIPPED_PROOF_SIZE_CAP")

    def test_r216_exact_byte_cap_minus_one_rejects(self):
        formula, equations, trace, _, stats = sample()
        proof, error, _ = _row_trace_refutation(formula, equations, trace,
            **{**OPTIONS, "max_proof_bytes": stats["proof_file_size_bytes"] - 1})
        self.assertIsNone(proof)
        self.assertEqual(error, "SKIPPED_PROOF_BYTES_CAP")

    def test_r217_exact_caps_succeed_and_external_accepts(self):
        formula, equations, trace, original, stats = sample()
        proof, error, result = _row_trace_refutation(formula, equations, trace,
            **{**OPTIONS, "max_proof_clauses": stats["proof_clause_count_actual"],
               "max_proof_bytes": stats["proof_file_size_bytes"]})
        self.assertIsNone(error)
        self.assertEqual(proof, original)
        self.assertEqual(result, stats)
        self.assertTrue(_external_check(formula, proof, self.checker))

    def test_r218_external_status_requires_explicit_checker(self):
        options = dict(seed=218, width=3, contradictory=True,
            overlap=True, shuffle=True, sparse_ids=False)
        without = exercise_case(**options)
        with_checker = exercise_case(**options, external_checker=self.checker)
        self.assertFalse(without["external_drat_verified"])
        self.assertTrue(with_checker["external_drat_verified"])
        self.assertEqual(without["proof_candidate_sha256"], with_checker["proof_candidate_sha256"])

    def test_r219_external_repeat_is_deterministic(self):
        formula, _, _, proof, _ = sample()
        self.assertEqual(_external_check(formula, proof, self.checker),
                         _external_check(formula, proof, self.checker))

    def test_r220_full_paired_external_suite(self):
        results = run_suite(seeds=2, external_checker=self.checker)
        self.assertEqual(results["cases"], 96)
        self.assertEqual(results["independently_enumerated_unsat"], 48)
        self.assertTrue(all(row["external_drat_verified"]
                            for row in results["records"] if row["contradictory"]))
        self.assertTrue(all(not row["external_drat_verified"]
                            for row in results["records"] if not row["contradictory"]))


if __name__ == "__main__":
    unittest.main()
