"""Opt-in verified parity-compression preprocessing for a SAT backend.

Lean verifies the input-to-residual equivalence before the backend may use
the compressed formula. A SAT model is independently lifted and checked.
A bare solver UNSAT verdict is *not* a Lean proof of UNSAT; for that result
the caller still needs a G5/G14 or another accepted UNSAT certificate.
The baseline/fallback always solves the unmodified original CNF.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from time import perf_counter
from typing import Any

from .cnf import CNFFormula, formula_satisfied
from .lean_parity_compression_gate import verify_parity_compression_with_lean
from .parity_compression import (
    compress_binary_xor_components, reconstruct_values,
    substitute_residual_formula,
)


def _glucose(formula: CNFFormula) -> dict[str, Any]:
    from pysat.solvers import Glucose3
    with Glucose3(bootstrap_with=formula.to_clause_lists()) as solver:
        if not solver.solve():
            return {"status": "UNSAT_SOLVER_REPORTED", "assignment": {}}
        true_literals = solver.get_model() or []
        model = {abs(lit): lit > 0 for lit in true_literals}
    assignment = {v: model.get(v, False) for v in formula.variables}
    if not formula_satisfied(formula, assignment):
        raise ValueError("SAT backend returned an invalid model")
    return {"status": "SAT_MODEL_CHECKED", "assignment": assignment}


def solve_with_verified_compression(
    formula: CNFFormula,
    *,
    raw_clauses: object,
    source_tokens: object,
    source_spellings: object,
    source_text: object,
    timeout_seconds: int = 120,
    project_root: Path | None = None,
) -> dict[str, Any]:
    start = perf_counter()
    gate = verify_parity_compression_with_lean(
        formula, raw_clauses=raw_clauses,
        source_tokens=source_tokens, source_spellings=source_spellings,
        source_text=source_text, timeout_seconds=timeout_seconds,
        project_root=project_root,
    )
    gate_seconds = perf_counter() - start
    if gate.get("verified") is not True or gate.get("lean_formal_status") != "LEAN_SOURCE_PARITY_RESIDUAL_EQUIVALENT":
        start = perf_counter()
        result = _glucose(formula)
        return {
            **result, "used_compression": False,
            "compression_proof_verified": False,
            "lean_gate": gate,
            "gate_seconds": gate_seconds,
            "solve_seconds": perf_counter() - start,
            "unsat_kernel_verified": False,
        }

    candidate = compress_binary_xor_components(formula)
    residual = substitute_residual_formula(formula, candidate)
    digest = sha256(json.dumps(candidate, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    if (candidate.get("status") != "UNVERIFIED_STRUCTURAL_CANDIDATE"
            or residual.formula_hash != gate.get("residual_formula_sha256")
            or digest != gate.get("component_certificate_sha256")):
        # A changed output, even after Lean acceptance, is never used.
        start = perf_counter()
        result = _glucose(formula)
        return {
            **result, "used_compression": False,
            "compression_proof_verified": False,
            "reason": "POST_GATE_CERTIFICATE_MISMATCH",
            "lean_gate": gate,
            "gate_seconds": gate_seconds,
            "solve_seconds": perf_counter() - start,
            "unsat_kernel_verified": False,
        }

    start = perf_counter()
    result = _glucose(residual)
    solve_seconds = perf_counter() - start
    if result["status"] == "SAT_MODEL_CHECKED":
        reduced_assignment = result["assignment"]
        roots = dict(candidate["roots"])
        root_values = {
            root: int(reduced_assignment.get(root, False))
            for root in set(roots.values())
        }
        lifted = reconstruct_values(candidate, root_values)
        original_assignment = {
            v: bool(lifted.get(v, reduced_assignment.get(v, False)))
            for v in formula.variables
        }
        if not formula_satisfied(formula, original_assignment):
            # This should be unreachable under a sound Lean gate; fail shut.
            return {
                "status": "RECONSTRUCTION_REJECTED",
                "assignment": {}, "used_compression": False,
                "compression_proof_verified": False,
                "unsat_kernel_verified": False,
                "gate_seconds": gate_seconds, "solve_seconds": solve_seconds,
            }
        result = {"status": "SAT_MODEL_CHECKED", "assignment": original_assignment}

    return {
        **result,
        "used_compression": True,
        "compression_proof_verified": True,
        "unsat_kernel_verified": False,
        "lean_gate_proof_sha256": gate["proof_source_sha256"],
        "original_variables": len(formula.variables),
        "residual_variables": len(residual.variables),
        "gate_seconds": gate_seconds,
        "solve_seconds": solve_seconds,
        "claim_boundary": "Lean-verified equisatisfiability of source and residual; UNSAT solver result still needs separate proof",
    }
