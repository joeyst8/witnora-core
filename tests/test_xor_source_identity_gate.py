"""R-157/R-158: wrong or malformed DIMACS cannot enter proof checkers."""
import unittest
from unittest.mock import patch

from tests.test_xor_native_export_gate import NativeXorExportGateTests
from witnora_core.xor_drat import export_xor_drat_for_path


class XorSourceIdentityGateTests(unittest.TestCase):
    def test_mismatched_and_malformed_dimacs_fail_before_checking(self):
        formula,path=NativeXorExportGateTests.fixture()
        bad_sources=("p cnf 1 1\n1 0\n", "not a DIMACS formula")
        for original_text in bad_sources:
            with self.subTest(original_text=original_text), patch(
                "witnora_core.xor_drat.check_drat_text") as internal, patch(
                "witnora_core.xor_drat.run_drat_trim") as external:
                result=export_xor_drat_for_path(formula,path,
                    drat_trim_path="test-only-placeholder",
                    original_dimacs_text=original_text,
                    proof_backend="rust",require_source_identity=True,
                    timeout_seconds=None)
            internal.assert_not_called()
            external.assert_not_called()
            self.assertEqual(result.xor_status["xor_drat_status"],"FAILED")
            self.assertEqual(result.xor_status["source_identity_status"],"FAILED")
            self.assertFalse(result.xor_status["external_drat"])

    def test_same_canonical_cnf_reaches_but_does_not_bypass_external(self):
        formula,path=NativeXorExportGateTests.fixture()
        for original_text in ("p cnf 1 2\n1 0\n-1 0\n",
                              "c comment\np cnf 2 2\n-1 0\n1 0\n"):
            with self.subTest(original_text=original_text), patch(
                "witnora_core.xor_drat.run_drat_trim",
                return_value={"external_checker_verified":False,
                              "error":"test external checker unavailable"}) as external:
                result=export_xor_drat_for_path(formula,path,
                    drat_trim_path="test-only-placeholder",
                    original_dimacs_text=original_text,
                    proof_backend="rust",require_source_identity=True,
                    timeout_seconds=None)
            self.assertEqual(external.call_count,1)
            self.assertEqual(result.xor_status["xor_drat_status"],"DRAT_TRIM_FAILED")
            self.assertFalse(result.xor_status["external_drat"])


if __name__ == "__main__":
    unittest.main()
