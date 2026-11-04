"""R-087 exact source cutset enumeration Python/Rust differential."""
import random
import unittest

from witnora_core.crc_cutset_count import count_source_by_separator


class CutsetRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_180_seeded_cnf_cutsets(self):
        rng = random.Random(87087)
        for trial in range(180):
            n = rng.randrange(4, 10)
            boundary = tuple(range(1, n + 1))
            source = []
            for _ in range(rng.randrange(0, 14)):
                variables = rng.sample(boundary, rng.randrange(1, 4))
                row = [v if rng.randrange(2) else -v for v in variables]
                row[0] = variables[0]  # checked all-ones model
                source.append(row)
            kw = dict(source_clauses=source, boundary_variables=boundary,
                      left_group=(1,), right_group=(2,),
                      satisfying_assignment=(1 << n) - 1,
                      max_separator_size=rng.randrange(0, 4),
                      max_component_variables=rng.randrange(1, 10),
                      max_assignment_states=rng.choice((1, 16, 1024, 100000)),
                      max_separator_branches=rng.choice((1, 2, 4, 8, 64)))
            with self.subTest(trial=trial):
                self.assertEqual(count_source_by_separator(**kw, backend="rust"),
                                 count_source_by_separator(**kw))

    def test_star_xor_and_free_components(self):
        cases = [([[v, 12] for v in range(1, 12)], tuple(range(1, 13)),
                  (1,), (2,), (1 << 12) - 1),
                 ([[-1, 2], [1, -2], [-2, 3], [2, -3]],
                  (1, 2, 3), (1,), (3,), 7),
                 ([[1, 3], [2, 4]], (1, 2, 3, 4), (1,), (2,), 15)]
        for source, boundary, left, right, witness in cases:
            kw = dict(source_clauses=source, boundary_variables=boundary,
                      left_group=left, right_group=right,
                      satisfying_assignment=witness)
            self.assertEqual(count_source_by_separator(**kw, backend="rust"),
                             count_source_by_separator(**kw))


if __name__ == "__main__":
    unittest.main()
