import unittest

from witnora_core.ci import evaluate_fail_conditions, evaluate_marketplace_fail_conditions


class CIFailPolicyTest(unittest.TestCase):
    def test_fail_on_risk_flags(self):
        report = {"verdict": "ARTIFACT_INTEGRITY_VERIFIED", "risk_flags": ["HASH_MISMATCH"]}
        reasons = evaluate_marketplace_fail_conditions(
            report,
            fail_on_risk_flags={"HASH_MISMATCH"},
            fail_on_verdict=set(),
        )
        self.assertEqual(reasons, ["risk_flag:HASH_MISMATCH"])
        print("CI_FAIL_ON_RISK_FLAGS_PASS")

    def test_fail_on_verdict(self):
        report = {"verdict": "PARTIALLY_VERIFIED", "risk_flags": []}
        reasons = evaluate_marketplace_fail_conditions(
            report,
            fail_on_risk_flags=set(),
            fail_on_verdict={"PARTIALLY_VERIFIED"},
        )
        self.assertEqual(reasons, ["verdict:PARTIALLY_VERIFIED"])
        print("CI_FAIL_ON_VERDICT_PASS")

    def test_legacy_fail_on_still_supported(self):
        report = {"verdict": "PARTIALLY_VERIFIED", "risk_flags": ["UNVERIFIED_CLAIM"]}
        reasons = evaluate_fail_conditions(report, {"overclaim", "partial_or_not_verified"})
        self.assertEqual(reasons, ["overclaim", "partial_or_not_verified"])


if __name__ == "__main__":
    unittest.main()
