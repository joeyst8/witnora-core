"""R-085 orbit-Walsh special case versus Python and the defect kernel."""
from itertools import combinations
import random
import unittest

from tests.test_crc_orbit_oracle import near_complete_source
from witnora_core.crc_boundary import _normalized_clauses
from witnora_core.crc_orbit_oracle import query_orbit_walsh


class OrbitRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_140_seeded_coherent_rank_two_and_three(self):
        rng = random.Random(85085)
        for trial in range(140):
            n = rng.randrange(4, 9)
            rank = rng.choice((2, 3))
            supports = list(combinations(range(1, n + 1), rank))
            missing = set(rng.sample(supports, rng.randrange(0, min(5, len(supports)))))
            polarity = {v: bool(rng.randrange(2)) for v in range(1, n + 1)}
            source = near_complete_source(n, rank, polarity, missing)
            boundary = tuple(range(1, n + rng.randrange(2) + 1))
            modes = tuple(rng.randrange(1 << len(boundary)) for _ in range(18))
            normalized = _normalized_clauses(source, boundary)
            with self.subTest(trial=trial):
                self.assertEqual(query_orbit_walsh(normalized, boundary, modes,
                    backend="rust"), query_orbit_walsh(normalized, boundary, modes))

    def test_resource_bound_and_no_source(self):
        boundary = tuple(range(1, 6))
        self.assertIsNone(query_orbit_walsh(None, boundary, (0,), backend="rust"))
        support = {(1, 2), (1, 3), (2, 3)}
        source = near_complete_source(5, 2, {v: True for v in boundary}, support)
        normalized = _normalized_clauses(source, boundary)
        for limit in (0, 1, 2, 3):
            self.assertEqual(query_orbit_walsh(normalized, boundary, (0, 1),
                max_missing=limit, backend="rust"), query_orbit_walsh(
                    normalized, boundary, (0, 1), max_missing=limit))


if __name__ == "__main__":
    unittest.main()
