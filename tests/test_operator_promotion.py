"""Operator promotion policy: direct Lean spoke proof and fail-closed status."""
import unittest
from unittest.mock import patch

from witnora_core.operator_promotion import (
    CANDIDATE_ONLY, NO_DISCOVERY, PROOF_REJECTED, PROOF_VERIFIED,
    assess_parity_spoke_operator, assess_odd_cycle_operator,
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

    def setUp(self):
        self.norm = patch(
            "witnora_core.operator_promotion.verify_cnf_normalization_with_lean",
            return_value={
                "verified": True, "source_document_verified": True,
                "token_stream_verified": True, "decimal_lexemes_verified": True,
                "proof_source_sha256": "n" * 64,
            }).start()
        self.addCleanup(patch.stopall)
        self.spoke = patch(
            "witnora_core.operator_promotion.verify_discovered_spoke_with_lean",
            return_value={
                "verified": True,
                "lean_formal_status": "LEAN_SOURCE_SPOKE_UNSAT_VERIFIED",
                "proof_source_sha256": "s" * 64,
            }).start()

    def call(self, cert=None):
        return assess_parity_spoke_operator(
            self.unsat, cert, raw_clauses=self.raw,
            source_tokens=self.tokens, source_spellings=self.spellings,
            source_text=self.source,
        )

    def test_no_discovery_never_invokes_lean(self):
        result = assess_parity_spoke_operator(self.sat)
        self.assertEqual(result["status"], NO_DISCOVERY)
        self.assertFalse(result["promoted"])
        self.norm.assert_not_called()
        self.spoke.assert_not_called()

    def test_missing_original_document_never_invokes_lean(self):
        result = assess_parity_spoke_operator(self.unsat, {"fake": "proof"})
        self.assertEqual(result["status"], CANDIDATE_ONLY)
        self.assertFalse(result["promoted"])
        self.norm.assert_not_called()
        self.spoke.assert_not_called()

    def test_missing_normalization_attestation_rejected(self):
        self.norm.return_value = {"verified": True}
        result = self.call()
        self.assertEqual(result["status"], PROOF_REJECTED)
        self.assertFalse(result["promoted"])
        self.spoke.assert_not_called()

    def test_forged_status_without_source_spoke_acceptance_rejected(self):
        self.spoke.return_value = {
            "verified": True, "lean_formal_status": "LEAN_VERIFIED",
        }
        result = self.call()
        self.assertEqual(result["status"], PROOF_REJECTED)
        self.assertFalse(result["promoted"])

    def test_direct_proof_suffices_without_separate_g5_certificate(self):
        with patch("witnora_core.operator_promotion.verify_g5_certificate_with_lean") as g5:
            result = self.call()
        self.assertEqual(result["status"], PROOF_VERIFIED)
        self.assertFalse(result["promoted"])
        self.assertFalse(result["novelty_verified"])
        self.assertFalse(result["performance_advantage_verified"])
        self.assertEqual(self.spoke.call_args.kwargs["source_text"], self.source)
        self.assertEqual(self.norm.call_args.args[0], self.raw)
        g5.assert_not_called()

    def test_supplied_bad_g5_certificate_is_not_ignored(self):
        with patch("witnora_core.operator_promotion.verify_g5_certificate_with_lean",
                   return_value={"verified": False}) as g5:
            result = self.call({"fake": "proof"})
        self.assertEqual(result["status"], PROOF_REJECTED)
        self.assertEqual(result["reason"], "SUPPLIED_G5_CERTIFICATE_REJECTED")
        g5.assert_called_once()

    def test_supplied_g5_requires_real_source_attestation(self):
        with patch("witnora_core.operator_promotion.verify_g5_certificate_with_lean",
                   return_value={"verified": True,
                                 "lean_formal_status": "LEAN_VERIFIED"}) as g5:
            result = self.call({"fake": "proof"})
        self.assertEqual(result["status"], PROOF_REJECTED)
        g5.assert_called_once()

    def test_accepted_additional_g5_still_cannot_promote(self):
        with patch("witnora_core.operator_promotion.verify_g5_certificate_with_lean",
                   return_value={"verified": True,
                                 "lean_formal_status": "LEAN_VERIFIED",
                                 "source_document_verified": True}):
            result = self.call({"fake": "proof"})
        self.assertEqual(result["status"], PROOF_VERIFIED)
        self.assertFalse(result["promoted"])



class OddCyclePromotionTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from witnora_core.cnf import CNFFormula
        from witnora_core.xor import canonical_xor_cnf_clauses
        clauses = set()
        for u, v, rhs in ((1, 2, 0), (2, 3, 0), (1, 3, 1)):
            clauses.update(canonical_xor_cnf_clauses((u, v), rhs))
        cls.formula = CNFFormula.from_raw_clauses(clauses)
        cls.raw = cls.formula.to_clause_lists()
        cls.tokens = [x for row in cls.raw for x in (*row, 0)]
        cls.source = cls.formula.canonical_dimacs()

    def assess(self, **kwargs):
        args = dict(raw_clauses=self.raw, source_tokens=self.tokens,
                    source_spellings=list(map(str, self.tokens)),
                    source_text=self.source)
        args.update(kwargs)
        return assess_odd_cycle_operator(self.formula, **args)

    def test_missing_source_is_candidate_only(self):
        result = assess_odd_cycle_operator(self.formula)
        self.assertEqual(result["status"], CANDIDATE_ONLY)
        self.assertFalse(result["promoted"])

    def test_no_discovery(self):
        from witnora_core.cnf import CNFFormula
        f = CNFFormula.from_raw_clauses([[1, 2], [-1, 2]])
        result = assess_odd_cycle_operator(f)
        self.assertEqual(result["status"], NO_DISCOVERY)

    def test_normalization_attestation_must_be_complete(self):
        with patch("witnora_core.operator_promotion.verify_cnf_normalization_with_lean",
                   return_value={"verified": True}), patch(
                       "witnora_core.operator_promotion.verify_odd_cycle_with_lean") as gate:
            result = self.assess()
        self.assertEqual(result["status"], PROOF_REJECTED)
        self.assertEqual(result["reason"], "SOURCE_CANONICALIZATION_REJECTED")
        gate.assert_not_called()

    def test_forged_lean_status_is_rejected(self):
        with patch("witnora_core.operator_promotion.verify_cnf_normalization_with_lean",
                   return_value={"verified": True, "source_document_verified": True,
                                 "token_stream_verified": True,
                                 "decimal_lexemes_verified": True}), patch(
                       "witnora_core.operator_promotion.verify_odd_cycle_with_lean",
                       return_value={"verified": True, "lean_formal_status": "LEAN_VERIFIED"}):
            result = self.assess()
        self.assertEqual(result["status"], PROOF_REJECTED)
        self.assertEqual(result["reason"], "SOURCE_CYCLE_THEOREM_REJECTED")

    def test_success_is_not_operator_promotion(self):
        with patch("witnora_core.operator_promotion.verify_cnf_normalization_with_lean",
                   return_value={"verified": True, "source_document_verified": True,
                                 "token_stream_verified": True,
                                 "decimal_lexemes_verified": True,
                                 "proof_source_sha256": "n" * 64}), patch(
                       "witnora_core.operator_promotion.verify_odd_cycle_with_lean",
                       return_value={"verified": True,
                                     "lean_formal_status": "LEAN_SOURCE_CYCLE_UNSAT_VERIFIED",
                                     "proof_source_sha256": "c" * 64,
                                     "cycle_length": 3}):
            result = self.assess()
        self.assertEqual(result["status"], PROOF_VERIFIED)
        self.assertFalse(result["promoted"])
        self.assertFalse(result["novelty_verified"])
        self.assertFalse(result["performance_advantage_verified"])
        self.assertEqual(result["cycle_length"], 3)

    def test_optional_g5_must_be_checked(self):
        with patch("witnora_core.operator_promotion.verify_cnf_normalization_with_lean",
                   return_value={"verified": True, "source_document_verified": True,
                                 "token_stream_verified": True,
                                 "decimal_lexemes_verified": True}), patch(
                       "witnora_core.operator_promotion.verify_odd_cycle_with_lean",
                       return_value={"verified": True,
                                     "lean_formal_status": "LEAN_SOURCE_CYCLE_UNSAT_VERIFIED"}), patch(
                       "witnora_core.operator_promotion.verify_g5_certificate_with_lean",
                       return_value={"verified": False}) as g5:
            result = assess_odd_cycle_operator(
                self.formula, certificate={"fake": True},
                raw_clauses=self.raw, source_tokens=self.tokens,
                source_spellings=list(map(str, self.tokens)),
                source_text=self.source)
        self.assertEqual(result["status"], PROOF_REJECTED)
        self.assertEqual(result["reason"], "SUPPLIED_G5_CERTIFICATE_REJECTED")
        g5.assert_called_once()


if __name__ == "__main__":
    unittest.main()
