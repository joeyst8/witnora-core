"""W-CRC-014: exact fail-closed factor-table variable elimination.

This is ordinary sum-product variable elimination for a small-width
CNF primal component. It is exponential in intermediate factor width,
not a general polynomial-time #SAT algorithm. Every table construction
and join is charged to explicit operation and factor-width limits.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from witnora_core.crc_boundary import _mask


@dataclass(frozen=True)
class VariableEliminationCount:
    models: int
    operations: int
    max_factor_variables: int
    eliminated_variables: int


@dataclass(frozen=True)
class _Factor:
    scope: tuple[int, ...]
    table: tuple[int, ...]


def count_component_by_elimination(
    violation_clauses: Iterable[tuple[int, int]],
    component_variables: tuple[int, ...],
    *,
    max_factor_variables: int = 6,
    max_operations: int = 1000000,
    backend: str = "python",
) -> VariableEliminationCount | None:
    """Count a signed CNF component exactly with bounded min-scope VE.

    Clauses are source-relative (must_be_zero, must_be_one) masks
    describing their unique violating assignments, as supplied by
    crc_boundary._normalized_clauses. None means resource exhaustion.
    """
    if (not isinstance(max_factor_variables, int) or
        not 1 <= max_factor_variables <= 16 or
        not isinstance(max_operations, int) or max_operations < 1):
        raise ValueError("invalid VE width or operation budget")
    if len(component_variables) != len(set(component_variables)):
        raise ValueError("duplicate component variable")
    allowed = _mask(component_variables)
    clauses = tuple(violation_clauses)
    if backend == "rust":
        from witnora_ve import crc_variable_eliminate_native
        native = crc_variable_eliminate_native(
            [(str(zeros), str(ones)) for zeros, ones in clauses],
            list(component_variables), max_factor_variables, max_operations)
        if native is None:
            return None
        models, operations, maximum_width, eliminated = native
        return VariableEliminationCount(int(models), operations, maximum_width, eliminated)
    if backend != "python":
        raise ValueError("unknown variable elimination backend")
    factors = []
    operations = 0
    maximum_width = 0
    for zeros, ones in clauses:
        if (not isinstance(zeros, int) or not isinstance(ones, int)
            or zeros < 0 or ones < 0 or (zeros & ones)
            or (zeros | ones) & ~allowed):
            raise ValueError("invalid violation masks")
        if not (zeros | ones):
            return VariableEliminationCount(0, operations, maximum_width, 0)
        scope = tuple(v for v in component_variables
                      if (zeros | ones) & (1 << (v - 1)))
        width = len(scope)
        if width > max_factor_variables:
            return None
        maximum_width = max(maximum_width, width)
        size = 1 << width
        if size > max_operations - operations:
            return None
        operations += size
        table = []
        for packed in range(size):
            assignment = 0
            for i, v in enumerate(scope):
                if packed & (1 << i):
                    assignment |= 1 << (v - 1)
            violated = (assignment & zeros) == 0 and (
                assignment & ones) == ones
            table.append(0 if violated else 1)
        factors.append(_Factor(scope, tuple(table)))

    active = set(component_variables)
    for _ in range(len(component_variables)):
        # Min-resulting-factor-scope heuristic; deterministic tie break.
        choices = []
        for v in sorted(active):
            touched = [f for f in factors if v in f.scope]
            scope = set().union(*(f.scope for f in touched)) if touched else {v}
            choices.append((len(scope), len(touched), v, touched, tuple(sorted(scope))))
        width, _, variable, touched, total_scope = min(
            choices, key=lambda row: (row[0], row[1], row[2]))
        if width > max_factor_variables:
            return None
        maximum_width = max(maximum_width, width)
        context = tuple(v for v in total_scope if v != variable)
        work = (1 << len(context)) * 2 * max(1, len(touched))
        if work > max_operations - operations:
            return None
        operations += work
        table = []
        for packed in range(1 << len(context)):
            vals = {v: bool(packed & (1 << i))
                    for i, v in enumerate(context)}
            summation = 0
            for x in (False, True):
                vals[variable] = x
                product = 1
                for f in touched:
                    key = sum(1 << i for i, v in enumerate(f.scope)
                              if vals[v])
                    product *= f.table[key]
                    if not product:
                        break
                summation += product
            table.append(summation)
        ids = {id(f) for f in touched}
        factors = [f for f in factors if id(f) not in ids]
        factors.append(_Factor(context, tuple(table)))
        active.remove(variable)

    result = 1
    for factor in factors:
        if factor.scope:
            raise AssertionError("VE left uneliminated factor variables")
        result *= factor.table[0]
    return VariableEliminationCount(
        result, operations, maximum_width, len(component_variables))
