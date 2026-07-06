import unittest

from witnora_core.operator_genesis import (
    AFFINE_RESIDUE_CERTIFICATE_FAILED,
    build_affine_residue_certificate,
    make_affine_residue_instance,
    run_affine_residue_lab,
)


class ModularResidueControlsTest(unittest.TestCase):
    def test_negative_controls_not_certified(self):
        result = run_affine_residue_lab(
            instances=["incomplete_affine_reject", "polluted_affine_reject", "over_cap_affine_diagnostic", "non_affine_high_overlap_control"],
            out_root="outputs/test-v26-controls",
        )
        for row in result["affine_residue_rows"]:
            self.assertEqual(row["public_category"], "NO_COLLAPSE_FOUND")
            self.assertEqual(row["checker_status"], AFFINE_RESIDUE_CERTIFICATE_FAILED)
        self.assertEqual(result["g5_operator_delta_summary"]["controls_not_certified"], 4)

    def test_over_cap_certificate_diagnostic(self):
        cert = build_affine_residue_certificate(make_affine_residue_instance("over_cap_affine_diagnostic"), max_arity=10)
        self.assertEqual(cert.public_category, "NO_COLLAPSE_FOUND")
        self.assertEqual(cert.status, "AFFINE_RESIDUE_OVER_CAP_DIAGNOSTIC")

    def test_no_fake_operator_solved_claim_for_controls(self):
        result = run_affine_residue_lab(instances=["polluted_affine_reject"], out_root="outputs/test-v26-control-no-solved")
        self.assertFalse(result["affine_residue_rows"][0]["novel_g5_delta"])


if __name__ == "__main__":
    unittest.main()
