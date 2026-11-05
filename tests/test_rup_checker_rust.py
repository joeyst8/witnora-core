"""R-014 independent RUP-only DRAT replay versus original Python checker.

This is a differential empirical control, not a Lean proof.
"""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.cnf import CNFFormula
from witnora_core.drat_check import check_drat_text


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustRupReplay(unittest.TestCase):
    def test_1200_seeded_full_replay_decisions_and_warnings(self):
        rng = random.Random(14142026)
        for n in range(1, 9):
            for _ in range(150):
                source = [
                    [rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                     for _ in range(rng.randrange(4))]
                    for _ in range(rng.randrange(11))
                ]
                original = CNFFormula.from_raw_clauses(source)
                proof = []
                for _ in range(rng.randrange(12)):
                    clause = [
                        rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                        for _ in range(rng.randrange(4))
                    ]
                    marker = "d " if rng.randrange(3) == 0 else ""
                    proof.append(marker + " ".join(map(str, clause + [0])))
                if rng.randrange(2):
                    proof.append("0")
                text = "\n".join(proof) + "\n"
                strict = bool(rng.randrange(2))
                with self.subTest(n=n, source=source, proof=text, strict=strict):
                    py = check_drat_text(
                        original, text, strict_deletions=strict)
                    rust = check_drat_text(
                        original, text, strict_deletions=strict, backend="rust")
                    for key in ("verified", "empty_clause_derived", "failed_line",
                                "warnings"):
                        self.assertEqual(rust[key], py[key], key)
                    self.assertEqual(bool(rust["error"]), bool(py["error"]))
                    if py["error"] in (
                        "addition is not RUP-checkable",
                        "deletion clause not present in active database",
                        "empty clause was not derived",
                    ):
                        self.assertEqual(rust["error"], py["error"])

    def test_true_rup_proofs_and_strict_deletion(self):
        original = CNFFormula([[1], [-1]])
        for backend in ("python", "rust"):
            with self.subTest(backend=backend):
                self.assertTrue(check_drat_text(
                    original, "0\n", backend=backend)["verified"])
                self.assertTrue(check_drat_text(
                    original, "d 2 0\n0\n", backend=backend)["verified"])
                self.assertEqual(check_drat_text(
                    original, "d 2 0\n0\n",
                    strict_deletions=True, backend=backend)["failed_line"], 1)
                self.assertFalse(check_drat_text(
                    CNFFormula([[1]]), "0\n", backend=backend)["verified"])

    def test_unknown_checker_backend(self):
        with self.assertRaises(ValueError):
            check_drat_text(CNFFormula(), "0\n", backend="fake")


if __name__ == "__main__":
    unittest.main()
