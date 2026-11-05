import unittest
from pathlib import Path

from witnora_core.operator_genesis import (
    generate_operator_candidates,
    extract_fingerprints,
    run_orbit_capacity_lab,
)


class OperatorGenesisPromotionToPrototypeTest(unittest.TestCase):
    def test_operator_genesis_promotion_to_prototype(self):
        candidates = generate_operator_candidates(extract_fingerprints(["pigeonhole", "subset-sum", "near-symmetry"]))
        orbit = next(candidate for candidate in candidates if candidate.name == "ORBIT_COUNTING_COLLAPSE")
        self.assertEqual(orbit.status, "GENERATED_CANDIDATE")
        result = run_orbit_capacity_lab(instances=["hall_local_4_3"], out_root="outputs/test-v25-promotion")
        self.assertEqual(result["g4_operator_delta_summary"]["promoted_candidate"], orbit.name)
        print("G4_GENERATED_OPERATOR_PROTOTYPE_PASS")

    def test_no_pnp_claim(self):
        result = run_orbit_capacity_lab(instances=["hall_local_4_3"], out_root="outputs/test-v25-no-pnp")
        report = (Path(result["out_root"]) / "ORBIT_CAPACITY_COLLAPSE_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("no P vs NP progress claim", report)
        self.assertNotIn("proves P vs NP", report)
        print("NO_PNP_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        result = run_orbit_capacity_lab(instances=["hall_local_4_3"], out_root="outputs/test-v25-no-hard")
        text = "\n".join(str(row) for row in result["orbit_capacity_rows"])
        self.assertNotIn("HARD", text)
        self.assertNotIn("UNKNOWN", text)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
