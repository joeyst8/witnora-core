import unittest

from witnora_core.proof_motif_generalization import (
    DIAGNOSTIC_ONLY,
    PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY,
    PROOF_MOTIF_GENERALIZATION_FAILED,
    build_proof_motif_generalization_certificate,
    check_proof_motif_generalization_certificate,
    make_proof_motif_generalization_instance,
)


class ProofMotifGeneralizationControlsTest(unittest.TestCase):
    def test_loose_similarity_diagnostic_only(self):
        instance = make_proof_motif_generalization_instance("loose_similarity_reject")
        cert = build_proof_motif_generalization_certificate(instance)
        result = check_proof_motif_generalization_certificate(instance.formula, cert)
        self.assertEqual(cert.certification_mode, DIAGNOSTIC_ONLY)
        self.assertEqual(result["status"], PROOF_MOTIF_GENERALIZATION_DIAGNOSTIC_ONLY)
        self.assertEqual(cert.public_category, "NO_COLLAPSE_FOUND")
        print("PROOF_MOTIF_LOOSE_SIMILARITY_NO_CERTIFY_PASS")

    def test_fake_drat_rejected(self):
        instance = make_proof_motif_generalization_instance("fake_drat_reject")
        cert = build_proof_motif_generalization_certificate(instance).to_dict()
        cert["drat_claim"] = "DRAT_VERIFIED"
        result = check_proof_motif_generalization_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_GENERALIZATION_FAILED)

    def test_no_theorem_or_completeness_or_pnp_claims(self):
        instance = make_proof_motif_generalization_instance("ladder_near_4")
        cert = build_proof_motif_generalization_certificate(instance)
        text = str(cert.to_dict()).lower()
        self.assertNotIn("theorem", text)
        self.assertNotIn("completeness", text)
        self.assertNotIn("p vs np progress", text)
        self.assertNotIn("drat verified", text)
        print("NO_THEOREM_CLAIM_PASS")
        print("NO_COMPLETENESS_CLAIM_PASS")
        print("NO_PNP_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        instance = make_proof_motif_generalization_instance("ladder_near_4")
        cert = build_proof_motif_generalization_certificate(instance)
        text = str(cert.to_dict())
        self.assertNotIn("'HARD'", text)
        self.assertNotIn("'UNKNOWN'", text)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
