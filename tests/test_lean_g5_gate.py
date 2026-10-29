"""Fail-closed production Lean G5 gate tests."""
import subprocess
import json
import io
from contextlib import redirect_stdout
import unittest
from pathlib import Path
from unittest.mock import patch

from witnora_core.lean_g5_gate import verify_g5_certificate_with_lean
from witnora_core.operator_genesis import (
    build_affine_residue_certificate,
    make_affine_residue_instance,
)


class G5LeanGateTest(unittest.TestCase):
    def setUp(self):
        patcher = patch(
            "witnora_core.lean_g5_gate.verify_cnf_normalization_with_lean",
            return_value={"verified": True,
                          "lean_formal_status": "LEAN_CNF_NORMALIZATION_VERIFIED"},
        )
        self.normalization_gate = patcher.start()
        self.addCleanup(patcher.stop)

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
        self.assertTrue(result["normalization_check"]["verified"])
        self.assertEqual(len(result["input_sha256"]), 64)

    def test_normalization_rejection_blocks_g5_proof(self):
        self.normalization_gate.return_value = {
            "verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED",
        }
        with patch("witnora_core.lean_g5_gate.subprocess.run") as runner:
            result = verify_g5_certificate_with_lean(self.instance.formula, self.cert)
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "CNF_NORMALIZATION_REJECTED")
        runner.assert_not_called()
        self.normalization_gate.assert_called_once()

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


    def test_cli_lean_mode_fails_closed_and_reports_separate_statuses(self):
        from witnora_core.operator_genesis import main
        certificate_json = json.dumps(self.cert.to_dict())
        with patch("witnora_core.operator_genesis.load_dimacs_with_raw", return_value=(self.instance.formula, [[1, 1, -1], [2, -2]])):
            with patch("pathlib.Path.read_text", return_value=certificate_json):
                with patch("witnora_core.lean_g5_gate.verify_g5_certificate_with_lean",
                           return_value={"verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED"}) as gate:
                    output = io.StringIO()
                    with redirect_stdout(output):
                        code = main(["check-affine-residue-cert", "--cnf", "ignored.cnf",
                                     "--certificate", "ignored.json", "--lean"])
        self.assertEqual(code, 1)
        payload = json.loads(output.getvalue())
        self.assertEqual(payload["native_check"]["status"], "AFFINE_RESIDUE_CERTIFICATE_VERIFIED")
        self.assertFalse(payload["lean_check"]["verified"])
        gate.assert_called_once()
        self.assertEqual(gate.call_args.kwargs["raw_clauses"], [[1, 1, -1], [2, -2]])

    def test_cli_lean_mode_accepts_only_gate_success(self):
        from witnora_core.operator_genesis import main
        certificate_json = json.dumps(self.cert.to_dict())
        with patch("witnora_core.operator_genesis.load_dimacs_with_raw", return_value=(self.instance.formula, [[1, -1]])):
            with patch("pathlib.Path.read_text", return_value=certificate_json):
                with patch("witnora_core.lean_g5_gate.verify_g5_certificate_with_lean",
                           return_value={"verified": True, "lean_formal_status": "LEAN_VERIFIED"}):
                    output = io.StringIO()
                    with redirect_stdout(output):
                        code = main(["check-affine-residue-cert", "--cnf", "ignored.cnf",
                                     "--certificate", "ignored.json", "--lean"])
        self.assertEqual(code, 0)
        payload = json.loads(output.getvalue())
        self.assertTrue(payload["lean_check"]["verified"])

    def test_raw_provenance_is_forwarded_to_lean(self):
        raw = [[2, 2, 1], [1, -1]]
        with patch("witnora_core.lean_g5_gate.subprocess.run",
                   return_value=subprocess.CompletedProcess([], 0, "", "")):
            result = verify_g5_certificate_with_lean(
                self.instance.formula, self.cert, raw_clauses=raw,
            )
        self.assertTrue(result["verified"])
        self.assertTrue(result["source_normalization_verified"])
        self.assertEqual(self.normalization_gate.call_args.args[0], raw)
        self.assertEqual(self.normalization_gate.call_args.args[1],
                         self.instance.formula.to_clause_lists())

    def test_raw_source_compiles_source_level_g5_claim(self):
        raw = self.instance.formula.to_clause_lists()
        def inspect_run(argv, **kwargs):
            source = Path(argv[3]).read_text(encoding="utf-8")
            self.assertIn("import Witnora.SourceG5", source)
            self.assertIn("Witnora.SourceG5.checkRawG5", source)
            self.assertNotIn("example : Witnora.SparseBridge.checkG5Closed", source)
            return subprocess.CompletedProcess(argv, 0, "", "")
        with patch("witnora_core.lean_g5_gate.subprocess.run", side_effect=inspect_run):
            result = verify_g5_certificate_with_lean(
                self.instance.formula, self.cert, raw_clauses=raw,
            )
        self.assertTrue(result["verified"])
        self.assertTrue(result["source_normalization_verified"])

    def test_attestation_digest_binds_raw_source(self):
        with patch("witnora_core.lean_g5_gate.subprocess.run",
                   return_value=subprocess.CompletedProcess([], 0, "", "")):
            a = verify_g5_certificate_with_lean(
                self.instance.formula, self.cert, raw_clauses=[[1]])
            b = verify_g5_certificate_with_lean(
                self.instance.formula, self.cert, raw_clauses=[[2]])
        self.assertTrue(a["verified"])
        self.assertEqual(a["source_formula_hash"], self.instance.formula.formula_hash)
        self.assertNotEqual(a["input_sha256"], b["input_sha256"])

    def test_bad_raw_provenance_fails_closed(self):
        self.normalization_gate.return_value = {"verified": False}
        with patch("witnora_core.lean_g5_gate.subprocess.run") as runner:
            result = verify_g5_certificate_with_lean(
                self.instance.formula, self.cert, raw_clauses=[[999]],
            )
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "CNF_NORMALIZATION_REJECTED")
        runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
