import unittest

from witnora_core.operator_genesis import (
    AFFINE_RESIDUE_CERTIFICATE_VERIFIED,
    AFFINE_RESIDUE_SAT_WITNESS_VERIFIED,
    AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED,
    MODULAR_RESIDUE_DRAT_NOT_CLAIMED,
    SAT_AFFINE_RESIDUE_NATIVE_CERTIFIED,
    UNSAT_AFFINE_RESIDUE_NATIVE_CERTIFIED,
    build_affine_residue_certificate,
    check_affine_residue_certificate,
    gaussian_eliminate_gf2,
    make_affine_residue_instance,
)


class AffineResidueCertificateTest(unittest.TestCase):
    def test_affine_residue_cert_schema(self):
        cert = build_affine_residue_certificate(make_affine_residue_instance("parity_arity_7_unsat"))
        data = cert.to_dict()
        for key in [
            "type",
            "formula_hash",
            "extraction_mode",
            "equations",
            "gaussian_elimination_trace",
            "row_operations",
            "final_rank",
            "claim_boundary",
        ]:
            self.assertIn(key, data)
        self.assertEqual(data["type"], "AFFINE_RESIDUE_GF2_CERTIFICATE")
        print("AFFINE_RESIDUE_CERT_SCHEMA_PASS")

    def test_gf2_gaussian_unsat(self):
        equations = [
            {"variables": [1, 2, 3], "parity_bit": 0},
            {"variables": [1, 2, 3], "parity_bit": 1},
        ]
        result = gaussian_eliminate_gf2(equations)
        self.assertEqual(result["status"], "UNSAT")
        self.assertEqual(result["contradiction_row"], {"coefficients": [], "rhs": 1})
        print("GF2_GAUSSIAN_UNSAT_PASS")

    def test_gf2_gaussian_sat(self):
        equations = [{"variables": [1, 2, 3], "parity_bit": 1}]
        result = gaussian_eliminate_gf2(equations)
        self.assertEqual(result["status"], "SAT")
        self.assertIsNotNone(result["solution"])
        print("GF2_GAUSSIAN_SAT_PASS")

    def test_affine_sat_and_unsat_public_categories(self):
        unsat = build_affine_residue_certificate(make_affine_residue_instance("parity_arity_8_unsat"))
        sat = build_affine_residue_certificate(make_affine_residue_instance("parity_arity_8_sat"))
        self.assertEqual(unsat.status, AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED)
        self.assertEqual(unsat.public_category, UNSAT_AFFINE_RESIDUE_NATIVE_CERTIFIED)
        self.assertEqual(sat.status, AFFINE_RESIDUE_SAT_WITNESS_VERIFIED)
        self.assertEqual(sat.public_category, SAT_AFFINE_RESIDUE_NATIVE_CERTIFIED)
        self.assertEqual(sat.checker_status, AFFINE_RESIDUE_CERTIFICATE_VERIFIED)

    def test_modular_residue_no_fake_drat(self):
        cert = build_affine_residue_certificate(make_affine_residue_instance("parity_arity_7_unsat"))
        self.assertEqual(cert.drat_claim, MODULAR_RESIDUE_DRAT_NOT_CLAIMED)
        self.assertNotIn("DRAT", cert.public_category)
        bad = cert.to_dict()
        bad["drat_claim"] = "UNSAT_DRAT_EXPORTED_VERIFIED"
        result = check_affine_residue_certificate(make_affine_residue_instance("parity_arity_7_unsat").formula, bad)
        self.assertNotEqual(result["status"], AFFINE_RESIDUE_CERTIFICATE_VERIFIED)
        self.assertIn("FAKE_DRAT_CLAIM", result["errors"])
        print("MODULAR_RESIDUE_NO_FAKE_DRAT_PASS")


if __name__ == "__main__":
    unittest.main()
