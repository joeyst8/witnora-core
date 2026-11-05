"""R-078 dense geometry Rust versus Python on frozen random sources."""
import random
import unittest
from dataclasses import replace

from witnora_core.constraint_geometry import (
    build_dense_random_sketch, validate_dense_sketch, audit_small_collisions,
    singleton_coverage_lower_bound, row_statistics,
)


class DenseGeometryRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_120_seeded_sketches_and_audits(self):
        rng = random.Random(78078)
        for trial in range(120):
            n = rng.randrange(1, 8)
            source = []
            for _ in range(rng.randrange(0, 20)):
                source.append([rng.choice((-1, 1)) * rng.randrange(1, n + 1)
                               for _ in range(rng.randrange(0, 5))])
            seed = 20000 + trial
            security = rng.randrange(0, 8)
            with self.subTest(trial=trial):
                p = build_dense_random_sketch(source, n, security_bits=security, seed=seed)
                r = build_dense_random_sketch(source, n, security_bits=security,
                                              seed=seed, backend="rust")
                self.assertEqual(r, p)
                self.assertEqual(validate_dense_sketch(source, r, backend="rust"),
                                 validate_dense_sketch(source, p))
                self.assertEqual(audit_small_collisions(source, r, backend="rust"),
                                 audit_small_collisions(source, p))
                self.assertEqual(row_statistics(r, backend="rust"), row_statistics(p))
                cp = audit_small_collisions(source, p)
                for width in (1, 2, 4, 13):
                    ids = cp.singleton_violation_clause_ids
                    self.assertEqual(singleton_coverage_lower_bound(ids, width, backend="rust"),
                                     singleton_coverage_lower_bound(ids, width))

    def test_validation_and_large_clause_width(self):
        source = [[1 if j % 2 else -1] for j in range(201)]
        sketch = build_dense_random_sketch(source, 1, security_bits=4,
                                           seed=78, backend="rust")
        self.assertEqual(sketch, build_dense_random_sketch(source, 1,
                         security_bits=4, seed=78))
        self.assertEqual(audit_small_collisions(source, sketch, backend="rust"),
                         audit_small_collisions(source, sketch))
        for invalid in (replace(sketch, digest="broken"),
                        replace(sketch, rows=((1, 1),) + sketch.rows[1:]),
                        replace(sketch, rows=sketch.rows[:-1])):
            with self.assertRaises(ValueError):
                validate_dense_sketch(source, invalid, backend="rust")
        with self.assertRaises(ValueError):
            audit_small_collisions(source, sketch, max_variables=0, backend="rust")


if __name__ == "__main__":
    unittest.main()
