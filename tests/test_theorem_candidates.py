import tempfile
import unittest
from pathlib import Path

from witnora_core.collapse_theory import obstruction_records, run_theory_experiment, theorem_candidates_outputs
from witnora_core.theorem_candidates import initial_theorem_candidates


class TheoremCandidateTest(unittest.TestCase):
    def test_theorem_candidate_registry(self):
        candidates = initial_theorem_candidates()
        self.assertGreaterEqual(len(candidates), 4)
        statuses = {candidate.status for candidate in candidates}
        self.assertIn("EMPIRICAL_EVIDENCE", statuses)
        self.assertIn("CONJECTURE", statuses)
        for candidate in candidates:
            self.assertTrue(candidate.required_proof_obligations)
            self.assertTrue(candidate.forbidden_interpretations)
        with tempfile.TemporaryDirectory() as tmp:
            payload = theorem_candidates_outputs(Path(tmp) / "theorems")
            self.assertTrue((Path(tmp) / "theorems" / "THEOREM_CANDIDATES.md").exists())
        self.assertIn("theorem_candidates", payload)
        print("THEOREM_CANDIDATE_REGISTRY_PASS")

    def test_obstruction_record_schema(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_theory_experiment(
                grammars=["G1_XOR"],
                families=["pigeonhole"],
                out_root=Path(tmp) / "lab",
                prefer_official_tseitin=False,
            )
        rows = result["results"]
        # Re-run through the public helper from object rows is intentionally not supported;
        # the v2.1 frontier writer exercises the dataclass path. Here we validate emitted
        # obstruction schema from that path.
        from witnora_core.collapse_theory import grammar_profiles, build_family_instances, run_instance

        grammar = grammar_profiles()["G1_XOR"]
        instances = build_family_instances(["pigeonhole"], prefer_official_tseitin=False)
        records = obstruction_records([run_instance(instance, grammar) for instance in instances])
        self.assertTrue(records)
        data = records[0].to_dict()
        for key in [
            "instance_id",
            "family",
            "grammar",
            "obstruction_type",
            "evidence",
            "suggested_operator",
            "confidence",
            "certifiable_next_step",
        ]:
            self.assertIn(key, data)
        self.assertTrue(rows)
        print("OBSTRUCTION_RECORD_SCHEMA_PASS")

    def test_pnp_conjecture_labeling(self):
        text = "\n".join(candidate.status + " " + " ".join(candidate.forbidden_interpretations) for candidate in initial_theorem_candidates())
        self.assertIn("CONJECTURE", text)
        self.assertIn("Does not prove P vs NP progress", text)
        print("PNP_CONJECTURE_LABELING_PASS")


if __name__ == "__main__":
    unittest.main()
