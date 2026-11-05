"""Generate Lean checks of Python 2-cut claims against their actual signed CNF.

Unlike the earlier graph-differential harness, no Python-generated adjacency
function is passed to Lean.  Lean decodes the normalized signed clauses,
constructs source variables and primal neighbors, and independently scans
residual connected components.  These finite cases are not a universal
CPython refinement theorem or a proof about original DIMACS bytes.
"""

from __future__ import annotations

import random
from itertools import combinations

from witnora_core.cnf import CNFFormula
from witnora_core.separator_affine_family_theorem import primal_graph
from witnora_core.separator_structural_priority import articulation_vertices
from witnora_core.vertex_coupling_separator import vertex_coupling_pairs
from tests.test_vertex_coupling_exhaustive import graph_by_edge_mask, oracle_component_count


def _list(items):
    return "[" + ", ".join(str(item) for item in items) + "]"


def _pairs(pairs):
    return "[" + ", ".join(f"({a}, {b})" for a, b in pairs) + "]"


def _cnf(clauses):
    return "[" + ", ".join(_list(clause) for clause in clauses) + "]"


def _source_formula(graph, case_id):
    # A deterministic mixture of literal signs makes signed decoding active.
    # Every graph edge gets one two-literal clause.  Unit clauses preserve
    # isolated vertices, although eligible connected graphs have none.
    clauses = []
    for a in sorted(graph):
        for b in sorted(graph[a]):
            if a >= b:
                continue
            clauses.append([
                -a if (case_id + a) % 2 else a,
                -b if (case_id + b) % 3 == 0 else b,
            ])
    for a in sorted(graph):
        if not graph[a]:
            clauses.append([a])
    formula = CNFFormula.from_raw_clauses(clauses)
    # Differential guard: normalization did not alter the intended graph.
    if primal_graph(formula) != graph:
        raise AssertionError(f"source/primal mismatch in case {case_id}")
    return formula


def _eligible_graphs():
    # Complete small census + deterministic sampled larger cases.
    for n in (3, 4):
        for mask in range(1 << (n * (n - 1) // 2)):
            graph = graph_by_edge_mask(n, mask)
            if oracle_component_count(graph) == 1 and not articulation_vertices(graph):
                yield graph
    rng = random.Random(630642)
    for n, wanted in ((5, 22), (6, 16)):
        obtained = 0
        attempts = 0
        while obtained < wanted:
            attempts += 1
            if attempts > 20000:
                raise AssertionError("eligible-graph sampler exhausted")
            bits = n * (n - 1) // 2
            mask = rng.randrange(1 << bits)
            graph = graph_by_edge_mask(n, mask)
            if oracle_component_count(graph) != 1 or articulation_vertices(graph):
                continue
            # Every few cases use large, sparse, permuted variable labels.
            if obtained % 4 == 0:
                labels = rng.sample(range(100, 500), n)
                graph = {
                    labels[v]: {labels[w] for w in neighbors}
                    for v, neighbors in graph.items()
                }
            obtained += 1
            yield graph
    for n in (4, 5, 6):
        graph = {v: {(v - 1) % n, (v + 1) % n} for v in range(1, n + 1)}
        # The modulo above is 0-based, so build the cycle explicitly.
        graph = {
            v: {((v - 2) % n) + 1, (v % n) + 1}
            for v in range(1, n + 1)
        }
        yield graph


def emit() -> str:
    lines = [
        "import Witnora.TC063SourceVertexCuts",
        "namespace Witnora.GeneratedPythonSourceVertexCutsDifferential",
        "open Witnora.TC063SourceVertexCuts",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 4000000",
    ]
    total = 0
    witness_cases = 0
    witnesses = 0
    for index, graph in enumerate(_eligible_graphs()):
        # The initial census is 0-based: shift every id to positive DIMACS ids.
        if 0 in graph:
            graph = {
                v + 1: {w + 1 for w in neighbors}
                for v, neighbors in graph.items()
            }
        formula = _source_formula(graph, index)
        raw = _cnf(formula.to_clause_lists())
        pairs = [
            tuple(row["separator"])
            for row in vertex_coupling_pairs(primal_graph(formula))["candidates"]
        ]
        lines.extend([
            f"-- Python signed-CNF source case {index}: "
            f"{len(graph)} variables, {len(formula.clauses)} canonical clauses, "
            f"{len(pairs)} claimed cuts",
            f"example : checkSignedTwoCuts {raw} {_pairs(pairs)} = true := by decide",
            f"example : checkSignedTwoCuts {raw} "
            f"{_pairs(pairs + [(9999, 10000)])} = false := by decide",
        ])
        if pairs:
            witness_cases += 1
            witnesses += len(pairs)
            lines.append(
                f"example : checkSignedTwoCuts {raw} "
                f"{_pairs(pairs[1:])} = false := by decide"
            )
            lines.append(
                f"example : checkSignedTwoCuts {raw} "
                f"{_pairs(pairs + [pairs[0]])} = false := by decide"
            )
        total += 1
    lines.extend([
        "example : checkSignedTwoCuts [[0, 1], [1, 2]] [] = false := by decide",
        "example : checkSignedTwoCuts [[-1, 2], [2, -3], [-3, 4], [1, 4]]",
        "  [(1, 3), (2, 4)] = true := by decide",
        f"-- {total} normalized Python signed-CNF cases; "
        f"{witness_cases} with true cuts; {witnesses} positive cut witnesses.",
        "end Witnora.GeneratedPythonSourceVertexCutsDifferential",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    print(emit(), end="")
