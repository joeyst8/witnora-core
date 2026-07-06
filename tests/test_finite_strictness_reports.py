import tempfile
import unittest
from pathlib import Path

from witnora_core.finite_strictness_certificate import build_outputs


class FiniteStrictnessReportsTest(unittest.TestCase):
    def test_finite_strictness_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "finite"
            build_outputs(instances=["tseitin_10", "xor_chain_unsat_n5"], cap_c=4, out_root=root, zip_path="")
            report = (root / "FINITE_STRICTNESS_CERTIFICATE_REPORT.md").read_text(encoding="utf-8")
        self.assertIn("FINITE_STRICTNESS_CERTIFIED", report)
        self.assertIn("not a scalable family theorem", report)
        self.assertIn("This does not prove full `G0_BASE` strictness.", report)
        print("FINITE_STRICTNESS_REPORT_PASS")

    def test_paper_finite_certificate_section(self):
        paper = Path("paper/WITNORA_COLLAPSE_HIERARCHY_DRAFT.md").read_text(encoding="utf-8")
        self.assertIn("Formal Finite Strictness Certificate", paper)
        self.assertIn("FINITE_STRICTNESS_CERTIFIED is a machine-checked finite-instance certificate", paper)
        print("PAPER_FINITE_CERTIFICATE_SECTION_PASS")


if __name__ == "__main__":
    unittest.main()
