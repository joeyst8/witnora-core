"""Independent finite graph oracle for Rust W-STRUCT-001 source-CNF diagnostic."""

from __future__ import annotations

import json
from itertools import combinations
import os
from pathlib import Path
import random
import subprocess
from tempfile import TemporaryDirectory
import unittest


RUST_BIN = os.environ.get("WITNORA_RUST_STRUCTURE_BIN")


def graph_profile(n: int, edges: list[tuple[int, int]]) -> dict:
    """Independent set/BFS enumerator; vertex identifiers are one-based."""
    adj = {i: set() for i in range(1, n + 1)}
    for u, v in edges:
        if u != v:
            adj[u].add(v)
            adj[v].add(u)

    def parts(removed: set[int]) -> list[int]:
        unseen = set(range(1, n + 1)) - removed
        sizes = []
        while unseen:
            seed = min(unseen)
            pending = [seed]
            unseen.remove(seed)
            size = 0
            while pending:
                current = pending.pop()
                size += 1
                for other in sorted(adj[current] & unseen):
                    unseen.remove(other)
                    pending.append(other)
            sizes.append(size)
        return sizes

    original = parts(set())
    order = 0 if len(original) >= 2 else None
    witness: list[int] = []
    residual = original
    if order is None:
        for width in (1, 2):
            found = False
            for candidate in combinations(range(1, n + 1), width):
                sizes = parts(set(candidate))
                if len(sizes) >= 2:
                    order, witness, residual = width, list(candidate), sizes
                    found = True
                    break
            if found:
                break
    distinct_edges = {tuple(sorted((u, v))) for u, v in edges if u != v}
    edge_list = sorted(distinct_edges)
    edge_ids = {pair: index for index, pair in enumerate(edge_list)}
    # Independent GF(2) column reduction over sets, not Rust's u128 masks.
    basis: dict[int, set[int]] = {}
    triangles = 0
    for a, b, c in combinations(range(1, n + 1), 3):
        sides = ((a, b), (a, c), (b, c))
        if not all(side in distinct_edges for side in sides):
            continue
        triangles += 1
        column = {edge_ids[side] for side in sides}
        while column:
            pivot = max(column)
            if pivot not in basis:
                basis[pivot] = column
                break
            column = column.symmetric_difference(basis[pivot])
    flag_beta1 = len(distinct_edges) + len(original) - n - len(basis)
    return {
        "variable_count": n,
        "clause_count": len(edges),
        "primal_edges": len(distinct_edges),
        "possible_primal_edges": n * (n - 1) // 2,
        "initial_components": len(original),
        "separator_order_le2": order,
        "separator_variables": witness,
        "residual_components": len(residual),
        "largest_residual_component": max(residual, default=0),
        "primal_flag_beta1_mod2": flag_beta1 if n <= 16 else None,
        "primal_flag_triangle_count": triangles if n <= 16 else None,
        "scope": "source-primal-graph-only; no SAT or complexity certificate",
    }


class IndependentOracleTests(unittest.TestCase):
    def test_matched_variable_count_clause_count_density_different_separators(self):
        bowtie = [(1, 2), (2, 3), (1, 3), (1, 4), (4, 5), (1, 5)]
        chorded_cycle = [(1, 2), (2, 3), (3, 4), (4, 5), (1, 5), (1, 3)]
        left = graph_profile(5, bowtie)
        right = graph_profile(5, chorded_cycle)
        for field in ("variable_count", "clause_count", "primal_edges"):
            self.assertEqual(left[field], right[field])
        self.assertEqual(left["separator_order_le2"], 1)
        self.assertEqual(right["separator_order_le2"], 2)
        self.assertEqual(left["primal_flag_beta1_mod2"], 0)
        self.assertEqual(right["primal_flag_beta1_mod2"], 1)

    def test_topology_small_controls(self):
        self.assertEqual(graph_profile(3, [(1, 2), (2, 3), (1, 3)])
                         ["primal_flag_beta1_mod2"], 0)
        self.assertEqual(graph_profile(4, [(1, 2), (2, 3), (3, 4), (1, 4)])
                         ["primal_flag_beta1_mod2"], 1)
        self.assertEqual(graph_profile(4, list(combinations(range(1, 5), 2)))
                         ["primal_flag_beta1_mod2"], 0)

    def test_matched_separator_order_different_topology_and_source_counts(self):
        # Both are connected monotone 2-CNFs with n=6, m=7, and a minimum
        # two-vertex separator. The flag-complex first Betti numbers differ.
        first = [(1, 2), (1, 3), (1, 4), (2, 3), (2, 5), (4, 6), (5, 6)]
        second = [(1, 2), (1, 3), (1, 4), (2, 5), (2, 6), (3, 5), (4, 6)]
        a, b = graph_profile(6, first), graph_profile(6, second)
        self.assertEqual(a["separator_order_le2"], b["separator_order_le2"])
        self.assertEqual(a["separator_order_le2"], 2)
        self.assertEqual((a["primal_flag_beta1_mod2"], b["primal_flag_beta1_mod2"]),
                         (1, 2))
        def exhaustive_count(edges):
            return sum(all((assignment >> (u - 1) & 1) or
                           (assignment >> (v - 1) & 1) for u, v in edges)
                       for assignment in range(1 << 6))
        self.assertEqual((exhaustive_count(first), exhaustive_count(second)), (16, 17))


@unittest.skipUnless(RUST_BIN and Path(RUST_BIN).is_file(),
                     "native structure diagnostic built by Rust CI")
class RustStructuralProfileTests(unittest.TestCase):
    def run_rust(self, source: str) -> tuple[int, dict | None]:
        with TemporaryDirectory() as tmp:
            source_path = Path(tmp) / "input.cnf"
            source_path.write_text(source, encoding="utf-8")
            result = subprocess.run([RUST_BIN, str(source_path)], capture_output=True, text=True)
            return result.returncode, json.loads(result.stdout) if result.returncode == 0 else None

    def test_300_seeded_source_graphs_against_independent_bfs(self):
        rng = random.Random(53001)
        for trial in range(300):
            n = rng.randrange(1, 9)
            edges = []
            for u in range(1, n + 1):
                for v in range(u + 1, n + 1):
                    if rng.randrange(4) == 0:
                        edges.append((u, v))
            source = f"c trial {trial}\np cnf {n} {len(edges)}\n"
            source += "".join(f"{u} {-v if (trial + u) % 2 else v} 0\n" for u, v in edges)
            code, actual = self.run_rust(source)
            self.assertEqual(code, 0, trial)
            self.assertEqual(actual, graph_profile(n, edges), trial)

    def test_matched_density_adversaries(self):
        families = [
            [(1, 2), (2, 3), (1, 3), (1, 4), (4, 5), (1, 5)],
            [(1, 2), (2, 3), (3, 4), (4, 5), (1, 5), (1, 3)],
        ]
        for edges in families:
            source = "p cnf 5 6\n" + "".join(f"{u} {v} 0\n" for u, v in edges)
            code, actual = self.run_rust(source)
            self.assertEqual(code, 0)
            self.assertEqual(actual, graph_profile(5, edges))

    def test_hostile_dimacs_rejected(self):
        for source in (
            "p cnf 2 1\n1 0\n2 0\n", "p cnf 2 1\n3 0\n",
            "p cnf 2 1\n1 2\n", "p cnf 129 0\n",
            "p cnf 2 1\n1 2 0\np cnf 2 0\n",
            "p cnf 1 1\n-9223372036854775808 0\n",
        ):
            code, value = self.run_rust(source)
            self.assertNotEqual(code, 0, source)
            self.assertIsNone(value)


if __name__ == "__main__":
    unittest.main()
