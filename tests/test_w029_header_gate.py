"""Check the paired-header audit does not silently manufacture separation."""

from copy import deepcopy
import unittest

from scripts.audit_w029_header_gate import audit


def fixture():
    cases = [
        ("w026_d0_r0_sat", "SAT", 10, 20),
        ("w026_d0_r0_unsat", "UNSAT", 10, 6),
    ]
    return {
        "study": "W-CROSSDOMAIN-027",
        "phase": "full_preregistered_protocol",
        "witnora_source_sha": "fixture",
        "rows": [
            {"stratum": "synthetic_xor", "arm": "kissat", "repeat": 0,
             "case_id": name, "variables": 64, "clauses": 20, "expected": expected}
            for name, expected, _, _ in cases
        ],
        "per_case_arm_medians": [
            {"stratum": "synthetic_xor", "arm": arm, "case_id": name,
             "solved_repetitions": 3, "median_solved_wall_ns": ns * 1_000_000}
            for name, _, kissat, witnora in cases
            for arm, ns in (("kissat", kissat), ("witnora_plus_kissat", witnora))
        ],
    }


class HeaderAuditTests(unittest.TestCase):
    def test_matched_costs_make_unconditional_gate_worse(self):
        result = audit(fixture())
        self.assertEqual(result["matched_pair_count"], 1)
        self.assertTrue(result["all_header_bins_balanced"])
        self.assertEqual(result["best_header_only_gate_for_these_empirical_bins"], "SKIP_EVERYWHERE")
        # (SAT penalty 10ms - UNSAT saving 4ms) / 2
        self.assertEqual(result["groups"][0]["mean_full_precheck_extra_ms_per_case"], 3)

    def test_mismatched_header_fails(self):
        report = deepcopy(fixture())
        report["rows"][1]["clauses"] = 19
        with self.assertRaisesRegex(ValueError, "header feature mismatch"):
            audit(report)

    def test_nonfull_run_rejected(self):
        report = fixture()
        report["phase"] = "exploratory_smoke_not_full_protocol"
        with self.assertRaisesRegex(ValueError, "frozen W027"):
            audit(report)


if __name__ == "__main__":
    unittest.main()
