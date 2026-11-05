import unittest

from witnora_core.composed_orchestration import (
    COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED,
    COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED,
    build_composed_orchestration_certificate,
    check_composed_orchestration_certificate,
    make_composed_instance,
    make_negative_control,
)


class ComposedOrchestrationCheckerTest(unittest.TestCase):
    def test_composed_orchestration_chain_verified(self):
        instance = make_composed_instance("composed_sat_lift")
        cert = build_composed_orchestration_certificate(instance).to_dict()
        result = check_composed_orchestration_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED)
        self.assertTrue(result["chain_verified"])
        print("COMPOSED_ORCHESTRATION_CHAIN_VERIFIED_PASS")

    def test_composed_orchestration_bad_handoff_reject(self):
        instance, cert = make_negative_control("broken_handoff_hash_reject")
        result = check_composed_orchestration_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED)
        self.assertTrue(any("HASH_MISMATCH" in error for error in result["errors"]))
        print("COMPOSED_ORCHESTRATION_BAD_HANDOFF_REJECT_PASS")

    def test_composed_orchestration_diagnostic_step_reject(self):
        instance, cert = make_negative_control("diagnostic_step_used_as_cert_reject")
        result = check_composed_orchestration_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED)
        self.assertIn("DIAGNOSTIC_STEP_USED_AS_CERTIFICATE", result["errors"])
        print("COMPOSED_ORCHESTRATION_DIAGNOSTIC_STEP_REJECT_PASS")

    def test_composed_orchestration_fake_drat_reject(self):
        instance, cert = make_negative_control("fake_drat_composed_reject")
        result = check_composed_orchestration_certificate(instance.formula, cert)
        self.assertEqual(result["checker_status"], COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED)
        self.assertIn("FAKE_DRAT_COMPOSED_CLAIM", result["errors"])
        print("COMPOSED_ORCHESTRATION_FAKE_DRAT_REJECT_PASS")


if __name__ == "__main__":
    unittest.main()
