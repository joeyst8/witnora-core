"""Branch coverage and fail-closed tests for the G14-to-G5 Lean gate."""

import unittest
import subprocess
import io
import json
from pathlib import Path
from contextlib import redirect_stdout
from unittest.mock import patch

from witnora_core.lean_g14_gate import verify_g14_unsat_cover_with_lean
from witnora_core.separator_affine_family_theorem import (
    build_separator_affine_certificate, make_separator_affine_instance,
)


class G14LeanCoverGateTest(unittest.TestCase):
    def setUp(self):
        patcher = patch(
            "witnora_core.lean_g14_gate.subprocess.run",
            return_value=subprocess.CompletedProcess([], 0, "", ""),
        )
        self.partition_runner = patcher.start()
        self.addCleanup(patcher.stop)
        normalization_patcher = patch(
            "witnora_core.lean_g14_gate.verify_cnf_normalization_with_lean",
            return_value={"verified": True,
                          "lean_formal_status": "LEAN_CNF_NORMALIZATION_VERIFIED"},
        )
        self.normalization_gate = normalization_patcher.start()
        self.addCleanup(normalization_patcher.stop)

    @classmethod
    def setUpClass(cls):
        cls.instance = make_separator_affine_instance("saf_unsat_cover_2")
        cls.certificate = build_separator_affine_certificate(cls.instance)

    def test_every_separator_branch_requires_lean_g5(self):
        accepted = {"verified": True, "lean_formal_status": "LEAN_VERIFIED",
                    "normalization_check": {"verified": True}}
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean",
                   return_value=accepted) as gate:
            result = verify_g14_unsat_cover_with_lean(
                self.instance.formula, self.certificate,
            )
        self.assertTrue(result["verified"])
        self.assertEqual(result["lean_formal_status"], "LEAN_G5_COVER_AND_PARTITIONS_VERIFIED")
        self.assertTrue(result["normalization_check"]["verified"])
        self.partition_runner.assert_called_once()
        self.assertEqual(gate.call_count, 2)
        self.assertEqual([b["assignment_id"] for b in result["branches"]], ["S1", "S2"])


    def test_full_source_requires_one_combined_lean_theorem(self):
        accepted = {"verified": True, "lean_formal_status": "LEAN_VERIFIED",
                    "normalization_check": {"verified": True}}
        raw = self.instance.formula.to_clause_lists()
        source = self.instance.formula.canonical_dimacs()
        tokens = [item for clause in raw for item in (*clause, 0)]
        spellings = [str(item) for item in tokens]
        captured = []
        def inspect_lean(argv, **kwargs):
            path = Path(argv[3])
            source_code = path.read_text(encoding="utf-8")
            if path.name == "G14CompleteSourceProof.lean":
                self.assertIn("checked_ascii_dimacs_g14_canonical_unsat", source_code)
                self.assertNotIn(chr(92) + "n", source_code)
                captured.append(source_code)
            return subprocess.CompletedProcess(argv, 0, "", "")
        self.partition_runner.side_effect = inspect_lean
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean",
                   return_value=accepted):
            result = verify_g14_unsat_cover_with_lean(
                self.instance.formula, self.certificate,
                raw_clauses=raw, source_tokens=tokens,
                source_spellings=spellings, source_text=source,
            )
        self.assertEqual(len(captured), 1)
        self.assertTrue(result["verified"], result)
        self.assertEqual(result["lean_formal_status"],
                         "LEAN_END_TO_END_G14_UNSAT_VERIFIED")
        self.assertEqual(self.partition_runner.call_count, 2)
        generated = self.partition_runner.call_args.args[0][3]
        self.assertIn("G14CompleteSourceProof.lean", generated)
        self.assertEqual(len(result["complete_proof_source_sha256"]), 64)

    def test_full_source_combined_lean_rejection_fails_closed(self):
        accepted = {"verified": True, "lean_formal_status": "LEAN_VERIFIED",
                    "normalization_check": {"verified": True}}
        raw = self.instance.formula.to_clause_lists()
        source = self.instance.formula.canonical_dimacs()
        tokens = [item for clause in raw for item in (*clause, 0)]
        spellings = [str(item) for item in tokens]
        self.partition_runner.side_effect = [
            subprocess.CompletedProcess([], 0, "", ""),
            subprocess.CompletedProcess([], 1, "", "rejected"),
        ]
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean",
                   return_value=accepted):
            result = verify_g14_unsat_cover_with_lean(
                self.instance.formula, self.certificate,
                raw_clauses=raw, source_tokens=tokens,
                source_spellings=spellings, source_text=source,
            )
        self.assertFalse(result["verified"])
        self.assertEqual(result["lean_formal_status"], "NOT_LEAN_VERIFIED")

    def test_normalization_rejection_blocks_g14_before_partitions(self):
        self.normalization_gate.return_value = {
            "verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED",
        }
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean") as g5:
            result = verify_g14_unsat_cover_with_lean(
                self.instance.formula, self.certificate,
            )
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "CNF_NORMALIZATION_REJECTED")
        self.partition_runner.assert_not_called()
        g5.assert_not_called()

    def test_missing_branch_normalization_attestation_rejects_cover(self):
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean",
                   return_value={"verified": True, "lean_formal_status": "LEAN_VERIFIED"}) as g5:
            result = verify_g14_unsat_cover_with_lean(
                self.instance.formula, self.certificate,
            )
        self.assertFalse(result["verified"])
        self.assertEqual(result["reason"], "BRANCH_G5_LEAN_REJECTED")
        self.assertEqual(g5.call_count, 1)

    def test_lean_partition_rejection_stops_before_g5(self):
        self.partition_runner.return_value = subprocess.CompletedProcess([], 1, "", "error")
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean") as g5:
            result = verify_g14_unsat_cover_with_lean(
                self.instance.formula, self.certificate,
            )
        self.assertFalse(result["verified"])
        g5.assert_not_called()

    def test_single_failed_branch_rejects_cover(self):
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean",
                   side_effect=[
                       {"verified": True, "lean_formal_status": "LEAN_VERIFIED",
                        "normalization_check": {"verified": True}},
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

    def test_forged_g14_formal_status_is_rejected(self):
        data = self.certificate.to_dict()
        data["lean_formal_status"] = "LEAN_G5_COVER_AND_PARTITIONS_VERIFIED"
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean") as gate:
            result = verify_g14_unsat_cover_with_lean(self.instance.formula, data)
        self.assertFalse(result["verified"])
        self.assertEqual(result["lean_formal_status"], "NOT_LEAN_VERIFIED")
        gate.assert_not_called()

    def test_g14_digest_binds_raw_input(self):
        accepted = {"verified": True, "lean_formal_status": "LEAN_VERIFIED",
                    "normalization_check": {"verified": True}}
        with patch("witnora_core.lean_g14_gate.verify_g5_certificate_with_lean",
                   return_value=accepted):
            a = verify_g14_unsat_cover_with_lean(
                self.instance.formula, self.certificate, raw_clauses=[[1]])
            b = verify_g14_unsat_cover_with_lean(
                self.instance.formula, self.certificate, raw_clauses=[[2]])
        self.assertTrue(a["source_normalization_verified"])
        self.assertEqual(a["source_formula_hash"], self.instance.formula.formula_hash)
        self.assertNotEqual(a["input_sha256"], b["input_sha256"])

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
        with patch("witnora_core.separator_affine_family_theorem.load_dimacs_with_document_evidence",
                   return_value=(self.instance.formula, [[1, 1, -1], [2, -2]], [1, 1, -1, 0, 2, -2, 0], ["1", "1", "-1", "0", "2", "-2", "0"], "p cnf 2 2\n1 1 -1 0\n2 -2 0\n")):
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
