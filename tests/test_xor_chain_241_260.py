"""R-241–R-260: linear-chain XOR proof experiment, independent controls."""

from __future__ import annotations

import os
import unittest

from scripts.benchmark_xor_chain_frontier import chain, measure_chain, run_chains
from scripts.benchmark_xor_frontier import exhaustive_sat
from scripts.benchmark_xor_proof_scaling import measure as dense_measure
from witnora_core.drat_trim import find_drat_trim


class XorChainResearchTests(unittest.TestCase):
    def assert_n(self, n):
        result = measure_chain(n)
        self.assertEqual(result["status"], "CANDIDATE_RUP_ACCEPTED")
        self.assertEqual(result["source_clauses"], 2 * n)
        self.assertEqual(result["proof_clauses"], n)
        self.assertEqual(result["trace_operations"], n)

    def test_r241_n2(self): self.assert_n(2)
    def test_r242_n3(self): self.assert_n(3)
    def test_r243_n4(self): self.assert_n(4)
    def test_r244_n5(self): self.assert_n(5)
    def test_r245_n8(self): self.assert_n(8)
    def test_r246_n10(self): self.assert_n(10)
    def test_r247_n16(self): self.assert_n(16)
    def test_r248_n20(self): self.assert_n(20)
    def test_r249_n40(self): self.assert_n(40)
    def test_r250_n80(self): self.assert_n(80)

    def test_r251_chain_source_size_linear(self):
        rows = run_chains()["rows"]
        self.assertTrue(all(row["source_clauses"] == 2 * row["n"] for row in rows))

    def test_r252_chain_proof_size_linear(self):
        rows = run_chains()["rows"]
        self.assertTrue(all(row["proof_clauses"] == row["n"] for row in rows))

    def test_r253_chain_row_trace_operations_linear(self):
        rows = run_chains()["rows"]
        self.assertTrue(all(row["trace_operations"] == row["n"] for row in rows))

    def test_r254_sparse_relabel_keeps_proof_clause_count(self):
        original = measure_chain(20)
        sparse = measure_chain(20, variable_gap=1000)
        self.assertEqual(original["proof_clauses"], sparse["proof_clauses"])
        self.assertNotEqual(original["original_cnf_sha256"], sparse["original_cnf_sha256"])

    def test_r255_original_clause_order_permutation(self):
        self.assertEqual(measure_chain(20), measure_chain(20, reverse_clauses=True))

    def test_r256_satisfiable_last_anchor_control(self):
        formula, _, _ = chain(10, contradictory=False)
        self.assertTrue(exhaustive_sat(formula))
        self.assertEqual(measure_chain(10, contradictory=False)["status"],
                         "ROW_OPERATION_TRACE_DID_NOT_DERIVE_EMPTY")

    def test_r257_independent_unsat_small_chain_oracle(self):
        for n in (2, 3, 4, 5, 6, 8):
            self.assertFalse(exhaustive_sat(chain(n)[0]))

    def test_r258_exact_proof_clause_cap_and_lower_rejection(self):
        self.assertEqual(measure_chain(20, max_proof_clauses=20)["proof_clauses"], 20)
        self.assertEqual(measure_chain(20, max_proof_clauses=19)["status"],
                         "SKIPPED_PROOF_SIZE_CAP")

    def test_r259_exact_proof_byte_cap_and_lower_rejection(self):
        measured = measure_chain(20)
        size = measured["proof_bytes"]
        self.assertEqual(measure_chain(20, max_proof_bytes=size)["proof_bytes"], size)
        self.assertEqual(measure_chain(20, max_proof_bytes=size - 1)["status"],
                         "SKIPPED_PROOF_BYTES_CAP")

    def test_r260_compare_linear_sparse_to_dense_full_encoding(self):
        chain_result = measure_chain(10)
        dense_result = dense_measure(10)
        self.assertEqual((chain_result["source_clauses"],chain_result["proof_clauses"]), (20,10))
        self.assertEqual((dense_result["source_clauses"],dense_result["proof_clauses"]), (1024,1023))
        self.assertNotEqual(chain_result["original_cnf_sha256"],dense_result["original_cnf_sha256"])


@unittest.skipUnless(find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM")),
                     "external drat-trim absent")
class XorChainExternalTests(unittest.TestCase):
    def test_r241_r260_externally_verified_chain(self):
        checker = find_drat_trim(os.environ.get("WITNORA_DRAT_TRIM"))
        result = run_chains(external_checker=checker)
        self.assertTrue(all(row["external_drat_verified"] for row in result["rows"]))


class XorChainNativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            raise unittest.SkipTest("Rust extension absent; CI builds and tests it")

    def test_r241_r260_native_output_and_caps(self):
        rows = run_chains(compare_rust=True)["rows"]
        self.assertTrue(all(row["native_differential"] for row in rows))
        self.assertEqual(measure_chain(80, compare_rust=True,
                                     max_proof_clauses=79)["status"], "SKIPPED_PROOF_SIZE_CAP")


if __name__ == "__main__":
    unittest.main()
