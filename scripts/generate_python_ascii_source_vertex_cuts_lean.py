"""Cross-check Python's exact canonical DIMACS bytes in independent Lean.

For each selected real Python CNFFormula, the new Lean gate checks:
  original ASCII document bytes -> parsed signed tokens -> exact clauses
  -> primal graph reconstructed by Lean -> full two-vertex-cut claims.

The supplied tokens/clauses/candidates are all treated as untrusted and
compared with the original document or independently recomputed by Lean.
Finite differential evidence is not universal Python-semantics refinement.
"""

from __future__ import annotations

from witnora_core.separator_affine_family_theorem import primal_graph
from witnora_core.vertex_coupling_separator import vertex_coupling_pairs
from scripts.generate_python_source_vertex_cuts_differential_lean import (
    _eligible_graphs,
    _source_formula,
    _list,
    _pairs,
    _cnf,
)


def emit() -> str:
    lines = [
        "import Witnora.TC063AsciiSourceVertexCuts",
        "namespace Witnora.GeneratedPythonAsciiSourceVertexCuts",
        "open Witnora.TC063AsciiSourceVertexCuts",
        "set_option maxRecDepth 8192",
        "set_option maxHeartbeats 8000000",
    ]
    selected = {0, 1, 2, 10, 51}
    count = 0
    for index, graph in enumerate(_eligible_graphs()):
        if index not in selected:
            continue
        if 0 in graph:
            graph = {
                v + 1: {w + 1 for w in neighbors}
                for v, neighbors in graph.items()
            }
        formula = _source_formula(graph, index)
        clauses = formula.to_clause_lists()
        tokens = [
            literal
            for clause in clauses
            for literal in [*clause, 0]
        ]
        source_bytes = list(formula.canonical_dimacs().encode("ascii"))
        pairs = [
            tuple(row["separator"])
            for row in vertex_coupling_pairs(primal_graph(formula))["candidates"]
        ]
        source = _list(source_bytes)
        token_text = _list(tokens)
        raw = _cnf(clauses)
        claims = _pairs(pairs)
        lines.extend([
            f"-- Case {index}: Python canonical_dimacs bytes, "
            f"{len(clauses)} clauses, {len(pairs)} claimed cuts.",
            f"example : checkAsciiTwoCuts {source} "
            f"{token_text} {raw} {claims} = true := by decide",
            f"example : checkAsciiTwoCuts {_list(source_bytes[:-2])} "
            f"{token_text} {raw} {claims} = false := by decide",
            f"example : checkAsciiTwoCuts {source} "
            f"{_list([*tokens, 0])} {raw} {claims} = false := by decide",
            f"example : checkAsciiTwoCuts {source} "
            f"{token_text} {_cnf(clauses[:-1])} {claims} = false := by decide",
            f"example : checkAsciiTwoCuts {source} "
            f"{token_text} {raw} "
            f"{_pairs([*pairs, (9999, 10000)])} = false := by decide",
        ])
        if count == 0:
            commented = list(b"c verified-source-input\\n") + source_bytes
            lines.append(
                f"example : checkAsciiTwoCuts {_list(commented)} "
                f"{token_text} {raw} {claims} = true := by decide"
            )
        count += 1
    if count != len(selected):
        raise AssertionError(f"only {count} of {len(selected)} requested cases")
    lines.extend([
        f"-- {count} real canonical DIMACS documents with 4 forged controls each.",
        "end Witnora.GeneratedPythonAsciiSourceVertexCuts",
        "",
    ])
    return "\n".join(lines)


if __name__ == "__main__":
    print(emit(), end="")
