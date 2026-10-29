"""Fail-closed G14 UNSAT-cover gate backed by per-branch Lean G5 proofs.

The Python separator/conditioning algorithm remains outside Lean's universal
refinement proof. This verifies its recomputed branch data and requires real
Lean acceptance for each selected residual UNSAT certificate. Never equate
a native G14 checker status with formal verification.
"""

from __future__ import annotations

from hashlib import sha256
import json
import subprocess
from tempfile import TemporaryDirectory
from pathlib import Path
from typing import Any

from .cnf import CNFFormula
from .lean_g5_gate import _serialize_cnf, verify_g5_certificate_with_lean
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



def _lean_partial_assignment(assignment: dict[int, bool]) -> str:
    """Emit only numeric fixed-variable tests and Bool constructors."""
    body = "none"
    for var in sorted(assignment, reverse=True):
        if type(var) is not int or var <= 0 or type(assignment[var]) is not bool:
            raise ValueError("invalid separator assignment")
        value = "true" if assignment[var] else "false"
        body = f"(if v == {var} then some {value} else {body})"
    return "(fun v : Nat => " + body + ")"


def _check_partitions_with_lean(
    original: CNFFormula,
    branch_partitions: list[tuple[dict[int, bool], list[CNFFormula]]],
    *,
    timeout_seconds: int,
    project_root: Path | None,
) -> str:
    """Compile closed Lean propositions for all actual conditioned branches."""
    lines = [
        "import Witnora.ComponentPartition",
        "import Witnora.SeparatorAssignments",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 0",
    ]
    source_cnf = _serialize_cnf(original)
    # The same Lean proof checks that Python supplied every branch in
    # the specified order, not merely that supplied branches are valid.
    variables = sorted(branch_partitions[0][0]) if branch_partitions else []
    patterns = []
    for assignment, _ in branch_partitions:
        if sorted(assignment) != variables:
            raise ValueError("inconsistent separator assignments")
        literals = ", ".join(
            f"({v}, {'true' if assignment[v] else 'false'})"
            for v in variables
        )
        patterns.append("[" + literals + "]")
    lines.append(
        "example : Witnora.SeparatorAssignments.enumerate "
        f"{variables} = [" + ", ".join(patterns) + "] := by decide"
    )
    for assignment, parts in branch_partitions:
        cnfs = "[" + ", ".join(_serialize_cnf(part) for part in parts) + "]"
        lines.append(
            "example : Witnora.ComponentPartition.checkPartition "
            "(Witnora.Conditioning.conditionCNF "
            f"{_lean_partial_assignment(assignment)} {source_cnf}) "
            f"{cnfs} = true := by decide"
        )
    source_text = "\n".join(lines) + "\n"
    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
    formal = root / "formal"
    if not (formal / "lakefile.toml").is_file():
        raise ValueError("Lean project unavailable")
    with TemporaryDirectory(prefix="witnora_g14_partitions_") as temp:
        proof_path = Path(temp) / "G14PartitionCheck.lean"
        proof_path.write_text(source_text, encoding="utf-8")
        result = subprocess.run(
            ["lake", "env", "lean", str(proof_path)],
            cwd=formal, capture_output=True, text=True,
            timeout=timeout_seconds, check=False,
        )
    if result.returncode != 0:
        raise ValueError("Lean rejected G14 conditioning or partition")
    return sha256(source_text.encode("utf-8")).hexdigest()


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
        branch_jobs = []
        partition_jobs = []
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
            partition_jobs.append((assignment, [parts[c["component_id"]] for c in components]))
            branch_jobs.append((branch_id, selected, parts[selected],
                                matching[0]["affine_certificate"]))
        if not branch_jobs:
            raise ValueError("empty separator branch coverage")
        partition_digest = _check_partitions_with_lean(
            formula, partition_jobs, timeout_seconds=timeout_seconds,
            project_root=project_root,
        )
        branches = []
        for branch_id, selected, component_formula, affine_certificate in branch_jobs:
            result = verify_g5_certificate_with_lean(
                component_formula, affine_certificate,
                timeout_seconds=timeout_seconds, max_arity=arity,
                project_root=project_root,
            )
            branches.append({"assignment_id": branch_id, "component_id": selected,
                             "lean_check": result})
            if not result.get("verified"):
                return {**failure, "reason": "BRANCH_G5_LEAN_REJECTED",
                        "partition_proof_source_sha256": partition_digest,
                        "branches": branches}
        return {"verified": True, "lean_formal_status": "LEAN_G5_COVER_AND_PARTITIONS_VERIFIED",
                "input_sha256": digest, "partition_proof_source_sha256": partition_digest,
                "branches": branches,
                "claim_boundary": "Lean verifies per-branch partitions and G5 proofs; universal Python refinement unproved"}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError,
            OSError, subprocess.TimeoutExpired) as exc:
        return {**failure, "reason": type(exc).__name__}
