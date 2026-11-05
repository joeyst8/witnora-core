import unittest

from witnora_core.operator_genesis import (
    PROOF_MOTIF_TEMPLATE_EXTRACTED,
    detect_proof_motif_templates,
    make_proof_motif_instance,
)


class ProofMotifDetectionTest(unittest.TestCase):
    def test_template_detection(self):
        instance = make_proof_motif_instance("motif_ladder_8")
        detection = detect_proof_motif_templates(instance)
        self.assertEqual(detection["status"], PROOF_MOTIF_TEMPLATE_EXTRACTED)
        self.assertEqual(len(detection["motif_templates"]), 1)
        self.assertEqual(len(detection["reuse_sites"]), 8)
        print("PROOF_MOTIF_TEMPLATE_DETECTION_PASS")


if __name__ == "__main__":
    unittest.main()
