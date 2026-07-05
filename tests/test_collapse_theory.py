import tempfile
import unittest
from pathlib import Path

from witnora_core.collapse_theory import (
    NO_COLLAPSE_FOUND,
    OPERATOR_STUB_NOT_EXECUTED,
    UNSAT_DRAT_EXPORTED_VERIFIED,
    collapse_operators,
    grammar_profiles,
    run_theory_experiment,
)


class CollapseTheoryTest(unittest.TestCase):
    def test_collapse_grammar_profile(self):
        profiles = grammar_profiles()
        self.assertIn("G0_BASE", profiles)
        self.assertIn("G1_XOR", profiles)
        self.assertIn("BCE", profiles["G0_BASE"].operators)
        self.assertIn("EXACT_XOR", profiles["G1_XOR"].operators)
        self.assertEqual(profiles["G1_XOR"].xor_max_k, 6)
        print("COLLAPSE_GRAMMAR_PROFILE_PASS")

    def test_collapse_operator_schema(self):
        operators = collapse_operators()
        for name, operator in operators.items():
            data = operator.to_dict()
            for key in [
                "name",
                "enabled",
                "description",
                "certificate_supported",
                "external_proof_supported",
                "deterministic",
                "resource_bounds",
            ]:
                self.assertIn(key, data, name)
        self.assertTrue(operators["HORN_PROTOTYPE"].stub)
        print("COLLAPSE_OPERATOR_SCHEMA_PASS")

    def test_strictness_witness_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_theory_experiment(
                grammars=["G0_BASE", "G1_XOR"],
                families=["xor-chain"],
                out_root=Path(tmp) / "lab",
                prefer_official_tseitin=False,
            )
        witnesses = result["strictness_witnesses"]
        self.assertTrue(witnesses)
        witness = witnesses[0]
        for key in [
            "family",
            "instance",
            "base_grammar",
            "extended_grammar",
            "added_operator",
            "base_result",
            "extended_result",
            "certification_level",
            "evidence",
        ]:
            self.assertIn(key, witness)
        print("STRICTNESS_WITNESS_SCHEMA_PASS")

    def test_g0_g1_tseitin_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_theory_experiment(
                grammars=["G0_BASE", "G1_XOR"],
                families=["tseitin"],
                out_root=Path(tmp) / "lab",
                prefer_official_tseitin=False,
            )
        rows = result["results"]
        g0 = next(row for row in rows if row["grammar"] == "G0_BASE")
        g1 = next(row for row in rows if row["grammar"] == "G1_XOR")
        self.assertEqual(g0["public_category"], NO_COLLAPSE_FOUND)
        self.assertNotEqual(g1["public_category"], NO_COLLAPSE_FOUND)
        self.assertTrue(result["strictness_witnesses"])
        print("G0_G1_TSEITIN_DELTA_PASS")

    def test_g0_g1_blocked_clique_delta(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_theory_experiment(
                grammars=["G0_BASE", "G1_XOR"],
                families=["blocked-clique"],
                out_root=Path(tmp) / "lab",
                prefer_official_tseitin=False,
            )
        witnesses = result["strictness_witnesses"]
        bce = [item for item in witnesses if item["added_operator"] == "BCE"]
        self.assertTrue(bce)
        self.assertEqual(bce[0]["extended_result"], "SAT_ASSIGNMENT_VERIFIED")
        print("G0_G1_BLOCKED_CLIQUE_DELTA_PASS")

    def test_operator_delta_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_theory_experiment(
                grammars=["G0_BASE", "G1_XOR"],
                families=["tseitin", "xor-chain"],
                out_root=Path(tmp) / "lab",
                prefer_official_tseitin=False,
            )
        delta = result["operator_delta_summary"][0]
        self.assertEqual(delta["operator_added"], "XOR_AFFINE")
        self.assertGreaterEqual(delta["instances_changed"], 2)
        self.assertGreaterEqual(delta["no_collapse_delta"], 2)
        print("OPERATOR_DELTA_SUMMARY_PASS")

    def test_operator_stub_honesty(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_theory_experiment(
                grammars=["G2_HORN_PROTOTYPE", "G3_CARDINALITY_PROTOTYPE"],
                families=["horn", "cardinality"],
                out_root=Path(tmp) / "lab",
                prefer_official_tseitin=False,
            )
        categories = {row["public_category"] for row in result["results"]}
        self.assertEqual(categories, {OPERATOR_STUB_NOT_EXECUTED})
        print("OPERATOR_STUB_HONESTY_PASS")

    def test_adversarial_near_xor_no_false_claim(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_theory_experiment(
                grammars=["G1_XOR"],
                families=["adversarial-mixed"],
                out_root=Path(tmp) / "lab",
                prefer_official_tseitin=False,
            )
        near = next(row for row in result["results"] if row["instance_id"] == "near_xor_incomplete_k4")
        self.assertEqual(near["detected_structures"]["detected_xor_equations"], 0)
        self.assertNotEqual(near["public_category"], UNSAT_DRAT_EXPORTED_VERIFIED)
        print("ADVERSARIAL_NEAR_XOR_NO_FALSE_CLAIM_PASS")

    def test_no_pnp_overclaim(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "lab"
            run_theory_experiment(
                grammars=["G0_BASE", "G1_XOR"],
                families=["tseitin", "xor-chain"],
                out_root=root,
                prefer_official_tseitin=False,
            )
            text = "\n".join(
                path.read_text(encoding="utf-8")
                for path in [root / "COLLAPSE_THEORY_REPORT.md", root / "STRICTNESS_WITNESSES.md"]
            )
        forbidden = [
            "proves P vs NP",
            "solves SAT",
            "hard for all algorithms",
            "complete collapse grammar",
            "CryptoMiniSat-style claim",
        ]
        for phrase in forbidden:
            self.assertNotIn(phrase, text)
        self.assertIn("does not claim P vs NP progress", text)
        print("NO_PNP_OVERCLAIM_PASS")


if __name__ == "__main__":
    unittest.main()
