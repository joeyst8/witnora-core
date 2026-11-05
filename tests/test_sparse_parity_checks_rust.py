"""R-056 native sparse odd-column parity matrix and independent finite audits."""
from __future__ import annotations

from itertools import combinations, product
import os
import random
import unittest

from witnora_core.sparse_parity_checks import (
    SparseOddSketch,
    column_signatures, column_signatures_rust,
    build_sparse_odd_sketch, build_sparse_odd_sketch_rust,
    validate_sparse_odd_sketch, validate_sparse_odd_sketch_rust,
    low_weight_collisions, low_weight_collisions_rust,
    source_row_scope, source_row_scope_rust,
    audit_sparse_small, audit_sparse_small_rust,
    min_degree_elimination_width, min_degree_elimination_width_rust,
)


def direct_truth_audit(source, sketch):
    """Independent Boolean assignment oracle without violation_mask helper."""
    models = 0
    fp = 0
    for choices in product((False, True), repeat=sketch.nvars):
        violated = []
        for clause in source:
            satisfied = any(
                (choices[abs(lit)-1] if lit > 0 else not choices[abs(lit)-1])
                for lit in clause
            )
            violated.append(not satisfied)
        if not any(violated):
            models += 1
        else:
            if all(sum(violated[j] for j in row) % 2 == 0
                   for row in sketch.rows):
                fp += 1
    return models, (2**sketch.nvars)-models, fp


@unittest.skipUnless(os.environ.get("WITNORA_RUST_VE_BIN"),
                     "Native PyO3 wheel installed in Rust CI")
class TestNativeSparseOddSketch(unittest.TestCase):
    def test_400_random_sources_exact_seeded_matrix_and_finite_audit(self):
        rng = random.Random(56112026)
        count = 0
        for m in range(10):
            for sample in range(40):
                nvars = rng.randrange(1, 8)
                source = [
                    [rng.randrange(1, nvars+1)*rng.choice((-1, 1))
                     for _ in range(rng.randrange(0, 5))]
                    for _ in range(m)
                ]
                max_width = rng.randrange(4, 8)
                seed = rng.randrange(1, 10**6)
                with self.subTest(m=m, sample=sample):
                    original = build_sparse_odd_sketch(
                        source, nvars, max_row_width=max_width,
                        seed=seed, max_attempts=100
                    )
                    native = build_sparse_odd_sketch_rust(
                        source, nvars, max_row_width=max_width,
                        seed=seed, max_attempts=100
                    )
                    self.assertEqual(native, original)
                    self.assertEqual(
                        validate_sparse_odd_sketch_rust(source, native),
                        validate_sparse_odd_sketch(source, original)
                    )
                    self.assertEqual(
                        column_signatures_rust(native.rows, m),
                        column_signatures(native.rows, m)
                    )
                    signatures = column_signatures_rust(native.rows, m)
                    self.assertTrue(all(sig.bit_count() == 3 for sig in signatures))
                    self.assertEqual(len(set(signatures)), len(signatures))
                    for weight in range(4):
                        self.assertEqual(
                            low_weight_collisions_rust(native, max_weight=weight),
                            low_weight_collisions(native, max_weight=weight)
                        )
                    self.assertEqual(low_weight_collisions_rust(native), 0)
                    py_audit = audit_sparse_small(source, original)
                    rust_audit = audit_sparse_small_rust(source, native)
                    self.assertEqual(rust_audit, py_audit)
                    self.assertEqual(
                        (rust_audit.source_models, rust_audit.nonmodels,
                         rust_audit.false_positives),
                        direct_truth_audit(source, native)
                    )
                    for row in native.rows:
                        self.assertEqual(
                            source_row_scope_rust(tuple(map(tuple, source)), row),
                            source_row_scope(tuple(map(tuple, source)), row)
                        )
                count += 1
        self.assertEqual(count, 400)

    def test_300_random_scopes_match_min_degree_with_clique_lower_bound(self):
        rng = random.Random(5606301)
        for n in range(10):
            for sample in range(30):
                scopes = [set(rng.sample(range(1, n+1),
                               rng.randrange(n+1)))
                          for _ in range(rng.randrange(0, 10))]
                with self.subTest(n=n, sample=sample):
                    py = min_degree_elimination_width(scopes, n)
                    rust = min_degree_elimination_width_rust(scopes, n)
                    self.assertEqual(rust, py)
                    self.assertGreaterEqual(rust, max(
                        (len(scope)-1 for scope in scopes), default=0
                    ))
                    self.assertLessEqual(rust, max(0, n-1))

    def test_invalid_source_and_sketch_inputs_fail_closed(self):
        cnf = [[1, -2], [2]]
        sketch = build_sparse_odd_sketch_rust(cnf, 2, max_row_width=5)
        mutated = SparseOddSketch(
            sketch.nvars, sketch.clause_count, "bad-digest",
            sketch.max_row_width, sketch.rows,
        )
        for func in (validate_sparse_odd_sketch,
                     validate_sparse_odd_sketch_rust):
            with self.assertRaises(ValueError):
                func(cnf, mutated)
        broken = SparseOddSketch(
            sketch.nvars, sketch.clause_count, sketch.digest,
            sketch.max_row_width, ((0, 0),) + sketch.rows[1:],
        )
        for func in (validate_sparse_odd_sketch,
                     validate_sparse_odd_sketch_rust):
            with self.assertRaises(ValueError):
                func(cnf, broken)
        for func in (build_sparse_odd_sketch, build_sparse_odd_sketch_rust):
            with self.assertRaises(ValueError):
                func(cnf, 2, max_row_width=0)
            with self.assertRaises(ValueError):
                func(cnf, 2, max_attempts=0)
        for func in (min_degree_elimination_width,
                     min_degree_elimination_width_rust):
            with self.assertRaises(ValueError):
                func([{3}], 2)
            with self.assertRaises(ValueError):
                func([], -1)


if __name__ == "__main__":
    unittest.main()
