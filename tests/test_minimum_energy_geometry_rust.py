"""Independent exact Max-SAT energy-landscape and connectivity oracle."""

from __future__ import annotations

import random
import unittest

from tests.test_ground_barriers_rust import independent_ground_barriers

try:
    from witnora_ve import aux_minimum_energy_geometry_native as native_minimum
except (ImportError, AttributeError):
    native_minimum = None


def independent_minimum_geometry(source: list[list[int]], nvars: int):
    energies = [sum(not any(bool(x & (1 << (abs(lit)-1))) == (lit > 0)
                            for lit in clause) for clause in source)
                for x in range(1 << nvars)]
    minimum = min(energies)
    minima = {x for x, energy in enumerate(energies) if energy == minimum}
    clusters, largest = [], []
    for extra in range(len(source) + 1):
        pending = {x for x, energy in enumerate(energies) if energy <= minimum + extra}
        sizes = []
        while pending:
            queue = [pending.pop()]
            ground_size = 0
            while queue:
                assignment = queue.pop()
                ground_size += int(assignment in minima)
                for bit in range(nvars):
                    neighbor = assignment ^ (1 << bit)
                    if neighbor in pending:
                        pending.remove(neighbor)
                        queue.append(neighbor)
            if ground_size:
                sizes.append(ground_size)
        clusters.append(len(sizes))
        largest.append(max(sizes, default=0))
    barrier = next(extra for extra, count in enumerate(clusters) if count == 1)
    return minimum, len(minima), clusters, largest, barrier


def unsat_equivalence_family(blocks: int):
    source = []
    for j in range(blocks):
        x, y = 2*j+1, 2*j+2
        source.extend([[x, -y], [-x, y]])
    z = 2*blocks+1
    source.extend([[z], [-z]])
    return source


class MinimumEnergyAnalyticTests(unittest.TestCase):
    def test_contradictory_unit_constraints_are_nonzero_energy_ground_states(self):
        self.assertEqual(independent_minimum_geometry([[1], [-1]], 1),
                         (1, 2, [1, 1, 1], [2, 2, 2], 0))
        self.assertEqual(independent_minimum_geometry([[]], 3),
                         (1, 8, [1, 1], [8, 8], 0))

    def test_25_variable_unsat_product_analytical_control(self):
        source = unsat_equivalence_family(12)
        self.assertEqual(len(source), 26)
        expected_min, expected_minimizers = 1, 1 << 13
        expected_counts = [1 << 12] + [1] * 26
        expected_largest = [2] + [expected_minimizers] * 26
        self.assertEqual((expected_counts[0], expected_counts[1]), (4096, 1))
        self.assertEqual((expected_min, expected_minimizers), (1, 8192))
        self.assertEqual(len(expected_largest), len(source) + 1)
        # A two-block independent truth table confirms the derived formula.
        self.assertEqual(independent_minimum_geometry(unsat_equivalence_family(2), 5),
                         (1, 8, [4,1,1,1,1,1,1], [2,8,8,8,8,8,8], 1))

    def test_sat_case_agrees_with_previous_ground_state_definition(self):
        source = [[1,2], [-1,3], [-2,3]]
        minimum, models, counts, largest, barrier = independent_minimum_geometry(source, 3)
        self.assertEqual(minimum, 0)
        self.assertEqual((models, counts, largest, barrier),
                         independent_ground_barriers(source, 3))


@unittest.skipUnless(native_minimum is not None, "native Rust wheel unavailable")
class NativeMinimumEnergyDifferentialTests(unittest.TestCase):
    def test_150_random_small_signed_sources_vs_independent_oracle(self):
        rng = random.Random(11032026)
        for trial in range(150):
            nvars = rng.randrange(1, 9)
            source = [[rng.choice((-1, 1)) * rng.randrange(1, nvars+1)
                       for _ in range(rng.randrange(4))]
                      for _ in range(rng.randrange(0, nvars + 5))]
            with self.subTest(trial=trial):
                self.assertEqual(native_minimum(source, nvars, 14),
                                 independent_minimum_geometry(source, nvars))

    def test_25_variable_unsat_analytical_family(self):
        source = unsat_equivalence_family(12)
        self.assertEqual(native_minimum(source, 25, 2),
                         (1, 8192, [4096] + [1] * 26,
                          [2] + [8192] * 26, 1))

    def test_empty_clause_free_variables_and_caps(self):
        self.assertEqual(native_minimum([[]], 3, 1), (1, 8, [1,1], [8,8], 0))
        self.assertEqual(native_minimum([], 32, 1),
                         (0, 1 << 32, [1], [1 << 32], 0))
        for source, nvars, cap in (([[0]], 1, 1), ([[4]], 3, 3),
                                   ([[1,2,3]], 3, 2)):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    native_minimum(source, nvars, cap)


if __name__ == "__main__":
    unittest.main()
