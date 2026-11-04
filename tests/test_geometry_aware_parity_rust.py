"""R-079 deterministic incidence-bucket geometry Rust differential tests."""
import random
import unittest

from witnora_core.geometry_aware_parity import (
    geometry_aware_sparse_sketch, source_primal_pairs,
)


class GeometryAwareRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_180_seeded_exact_width_three_sources(self):
        rng = random.Random(79079)
        for trial in range(180):
            n = rng.randrange(3, 11)
            source = []
            for _ in range(rng.randrange(0, 42)):
                vs = rng.sample(range(1, n + 1), 3)
                source.append([v if rng.randrange(2) else -v for v in vs])
            width = rng.randrange(1, 7)
            with self.subTest(trial=trial):
                self.assertEqual(source_primal_pairs(tuple(map(tuple, source)), backend="rust"),
                                 source_primal_pairs(tuple(map(tuple, source))))
                self.assertEqual(geometry_aware_sparse_sketch(source, n,
                        max_row_width=width, backend="rust"),
                    geometry_aware_sparse_sketch(source, n, max_row_width=width))

    def test_duplicate_signature_repair_and_invalid(self):
        source = [[1, 2, 3], [-1, 2, -3], [1, -2, -3]] * 5
        for width in (1, 2, 3, 5, 20):
            self.assertEqual(geometry_aware_sparse_sketch(source, 3,
                max_row_width=width, backend="rust"),
                geometry_aware_sparse_sketch(source, 3, max_row_width=width))
        with self.assertRaises(ValueError):
            geometry_aware_sparse_sketch([[1, 1, 2]], 3, backend="rust")


if __name__ == "__main__":
    unittest.main()
