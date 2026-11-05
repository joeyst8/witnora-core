"""Independent W-017 3-CNF source, covariance and DPLL controls.

The off-diagonal covariance is derived using Python assignment dictionaries;
selected pairs also have a direct 4096-assignment truth-table oracle.
"""

from __future__ import annotations

import json
import os
import subprocess
import unittest

from tests.test_wave_branching_rust import next_random, independent_dpll


BIN = os.environ.get("WITNORA_RUST_SIGNED_COVARIANCE_BIN")
SEEDS = {"fresh_planted_sat_48": 0xD17C0DE1,
         "fresh_uniform_boundary_48": 0xD17C0DE2,
         "fresh_embedded_unsat_56": 0xD17C0DE3}
MASK = (1 << 32) - 1


def independent_source(name: str, index: int) -> list[list[int]]:
    state = (SEEDS[name] ^ (((index + 1) * 0x9E3779B9) & MASK)) & MASK
    clauses = []
    if name == "fresh_embedded_unsat_56":
        clauses.extend([[-v if sign & (1 << (v - 1)) else v for v in (1, 2, 3)]
                        for sign in range(8)])
    count = 56 if name == "fresh_embedded_unsat_56" else 48
    while len(clauses) < count:
        signs = []
        seen = set()
        while len(signs) < 3:
            state = next_random(state)
            var = 1 + state % 12
            if var in seen:
                continue
            seen.add(var)
            state = next_random(state)
            signs.append(-var if state & 1 else var)
        if name == "fresh_planted_sat_48" and all(lit > 0 for lit in signs):
            continue
        clauses.append(signs)
    return clauses


def covariance_matrix(source: list[list[int]]) -> list[list[int]]:
    # Python violation-requirement dictionaries are independent of Rust's
    # signed-literal pair-overlap loops.
    required = [{abs(lit): lit < 0 for lit in clause} for clause in source]
    matrix = []
    for a in required:
        row = []
        for b in required:
            common = a.keys() & b.keys()
            disagree = any(a[k] != b[k] for k in common)
            row.append(-1 if disagree else (1 << len(common)) - 1)
        matrix.append(row)
    return matrix


def geometry(matrix: list[list[int]]) -> dict[str, int]:
    positives = []
    negatives = []
    negative_cycles = 0
    positive_cycles = 0
    for i in range(len(matrix)):
        for j in range(i + 1, len(matrix)):
            val = matrix[i][j]
            if val < 0:
                negatives.append(-val)
            elif val > 0:
                positives.append(val)
            for k in range(j + 1, len(matrix)):
                product = val * matrix[j][k] * matrix[k][i]
                if product < 0:
                    negative_cycles -= product
                elif product > 0:
                    positive_cycles += product
    return {"negative_pairs": len(negatives), "positive_mass": sum(positives),
            "negative_mass": sum(negatives),
            "signed_mass": sum(positives) - sum(negatives),
            "negative_triangle_mass": negative_cycles,
            "positive_triangle_mass": positive_cycles}


def energy_moments(source: list[list[int]]) -> tuple[int, int, int]:
    models = sum_energy = square_energy = 0
    for assignment in range(1 << 12):
        energy = sum(not any(bool(assignment & (1 << (abs(lit) - 1))) == (lit > 0)
                                 for lit in clause) for clause in source)
        models += energy == 0
        sum_energy += energy
        square_energy += energy * energy
    return models, sum_energy, square_energy


def pair_truth(source: list[list[int]], i: int, j: int) -> int:
    both = 0
    for assignment in range(1 << 12):
        if all(not any(bool(assignment & (1 << (abs(lit) - 1))) == (lit > 0)
                       for lit in source[k]) for k in (i, j)):
            both += 1
    # 64 * Cov = 64 * (P(both) - (1/8)*(1/8)).
    return 64 * both // (1 << 12) - 1


@unittest.skipUnless(BIN, "compiled Rust W-017 executable unavailable")
class SignedCovarianceIndependentOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(subprocess.run([BIN], check=True, capture_output=True,
                                               text=True, timeout=240).stdout)

    def test_frozen_populations_and_bounded_correlations(self):
        self.assertEqual(self.report["research_id"], "W-CROSSDOMAIN-017")
        self.assertEqual({f["graph_family"] for f in self.report["families"]}, set(SEEDS))
        for family in self.report["families"]:
            self.assertEqual(family["formulas"], 32)
            self.assertEqual(family["sat_count"] + family["unsat_count"], 32)
            self.assertGreater(family["mean_degree_dpll_clause_scans"], 0)
            self.assertEqual([c["index"] for c in family["controls"]], [0, 1, 31])
            if family["graph_family"] == "fresh_planted_sat_48":
                self.assertEqual(family["sat_count"], 32)
            if family["graph_family"] == "fresh_embedded_unsat_56":
                self.assertEqual(family["unsat_count"], 32)
            for key in ("correlation_scans_with_negative_pairs",
                        "correlation_scans_with_signed_mass",
                        "correlation_scans_with_negative_triangle_mass"):
                value = family[key]
                self.assertTrue(value is None or -1 <= value <= 1)

    def test_independent_controls_variance_gauge_and_search(self):
        for family in self.report["families"]:
            for control in family["controls"]:
                with self.subTest(name=family["graph_family"], index=control["index"]):
                    source = independent_source(family["graph_family"], control["index"])
                    self.assertEqual(control["source"], source)
                    matrix = covariance_matrix(source)
                    self.assertEqual(control["covariance_top_left_8"],
                                     [row[:8] for row in matrix[:8]])
                    stats = geometry(matrix)
                    self.assertEqual(control["geometry"], stats)
                    models, total, squares = energy_moments(source)
                    self.assertEqual(control["models"], models)
                    scaled = 7 * len(source) + 2 * stats["signed_mass"]
                    self.assertEqual(control["scaled_energy_variance"], scaled)
                    self.assertEqual(64 * ((1 << 12) * squares - total ** 2),
                                     scaled * (1 << 24))
                    degree = [sum(abs(lit) == i + 1 for clause in source for lit in clause)
                              for i in range(12)]
                    order = sorted(range(12), key=lambda i: (-degree[i], i))
                    self.assertEqual(control["degree_dpll"], independent_dpll(source, order))
                    for i, j in ((0, 1), (0, 7), (5, len(source) - 1)):
                        self.assertEqual(matrix[i][j], pair_truth(source, i, j))
                    for variable in (1, 5, 12):
                        flip = [[-lit if abs(lit) == variable else lit for lit in clause]
                                for clause in source]
                        self.assertEqual(covariance_matrix(flip), matrix)


if __name__ == "__main__":
    unittest.main()
