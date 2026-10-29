"""Branch coverage and fail-closed tests for the G14-to-G5 Lean gate."""

import unittest
import io
import json
from contextlib import redirect_stdout
from unittest.mock import patch

from witnora_core.lean_g14_gate import verify_g14_unsat_cover_with_lean
from witnora_core.separator_affine_family_theorem import (
    build_separator_affine_certificate, make_separator_affine_instance,
)


class G14LeanCoverGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instance = make_separator_affine_instance("saf_unsat_cover_2")
        cls.certificate = build_separator_affine_certificate(cls.instance)

    def test_every_separator_branch_requires_lean_g5(self):
        accepted = {"verified": True, "lean_formal_status": "LEAN_VERIFIED"}
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean",
                   return_value=accepted) as gate:
            result = verify_g14_unsat_cover_with_lean(
                self.instance.formula, self.certificate,
            )
        self.assertTrue(result["verified"])
        self.assertEqual(result["lean_formal_status"], "LEAN_G5_COVER_VERIFIED")
        self.assertEqual(gate.call_count, 2)
        self.assertEqual([b["assignment_id"] for b in result["branches"]], ["S1", "S2"])

    def test_single_failed_branch_rejects_cover(self):
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean",
                   side_effect=[
                       {"verified": True},
                       {"verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED"},
                   ]) as gate:
            result = verify_g14_unsat_cover_with_lean(
                self.instance.formula, self.certificate,
            )
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "BRANCH_G5_LEAN_REJECTED")
        self.assertEqual(gate.call_count, 2)

    def test_tampered_source_formula_blocks_lean(self):
        data = self.certificate.to_dict()
        data["formula_hash"] = "0" * 64
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean") as gate:
            result = verify_g14_unsat_cover_with_lean(self.instance.formula, data)
        self.assertFalse(result["verified"])
        gate.assert_not_called()

    def test_sat_certificate_not_accepted_as_unsat_cover(self):
        instance = make_separator_affine_instance("saf_sat_chain_2")
        cert = build_separator_affine_certificate(instance)
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean") as gate:
            result = verify_g14_unsat_cover_with_lean(instance.formula, cert)
        self.assertFalse(result["verified"])
        gate.assert_not_called()


    def test_cli_lean_rejection_returns_failure(self):
        from witnora_core.separator_affine_family_theorem import main
        payload = json.dumps(self.certificate.to_dict())
        with patch("witnora_core.separator_affine_family_theorem.load_dimacs",
                   return_value=self.instance.formula):
            with patch("witnora_core.separator_affine_family_theorem._load_json",
                       return_value=json.loads(payload)):
                with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean",
                           return_value={"verified": False}) as gate:
                    output = io.StringIO()
                    with redirect_stdout(output):
                        code = main(["check", "--cnf", "ignored.cnf",
                                     "--certificate", "ignored.json", "--lean"])
        self.assertEqual(code, 1)
        self.assertFalse(json.loads(output.getvalue())["lean_cover_check"]["verified"])
        gate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
