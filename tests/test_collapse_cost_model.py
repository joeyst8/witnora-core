import tempfile
import unittest
from pathlib import Path

from witnora_core.collapse_theory import (
    bound_profiles,
    run_theory_experiment,
)


class CollapseCostModelTest(unittest.TestCase):
    def test_collapse_cost_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_theory_experiment(
                grammars=["G0_BASE", "G1_XOR"],
                families=["xor-chain"],
                out_root=Path(tmp) / "lab",
                prefer_official_tseitin=False,
            )
        row = next(item for item in result["results"] if item["grammar"] == "G1_XOR")
        cost = row["collapse_cost"]
        for key in [
            "path_length",
            "operator_applications",
            "peak_formula_size",
            "peak_clause_count",
            "peak_variable_count",
            "peak_width",
            "proof_clause_count",
            "proof_bytes",
            "runtime_seconds",
            "external_verification_runtime_seconds",
            "certificate_size_bytes",
            "search_nodes_expanded",
            "resource_bound_profile",
        ]:
            self.assertIn(key, cost)
        self.assertIn("bounded_cost_status", row)
        print("COLLAPSE_COST_SCHEMA_PASS")

    def test_bounded_collapse_class_doc(self):
        self.assertIn("B_V21_DEFAULT", bound_profiles())
        text = Path("docs/COLLAPSE_THEORY_LAB.md").read_text(encoding="utf-8")
        theory = Path("theory/COLLAPSE_GRAMMAR_PROGRAM.md").read_text(encoding="utf-8")
        self.assertIn("W_B(G)", text)
        self.assertIn("W_B(G)", theory)
        self.assertIn("not a proof", text)
        print("BOUNDED_COLLAPSE_CLASS_DOC_PASS")


if __name__ == "__main__":
    unittest.main()
