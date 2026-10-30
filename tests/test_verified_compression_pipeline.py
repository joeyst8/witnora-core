"""Fail-closed checks for opt-in verified compression solve path."""
from hashlib import sha256
import json
import unittest
from unittest.mock import patch

from witnora_core.cnf import CNFFormula, formula_satisfied
from witnora_core.parity_compression import (
    compress_binary_xor_components, substitute_residual_formula,
)
from witnora_core.verified_compression_pipeline import solve_with_verified_compression
from witnora_core.xor import canonical_xor_cnf_clauses


class CompressionPipelineTest(unittest.TestCase):
    def setUp(self):
        clauses = set()
        for u, v, rhs in ((1, 2, 0), (2, 3, 1)):
            clauses.update(canonical_xor_cnf_clauses((u, v), rhs))
        clauses.add((3,))
        self.formula = CNFFormula.from_raw_clauses(clauses)
        raw = self.formula.to_clause_lists()
        tokens = [v for row in raw for v in (*row, 0)]
        self.source = dict(
            raw_clauses=raw, source_tokens=tokens,
            source_spellings=list(map(str, tokens)),
            source_text=self.formula.canonical_dimacs(),
        )
        cert = compress_binary_xor_components(self.formula)
        residual = substitute_residual_formula(self.formula, cert)
        self.gate = {
            "verified": True,
            "lean_formal_status": "LEAN_SOURCE_PARITY_RESIDUAL_EQUIVALENT",
            "proof_source_sha256": "a" * 64,
            "residual_formula_sha256": residual.formula_hash,
            "component_certificate_sha256": sha256(
                json.dumps(cert, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
        }

    def test_rejected_proof_uses_original_formula(self):
        with patch("witnora_core.verified_compression_pipeline.verify_parity_compression_with_lean",
                   return_value={"verified": False}), patch(
                       "witnora_core.verified_compression_pipeline._glucose",
                       return_value={"status": "SAT_MODEL_CHECKED", "assignment": {}}) as solver:
            result = solve_with_verified_compression(self.formula, **self.source)
        self.assertFalse(result["used_compression"])
        self.assertFalse(result["compression_proof_verified"])
        solver.assert_called_once_with(self.formula)

    def test_changed_residual_is_never_used(self):
        bad = dict(self.gate, residual_formula_sha256="0" * 64)
        with patch("witnora_core.verified_compression_pipeline.verify_parity_compression_with_lean",
                   return_value=bad), patch(
                       "witnora_core.verified_compression_pipeline._glucose",
                       return_value={"status": "UNSAT_SOLVER_REPORTED", "assignment": {}}) as solver:
            result = solve_with_verified_compression(self.formula, **self.source)
        self.assertFalse(result["used_compression"])
        self.assertEqual(result["reason"], "POST_GATE_CERTIFICATE_MISMATCH")
        solver.assert_called_once_with(self.formula)

    def test_unproved_unsat_stays_unverified(self):
        with patch("witnora_core.verified_compression_pipeline.verify_parity_compression_with_lean",
                   return_value=self.gate), patch(
                       "witnora_core.verified_compression_pipeline._glucose",
                       return_value={"status": "UNSAT_SOLVER_REPORTED", "assignment": {}}):
            result = solve_with_verified_compression(self.formula, **self.source)
        self.assertTrue(result["used_compression"])
        self.assertFalse(result["unsat_kernel_verified"])

    def test_real_sat_assignment_is_lifted_and_checked(self):
        from itertools import product
        cert = compress_binary_xor_components(self.formula)
        residual = substitute_residual_formula(self.formula, cert)
        model = None
        for values in product((False, True), repeat=len(residual.variables)):
            assignment = dict(zip(residual.variables, values))
            if formula_satisfied(residual, assignment):
                model = assignment
                break
        self.assertIsNotNone(model)
        with patch("witnora_core.verified_compression_pipeline.verify_parity_compression_with_lean",
                   return_value=self.gate), patch(
                       "witnora_core.verified_compression_pipeline._glucose",
                       return_value={"status": "SAT_MODEL_CHECKED", "assignment": model}):
            result = solve_with_verified_compression(self.formula, **self.source)
        self.assertTrue(result["used_compression"])
        self.assertTrue(formula_satisfied(self.formula, result["assignment"]))
        self.assertFalse(result["unsat_kernel_verified"])


if __name__ == "__main__":
    unittest.main()
