"""Operator-promotion policy tests; no forged Lean status may promote research."""
import unittest
from unittest.mock import patch

from witnora_core.operator_promotion import (
    CANDIDATE_ONLY, NO_DISCOVERY, PROOF_REJECTED, PROOF_VERIFIED,
    assess_parity_spoke_operator,
)
from witnora_core.spoke_collapse import make_spoke_family


class OperatorPromotionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.unsat, _ = make_spoke_family(3, contradictory=True)
        cls.sat, _ = make_spoke_family(3, contradictory=False)
        cls.raw = cls.unsat.to_clause_lists()
        cls.tokens = [v for clause in cls.raw for v in (*clause, 0)]
        cls.spellings = list(map(str, cls.tokens))
        cls.source = cls.unsat.canonical_dimacs()

    def call(self, cert=None):
        return assess_parity_spoke_operator(
            self.unsat, cert,
            raw_clauses=self.raw, source_tokens=self.tokens,
            source_spellings=self.spellings, source_text=self.source,
        )

    def test_no_discovery_never_invokes_lean(self):
        with patch("witnora_core.operator_promotion.verify_g5_certificate_with_lean") as gate:
            result = assess_parity_spoke_operator(self.sat)
        self.assertEqual(result["status"], NO_DISCOVERY)
        self.assertFalse(result["promoted"])
        gate.assert_not_called()

    def test_missing_document_proof_never_invokes_lean(self):
        with patch("witnora_core.operator_promotion.verify_g5_certificate_with_lean") as gate:
            result = assess_parity_spoke_operator(self.unsat, {"fake": "proof"})
        self.assertEqual(result["status"], CANDIDATE_ONLY)
        self.assertFalse(result["promoted"])
        gate.assert_not_called()

    def test_forged_status_without_document_attestation_rejected(self):
        fake = {
            "verified": True, "lean_formal_status": "LEAN_VERIFIED",
            "normalization_check": {"verified": True},
        }
        with patch("witnora_core.operator_promotion.verify_g5_certificate_with_lean",
                   return_value=fake):
            result = self.call({"fake": "proof"})
        self.assertEqual(result["status"], PROOF_REJECTED)
        self.assertFalse(result["promoted"])

    def test_failed_proof_rejected(self):
        with patch("witnora_core.operator_promotion.verify_g5_certificate_with_lean",
                   return_value={"verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED"}):
            result = self.call({"fake": "proof"})
        self.assertEqual(result["status"], PROOF_REJECTED)

    def test_full_acceptance_only_proves_instance_not_promotion(self):
        accepted = {
            "verified": True, "lean_formal_status": "LEAN_VERIFIED",
            "source_document_verified": True,
            "source_normalization_verified": True,
            "source_tokens_verified": True,
            "source_lexemes_verified": True,
            "normalization_check": {"verified": True},
            "proof_source_sha256": "a" * 64,
            "input_sha256": "b" * 64,
        }
        with patch("witnora_core.operator_promotion.verify_g5_certificate_with_lean",
                   return_value=accepted) as gate:
            result = self.call({"fake": "proof"})
        self.assertEqual(result["status"], PROOF_VERIFIED)
        self.assertFalse(result["promoted"])
        self.assertFalse(result["novelty_verified"])
        self.assertFalse(result["performance_advantage_verified"])
        self.assertEqual(gate.call_args.kwargs["source_text"], self.source)
        self.assertEqual(gate.call_args.kwargs["raw_clauses"], self.raw)

    def test_caller_provided_promotion_claim_ignored(self):
        forged = {"promoted": True, "lean_formal_status": "LEAN_VERIFIED"}
        with patch("witnora_core.operator_promotion.verify_g5_certificate_with_lean",
                   return_value={"verified": False}) as gate:
            result = self.call(forged)
        self.assertEqual(result["status"], PROOF_REJECTED)
        self.assertFalse(result["promoted"])
        gate.assert_called_once()


if __name__ == "__main__":
    unittest.main()
