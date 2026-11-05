"""Read-only structural fingerprint for independently sourced DIMACS CNFs.

Descriptive metrics are not mathematical discoveries or correctness certificates.
"""
from __future__ import annotations

from collections import Counter

from .cnf import CNFFormula
from .incremental_separator import possible_two_xor_patterns
from .separator_conditioned_solve import primal_components
from .xor import detect_cnf_xor_patterns


def fingerprint(formula: CNFFormula, *, backend: str = "python") -> dict:
    if backend == "rust":
        from witnora_ve import satlib_structural_metrics_native
        (variables, clauses, max_width, units, binaries, ternaries,
         components, max_occurrences, mixed) = satlib_structural_metrics_native(
            formula.to_clause_lists())
    elif backend == "python":
        sizes = Counter(len(clause) for clause in formula.clauses)
        occ = Counter(abs(lit) for clause in formula.clauses for lit in clause)
        pos = Counter(lit for clause in formula.clauses for lit in clause if lit > 0)
        neg = Counter(-lit for clause in formula.clauses for lit in clause if lit < 0)
        variables, clauses = formula.num_vars, formula.num_clauses
        max_width, units, binaries, ternaries = (max(sizes, default=0),
                                                 sizes[1], sizes[2], sizes[3])
        components = len(primal_components(formula))
        max_occurrences = max(occ.values(), default=0)
        mixed = sum(bool(pos[var]) and bool(neg[var]) for var in formula.variables)
    else:
        raise ValueError("unknown fingerprint backend")
    # Only perform more expensive parity detection if its necessary screen passes.
    xor_count = len(detect_cnf_xor_patterns(formula).equations) if possible_two_xor_patterns(formula) else 0
    return {
        "source_sha256": formula.formula_hash,
        "variables": variables,
        "clauses": clauses,
        "max_clause_width": max_width,
        "unit_clauses": units,
        "binary_clauses": binaries,
        "ternary_clauses": ternaries,
        "primal_components": components,
        "max_variable_occurrences": max_occurrences,
        "mixed_polarity_fraction": round(mixed / variables, 6) if variables else 0,
        "exact_xor_equations_detected": xor_count,
        "lean_verified": False,
        "novelty_verified": False,
        "promoted": False,
    }
