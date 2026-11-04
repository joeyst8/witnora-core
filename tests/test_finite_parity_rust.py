"""R-058 exact finite source clause-violation parity native equivalence and oracle."""
from __future__ import annotations

from dataclasses import replace
from itertools import combinations, product
import os
import random
import unittest

from witnora_core.eth_clause_violation_parity import (
    source_digest, source_digest_rust,
    violation_mask, violation_mask_rust,
    parity_accepts, parity_accepts_rust,
    build_finite_sketch, build_finite_sketch_rust,
    verify_finite_sketch, verify_finite_sketch_rust,
    is_complete_primal, is_complete_primal_rust,
)


def brute_violations(source, nvars, assignment):
    values = tuple(bool((assignment >> j) & 1) for j in range(nvars))
    result = 0
    for j, clause in enumerate(source):
        if not any(values[abs(lit)-1] == (lit > 0) for lit in clause):
            result |= 1 << j
    return result


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust CI")
class TestNativeFiniteParity(unittest.TestCase):
    def test_400_seeded_sources_greedy_rows_and_direct_truth_oracle(self):
        rng = random.Random(58112026)
        for case in range(400):
            nvars = rng.randrange(1, 8)
            source = tuple(
                tuple(rng.randrange(1, nvars+1) * rng.choice((-1, 1))
                      for _ in range(rng.randrange(0, 5)))
                for _ in range(rng.randrange(0, 9))
            )
            seed = rng.randrange(1000000)
            candidate_count = rng.randrange(1, 25)
            with self.subTest(case=case):
                self.assertEqual(source_digest_rust(source), source_digest(source))
                py = build_finite_sketch(
                    source, nvars, seed=seed,
                    candidates_per_width=candidate_count
                )
                native = build_finite_sketch_rust(
                    source, nvars, seed=seed,
                    candidates_per_width=candidate_count
                )
                self.assertEqual(native, py)
                self.assertTrue(verify_finite_sketch(source, py))
                self.assertTrue(verify_finite_sketch_rust(source, native))
                self.assertEqual(
                    is_complete_primal_rust(source, nvars),
                    is_complete_primal(source, nvars)
                )
                exact_models = sum(
                    brute_violations(source, nvars, assignment) == 0
                    for assignment in range(1 << nvars)
                )
                self.assertEqual(native.satisfying_count, exact_models)
                self.assertEqual(native.survivors[-1], 0)
                for assignment in range(1 << nvars):
                    violations = brute_violations(source, nvars, assignment)
                    self.assertEqual(violation_mask(source, assignment),
                                     violations)
                    self.assertEqual(violation_mask_rust(source, assignment),
                                     violations)
                    self.assertEqual(
                        parity_accepts_rust(violations, native.rows),
                        parity_accepts(violations, native.rows)
                    )
                    self.assertEqual(
                        parity_accepts_rust(violations, native.rows),
                        violations == 0
                    )
                for mask in range(1 << len(source)):
                    self.assertEqual(parity_accepts_rust(mask, native.rows),
                                     parity_accepts(mask, native.rows))

    def test_large_unbounded_violation_mask_and_digest(self):
        source = tuple((i+1,) for i in range(140))
        self.assertEqual(source_digest_rust(source), source_digest(source))
        for assignment in (0, 1, (1 << 129) | (1 << 139)):
            self.assertEqual(violation_mask_rust(source, assignment),
                             violation_mask(source, assignment))
        rows = ((0, 129, 139), (1, 77))
        for mask in (0, (1 << 139), (1 << 77) + (1 << 1)):
            self.assertEqual(parity_accepts_rust(mask, rows),
                             parity_accepts(mask, rows))

    def test_tampering_and_negative_input_controls(self):
        source = ((1,), (-1,))
        py = build_finite_sketch(source, 1)
        native = build_finite_sketch_rust(source, 1)
        self.assertEqual(native, py)
        for bad in (
            replace(native, digest="tampered"),
            replace(native, rows=((0, 0),)),
            replace(native, rows=()),
            replace(native, clause_count=3),
            replace(native, nvars=2),
        ):
            with self.subTest(bad=bad):
                self.assertFalse(verify_finite_sketch(source, bad))
                self.assertFalse(verify_finite_sketch_rust(source, bad))
        for func in (build_finite_sketch, build_finite_sketch_rust):
            with self.assertRaises(ValueError):
                func(source, 1, max_rows=0)
            with self.assertRaises(ValueError):
                func(source, 1, candidates_per_width=0)
            with self.assertRaises(ValueError):
                func(source, 15)
        self.assertFalse(verify_finite_sketch_rust(((2,),), native))


if __name__ == "__main__":
    unittest.main()
