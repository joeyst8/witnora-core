"""Independent occurrence-aware clause-owner checker for TC-063.

Trust boundary: check a proposed partition directly against CNF clauses.
No DFS/primal-graph implementation is trusted to establish clause ownership.
The input clauses are *occurrences*, not a de-duplicated CNFFormula.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence


def _positive_int(value: Any) -> bool:
    return type(value) is int and value > 0


def verify_owner_partition(
    clauses: Sequence[Sequence[int]],
    separator_variables: Sequence[int],
    components: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Verify exact routing of every raw clause occurrence.

    A component specifies component_id, variables, clause_ids (1-based), and
    boundary_separator_variables. Separator-only and empty clauses are
    explicitly retained in a separate bucket. Connectivity/maximality of
    components is deliberately not required for logical soundness.
    """
    errors: list[str] = []
    all_variables: set[int] = set()
    for clause_id, clause in enumerate(clauses, 1):
        for literal in clause:
            if type(literal) is not int or literal == 0:
                errors.append(f"INVALID_LITERAL:{clause_id}")
            else:
                all_variables.add(abs(literal))

    separator = set(separator_variables)
    if any(not _positive_int(v) for v in separator_variables):
        errors.append("INVALID_SEPARATOR_VARIABLE")
    if len(separator) != len(separator_variables):
        errors.append("DUPLICATE_SEPARATOR_VARIABLE")
    if not separator.issubset(all_variables):
        errors.append("SEPARATOR_VARIABLE_NOT_IN_FORMULA")

    variable_owner: dict[int, str] = {}
    claimed_owner: dict[int, str] = {}
    component_ids: set[str] = set()
    claimed_boundaries: dict[str, set[int]] = {}
    for component in components:
        cid = component.get("component_id")
        if not isinstance(cid, str) or not cid or cid in component_ids:
            errors.append("INVALID_OR_DUPLICATE_COMPONENT_ID")
            continue
        component_ids.add(cid)
        variables = list(component.get("variables", []))
        clause_ids = list(component.get("clause_ids", []))
        boundary = list(component.get("boundary_separator_variables", []))
        if any(not _positive_int(v) for v in variables) or len(set(variables)) != len(variables):
            errors.append(f"INVALID_COMPONENT_VARIABLES:{cid}")
        for var in variables:
            if var in separator or var in variable_owner:
                errors.append(f"VARIABLE_OVERLAP:{cid}:{var}")
            else:
                variable_owner[var] = cid
        if any(not _positive_int(i) or i > len(clauses) for i in clause_ids):
            errors.append(f"INVALID_CLAUSE_ID:{cid}")
        if len(set(clause_ids)) != len(clause_ids):
            errors.append(f"DUPLICATE_CLAUSE_ID:{cid}")
        for clause_id in clause_ids:
            if clause_id in claimed_owner:
                errors.append(f"CLAUSE_ASSIGNED_TWICE:{clause_id}")
            else:
                claimed_owner[clause_id] = cid
        if any(not _positive_int(v) for v in boundary) or len(set(boundary)) != len(boundary):
            errors.append(f"INVALID_BOUNDARY:{cid}")
        claimed_boundaries[cid] = set(boundary)

    if set(variable_owner) != all_variables - separator:
        errors.append("NON_SEPARATOR_VARIABLE_COVERAGE_MISMATCH")

    expected_owner: dict[int, str] = {}
    separator_only: list[int] = []
    expected_boundaries: dict[str, set[int]] = {cid: set() for cid in component_ids}
    for clause_id, clause in enumerate(clauses, 1):
        variables = {abs(lit) for lit in clause if type(lit) is int and lit != 0}
        local = variables - separator
        if not local:
            separator_only.append(clause_id)
            continue
        owners = {variable_owner.get(var) for var in local}
        if len(owners) != 1 or None in owners:
            errors.append(f"CROSS_COMPONENT_OR_UNOWNED_CLAUSE:{clause_id}")
            continue
        owner = next(iter(owners))
        expected_owner[clause_id] = owner
        expected_boundaries[owner].update(variables & separator)

    if claimed_owner != expected_owner:
        errors.append("CLAUSE_OWNER_MISMATCH")
    for cid in component_ids:
        if claimed_boundaries[cid] != expected_boundaries[cid]:
            errors.append(f"COMPONENT_BOUNDARY_MISMATCH:{cid}")

    return {
        "accepted": not errors,
        "errors": errors,
        "owner_by_clause_id": {str(k): expected_owner[k] for k in sorted(expected_owner)},
        "separator_only_clause_ids": separator_only,
        "expected_component_boundaries": {
            cid: sorted(expected_boundaries[cid]) for cid in sorted(component_ids)
        },
    }


def condition_verified_partition(
    clauses: Sequence[Sequence[int]],
    separator_variables: Sequence[int],
    components: Sequence[Mapping[str, Any]],
    separator_assignment: Mapping[int, bool],
) -> dict[str, Any]:
    """Condition a verified partition without dropping clause occurrences."""
    audit = verify_owner_partition(clauses, separator_variables, components)
    if not audit["accepted"]:
        raise ValueError(f"invalid owner certificate: {audit['errors']}")
    if set(separator_assignment) != set(separator_variables) or any(
        type(value) is not bool for value in separator_assignment.values()
    ):
        raise ValueError("assignment must assign each separator variable exactly once")

    component_residuals: dict[str, list[list[int]]] = {
        str(component["component_id"]): [] for component in components
    }
    separator_residual: list[list[int]] = []
    for clause_id, clause in enumerate(clauses, 1):
        satisfied = False
        remaining: list[int] = []
        for literal in clause:
            var = abs(literal)
            if var not in separator_assignment:
                remaining.append(literal)
            elif (literal > 0) == separator_assignment[var]:
                satisfied = True
                break
        if satisfied:
            continue
        owner = audit["owner_by_clause_id"].get(str(clause_id))
        if owner is None:
            separator_residual.append(remaining)
        else:
            component_residuals[owner].append(remaining)
    return {
        "separator_residual": separator_residual,
        "component_residuals": component_residuals,
    }
