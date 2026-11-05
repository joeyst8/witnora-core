"""R-461–R-480: hostile CNF and certifier fail-closed tests."""

from __future__ import annotations

import os
import unittest

from scripts.benchmark_xor_frontier import _external_check, exhaustive_sat
from scripts.benchmark_xor_heldout_401_460 import background_instance
from scripts.benchmark_xor_hostile_461_480 import (
    attempt_proof, hostile_fixture, hostile_report,
)
from scripts.benchmark_xor_syndrome_frontier import (
    shortest_inconsistent_subset, validate_witness_against_original,
)
from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text
from witnora_core.drat_trim import find_drat_trim
from witnora_core.xor import XorEquation


class HostileSourceTests(unittest.TestCase):
    def test_r461_reference_source_provenance(self):
        formula, rows, witness, *_ = hostile_fixture(461)
        self.assertTrue(validate_witness_against_original(formula, rows, witness)["exact_original_source_verified"])

    def test_r462_full_original_internal_rup(self):
        f, _, _, selected, trace, _ = hostile_fixture(462)
        proof, error, _ = attempt_proof(f, selected, trace)
        self.assertIsNone(error)
        self.assertTrue(check_drat_text(f, proof)["verified"])

    def test_r463_source_clause_removed(self):
        f, rows, witness, selected, _, _ = hostile_fixture(463)
        clause = tuple(selected[0].source_clauses[0])
        damaged = CNFFormula(c for c in f.to_clause_lists() if tuple(c) != clause)
        with self.assertRaisesRegex(ValueError, "missing from original"):
            validate_witness_against_original(damaged, rows, witness)

    def test_r464_source_clause_removed_fails_closed(self):
        f, _, _, selected, trace, _ = hostile_fixture(464)
        clause = tuple(selected[0].source_clauses[0])
        damaged = CNFFormula(c for c in f.to_clause_lists() if tuple(c) != clause)
        proof, error, _ = attempt_proof(damaged, selected, trace)
        self.assertIsNone(proof)
        self.assertEqual(error, "DETECTED_XOR_SOURCE_CLAUSE_MISSING_FROM_ORIGINAL")

    def test_r465_forged_rhs_detected(self):
        f, rows, witness, *_ = hostile_fixture(465)
        i = witness[0]
        original = rows[i]
        rows[i] = XorEquation(original.variables, original.rhs ^ 1,
                              source_clauses=original.source_clauses)
        with self.assertRaisesRegex(ValueError, "altered"):
            validate_witness_against_original(f, rows, witness)

    def test_r466_duplicate_witness_rejected(self):
        f, rows, witness, *_ = hostile_fixture(466)
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_witness_against_original(f, rows, witness + (witness[0],))

    def test_r467_boolean_witness_index_rejected(self):
        f, rows, _, *_ = hostile_fixture(467)
        with self.assertRaisesRegex(ValueError, "outside source"):
            validate_witness_against_original(f, rows, (True,))

    def test_r468_negative_witness_index_rejected(self):
        f, rows, _, *_ = hostile_fixture(468)
        with self.assertRaisesRegex(ValueError, "outside source"):
            validate_witness_against_original(f, rows, (-1,))

    def test_r469_missing_witness_index_rejected(self):
        f, rows, witness, *_ = hostile_fixture(469)
        with self.assertRaisesRegex(ValueError, "odd GF2"):
            validate_witness_against_original(f, rows, witness[:-1])

    def test_r470_empty_witness_rejected(self):
        f, rows, _, *_ = hostile_fixture(470)
        with self.assertRaisesRegex(ValueError, "invalid"):
            validate_witness_against_original(f, rows, ())

    def test_r471_exact_clause_cap_passes(self):
        f, _, _, selected, trace, _ = hostile_fixture(471)
        proof, error, stats = attempt_proof(f, selected, trace)
        self.assertEqual((proof, error, stats), attempt_proof(f, selected, trace,
            max_proof_clauses=stats["proof_clause_count_actual"]))

    def test_r472_under_clause_cap_rejects(self):
        f, _, _, selected, trace, _ = hostile_fixture(472)
        _, _, stats = attempt_proof(f, selected, trace)
        proof, error, _ = attempt_proof(f, selected, trace,
            max_proof_clauses=stats["proof_clause_count_actual"] - 1)
        self.assertEqual((proof, error), (None, "SKIPPED_PROOF_SIZE_CAP"))

    def test_r473_exact_byte_cap_passes(self):
        f, _, _, selected, trace, _ = hostile_fixture(473)
        proof, error, stats = attempt_proof(f, selected, trace)
        self.assertEqual((proof, error, stats), attempt_proof(f, selected, trace,
            max_proof_bytes=stats["proof_file_size_bytes"]))

    def test_r474_under_byte_cap_rejects(self):
        f, _, _, selected, trace, _ = hostile_fixture(474)
        _, _, stats = attempt_proof(f, selected, trace)
        proof, error, _ = attempt_proof(f, selected, trace,
            max_proof_bytes=stats["proof_file_size_bytes"] - 1)
        self.assertEqual((proof, error), (None, "SKIPPED_PROOF_BYTES_CAP"))

    def test_r475_zero_clause_cap_rejects(self):
        f, _, _, selected, trace, _ = hostile_fixture(475)
        self.assertEqual(attempt_proof(f, selected, trace, max_proof_clauses=0)[1],
                         "SKIPPED_PROOF_SIZE_CAP")

    def test_r476_zero_byte_cap_rejects(self):
        f, _, _, selected, trace, _ = hostile_fixture(476)
        self.assertEqual(attempt_proof(f, selected, trace, max_proof_bytes=0)[1],
                         "SKIPPED_PROOF_BYTES_CAP")

    def test_r477_sat_background_never_certified(self):
        f, rows, _ = background_instance(477, contradictory=False)
        self.assertTrue(exhaustive_sat(f))
        self.assertIsNone(shortest_inconsistent_subset(rows)[0])

    def test_r478_hostile_seed_batch(self):
        for seed in range(47800, 47816):
            self.assertTrue(hostile_report(seed)["one_below_budget_rejected"])

    def test_r479_original_permutation_does_not_change_certificate(self):
        f, _, _, selected, trace, _ = hostile_fixture(479)
        reversed_formula = CNFFormula(reversed(f.to_clause_lists()))
        self.assertEqual(attempt_proof(f, selected, trace),
                         attempt_proof(reversed_formula, selected, trace))

    def test_r480_no_external_checker_claim_without_checker(self):
        result = hostile_report(480)
        self.assertFalse(result["external_original_verified"])


@unittest.skipUnless(find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
                     "pinned drat-trim unavailable")
class HostileExternalTests(unittest.TestCase):
    def test_r461_r480_original_cnf_checker(self):
        checker = find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))
        for seed in range(461000, 461024):
            self.assertTrue(hostile_report(seed, external_checker=checker)["external_original_verified"])


class HostileNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("native Rust extension absent; CI builds it")

    def test_r461_r480_native_differential(self):
        self.assertTrue(all(hostile_report(seed, compare_rust=True)["native_differential"]
                            for seed in range(461000, 461016)))


if __name__ == "__main__":
    unittest.main()
