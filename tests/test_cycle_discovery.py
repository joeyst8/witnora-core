"""Independent bounded validation of odd XOR cycle discovery."""
from itertools import product
import random
import subprocess
from pathlib import Path
from unittest.mock import patch
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.cycle_discovery import discover_odd_xor_cycle
from witnora_core.lean_cycle_gate import verify_odd_cycle_with_lean
from witnora_core.spoke_discovery import discover_parity_spoke_conflicts
from witnora_core.xor import canonical_xor_cnf_clauses


def formula_from_edges(edges):
    clauses = set()
    for u, v, rhs in edges:
        clauses.update(canonical_xor_cnf_clauses((u, v), rhs))
    return CNFFormula.from_raw_clauses(clauses)


def reference_inconsistent(edges, n):
    return not any(
        all((bits[u - 1] ^ bits[v - 1]) == rhs for u, v, rhs in edges)
        for bits in product((0, 1), repeat=n)
    )


class CycleDiscoveryTest(unittest.TestCase):
    def test_triangle_not_spoke(self):
        f = formula_from_edges([(1, 2, 0), (2, 3, 0), (1, 3, 1)])
        self.assertEqual(discover_parity_spoke_conflicts(f), [])
        cycle = discover_odd_xor_cycle(f)
        self.assertIsNotNone(cycle)
        self.assertEqual(cycle["status"], "UNVERIFIED_STRUCTURAL_CANDIDATE")
        self.assertEqual(cycle["cycle_length"], 3)
        self.assertEqual(cycle["start"], cycle["steps"][-1]["next"])
        self.assertEqual(sum(s["rhs"] for s in cycle["steps"]) % 2, 1)

    def test_even_triangle_is_not_conflict(self):
        f = formula_from_edges([(1, 2, 0), (2, 3, 1), (1, 3, 1)])
        self.assertIsNone(discover_odd_xor_cycle(f))

    def test_randomized_against_independent_exhaustive_reference(self):
        rng = random.Random(190317)
        for _ in range(100):
            n = rng.randrange(3, 7)
            edges = [
                (u, v, rng.randrange(2))
                for u in range(1, n + 1)
                for v in range(u + 1, n + 1)
                if rng.random() < 0.42
            ]
            f = formula_from_edges(edges)
            found = discover_odd_xor_cycle(f)
            self.assertEqual(found is not None, reference_inconsistent(edges, n))
            if found:
                self.assertEqual(found["steps"][-1]["next"], found["start"])
                self.assertEqual(sum(s["rhs"] for s in found["steps"]) % 2, 1)

    def test_gate_proof_has_source_and_closed_walk(self):
        f = formula_from_edges([(1, 2, 0), (2, 3, 0), (1, 3, 1)])
        raw = f.to_clause_lists()
        def inspect(argv, **kwargs):
            proof = Path(argv[3]).read_text()
            self.assertIn("CycleParity.closedWalk_unsat", proof)
            self.assertIn("DIMACSDocument.parseDocument", proof)
            self.assertNotIn("sorry", proof)
            return subprocess.CompletedProcess(argv, 0, "", "")
        with patch("witnora_core.lean_cycle_gate.subprocess.run", side_effect=inspect):
            result = verify_odd_cycle_with_lean(
                f, raw_clauses=raw,
                source_tokens=[v for c in raw for v in (*c, 0)],
                source_text=f.canonical_dimacs(),
            )
        self.assertTrue(result["verified"])

    def test_gate_fails_closed_on_lean_rejection(self):
        f = formula_from_edges([(1, 2, 0), (2, 3, 0), (1, 3, 1)])
        raw = f.to_clause_lists()
        with patch("witnora_core.lean_cycle_gate.subprocess.run",
                   return_value=subprocess.CompletedProcess([], 1, "", "rejected")):
            result = verify_odd_cycle_with_lean(
                f, raw_clauses=raw,
                source_tokens=[v for c in raw for v in (*c, 0)],
                source_text=f.canonical_dimacs(),
            )
        self.assertFalse(result["verified"])


if __name__ == "__main__":
    unittest.main()
