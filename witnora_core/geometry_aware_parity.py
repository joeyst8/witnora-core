"""Geometry-aware sparse parity rows for exact-width-three CNFs.

Each source clause has exactly three distinct variables. For each variable,
partition its incident clauses into capacity-w buckets and make each bucket
a parity row. Thus every clause participates in exactly three rows and
each row touches at most w clauses sharing one source variable.
Duplicated column signatures are repaired with dedicated incidence rows.

The resulting signatures remain distinct and odd-weight, giving the same
1/2/3-violation support guarantee as SparseOddSketch. Grouping is guided by
additional fill edges over the ORIGINAL source variable graph. This is a
construction/geometry experiment, not a guaranteed treewidth optimizer,
not general CNF equivalence, and not a fast SAT solver.
"""
from __future__ import annotations

from itertools import combinations

from witnora_core.constraint_geometry import canonical_source
from witnora_core.sparse_parity_checks import (
    SparseOddSketch, validate_sparse_odd_sketch,
)
from witnora_core.eth_clause_violation_parity import CNF, source_digest


def source_primal_pairs(cnf: CNF) -> set[tuple[int, int]]:
    return {tuple(sorted((abs(a), abs(b))))
            for clause in cnf for a, b in combinations(clause, 2)}


def geometry_aware_sparse_sketch(
    source: list[list[int]] | CNF, nvars: int, *,
    max_row_width: int = 5,
) -> SparseOddSketch:
    """Deterministic incidence-bucket construction; NO SAT enumeration."""
    cnf = canonical_source(source, nvars)
    if max_row_width < 1:
        raise ValueError("max_row_width must be positive")
    if any(len(c) != 3 or len({abs(lit) for lit in c}) != 3
           for c in cnf):
        raise ValueError("geometry-aware prototype supports distinct 3-CNF only")
    m = len(cnf)
    incident: dict[int, list[int]] = {v: [] for v in range(1, nvars + 1)}
    scopes = [frozenset(abs(lit) for lit in clause) for clause in cnf]
    for j, vars_ in enumerate(scopes):
        for v in vars_:
            incident[v].append(j)
    original_pairs = source_primal_pairs(cnf)

    def fill_count(scope: set[int]) -> int:
        return sum(tuple(sorted((a, b))) not in original_pairs
                   for a, b in combinations(sorted(scope), 2))

    rows: list[set[int]] = []
    selected_rows: list[set[int]] = [set() for _ in range(m)]
    for v in range(1, nvars + 1):
        buckets: list[set[int]] = []
        bucket_scopes: list[set[int]] = []
        # Similar neighboring variable pairs are processed together.
        ordered = sorted(incident[v],
                         key=lambda j: tuple(sorted(scopes[j] - {v})))
        for j in ordered:
            available = [i for i, bucket in enumerate(buckets)
                         if len(bucket) < max_row_width]
            if not available:
                buckets.append(set())
                bucket_scopes.append({v})
                chosen = len(buckets) - 1
            else:
                chosen = min(
                    available,
                    key=lambda i: (
                        fill_count(bucket_scopes[i] | scopes[j])
                        - fill_count(bucket_scopes[i]),
                        len((bucket_scopes[i] | scopes[j]) - bucket_scopes[i]),
                        -len(buckets[i]), i,
                    ),
                )
            buckets[chosen].add(j)
            bucket_scopes[chosen].update(scopes[j])
        for bucket in buckets:
            row_id = len(rows)
            rows.append(set(bucket))
            for j in bucket:
                selected_rows[j].add(row_id)

    # Any duplicate signature must involve clauses that share all three
    # source variables. Split an incidence to guarantee distinct columns.
    used: set[tuple[int, ...]] = set()
    for j in range(m):
        signature = tuple(sorted(selected_rows[j]))
        if signature in used:
            old_id = max(selected_rows[j], key=lambda i: (len(rows[i]), -i))
            rows[old_id].remove(j)
            selected_rows[j].remove(old_id)
            new_id = len(rows)
            rows.append({j})
            selected_rows[j].add(new_id)
        used.add(tuple(sorted(selected_rows[j])))

    # Remove empty rows while retaining deterministic row order.
    compact = tuple(tuple(sorted(row)) for row in rows if row)
    sketch = SparseOddSketch(nvars=nvars, clause_count=m,
                             digest=source_digest(cnf),
                             max_row_width=max_row_width, rows=compact)
    validate_sparse_odd_sketch(cnf, sketch)
    return sketch
