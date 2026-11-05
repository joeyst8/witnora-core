"""Adversarial DIMACS/CNF parsing and canonicalization refinement tests."""

import random
import unittest

from witnora_core.cnf import CNFError, CNFFormula, Clause, formula_satisfied
from witnora_core.dimacs import (DIMACSError, export_dimacs, parse_dimacs,
                                parse_dimacs_with_raw, parse_dimacs_with_evidence,
                                parse_dimacs_with_text_evidence, load_dimacs_with_raw)


def raw_cnf_holds(raw, assignment):
    return all(
        any(assignment[abs(lit)] if lit > 0 else not assignment[abs(lit)]
            for lit in clause)
        for clause in raw
    )


class DIMACSRefinementTest(unittest.TestCase):
    def test_boolean_literals_are_not_signed_integers(self):
        for literal in (True, False):
            with self.subTest(literal=literal):
                with self.assertRaises(CNFError):
                    Clause([literal])

    def test_tautological_clause_still_validates_every_literal(self):
        for malformed in (0, True, False, "invalid", None, 1.0):
            with self.subTest(malformed=malformed):
                with self.assertRaises(CNFError):
                    Clause.from_literals([1, -1, malformed])
                with self.assertRaises(CNFError):
                    CNFFormula.from_raw_clauses([[1, -1, malformed]])
        self.assertIsNone(Clause.from_literals([1, -1, 2]))

    def test_randomized_canonicalization_preserves_semantics_and_roundtrip(self):
        rng = random.Random(6397)
        for _ in range(160):
            variables = rng.randint(1, 6)
            raw = [
                [rng.choice((-1, 1)) * rng.randint(1, variables)
                 for _ in range(rng.randint(0, 6))]
                for _ in range(rng.randint(0, 9))
            ]
            formula = CNFFormula.from_raw_clauses(raw)
            serialized = export_dimacs(formula)
            parsed = parse_dimacs(serialized)
            self.assertEqual(parsed.to_clause_lists(), formula.to_clause_lists())
            self.assertEqual(parsed.formula_hash, formula.formula_hash)
            for bits in range(1 << variables):
                assignment = {v: bool(bits & (1 << (v - 1)))
                              for v in range(1, variables + 1)}
                self.assertEqual(raw_cnf_holds(raw, assignment),
                                 formula_satisfied(parsed, assignment))

    def test_malformed_dimacs_never_silently_recovers(self):
        invalid = [
            "",
            "p cnf 1 1\n1",
            "p cnf 1 1\n2 0\n",
            "p cnf 1 2\n1 0\n",
            "p cnf -1 0\n",
            "p cnf 1 0\np cnf 1 0\n",
            "1 0\n",
            "p cnf 1 1\ntrue 0\n",
            "p cnf 1 1\n1 -1\n",
        ]
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(DIMACSError):
                parse_dimacs(text)

    def test_source_clauses_preserved_before_normalization(self):
        text = "c keep the actual source\np cnf 4 4\n2 1 2 0\n1 -1 4 0\n-4 0\n0\n"
        formula, raw = parse_dimacs_with_raw(text)
        self.assertEqual(raw, [[2, 1, 2], [1, -1, 4], [-4], []])
        self.assertEqual(formula, parse_dimacs(text))
        self.assertEqual(formula, CNFFormula.from_raw_clauses(raw))
        self.assertNotEqual(raw, formula.to_clause_lists())
        with_evidence, raw_again, tokens = parse_dimacs_with_evidence(text)
        self.assertEqual(with_evidence, formula)
        self.assertEqual(raw_again, raw)
        self.assertEqual(tokens, [2, 1, 2, 0, 1, -1, 4, 0, -4, 0, 0])
        _, _, _, spellings = parse_dimacs_with_text_evidence(text)
        self.assertEqual(spellings, ["2", "1", "2", "0", "1", "-1", "4", "0", "-4", "0", "0"])

    def test_empty_clause_is_preserved_as_contradiction(self):
        formula = parse_dimacs("p cnf 1 1\n0\n")
        self.assertTrue(formula.contains_empty_clause)
        self.assertFalse(formula_satisfied(formula, {1: True}))


if __name__ == "__main__":
    unittest.main()
