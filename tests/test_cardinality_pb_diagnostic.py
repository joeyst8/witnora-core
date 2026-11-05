import tempfile
import unittest
from pathlib import Path

from witnora_core.collapse_theory import (
    CARDINALITY_STRUCTURE_DETECTED,
    detect_cardinality_pb,
    run_symmetry_lab,
)
from witnora_core.cnf import CNFFormula


class CardinalityPBDiagnosticTest(unittest.TestCase):
    def test_cardinality_pb_detection(self):
        formula = CNFFormula.from_raw_clauses([[1, 2, 3], [-1, -2], [-1, -3], [-2, -3]])
        result = detect_cardinality_pb(formula)
        self.assertEqual(result["status"], CARDINALITY_STRUCTURE_DETECTED)
        self.assertEqual(result["exactly_one_constraints"], [[1, 2, 3]])
        print("CARDINALITY_PB_DETECTION_PASS")

    def test_cardinality_pb_no_solver_overclaim(self):
        formula = CNFFormula.from_raw_clauses([[1, 2], [-1, -2]])
        result = detect_cardinality_pb(formula)
        self.assertEqual(result["solver_claim"], "NO_PB_SOLVING_CLAIM")
        self.assertNotIn("SAT_ASSIGNMENT_VERIFIED", str(result))
        print("CARDINALITY_PB_NO_SOLVER_OVERCLAIM_PASS")

    def test_no_pnp_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "symmetry"
            run_symmetry_lab(families=["symmetric-toy", "pigeonhole"], out_root=root)
            text = (root / "CERTIFIED_SYMMETRY_COLLAPSE_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("does not claim P vs NP progress", text)
        self.assertNotIn("proves P vs NP", text)
        print("NO_PNP_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "symmetry"
            run_symmetry_lab(families=["symmetric-toy", "pigeonhole"], out_root=root)
            payload = "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.json"))
        self.assertNotIn('"HARD"', payload)
        self.assertNotIn('"UNKNOWN"', payload)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
