"""Emit Lean checks of actual G5 path-boundary hints against signed source CNF.

Python generates affine XOR clauses, runs Gaussian elimination, replays G5
edge provenance and picks a balance-oriented path candidate. Lean then
rebuilds the source primal graph from the signed clauses and independently
checks the resulting two-vertex cut with its verified G14 DFS count.
Finite differential evidence only; the ranking heuristic is not trusted.
"""
from __future__ import annotations

import random
from itertools import combinations

from witnora_core.cnf import CNFFormula
from witnora_core.g5_boundary_path_signal import boundary_path_candidates_from_g5
from witnora_core.operator_genesis import gaussian_eliminate_gf2
from witnora_core.separator_affine_family_theorem import (
    _components_after_removing,
    primal_graph,
)
from witnora_core.xor import canonical_xor_cnf_clauses


def _list(values):
    return "[" + ", ".join(str(v) for v in values) + "]"


def _signed(rows):
    return "[" + ", ".join(_list(row) for row in rows) + "]"


def _pairs(values):
    return "[" + ", ".join(f"({u}, {v})" for u, v in values) + "]"


def emit():
    rng = random.Random(630641)
    lines = [
        "import Witnora.TC063SourceVertexCuts",
        "namespace Witnora.GeneratedG5PathSourceTwoCuts",
        "open Witnora.TC063SourceVertexCuts",
        "open Witnora.TC063VertexCouplingFiniteOracle",
        "open Witnora.G14DFSSeenEnqueue",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 4000000",
    ]
    for n, offset in ((8, 0), (12, 100), (16, 1048576)):
        labels = rng.sample(range(offset + 1, offset + n * 17), n)
        edges = [(labels[i], labels[(i + 1) % n]) for i in range(n)]
        rng.shuffle(edges)
        equations = [
            {"variables": [u, v], "parity_bit": int(j == n - 1)}
            for j, (u, v) in enumerate(edges)
        ]
        elimination = gaussian_eliminate_gf2(equations)
        if elimination["status"] != "UNSAT":
            # Exactly one odd-syndrome edge in the cycle is contradictory.
            raise AssertionError("cyclic XOR source unexpectedly SAT")
        initial = elimination["gaussian_elimination_trace"][0]["rows"]
        hints = boundary_path_candidates_from_g5(
            initial, elimination["row_operations"]
        )["candidates"]
        if not hints:
            raise AssertionError("no path boundary survived the G5 trace")
        selected = tuple(hints[0]["separator"])
        raw = [
            list(clause)
            for eq in equations
            for clause in sorted(
                canonical_xor_cnf_clauses(
                    eq["variables"], eq["parity_bit"]
                )
            )
        ]
        formula = CNFFormula.from_raw_clauses(raw)
        graph = primal_graph(formula)
        pieces = _components_after_removing(graph, set(selected))
        if sorted(map(len, pieces)) != [(n - 2) // 2, (n - 2) // 2]:
            raise AssertionError(
                f"n={n}: selected G5 hint is not an optimal two-cut"
            )
        source = _signed(formula.to_clause_lists())
        decode = f"(Witnora.SignedSerialization.decodeCNF {source})"
        vertices = f"(canonicalSourceVertices {decode})"
        neighbors = f"(clauseNeighbors {decode})"
        u, v = selected
        lines.extend([
            f"-- Python G5 source cycle n={n}, {len(raw)} source clauses; "
            f"optimal derived cut {selected}",
            f"example : twoCutFlag {vertices} {neighbors} "
            f"{u} {v} = true := by decide",
            f"example : residualComponentCount {vertices} {neighbors} "
            f"[{u}, {v}] = 2 := by decide",
        ])
        if n == 8:
            all_cuts = [
                pair for pair in combinations(sorted(graph), 2)
                if len(_components_after_removing(graph, set(pair))) > 1
            ]
            lines.append(
                f"example : checkSignedTwoCuts {source} "
                f"{_pairs(all_cuts)} = true := by decide"
            )
    lines.extend([
        "end Witnora.GeneratedG5PathSourceTwoCuts",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    print(emit(), end="")
