"""R-161/R-162: independent text/width/byte audit before RUP/DRAT checking."""
import random
import unittest
from unittest.mock import patch

from witnora_core.xor_drat import _clause_line, export_xor_drat_for_path
from tests.test_xor_native_export_gate import NativeXorExportGateTests


class XorProofAuditRustTests(unittest.TestCase):
    def test_seeded_proof_text_accounting(self):
        from witnora_ve import xor_proof_audit_native
        rng=random.Random(161162)
        for trial in range(240):
            clauses=[]
            for _ in range(rng.randrange(1,25)):
                clauses.append(tuple(rng.sample([*range(-40,0),*range(1,41)],
                                                rng.randrange(0,8))))
            proof="\n".join(_clause_line(c) for c in clauses)+"\n"
            with self.subTest(trial=trial):
                self.assertEqual(xor_proof_audit_native(proof),
                                 (len(clauses), max(map(len,clauses)),
                                  len(proof.encode("utf-8")),None))
        self.assertIsNotNone(xor_proof_audit_native("0")[3])
        self.assertIsNotNone(xor_proof_audit_native("d 1 0\n")[3])

    def test_mismatch_never_reaches_external_checker(self):
        formula,path=NativeXorExportGateTests.fixture()
        with patch("witnora_ve.xor_proof_audit_native",
                   return_value=(99,0,2,None)),patch(
                   "witnora_core.xor_drat.check_drat_text") as internal,patch(
                   "witnora_core.xor_drat.run_drat_trim") as external:
            result=export_xor_drat_for_path(formula,path,
                drat_trim_path="test-only-placeholder",proof_backend="rust",
                require_native_proof_audit=True,timeout_seconds=None)
        internal.assert_not_called()
        external.assert_not_called()
        self.assertEqual(result.xor_status["native_candidate_audit_status"],"FAILED")
        self.assertFalse(result.xor_status["external_drat"])

    def test_good_audit_still_needs_external_checker(self):
        formula,path=NativeXorExportGateTests.fixture()
        with patch("witnora_core.xor_drat.run_drat_trim",
                   return_value={"external_checker_verified":False,
                                 "error":"test external checker unavailable"}) as external:
            result=export_xor_drat_for_path(formula,path,
                drat_trim_path="test-only-placeholder",proof_backend="rust",
                require_native_proof_audit=True,timeout_seconds=None)
        self.assertEqual(external.call_count,1)
        self.assertEqual(result.xor_status["xor_drat_status"],"DRAT_TRIM_FAILED")
        self.assertFalse(result.xor_status["external_drat"])


if __name__ == "__main__":
    unittest.main()
