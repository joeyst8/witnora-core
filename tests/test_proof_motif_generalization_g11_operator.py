import tempfile
import unittest
from pathlib import Path

from witnora_core.proof_motif_generalization import (
    FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
    G11_GRAMMAR,
    G11_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED,
    PROMOTED_RECOMMENDATION,
    SOURCE_RECOMMENDATION,
    run_proof_motif_generalization_lab,
)


class ProofMotifGeneralizationG11OperatorTest(unittest.TestCase):
    def _run(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return run_proof_motif_generalization_lab(
            instances=[
                "ladder_near_4",
                "ladder_near_8",
                "chain_near_6",
                "gadget_variants",
                "proof_motif_near_miss",
                "exact_motif_duplicate_control",
                "loose_similarity_reject",
            ],
            out_root=Path(tmp.name) / "g11",
            strict=True,
            zip_path=None,
        )

    def test_g11_obstruction_recommendation_promoted(self):
        result = self._run()
        summary = result["g11_operator_delta_summary"]
        self.assertEqual(summary["operator_added"], G11_GRAMMAR)
        self.assertEqual(summary["source_recommendation"], SOURCE_RECOMMENDATION)
        self.assertEqual(summary["promoted_recommendation"], PROMOTED_RECOMMENDATION)
        print("G11_OBSTRUCTION_RECOMMENDATION_PROMOTED_PASS")

    def test_g11_operator_delta(self):
        result = self._run()
        summary = result["g11_operator_delta_summary"]
        self.assertGreaterEqual(summary["novel_g11_delta_count"], 4)
        self.assertEqual(summary["evidence_grade"], FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED)
        self.assertTrue(any(row["g11_delta_status"] == G11_PROOF_MOTIF_GENERALIZATION_NATIVE_CERTIFIED for row in result["rows"]))
        print("G11_OPERATOR_DELTA_PASS")

    def test_exact_motif_duplicate_not_counted(self):
        result = self._run()
        row = {item["instance_id"]: item for item in result["rows"]}["exact_motif_duplicate_control"]
        self.assertTrue(row["duplicate_of_g6"])
        self.assertFalse(row["novel_g11_delta"])
        self.assertEqual(row["g11_delta_status"], "PROOF_MOTIF_GENERALIZED_NO_NEW_DELTA")
        print("G11_EXACT_MOTIF_DUPLICATE_NOT_COUNTED_PASS")


if __name__ == "__main__":
    unittest.main()
