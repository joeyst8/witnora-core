"""R-081 exact Walsh cross-moment Rust/Python oracle differential."""
import random
import unittest
from fractions import Fraction
from itertools import combinations

from tests.test_crc_orbit_oracle import near_complete_source
from witnora_core.crc_independence_audit import audit_defect_source_independence


class IndependenceRustTests(unittest.TestCase):
    def setUp(self):
        try:
            import witnora_ve  # noqa: F401
        except ImportError:
            self.skipTest("native Rust wheel not installed")

    def test_120_seeded_supported_sources(self):
        rng = random.Random(81081)
        for trial in range(120):
            n = rng.randrange(4, 9)
            rank = rng.choice((2, 3))
            universe = list(combinations(range(1, n + 1), rank))
            missing = set(rng.sample(universe, rng.randrange(0, min(5, len(universe)))))
            polarity = {v: bool(rng.randrange(2)) for v in range(1, n + 1)}
            source = near_complete_source(n, rank, polarity, missing)
            chosen = rng.sample(range(1, n + 1), 4)
            left, right = tuple(chosen[:2]), tuple(chosen[2:])
            kw = dict(source_clauses=source,
                      boundary_variables=tuple(range(1, n + 1)),
                      left_group=left, right_group=right)
            with self.subTest(trial=trial):
                self.assertEqual(audit_defect_source_independence(**kw, backend="rust"),
                                 audit_defect_source_independence(**kw))

    def test_big_integer_modes_and_exact_fraction(self):
        from witnora_ve import crc_independence_modes_native, crc_independence_audit_native
        left = [str(1 << 170)]
        right = [str(1 << 200)]
        modes = crc_independence_modes_native(left, right)
        self.assertEqual(list(map(int, modes)), [0, 1 << 170, 1 << 200,
                                                 (1 << 170) | (1 << 200)])
        coeff = [(str(mode), "1", "1" if mode == modes[-1] else "3")
                 for mode in modes]
        failure = crc_independence_audit_native(left, right, coeff)
        self.assertIsNotNone(failure)
        l, r, n, d = failure
        self.assertEqual((int(l), int(r)), (1 << 170, 1 << 200))
        self.assertEqual(Fraction(int(n), int(d)), Fraction(2, 9))


if __name__ == "__main__":
    unittest.main()
