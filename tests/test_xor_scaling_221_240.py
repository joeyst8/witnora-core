"""R-221–R-240: bounded exporter scaling and exact cap boundary gates."""

from __future__ import annotations

import os
import unittest

from scripts.benchmark_xor_frontier import exhaustive_sat
from scripts.benchmark_xor_proof_scaling import contradiction, measure, run_scaling
from witnora_core.drat_trim import find_drat_trim


class XorProofScalingTests(unittest.TestCase):
    def assert_width(self, width):
        result = measure(width)
        self.assertEqual(result["status"], "CANDIDATE_RUP_ACCEPTED")
        self.assertEqual(result["source_clauses"], 2 ** width)
        self.assertEqual(result["proof_clauses"], 2 ** width - 1)
        self.assertEqual(result["peak_proof_width"], width - 1)

    def test_r221_width1(self): self.assert_width(1)
    def test_r222_width2(self): self.assert_width(2)
    def test_r223_width3(self): self.assert_width(3)
    def test_r224_width4(self): self.assert_width(4)
    def test_r225_width5(self): self.assert_width(5)
    def test_r226_width6(self): self.assert_width(6)
    def test_r227_width7(self): self.assert_width(7)
    def test_r228_width8(self): self.assert_width(8)
    def test_r229_width9(self): self.assert_width(9)
    def test_r230_width10(self): self.assert_width(10)

    def test_r231_exact_exponential_clause_growth(self):
        counts = [measure(w)["proof_clauses"] for w in range(1, 11)]
        self.assertEqual(counts, [(1 << w) - 1 for w in range(1, 11)])

    def test_r232_proof_growth_recurrence(self):
        counts = [measure(w)["proof_clauses"] for w in range(1, 11)]
        self.assertTrue(all(b == 2 * a + 1 for a, b in zip(counts, counts[1:])))

    def test_r233_byte_growth_is_not_hidden_by_clause_count(self):
        result = run_scaling(max_width=10)
        size = [row["proof_bytes"] for row in result["rows"]]
        self.assertEqual(size, sorted(set(size)))
        self.assertGreater(size[-1], 100 * size[0])

    def test_r234_clause_cap_one_below_fails_closed(self):
        result = measure(8, max_proof_clauses=254)
        self.assertEqual(result["status"], "SKIPPED_PROOF_SIZE_CAP")

    def test_r235_byte_cap_one_below_fails_closed(self):
        measured = measure(8)
        result = measure(8, max_proof_bytes=measured["proof_bytes"] - 1)
        self.assertEqual(result["status"], "SKIPPED_PROOF_BYTES_CAP")

    def test_r236_exact_clause_and_byte_budgets_pass(self):
        measured = measure(8)
        result = measure(8, max_proof_clauses=measured["proof_clauses"],
                         max_proof_bytes=measured["proof_bytes"])
        self.assertEqual(result["proof_sha256"], measured["proof_sha256"])

    def test_r237_independent_enumeration_of_original_cnf(self):
        for width in range(1, 7):
            formula, _, _ = contradiction(width)
            self.assertFalse(exhaustive_sat(formula))

    def test_r238_deterministic_proof_and_source_hashes(self):
        self.assertEqual(run_scaling(10), run_scaling(10))

    def test_r239_no_checker_does_not_count_as_external(self):
        self.assertFalse(run_scaling(10)["external_drat_verification_performed"])
        self.assertTrue(all(not row["external_drat_verified"]
                            for row in run_scaling(10)["rows"]))

    def test_r240_width_guard_fails_closed(self):
        for width in (0, 13):
            with self.assertRaisesRegex(ValueError, "bounded domain|width"):
                run_scaling(width)


@unittest.skipUnless(find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
                     "external drat-trim not available")
class XorProofScalingExternalTests(unittest.TestCase):
    def test_r221_r240_real_external_verification(self):
        result = run_scaling(10, external_checker=find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")))
        self.assertTrue(all(row["external_drat_verified"] for row in result["rows"]))


class XorProofScalingNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("Rust extension absent; focused CI builds it")

    def test_r221_r240_native_differential(self):
        result = run_scaling(10, compare_rust=True)
        self.assertTrue(all(row["rust_differential_verified"] for row in result["rows"]))


if __name__ == "__main__":
    unittest.main()
