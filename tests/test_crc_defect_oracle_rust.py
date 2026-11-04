"""R-082 fixed-parameter defect Walsh source Python/Rust differential."""
import random
import unittest
from itertools import combinations

from tests.test_crc_orbit_oracle import near_complete_source
from witnora_core.crc_boundary import _normalized_clauses
from witnora_core.crc_defect_oracle import query_defect_walsh


class CRCDefectRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_120_seeded_rank_two_and_three_sources(self):
        rng = random.Random(82082)
        for trial in range(120):
            n = rng.randrange(4, 9)
            rank = rng.choice((2, 3))
            support = list(combinations(range(1, n + 1), rank))
            defects = rng.randrange(0, min(7, len(support)))
            missing = set(rng.sample(support, defects))
            polarity = {v: bool(rng.randrange(2)) for v in range(1, n + 1)}
            source = near_complete_source(n, rank, polarity, missing)
            boundary = tuple(range(1, n + rng.randrange(2) + 1))
            modes = tuple(rng.randrange(1 << len(boundary)) for _ in range(16))
            normalized = _normalized_clauses(source, boundary)
            with self.subTest(trial=trial):
                self.assertEqual(query_defect_walsh(normalized, boundary,
                    modes, backend="rust"), query_defect_walsh(normalized, boundary, modes))

    def test_restrictions_and_high_bit_domain(self):
        n = 7
        boundary = tuple(range(1, n + 1))
        source = near_complete_source(n, 3, {v: True for v in boundary},
                                      {(1, 2, 3), (1, 2, 4), (1, 3, 4), (2, 3, 4)})
        normalized = _normalized_clauses(source, boundary)
        for kw in ({"max_missing": 3}, {"max_defect_variables": 2},
                   {"max_subset_checks": 2}):
            self.assertEqual(query_defect_walsh(normalized, boundary, (0,),
                backend="rust", **kw), query_defect_walsh(normalized, boundary, (0,), **kw))
        with self.assertRaises(ValueError):
            query_defect_walsh(normalized, boundary, (1 << 8,), backend="rust")
        self.assertIsNone(query_defect_walsh(None, (1, 256), (0,), backend="rust"))
        self.assertIsNone(query_defect_walsh(None, (1, 256), (0,)))


if __name__ == "__main__":
    unittest.main()
