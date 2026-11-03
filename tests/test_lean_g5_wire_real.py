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


if __name__ == "__main__":
    unittest.main()
