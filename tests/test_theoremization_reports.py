import json
import tempfile
import unittest
from pathlib import Path

from witnora_core.hierarchy_formalization import build_hierarchy_theoremization


def _status_values(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key.endswith("status") or key in {"status", "current_status", "strictness_status", "empirical_status"}:
                yield value
            yield from _status_values(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from _status_values(item)


class TheoremizationReportsTest(unittest.TestCase):
    def test_paper_draft_nonclaims(self):
        with tempfile.TemporaryDirectory() as tmp:
            build_hierarchy_theoremization(out_root=Path(tmp) / "theoremization", zip_path="")
        paper = Path("paper/WITNORA_COLLAPSE_HIERARCHY_DRAFT.md").read_text(encoding="utf-8")
        self.assertIn("This work does not prove P vs NP.", paper)
        self.assertIn("Strictness results are empirical unless marked with a formal proof.", paper)
        self.assertIn("Native certificates are not DRAT unless explicitly exported and checked.", paper)
        self.assertIn("The hierarchy is a research program, not a complete SAT algorithm.", paper)
        print("PAPER_DRAFT_NONCLAIMS_PASS")

    def test_no_hard_unknown_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "theoremization"
            build_hierarchy_theoremization(out_root=root, zip_path="")
            payloads = [
                json.loads((root / "hierarchy_edges.json").read_text(encoding="utf-8")),
                json.loads((root / "empirical_strictness_evidence.json").read_text(encoding="utf-8")),
                json.loads((root / "theorem_candidates_v28.json").read_text(encoding="utf-8")),
                json.loads((root / "proof_obligation_matrix.json").read_text(encoding="utf-8")),
            ]
        statuses = [value for payload in payloads for value in _status_values(payload)]
        self.assertNotIn("HARD", statuses)
        self.assertNotIn("UNKNOWN", statuses)
        self.assertNotIn("PROVEN", statuses)
        print("NO_HARD_UNKNOWN_STATUS_PASS")


if __name__ == "__main__":
    unittest.main()

