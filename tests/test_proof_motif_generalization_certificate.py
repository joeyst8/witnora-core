import unittest

from witnora_core.proof_motif_generalization import (
    PROOF_MOTIF_GENERALIZATION_VERIFIED,
    PROOF_MOTIF_GENERALIZED_DRAT_NOT_CLAIMED,
    UNSAT_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED,
    build_proof_motif_generalization_certificate,
    check_proof_motif_generalization_certificate,
    make_proof_motif_generalization_instance,
)


class ProofMotifGeneralizationCertificateTest(unittest.TestCase):
    def test_certificate_schema(self):
        instance = make_proof_motif_generalization_instance("ladder_near_4")
        cert = build_proof_motif_generalization_certificate(instance)
        data = cert.to_dict()
        self.assertEqual(data["type"], "PROOF_MOTIF_GENERALIZATION_CERTIFICATE")
        self.assertEqual(data["public_category"], UNSAT_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED)
        self.assertIn("base_motifs", data)
        self.assertIn("generalized_templates", data)
        self.assertIn("reuse_sites", data)
        self.assertIn("fallback_expansions", data)
        self.assertIn("compression_summary", data)
        self.assertIn("final_macro_proof", data)
        print("PROOF_MOTIF_GENERALIZATION_CERT_SCHEMA_PASS")

    def test_generalized_reuse_and_final_contradiction(self):
        instance = make_proof_motif_generalization_instance("ladder_near_4")
        cert = build_proof_motif_generalization_certificate(instance)
        result = check_proof_motif_generalization_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_GENERALIZATION_VERIFIED)
        self.assertTrue(result["final_contradiction_verified"])
        self.assertTrue(all(reuse["reuse_checker_status"] for reuse in cert.reuse_sites))
        print("PROOF_MOTIF_GENERALIZED_REUSE_CHECK_PASS")
        print("PROOF_MOTIF_GENERALIZED_FINAL_CONTRADICTION_PASS")

    def test_compression_ratio_and_no_fake_drat(self):
        instance = make_proof_motif_generalization_instance("ladder_near_8")
        cert = build_proof_motif_generalization_certificate(instance)
        self.assertGreater(cert.compression_summary["compression_ratio"], 1.0)
        self.assertEqual(cert.drat_claim, PROOF_MOTIF_GENERALIZED_DRAT_NOT_CLAIMED)
        self.assertNotIn("DRAT", cert.public_category)
        print("PROOF_MOTIF_GENERALIZATION_COMPRESSION_RATIO_PASS")
        print("PROOF_MOTIF_GENERALIZATION_NO_FAKE_DRAT_PASS")


if __name__ == "__main__":
    unittest.main()
