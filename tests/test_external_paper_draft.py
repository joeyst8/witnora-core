import unittest
from pathlib import Path

from witnora_core.reproducibility_package import external_paper_text


class ExternalPaperDraftTest(unittest.TestCase):
    def test_external_paper_draft_complete(self):
        paper = external_paper_text()
        for section in [
            "## Abstract",
            "## Introduction",
            "## Motivation: Verifier-to-Witness Collapse",
            "## Non-Claims",
            "## Bounded Collapse Classes W_B(G)",
            "## Grammar Hierarchy G0-G6",
            "## Native Certificate Types",
            "## Operator Genesis",
            "## Finite Strictness Certificate: G0_WIDTH_C -> G1_XOR",
            "## Finite Empirical Edge Delta: G1_XOR -> G2_SYMMETRY_CERTIFIED",
            "## Empirical Evidence for G2-G6",
            "## Proof Obligations",
            "## Gap Analysis",
            "## Relationship to P vs NP",
            "## Why This Does Not Prove P vs NP",
            "## Reproducibility",
            "## Limitations",
            "## Future Work",
        ]:
            self.assertIn(section, paper)
        self.assertIn("Witnora Collapse Hierarchy: Certificate-Backed Operator Discovery", paper)
        print("PAPER_EXTERNAL_DRAFT_COMPLETE_PASS")

    def test_paper_required_nonclaims(self):
        paper = Path("paper/WITNORA_COLLAPSE_HIERARCHY_EXTERNAL_DRAFT.md").read_text(encoding="utf-8")
        for phrase in [
            "This work does not prove P vs NP.",
            "This work does not claim a polynomial-time SAT algorithm.",
            "Strictness is only claimed where a finite strictness certificate with lower obstruction evidence is verified.",
            "FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED is not a lower-bound proof.",
            "Native certificates are not DRAT proofs unless explicitly exported and checked.",
            "The hierarchy is a research program, not a complete SAT algorithm.",
        ]:
            self.assertIn(phrase, paper)
        print("PAPER_REQUIRED_NONCLAIMS_PASS")
        print("NO_POLYTIME_SAT_CLAIM_PASS")
        print("NO_PNP_CLAIM_PASS")


if __name__ == "__main__":
    unittest.main()
