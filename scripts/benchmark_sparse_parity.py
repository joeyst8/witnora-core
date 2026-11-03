"""Compare clause-row sparsity with *actual factor-graph connectivity*.

Elimination widths are min-degree heuristic UPPER bounds on treewidth,
not exact optimum or a proof of counting complexity. No tensor network
or transformed SAT solver is executed in this diagnostic.
"""
from __future__ import annotations

from time import perf_counter

from scripts.generate_glucose_dense_3sat_lean import random_three_cnf
from witnora_core.constraint_geometry import build_dense_random_sketch
from witnora_core.sparse_parity_checks import (
    audit_sparse_small, build_sparse_odd_sketch, low_weight_collisions,
    min_degree_elimination_width, source_row_scope,
)


def row_scopes(cnf: list[list[int]], rows: tuple[tuple[int, ...], ...]) -> list[set[int]]:
    return [{abs(lit) for j in row for lit in cnf[j]} for row in rows]


def main() -> None:
    print("n clauses sparse_rows sparse_max_width sparse_max_vars "
          "source_width sparse_width dense_width build_ms "
          "bad_survivors")
    for nvars, nclauses in ((8, 54), (12, 84), (32, 224),
                            (96, 576), (256, 1536)):
        source = random_three_cnf(nvars, nclauses, 630000 + nvars,
                                  planted=True)
        t0 = perf_counter()
        sparse = build_sparse_odd_sketch(source, nvars)
        build_ms = (perf_counter() - t0) * 1000
        dense = build_dense_random_sketch(source, nvars,
                                          security_bits=20, seed=73)
        cscopes = [set(abs(lit) for lit in row) for row in source]
        sparse_scopes = row_scopes(source, sparse.rows)
        dense_scopes = row_scopes(source, dense.rows)
        source_width = min_degree_elimination_width(cscopes, nvars)
        sparse_width = min_degree_elimination_width(sparse_scopes, nvars)
        dense_width = min_degree_elimination_width(dense_scopes, nvars)
        if nvars <= 12:
            assert low_weight_collisions(sparse) == 0
            collisions = str(audit_sparse_small(source, sparse).false_positives)
        else:
            collisions = "NOT_AUDITED"
        print(f"{nvars} {nclauses} {len(sparse.rows)} "
              f"{max((len(row) for row in sparse.rows), default=0)} "
              f"{max((len(scope) for scope in sparse_scopes), default=0)} "
              f"{source_width} {sparse_width} {dense_width} "
              f"{build_ms:.3f} {collisions}")
    print("Width = min-degree elimination heuristic, not exact treewidth.")
    print("Neither sparse nor dense encoding was actually solved/counted.")


if __name__ == "__main__":
    main()
