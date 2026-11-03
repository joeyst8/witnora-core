"""Emit Lean-kernel finite checks of actual Python articulation and 2-cut outputs.

The expected lists come from the production Python low-link scanner.
The Lean checks independently recompute connectivity with its existing
verified finite DFS component scanner. This is finite differential
acceptance, not universal Python execution refinement.
"""

from __future__ import annotations

import random

from tests.test_vertex_coupling_exhaustive import (
    graph_by_edge_mask,
    oracle_component_count,
)
from witnora_core.separator_structural_priority import articulation_vertices
from witnora_core.vertex_coupling_separator import vertex_coupling_pairs


def _cases():
    for n in (2, 3, 4):
        for mask in range(1 << (n * (n - 1) // 2)):
            yield n, mask
    rng = random.Random(630641)
    for n, count in ((5, 96), (6, 64)):
        bits = n * (n - 1) // 2
        for mask in rng.sample(range(1 << bits), count):
            yield n, mask


def _list(values):
    return "[" + ", ".join(map(str, values)) + "]"


def _pairs(pairs):
    return "[" + ", ".join(f"({u}, {v})" for u, v in pairs) + "]"


def emit() -> str:
    lines = [
        "import Witnora.TC063VertexCouplingFiniteOracle",
        "namespace Witnora.GeneratedPythonVertexCouplingDifferential",
        "open Witnora.TC063VertexCouplingFiniteOracle",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 4000000",
    ]
    total = eligible = 0
    for idx, (n, mask) in enumerate(_cases()):
        graph = graph_by_edge_mask(n, mask)
        name = f"case{idx}Neighbors"
        lines.extend([
            f"-- Actual Python case {idx}: {n} vertices, mask={mask}",
            f"def {name} (v : Nat) : List Nat :=",
            "  match v with",
        ])
        for vertex in graph:
            lines.append(f"  | {vertex} => {_list(sorted(graph[vertex]))}")
        lines.append("  | _ => []")
        vertices = _list(range(n))
        art = list(articulation_vertices(graph))
        lines.append(
            f"example : checkArticulations {vertices} {name} {_list(art)} = true := by decide"
        )
        baseline = oracle_component_count(graph)
        lines.append(
            f"example : residualComponentCount {vertices} {name} [] = {baseline} := by decide"
        )
        if n >= 3 and baseline == 1 and not art:
            pairs = [
                tuple(row["separator"])
                for row in vertex_coupling_pairs(graph)["candidates"]
            ]
            lines.append(
                f"example : checkTwoCuts {vertices} {name} {_pairs(pairs)} = true := by decide"
            )
            eligible += 1
        total += 1
    lines.extend([
        f"-- {total} Python graph cases, {eligible} connected articulation-free pair cases",
        "end Witnora.GeneratedPythonVertexCouplingDifferential",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    print(emit(), end="")
