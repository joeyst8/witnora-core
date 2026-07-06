import unittest

from witnora_core.external_review_package_v224 import paper_text


class ExternalReviewPaperV224Test(unittest.TestCase):
    def test_external_review_paper_required_sections_and_nonclaims(self):
        text = paper_text()
        for heading in [
            "## Abstract",
            "## Collapse Grammar Hierarchy G0-G14",
            "## TC-063 Bounded Separator-Affine Family Theorem",
            "## Reproducibility",
            "## Claim Boundaries",
            "## Limitations",
        ]:
            self.assertIn(heading, text)
        self.assertIn("Witnora does not claim a proof of P vs NP.", text)
        self.assertIn("TC-063 is a restricted theorem with proof obligations over SAF(c,r), not an all-SAT theorem.", text)
        self.assertIn("Native certificates are not DRAT/LRAT/FRAT unless explicitly exported and externally checked.", text)
        self.assertIn("Finite evidence supports implementation behavior but does not substitute for a family proof.", text)
        self.assertIn("Planner certificates are plan-only unless paired with separate verified execution certificates.", text)
        print("EXTERNAL_REVIEW_PAPER_UPDATED_PASS")


if __name__ == "__main__":
    unittest.main()
