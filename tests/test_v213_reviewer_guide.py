import tempfile
import unittest
from pathlib import Path

from witnora_core.paper_hardening import build_paper_hardening_package, reviewer_guide_text


class V213ReviewerGuideTest(unittest.TestCase):
    def test_reviewer_guide_present(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = build_paper_hardening_package(out_root=Path(tmp) / "pkg", zip_path="")
            guide = Path(result["out_root"]) / "REVIEWER_GUIDE.md"
            self.assertTrue(guide.is_file())
            self.assertIn("What to read first", guide.read_text(encoding="utf-8"))
        print("REVIEWER_GUIDE_PRESENT_PASS")

    def test_reviewer_guide_inspection_order(self):
        guide = reviewer_guide_text()
        self.assertIn("What to read first", guide)
        self.assertIn("How to inspect v2.10 finite strictness certificate", guide)
        self.assertIn("How to inspect v2.11 finite empirical edge delta", guide)
        self.assertIn("Should the hierarchy be a lattice instead of a chain?", guide)
        print("REVIEWER_GUIDE_INSPECTION_ORDER_PASS")


if __name__ == "__main__":
    unittest.main()
