"""Auxiliary-variable factor geometry, not a tensor runtime benchmark.

Compare original clause factors, flat source-scope parity factors, and
the clause↔aux plus aux-parity decomposition. All widths are obtained
by the same greedy min-degree elimination algorithm, not exact treewidth.
"""
from __future__ import annotations

from time import perf_counter

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from witnora_core.aux_violation_tensors import (
    auxiliary_factor_scopes, direct_parity_factor_scopes,
)
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.sparse_parity_checks import min_degree_elimination_width


def width(scopes: list[set[int]], nvars: int) -> tuple[int, float]:
    start = perf_counter()
    result = min_degree_elimination_width(scopes, nvars)
    return result, 1000 * (perf_counter() - start)


def main() -> None:
    print("n clauses kind factor_count graph_vertices max_scope "
          "greedy_elimination_width elimination_ms")
    for nvars, nclauses in ((32, 224), (96, 576), (256, 1536)):
        source = random_three_cnf(nvars, nclauses, 630000 + nvars,
                                  planted=True)
        sketch = geometry_aware_sparse_sketch(source, nvars)
        original = [{abs(lit) for lit in clause} for clause in source]
        direct = direct_parity_factor_scopes(source, sketch)
        aux = auxiliary_factor_scopes(source, sketch)
        for name, factors, graph_size in (
                ("source", original, nvars),
                ("direct", direct, nvars),
                ("aux", aux, nvars + nclauses)):
            w, elapsed = width(factors, graph_size)
            print(f"{nvars} {nclauses} {name} {len(factors)} "
                  f"{graph_size} {max(map(len, factors), default=0)} "
                  f"{w} {elapsed:.3f}")
    print("No tensor coefficient extraction, interpolation, or SAT "
          "performance comparison was performed.")


if __name__ == "__main__":
    main()
