"""Fail-closed, per-certificate Lean gate for G5 affine UNSAT claims.

A native Python check is not a formal proof. This function emits only a fixed
Lean proposition containing concrete numeric CNF clauses, initial rows and a
DAG of row references; Lean must kernel-check `checkG5Closed = true`.
No certificate-controlled Lean source or imports are accepted.

The return value is an attestation about this invocation, not an editable
claim in the original certificate. A later production integration must bind
and persist the attestation within a trusted service.
"""

from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path
import subprocess
from tempfile import TemporaryDirectory
from typing import Any

from .cnf import CNFFormula
from .lean_cnf_gate import (_lean_rows, _strict_rows,
                            verify_cnf_normalization_with_lean)


def _strict_nonnegative(value: Any) -> int:
    if type(value) is not int or value < 0:
        raise ValueError("certificate index must be a nonnegative integer")
    return value


def _serialize_cnf(formula: CNFFormula) -> str:
    clauses = []
    for clause in formula.to_clause_lists():
        entries = []
        for value in clause:
            if type(value) is not int or value == 0:
                raise ValueError("invalid signed CNF literal")
            entries.append(f"({abs(value)}, {'true' if value > 0 else 'false'})")
        clauses.append("[" + ", ".join(entries) + "]")
    return "[" + ", ".join(clauses) + "]"


def _serialize_rows(rows: Any) -> str:
    if not isinstance(rows, list):
        raise ValueError("initial rows must be a list")
    rendered = []
    for row in rows:
        if not isinstance(row, dict) or not isinstance(row.get("coefficients"), list):
            raise ValueError("malformed G5 input row")
        coeff = [_strict_nonnegative(v) for v in row["coefficients"]]
        if type(row.get("rhs")) is not int or row["rhs"] not in (0, 1):
            raise ValueError("row rhs must be a Boolean integer")
        rendered.append(
            "{ coefficients := [" + ", ".join(map(str, coeff)) +
            "], rhs := " + ("true" if row["rhs"] == 1 else "false") + " }"
        )
    return "[" + ", ".join(rendered) + "]"


def _compile_dag(rows: list[dict[str, Any]], ops: Any) -> str:
    if not isinstance(ops, list):
        raise ValueError("G5 operations must be a list")
    refs = list(range(len(rows)))
    next_id = len(refs)
    compiled = []
    for op in ops:
        if not isinstance(op, dict):
            raise ValueError("malformed G5 operation")
        kind = op.get("operation")
        if kind == "SWAP_ROWS":
            a = _strict_nonnegative(op.get("row_a"))
            b = _strict_nonnegative(op.get("row_b"))
            if a >= len(refs) or b >= len(refs):
                raise ValueError("out-of-range swap")
            refs[a], refs[b] = refs[b], refs[a]
        elif kind == "ADD_ROW_XOR":
            target = _strict_nonnegative(op.get("target_row"))
            source = _strict_nonnegative(op.get("source_row"))
            if (target >= len(refs) or source >= len(refs)
                    or target == source):
                raise ValueError("invalid XOR row reference")
            compiled.append(f"({refs[target]}, {refs[source]})")
            refs[target] = next_id
            next_id += 1
        else:
            raise ValueError("unsupported G5 operation")
    return "[" + ", ".join(compiled) + "]"


def verify_g5_certificate_with_lean(
    formula: CNFFormula,
    certificate: Any,
    *,
    timeout_seconds: int = 120,
    max_arity: int = 10,
    project_root: Path | None = None,
    raw_clauses: object | None = None,
) -> dict[str, Any]:
    """Return LEAN_VERIFIED only after independent Lean execution succeeds.

    Fail closed on malformed data, unavailable Lean, timeout, or kernel error.
    Never mutates the native certificate or changes its native solver status.
    """
    data = certificate.to_dict() if hasattr(certificate, "to_dict") else certificate
    identity = sha256(json.dumps(
        {"formula": formula.to_clause_lists(), "certificate": data,
         "raw_clauses": raw_clauses},
        sort_keys=True, separators=(",", ":"), default=str,
    ).encode("utf-8")).hexdigest()
    failure = {"lean_formal_status": "NOT_LEAN_VERIFIED",
               "verified": False, "input_sha256": identity}

    try:
        if not isinstance(data, dict):
            raise ValueError("certificate must be a mapping")
        if data.get("lean_formal_status", "NOT_LEAN_VERIFIED") != "NOT_LEAN_VERIFIED":
            raise ValueError("untrusted formal verification claim")
        if data.get("formula_hash") != formula.formula_hash:
            raise ValueError("formula hash mismatch")
        if data.get("checker_status") != "AFFINE_RESIDUE_CERTIFICATE_VERIFIED":
            raise ValueError("native certificate not verified")
        if data.get("status") != "AFFINE_RESIDUE_UNSAT_NATIVE_CERTIFIED":
            raise ValueError("not an eligible G5 UNSAT certificate")
        from .operator_genesis import check_affine_residue_certificate
        native = check_affine_residue_certificate(formula, data, max_arity=max_arity)
        if native.get("status") != "AFFINE_RESIDUE_CERTIFICATE_VERIFIED":
            raise ValueError("native certificate consistency check failed")

        # With raw DIMACS provenance, Lean checks the actual parsed clauses
        # against Python's canonical formula. Without it only canonicality
        # (not source-to-formula fidelity) is established.
        normalization_check = verify_cnf_normalization_with_lean(
            formula.to_clause_lists() if raw_clauses is None else raw_clauses,
            formula.to_clause_lists(),
            timeout_seconds=timeout_seconds, project_root=project_root,
        )
        if not normalization_check.get("verified"):
            return {**failure, "reason": "CNF_NORMALIZATION_REJECTED",
                    "normalization_check": normalization_check}

        trace = data.get("gaussian_elimination_trace")
        if (not isinstance(trace, list) or len(trace) < 2
                or not isinstance(trace[0], dict)
                or not isinstance(trace[-1], dict)
                or trace[0].get("type") != "INITIAL_ROWS"
                or trace[-1].get("type") != "FINAL_ROWS"):
            raise ValueError("invalid G5 trace envelope")
        initial_rows = trace[0].get("rows")
        if not isinstance(initial_rows, list):
            raise ValueError("missing initial rows")
        cnf = _serialize_cnf(formula)
        rows = _serialize_rows(initial_rows)
        dag = _compile_dag(initial_rows, data.get("row_operations"))
        bound = _strict_nonnegative(formula.max_var) + 1
        lean_source = (
            "import Witnora.SparseBridge\n"
            "import Witnora.SignedSerialization\n"
            "set_option maxRecDepth 16384\n"
            "set_option maxHeartbeats 0\n"
            "example : Witnora.SignedSerialization.decodeCNF "
            f"{formula.to_clause_lists()} = {cnf} := by decide\n"
        )
        if raw_clauses is None:
            lean_source += (
                "example : Witnora.SparseBridge.checkG5Closed "
                f"{bound} {cnf} {rows} {dag} = true := by decide\n"
            )
        else:
            # This closed theorem proves UNSAT of the source signed clauses
            # themselves, using canonicalization plus G5 reconstruction.
            lean_source = "import Witnora.SourceG5\n" + lean_source
            lean_source += (
                "example : Witnora.SourceG5.checkRawG5 "
                f"{bound} {_lean_rows(_strict_rows(raw_clauses))} "
                f"{rows} {dag} = true := by decide\n"
            )
        root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[1]
        formal_dir = root / "formal"
        if not (formal_dir / "lakefile.toml").is_file():
            raise ValueError("Lean project unavailable")
        with TemporaryDirectory(prefix="witnora_g5_lean_") as temp:
            source = Path(temp) / "G5CertificateCheck.lean"
            source.write_text(lean_source, encoding="utf-8")
            result = subprocess.run(
                ["lake", "env", "lean", str(source)],
                cwd=formal_dir, capture_output=True, text=True,
                timeout=timeout_seconds, check=False,
            )
        if result.returncode != 0:
            raise ValueError("Lean kernel rejected the certificate: " + result.stderr[-1200:])
        return {
            "lean_formal_status": "LEAN_VERIFIED",
            "verified": True,
            "input_sha256": identity,
            "normalization_check": normalization_check,
            "source_normalization_verified": raw_clauses is not None,
            "source_formula_hash": formula.formula_hash,
            "proof_source_sha256": sha256(lean_source.encode("utf-8")).hexdigest(),
        }
    except (ValueError, TypeError, KeyError, IndexError, OSError,
            subprocess.TimeoutExpired) as exc:
        return {**failure, "reason": type(exc).__name__,
                "detail": str(exc)[-1200:]}
