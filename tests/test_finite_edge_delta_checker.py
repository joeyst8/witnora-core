import copy
import unittest

from witnora_core.finite_edge_certificate import (
    FINITE_EDGE_DELTA_CERTIFICATE_FAILED,
    FINITE_EDGE_DELTA_CERTIFICATE_VERIFIED,
    build_finite_edge_delta_certificate,
    check_finite_edge_delta_certificate,
)


class FiniteEdgeDeltaCheckerTest(unittest.TestCase):
    def test_finite_edge_delta_checker(self):
        cert = build_finite_edge_delta_certificate(
            instances=["cycle_4_3color", "cycle_6_3color"],
        ).to_dict()
        result = check_finite_edge_delta_certificate(cert).to_dict()
        self.assertEqual(result["checker_status"], FINITE_EDGE_DELTA_CERTIFICATE_VERIFIED)
        self.assertEqual(result["failed_instances"], [])
        self.assertEqual(result["checked_instances"], 2)
        print("FINITE_EDGE_DELTA_CHECKER_PASS")

    def test_finite_edge_delta_tamper_reject(self):
        cert = build_finite_edge_delta_certificate(instances=["cycle_4_3color"]).to_dict()
        tampered = copy.deepcopy(cert)
        tampered["instances"][0]["upper_result"]["witness_or_certificate_verified"] = False
        result = check_finite_edge_delta_certificate(tampered).to_dict()
        self.assertEqual(result["checker_status"], FINITE_EDGE_DELTA_CERTIFICATE_FAILED)
        self.assertTrue(result["failed_instances"] or result["errors"])
        print("FINITE_EDGE_DELTA_TAMPER_REJECT_PASS")


if __name__ == "__main__":
    unittest.main()
