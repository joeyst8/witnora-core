"""R-159/R-160: fail-closed Python/Rust source-DIMACS parser agreement."""
import unittest
from unittest.mock import patch

from witnora_core.cnf import CNFFormula
from witnora_core.xor_drat import export_xor_drat_for_path
from tests.test_xor_native_export_gate import NativeXorExportGateTests


class XorDualSourceParserTests(unittest.TestCase):
    def test_invalid_gate_combo(self):
        formula,path=NativeXorExportGateTests.fixture()
        with self.assertRaisesRegex(ValueError,"dual source parser requires"):
            export_xor_drat_for_path(formula,path,drat_trim_path=None,
                                     require_dual_source_parser=True)

    def test_parser_disagreement_refuses_all_proof_checkers(self):
        formula,path=NativeXorExportGateTests.fixture()
        with patch("witnora_core.xor_drat.parse_dimacs_with_text_evidence",
                   return_value=(CNFFormula([[1]]), [[1]],[1,0],["1","0"])), patch(
                   "witnora_core.xor_drat.check_drat_text") as internal, patch(
                   "witnora_core.xor_drat.run_drat_trim") as external:
            result=export_xor_drat_for_path(formula,path,
                drat_trim_path="test-only-placeholder",
                original_dimacs_text="p cnf 1 2\n1 0\n-1 0\n",
                proof_backend="python",require_source_identity=True,
                require_dual_source_parser=True,timeout_seconds=None)
        internal.assert_not_called()
        external.assert_not_called()
        self.assertEqual(result.xor_status["source_identity_status"],"FAILED")
        self.assertFalse(result.xor_status["external_drat"])

    def test_real_both_parsers_agree_external_checker_remains_required(self):
        formula,path=NativeXorExportGateTests.fixture()
        with patch("witnora_core.xor_drat.run_drat_trim",
                   return_value={"external_checker_verified":False,
                                 "error":"test external checker unavailable"}) as external:
            result=export_xor_drat_for_path(formula,path,
                drat_trim_path="test-only-placeholder",
                original_dimacs_text="c source\np cnf 1 2\n-1 0\n1 0\n",
                proof_backend="rust",require_source_identity=True,
                require_dual_source_parser=True,timeout_seconds=None)
        self.assertEqual(external.call_count,1)
        self.assertEqual(result.xor_status["xor_drat_status"],"DRAT_TRIM_FAILED")
        self.assertFalse(result.xor_status["external_drat"])


if __name__ == "__main__":
    unittest.main()
