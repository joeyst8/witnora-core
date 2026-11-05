import unittest

from witnora_core.proof_motif_generalization import (
    PARAMETRIC_GENERALIZATION,
    PROOF_MOTIF_NEAR_STRUCTURE_DETECTED,
    TEMPLATE_ABSTRACTION,
    build_proof_motif_generalization_certificate,
    detect_near_motifs,
    make_proof_motif_generalization_instance,
)


class ProofMotifGeneralizationDetectionTest(unittest.TestCase):
    def test_near_detection_and_template_abstraction(self):
        instance = make_proof_motif_generalization_instance("ladder_near_4")
        detection = detect_near_motifs(instance)
        self.assertEqual(detection["status"], PROOF_MOTIF_NEAR_STRUCTURE_DETECTED)
        self.assertEqual(detection["detection_mode"], PARAMETRIC_GENERALIZATION)
        self.assertFalse(detection["similarity_is_proof"])
        self.assertTrue(detection["generalized_templates"])
        print("PROOF_MOTIF_NEAR_DETECTION_PASS")
        print("PROOF_MOTIF_TEMPLATE_ABSTRACTION_PASS")

    def test_exact_duplicate_uses_template_abstraction(self):
        instance = make_proof_motif_generalization_instance("exact_motif_duplicate_control")
        detection = detect_near_motifs(instance)
        cert = build_proof_motif_generalization_certificate(instance)
        self.assertEqual(detection["detection_mode"], TEMPLATE_ABSTRACTION)
        self.assertEqual(cert.g11_delta_status, "PROOF_MOTIF_GENERALIZED_NO_NEW_DELTA")


if __name__ == "__main__":
    unittest.main()
