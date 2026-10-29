"""Source-bound discovered spoke proof gate tests."""
from pathlib import Path
import subprocess
import unittest
from unittest.mock import patch

from witnora_core.lean_spoke_gate import verify_discovered_spoke_with_lean
from witnora_core.spoke_collapse import make_spoke_family
from witnora_core.cnf import CNFFormula


class SourceSpokeGateTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.formula, _ = make_spoke_family(3, contradictory=True)
        cls.raw = cls.formula.to_clause_lists()
        cls.source = cls.formula.canonical_dimacs()
        cls.tokens = [v for clause in cls.raw for v in (*clause, 0)]

    def check(self, *, source=None, tokens=None, raw=None):
        return verify_discovered_spoke_with_lean(
            self.formula,
            raw_clauses=self.raw if raw is None else raw,
            source_tokens=self.tokens if tokens is None else tokens,
            source_text=self.source if source is None else source,
        )

    def test_proof_uses_actual_source_and_extraction_checker(self):
        def inspect(argv, **kwargs):
            proof = Path(argv[3]).read_text(encoding="utf-8")
            self.assertIn("checked_ascii_dimacs_spoke_unsat", proof)
            self.assertIn("signedCNFHolds", proof)
            self.assertNotIn("sorry", proof)
            self.assertNotIn("axiom", proof)
            return subprocess.CompletedProcess(argv, 0, "", "")
        with patch("witnora_core.lean_spoke_gate.subprocess.run", side_effect=inspect):
            result = self.check()
        self.assertTrue(result["verified"])
        self.assertEqual(result["lean_formal_status"], "LEAN_SOURCE_SPOKE_UNSAT_VERIFIED")

    def test_lean_rejection_fails_closed(self):
        with patch("witnora_core.lean_spoke_gate.subprocess.run",
                   return_value=subprocess.CompletedProcess([], 1, "", "rejected")):
            result = self.check()
        self.assertFalse(result["verified"])
        self.assertEqual(result["lean_formal_status"], "NOT_LEAN_VERIFIED")

    def test_no_conflict_does_not_invoke_lean(self):
        formula, _ = make_spoke_family(3, contradictory=False)
        with patch("witnora_core.lean_spoke_gate.subprocess.run") as runner:
            result = verify_discovered_spoke_with_lean(
                formula, raw_clauses=formula.to_clause_lists(),
                source_tokens=[], source_text=formula.canonical_dimacs(),
            )
        self.assertFalse(result["verified"])
        runner.assert_not_called()

    def test_non_ascii_source_rejected_before_lean(self):
        with patch("witnora_core.lean_spoke_gate.subprocess.run") as runner:
            result = self.check(source=self.source + "☃")
        self.assertFalse(result["verified"])
        runner.assert_not_called()


if __name__ == "__main__":
    unittest.main()
