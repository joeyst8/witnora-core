"""Blocked Clause Elimination."""

from __future__ import annotations

from hashlib import sha256
from typing import Any

from .cnf import CNFFormula, Clause, has_tautology, literal_sort_key


def _resolvent_literals_for_log(clause: Clause, other: Clause, pivot: int) -> list[int]:
    return sorted([lit for lit in clause if lit != pivot] + [lit for lit in other if lit != -pivot])


def _native_checked_proof(pivot: int, rows: list[tuple[list[int], list[int], bool]]) -> dict[str, Any]:
    checked = [
        {"against_clause": other, "resolvent": resolvent,
         "tautological": tautological}
        for other, resolvent, tautological in rows
    ]
    from witnora_ve import blocked_clause_digest_native
    return {
        "blocked_literal": pivot, "checked_resolvents": checked,
        "proof_digest": blocked_clause_digest_native(rows),
    }


def blocked_clause_proof(formula: CNFFormula, clause: Clause, pivot: int, *,
                         backend: str = "python") -> dict[str, Any] | None:
    """Return a proof dict if the clause is blocked on pivot."""
    if backend == "rust":
        from witnora_ve import blocked_clause_witness_native
        result = blocked_clause_witness_native(
            formula.to_clause_lists(), clause.to_list(), pivot)
        return None if result is None else _native_checked_proof(*result)
    if backend != "python":
        raise ValueError("unknown BCE witness backend")

    checked: list[dict[str, Any]] = []
    for other in formula.clauses:
        if other == clause:
            continue
        if -pivot not in other:
            continue
        resolvent_lits = _resolvent_literals_for_log(clause, other, pivot)
        tautological = has_tautology(resolvent_lits)
        checked.append(
            {
                "against_clause": other.to_list(),
                "resolvent": resolvent_lits,
                "tautological": tautological,
            }
        )
        if not tautological:
            return None

    digest_payload = repr(
        [
            (item["against_clause"], item["resolvent"], item["tautological"])
            for item in checked
        ]
    ).encode("utf-8")
    return {
        "blocked_literal": pivot,
        "checked_resolvents": checked,
        "proof_digest": sha256(digest_payload).hexdigest(),
    }


def find_first_blocked_clause(formula: CNFFormula, *,
                              backend: str = "python") -> tuple[Clause, dict[str, Any]] | None:
    """Find the first BCE-removable clause in the mandated deterministic order."""
    if backend == "rust":
        from witnora_ve import first_blocked_clause_native
        result = first_blocked_clause_native(formula.to_clause_lists())
        if result is None:
            return None
        clause, pivot, rows = result
        return Clause(clause), _native_checked_proof(pivot, rows)
    if backend != "python":
        raise ValueError("unknown BCE search backend")

    ordered_clauses = sorted(formula.clauses, key=lambda c: (-len(c), c.literals))
    for clause in ordered_clauses:
        for lit in sorted(clause.literals, key=literal_sort_key):
            proof = blocked_clause_proof(formula, clause, lit)
            if proof is not None:
                return clause, proof
    return None
