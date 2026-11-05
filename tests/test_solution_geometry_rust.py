"""Independent SAT truth-table/Hamming-graph oracle for Rust geometry bridge."""

from __future__ import annotations

from math import comb
import random
import unittest

try:
    from witnora_ve import aux_solution_geometry_native as native_geometry
except (ImportError, AttributeError):
    native_geometry = None


def independent_geometry(source: list[list[int]], nvars: int):
    """(models, clusters, largest cluster, ordered pair distance histogram)."""
    satisfied = [x for x in range(1 << nvars) if all(
        any(bool(x & (1 << (abs(lit) - 1))) == (lit > 0) for lit in clause)
        for clause in source)]
    valid = set(satisfied)
    pending = set(satisfied)
    cluster_sizes = []
    while pending:
        queue = [pending.pop()]
        size = 0
        while queue:
            x = queue.pop()
            size += 1
            for bit in range(nvars):
                y = x ^ (1 << bit)
                if y in pending:
                    pending.remove(y)
                    queue.append(y)
        cluster_sizes.append(size)
    histogram = [0] * (nvars + 1)
    for x in satisfied:
        for y in satisfied:
            histogram[(x ^ y).bit_count()] += 1
    return (len(valid), len(cluster_sizes), max(cluster_sizes, default=0), histogram)


def independent_twelve_clause_analytic() -> list[int]:
    # One (x OR y) has ordered-pair Hamming polynomial 3 + 4t + 2t².
    polynomial = [1]
    for _ in range(12):
        product = [0] * (len(polynomial) + 2)
        for degree, count in enumerate(polynomial):
            for offset, coefficient in enumerate((3, 4, 2)):
                product[degree + offset] += count * coefficient
        polynomial = product
    return polynomial


class GeometryAnalyticControls(unittest.TestCase):
    def test_24_variable_product_geometry(self):
        distances = independent_twelve_clause_analytic()
        self.assertEqual(distances[0], 3 ** 12)
        self.assertEqual(sum(distances), (3 ** 12) ** 2)
        self.assertEqual(len(distances), 25)

    def test_six_variable_matched_energy_formulas_differ_geometrically(self):
        a = [[1, 2], [-1, 3], [-1, 4], [-2, -3], [-2, 5], [-4, 6], [-5, -6]]
        b = [[1, 2], [1, 3], [-1, 4], [-2, -3], [-2, 5], [-4, 6], [-5, -6]]
        self.assertEqual(independent_geometry(a, 6),
                         (2, 2, 1, [2, 0, 0, 0, 0, 0, 2]))
        self.assertEqual(independent_geometry(b, 6),
                         (2, 1, 2, [2, 2, 0, 0, 0, 0, 0]))

    def test_32_free_variable_geometry_is_implicit(self):
        expected = [comb(32, k) * (1 << 32) for k in range(33)]
        self.assertEqual(sum(expected), 1 << 64)
        self.assertEqual(expected[0], 1 << 32)


@unittest.skipUnless(native_geometry is not None, "native Rust wheel unavailable")
class NativeGeometryDifferentialTests(unittest.TestCase):
    @staticmethod
    def native(source, nvars, cap):
        models, clusters, largest, distance_strings = native_geometry(source, nvars, cap)
        return models, clusters, largest, [int(count) for count in distance_strings]

    def test_150_seeded_small_source_geometry_vs_independent_oracle(self):
        rng = random.Random(10012026)
        for trial in range(150):
            nvars = rng.randrange(1, 9)
            source = [[rng.choice((-1, 1)) * rng.randrange(1, nvars + 1)
                       for _ in range(rng.randrange(4))]
                      for _ in range(rng.randrange(0, nvars + 5))]
            with self.subTest(trial=trial):
                self.assertEqual(self.native(source, nvars, 14),
                                 independent_geometry(source, nvars))

    def test_24_variable_analytic_family_without_full_enumeration(self):
        source = [[2*j+1, 2*j+2] for j in range(12)]
        self.assertEqual(self.native(source, 24, 2),
                         (3 ** 12, 1, 3 ** 12, independent_twelve_clause_analytic()))

    def test_32_free_variables_and_exact_2_to_64_pair_sum(self):
        distances = [comb(32, k) * (1 << 32) for k in range(33)]
        self.assertEqual(self.native([], 32, 1),
                         (1 << 32, 1, 1 << 32, distances))

    def test_empty_clause_and_caps_fail_closed(self):
        self.assertEqual(self.native([[]], 3, 1), (0, 0, 0, [0, 0, 0, 0]))
        for source, nvars, cap in (([[0]], 1, 1), ([[3]], 2, 2),
                                   ([[1, 2, 3]], 3, 2)):
            with self.subTest(source=source):
                with self.assertRaises(ValueError):
                    native_geometry(source, nvars, cap)


if __name__ == "__main__":
    unittest.main()
