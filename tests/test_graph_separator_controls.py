import tempfile
import unittest
from pathlib import Path

from witnora_core.graph_separator_lift import run_graph_separator_lab


class GraphSeparatorControlsTest(unittest.TestCase):
    def _payload(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name) / "g8"
        run_graph_separator_lab(
            instances=["separator_sat_pair", "separator_unsat_cover", "grid_3x3_3color"],
            out_root=root,
            strict=True,
            zip_path=None,
        )
        return "\n".join(path.read_text(encoding="utf-8") for path in root.glob("*.json")) + "\n" + (root / "GRAPH_SEPARATOR_LIFT_REPORT.md").read_text(encoding="utf-8")

    def test_graph_separator_no_theorem_claim(self):
        text = self._payload()
        self.assertIn("not a lower-bound", text)
        self.assertNotIn("strictness theorem", text)
        self.assertNotIn("family theorem", text)
        print("GRAPH_SEPARATOR_NO_THEOREM_CLAIM_PASS")

    def test_graph_separator_no_completeness_claim(self):
        text = self._payload()
        self.assertIn("not a graph-formula completeness claim", text)
        self.assertNotIn("solves all graph formulas", text)
        self.assertNotIn("separator completeness theorem", text)
        print("GRAPH_SEPARATOR_NO_COMPLETENESS_CLAIM_PASS")

    def test_no_pnp_claim(self):
        text = self._payload()
        self.assertIn("no P vs NP claim", text)
        self.assertNotIn("proves P vs NP", text)
        print("NO_PNP_CLAIM_PASS")

    def test_no_hard_unknown_status(self):
        text = self._payload()
        self.assertNotIn('"HARD"', text)
        self.assertNotIn('"UNKNOWN"', text)
        self.assertNotIn("HARD", text)
        self.assertNotIn("UNKNOWN", text)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()
