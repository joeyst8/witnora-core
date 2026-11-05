"""Independent source-level sublevel connectivity oracle for Rust ground barriers."""

from __future__ import annotations

import random
import unittest

try:
    from witnora_ve import aux_ground_barriers_native as native_barriers
except (ImportError, AttributeError):
    native_barriers = None


def independent_ground_barriers(source: list[list[int]], nvars: int):
    """Ground-state equivalence only; excludes sublevel components without models."""
    energy = [sum(not any(bool(x & (1 << (abs(lit)-1))) == (lit > 0)
                          for lit in clause) for clause in source)
              for x in range(1 << nvars)]
    ground = {x for x, count in enumerate(energy) if count == 0}
    counts, largest = [], []
    for threshold in range(len(source) + 1):
        pending = {x for x, count in enumerate(energy) if count <= threshold}
        ground_sizes = []
        while pending:
            queue = [pending.pop()]
            ground_size = 0
            while queue:
                x = queue.pop()
                ground_size += int(x in ground)
                for bit in range(nvars):
                    neighbor = x ^ (1 << bit)
                    if neighbor in pending:
                        pending.remove(neighbor)
                        queue.append(neighbor)
            if ground_size:
                ground_sizes.append(ground_size)
        counts.append(len(ground_sizes))
        largest.append(max(ground_sizes, default=0))
    barrier = next((threshold for threshold, count in enumerate(counts) if count == 1), None)
    return len(ground), counts, largest, barrier


def independent_equivalence_family(blocks: int):
    source = []
    for j in range(blocks):
        x, y = 2*j+1, 2*j+2
        source += [[x, -y], [-x, y]]
    return source


class GroundBarrierAnalyticTests(unittest.TestCase):
    def test_twelve_independent_pairs_collapse_at_one_energy_unit(self):
        source = independent_equivalence_family(12)
        self.assertEqual(len(source), 24)
        expected_models = 1 << 12
        expected_counts = [expected_models] + [1] * 24
        expected_largest = [1] + [expected_models] * 24
        self.assertEqual((expected_counts[0], expected_counts[1]), (4096, 1))
        # Independent direct truth table at two blocks checks the same pattern.
        self.assertEqual(independent_ground_barriers(independent_equivalence_family(2), 4),
                         (4, [4, 1, 1, 1, 1], [1, 4, 4, 4, 4], 1))
        self.assertEqual(len(expected_counts), len(source) + 1)
        self.assertEqual(len(expected_largest), len(source) + 1)

    def test_matched_earlier_spectrum_witness_has_distinct_barriers(self):
        source_a = [[1,2],[-1,3],[-1,4],[-2,-3],[-2,5],[-4,6],[-5,-6]]
        source_b = [[1,2],[1,3],[-1,4],[-2,-3],[-2,5],[-4,6],[-5,-6]]
        a = independent_ground_barriers(source_a, 6)
        b = independent_ground_barriers(source_b, 6)
        self.assertEqual(a[0], 2)
        self.assertEqual(b[0], 2)
        self.assertEqual(a[1][:2], [2, 1])
        self.assertEqual(b[1][:2], [1, 1])
        self.assertEqual((a[3], b[3]), (1, 0))


@unittest.skipUnless(native_barriers is not None, "native Rust wheel unavailable")
class NativeGroundBarrierTests(unittest.TestCase):
    def test_150_seeded_random_cnf_full_threshold_profiles(self):
        rng = random.Random(10022026)
        for trial in range(150):
            nvars = rng.randrange(1, 9)
            source = [[rng.choice((-1, 1)) * rng.randrange(1, nvars + 1)
                       for _ in range(rng.randrange(4))]
                      for _ in range(rng.randrange(0, nvars + 5))]
            with self.subTest(trial=trial):
                self.assertEqual(native_barriers(source, nvars, 14),
                                 independent_ground_barriers(source, nvars))

    def test_24_variable_analytic_family_without_global_enumeration(self):
        source = independent_equivalence_family(12)
        self.assertEqual(native_barriers(source, 24, 2),
                         (4096, [4096] + [1] * 24, [1] + [4096] * 24, 1))

    def test_unsat_free_variables_and_fail_closed_caps(self):
        self.assertEqual(native_barriers([], 32, 1),
                         (1 << 32, [1], [1 << 32], 0))
        self.assertEqual(native_barriers([[1], [-1]], 1, 1),
                         (0, [0, 0, 0], [0, 0, 0], None))
        for source, nvars, cap in (([[0]], 1, 1), ([[3]], 2, 2),
                                   ([[1,2,3]], 3, 2)):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    native_barriers(source, nvars, cap)


if __name__ == "__main__":
    unittest.main()
