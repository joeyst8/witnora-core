"""R-086 deterministic split-vertex max-flow Rust/Python comparison."""
import random
import unittest

from witnora_core.crc_separator_discovery import discover_source_separator


class SeparatorRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_180_seeded_primal_min_cuts(self):
        rng = random.Random(86086)
        for trial in range(180):
            n = rng.randrange(4, 13)
            boundary = tuple(range(1, n + 1))
            source = []
            for _ in range(rng.randrange(0, 25)):
                vs = rng.sample(boundary, rng.randrange(1, min(n, 4) + 1))
                source.append(vs)  # all-ones assignment is a model
            choices = rng.sample(boundary, 4)
            left = tuple(choices[:2]) if rng.randrange(2) else (choices[0],)
            right = tuple(choices[2:]) if rng.randrange(2) else (choices[2],)
            kw = dict(source_clauses=source, boundary_variables=boundary,
                      left_group=left, right_group=right,
                      satisfying_assignment=(1 << n) - 1,
                      max_separator_size=rng.randrange(0, 6),
                      max_primal_edges=rng.randrange(0, 45))
            with self.subTest(trial=trial):
                self.assertEqual(discover_source_separator(**kw, backend="rust"),
                                 discover_source_separator(**kw))

    def test_named_cut_and_invalid_witness(self):
        cases = [([[1, 3], [3, 2]], (1, 2, 3), (1,), (2,), 7, 1),
                 ([[1, 2]], (1, 2, 3), (1,), (2,), 7, 100),
                 ([[1, 3], [2, 4]], (1, 2, 3, 4), (1,), (2,), 15, 0),
                 ([[1, 3]], (1, 2, 3), (1,), (2,), 0, 2)]
        for source, boundary, left, right, witness, cap in cases:
            kw = dict(source_clauses=source, boundary_variables=boundary,
                      left_group=left, right_group=right,
                      satisfying_assignment=witness, max_separator_size=cap)
            self.assertEqual(discover_source_separator(**kw, backend="rust"),
                             discover_source_separator(**kw))


if __name__ == "__main__":
    unittest.main()
