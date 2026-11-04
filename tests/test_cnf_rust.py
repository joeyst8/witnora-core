"""R-011 Rust canonical CNF and strict subsumption differentials."""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.cnf_rust import canonicalize_cnf_in_rust
from witnora_core.subsumption import find_first_subsumption


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustCanonicalCnf(unittest.TestCase):
    def test_1600_seeded_full_normalization_dimacs_and_subsumption(self):
        rng = random.Random(110112026)
        for n in range(1, 9):
            for _ in range(200):
                source = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(5))]
                    for _ in range(rng.randrange(13))
                ]
                reference = CNFFormula.from_raw_clauses(source)
                native = canonicalize_cnf_in_rust(source)
                with self.subTest(n=n, source=source):
                    self.assertEqual(native.clauses,
                                     tuple(c.literals for c in reference.clauses))
                    self.assertEqual(native.canonical_dimacs,
                                     reference.canonical_dimacs())
                    self.assertEqual(native.variables, reference.variables)
                    self.assertEqual(native.is_2cnf, reference.is_2cnf)
                    self.assertEqual(
                        find_first_subsumption(reference, backend="rust"),
                        find_first_subsumption(reference, backend="python"))

    def test_empty_tautologies_literals_and_invalid_input(self):
        self.assertEqual(
            canonicalize_cnf_in_rust([]).canonical_dimacs,
            "p cnf 0 0\n")
        self.assertEqual(
            canonicalize_cnf_in_rust([[1, -1], [2, -2]]).clauses,
            ())
        self.assertEqual(
            canonicalize_cnf_in_rust([[3, -2, 1, 1], [3, 1, -2]]).clauses,
            ((-2, 1, 3),))
        for raw in ([[0]], [[True]], [[1 << 35]], [[-(1 << 31)]]):
            with self.assertRaises(ValueError):
                canonicalize_cnf_in_rust(raw)

    def test_mixed_subsumption_and_unknown_backend(self):
        source = CNFFormula([[1], [1, 2], [1, 2, 3], [-1, -2]])
        rust = find_first_subsumption(source, backend="rust")
        self.assertEqual(rust, find_first_subsumption(source))
        with self.assertRaisesRegex(ValueError, "unknown"):
            find_first_subsumption(source, backend="unknown")


if __name__ == "__main__":
    unittest.main()
