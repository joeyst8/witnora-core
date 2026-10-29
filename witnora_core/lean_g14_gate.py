"""Fail-closed G14 UNSAT-cover gate backed by per-branch Lean G5 proofs.

The Python separator/conditioning algorithm remains outside Lean's universal
refinement proof. This verifies its recomputed branch data and requires real
Lean acceptance for each selected residual UNSAT certificate. Never equate
a native G14 checker status with formal verification.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
from typing import Any

from .cnf import CNFFormula
from .lean_g5_gate import verify_g5_certificate_with_lean
from .separator_affine_family_theorem import (
    SEPARATOR_AFFINE_CERTIFICATE_VERIFIED,
    UNSAT_CERTIFIED,
    _all_assignments,
    _assignment_from_payload,
    _branch_partition_exact,
    _component_dicts,
    _condition_by_separator,
    check_separator_affine_certificate,
)


def verify_g14_unsat_cover_with_lean(
    formula: CNFFormula,
    certificate: Any,
    *,
    timeout_seconds: int = 120,
    project_root: Path | None = None,
) -> dict[str, Any]:
    """Accept only when every recomputed separator branch has a Lean G5 proof."""
    try:
        data = certificate.to_dict() if hasattr(certificate, "to_dict") else certificate
        if not isinstance(data, dict):
            raise ValueError("malformed G14 certificate")
        digest = sha256(json.dumps(
            {"cnf": formula.to_clause_lists(), "certificate": data},
            sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest()
    except (ValueError, TypeError, AttributeError):
        return {"verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED",
                "reason": "MALFORMED_INPUT"}

    failure = {"verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED",
               "input_sha256": digest}
    try:
        native = check_separator_affine_certificate(formula, data)
        if (native.get("checker_status") != SEPARATOR_AFFINE_CERTIFICATE_VERIFIED
                or data.get("final_result") != UNSAT_CERTIFIED):
            raise ValueError("G14 native UNSAT-cover check failed")
        separator = data["separator_variables"]
        if (not isinstance(separator, list)
                or any(type(v) is not int or v <= 0 for v in separator)
                or len(set(separator)) != len(separator)):
            raise ValueError("invalid separator")
        components = _component_dicts(formula, separator)
        records = data["separator_assignments"]
        if not isinstance(records, list):
            raise ValueError("invalid branch records")
        by_id = {rec["assignment_id"]: rec for rec in records}
        cover = data["unsat_cover"]["covering_unsat_component_per_assignment"]
        arity = data["family_parameters"]["affine_arity_bound_r"]
        if type(arity) is not int or arity < 0:
            raise ValueError("invalid arity")
        branches = []
        for i, assignment in enumerate(_all_assignments(separator), start=1):
            branch_id = f"S{i}"
            record = by_id[branch_id]
            if _assignment_from_payload(record["separator_assignment"]) != assignment:
                raise ValueError("tampered separator assignment")
            residual, parts, errors = _condition_by_separator(
                formula, assignment, components,
            )
            if errors or not _branch_partition_exact(residual, parts):
                raise ValueError("residual component partition rejected")
            selected = cover[branch_id]
            matching = [
                item for item in record["component_records"]
                if item["component_id"] == selected
            ]
            if len(matching) != 1 or selected not in parts:
                raise ValueError("missing or duplicated covering component")
            result = verify_g5_certificate_with_lean(
                parts[selected], matching[0]["affine_certificate"],
                timeout_seconds=timeout_seconds, max_arity=arity,
                project_root=project_root,
            )
            branches.append({"assignment_id": branch_id, "component_id": selected,
                             "lean_check": result})
            if not result.get("verified"):
                return {**failure, "reason": "BRANCH_G5_LEAN_REJECTED",
                        "branches": branches}
        if not branches:
            raise ValueError("empty separator branch coverage")
        return {"verified": True, "lean_formal_status": "LEAN_G5_COVER_VERIFIED",
                "input_sha256": digest, "branches": branches,
                "claim_boundary": "G5 proofs verified per G14 branch; Python decomposition refinement unproved"}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError) as exc:
        return {**failure, "reason": type(exc).__name__}
