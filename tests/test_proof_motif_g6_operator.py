import unittest
from pathlib import Path

from witnora_core.operator_genesis import (
    DUPLICATE_OF_G1_XOR_PATTERN,
    G6_PROOF_MOTIF_NATIVE_CERTIFIED,
    run_proof_motif_lab,
)


class ProofMotifG6OperatorTest(unittest.TestCase):
    def test_motif_ladder_rows(self):
        result = run_proof_motif_lab(instances=["motif_ladder_4", "motif_ladder_8"], out_root="outputs/test-v27-ladders")
        rows = {row["instance_id"]: row for row in result["proof_motif_rows"]}
        self.assertEqual(rows["motif_ladder_4"]["g6_delta_status"], G6_PROOF_MOTIF_NATIVE_CERTIFIED)
        self.assertEqual(rows["motif_ladder_8"]["g6_delta_status"], G6_PROOF_MOTIF_NATIVE_CERTIFIED)
        print("MOTIF_LADDER_4_PASS")
        print("MOTIF_LADDER_8_PASS")

    def test_renamed_and_selector_rows(self):
        result = run_proof_motif_lab(
            instances=["renamed_conflict_motif_8", "motif_chain_with_selectors_8"],
            out_root="outputs/test-v27-renamed-selector",
        )
        rows = {row["instance_id"]: row for row in result["proof_motif_rows"]}
        self.assertEqual(rows["renamed_conflict_motif_8"]["g6_delta_status"], G6_PROOF_MOTIF_NATIVE_CERTIFIED)
        self.assertEqual(rows["motif_chain_with_selectors_8"]["g6_delta_status"], G6_PROOF_MOTIF_NATIVE_CERTIFIED)
        print("RENAMED_CONFLICT_MOTIF_PASS")
        print("MOTIF_CHAIN_WITH_SELECTORS_PASS")

    def test_g6_operator_delta_and_prototype(self):
        result = run_proof_motif_lab(
            instances=["motif_ladder_4", "motif_ladder_8", "tseitin_grid_optional"],
            out_root="outputs/test-v27-g6-delta",
        )
        summary = result["g6_operator_delta_summary"]
        self.assertEqual(summary["operator_added"], "G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE")
        self.assertEqual(summary["promoted_candidate"], "PROOF_MOTIF_COMPRESSION")
        self.assertGreaterEqual(summary["novel_g6_deltas"], 2)
        print("G6_OPERATOR_DELTA_PASS")
        print("G6_GENERATED_OPERATOR_PROTOTYPE_PASS")

    def test_g6_strictness_not_theorem(self):
        result = run_proof_motif_lab(instances=["motif_ladder_4"], out_root="outputs/test-v27-not-theorem")
        statuses = {item["status"] for item in result["theorem_candidates"]}
        self.assertIn("EMPIRICAL_EVIDENCE_NOT_THEOREM", statuses)
        self.assertNotIn("THEOREM", statuses)
        print("G6_STRICTNESS_NOT_THEOREM_PASS")

    def test_tseitin_duplicate_not_counted(self):
        result = run_proof_motif_lab(instances=["tseitin_grid_optional"], out_root="outputs/test-v27-tseitin-duplicate")
        row = result["proof_motif_rows"][0]
        self.assertEqual(row["g6_delta_status"], DUPLICATE_OF_G1_XOR_PATTERN)
        self.assertFalse(row["novel_g6_delta"])
        print("TSEITIN_DUPLICATE_NOT_COUNTED_PASS")

    def test_claim_boundary(self):
        result = run_proof_motif_lab(instances=["motif_ladder_4"], out_root="outputs/test-v27-claim-boundary")
        report = (Path(result["out_root"]) / "PROOF_MOTIF_COMPRESSION_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("no P vs NP progress claim", report)
        self.assertIn("no DRAT verification claim", report)
        text = "\n".join(str(row) for row in result["proof_motif_rows"])
        self.assertNotIn("HARD", text)
        self.assertNotIn("UNKNOWN", text)
        print("NO_PNP_CLAIM_PASS")
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
