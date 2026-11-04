"""R-022 independent canonical-DIMACS SHA-256 proof hash parity."""
from __future__ import annotations

import os
import random
import re
import unittest
from hashlib import sha256

from witnora_core.cnf import CNFFormula
from witnora_core.cnf_rust import canonical_hash_in_rust, canonicalize_cnf_in_rust


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustCanonicalHash(unittest.TestCase):
    def test_1600_randomized_canonical_source_hashes(self):
        rng = random.Random(220112026)
        for n in range(1, 9):
            for _ in range(200):
                source = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(6))]
                    for _ in range(rng.randrange(14))
                ]
                reference = CNFFormula.from_raw_clauses(source)
                got = canonical_hash_in_rust(source)
                with self.subTest(n=n, source=source):
                    self.assertEqual(got, reference.formula_hash())
                    self.assertRegex(got, r"^[0-9a-f]{64}$")
                    native = canonicalize_cnf_in_rust(source)
                    self.assertEqual(got, sha256(
                        native.canonical_dimacs.encode("utf-8")
                    ).hexdigest())

    def test_empty_tautology_duplicate_and_empty_clause(self):
        sources = (
            [], [[]], [[1, -1]], [[1, 1], [1]],
            [[-3, 2], [2, -3]], [[1], [-1], []],
        )
        for source in sources:
            with self.subTest(source=source):
                self.assertEqual(
                    canonical_hash_in_rust(source),
                    CNFFormula.from_raw_clauses(source).formula_hash(),
                )

    def test_rejects_unsafe_signed_inputs(self):
        for source in ([[0]], [[True]], [[1 << 40]], [[-(1 << 31)]]):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    canonical_hash_in_rust(source)


if __name__ == "__main__":
    unittest.main()
