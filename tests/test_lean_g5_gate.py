"""Fail-closed production Lean G5 gate tests."""
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from witnora_core.lean_g5_gate import verify_g5_certificate_with_lean
from witnora_core.operator_genesis import (
    build_affine_residue_certificate,
    make_affine_residue_instance,
)


class G5LeanGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.instance = make_affine_residue_instance("parity_arity_7_unsat")
        cls.cert = build_affine_residue_certificate(cls.instance)

    def test_gate_emits_fixed_closed_checker_and_binds_hash(self):
        def inspect_run(argv, **kwargs):
            self.assertEqual(argv[:3], ["lake", "env", "lean"])
            source = Path(argv[3]).read_text(encoding="utf-8")
            self.assertIn("Witnora.SparseBridge.checkG5Closed", source)
            self.assertIn("= true := by decide", source)
            self.assertNotIn("isUnsat", source)
            self.assertNotIn("sorry", source)
            return subprocess.CompletedProcess(argv, 0, "", "")

        with patch("witnora_core.lean_g5_gate.subprocess.run", side_effect=inspect_run):
            result = verify_g5_certificate_with_lean(self.instance.formula, self.cert)
        self.assertTrue(result["verified"])
        self.assertEqual(result["lean_formal_status"], "LEAN_VERIFIED")
        self.assertEqual(len(result["input_sha256"]), 64)

    def test_lean_unavailable_is_not_verified(self):
        with patch("witnora_core.lean_g5_gate.subprocess.run", side_effect=FileNotFoundError):
            result = verify_g5_certificate_with_lean(self.instance.formula, self.cert)
        self.assertFalse(result["verified"])
        self.assertEqual(result["lean_formal_status"], "NOT_LEAN_VERIFIED")

    def test_lean_rejection_is_not_verified(self):
        with patch("witnora_core.lean_g5_gate.subprocess.run",
                   return_value=subprocess.CompletedProcess([], 1, "", "error")):
            result = verify_g5_certificate_with_lean(self.instance.formula, self.cert)
        self.assertFalse(result["verified"])

    def test_forged_verification_claim_is_rejected(self):
        forged = self.cert.to_dict()
        forged["lean_formal_status"] = "LEAN_VERIFIED"
        with patch("witnora_core.lean_g5_gate.subprocess.run") as runner:
            result = verify_g5_certificate_with_lean(self.instance.formula, forged)
        self.assertFalse(result["verified"])
        runner.assert_not_called()

    def test_modified_cnf_hash_is_rejected(self):
        forged = self.cert.to_dict()
        forged["formula_hash"] = "0" * 64
        with patch("witnora_core.lean_g5_gate.subprocess.run") as runner:
            result = verify_g5_certificate_with_lean(self.instance.formula, forged)
        self.assertFalse(result["verified"])
        runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
