import unittest

from witnora_core.circuit_projection_lift import (
    CIRCUIT_PROJECTION_CERTIFICATE_FAILED,
    build_circuit_projection_certificate,
    check_circuit_projection_certificate,
    detect_gate_definitions,
    make_circuit_projection_instance,
    make_negative_control,
)


class CircuitProjectionDetectionTest(unittest.TestCase):
    def test_circuit_gate_and_detection(self):
        instance = make_circuit_projection_instance("and_gate_sat")
        detected = detect_gate_definitions(instance.formula)
        self.assertTrue(any(row["gate_type"] == "AND" and row["output_variable"] == 3 for row in detected))
        print("CIRCUIT_GATE_AND_DETECTION_PASS")

    def test_circuit_gate_or_detection(self):
        instance = make_circuit_projection_instance("or_gate_sat")
        detected = detect_gate_definitions(instance.formula)
        self.assertTrue(any(row["gate_type"] == "OR" and row["output_variable"] == 3 for row in detected))
        print("CIRCUIT_GATE_OR_DETECTION_PASS")

    def test_circuit_gate_not_detection(self):
        instance = make_circuit_projection_instance("not_gate_sat")
        detected = detect_gate_definitions(instance.formula)
        self.assertTrue(any(row["gate_type"] == "NOT" and row["output_variable"] == 2 for row in detected))
        print("CIRCUIT_GATE_NOT_DETECTION_PASS")

    def test_circuit_gate_incomplete_reject(self):
        instance, cert = make_negative_control("gate_definition_incomplete_reject")
        result = check_circuit_projection_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], CIRCUIT_PROJECTION_CERTIFICATE_FAILED)
        self.assertTrue(any("GATE_DEFINITION_INCOMPLETE" in error for error in result["errors"]))
        print("CIRCUIT_GATE_INCOMPLETE_REJECT_PASS")

    def test_circuit_gate_polluted_reject(self):
        instance, cert = make_negative_control("gate_definition_polluted_reject")
        result = check_circuit_projection_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], CIRCUIT_PROJECTION_CERTIFICATE_FAILED)
        self.assertTrue(any("UNSAFE_AUXILIARY_USE" in error for error in result["errors"]))
        print("CIRCUIT_GATE_POLLUTED_REJECT_PASS")

    def test_circuit_unsafe_aux_use_reject(self):
        instance, cert = make_negative_control("unsafe_auxiliary_use_reject")
        result = check_circuit_projection_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], CIRCUIT_PROJECTION_CERTIFICATE_FAILED)
        self.assertTrue(any("PROJECTED_VARIABLE_REMAINS_IN_CORE" in error for error in result["errors"]))
        print("CIRCUIT_UNSAFE_AUX_USE_REJECT_PASS")

    def test_circuit_projection_core_hash(self):
        instance = make_circuit_projection_instance("mux2_sat")
        cert = build_circuit_projection_certificate(instance).to_dict()
        result = check_circuit_projection_certificate(instance.formula, cert)
        self.assertEqual(result["core_formula_hash"], cert["core_formula_hash"])
        print("CIRCUIT_PROJECTION_CORE_HASH_PASS")

    def test_circuit_projection_equisat(self):
        instance = make_circuit_projection_instance("mux4_sat")
        cert = build_circuit_projection_certificate(instance).to_dict()
        self.assertTrue(all(step["equisat_preservation_verified"] for step in cert["projection_steps"]))
        print("CIRCUIT_PROJECTION_EQUI_SAT_PASS")


if __name__ == "__main__":
    unittest.main()
