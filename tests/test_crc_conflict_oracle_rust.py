"""R-084 mixed-polarity bounded Walsh convolution Rust differential."""
from itertools import combinations
import random
import unittest

from tests.test_crc_conflict_oracle import add_conflict
from tests.test_crc_orbit_oracle import near_complete_source
from witnora_core.crc_boundary import _normalized_clauses
from witnora_core.crc_conflict_oracle import query_conflict_walsh


class ConflictRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_100_seeded_mixed_sign_sources(self):
        rng = random.Random(84084)
        for trial in range(100):
            n = rng.randrange(5, 9)
            boundary = tuple(range(1, n + 1))
            universe = list(combinations(boundary, 3))
            missing = set(rng.sample(universe, rng.randrange(0, 5)))
            polarity = {v: bool(rng.randrange(2)) for v in boundary}
            source = near_complete_source(n, 3, polarity, missing)
            supports = [s for s in universe if s not in missing]
            for support in rng.sample(supports, rng.choice((1, 2))):
                source = add_conflict(source, support)
            extra = rng.randrange(2)
            boundary = tuple(range(1, n + extra + 1))
            normalized = _normalized_clauses(source, boundary)
            modes = tuple(rng.randrange(1 << len(boundary)) for _ in range(14))
            with self.subTest(trial=trial):
                self.assertEqual(query_conflict_walsh(normalized, boundary,
                    modes, backend="rust"), query_conflict_walsh(normalized, boundary, modes))

    def test_caps_and_no_conflict(self):
        boundary = tuple(range(1, 7))
        source = near_complete_source(6, 3, {v: True for v in boundary}, set())
        normalized = _normalized_clauses(source, boundary)
        self.assertIsNone(query_conflict_walsh(normalized, boundary, (0,), backend="rust"))
        conflict = _normalized_clauses(add_conflict(source, (1, 2, 3)), boundary)
        for kw in ({"max_exception_clauses": 0}, {"max_exception_variables": 1},
                   {"max_base_mode_queries": 1}):
            self.assertEqual(query_conflict_walsh(conflict, boundary,
                    (0, 1), backend="rust", **kw),
                query_conflict_walsh(conflict, boundary, (0, 1), **kw))


if __name__ == "__main__":
    unittest.main()
