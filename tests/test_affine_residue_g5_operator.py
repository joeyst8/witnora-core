import unittest
from pathlib import Path

from witnora_core.operator_genesis import (
    G5_AFFINE_RESIDUE_NATIVE_CERTIFIED,
    SAT_AFFINE_RESIDUE_NATIVE_CERTIFIED,
    UNSAT_AFFINE_RESIDUE_NATIVE_CERTIFIED,
    run_affine_residue_lab,
)


class AffineResidueG5OperatorTest(unittest.TestCase):
    def test_parity_arity_rows(self):
        result = run_affine_residue_lab(
            instances=["parity_arity_7_unsat", "parity_arity_8_unsat", "parity_arity_9_unsat", "parity_arity_10_unsat"],
            out_root="outputs/test-v26-parity-rows",
        )
        rows = {row["instance_id"]: row for row in result["affine_residue_rows"]}
        for arity in (7, 8, 9, 10):
            row = rows[f"parity_arity_{arity}_unsat"]
            self.assertEqual(row["public_category"], UNSAT_AFFINE_RESIDUE_NATIVE_CERTIFIED)
            self.assertEqual(row["g5_delta_status"], G5_AFFINE_RESIDUE_NATIVE_CERTIFIED)
            print(f"PARITY_ARITY_{arity}_PASS")

    def test_sat_and_mixed_affine_results(self):
        result = run_affine_residue_lab(
            instances=["parity_arity_7_sat", "parity_arity_8_sat", "mixed_affine_arity_8_unsat", "mixed_affine_arity_8_sat"],
            out_root="outputs/test-v26-sat-mixed",
        )
        rows = {row["instance_id"]: row for row in result["affine_residue_rows"]}
        self.assertEqual(rows["parity_arity_7_sat"]["public_category"], SAT_AFFINE_RESIDUE_NATIVE_CERTIFIED)
        self.assertEqual(rows["parity_arity_8_sat"]["public_category"], SAT_AFFINE_RESIDUE_NATIVE_CERTIFIED)
        self.assertEqual(rows["mixed_affine_arity_8_unsat"]["public_category"], UNSAT_AFFINE_RESIDUE_NATIVE_CERTIFIED)
        self.assertEqual(rows["mixed_affine_arity_8_sat"]["public_category"], SAT_AFFINE_RESIDUE_NATIVE_CERTIFIED)

    def test_g5_operator_delta(self):
        result = run_affine_residue_lab(
            instances=["parity_arity_7_unsat", "parity_arity_8_sat", "incomplete_affine_reject"],
            out_root="outputs/test-v26-g5-delta",
        )
        summary = result["g5_operator_delta_summary"]
        self.assertEqual(summary["operator_added"], "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE")
        self.assertEqual(summary["promoted_candidate"], "MODULAR_RESIDUE_COLLAPSE")
        self.assertGreaterEqual(summary["native_certified"], 2)
        print("G5_OPERATOR_DELTA_PASS")

    def test_g5_generated_operator_prototype(self):
        result = run_affine_residue_lab(instances=["parity_arity_7_unsat"], out_root="outputs/test-v26-generated-prototype")
        self.assertEqual(result["g5_operator_delta_summary"]["promoted_candidate"], "MODULAR_RESIDUE_COLLAPSE")
        print("G5_GENERATED_OPERATOR_PROTOTYPE_PASS")

    def test_g5_strictness_not_theorem(self):
        result = run_affine_residue_lab(instances=["parity_arity_7_unsat"], out_root="outputs/test-v26-not-theorem")
        statuses = {item["status"] for item in result["theorem_candidates"]}
        self.assertIn("EMPIRICAL_EVIDENCE_NOT_THEOREM", statuses)
        self.assertNotIn("THEOREM", statuses)
        print("G5_STRICTNESS_NOT_THEOREM_PASS")

    def test_modular_residue_no_broad_solver_claim(self):
        result = run_affine_residue_lab(instances=["parity_arity_7_unsat"], out_root="outputs/test-v26-no-broad")
        report = (Path(result["out_root"]) / "AFFINE_RESIDUE_COLLAPSE_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("no broad modular arithmetic solver claim", report)
        self.assertIn("no CryptoMiniSat-style XOR mining claim", report)
        print("MODULAR_RESIDUE_NO_BROAD_SOLVER_CLAIM_PASS")

    def test_no_pnp_or_hard_unknown_status(self):
        result = run_affine_residue_lab(instances=["parity_arity_7_unsat"], out_root="outputs/test-v26-claim-boundary")
        report = (Path(result["out_root"]) / "AFFINE_RESIDUE_COLLAPSE_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("no P vs NP progress claim", report)
        text = "\n".join(str(row) for row in result["affine_residue_rows"])
        self.assertNotIn("HARD", text)
        self.assertNotIn("UNKNOWN", text)
        print("NO_PNP_CLAIM_PASS")
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
