import unittest

from witnora_core.operator_genesis import (
    DUPLICATE_OF_G3_PIGEONHOLE_PATTERN,
    G4_ORBIT_CAPACITY_NATIVE_CERTIFIED,
    ORBIT_COUNTING_DRAT_NOT_CLAIMED,
    run_orbit_capacity_lab,
)


class OrbitCapacityG4OperatorTest(unittest.TestCase):
    def test_g4_operator_delta(self):
        result = run_orbit_capacity_lab(
            instances=["hall_local_4_3", "complete_match_3_2", "hall_balanced_3_3_sat_control"],
            out_root="outputs/test-v25-g4-delta",
        )
        summary = result["g4_operator_delta_summary"]
        self.assertEqual(summary["operator_added"], "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE")
        self.assertGreaterEqual(summary["novel_local_hall_deltas"], 1)
        print("G4_OPERATOR_DELTA_PASS")

    def test_g4_duplicate_g3_not_counted(self):
        result = run_orbit_capacity_lab(instances=["complete_match_3_2"], out_root="outputs/test-v25-duplicate")
        row = result["orbit_capacity_rows"][0]
        self.assertEqual(row["g4_delta_status"], DUPLICATE_OF_G3_PIGEONHOLE_PATTERN)
        self.assertFalse(row["novel_g4_delta"])
        print("G4_DUPLICATE_G3_NOT_COUNTED_PASS")

    def test_g4_generated_operator_prototype(self):
        result = run_orbit_capacity_lab(instances=["hall_local_5_4"], out_root="outputs/test-v25-generated-prototype")
        row = result["orbit_capacity_rows"][0]
        self.assertEqual(result["g4_operator_delta_summary"]["promoted_candidate"], "ORBIT_COUNTING_COLLAPSE")
        self.assertEqual(row["g4_delta_status"], G4_ORBIT_CAPACITY_NATIVE_CERTIFIED)
        print("G4_GENERATED_OPERATOR_PROTOTYPE_PASS")

    def test_orbit_capacity_no_matching_completeness_claim(self):
        result = run_orbit_capacity_lab(instances=["hall_local_4_3"], out_root="outputs/test-v25-no-completeness")
        report = ( __import__("pathlib").Path(result["out_root"]) / "ORBIT_CAPACITY_COLLAPSE_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("does not claim a full matching solver", report)
        self.assertIn("no full matching/allocation solver claim", result["g4_operator_delta_summary"]["claim_boundary"])
        print("ORBIT_CAPACITY_NO_MATCHING_COMPLETENESS_CLAIM_PASS")

    def test_generated_operator_not_theorem(self):
        result = run_orbit_capacity_lab(instances=["hall_local_4_3"], out_root="outputs/test-v25-not-theorem")
        statuses = {item["status"] for item in result["theorem_candidates"]}
        self.assertIn("EMPIRICAL_EVIDENCE_NOT_THEOREM", statuses)
        self.assertNotIn("THEOREM", statuses)
        print("GENERATED_OPERATOR_NOT_THEOREM_PASS")

    def test_no_fake_drat_claims_in_lab(self):
        result = run_orbit_capacity_lab(instances=["hall_local_4_3", "complete_match_3_2"], out_root="outputs/test-v25-no-drat")
        self.assertEqual(result["g4_operator_delta_summary"]["fake_drat_claims"], 0)
        for row in result["orbit_capacity_rows"]:
            self.assertEqual(row["drat_claim"], ORBIT_COUNTING_DRAT_NOT_CLAIMED)
        print("ORBIT_CAPACITY_NO_FAKE_DRAT_PASS")


if __name__ == "__main__":
    unittest.main()
