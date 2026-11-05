"""R-155/R-156: dual RUP checker agreement must precede external verification."""
import unittest
from unittest.mock import patch

from witnora_core.drat_check import check_drat_text as real_check
from witnora_core.xor_drat import export_xor_drat_for_path
from tests.test_xor_native_export_gate import NativeXorExportGateTests


class DualRupGateTests(unittest.TestCase):
    def test_both_internal_checkers_agree_then_external_must_still_run(self):
        formula,path = NativeXorExportGateTests.fixture()
        for order in ("gaussian","sparse-min-fill"):
            with self.subTest(order=order):
                with patch("witnora_core.xor_drat.run_drat_trim",
                           return_value={"external_checker_verified":False,
                                         "error":"test external checker unavailable"}) as external:
                    result=export_xor_drat_for_path(formula,path,
                        drat_trim_path="test-only-placeholder",xor_elim_order=order,
                        proof_backend="rust",require_dual_internal=True,
                        timeout_seconds=None)
                self.assertEqual(external.call_count,1)
                self.assertEqual(result.xor_status["internal_rup_status"],"VERIFIED")
                self.assertEqual(result.xor_status["native_internal_rup_status"],"VERIFIED")
                self.assertEqual(result.xor_status["xor_drat_status"],"DRAT_TRIM_FAILED")
                self.assertFalse(result.xor_status["external_drat"])

    def test_disagreement_fails_before_external_checker(self):
        formula,path = NativeXorExportGateTests.fixture()
        def conflicting_backend(*args,**kwargs):
            result=real_check(*args,**kwargs)
            if kwargs.get("backend")=="rust":
                result=dict(result)
                result["verified"]=False
                result["error"]="deliberate test disagreement"
            return result
        with patch("witnora_core.xor_drat.check_drat_text",
                   side_effect=conflicting_backend), patch(
                   "witnora_core.xor_drat.run_drat_trim") as external:
            result=export_xor_drat_for_path(formula,path,
                drat_trim_path="test-only-placeholder",proof_backend="python",
                require_dual_internal=True,timeout_seconds=None)
        external.assert_not_called()
        self.assertEqual(result.xor_status["xor_drat_status"],"INTERNAL_RUP_FAILED")
        self.assertEqual(result.xor_status["internal_rup_status"],"CHECKER_DISAGREEMENT")
        self.assertFalse(result.xor_status["external_drat"])


if __name__ == "__main__":
    unittest.main()
