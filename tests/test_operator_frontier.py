import tempfile
import unittest
from pathlib import Path

from witnora_core.collapse_theory import run_frontier_search


class OperatorFrontierTest(unittest.TestCase):
    def test_operator_frontier_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "frontier"
            result = run_frontier_search(
                base_grammar="G1_XOR",
                candidate_operators=["horn", "cardinality", "backdoor"],
                families=["pigeonhole", "adversarial-mixed"],
                out_root=root,
            )
            report = (root / "OPERATOR_FRONTIER_REPORT.md").read_text(encoding="utf-8")
            self.assertTrue((root / "frontier_failures.json").exists())
            self.assertTrue((root / "candidate_operator_recommendations.json").exists())
        self.assertTrue(result["frontier_failures"])
        self.assertIn("Operator Frontier Report", report)
        self.assertIn("does not claim", report)
        print("OPERATOR_FRONTIER_REPORT_PASS")


if __name__ == "__main__":
    unittest.main()
