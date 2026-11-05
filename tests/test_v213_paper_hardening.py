import unittest
from pathlib import Path

from witnora_core.reproducibility_package import external_paper_text


class V213PaperHardeningTest(unittest.TestCase):
    def test_related_work_section(self):
        paper = external_paper_text()
        self.assertIn("## Related Work", paper)
        self.assertIn("SAT preprocessing", paper)
        self.assertIn("certified SAT solving", paper)
        self.assertIn("proof compression", paper)
        print("PAPER_RELATED_WORK_PASS")

    def test_contribution_table(self):
        paper = external_paper_text()
        self.assertIn("## Contribution Table", paper)
        self.assertIn("Bounded collapse hierarchy G0-G6", paper)
        self.assertIn("what is not claimed", paper.lower())
        print("PAPER_CONTRIBUTION_TABLE_PASS")

    def test_reviewer_objection_table(self):
        paper = external_paper_text()
        self.assertIn("## Reviewer Objection Table", paper)
        self.assertIn("Empirical edge deltas are not lower bounds.", paper)
        self.assertIn("no peer-review acceptance is claimed", paper)
        print("PAPER_REVIEWER_OBJECTION_TABLE_PASS")

    def test_limitations_section(self):
        paper = external_paper_text()
        self.assertIn("## Limitations", paper)
        self.assertIn("No P vs NP progress", paper)
        self.assertIn("Native checkers are not formally verified proof-assistant artifacts.", paper)
        print("PAPER_LIMITATIONS_SECTION_PASS")

    def test_claim_boundary_appendix(self):
        paper = Path("paper/WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md").read_text(encoding="utf-8")
        self.assertIn("## Claim-Boundary Appendix", paper)
        self.assertIn("Allowed wording", paper)
        self.assertIn("Forbidden wording", paper)
        print("PAPER_CLAIM_BOUNDARY_APPENDIX_PASS")


if __name__ == "__main__":
    unittest.main()
