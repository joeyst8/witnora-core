import unittest

from witnora_core.composed_orchestration import (
    COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED,
    COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED,
    SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED,
    UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED,
    build_composed_orchestration_certificate,
    check_composed_orchestration_certificate,
    make_composed_instance,
    make_negative_control,
)


class ComposedOrchestrationLiftTest(unittest.TestCase):
    def test_composed_orchestration_witness_lift(self):
        instance = make_composed_instance("composed_sat_lift")
        cert = build_composed_orchestration_certificate(instance).to_dict()
        self.assertEqual(cert["public_category"], SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED)
        self.assertTrue(cert["lift_trace"]["verified_against_original_cnf"])
        result = check_composed_orchestration_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED)
        print("COMPOSED_ORCHESTRATION_WITNESS_LIFT_PASS")

    def test_composed_orchestration_unsat_lift(self):
        instance = make_composed_instance("composed_unsat_cover")
        cert = build_composed_orchestration_certificate(instance).to_dict()
        self.assertEqual(cert["public_category"], UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED)
        self.assertTrue(cert["lift_trace"]["final_unsat_certificate"]["verified_unsat"])
        result = check_composed_orchestration_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED)
        print("COMPOSED_ORCHESTRATION_UNSAT_LIFT_PASS")

    def test_composed_orchestration_bad_witness_lift_reject(self):
        instance, cert = make_negative_control("bad_witness_lift_reject")
        result = check_composed_orchestration_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED)
        self.assertIn("FINAL_WITNESS_DOES_NOT_SATISFY_ORIGINAL_CNF", result["errors"])
        print("COMPOSED_ORCHESTRATION_BAD_WITNESS_LIFT_REJECT_PASS")

    def test_composed_orchestration_unsat_no_preservation_reject(self):
        instance, cert = make_negative_control("unsat_step_without_preservation_reject")
        result = check_composed_orchestration_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED)
        self.assertTrue(any("UNSAT_STEP_WITHOUT_PRESERVATION" in error for error in result["errors"]))
        print("COMPOSED_ORCHESTRATION_UNSAT_NO_PRESERVATION_REJECT_PASS")


if __name__ == "__main__":
    unittest.main()
