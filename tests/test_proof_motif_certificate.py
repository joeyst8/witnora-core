import unittest

from witnora_core.operator_genesis import (
    PROOF_MOTIF_CERTIFICATE_VERIFIED,
    PROOF_MOTIF_DRAT_NOT_CLAIMED,
    UNSAT_PROOF_MOTIF_NATIVE_CERTIFIED,
    build_proof_motif_certificate,
    check_proof_motif_certificate,
    make_proof_motif_instance,
)


class ProofMotifCertificateTest(unittest.TestCase):
    def test_proof_motif_cert_schema(self):
        instance = make_proof_motif_instance("motif_ladder_4")
        cert = build_proof_motif_certificate(instance)
        data = cert.to_dict()
        self.assertEqual(data["type"], "PROOF_MOTIF_COMPRESSION_CERTIFICATE")
        self.assertEqual(data["public_category"], UNSAT_PROOF_MOTIF_NATIVE_CERTIFIED)
        self.assertIn("motif_templates", data)
        self.assertIn("reuse_sites", data)
        self.assertIn("compressed_proof", data)
        print("PROOF_MOTIF_CERT_SCHEMA_PASS")

    def test_template_and_reuse_verification(self):
        instance = make_proof_motif_instance("motif_ladder_4")
        cert = build_proof_motif_certificate(instance)
        self.assertTrue(all(template["template_verified"] for template in cert.motif_templates))
        self.assertTrue(all(reuse["reuse_verified"] for reuse in cert.reuse_sites))
        result = check_proof_motif_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_CERTIFICATE_VERIFIED)
        print("PROOF_MOTIF_TEMPLATE_VERIFICATION_PASS")
        print("PROOF_MOTIF_REUSE_VERIFICATION_PASS")

    def test_final_contradiction_and_compression(self):
        instance = make_proof_motif_instance("motif_ladder_8")
        cert = build_proof_motif_certificate(instance)
        self.assertTrue(cert.compressed_proof["final_contradiction"])
        self.assertGreater(cert.compressed_proof["compression_ratio"], 1.0)
        print("PROOF_MOTIF_FINAL_CONTRADICTION_PASS")
        print("PROOF_MOTIF_COMPRESSION_RATIO_PASS")

    def test_no_fake_drat_claim(self):
        instance = make_proof_motif_instance("motif_ladder_4")
        cert = build_proof_motif_certificate(instance)
        self.assertEqual(cert.drat_claim, PROOF_MOTIF_DRAT_NOT_CLAIMED)
        self.assertNotIn("DRAT", cert.public_category)
        print("PROOF_MOTIF_NO_FAKE_DRAT_PASS")


if __name__ == "__main__":
    unittest.main()
