"""R-011 strict native Rust canonical CNF and subsumption adapter."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from witnora_core.cnf import CNFFormula, Clause


@dataclass(frozen=True)
class RustCanonicalCnf:
    clauses: tuple[tuple[int, ...], ...]
    canonical_dimacs: str
    variables: tuple[int, ...]
    is_2cnf: bool


def _native_clauses(raw_clauses: Iterable[Iterable[int]]) -> list[list[int]]:
    checked = []
    for clause in raw_clauses:
        items = list(clause)
        for lit in items:
            if type(lit) is not int or not -(1 << 31) < lit < (1 << 31) or lit == 0:
                raise ValueError("Rust canonical CNF requires nonzero signed 32-bit literals")
        checked.append(items)
    return checked


def canonicalize_cnf_in_rust(
    raw_clauses: Iterable[Iterable[int]],
) -> RustCanonicalCnf:
    from witnora_ve import canonical_cnf_native
    clauses, dimacs, variables, is_two = canonical_cnf_native(
        _native_clauses(raw_clauses))
    return RustCanonicalCnf(
        clauses=tuple(tuple(c) for c in clauses),
        canonical_dimacs=dimacs,
        variables=tuple(variables),
        is_2cnf=bool(is_two),
    )


def first_subsumption_in_rust(
    formula: CNFFormula,
) -> tuple[Clause, Clause] | None:
    from witnora_ve import first_subsumption_native
    got = first_subsumption_native(_native_clauses(
        formula.to_clause_lists()))
    if got is None:
        return None
    left, right = got
    return Clause(left), Clause(right)


def canonical_hash_in_rust(raw_clauses: Iterable[Iterable[int]]) -> str:
    """Return the Rust SHA-256 hash of Python-compatible canonical DIMACS bytes."""
    from witnora_ve import canonical_cnf_hash_native
    return canonical_cnf_hash_native(_native_clauses(raw_clauses))
