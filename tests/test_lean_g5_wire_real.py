"""Real Lean smoke test for the source-G5 numeric-wire acceptance gate.

This test invokes both production Python certificate generation and the
actual Lean executable checker, not a mocked subprocess.
"""
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.lean_g5_gate import verify_g5_certificate_with_lean
from witnora_core.operator_genesis import (
    AffineResidueInstance,
    build_affine_residue_certificate,
)


class G5WireRealLeanTest(unittest.TestCase):
    def test_small_conflicting_unit_rows_reach_lean_verified(self):
        formula = CNFFormula.from_raw_clauses([[1], [-1]])
        instance = AffineResidueInstance(
            instance_id="tc063_wire_codec_small_unsat",
            equations=(),
            formula=formula,
        )
        cert = build_affine_residue_certificate(instance, max_arity=2)
        result = verify_g5_certificate_with_lean(
            formula,
            cert,
            max_arity=2,
            timeout_seconds=120,
            use_sparse_checker=True,
        )
        self.assertTrue(result.get("verified"), result)
        self.assertEqual(result["lean_formal_status"], "LEAN_VERIFIED")


    def test_overlapping_affine_source_document_reaches_lean_verified(self):
        """Exercise exact DIMACS bytes, overlapping XOR extraction and indexed G5."""
        from pathlib import Path
        from witnora_core.dimacs import load_dimacs_with_document_evidence

        fixture = Path(__file__).resolve().parents[1] / "fixtures" / "tc063_three_row_affine_unsat.cnf"
        formula, raw, tokens, spellings, source = load_dimacs_with_document_evidence(fixture)
        self.assertEqual(formula.num_clauses, 10)
        instance = AffineResidueInstance(
            instance_id="tc063_three_row_affine_source_unsat",
            equations=(),
            formula=formula,
        )
        cert = build_affine_residue_certificate(instance, max_arity=3)
        self.assertEqual(cert.status, "AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED")
        self.assertEqual(len(cert.equations), 3)
        self.assertGreaterEqual(len(cert.row_operations), 2)

        result = verify_g5_certificate_with_lean(
            formula,
            cert,
            max_arity=3,
            timeout_seconds=180,
            raw_clauses=raw,
            source_tokens=tokens,
            source_spellings=spellings,
            source_text=source,
        )
        self.assertTrue(result.get("verified"), result)
        self.assertEqual(result["lean_formal_status"], "LEAN_VERIFIED")
        self.assertTrue(result["source_document_verified"], result)
        self.assertTrue(result["source_lexemes_verified"], result)
        self.assertTrue(result["source_normalization_verified"], result)

if __name__ == "__main__":
    unittest.main()
