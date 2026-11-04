"""R-104: graph components and constructive coloring-bound exact checks."""
import random
import unittest
from itertools import combinations

from witnora_core.nonedge_matching_bound import (
    _connected_components, _is_two_connected,
    _brooks_componentwise_bound, _degeneracy_bound,
)


class NonedgeGraphBoundsRustTests(unittest.TestCase):
    def test_seeded_families(self):
        rng = random.Random(20261111)
        functions = (_connected_components, _is_two_connected,
                     _brooks_componentwise_bound, _degeneracy_bound)
        for trial in range(350):
            n = rng.randrange(0, 19)
            density = rng.choice((0, 0.1, 0.3, 0.5, 0.7, 1.0))
            edges = tuple((u, v) for u, v in combinations(range(n), 2)
                          if rng.random() < density)
            with self.subTest(trial=trial, n=n):
                for func in functions:
                    self.assertEqual(func(n, edges, backend="rust"),
                                     func(n, edges), func.__name__)


if __name__ == "__main__":
    unittest.main()
