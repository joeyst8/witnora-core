"""Sparse odd-column parity checks with a non-enumerative 1/2/3-error guarantee.

Treat each source clause as a *column* in an r x m Boolean test matrix.
Every column has exactly three 1s, and distinct clauses have distinct
column signatures. No assignment enumeration is needed to construct or
validate these properties.

For a violation support S of size 1: its nonempty column is detected.
For size 2: distinct columns have nonzero XOR.
For size 3: XOR of three odd-weight columns has odd parity, so is nonzero.
Thus *every* violation vector of Hamming weight 1, 2 or 3 is rejected.
Larger supports may collide; no universal CNF equivalence or fast
counting claim is made. Row width is capped at max_row_width.
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from math import comb
from random import Random

from witnora_core.constraint_geometry import canonical_source
from witnora_core.eth_clause_violation_parity import (
    CNF, parity_accepts, source_digest, violation_mask,
)


@dataclass(frozen=True)
class SparseOddSketch:
    nvars: int
    clause_count: int
    digest: str
    max_row_width: int
    rows: tuple[tuple[int, ...], ...]


@dataclass(frozen=True)
class SparseAudit:
    source_models: int
    nonmodels: int
    false_positives: int
    max_scope_variables: int
    mean_scope_variables: float


def column_signatures(rows: tuple[tuple[int, ...], ...],
                      nclauses: int) -> tuple[int, ...]:
    result = [0] * nclauses
    for rid, row in enumerate(rows):
        for j in row:
            result[j] |= 1 << rid
    return tuple(result)


def build_sparse_odd_sketch(source: list[list[int]] | CNF, nvars: int,
                            *, max_row_width: int = 5, seed: int = 73,
                            max_attempts: int = 100) -> SparseOddSketch:
    """Generate degree-three DISTINCT odd columns with bounded row load.

    Does not inspect assignments or source models. May fail closed if
    randomized load balancing cannot realize this matrix within attempts.
    """
    cnf = canonical_source(source, nvars)
    if max_row_width < 1 or max_attempts < 1:
        raise ValueError("row width and attempt count must be positive")
    m = len(cnf)
    if m == 0:
        return SparseOddSketch(nvars, 0, source_digest(cnf), max_row_width, ())
    degree = 3
    r = max(degree, (degree * m + max_row_width - 1) // max_row_width + degree)
    while comb(r, degree) < m:
        r += 1
    rng = Random(seed)
    for _ in range(max_attempts):
        loads = [0] * r
        cols: list[tuple[int, ...]] = []
        used: set[tuple[int, ...]] = set()
        success = True
        for _col in range(m):
            # Choose from the least-loaded available rows, breaking ties
            # randomly. Repeated signatures are forbidden.
            choices = [j for j in range(r) if loads[j] < max_row_width]
            if len(choices) < degree:
                success = False
                break
            winner = None
            for _ in range(50):
                jitter = {j: rng.random() for j in choices}
                proposal = tuple(sorted(
                    sorted(choices, key=lambda j: (loads[j], jitter[j]))[:degree]))
                if proposal not in used:
                    winner = proposal
                    break
            if winner is None:
                success = False
                break
            used.add(winner)
            cols.append(winner)
            for j in winner:
                loads[j] += 1
        if success:
            row_sets = [set() for _ in range(r)]
            for col, selected_rows in enumerate(cols):
                for rid in selected_rows:
                    row_sets[rid].add(col)
            rows = tuple(tuple(sorted(row)) for row in row_sets)
            sketch = SparseOddSketch(nvars, m, source_digest(cnf),
                                     max_row_width, rows)
            validate_sparse_odd_sketch(cnf, sketch)
            return sketch
    raise RuntimeError("could not construct bounded-degree odd-column matrix")


def validate_sparse_odd_sketch(source: list[list[int]] | CNF,
                               sketch: SparseOddSketch) -> CNF:
    """Structural guarantee, not SAT source-equivalence certification."""
    cnf = canonical_source(source, sketch.nvars)
    if len(cnf) != sketch.clause_count or source_digest(cnf) != sketch.digest:
        raise ValueError("source identity mismatch")
    if sketch.max_row_width < 1:
        raise ValueError("invalid row-width bound")
    for row in sketch.rows:
        if len(row) > sketch.max_row_width:
            raise ValueError("row exceeds declared width")
        if tuple(sorted(set(row))) != row or any(j < 0 or j >= len(cnf)
                                                 for j in row):
            raise ValueError("invalid sparse row")
    signatures = column_signatures(sketch.rows, len(cnf))
    if any(sig.bit_count() != 3 for sig in signatures):
        raise ValueError("column degree is not three")
    if len(set(signatures)) != len(signatures):
        raise ValueError("columns have duplicate signatures")
    return cnf


def low_weight_collisions(sketch: SparseOddSketch,
                          *, max_weight: int = 3) -> int:
    """Independent exhaustive SUPPORT audit, not SAT assignment enumeration."""
    signatures = column_signatures(sketch.rows, sketch.clause_count)
    collisions = 0
    for weight in range(1, max_weight + 1):
        for support in combinations(range(sketch.clause_count), weight):
            odd_row_mask = 0
            for j in support:
                odd_row_mask ^= signatures[j]
            collisions += (odd_row_mask == 0)
    return collisions


def source_row_scope(source: CNF, row: tuple[int, ...]) -> int:
    return len({abs(lit) for j in row for lit in source[j]})


def audit_sparse_small(source: list[list[int]] | CNF,
                       sketch: SparseOddSketch, *,
                       max_variables: int = 14) -> SparseAudit:
    """EXPONENTIAL independent finite audit, never used by constructor."""
    cnf = validate_sparse_odd_sketch(source, sketch)
    if sketch.nvars > max_variables:
        raise ValueError("small-only assignment audit")
    models = false_positives = 0
    for assignment in range(1 << sketch.nvars):
        violated = violation_mask(cnf, assignment)
        if violated == 0:
            models += 1
        elif parity_accepts(violated, sketch.rows):
            false_positives += 1
    scopes = [source_row_scope(cnf, row) for row in sketch.rows]
    return SparseAudit(models, (1 << sketch.nvars) - models,
                       false_positives, max(scopes, default=0),
                       sum(scopes)/len(scopes) if scopes else 0.0)


def min_degree_elimination_width(scopes: list[set[int]],
                                 nvars: int) -> int:
    """Heuristic induced width of a factor graph (NOT exact treewidth).

    Builds the primal graph from each factor scope and eliminates a
    minimum-degree vertex, filling its neighbors into a clique.
    The maximum live-neighbor count is an explicit elimination width,
    hence an upper bound on treewidth, not a lower bound.
    """
    if nvars < 0:
        raise ValueError("nvars must be nonnegative")
    graph: dict[int, set[int]] = {v: set() for v in range(1, nvars + 1)}
    for scope in scopes:
        if any(v < 1 or v > nvars for v in scope):
            raise ValueError("factor variable out of range")
        for v in scope:
            graph[v].update(scope - {v})
    active = set(graph)
    maximum = 0
    while active:
        v = min(active, key=lambda j: (len(graph[j] & active), j))
        neighbors = graph[v] & active
        maximum = max(maximum, len(neighbors))
        for u in neighbors:
            graph[u].update(neighbors - {u})
            graph[u].discard(v)
        active.remove(v)
    return maximum


def column_signatures_rust(
    rows: tuple[tuple[int, ...], ...], nclauses: int,
) -> tuple[int, ...]:
    """R-056 opt-in native arbitrary-precision odd-column bit signatures."""
    from witnora_ve import sparse_column_signatures_native

    return tuple(int(x) for x in sparse_column_signatures_native(
        [list(row) for row in rows], nclauses
    ))


def validate_sparse_odd_sketch_rust(
    source: list[list[int]] | CNF,
    sketch: SparseOddSketch,
) -> CNF:
    """Source identity in Python; independent native structural validation."""
    from witnora_ve import sparse_validate_rows_native

    cnf = canonical_source(source, sketch.nvars)
    if len(cnf) != sketch.clause_count or source_digest(cnf) != sketch.digest:
        raise ValueError("source identity mismatch")
    sparse_validate_rows_native(
        sketch.clause_count, sketch.max_row_width,
        [list(row) for row in sketch.rows],
    )
    return cnf


def build_sparse_odd_sketch_rust(
    source: list[list[int]] | CNF, nvars: int,
    *, max_row_width: int = 5, seed: int = 73,
    max_attempts: int = 100,
) -> SparseOddSketch:
    """R-056 native bounded-load placement with Python's identical seed RNG."""
    from witnora_ve import sparse_build_rows_native

    cnf = canonical_source(source, nvars)
    if max_row_width < 1 or max_attempts < 1:
        raise ValueError("row width and attempt count must be positive")
    rows = sparse_build_rows_native(
        len(cnf), max_row_width, max_attempts, Random(seed)
    )
    sketch = SparseOddSketch(
        nvars, len(cnf), source_digest(cnf), max_row_width,
        tuple(tuple(row) for row in rows),
    )
    validate_sparse_odd_sketch_rust(cnf, sketch)
    return sketch


def low_weight_collisions_rust(
    sketch: SparseOddSketch, *, max_weight: int = 3,
) -> int:
    from witnora_ve import sparse_low_weight_collisions_native

    return sparse_low_weight_collisions_native(
        [list(row) for row in sketch.rows], sketch.clause_count, max_weight
    )


def source_row_scope_rust(source: CNF, row: tuple[int, ...]) -> int:
    from witnora_ve import sparse_row_scope_native

    return sparse_row_scope_native([list(c) for c in source], list(row))


def audit_sparse_small_rust(
    source: list[list[int]] | CNF,
    sketch: SparseOddSketch, *, max_variables: int = 14,
) -> SparseAudit:
    """Native independent finite audit, with a 20-variable safety bound."""
    from witnora_ve import sparse_audit_small_native

    cnf = validate_sparse_odd_sketch_rust(source, sketch)
    models, nonmodels, false_positives, max_scope, mean_scope = (
        sparse_audit_small_native(
            [list(clause) for clause in cnf], sketch.nvars,
            [list(row) for row in sketch.rows], max_variables
        )
    )
    return SparseAudit(
        models, nonmodels, false_positives, max_scope, mean_scope
    )


def min_degree_elimination_width_rust(
    scopes: list[set[int]], nvars: int,
) -> int:
    """Opt-in exact native reproduction of the min-degree induced width."""
    from witnora_ve import sparse_min_degree_width_native

    return sparse_min_degree_width_native(
        [sorted(scope) for scope in scopes], nvars
    )
