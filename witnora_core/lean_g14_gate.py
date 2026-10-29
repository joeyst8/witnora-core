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
from .lean_cnf_gate import verify_cnf_normalization_with_lean
from .lean_g5_gate import (_serialize_cnf, _serialize_rows, _compile_dag,
                            verify_g5_certificate_with_lean)
from .lean_cnf_gate import _lean_rows, _strict_rows
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
        "import Witnora.SignedSerialization",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 0",
    ]
    source_cnf = _serialize_cnf(original)
    lines.append(
        "example : Witnora.SignedSerialization.decodeCNF "
        f"{original.to_clause_lists()} = {source_cnf} := by decide"
    )
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
        for part in parts:
            lines.append(
                "example : Witnora.SignedSerialization.decodeCNF "
                f"{part.to_clause_lists()} = {_serialize_cnf(part)} := by decide"
            )
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



def _check_complete_g14_with_lean(
    formula: CNFFormula,
    raw_clauses: object,
    source_tokens: object,
    source_text: object,
    separator: list[int],
    partitions: list[tuple[dict[int, bool], list[CNFFormula]]],
    branch_jobs: list[tuple[str, str, CNFFormula, Any]],
    *,
    timeout_seconds: int,
    project_root: Path | None,
) -> str:
    """Kernel-check one closed source -> canonical -> G14 -> G5 theorem."""
    if type(source_text) is not str or not source_text.isascii() or len(source_text) > 65536:
        raise ValueError("unsupported full-document source")
    if type(source_tokens) not in (list, tuple) or any(type(x) is not int for x in source_tokens):
        raise ValueError("invalid source integer stream")
    raw = _lean_rows(_strict_rows(raw_clauses))
    canonical = _lean_rows(formula.to_clause_lists())
    source_bytes = [ord(c) for c in source_text]
    token_data = list(source_tokens)
    if len(partitions) != len(branch_jobs) or not partitions:
        raise ValueError("incomplete G14 branch certificates")
    sorted_vars = sorted(separator)
    branch_patterns = []
    component_values = []
    chosen_values = []
    bound_values = []
    row_values = []
    step_values = []
    for (assignment, parts), (_branch_id, _selected_id, chosen, certificate) in zip(
            partitions, branch_jobs):
        if sorted(assignment) != sorted_vars:
            raise ValueError("malformed branch")
        pattern = "[" + ", ".join(
            f"({v}, {'true' if assignment[v] else 'false'})" for v in sorted_vars
        ) + "]"
        branch_patterns.append(pattern)
        component_values.append("[" + ", ".join(_serialize_cnf(part) for part in parts) + "]")
        chosen_values.append(_serialize_cnf(chosen))
        payload = certificate.to_dict() if hasattr(certificate, "to_dict") else certificate
        if not isinstance(payload, dict):
            raise ValueError("invalid branch proof")
        trace = payload.get("gaussian_elimination_trace")
        if (not isinstance(trace, list) or not trace
                or not isinstance(trace[0], dict) or trace[0].get("type") != "INITIAL_ROWS"):
            raise ValueError("invalid branch rows")
        initial = trace[0].get("rows")
        row_values.append(_serialize_rows(initial))
        step_values.append(_compile_dag(initial, payload.get("row_operations")))
        bound_values.append(str(chosen.max_var + 1))

    if len(set(branch_patterns)) != len(branch_patterns):
        raise ValueError("duplicate separator branches")
    def definition(name: str, result_type: str, values: list[str], default: str) -> str:
        expression = default
        for pattern, value in reversed(list(zip(branch_patterns, values))):
            expression = f"(if branch == {pattern} then {value} else {expression})"
        return f"def {name} (branch : List (Nat × Bool)) : {result_type} := {expression}"

    lines = [
        "import Witnora.G14ConcreteBridge",
        "set_option maxRecDepth 16384",
        "set_option maxHeartbeats 0",
        definition("certComponents", "List Witnora.Concrete.CNF", component_values, "[]"),
        definition("certSelected", "Witnora.Concrete.CNF", chosen_values, "[]"),
        definition("certBound", "Nat", bound_values, "0"),
        definition("certRows", "List Witnora.G5Trace.Row", row_values, "[]"),
        definition("certSteps", "List Witnora.G5Dag.XorRef", step_values, "[]"),
    ]
    enumerated = "[" + ", ".join(branch_patterns) + "]"
    # Each quantified premise is discharged from precisely the generated
    # finite branch enumeration; no unbounded universal is decided.
    def branch_cases() -> list[str]:
        return [
            "    intro branch hb",
            f"    have he : Witnora.SeparatorAssignments.enumerate {sorted_vars} = {enumerated} := by decide",
            "    rw [he] at hb",
            "    simp only [List.mem_cons, List.mem_singleton] at hb",
            "    rcases hb with " + " | ".join(f"h{i}" for i in range(len(branch_patterns))),
        ] + [
            "    · subst branch" + "\\n" + "      decide" for _ in branch_patterns
        ]

    lines.append(
        "example : Witnora.DIMACSDocument.parseDocument "
        f"{source_bytes} = some (Witnora.DIMACSTokens.serialize {raw}) "
        "∧ ¬ ∃ a, Witnora.SignedSerialization.signedCNFHolds "
        f"{raw} a := by"
    )
    def proof_for(name: str, goal: str) -> None:
        lines.append(f"  have {name} : {goal} := by")
        lines.extend(branch_cases())
    proof_for("hpart",
        f"∀ branch ∈ Witnora.SeparatorAssignments.enumerate {sorted_vars}, "
        "Witnora.ComponentPartition.checkPartition "
        "(Witnora.Conditioning.conditionCNF "
        "(Witnora.SeparatorAssignments.fixedOf branch) "
        f"(Witnora.SignedSerialization.decodeCNF {canonical})) "
        "(certComponents branch) = true")
    proof_for("hselected",
        f"∀ branch ∈ Witnora.SeparatorAssignments.enumerate {sorted_vars}, "
        "certSelected branch ∈ certComponents branch")
    proof_for("hcert",
        f"∀ branch ∈ Witnora.SeparatorAssignments.enumerate {sorted_vars}, "
        "Witnora.SparseBridge.checkG5Closed "
        "(certBound branch) (certSelected branch) "
        "(certRows branch) (certSteps branch) = true")
    lines.append(
        "  exact Witnora.G14ConcreteBridge.checked_ascii_dimacs_g14_canonical_unsat "
        f"{source_bytes} {token_data} {raw} {canonical} "
        f"(by decide) (by decide) (by decide) {sorted_vars} "
        "certComponents hpart certSelected hselected certBound certRows certSteps hcert"
    )
    proof_source = "\n".join(lines) + "\n"
    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
    formal_dir = root / "formal"
    if not (formal_dir / "lakefile.toml").is_file():
        raise ValueError("Lean project unavailable")
    with TemporaryDirectory(prefix="witnora_g14_complete_") as temp:
        path = Path(temp) / "G14CompleteSourceProof.lean"
        path.write_text(proof_source, encoding="utf-8")
        result = subprocess.run(
            ["lake", "env", "lean", str(path)], cwd=formal_dir,
            capture_output=True, text=True, timeout=timeout_seconds, check=False)
    if result.returncode != 0:
        raise ValueError("Lean rejected complete G14 theorem: " +
                         (result.stdout + result.stderr)[-1200:])
    return sha256(proof_source.encode("utf-8")).hexdigest()


def verify_g14_unsat_cover_with_lean(
    formula: CNFFormula,
    certificate: Any,
    *,
    timeout_seconds: int = 120,
    project_root: Path | None = None,
    raw_clauses: object | None = None,
    source_tokens: object | None = None,
    source_spellings: object | None = None,
    source_text: object | None = None,
) -> dict[str, Any]:
    """Accept only when every recomputed separator branch has a Lean G5 proof."""
    try:
        data = certificate.to_dict() if hasattr(certificate, "to_dict") else certificate
        if not isinstance(data, dict):
            raise ValueError("malformed G14 certificate")
        digest = sha256(json.dumps(
            {"cnf": formula.to_clause_lists(), "certificate": data,
             "raw_clauses": raw_clauses, "source_tokens": source_tokens,
         "source_spellings": source_spellings, "source_text": source_text},
            sort_keys=True, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")).hexdigest()
    except (ValueError, TypeError, AttributeError):
        return {"verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED",
                "reason": "MALFORMED_INPUT"}

    failure = {"verified": False, "lean_formal_status": "NOT_LEAN_VERIFIED",
               "input_sha256": digest}
    try:
        if source_text is not None and source_spellings is None:
            raise ValueError("source text requires original decimal spellings")
        if source_spellings is not None and source_tokens is None:
            raise ValueError("lexemes require original integer token stream")
        if source_tokens is not None and raw_clauses is None:
            raise ValueError("source tokens require original clauses")
        if data.get("lean_formal_status", "NOT_LEAN_VERIFIED") != "NOT_LEAN_VERIFIED":
            raise ValueError("untrusted G14 formal verification claim")
        if data.get("formula_hash") != formula.formula_hash:
            raise ValueError("G14 source formula hash mismatch")
        native = check_separator_affine_certificate(formula, data)
        if (native.get("checker_status") != SEPARATOR_AFFINE_CERTIFICATE_VERIFIED
                or data.get("final_result") != UNSAT_CERTIFIED):
            raise ValueError("G14 native UNSAT-cover check failed")
        # Source CNF canonicality is mandatory; selected residual branches
        # receive their own mandatory check through the G5 Lean gate.
        normalization_check = verify_cnf_normalization_with_lean(
            formula.to_clause_lists() if raw_clauses is None else raw_clauses,
            formula.to_clause_lists(),
            timeout_seconds=timeout_seconds, project_root=project_root,
            source_tokens=source_tokens, source_spellings=source_spellings,
            source_text=source_text,
        )
        if not normalization_check.get("verified"):
            return {**failure, "reason": "CNF_NORMALIZATION_REJECTED",
                    "normalization_check": normalization_check}
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
            if (not result.get("verified")
                    or result.get("lean_formal_status") != "LEAN_VERIFIED"
                    or not isinstance(result.get("normalization_check"), dict)
                    or not result["normalization_check"].get("verified")):
                return {**failure, "reason": "BRANCH_G5_LEAN_REJECTED",
                        "partition_proof_source_sha256": partition_digest,
                        "branches": branches}
        complete_proof_digest = None
        if source_text is not None:
            complete_proof_digest = _check_complete_g14_with_lean(
                formula, raw_clauses, source_tokens, source_text,
                separator, partition_jobs, branch_jobs,
                timeout_seconds=timeout_seconds, project_root=project_root,
            )
        return {"verified": True, "lean_formal_status": (
                    "LEAN_END_TO_END_G14_UNSAT_VERIFIED"
                    if complete_proof_digest is not None
                    else "LEAN_G5_COVER_AND_PARTITIONS_VERIFIED"),
                "input_sha256": digest, "normalization_check": normalization_check,
                "source_normalization_verified": raw_clauses is not None,
                "source_tokens_verified": source_tokens is not None,
                "source_lexemes_verified": source_spellings is not None,
            "source_document_verified": source_text is not None,
                "source_formula_hash": formula.formula_hash,
                "partition_proof_source_sha256": partition_digest,
                "complete_proof_source_sha256": complete_proof_digest,
                "branches": branches,
                "claim_boundary": "Full-source status requires one combined kernel-checked G14 theorem; universal Python refinement unproved"}
    except (ValueError, TypeError, KeyError, IndexError, AttributeError,
            OSError, subprocess.TimeoutExpired) as exc:
        return {**failure, "reason": type(exc).__name__, "detail": str(exc)[-1600:]}
