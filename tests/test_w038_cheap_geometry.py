"""Cheap overlap identity and wave-geometry equivalence tests."""

import itertools
import random
import unittest

from scripts.w037_geometry_features import features
from scripts.w038_cheap_geometry import FEATURE_NAMES, cheap_features


class CheapGeometryTests(unittest.TestCase):
    def test_full_feature_equivalence_on_random_sources(self):
        rng = random.Random(380038)
        pool = [[s * v for s, v in zip(signs, variables)]
                for variables in itertools.combinations(range(1, 9), 3)
                for signs in itertools.product((-1, 1), repeat=3)]
        for n in (5, 8):
            restricted = [c for c in pool if max(map(abs, c)) <= n]
            for m in (1, 3, 12, 32):
                for _ in range(5):
                    clauses = rng.sample(restricted, m)
                    got = cheap_features(n, clauses)
                    full = features(n, clauses)
                    self.assertEqual(tuple(got), FEATURE_NAMES)
                    for name in FEATURE_NAMES:
                        self.assertAlmostEqual(got[name], full[name], places=11)

    def test_permutation_and_flip_invariance(self):
        clauses = [[1, -2, 3], [-1, 2, 4], [1, 2, -4], [-2, -3, -4]]
        baseline = cheap_features(4, clauses)
        perm = {1: 3, 2: 4, 3: 1, 4: 2}
        transformed = [[(1 if x > 0 else -1) * perm[abs(x)] * (-1 if abs(x) == 2 else 1)
                        for x in clause] for clause in reversed(clauses)]
        changed = cheap_features(4, transformed)
        for name in FEATURE_NAMES:
            self.assertAlmostEqual(baseline[name], changed[name], places=11)

    def test_reject_invalid_clauses(self):
        for clauses in ([], [[0]], [[1, -1]], [[1, 2, 3, 4]], [[5]]):
            with self.assertRaises(ValueError):
                cheap_features(4, clauses)


if __name__ == '__main__':
    unittest.main()
