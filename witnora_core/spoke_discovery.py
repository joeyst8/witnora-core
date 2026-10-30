"""Conservative structural invariant discovery in unrestricted CNF.

Find only *complete* two-variable canonical XOR-CNF patterns. Every detected
equation is implied by the original formula (even if unrelated clauses remain).
Pairing equations across middle variables may reveal conflicting endpoint
parities. Discovery never awards formal UNSAT status; a certificate checker
must independently establish the original-CNF deduction.
"""
from __future__ import annotations

from collections import defaultdict
from itertools import combinations
from typing import Any

from .cnf import CNFFormula
from .xor import canonical_xor_cnf_clauses


def extract_binary_xor_equations(formula: CNFFormula) -> list[tuple[int, int, int]]:
    """Deterministic exact width-two XOR extraction, with u < v.

    The candidate pair scan is an optimization; Lean independently enumerates
    all u/v/rhs possibilities and checks the full pattern for each.
    """
    clauses = {tuple(clause) for clause in formula.to_clause_lists()}
    pairs = {
        tuple(sorted((abs(clause[0]), abs(clause[1]))))
        for clause in clauses
        if len(clause) == 2 and abs(clause[0]) != abs(clause[1])
    }
    return [
        (u, v, rhs)
        for u, v in sorted(pairs)
        for rhs in (0, 1)
        if canonical_xor_cnf_clauses((u, v), rhs).issubset(clauses)
    ]


def discover_parity_spoke_conflicts(formula: CNFFormula) -> list[dict[str, Any]]:
    """Return candidate contradictions with exact source-clause witnesses.

    The routine checks both forbidden assignment clauses for each binary
    equation, and never infers an XOR from a single suggestive CNF clause.
    """
    edges: dict[int, list[tuple[int, int, tuple[tuple[int, ...], ...]]]] = defaultdict(list)
    for u, v, rhs in extract_binary_xor_equations(formula):
        witness = tuple(sorted(canonical_xor_cnf_clauses((u, v), rhs)))
        edges[u].append((v, rhs, witness))
        edges[v].append((u, rhs, witness))

    by_endpoints: dict[tuple[int, int], list[dict[str, Any]]] = defaultdict(list)
    for middle in sorted(edges):
        for (x, l, source_left), (z, r, source_right) in combinations(edges[middle], 2):
            if x == z:
                continue
            a, b = sorted((x, z))
            by_endpoints[(a, b)].append({
                "middle": middle,
                "syndrome": l ^ r,
                "equations": [
                    {"variables": sorted((x, middle)), "rhs": l,
                     "source_clauses": [list(c) for c in source_left]},
                    {"variables": sorted((middle, z)), "rhs": r,
                     "source_clauses": [list(c) for c in source_right]},
                ],
            })
    conflicts = []
    for endpoints, paths in sorted(by_endpoints.items()):
        for first, second in combinations(paths, 2):
            if first["middle"] == second["middle"]:
                continue
            if first["syndrome"] == second["syndrome"]:
                continue
            conflicts.append({
                "status": "UNVERIFIED_STRUCTURAL_CANDIDATE",
                "operator": "PARITY_SPOKE_SYNDROME",
                "endpoints": list(endpoints),
                "paths": [first, second],
                "reason": "incompatible implied endpoint parities",
                "formal_status": "NOT_LEAN_VERIFIED",
            })
    return conflicts
