"""Fail-closed integration tests for source-bound parity residual gate."""
import subprocess
from pathlib import Path
import unittest
from unittest.mock import patch

from witnora_core.cnf import CNFFormula
from witnora_core.lean_parity_compression_gate import verify_parity_compression_with_lean
from witnora_core.xor import canonical_xor_cnf_clauses


def example_formula():
    clauses = set()
    for u, v, rhs in ((1, 2, 0), (2, 3, 1)):
        clauses.update(canonical_xor_cnf_clauses((u, v), rhs))
    clauses.add((3, 4, -5))
    return CNFFormula.from_raw_clauses(clauses)


class CompressionGateTest(unittest.TestCase):
    def setUp(self):
        self.formula = example_formula()
        self.raw = self.formula.to_clause_lists()
        self.tokens = [v for row in self.raw for v in (*row, 0)]
        self.data = dict(
            raw_clauses=self.raw, source_tokens=self.tokens,
            source_spellings=list(map(str, self.tokens)),
            source_text=self.formula.canonical_dimacs(),
        )

    def test_real_proof_shape_with_mocked_process(self):
        normalization = {
            "verified": True, "source_document_verified": True,
            "token_stream_verified": True, "decimal_lexemes_verified": True,
        }
        def inspect(argv, **kwargs):
            text = Path(argv[3]).read_text(encoding="utf-8")
            self.assertIn("ValidSourcePaths", text)
            self.assertIn("source_iff_rewritten_residual", text)
            self.assertIn("substituteCNF", text)
            self.assertIn("parseDocument", text)
            self.assertNotIn("sorry", text)
            return subprocess.CompletedProcess(argv, 0, "", "")
        with patch("witnora_core.lean_parity_compression_gate.verify_cnf_normalization_with_lean",
                   return_value=normalization), patch(
                       "witnora_core.lean_parity_compression_gate.subprocess.run",
                       side_effect=inspect):
            proof = verify_parity_compression_with_lean(self.formula, **self.data)
        self.assertTrue(proof["verified"], proof)
        self.assertEqual(proof["root_variables_saved"], 2)

    def test_rejects_source_normalization_failure(self):
        with patch("witnora_core.lean_parity_compression_gate.verify_cnf_normalization_with_lean",
                   return_value={"verified": False}), patch(
                       "witnora_core.lean_parity_compression_gate.subprocess.run") as lean:
            result = verify_parity_compression_with_lean(self.formula, **self.data)
        self.assertFalse(result["verified"])
        lean.assert_not_called()

    def test_rejects_kernel_failure(self):
        normalization = {
            "verified": True, "source_document_verified": True,
            "token_stream_verified": True, "decimal_lexemes_verified": True,
        }
        with patch("witnora_core.lean_parity_compression_gate.verify_cnf_normalization_with_lean",
                   return_value=normalization), patch(
                       "witnora_core.lean_parity_compression_gate.subprocess.run",
                       return_value=subprocess.CompletedProcess([], 1, "", "rejected")):
            result = verify_parity_compression_with_lean(self.formula, **self.data)
        self.assertFalse(result["verified"])

    def test_rejects_unverified_source_document(self):
        wrong = dict(self.data, source_text=self.data["source_text"].replace("p cnf", "p cna"))
        result = verify_parity_compression_with_lean(self.formula, **wrong)
        self.assertFalse(result["verified"])



    def test_optional_g5_requires_accepted_residual_certificate(self):
        normalization = {
            "verified": True, "source_document_verified": True,
            "token_stream_verified": True, "decimal_lexemes_verified": True,
        }
        with patch("witnora_core.lean_parity_compression_gate.verify_cnf_normalization_with_lean",
                   return_value=normalization), patch(
                       "witnora_core.lean_parity_compression_gate.verify_g5_certificate_with_lean",
                       return_value={"verified": False}) as g5:
            result = verify_parity_compression_with_lean(
                self.formula, residual_g5_certificate={"fake": "certificate"},
                **self.data)
        self.assertFalse(result["verified"])
        g5.assert_called_once()

if __name__ == "__main__":
    unittest.main()
