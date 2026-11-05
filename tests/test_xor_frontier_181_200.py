"""R-181–R-200: independently enumerated XOR proof and safety gates."""

import copy
import unittest

from scripts.benchmark_xor_frontier import (
    build_case, exercise_case, exhaustive_sat, run_suite,
)
from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.xor_drat import _row_trace_refutation


OPTIONS = dict(max_proof_clauses=2000, max_proof_bytes=40000,
               timeout_seconds=None)


def candidate(formula, equations, trace, **overrides):
    return _row_trace_refutation(formula, equations, trace,
        **{**OPTIONS, **overrides})


class XorFrontierIndependentTests(unittest.TestCase):
    def fixture(self, *, contradictory=True, width=3, overlap=False,
                shuffle=False, sparse_ids=False, seed=181):
        return build_case(seed, width=width, contradictory=contradictory,
            overlap=overlap, shuffle=shuffle, sparse_ids=sparse_ids)

    def test_r181_independent_truth_table_sat(self):
        self.assertTrue(exhaustive_sat(CNFFormula([[1, 2], [-1, 2]])))
        self.assertTrue(exhaustive_sat(CNFFormula(())))

    def test_r182_independent_truth_table_unsat(self):
        self.assertFalse(exhaustive_sat(CNFFormula([[1], [-1]])))
        self.assertFalse(exhaustive_sat(CNFFormula([[]])))

    def test_r183_oracle_variable_cap_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "variable cap"):
            exhaustive_sat(CNFFormula([[i] for i in range(1, 14)]))

    def test_r184_planted_sat_source_control(self):
        for width in (1, 2, 3):
            formula, equations, trace = self.fixture(contradictory=False, width=width)
            self.assertTrue(exhaustive_sat(formula))
            self.assertEqual(candidate(formula, equations, trace)[0], None)

    def test_r185_contradictory_original_cnf_unsat(self):
        for width in (1, 2, 3):
            formula, _, _ = self.fixture(width=width)
            self.assertFalse(exhaustive_sat(formula))

    def test_r186_positive_proof_rup_original_cnf(self):
        for width in (1, 2, 3):
            formula, equations, trace = self.fixture(width=width)
            proof, error, _ = candidate(formula, equations, trace)
            self.assertIsNone(error)
            self.assertTrue(check_drat_text(formula, proof)["verified"])

    def test_r187_tampered_proof_rejected(self):
        formula, equations, trace = self.fixture()
        proof, _, _ = candidate(formula, equations, trace)
        self.assertFalse(check_drat_text(formula, "\n".join(proof.splitlines()[:-1]) + "\n")["verified"])

    def test_r188_original_clause_permutation(self):
        formula, equations, trace = self.fixture(shuffle=True)
        reordered = CNFFormula(reversed(formula.to_clause_lists()))
        self.assertEqual(formula.canonical_dimacs(), reordered.canonical_dimacs())
        self.assertEqual(candidate(formula, equations, trace), candidate(reordered, equations, trace))

    def test_r189_original_clause_duplication(self):
        formula, equations, trace = self.fixture()
        duplicated = CNFFormula(formula.to_clause_lists() * 2)
        self.assertEqual(formula, duplicated)
        self.assertEqual(candidate(formula, equations, trace), candidate(duplicated, equations, trace))

    def test_r190_sparse_label_invariance(self):
        output = exercise_case(190, width=3, contradictory=True, overlap=True,
            shuffle=True, sparse_ids=True)
        self.assertFalse(output["exhaustive_original_cnf_sat"])
        self.assertTrue(output["rup_subset_verified"])

    def test_r191_overlapping_background_sat_control(self):
        result = exercise_case(191, width=3, contradictory=False, overlap=True,
            shuffle=True, sparse_ids=False)
        self.assertTrue(result["exhaustive_original_cnf_sat"])
        self.assertIsNone(result["proof_candidate_sha256"])

    def test_r192_missing_original_clause_rejected(self):
        formula, equations, trace = self.fixture()
        target = min(equations[0].source_clauses)
        reduced = CNFFormula(c for c in formula.to_clause_lists() if tuple(c) != target)
        self.assertEqual(candidate(reduced, equations, trace)[1],
            "DETECTED_XOR_SOURCE_CLAUSE_MISSING_FROM_ORIGINAL")

    def test_r193_mutated_original_source_rejected(self):
        formula, equations, trace = self.fixture()
        changed = [list(c) for c in formula.to_clause_lists()]
        target = min(equations[0].source_clauses)
        index = next(i for i, clause in enumerate(changed) if tuple(clause) == target)
        changed[index][0] *= -1
        mutated = CNFFormula(changed)
        self.assertEqual(candidate(mutated, equations, trace)[1],
            "DETECTED_XOR_SOURCE_CLAUSE_MISSING_FROM_ORIGINAL")

    def test_r194_missing_parent_id_rejected(self):
        formula, equations, trace = self.fixture()
        altered = copy.deepcopy(trace)
        altered[0]["left_row_id"] = "not-a-real-row"
        proof, error, _ = candidate(formula, equations, altered)
        self.assertIsNone(proof)
        self.assertIsNotNone(error)

    def test_r195_bad_result_parity_rejected(self):
        formula, equations, trace = self.fixture()
        altered = copy.deepcopy(trace)
        altered[0]["result_rhs"] ^= 1
        proof, error, _ = candidate(formula, equations, altered)
        self.assertIsNone(proof)
        self.assertIsNotNone(error)

    def test_r196_zero_clause_cap_rejected(self):
        formula, equations, trace = self.fixture()
        proof, error, _ = candidate(formula, equations, trace, max_proof_clauses=0)
        self.assertIsNone(proof)
        self.assertEqual(error, "SKIPPED_PROOF_SIZE_CAP")

    def test_r197_zero_byte_cap_rejected(self):
        formula, equations, trace = self.fixture()
        proof, error, _ = candidate(formula, equations, trace, max_proof_bytes=0)
        self.assertIsNone(proof)
        self.assertEqual(error, "SKIPPED_PROOF_BYTES_CAP")

    def test_r198_missing_external_verifier_not_certified(self):
        result = run_suite(seeds=1)
        self.assertFalse(result["external_drat_verification_performed"])
        self.assertTrue(all(not row["external_drat_verified"] for row in result["records"]))

    def test_r199_invalid_external_verifier_path_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "unavailable"):
            run_suite(seeds=1, external_checker="/does-not-exist/witnora-drat-trim")

    def test_r200_reproducible_mixed_sat_unsat_suite(self):
        first = run_suite(seeds=2)
        second = run_suite(seeds=2)
        self.assertEqual(first, second)
        self.assertEqual(first["cases"], 96)
        self.assertEqual(first["independently_enumerated_sat"], 48)
        self.assertEqual(first["independently_enumerated_unsat"], 48)


class XorFrontierNativeDifferentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("native extension absent; CI builds and checks Rust")

    def test_r181_r200_native_vs_python_96_cases(self):
        result = run_suite(seeds=2, compare_rust=True)
        self.assertTrue(result["native_python_differential"])
        self.assertEqual(result["cases"], 96)


if __name__ == "__main__":
    unittest.main()
