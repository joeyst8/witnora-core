import unittest

from witnora_core.collapse_theory import (
    SYMMETRY_CERTIFICATION_FAILED,
    build_family_instances,
    build_symmetry_certificate,
    check_symmetry_certificate,
    validate_automorphism,
)


class SymmetryCertificateTest(unittest.TestCase):
    def test_symmetry_cert_schema(self):
        instance = build_family_instances(["symmetric-toy"])[0]
        cert = build_symmetry_certificate(instance)
        data = cert.to_dict()
        for key in [
            "instance_id",
            "formula_hash",
            "automorphism_generators",
            "automorphism_validation_status",
            "variable_orbits",
            "literal_orbits",
            "clause_orbits",
            "sbp_clauses",
            "sbp_type",
            "preservation_argument",
            "checker_status",
            "certification_level",
        ]:
            self.assertIn(key, data)
        print("SYMMETRY_CERT_SCHEMA_PASS")

    def test_automorphism_validation(self):
        instance = build_family_instances(["symmetric-toy"])[0]
        result = validate_automorphism(instance.formula, {1: 2, 2: 1})
        self.assertEqual(result["status"], "PASS")
        print("AUTOMORPHISM_VALIDATION_PASS")

    def test_false_automorphism_reject(self):
        instance = build_family_instances(["near-symmetry"])[0]
        result = validate_automorphism(instance.formula, {1: 4, 4: 1})
        self.assertEqual(result["status"], "FAIL")
        print("FALSE_AUTOMORPHISM_REJECT_PASS")

    def test_orbit_partition_validation(self):
        instance = build_family_instances(["symmetric-toy"])[0]
        cert = build_symmetry_certificate(instance)
        check = check_symmetry_certificate(instance.formula, cert)
        self.assertEqual(check["checker_status"], "PASS")
        self.assertIn([1, 2, 3, 4], cert.variable_orbits)
        print("ORBIT_PARTITION_VALIDATION_PASS")

    def test_near_symmetry_reject(self):
        instance = build_family_instances(["near-symmetry"])[0]
        cert = build_symmetry_certificate(instance)
        self.assertEqual(cert.checker_status, "PASS")
        self.assertIn([1, 2, 3], cert.variable_orbits)
        self.assertIn([4], cert.variable_orbits)
        self.assertNotIn([1, 2, 3, 4], cert.variable_orbits)
        false_cert = cert.to_dict()
        false_cert["automorphism_generators"] = [{1: 4, 4: 1}]
        false_cert["automorphism_validation_status"] = "VALIDATED"
        check = check_symmetry_certificate(instance.formula, false_cert)
        self.assertEqual(check["checker_status"], SYMMETRY_CERTIFICATION_FAILED)
        print("NEAR_SYMMETRY_REJECT_PASS")


if __name__ == "__main__":
    unittest.main()
