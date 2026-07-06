import tempfile
import unittest
from pathlib import Path

from witnora_core.hierarchy_formalization import (
    EMPIRICAL_NOT_THEOREM,
    G_CHAIN,
    bounded_collapse_classes,
    build_hierarchy_theoremization,
    grammar_definitions,
)


class HierarchyFormalizationTest(unittest.TestCase):
    def test_hierarchy_grammar_definitions(self):
        grammars = grammar_definitions()
        self.assertEqual([item.name for item in grammars], G_CHAIN)
        self.assertEqual(grammars[-1].name, "G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE")
        print("HIERARCHY_GRAMMAR_DEFINITIONS_PASS")
        print("HIERARCHY_FULL_CHAIN_G0_TO_G6_PASS")

    def test_bounded_collapse_class_definition(self):
        classes = bounded_collapse_classes()
        self.assertEqual(len(classes), len(G_CHAIN))
        text = classes[0].membership_definition
        self.assertIn("SAT witness verified against the original CNF", text)
        self.assertIn("accepted native certificate", text)
        self.assertIn("within configured cost", text)
        self.assertTrue(all(item.notation.startswith("W_B(") for item in classes))
        print("BOUNDED_COLLAPSE_CLASS_DEFINITION_PASS")

    def test_build_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "theoremization"
            result = build_hierarchy_theoremization(out_root=root, zip_path="")
            required = [
                "grammar_definitions.json",
                "operator_definitions.json",
                "bound_profile_definitions.json",
                "bounded_collapse_classes.json",
                "hierarchy_edges.json",
                "empirical_strictness_evidence.json",
                "theorem_candidates_v28.json",
                "proof_obligation_matrix.json",
                "hierarchy_evidence_bundle.json",
                "gap_analysis.json",
                "COLLAPSE_HIERARCHY_THEOREMIZATION_REPORT.md",
            ]
            for name in required:
                self.assertTrue((root / name).exists(), name)
        statuses = {row["strictness_status"] for row in result["empirical_strictness_evidence"]}
        self.assertEqual(statuses, {EMPIRICAL_NOT_THEOREM})
        print("EMPIRICAL_STRICTNESS_EVIDENCE_PASS")
        print("STRICTNESS_STATUS_NOT_THEOREM_PASS")


if __name__ == "__main__":
    unittest.main()

