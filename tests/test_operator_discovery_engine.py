import tempfile
import unittest
from pathlib import Path

from witnora_core.collapse_theory import run_collapse_theory_frontier, run_operator_discovery


class OperatorDiscoveryEngineTest(unittest.TestCase):
    def test_operator_discovery_ranking(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_operator_discovery(
                base_grammar="G1_XOR",
                candidate_operators=["symmetry", "cardinality", "xor", "horn", "backdoor", "graph"],
                families=["pigeonhole", "graph-coloring", "parity"],
                out_root=Path(tmp) / "discovery",
            )
            report = (Path(tmp) / "discovery" / "OPERATOR_DISCOVERY_REPORT.md").read_text(encoding="utf-8")
        rankings = result["candidate_operator_rankings"]
        self.assertTrue(rankings)
        self.assertEqual(rankings[0]["candidate_operator"], "SYMMETRY_ORBIT")
        self.assertIn("not a theorem", report)
        print("OPERATOR_DISCOVERY_RANKING_PASS")

    def test_operator_discovery_no_theorem_overclaim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "frontier"
            run_collapse_theory_frontier(
                grammars=["G0_BASE", "G1_XOR", "G2_SYMMETRY_PROTOTYPE"],
                families=["pigeonhole", "graph-coloring"],
                out_root=root,
                prefer_official_tseitin=False,
            )
            text = (root / "COLLAPSE_THEORY_FRONTIER_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("conjectural", text)
        self.assertIn("does not claim P vs NP progress", text)
        self.assertIn("does not claim symmetry has collapsed pigeonhole", text)
        print("OPERATOR_DISCOVERY_NO_THEOREM_OVERCLAIM_PASS")

    def test_no_hard_unknown_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "frontier"
            run_collapse_theory_frontier(
                grammars=["G1_XOR", "G2_SYMMETRY_PROTOTYPE"],
                families=["pigeonhole", "graph-coloring", "adversarial-near-symmetry"],
                out_root=root,
                prefer_official_tseitin=False,
            )
            status_text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in [
                    root / "operator_discovery_results.json",
                    root / "candidate_operator_rankings.json",
                    root / "obstruction_records.json",
                ]
            )
        self.assertNotIn('"HARD"', status_text)
        self.assertNotIn('"UNKNOWN"', status_text)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
