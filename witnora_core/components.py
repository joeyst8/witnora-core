"""Incidence-graph component decomposition."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from .cnf import CNFFormula, Clause


def connected_components(formula: CNFFormula) -> list[CNFFormula]:
    if not formula.clauses:
        return []

    var_to_clauses: dict[int, list[int]] = defaultdict(list)
    for idx, clause in enumerate(formula.clauses):
        for var in clause.variables:
            var_to_clauses[var].append(idx)

    seen_clauses: set[int] = set()
    components: list[list[Clause]] = []

    for start in range(len(formula.clauses)):
        if start in seen_clauses:
            continue
        queue: deque[tuple[str, int]] = deque([("c", start)])
        component_clause_ids: set[int] = set()
        seen_vars: set[int] = set()
        while queue:
            kind, node = queue.popleft()
            if kind == "c":
                if node in seen_clauses:
                    continue
                seen_clauses.add(node)
                component_clause_ids.add(node)
                for var in formula.clauses[node].variables:
                    if var not in seen_vars:
                        queue.append(("v", var))
            else:
                if node in seen_vars:
                    continue
                seen_vars.add(node)
                for clause_idx in var_to_clauses[node]:
                    if clause_idx not in seen_clauses:
                        queue.append(("c", clause_idx))
        components.append([formula.clauses[idx] for idx in sorted(component_clause_ids)])

    return [CNFFormula(component) for component in components]


def component_details(formula: CNFFormula) -> dict[str, Any]:
    comps = connected_components(formula)
    clause_to_index = {clause.literals: idx for idx, clause in enumerate(formula.clauses)}
    return {
        "component_count": len(comps),
        "incidence_edges": [
            [var, clause_idx]
            for clause_idx, clause in enumerate(formula.clauses)
            for var in clause.variables
        ],
        "components": [
            {
                "component_id": idx,
                "formula_hash": component.formula_hash,
                "variables": list(component.variables),
                "clauses": component.to_clause_lists(),
                "clause_indices": [
                    clause_to_index[clause.literals] for clause in component.clauses
                ],
            }
            for idx, component in enumerate(comps)
        ],
    }
