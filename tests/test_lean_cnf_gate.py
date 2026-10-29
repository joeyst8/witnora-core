"""Fail-closed tests for actual Python-to-Lean CNF normalization checks."""
import subprocess
import unittest
from pathlib import Path
from unittest.mock import patch

from witnora_core.lean_cnf_gate import verify_cnf_normalization_with_lean


class LeanCNFNormalizationGateTest(unittest.TestCase):
    def test_emits_fixed_exact_equality_and_binds_input_hash(self):
        def inspect_run(argv, **kwargs):
            self.assertEqual(argv[:3], ["lake", "env", "lean"])
            source = Path(argv[3]).read_text(encoding="utf-8")
            self.assertIn("Witnora.CNFSorted.canonicalize", source)
            self.assertIn("Witnora.SignedSerialization.decodeCNF", source)
            self.assertIn(":= by decide", source)
            self.assertNotIn("sorry", source)
            return subprocess.CompletedProcess(argv, 0, "", "")

        raw = [[1, 1, -2], [1, -1], [1, 1, -2], []]
        with patch("witnora_core.lean_cnf_gate.subprocess.run", side_effect=inspect_run):
            result = verify_cnf_normalization_with_lean(raw)
        self.assertTrue(result["verified"])
        self.assertEqual(result["lean_formal_status"], "LEAN_CNF_NORMALIZATION_VERIFIED")
        self.assertEqual(len(result["input_sha256"]), 64)

    def test_token_stream_lean_contract_is_mandatory_when_present(self):
        def inspect_run(argv, **kwargs):
            source = Path(argv[3]).read_text(encoding="utf-8")
            self.assertIn("import Witnora.DIMACSTokens", source)
            self.assertIn("Witnora.DIMACSTokens.checkStream", source)
            return subprocess.CompletedProcess(argv, 0, "", "")
        with patch("witnora_core.lean_cnf_gate.subprocess.run", side_effect=inspect_run):
            accepted = verify_cnf_normalization_with_lean(
                [[1, 1], [-2], []], source_tokens=[1, 1, 0, -2, 0, 0],
            )
        self.assertTrue(accepted["verified"])
        self.assertTrue(accepted["token_stream_verified"])

    def test_original_ascii_decimal_spelling_checked_by_lean(self):
        def inspect_run(argv, **kwargs):
            source = Path(argv[3]).read_text(encoding="utf-8")
            self.assertIn("Witnora.DIMACSLexemes.checkLexemes", source)
            self.assertIn("[[49], [48], [45, 50], [48]]", source)
            return subprocess.CompletedProcess(argv, 0, "", "")
        with patch("witnora_core.lean_cnf_gate.subprocess.run", side_effect=inspect_run):
            result = verify_cnf_normalization_with_lean(
                [[1], [-2]], source_tokens=[1, 0, -2, 0],
                source_spellings=["1", "0", "-2", "0"],
            )
        self.assertTrue(result["verified"])
        self.assertTrue(result["decimal_lexemes_verified"])

    def test_complete_source_document_is_checked_in_lean(self):
        document = "c source comment\\r\\np cnf 2 2\\r\\n1 0\\r\\n-2 0\\r\\n"
        def inspect_run(argv, **kwargs):
            source = Path(argv[3]).read_text(encoding="utf-8")
            self.assertIn("import Witnora.DIMACSDocument", source)
            self.assertIn("Witnora.DIMACSDocument.checkDocument", source)
            self.assertIn("[99, 32, 115, 111, 117", source)
            return subprocess.CompletedProcess(argv, 0, "", "")
        with patch("witnora_core.lean_cnf_gate.subprocess.run", side_effect=inspect_run):
            result = verify_cnf_normalization_with_lean(
                [[1], [-2]], source_tokens=[1, 0, -2, 0],
                source_spellings=["1", "0", "-2", "0"],
                source_text=document,
            )
        self.assertTrue(result["verified"])
        self.assertTrue(result["source_document_verified"])

    def test_non_ascii_document_rejected_before_launch(self):
        with patch("witnora_core.lean_cnf_gate.subprocess.run") as runner:
            result = verify_cnf_normalization_with_lean(
                [[1]], source_tokens=[1, 0], source_spellings=["1", "0"],
                source_text="p cnf 1 1\\n1 0\\n\\u00e9",
            )
        self.assertFalse(result["verified"])
        runner.assert_not_called()

    def test_unsupported_decimal_spellings_fail_closed(self):
        for spelling in ("+1", "01", "1_0", "a", "\\u0661"):
            with self.subTest(spelling=spelling):
                with patch("witnora_core.lean_cnf_gate.subprocess.run") as runner:
                    result = verify_cnf_normalization_with_lean(
                        [[1]], source_tokens=[1, 0],
                        source_spellings=[spelling, "0"],
                    )
                self.assertFalse(result["verified"])
                runner.assert_not_called()

    def test_invalid_token_types_rejected_before_lean(self):
        for tokens in ([1, True, 0], [1, "0"], [1.0, 0]):
            with self.subTest(tokens=tokens):
                with patch("witnora_core.lean_cnf_gate.subprocess.run") as runner:
                    result = verify_cnf_normalization_with_lean(
                        [[1]], source_tokens=tokens,
                    )
                self.assertFalse(result["verified"])
                runner.assert_not_called()

    def test_lean_rejects_altered_output(self):
        with patch(
            "witnora_core.lean_cnf_gate.subprocess.run",
            return_value=subprocess.CompletedProcess([], 1, "", "error"),
        ):
            result = verify_cnf_normalization_with_lean([[1]], [[-1]])
        self.assertFalse(result["verified"])

    def test_missing_lean_fails_closed(self):
        with patch("witnora_core.lean_cnf_gate.subprocess.run", side_effect=FileNotFoundError):
            result = verify_cnf_normalization_with_lean([[1]])
        self.assertFalse(result["verified"])

    def test_malformed_literals_fail_before_launch(self):
        for input_rows in ([[1, -1, True]], [[1, -1, 0]],
                           [[1, -1, "invalid"]], [[1, -1, 2.0]]):
            with self.subTest(input_rows=input_rows):
                with patch("witnora_core.lean_cnf_gate.subprocess.run") as runner:
                    result = verify_cnf_normalization_with_lean(input_rows)
                self.assertFalse(result["verified"])
                runner.assert_not_called()

    def test_malformed_proposed_output_fails_before_launch(self):
        with patch("witnora_core.lean_cnf_gate.subprocess.run") as runner:
            result = verify_cnf_normalization_with_lean([[1]], [[True]])
        self.assertFalse(result["verified"])
        runner.assert_not_called()

    def test_missing_project_fails_closed(self):
        result = verify_cnf_normalization_with_lean([[1]], project_root=Path("/nonexistent_witnora"))
        self.assertFalse(result["verified"])


if __name__ == "__main__":
    unittest.main()
