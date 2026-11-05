import unittest

from witnora_core.composed_orchestration import (
    COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED,
    COMPOSED_ORCHESTRATION_STEP_VERIFIED,
    G9_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED,
    SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED,
    build_composed_orchestration_certificate,
    check_composed_orchestration_certificate,
    make_composed_instance,
)


class ComposedOrchestrationCertificateTest(unittest.TestCase):
    def test_composed_orchestration_cert_schema(self):
        instance = make_composed_instance("composed_sat_lift")
        cert = build_composed_orchestration_certificate(instance).to_dict()
        self.assertEqual(cert["type"], "COMPOSED_ORCHESTRATION_CERTIFICATE")
        self.assertEqual(cert["public_category"], SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED)
        self.assertEqual(cert["certification_level"], G9_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED)
        self.assertEqual(cert["checker_status"], COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED)
        self.assertGreaterEqual(len(cert["orchestration_sequence"]), 2)
        print("COMPOSED_ORCHESTRATION_CERT_SCHEMA_PASS")

    def test_composed_orchestration_sequence(self):
        instance = make_composed_instance("projection_affine_capacity")
        cert = build_composed_orchestration_certificate(instance).to_dict()
        operators = [step["operator_name"] for step in cert["orchestration_sequence"]]
        self.assertIn("G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE", operators)
        self.assertIn("G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE", operators)
        self.assertIn("G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE", operators)
        print("COMPOSED_ORCHESTRATION_SEQUENCE_PASS")

    def test_composed_orchestration_step_cert_check(self):
        instance = make_composed_instance("composed_sat_lift")
        cert = build_composed_orchestration_certificate(instance).to_dict()
        for step in cert["orchestration_sequence"]:
            self.assertEqual(step["step_checker_status"], COMPOSED_ORCHESTRATION_STEP_VERIFIED)
            self.assertEqual(step["step_certificate"]["checker_status"], COMPOSED_ORCHESTRATION_STEP_VERIFIED)
        result = check_composed_orchestration_certificate(instance.formula, cert)
        self.assertEqual(result["steps_verified"], len(cert["orchestration_sequence"]))
        print("COMPOSED_ORCHESTRATION_STEP_CERT_CHECK_PASS")

    def test_composed_orchestration_handoff_hash(self):
        instance = make_composed_instance("composed_sat_lift")
        cert = build_composed_orchestration_certificate(instance).to_dict()
        sequence = cert["orchestration_sequence"]
        self.assertEqual(sequence[0]["input_formula_hash"], cert["original_formula_hash"])
        for left, right in zip(sequence, sequence[1:]):
            self.assertEqual(left["output_formula_hash"], right["input_formula_hash"])
        print("COMPOSED_ORCHESTRATION_HANDOFF_HASH_PASS")


if __name__ == "__main__":
    unittest.main()
