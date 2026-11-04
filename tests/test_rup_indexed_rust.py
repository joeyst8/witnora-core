"""R-013 indexed RUP unit-conflict native witness differential tests.

The producer is untrusted; the Lean GeneralRUP verifier remains unchanged.
"""
from __future__ import annotations

import os
import random
import unittest

from witnora_core.rup_indexed_propagation import indexed_unit_conflict_witness


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in dedicated Rust CI")
class TestRustIndexedRup(unittest.TestCase):
    def test_2000_seeded_exact_witness_and_refusal_differentials(self):
        rng = random.Random(13132026)
        for n in range(1, 9):
            for _ in range(250):
                database = [
                    tuple(rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                          for _ in range(rng.randrange(5)))
                    for _ in range(rng.randrange(14))
                ]
                target = tuple(
                    rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                    for _ in range(rng.randrange(4)))
                cap = rng.randrange(9)
                py = indexed_unit_conflict_witness(
                    database, target, max_units=cap)
                rust = indexed_unit_conflict_witness(
                    database, target, max_units=cap, backend="rust")
                with self.subTest(n=n, db=database, target=target, cap=cap):
                    self.assertEqual(rust, py)

    def test_immediate_contradiction_and_nonzero_witness(self):
        self.assertEqual(indexed_unit_conflict_witness(
            [()], (), backend="rust"), ())
        self.assertEqual(indexed_unit_conflict_witness(
            [(1,), (-1,)], (), backend="rust"), (1,))
        self.assertEqual(indexed_unit_conflict_witness(
            [(1, 1), (-1, -1)], (), backend="rust"), (1,))
        self.assertIsNone(indexed_unit_conflict_witness(
            [(1,), (-1,)], (), backend="rust", max_units=0))

    def test_invalid_caps_and_backend(self):
        with self.assertRaises(ValueError):
            indexed_unit_conflict_witness([], (), max_units=-1, backend="rust")
        with self.assertRaises(ValueError):
            indexed_unit_conflict_witness([], (), backend="not_a_backend")


if __name__ == "__main__":
    unittest.main()
