"""Independent literal, Walsh-moment and decision-DPLL oracle for Rust W-016.

The test implements the frozen generator and complete DPLL independently from
the Rust code. Positive solver-speed results are never required for CI.
"""

from __future__ import annotations

import json
import math
import os
import subprocess
import unittest


BIN = os.environ.get("WITNORA_RUST_WAVE_BRANCHING_BIN")
MASK = (1 << 32) - 1
SEEDS = {"new_planted_sat_48": 0xC0FFEE11,
         "new_uniform_boundary_48": 0xC0FFEE22,
         "new_embedded_unsat_56": 0xC0FFEE33}


def next_random(state: int) -> int:
    state ^= (state << 13) & MASK
    state ^= state >> 17
    state ^= (state << 5) & MASK
    return state & MASK


def independent_source(name: str, index: int) -> list[list[int]]:
    state = (SEEDS[name] ^ (((index + 1) * 0x9E3779B9) & MASK)) & MASK
    clauses = []
    if name == "new_embedded_unsat_56":
        for signing in range(8):
            clauses.append([-v if signing & (1 << (v - 1)) else v
                            for v in (1, 2, 3)])
    target = 56 if name == "new_embedded_unsat_56" else 48
    while len(clauses) < target:
        used = set()
        clause = []
        while len(clause) < 3:
            state = next_random(state)
            variable = state % 12 + 1
            if variable in used:
                continue
            used.add(variable)
            state = next_random(state)
            clause.append(-variable if state & 1 else variable)
        if name == "new_planted_sat_48" and all(lit > 0 for lit in clause):
            continue
        clauses.append(clause)
    return clauses


def scope_selection(clauses: list[list[int]]) -> tuple[list[int], int]:
    selected = [0]
    comparisons = 0
    while len(selected) < 4:
        best = None
        for candidate, clause in enumerate(clauses):
            if candidate in selected:
                continue
            score = 0
            for prior in selected:
                comparisons += 1
                score += len({abs(x) for x in clause}
                             & {abs(x) for x in clauses[prior]})
            if best is None or score > best[1]:
                best = (candidate, score)
        selected.append(best[0])
    return selected, comparisons


def independent_moments(clauses: list[list[int]], selected: list[int]) -> tuple[int, list[int]]:
    bias = 0
    moments = [0] * 12
    for assignment in range(1 << 12):
        parity = 0
        for index in selected:
            if not any(bool(assignment & (1 << (abs(lit) - 1))) == (lit > 0)
                       for lit in clauses[index]):
                parity ^= 1
        character = -1 if parity else 1
        bias += character
        for variable in range(12):
            moments[variable] += character * (
                -1 if assignment & (1 << variable) else 1)
    return bias, moments


def entropy(p: float) -> float:
    if p <= 0.0 or p >= 1.0:
        return 0.0
    return -p * math.log2(p) - (1 - p) * math.log2(1 - p)


def independent_order(clauses: list[list[int]], bias: int,
                      moments: list[int]) -> tuple[list[list[int]], bool, list[float]]:
    degree = [sum(abs(lit) == i + 1 for clause in clauses for lit in clause)
              for i in range(12)]
    degree_order = sorted(range(12), key=lambda i: (-degree[i], i))
    mu = bias / (1 << 12)
    gain = []
    for first in moments:
        h = first / (1 << 12)
        value = entropy((1 + mu) / 2) - 0.5 * (
            entropy((1 + mu + h) / 2) + entropy((1 + mu - h) / 2))
        gain.append(max(value, 0))
    # Nonnegative values are safely and deterministically rounded here.
    wave_order = sorted(range(12), key=lambda i: (-round(gain[i], 12), -degree[i], i))
    use_wave = max(gain) >= 0.02
    return [list(range(12)), degree_order, wave_order,
            wave_order if use_wave else degree_order], use_wave, gain


def independent_dpll(clauses: list[list[int]], order: list[int]) -> dict[str, int | bool]:
    scans = 0
    nodes = 0

    def visit(values: tuple[bool | None, ...]) -> bool:
        nonlocal scans, nodes
        nodes += 1
        values = list(values)
        while True:
            changed = False
            for clause in clauses:
                scans += 1
                if any(values[abs(lit) - 1] is not None
                       and values[abs(lit) - 1] == (lit > 0) for lit in clause):
                    continue
                free = [lit for lit in clause if values[abs(lit) - 1] is None]
                if not free:
                    return False
                if len(free) == 1:
                    lit = free[0]
                    values[abs(lit) - 1] = lit > 0
                    changed = True
            if not changed:
                break
        all_satisfied = True
        for clause in clauses:
            scans += 1
            if not any(values[abs(lit) - 1] is not None
                       and values[abs(lit) - 1] == (lit > 0) for lit in clause):
                all_satisfied = False
                break
        if all_satisfied:
            return True
        variable = next(i for i in order if values[i] is None)
        for choice in (False, True):
            branch = values.copy()
            branch[variable] = choice
            if visit(tuple(branch)):
                return True
        return False

    sat = visit((None,) * 12)
    return {"nodes": nodes, "clause_scans": scans, "sat": sat}


def independent_sat(clauses: list[list[int]]) -> bool:
    for assignment in range(1 << 12):
        if all(any(bool(assignment & (1 << (abs(lit) - 1))) == (lit > 0)
                   for lit in clause) for clause in clauses):
            return True
    return False


@unittest.skipUnless(BIN, "Rust W-016 executable unavailable")
class WaveBranchingIndependentOracle(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = json.loads(subprocess.run([BIN], capture_output=True, text=True,
                                               timeout=240, check=True).stdout)

    def test_predeclared_populations_and_cost_accounting(self):
        self.assertEqual(self.report["research_id"], "W-CROSSDOMAIN-016")
        self.assertEqual(self.report["frozen_gate_min_mutual_information_bits"], 0.02)
        self.assertEqual({r["name"] for r in self.report["families"]}, set(SEEDS))
        for family in self.report["families"]:
            self.assertEqual(family["cases"], 32)
            self.assertEqual(family["sat_count"] + family["unsat_count"], 32)
            self.assertTrue(0 <= family["gated_wave_uses"] <= 32)
            self.assertTrue(0 <= family["mean_wave_selected_clause_visits"] <= 32)
            self.assertTrue(0 <= family["mean_wave_literal_visits"] <= 96)
            self.assertEqual([r["index"] for r in family["controls"]], [0, 1, 31])
            if family["name"] == "new_planted_sat_48":
                self.assertEqual(family["sat_count"], 32)
            if family["name"] == "new_embedded_unsat_56":
                self.assertEqual(family["unsat_count"], 32)
            for name in ("ascending", "degree", "wave", "gated_wave"):
                method = family["methods"][name]
                self.assertGreater(method["mean_nodes"], 0)
                self.assertGreater(method["mean_clause_scans"], 0)
                self.assertEqual(sum(method[k] for k in (
                    "wins_vs_degree", "ties_vs_degree", "losses_vs_degree")), 32)
                if name != "ascending":
                    self.assertEqual(method["timing_repetitions"], 20)
                    self.assertGreater(method["timed_full_pipeline_total_nanoseconds"], 0)

    def test_independent_source_truth_table_moments_and_dpll(self):
        for family in self.report["families"]:
            for control in family["controls"]:
                with self.subTest(name=family["name"], index=control["index"]):
                    clauses = independent_source(family["name"], control["index"])
                    self.assertEqual(control["source"], clauses)
                    row, comparisons = scope_selection(clauses)
                    self.assertEqual(control["selected_parity_row"], row)
                    self.assertEqual(control["selector_comparisons"], comparisons)
                    bias, moments = independent_moments(clauses, row)
                    self.assertEqual(control["signed_wave_bias"], bias)
                    self.assertEqual(control["signed_first_moments"], moments)
                    orders, uses, gain = independent_order(clauses, bias, moments)
                    self.assertEqual(control["gate_uses_wave"], uses)
                    self.assertEqual(control["orders"], orders)
                    for actual, expected in zip(control["mutual_information_bits"], gain):
                        self.assertAlmostEqual(actual, expected, places=12)
                    truth = independent_sat(clauses)
                    for order, observed in zip(orders, control["costs"]):
                        self.assertEqual(independent_dpll(clauses, order), observed)
                        self.assertEqual(observed["sat"], truth)


if __name__ == "__main__":
    unittest.main()
