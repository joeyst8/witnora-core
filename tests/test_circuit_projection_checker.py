import unittest

from witnora_core.circuit_projection_lift import (
    CIRCUIT_PROJECTION_CERTIFICATE_FAILED,
    CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED,
    build_circuit_projection_certificate,
    check_circuit_projection_certificate,
    make_circuit_projection_instance,
    make_negative_control,
)


class CircuitProjectionCheckerTest(unittest.TestCase):
    def test_circuit_projection_checker(self):
        instance = make_circuit_projection_instance("half_adder_sat")
        cert = build_circuit_projection_certificate(instance).to_dict()
        result = check_circuit_projection_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED)
        self.assertEqual(result["gate_count"], 2)
        print("CIRCUIT_PROJECTION_CHECKER_PASS")

    def test_circuit_projection_bad_lift_reject(self):
        instance, cert = make_negative_control("bad_lift_reject")
        result = check_circuit_projection_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], CIRCUIT_PROJECTION_CERTIFICATE_FAILED)
        self.assertIn("LIFTED_ASSIGNMENT_MISMATCH", result["errors"])
        print("CIRCUIT_PROJECTION_BAD_LIFT_REJECT_PASS")

    def test_circuit_projection_tamper_reject(self):
        instance, cert = make_negative_control("tamper_reject")
        result = check_circuit_projection_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], CIRCUIT_PROJECTION_CERTIFICATE_FAILED)
        self.assertIn("ORIGINAL_FORMULA_HASH_MISMATCH", result["errors"])
        print("CIRCUIT_PROJECTION_TAMPER_REJECT_PASS")


if __name__ == "__main__":
    unittest.main()
