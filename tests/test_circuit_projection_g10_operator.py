import tempfile
import unittest
from pathlib import Path

from witnora_core.circuit_projection_lift import (
    FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
    G10_GRAMMAR,
    PROMOTED_RECOMMENDATION,
    SOURCE_RECOMMENDATION_SIGNAL,
    CIRCUIT_PROJECTION_NO_NEW_DELTA,
    SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED,
    UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED,
    run_circuit_projection_lab,
)


class CircuitProjectionG10OperatorTest(unittest.TestCase):
    def _run(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        return run_circuit_projection_lab(
            instances=[
                "and_gate_sat",
                "or_gate_sat",
                "not_gate_sat",
                "half_adder_sat",
                "mux2_sat",
                "mux4_sat",
                "circuit_unsat_control",
                "projected_affine_core",
                "projected_capacity_core",
            ],
            out_root=Path(tmp.name) / "g10",
            strict=True,
            zip_path=None,
        )

    def test_g10_obstruction_recommendation_promoted(self):
        result = self._run()
        delta = result["g10_operator_delta_summary"]
        self.assertEqual(delta["operator_added"], G10_GRAMMAR)
        self.assertEqual(delta["source_recommendation_signal"], SOURCE_RECOMMENDATION_SIGNAL)
        self.assertEqual(delta["promoted_recommendation"], PROMOTED_RECOMMENDATION)
        print("G10_OBSTRUCTION_RECOMMENDATION_PROMOTED_PASS")

    def test_g10_operator_delta(self):
        result = self._run()
        rows = result["rows"]
        self.assertTrue(any(row["public_category"] == SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED for row in rows))
        self.assertTrue(any(row["public_category"] == UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED for row in rows))
        self.assertGreaterEqual(result["g10_operator_delta_summary"]["novel_g10_delta_count"], 3)
        self.assertEqual(result["g10_operator_delta_summary"]["evidence_grade"], FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED)
        print("G10_OPERATOR_DELTA_PASS")

    def test_g10_trivial_gate_not_counted(self):
        result = self._run()
        trivial = [row for row in result["rows"] if row["instance_id"] in {"and_gate_sat", "or_gate_sat", "not_gate_sat"}]
        self.assertEqual(len(trivial), 3)
        self.assertTrue(all(row["public_category"] == CIRCUIT_PROJECTION_NO_NEW_DELTA for row in trivial))
        self.assertTrue(all(row["novel_g10_delta"] is False for row in trivial))
        print("G10_TRIVIAL_GATE_NOT_COUNTED_PASS")

    def test_g10_orchestration_integration(self):
        result = self._run()
        integrated = result["orchestration_integration_summary"]
        self.assertTrue(integrated)
        self.assertTrue(all(row["orchestration_trace"]["chain_verified"] for row in integrated))
        print("G10_ORCHESTRATION_INTEGRATION_PASS")


if __name__ == "__main__":
    unittest.main()
