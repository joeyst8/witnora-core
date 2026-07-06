import unittest

from witnora_core.circuit_projection_lift import (
    CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED,
    CIRCUIT_PROJECTION_DRAT_NOT_CLAIMED,
    G10_CIRCUIT_PROJECTION_NATIVE_CERTIFIED,
    SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED,
    UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED,
    build_circuit_projection_certificate,
    check_circuit_projection_certificate,
    make_circuit_projection_instance,
)


class CircuitProjectionCertificateTest(unittest.TestCase):
    def test_circuit_projection_cert_schema(self):
        instance = make_circuit_projection_instance("half_adder_sat")
        cert = build_circuit_projection_certificate(instance).to_dict()
        self.assertEqual(cert["type"], "CIRCUIT_PROJECTION_LIFT_CERTIFICATE")
        self.assertEqual(cert["checker_status"], CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED)
        self.assertEqual(cert["certification_level"], G10_CIRCUIT_PROJECTION_NATIVE_CERTIFIED)
        self.assertTrue(cert["gate_definitions"])
        self.assertTrue(cert["projection_steps"])
        print("CIRCUIT_PROJECTION_CERT_SCHEMA_PASS")

    def test_circuit_projection_sat_witness_lift(self):
        instance = make_circuit_projection_instance("mux2_sat")
        cert = build_circuit_projection_certificate(instance).to_dict()
        self.assertEqual(cert["public_category"], SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED)
        self.assertTrue(cert["sat_lift"]["lifted_assignment_verified_against_original_cnf"])
        check = check_circuit_projection_certificate(instance.formula, cert)
        self.assertEqual(check["checker_status"], CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED)
        print("CIRCUIT_PROJECTION_SAT_WITNESS_LIFT_PASS")

    def test_circuit_projection_unsat_preservation(self):
        instance = make_circuit_projection_instance("circuit_unsat_control")
        cert = build_circuit_projection_certificate(instance).to_dict()
        self.assertEqual(cert["public_category"], UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED)
        self.assertTrue(cert["unsat_lift"]["equisat_chain_verified"])
        self.assertTrue(cert["unsat_lift"]["original_unsat_preserved"])
        print("CIRCUIT_PROJECTION_UNSAT_PRESERVATION_PASS")

    def test_circuit_projection_no_fake_drat(self):
        instance = make_circuit_projection_instance("half_adder_sat")
        cert = build_circuit_projection_certificate(instance).to_dict()
        self.assertEqual(cert["drat_claim"], CIRCUIT_PROJECTION_DRAT_NOT_CLAIMED)
        self.assertNotIn("DRAT", cert["public_category"])
        print("CIRCUIT_PROJECTION_NO_FAKE_DRAT_PASS")


if __name__ == "__main__":
    unittest.main()
