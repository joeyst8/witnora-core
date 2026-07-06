import unittest

from witnora_core.operator_genesis import (
    PROOF_MOTIF_CERTIFICATE_FAILED,
    build_proof_motif_certificate,
    check_proof_motif_certificate,
    make_proof_motif_instance,
    run_proof_motif_lab,
)


class ProofMotifControlsTest(unittest.TestCase):
    def test_repeated_pattern_requires_checker(self):
        instance = make_proof_motif_instance("motif_ladder_4")
        cert = build_proof_motif_certificate(instance).to_dict()
        cert["reuse_sites"][0]["instantiated_steps_hash"] = "bad"
        result = check_proof_motif_certificate(instance.formula, cert)
        self.assertEqual(result["status"], PROOF_MOTIF_CERTIFICATE_FAILED)

    def test_no_fake_operator_claim_for_duplicate(self):
        result = run_proof_motif_lab(instances=["tseitin_grid_optional"], out_root="outputs/test-v27-duplicate-control")
        row = result["proof_motif_rows"][0]
        self.assertFalse(row["novel_g6_delta"])
        self.assertEqual(row["public_category"], "NO_COLLAPSE_FOUND")


if __name__ == "__main__":
    unittest.main()
