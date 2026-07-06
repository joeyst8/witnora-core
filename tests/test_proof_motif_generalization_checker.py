import copy
import unittest

from witnora_core.proof_motif_generalization import (
    PROOF_MOTIF_GENERALIZATION_FAILED,
    PROOF_MOTIF_GENERALIZATION_VERIFIED,
    build_proof_motif_generalization_certificate,
    check_proof_motif_generalization_certificate,
    make_proof_motif_generalization_instance,
)


class ProofMotifGeneralizationCheckerTest(unittest.TestCase):
    def test_generalized_template_and_parametric_instantiation(self):
        instance = make_proof_motif_generalization_instance("ladder_near_4")
        cert = build_proof_motif_generalization_certificate(instance)
        result = check_proof_motif_generalization_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_GENERALIZATION_VERIFIED)
        self.assertEqual(cert.certification_mode, "PARAMETRIC_TEMPLATE_CHECKED")
        print("PROOF_MOTIF_GENERALIZED_TEMPLATE_CHECK_PASS")
        print("PROOF_MOTIF_PARAMETRIC_INSTANTIATION_PASS")

    def test_concrete_fallback_expansion(self):
        instance = make_proof_motif_generalization_instance("gadget_variants")
        cert = build_proof_motif_generalization_certificate(instance)
        self.assertTrue(cert.fallback_expansions)
        result = check_proof_motif_generalization_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_GENERALIZATION_VERIFIED)
        print("PROOF_MOTIF_CONCRETE_FALLBACK_PASS")

    def test_bad_generalization_rejected(self):
        instance = make_proof_motif_generalization_instance("bad_generalization_control")
        cert = build_proof_motif_generalization_certificate(instance).to_dict()
        cert["generalized_templates"][0]["parameter_constraints"]["instantiated_resolution_steps_must_verify"] = False
        result = check_proof_motif_generalization_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_GENERALIZATION_FAILED)
        print("PROOF_MOTIF_BAD_GENERALIZATION_REJECT_PASS")

    def test_bad_substitution_rejected(self):
        instance = make_proof_motif_generalization_instance("bad_substitution_reject")
        cert = build_proof_motif_generalization_certificate(instance).to_dict()
        cert["reuse_sites"][0]["substitution_map"]["y"] = cert["reuse_sites"][0]["substitution_map"]["x"]
        result = check_proof_motif_generalization_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_GENERALIZATION_FAILED)
        print("PROOF_MOTIF_BAD_SUBSTITUTION_REJECT_PASS")

    def test_tamper_rejected(self):
        instance = make_proof_motif_generalization_instance("tamper_reject")
        cert = build_proof_motif_generalization_certificate(instance).to_dict()
        cert["formula_hash"] = "0" * 64
        result = check_proof_motif_generalization_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_GENERALIZATION_FAILED)
        print("PROOF_MOTIF_TAMPER_REJECT_PASS")


if __name__ == "__main__":
    unittest.main()
