"""Fail-closed boundaries of the compressed-G14 source proof gate."""
import unittest
from unittest.mock import patch

from witnora_core.cnf import CNFFormula
from witnora_core.lean_compressed_g14_gate import verify_compressed_g14_with_lean


class CompressedG14GateTests(unittest.TestCase):
    def setUp(self):
        self.formula = CNFFormula.from_raw_clauses([[1], [-1]])
        self.kw = dict(
            raw_clauses=self.formula.to_clause_lists(),
            source_tokens=[1, 0, -1, 0],
            source_spellings=["1", "0", "-1", "0"],
            source_text=self.formula.canonical_dimacs(),
        )

    def test_source_rejection_blocks_g14(self):
        with patch(
            "witnora_core.lean_compressed_g14_gate.verify_parity_compression_with_lean",
            return_value={"verified": False},
        ), patch(
            "witnora_core.lean_compressed_g14_gate.verify_g14_unsat_cover_with_lean",
        ) as g14:
            result = verify_compressed_g14_with_lean(self.formula, {}, **self.kw)
        self.assertFalse(result["verified"])
        self.assertEqual(result["lean_formal_status"], "NOT_LEAN_VERIFIED")
        g14.assert_not_called()

    def test_non_ascii_document_rejected_before_lean(self):
        with patch(
            "witnora_core.lean_compressed_g14_gate.verify_parity_compression_with_lean",
        ) as compression:
            result = verify_compressed_g14_with_lean(
                self.formula, {}, **dict(self.kw, source_text="λ"))
        self.assertFalse(result["verified"])
        compression.assert_not_called()

    def test_g14_rejection_does_not_promote_unsat(self):
        candidate = {
            "verified": True,
            "residual_formula_sha256": self.formula.formula_hash,
        }
        with patch(
            "witnora_core.lean_compressed_g14_gate.verify_parity_compression_with_lean",
            return_value=candidate,
        ), patch(
            "witnora_core.lean_compressed_g14_gate.verify_g14_unsat_cover_with_lean",
            return_value={"verified": False},
        ):
            result = verify_compressed_g14_with_lean(self.formula, {}, **self.kw)
        self.assertFalse(result["verified"])
        self.assertNotEqual(result.get("original_unsat_kernel_verified"), True)


if __name__ == "__main__":
    unittest.main()
