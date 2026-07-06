import tempfile
import unittest
from pathlib import Path

from witnora_core.graph_separator_lift import (
    G8_GRAMMAR,
    PROMOTED_RECOMMENDATION,
    GRAPH_SEPARATOR_NO_NEW_DELTA,
    SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED,
    UNSAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED,
    run_graph_separator_lab,
)


class GraphSeparatorG8OperatorTest(unittest.TestCase):
    def _run(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return run_graph_separator_lab(
            instances=[
                "separator_sat_pair",
                "separator_unsat_cover",
                "grid_3x3_3color",
                "grid_4x4_3color",
            ],
            out_root=Path(tmp.name) / "g8",
            strict=True,
            zip_path=None,
        )

    def test_g8_obstruction_recommendation_promoted(self):
        result = self._run()
        delta = result["g8_operator_delta_summary"]
        self.assertEqual(delta["operator_added"], G8_GRAMMAR)
        self.assertEqual(delta["promoted_recommendation"], PROMOTED_RECOMMENDATION)
        print("G8_OBSTRUCTION_RECOMMENDATION_PROMOTED_PASS")

    def test_g8_operator_delta(self):
        result = self._run()
        rows = result["rows"]
        self.assertTrue(any(row["public_category"] == SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED for row in rows))
        self.assertTrue(any(row["public_category"] == UNSAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED for row in rows))
        self.assertGreaterEqual(result["g8_operator_delta_summary"]["novel_g8_delta_count"], 2)
        print("G8_OPERATOR_DELTA_PASS")

    def test_g8_duplicate_prior_not_counted(self):
        result = self._run()
        grid_rows = [row for row in result["rows"] if row["instance_id"].startswith("grid_")]
        self.assertTrue(grid_rows)
        self.assertTrue(all(row["prior_replay_status"] == GRAPH_SEPARATOR_NO_NEW_DELTA for row in grid_rows))
        self.assertTrue(all(row["novel_g8_delta"] is False for row in grid_rows))
        print("G8_DUPLICATE_PRIOR_NOT_COUNTED_PASS")


if __name__ == "__main__":
    unittest.main()
