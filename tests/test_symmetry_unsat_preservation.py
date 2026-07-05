import unittest

from witnora_core.collapse_theory import (
    SYMMETRY_CERTIFICATION_FAILED,
    SYMMETRY_DRAT_VERIFIED,
    SYMMETRY_UNSAT_NATIVE_CERTIFIED,
    build_family_instances,
    build_symmetry_certificate,
    check_symmetry_certificate,
)


class SymmetryUnsatPreservationTest(unittest.TestCase):
    def test_sbp_not_claimed_implied(self):
        instance = build_family_instances(["symmetric-toy"])[0]
        cert = build_symmetry_certificate(instance)
        self.assertTrue(cert.sbp_clauses)
        self.assertNotEqual(cert.preservation_argument, "IMPLIED_BY_ORIGINAL_FORMULA")
        self.assertIn("sbp_is_not_claimed_implied_by_original_formula", cert.preservation_obligations)
        print("SBP_NOT_CLAIMED_IMPLIED_PASS")

    def test_sbp_preservation_obligation(self):
        instance = build_family_instances(["symmetric-toy"])[0]
        cert = build_symmetry_certificate(instance)
        bad = cert.to_dict()
        bad["preservation_argument"] = "NONE"
        result = check_symmetry_certificate(instance.formula, bad)
        self.assertEqual(result["checker_status"], SYMMETRY_CERTIFICATION_FAILED)
        self.assertIn("SBP_WITHOUT_PRESERVATION_ARGUMENT", result["errors"])
        print("SBP_PRESERVATION_OBLIGATION_PASS")

    def test_unsat_strengthening_not_enough(self):
        instance = build_family_instances(["symmetric-toy"])[0]
        cert = build_symmetry_certificate(instance)
        bad = cert.to_dict()
        bad["status"] = SYMMETRY_UNSAT_NATIVE_CERTIFIED
        bad["preservation_obligations"] = ["strengthened_unsat_native_proof"]
        result = check_symmetry_certificate(instance.formula, bad)
        self.assertEqual(result["checker_status"], SYMMETRY_CERTIFICATION_FAILED)
        self.assertIn("UNSAT_PRESERVATION_OBLIGATIONS_MISSING", result["errors"])
        print("UNSAT_STRENGTHENING_NOT_ENOUGH_PASS")

    def test_symmetry_drat_no_fake_claim(self):
        instance = build_family_instances(["symmetric-toy"])[0]
        cert = build_symmetry_certificate(instance)
        bad = cert.to_dict()
        bad["status"] = SYMMETRY_DRAT_VERIFIED
        bad["drat_trim_verified_against_original"] = False
        bad["proof_base"] = "symmetry_broken_cnf"
        result = check_symmetry_certificate(instance.formula, bad)
        self.assertEqual(result["checker_status"], SYMMETRY_CERTIFICATION_FAILED)
        self.assertIn("DRAT_NOT_VERIFIED_AGAINST_ORIGINAL_CNF", result["errors"])
        print("SYMMETRY_DRAT_NO_FAKE_CLAIM_PASS")


if __name__ == "__main__":
    unittest.main()
