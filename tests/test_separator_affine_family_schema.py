import unittest

from witnora_core.separator_affine_family_theorem import (
    G14_GRAMMAR,
    SAT_CERTIFIED,
    SEPARATOR_AFFINE_CERTIFICATE_VERIFIED,
    build_separator_affine_certificate,
    check_separator_affine_certificate,
    make_separator_affine_instance,
)


class SeparatorAffineFamilySchemaTest(unittest.TestCase):
    def test_separator_affine_cert_schema(self):
        instance = make_separator_affine_instance("saf_sat_chain_4")
        cert = build_separator_affine_certificate(instance)
        data = cert.to_dict()
        self.assertEqual(data["type"], "SEPARATOR_AFFINE_FAMILY_CERTIFICATE")
        self.assertEqual(data["grammar"], G14_GRAMMAR)
        self.assertEqual(data["family_parameters"]["separator_bound_c"], 1)
        self.assertEqual(data["family_parameters"]["affine_arity_bound_r"], 2)
        self.assertEqual(data["final_result"], SAT_CERTIFIED)
        self.assertIn("separator_assignments", data)
        self.assertIn("polynomial_bound_record", data)
        print("SEPARATOR_AFFINE_CERT_SCHEMA_PASS")

    def test_separator_verify_and_component_extraction(self):
        instance = make_separator_affine_instance("saf_sat_chain_4")
        cert = build_separator_affine_certificate(instance)
        data = cert.to_dict()
        check = check_separator_affine_certificate(instance.formula, data)
        self.assertEqual(check["checker_status"], SEPARATOR_AFFINE_CERTIFICATE_VERIFIED)
        self.assertEqual(check["separator_size"], 1)
        self.assertEqual(check["component_count"], 4)
        self.assertTrue(data["separator_verification"]["separator_valid"])
        self.assertEqual(len(data["separator_verification"]["components_after_removal"]), 4)
        print("SEPARATOR_AFFINE_SEPARATOR_VERIFY_PASS")
        print("SEPARATOR_AFFINE_COMPONENT_EXTRACTION_PASS")

    def test_component_affine_verify_and_assignment_enumeration(self):
        instance = make_separator_affine_instance("saf_sat_chain_4")
        cert = build_separator_affine_certificate(instance)
        data = cert.to_dict()
        self.assertEqual(len(data["separator_assignments"]), 2)
        for assignment in data["separator_assignments"]:
            self.assertEqual(len(assignment["component_records"]), 4)
            for component in assignment["component_records"]:
                self.assertEqual(
                    component["affine_detection_status"],
                    "SEPARATOR_AFFINE_COMPONENT_AFFINE_VERIFIED",
                )
                self.assertIn(component["component_result"], {"SAT", "UNSAT"})
        print("SEPARATOR_AFFINE_COMPONENT_AFFINE_VERIFY_PASS")
        print("SEPARATOR_AFFINE_ASSIGNMENT_ENUMERATION_PASS")


if __name__ == "__main__":
    unittest.main()
