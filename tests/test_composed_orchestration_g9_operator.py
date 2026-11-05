import tempfile
import unittest
from pathlib import Path

from witnora_core.composed_orchestration import (
    FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
    G9_GRAMMAR,
    PROMOTED_RECOMMENDATION,
    SOURCE_OBSTRUCTION,
    SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED,
    UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED,
    run_composed_orchestration_lab,
)


class ComposedOrchestrationG9OperatorTest(unittest.TestCase):
    def _run(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return run_composed_orchestration_lab(
            instances=[
                "affine_separator",
                "cardinality_separator",
                "proof_motif_separator",
                "projection_affine_capacity",
                "composed_sat_lift",
                "composed_unsat_cover",
                "duplicate_single_operator_not_counted",
            ],
            out_root=Path(tmp.name) / "g9",
            strict=True,
            zip_path=None,
        )

    def test_g9_obstruction_recommendation_promoted(self):
        result = self._run()
        delta = result["g9_operator_delta_summary"]
        self.assertEqual(delta["operator_added"], G9_GRAMMAR)
        self.assertEqual(delta["source_obstruction"], SOURCE_OBSTRUCTION)
        self.assertEqual(delta["promoted_recommendation"], PROMOTED_RECOMMENDATION)
        print("G9_OBSTRUCTION_RECOMMENDATION_PROMOTED_PASS")

    def test_g9_operator_delta(self):
        result = self._run()
        rows = result["rows"]
        self.assertTrue(any(row["public_category"] == SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED for row in rows))
        self.assertTrue(any(row["public_category"] == UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED for row in rows))
        self.assertGreaterEqual(result["g9_operator_delta_summary"]["novel_g9_delta_count"], 2)
        self.assertEqual(result["g9_operator_delta_summary"]["evidence_grade"], FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED)
        print("G9_OPERATOR_DELTA_PASS")

    def test_g9_duplicate_single_operator_not_counted(self):
        result = self._run()
        duplicate = [row for row in result["rows"] if row["instance_id"] == "duplicate_single_operator_not_counted"]
        self.assertEqual(len(duplicate), 1)
        self.assertFalse(duplicate[0]["novel_g9_delta"])
        self.assertTrue(duplicate[0]["duplicate_single_operator_not_counted"])
        print("G9_DUPLICATE_SINGLE_OPERATOR_NOT_COUNTED_PASS")


if __name__ == "__main__":
    unittest.main()
