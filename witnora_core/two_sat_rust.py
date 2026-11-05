"""R-010 strict native 2-SAT SCC decision and witness bridge.

The Rust operation is a semantic solver, not a Lean/DRAT certificate emitter.
The Python proof-logging 2-SAT implementation remains the default.
"""
from __future__ import annotations

from witnora_core.cnf import CNFFormula, formula_satisfied


def solve_two_sat_in_rust(formula: CNFFormula) -> dict:
    """Exact SAT/UNSAT with a verified assignment on SAT; never fallback."""
    if not formula.is_2cnf:
        raise ValueError("formula is not 2-CNF")
    from witnora_ve import solve_two_sat_native
    witness = solve_two_sat_native(formula.to_clause_lists(), formula.max_var)
    if witness is None:
        return {
            "status": "UNSAT", "assignment": {},
            "details": {"status": "UNSAT", "backend": "rust_scc",
                        "proof_certificate": "not_emitted"},
        }
    assignment = {var: bool(witness[var - 1]) for var in formula.variables}
    if not formula_satisfied(formula, assignment):
        raise AssertionError("Rust 2-SAT witness failed independent CNF validation")
    return {
        "status": "SAT", "assignment": assignment,
        "details": {"status": "SAT", "backend": "rust_scc",
                    "proof_certificate": "not_emitted",
                    "assignment": {str(v): assignment[v] for v in sorted(assignment)}},
    }
