"""Compression-versus-contraction frontier for geometry-aware parity rows.

Constructs one factor directly per parity row, whose scope is the union of
variables of its selected source clauses. Widths are heuristic min-degree
elimination widths, not exact treewidth or measured tensor runtimes.
"""
from __future__ import annotations

from time import perf_counter

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from witnora_core.geometry_aware_parity import geometry_aware_sparse_sketch
from witnora_core.sparse_parity_checks import (
    build_sparse_odd_sketch, min_degree_elimination_width,
)


def scopes(source: list[list[int]],
           rows: tuple[tuple[int, ...], ...]) -> list[set[int]]:
    return [{abs(lit) for j in row for lit in source[j]} for row in rows]


def main() -> None:
    print("n clauses grouping row_limit rows max_factor_vars "
          "heuristic_width construction_ms")
    for nvars, nclauses in ((32, 224), (96, 576), (256, 1536)):
        source = random_three_cnf(nvars, nclauses, 630000 + nvars,
                                  planted=True)
        original_scopes = [{abs(lit) for lit in row} for row in source]
        original_width = min_degree_elimination_width(original_scopes, nvars)
        print(f"{nvars} {nclauses} source 3 {nclauses} 3 "
              f"{original_width} NA")
        for maxwidth in (1, 2, 3, 4, 5):
            start = perf_counter()
            sketch = geometry_aware_sparse_sketch(
                source, nvars, max_row_width=maxwidth)
            elapsed_ms = (perf_counter() - start) * 1000
            factors = scopes(source, sketch.rows)
            width = min_degree_elimination_width(factors, nvars)
            self_scope = max((len(factor) for factor in factors), default=0)
            print(f"{nvars} {nclauses} local {maxwidth} "
                  f"{len(sketch.rows)} {self_scope} {width} {elapsed_ms:.3f}")
        random_sketch = build_sparse_odd_sketch(source, nvars)
        random_factors = scopes(source, random_sketch.rows)
        random_width = min_degree_elimination_width(random_factors, nvars)
        print(f"{nvars} {nclauses} random 5 {len(random_sketch.rows)} "
              f"{max(map(len, random_factors), default=0)} {random_width} NA")
    print("No transformed SAT solving/counting was performed.")


if __name__ == "__main__":
    main()
