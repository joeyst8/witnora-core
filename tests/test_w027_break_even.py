"""Analytic cross-check of the W027 statistical break-even formula."""

import unittest

from scripts.analyze_w027_break_even import analyze, break_even, NOISE_LEVELS


class W027BreakEvenTests(unittest.TestCase):
    def test_exact_mixture_condition_and_degenerate_cases(self):
        self.assertEqual(break_even(6, 4), {"rule": "UNSAT_fraction_gt", "threshold": 0.6})
        self.assertEqual(break_even(-2, -1), {"rule": "UNSAT_fraction_lt", "threshold": 2 / 3})
        self.assertEqual(break_even(-1, 1)["rule"], "always")
        self.assertEqual(break_even(2, -1)["rule"], "never")

    def test_all_96_synthetic_pairs_and_full_only_guard(self):
        medians = []
        for d in NOISE_LEVELS:
            for r in range(16):
                for status in ("sat", "unsat"):
                    case = f"w026_d{d}_r{r}_{status}"
                    for arm, millis in (("kissat", 10 if status == "sat" else 12),
                                        ("witnora_plus_kissat", 16 if status == "sat" else 8)):
                        medians.append({"case_id": case, "arm": arm,
                                        "solved_repetitions": 3,
                                        "median_solved_wall_ns": millis * 1_000_000})
        mock = {"study": "W-CROSSDOMAIN-027", "phase": "full_preregistered_protocol",
                "per_case_arm_medians": medians}
        result = analyze(mock)
        self.assertEqual(len(result["noise_groups"]), 6)
        for row in result["noise_groups"]:
            self.assertEqual(row["usable_matched_pairs"], 16)
            self.assertEqual(row["mean_sat_overhead_ms"], 6)
            self.assertEqual(row["mean_unsat_saving_ms"], 4)
            self.assertAlmostEqual(row["break_even"]["threshold"], 0.6)
            self.assertEqual(row["conditional_bootstrap_95pct_interval"], [0.6, 0.6])
        mock["phase"] = "exploratory_smoke_not_full_protocol"
        with self.assertRaises(ValueError):
            analyze(mock)


if __name__ == "__main__":
    unittest.main()
