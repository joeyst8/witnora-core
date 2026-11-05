import tempfile
import unittest
from pathlib import Path

from witnora_core.separator_affine_family_theorem import (
    SEPARATOR_AFFINE_CERTIFICATE_VERIFIED,
    build_separator_affine_certificate,
    check_separator_affine_certificate,
    make_separator_affine_instance,
    run_separator_affine_family_lab,
)


class SeparatorAffineFamilyGeneratorsTest(unittest.TestCase):
    def _verify(self, instance_id):
        instance = make_separator_affine_instance(instance_id)
        cert = build_separator_affine_certificate(instance)
        check = check_separator_affine_certificate(instance.formula, cert)
        self.assertEqual(check["checker_status"], SEPARATOR_AFFINE_CERTIFICATE_VERIFIED)
        return check

    def test_family_generator(self):
        for name in [
            "saf_sat_chain_4",
            "saf_unsat_cover_4",
            "saf_mixed_components_6",
            "saf_balanced_sat_8",
        ]:
            self._verify(name)
        print("SEPARATOR_AFFINE_FAMILY_GENERATOR_PASS")

    def test_n4(self):
        self._verify("saf_sat_chain_4")
        self._verify("saf_unsat_cover_4")
        print("SEPARATOR_AFFINE_N4_PASS")

    def test_n8(self):
        self._verify("saf_sat_chain_8")
        self._verify("saf_unsat_cover_8")
        print("SEPARATOR_AFFINE_N8_PASS")

    def test_n16(self):
        self._verify("saf_sat_chain_16")
        self._verify("saf_unsat_cover_16")
        print("SEPARATOR_AFFINE_N16_PASS")

    def test_n32(self):
        self._verify("saf_sat_chain_32")
        self._verify("saf_unsat_cover_32")
        print("SEPARATOR_AFFINE_N32_PASS")

    def test_lab_outputs_polynomial_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "v222"
            result = run_separator_affine_family_lab(
                ["saf_sat_chain_4", "saf_unsat_cover_4", "invalid_cross_clause"],
                out,
                strict=True,
                zip_path=None,
            )
            self.assertTrue((out / "polynomial_bound_summary.json").exists())
            self.assertEqual(result["g14_family_theorem_summary"]["scope"], "SAF(c,r)")
            self.assertIn("fixed", result["g14_family_theorem_summary"]["polynomiality_boundary"])
            print("SEPARATOR_AFFINE_POLYNOMIAL_BOUND_PASS")


if __name__ == "__main__":
    unittest.main()
