"""Audit the new Lean executable graph fixture against archived source clauses.

The file's Boolean graph check and universal soundness theorem run in Lean;
these tests ensure its 160 literal triples are source-exact and ordered.
"""

import json
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LEAN = (ROOT / "theory" / "TC063DuboisCheckedGraph.lean").read_text()
ARCHIVE = json.loads((ROOT / "research" / "PR119_DUBOIS20_SOURCE_XOR_CERTIFICATE.json").read_text())


class CheckedGraphFixtureTests(unittest.TestCase):
    def test_lean_clause_encoding_matches_all_160_source_clauses_in_order(self):
        start = LEAN.index("def dubois20Clauses : CNF (Fin 60) := [")
        end = LEAN.index("-- Component A zero-based:", start)
        fragment = LEAN[start:end]
        pattern = re.compile(
            r"\[\(\((\d+) : Fin 60\), (true|false)\), "
            r"\((\d+), (true|false)\), \((\d+), (true|false)\)\]"
        )
        found = [
            tuple((int(match.group(i * 2 + 1)), match.group(i * 2 + 2) == "true")
                  for i in range(3))
            for match in pattern.finditer(fragment)
        ]
        source = [
            tuple((abs(lit) - 1, lit > 0) for lit in clause)
            for eq in ARCHIVE["proof_equations"]
            for clause in eq["source_clauses"]
        ]
        self.assertEqual(len(found), 160)
        self.assertEqual(found, source)
        self.assertTrue(all(0 <= var < 60 for clause in found for var, _ in clause))

    def test_owner_mapping_and_separator_exactly_cover_all_60_vars(self):
        self.assertIn("v.val = 9 ∨ v.val = 28", LEAN)
        self.assertIn("v.val < 9 ∨ (29 ≤ v.val ∧ v.val ≤ 48)", LEAN)
        self.assertIn("duboisGraphInvariant", LEAN)
        self.assertIn("duboisNoEmptyResidual", LEAN)
        components = {"A": set(range(0, 9)) | set(range(29, 49)),
                      "B": set(range(10, 28)) | set(range(49, 60)),
                      "S": {9, 28}}
        self.assertEqual({k: len(v) for k, v in components.items()},
                         {"A": 29, "B": 29, "S": 2})
        self.assertEqual(set.union(*components.values()), set(range(60)))
        for x, sx in [("A", "B"), ("A", "S"), ("B", "S")]:
            self.assertFalse(components[x] & components[sx])


if __name__ == "__main__":
    unittest.main()
