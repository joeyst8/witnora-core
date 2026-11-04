"""Incidence-graph component decomposition."""

from __future__ import annotations

from collections import defaultdict, deque
from typing import Any

from .cnf import CNFFormula, Clause


def connected_components(formula: CNFFormula, *, backend: str = "python") -> list[CNFFormula]:
    if backend == "rust":
        from witnora_ve import incidence_components_native
        components = incidence_components_native(formula.to_clause_lists())
        return [CNFFormula.from_raw_clauses(rows) for rows in components]
    if backend != "python":
        raise ValueError("unknown component backend")
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


def component_details(formula: CNFFormula, *, backend: str = "python") -> dict[str, Any]:
    if backend == "rust_details":
        from witnora_ve import component_evidence_native
        count, edges, records = component_evidence_native(formula.to_clause_lists())
        return {
            "component_count": count,
            "incidence_edges": [[var, idx] for var, idx in edges],
            "components": [
                {
                    "component_id": cid, "formula_hash": digest,
                    "variables": variables, "clauses": clauses,
                    "clause_indices": clause_indices,
                }
                for cid, digest, variables, clauses, clause_indices in records
            ],
        }
    comps = connected_components(formula, backend=backend)
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


def verify_component_evidence_in_rust(
    formula: CNFFormula, evidence: dict[str, Any], output_hash: str,
) -> str | None:
    """Independent native verification of full CD step metadata.

    Returns the same first-error message as Python's _verify_cd_step for
    well-formed CD evidence; None indicates valid metadata.
    """
    from witnora_ve import verify_component_evidence_native

    return verify_component_evidence_native(
        formula.to_clause_lists(),
        output_hash,
        int(evidence.get("component_count", 0)),
        [tuple(int(v) for v in item)
         for item in evidence.get("incidence_edges", [])],
        [
            (
                int(component["component_id"]),
                str(component["formula_hash"]),
                [int(v) for v in component.get("variables", [])],
                [[int(v) for v in clause]
                 for clause in component.get("clauses", [])],
                [int(v) for v in component.get("clause_indices", [])],
            )
            for component in evidence.get("components", [])
        ],
    )
