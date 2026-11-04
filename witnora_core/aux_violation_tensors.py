"""Auxiliary violation-variable factor bridge and exact constant-term check.

For source clauses C_j, introduce one Boolean v_j forced by a local factor
v_j = 1[C_j is false]. Sparse parity factors reference only the v_j's;
they never flatten back into unions of all source variables.

The polynomial Z_H(t) = sum_(source assignments x with H v(x)=0)
t^weight(v(x)) has coefficient [t^0] exactly #SAT(source), for ANY H.
A parity sketch alone may admit nonsolutions at positive degree.
Computing the coefficient via tensor contraction/interpolation is NOT
implemented here; the small verifier explicitly enumerates x.
"""
from __future__ import annotations

from dataclasses import dataclass

from witnora_core.constraint_geometry import canonical_source
from witnora_core.eth_clause_violation_parity import (
    CNF, parity_accepts, source_digest, violation_mask,
)
from witnora_core.sparse_parity_checks import (
    SparseOddSketch, validate_sparse_odd_sketch,
)


@dataclass(frozen=True)
class AuxBridgeProfile:
    nvars: int
    nclauses: int
    row_count: int
    coefficients: tuple[int, ...]

    @property
    def constant_coefficient(self) -> int:
        return self.coefficients[0]


def independent_violation_mask(cnf: CNF, assignment: int, *,
                               backend: str = "python") -> int:
    """Independent literal-level evaluator for bridge regression testing."""
    if backend == "rust":
        from witnora_ve import finite_parity_violation_mask_native
        return int(finite_parity_violation_mask_native(
            [list(row) for row in cnf], str(assignment)))
    if backend != "python":
        raise ValueError("unknown auxiliary bridge backend")
    mask = 0
    for j, clause in enumerate(cnf):
        satisfied = False
        for lit in clause:
            bit = bool(assignment & (1 << (abs(lit) - 1)))
            if bit == (lit > 0):
                satisfied = True
                break
        if not satisfied:
            mask |= 1 << j
    return mask


def auxiliary_factor_scopes(
    source: list[list[int]] | CNF, sketch: SparseOddSketch,
    *, backend: str = "python",
) -> list[set[int]]:
    """Scopes of local clause↔violation factors and parity-on-violation factors.

    Source variable IDs 1..n, auxiliary IDs n+1..n+m. The local factor
    computes each clause's violation bit; parity factors use only aux IDs.
    This does NOT include the optional unary zero selectors v_j = 0.
    """
    cnf = validate_sparse_odd_sketch(source, sketch)
    if backend == "rust":
        from witnora_ve import aux_local_scopes_native
        return [set(scope) for scope in aux_local_scopes_native(
            [list(row) for row in cnf], sketch.nvars,
            [list(row) for row in sketch.rows])]
    if backend != "python":
        raise ValueError("unknown auxiliary bridge backend")
    n = sketch.nvars
    local = [{abs(lit) for lit in clause} | {n + j + 1}
             for j, clause in enumerate(cnf)]
    parity = [{n + j + 1 for j in row} for row in sketch.rows]
    return local + parity


def direct_parity_factor_scopes(
    source: list[list[int]] | CNF, sketch: SparseOddSketch,
    *, backend: str = "python",
) -> list[set[int]]:
    cnf = validate_sparse_odd_sketch(source, sketch)
    if backend == "rust":
        from witnora_ve import aux_direct_scopes_native
        return [set(scope) for scope in aux_direct_scopes_native(
            [list(row) for row in cnf], [list(row) for row in sketch.rows])]
    if backend != "python":
        raise ValueError("unknown auxiliary bridge backend")
    return [{abs(lit) for j in row for lit in cnf[j]}
            for row in sketch.rows]


def exact_source_models_small(
    source: list[list[int]] | CNF, nvars: int, *,
    max_variables: int = 14, backend: str = "python",
) -> int:
    """Exponential oracle confined to small independent test cases."""
    cnf = canonical_source(source, nvars)
    if nvars > max_variables:
        raise ValueError("exhaustive model oracle restricted to small instances")
    if backend == "rust":
        from witnora_ve import aux_exact_models_native
        return aux_exact_models_native([list(row) for row in cnf], nvars, max_variables)
    if backend != "python":
        raise ValueError("unknown auxiliary bridge backend")
    return sum(independent_violation_mask(cnf, x) == 0
               for x in range(1 << nvars))


def auxiliary_weight_profile_small(
    source: list[list[int]] | CNF,
    sketch: SparseOddSketch, *,
    max_variables: int = 14, backend: str = "python",
) -> AuxBridgeProfile:
    """Enumerate Z_H(t) coefficients for TESTING only, not construction."""
    cnf = validate_sparse_odd_sketch(source, sketch)
    n = sketch.nvars
    if n > max_variables:
        raise ValueError("exhaustive auxiliary bridge restricted to small instances")
    if backend == "rust":
        from witnora_ve import aux_weight_profile_native
        coefficients = aux_weight_profile_native(
            [list(row) for row in cnf], n, [list(row) for row in sketch.rows],
            max_variables)
        return AuxBridgeProfile(n, len(cnf), len(sketch.rows), tuple(coefficients))
    if backend != "python":
        raise ValueError("unknown auxiliary bridge backend")
    coefficients = [0] * (len(cnf) + 1)
    for x in range(1 << n):
        v = independent_violation_mask(cnf, x)
        if parity_accepts(v, sketch.rows):
            coefficients[v.bit_count()] += 1
    return AuxBridgeProfile(n, len(cnf), len(sketch.rows),
                            tuple(coefficients))


def constant_term_matches_source(
    source: list[list[int]] | CNF, sketch: SparseOddSketch,
    *, backend: str = "python",
) -> bool:
    """Finite control for the universal (and algebraically trivial) identity."""
    p = auxiliary_weight_profile_small(source, sketch, backend=backend)
    return p.constant_coefficient == exact_source_models_small(
        source, sketch.nvars, backend=backend)
