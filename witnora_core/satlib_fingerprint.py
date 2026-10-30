"""Read-only structural fingerprint for independently sourced DIMACS CNFs.

Descriptive metrics are not mathematical discoveries or correctness certificates.
"""
from __future__ import annotations

from collections import Counter

from .cnf import CNFFormula
from .incremental_separator import possible_two_xor_patterns
from .separator_conditioned_solve import primal_components
from .xor import detect_cnf_xor_patterns


def fingerprint(formula: CNFFormula) -> dict:
    sizes = Counter(len(clause) for clause in formula.clauses)
    occ = Counter(abs(lit) for clause in formula.clauses for lit in clause)
    pos = Counter(lit for clause in formula.clauses for lit in clause if lit > 0)
    neg = Counter(-lit for clause in formula.clauses for lit in clause if lit < 0)
    mixed = sum(bool(pos[var]) and bool(neg[var]) for var in formula.variables)
    # Only perform more expensive parity detection if its necessary screen passes.
    xor_count = len(detect_cnf_xor_patterns(formula).equations) if possible_two_xor_patterns(formula) else 0
    return {
        "source_sha256": formula.formula_hash,
        "variables": formula.num_vars,
        "clauses": formula.num_clauses,
        "max_clause_width": max(sizes, default=0),
        "unit_clauses": sizes[1],
        "binary_clauses": sizes[2],
        "ternary_clauses": sizes[3],
        "primal_components": len(primal_components(formula)),
        "max_variable_occurrences": max(occ.values(), default=0),
        "mixed_polarity_fraction": round(mixed / formula.num_vars, 6) if formula.num_vars else 0,
        "exact_xor_equations_detected": xor_count,
        "lean_verified": False,
        "novelty_verified": False,
        "promoted": False,
    }
