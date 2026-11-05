"""First source-file migration wave: the CI failure-policy decision kernel.

The Python policy is the unchanged default and the differential oracle.
"""

from __future__ import annotations

import random
import unittest

from witnora_core.ci import (
    evaluate_fail_conditions, evaluate_marketplace_fail_conditions,
)


FAIL_OPTIONS = (
    "hash_mismatch", "missing_file", "overclaim", "partial_or_not_verified",
    "drat_replay_failed", "independent_checker_failed",
)
RISK_FLAGS = (
    "HASH_MISMATCH", "MISSING_FILE", "UNVERIFIED_CLAIM",
    "DRAT_TRIM_REPLAY_FAILED_OR_SKIPPED", "OTHER", "hash_mismatch",
)


class PythonPolicyCompatibilityTests(unittest.TestCase):
    def test_python_reference_default_and_explicit(self):
        report = {"risk_flags": ["HASH_MISMATCH", "MISSING_FILE"], "verdict": "OVERCLAIM"}
        self.assertEqual(evaluate_fail_conditions(report, set(FAIL_OPTIONS)),
                         evaluate_fail_conditions(report, set(FAIL_OPTIONS), backend="python"))

    def test_native_is_not_silently_the_default(self):
        report = {"risk_flags": ["HASH_MISMATCH"]}
        self.assertEqual(evaluate_fail_conditions(report, {"hash_mismatch"}), ["hash_mismatch"])

    def test_unknown_fail_backend_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown CI"):
            evaluate_fail_conditions({}, set(), backend="unknown")

    def test_unknown_marketplace_backend_rejected(self):
        with self.assertRaisesRegex(ValueError, "unknown CI"):
            evaluate_marketplace_fail_conditions({}, fail_on_risk_flags=set(),
                fail_on_verdict=set(), backend="unknown")


class NativePolicyDifferentialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from witnora_ve import (ci_failure_reasons_native,
                                    ci_marketplace_failure_reasons_native)
        except ImportError:
            raise unittest.SkipTest("native wheel unavailable; focused GitHub CI builds it")

    def test_exact_error_order_and_duplicate_suppression(self):
        report = {"risk_flags": list(RISK_FLAGS), "verdict": "OVERCLAIM",
                  "drat_trim_replay": [{"status": "SKIP"}],
                  "independent_checker_replay": [{"status": "FAIL"}]}
        expected = evaluate_fail_conditions(report, set(FAIL_OPTIONS))
        self.assertEqual(evaluate_fail_conditions(report, set(FAIL_OPTIONS), backend="rust"), expected)

    def test_positive_verdict_does_not_trigger_partial(self):
        report = {"risk_flags": [], "verdict": "ARTIFACT_INTEGRITY_VERIFIED"}
        self.assertEqual(evaluate_fail_conditions(report, {"partial_or_not_verified"}, backend="rust"),
                         evaluate_fail_conditions(report, {"partial_or_not_verified"}))

    def test_status_casing_and_skips(self):
        for status in ("FAIL", "fail", "SKIP", "skip", "PASS", "", "UNKNOWN"):
            report = {"drat_trim_replay": [{"status": status}],
                      "independent_checker_replay": [{"status": status}]}
            selected = {"drat_replay_failed", "independent_checker_failed"}
            self.assertEqual(evaluate_fail_conditions(report, selected, backend="rust"),
                             evaluate_fail_conditions(report, selected))

    def test_empty_report(self):
        self.assertEqual(evaluate_fail_conditions({}, set(FAIL_OPTIONS), backend="rust"),
                         evaluate_fail_conditions({}, set(FAIL_OPTIONS)))

    def test_seeded_ci_decisions_against_python(self):
        rng = random.Random(5012026)
        verdicts = ("OVERCLAIM", "PARTIALLY_VERIFIED", "ARTIFACT_INTEGRITY_VERIFIED",
                    "PARTIAL_REPLAY_VERIFIED", "", "UNKNOWN")
        for _ in range(512):
            report = {
                "risk_flags": [flag for flag in RISK_FLAGS if rng.randrange(2)],
                "verdict": rng.choice(verdicts),
                "drat_trim_replay": [{"status": rng.choice(("PASS", "FAIL", "SKIP", ""))}],
                "independent_checker_replay": [{"status": rng.choice(("PASS", "FAIL", "SKIP", ""))}],
            }
            enabled = {option for option in FAIL_OPTIONS if rng.randrange(2)}
            self.assertEqual(evaluate_fail_conditions(report, enabled, backend="rust"),
                             evaluate_fail_conditions(report, enabled))

    def test_seeded_marketplace_decisions_against_python(self):
        rng = random.Random(5022026)
        for _ in range(512):
            report = {"risk_flags": [rng.choice(("a", "B", "c", "b")) for _ in range(5)],
                      "verdict": rng.choice(("PARTIAL", "OVERCLAIM", "verified", ""))}
            flags = {flag for flag in ("A", "B", "C", "D") if rng.randrange(2)}
            verdicts = {v for v in ("PARTIAL", "OVERCLAIM", "VERIFIED") if rng.randrange(2)}
            kw = dict(fail_on_risk_flags=flags, fail_on_verdict=verdicts)
            self.assertEqual(evaluate_marketplace_fail_conditions(report, backend="rust", **kw),
                             evaluate_marketplace_fail_conditions(report, **kw))

    def test_marketplace_sorting_is_stable(self):
        report = {"risk_flags": ["B", "a", "B", "A"], "verdict": "overclaim"}
        result = evaluate_marketplace_fail_conditions(report,
            fail_on_risk_flags={"A", "B"}, fail_on_verdict={"OVERCLAIM"}, backend="rust")
        self.assertEqual(result, ["risk_flag:A", "risk_flag:B", "verdict:OVERCLAIM"])


if __name__ == "__main__":
    unittest.main()
