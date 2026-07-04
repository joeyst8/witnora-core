"""Bounded XOR-to-DRAT bridge for detected-CNF XOR contradictions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any, Iterable

from .certificate import CollapsePath, XOR_UNSAT_NATIVE
from .cnf import CNFFormula, Clause, has_tautology
from .dimacs import export_dimacs
from .drat import DRATExport, PROOF_SCOPE_END_TO_END, PROOF_SCOPE_FINAL_STATE_ONLY_UNSUPPORTED
from .drat_check import CHECKED_AGAINST, check_drat_text, is_rup
from .drat_trim import run_drat_trim
from .xor import XorEquation, XorSystem, solve_xor_system_gaussian

XOR_DRAT_VERIFIED = "VERIFIED"
XOR_DRAT_FAILED = "FAILED"
XOR_DRAT_NOT_RUN_NO_DRAT_TRIM = "NOT_RUN_NO_DRAT_TRIM"
XOR_DRAT_SKIPPED_ROW_WIDTH_CAP = "SKIPPED_ROW_WIDTH_CAP"
XOR_DRAT_SKIPPED_PROOF_SIZE_CAP = "SKIPPED_PROOF_SIZE_CAP"
XOR_DRAT_UNSUPPORTED_SIDECAR_ORIGINAL_CNF = "UNSUPPORTED_SIDECAR_ORIGINAL_CNF"


@dataclass(frozen=True)
class XorDRATBridgeResult:
    drat_export: DRATExport
    xor_status: dict[str, Any]


def _clause_line(clause: tuple[int, ...]) -> str:
    if not clause:
        return "0"
    return " ".join(str(lit) for lit in clause) + " 0"


def _canonical_clause(raw: Iterable[int]) -> tuple[int, ...]:
    return Clause(raw).literals


def _resolve(a: tuple[int, ...], b: tuple[int, ...], pivot: int) -> tuple[int, ...] | None:
    raw = [lit for lit in a if lit != pivot] + [lit for lit in b if lit != -pivot]
    if has_tautology(raw):
        return None
    return Clause(raw).literals


def _base_xor_status(
    status: str,
    *,
    proof_base: str | None = None,
    proof_file: str | None = None,
    source: str | None = None,
    reason: str | None = None,
    external_verified: bool = False,
) -> dict[str, Any]:
    return {
        "xor_drat_bridge": external_verified,
        "xor_drat_status": status,
        "proof_base": proof_base,
        "proof_file": proof_file,
        "source": source,
        "external_drat": external_verified,
        "drat_claim": "EXPORTED_VERIFIED" if external_verified else ("FAILED" if status == XOR_DRAT_FAILED else "NOT_EXPORTED"),
        "xor_native_trace_retained": True,
        "reason": reason,
    }


def _base_drat_status(
    export_status: str,
    *,
    xor_status: dict[str, Any],
    supported_reason: str | None = None,
    unsupported_reason: str | None = None,
    proof_file: str | None = None,
    internal_verified: bool = False,
) -> dict[str, Any]:
    return {
        "drat_export_status": export_status,
        "proof_scope": PROOF_SCOPE_END_TO_END if export_status == "EXPORTED" else PROOF_SCOPE_FINAL_STATE_ONLY_UNSUPPORTED,
        "checked_against": CHECKED_AGAINST,
        "supported_reason": supported_reason,
        "unsupported_reason": unsupported_reason,
        "requires_external_checker": False,
        "external_checker": "NOT_RUN",
        "external_checker_path": None,
        "external_checker_ran": False,
        "external_checker_verified": False,
        "external_checker_exit_code": None,
        "external_checker_stdout_excerpt": "",
        "external_checker_stderr_excerpt": "",
        "external_checker_timeout": False,
        "external_checker_error": None,
        "internal_rup_subset_checker_verified": internal_verified,
        "internal_drat_checker_verified": internal_verified,
        "proof_file": proof_file,
        **xor_status,
    }


def _detected_equations(path: CollapsePath) -> list[XorEquation]:
    data = (path.xor_data or {}).get("xor_system", {})
    equations: list[XorEquation] = []
    for item in data.get("equations", []):
        if item.get("source") != "detected_cnf_pattern":
            continue
        equations.append(
            XorEquation(
                item.get("variables", []),
                int(item.get("rhs", 0)),
                source="detected_cnf_pattern",
                source_clauses=item.get("source_clauses", []),
                pattern_size=int(item.get("pattern_size", len(item.get("variables", [])))),
                source_clauses_removed=bool(item.get("source_clauses_removed", False)),
                exact_full_encoding=bool(item.get("exact_full_encoding", False)),
                safe_use=bool(item.get("safe_use", True)),
            )
        )
    return equations


def _source_clauses(equations: Iterable[XorEquation]) -> set[tuple[int, ...]]:
    clauses: set[tuple[int, ...]] = set()
    for equation in equations:
        for clause in equation.source_clauses:
            clauses.add(_canonical_clause(clause))
    return clauses


def _resolution_refutation(
    original_formula: CNFFormula,
    support_clauses: set[tuple[int, ...]],
    *,
    max_proof_clauses: int,
) -> tuple[str | None, str | None, int]:
    active = {clause.literals for clause in original_formula.clauses}
    if not support_clauses <= active:
        return None, "DETECTED_XOR_SOURCE_CLAUSE_MISSING_FROM_ORIGINAL", 0

    known = set(support_clauses)
    lines: list[str] = []
    emitted = 0

    if () in known:
        if not is_rup(active, ()):
            return None, "EMPTY_SOURCE_NOT_RUP", emitted
        return "0\n", None, 1

    while True:
        progress = False
        ordered = sorted(known, key=lambda clause: (len(clause), clause))
        for idx, left in enumerate(ordered):
            for right in ordered[idx + 1 :]:
                pivots = sorted(set(left) & {-lit for lit in right}, key=lambda lit: (abs(lit), lit < 0))
                for pivot in pivots:
                    resolvent = _resolve(left, right, pivot)
                    if resolvent is None or resolvent in known:
                        continue
                    if not is_rup(active, resolvent):
                        return None, "RESOLVENT_NOT_RUP_CHECKABLE", emitted
                    lines.append(_clause_line(resolvent))
                    active.add(resolvent)
                    known.add(resolvent)
                    emitted += 1
                    if emitted > max_proof_clauses:
                        return None, XOR_DRAT_SKIPPED_PROOF_SIZE_CAP, emitted
                    if resolvent == ():
                        return "\n".join(lines) + "\n", None, emitted
                    progress = True
                    break
                if progress:
                    break
            if progress:
                break
        if not progress:
            return None, "RESOLUTION_CLOSURE_DID_NOT_DERIVE_EMPTY", emitted


def export_xor_drat_for_path(
    original_formula: CNFFormula,
    path: CollapsePath,
    *,
    drat_trim_path: str | Path | None,
    original_dimacs_text: str | None = None,
    max_row_width: int = 8,
    max_proof_clauses: int = 50000,
) -> XorDRATBridgeResult:
    if path.status != XOR_UNSAT_NATIVE:
        xor_status = _base_xor_status("NOT_APPLICABLE", reason="result is not XOR-native UNSAT")
        return XorDRATBridgeResult(
            DRATExport(None, _base_drat_status("UNSUPPORTED", xor_status=xor_status, unsupported_reason="result is not XOR-native UNSAT")),
            xor_status,
        )

    if drat_trim_path is None:
        xor_status = _base_xor_status(
            XOR_DRAT_NOT_RUN_NO_DRAT_TRIM,
            proof_base=None,
            proof_file=None,
            source=None,
            reason="real drat-trim path was not provided",
        )
        return XorDRATBridgeResult(
            DRATExport(None, _base_drat_status("UNSUPPORTED", xor_status=xor_status, unsupported_reason=xor_status["reason"])),
            xor_status,
        )

    detected = _detected_equations(path)
    if not detected:
        xor_status = _base_xor_status(
            XOR_DRAT_UNSUPPORTED_SIDECAR_ORIGINAL_CNF,
            reason="XOR contradiction is not implied by detected CNF XOR clauses alone",
        )
        return XorDRATBridgeResult(
            DRATExport(None, _base_drat_status("UNSUPPORTED", xor_status=xor_status, unsupported_reason=xor_status["reason"])),
            xor_status,
        )

    widest = max((len(eq.variables) for eq in detected), default=0)
    if widest > max_row_width:
        xor_status = _base_xor_status(
            XOR_DRAT_SKIPPED_ROW_WIDTH_CAP,
            reason=f"detected XOR row width {widest} exceeds cap {max_row_width}",
        )
        return XorDRATBridgeResult(
            DRATExport(None, _base_drat_status("UNSUPPORTED", xor_status=xor_status, unsupported_reason=xor_status["reason"])),
            xor_status,
        )

    detected_solution = solve_xor_system_gaussian(XorSystem(detected))
    if detected_solution.get("status") != "UNSAT":
        xor_status = _base_xor_status(
            XOR_DRAT_UNSUPPORTED_SIDECAR_ORIGINAL_CNF,
            reason="detected CNF XOR equations alone are satisfiable; sidecar or CNF-unit conflict may be needed",
        )
        return XorDRATBridgeResult(
            DRATExport(None, _base_drat_status("UNSUPPORTED", xor_status=xor_status, unsupported_reason=xor_status["reason"])),
            xor_status,
        )

    proof_text, error, emitted = _resolution_refutation(
        original_formula,
        _source_clauses(detected),
        max_proof_clauses=max_proof_clauses,
    )
    if error is not None or proof_text is None:
        status_name = XOR_DRAT_SKIPPED_PROOF_SIZE_CAP if error == XOR_DRAT_SKIPPED_PROOF_SIZE_CAP else XOR_DRAT_FAILED
        xor_status = _base_xor_status(status_name, reason=error, source="detected_cnf_pattern")
        return XorDRATBridgeResult(
            DRATExport(None, _base_drat_status("FAILED" if status_name == XOR_DRAT_FAILED else "UNSUPPORTED", xor_status=xor_status, unsupported_reason=error)),
            xor_status,
        )

    internal = check_drat_text(original_formula, proof_text, strict_deletions=False)
    if not internal.get("verified"):
        xor_status = _base_xor_status(
            XOR_DRAT_FAILED,
            source="detected_cnf_pattern",
            reason=f"internal RUP-subset checker rejected proof: {internal.get('error')}",
        )
        return XorDRATBridgeResult(
            DRATExport(None, _base_drat_status("FAILED", xor_status=xor_status, unsupported_reason=xor_status["reason"])),
            xor_status,
        )

    original_text = original_dimacs_text or export_dimacs(original_formula)
    with TemporaryDirectory() as tmp:
        root = Path(tmp)
        original_path = root / "original.dimacs"
        proof_path = root / "proof.drat"
        original_path.write_text(original_text if original_text.endswith("\n") else original_text + "\n", encoding="utf-8")
        proof_path.write_text(proof_text, encoding="utf-8")
        trim_result = run_drat_trim(original_path, proof_path, drat_trim_path)

    if not trim_result.get("external_checker_verified", False):
        xor_status = _base_xor_status(
            XOR_DRAT_FAILED,
            source="detected_cnf_pattern",
            reason=f"drat-trim did not verify proof: {trim_result.get('error')}",
        )
        drat_status = _base_drat_status("FAILED", xor_status=xor_status, unsupported_reason=xor_status["reason"])
        drat_status.update(
            {
                "external_checker": trim_result.get("external_checker", "DRAT_TRIM"),
                "external_checker_path": trim_result.get("external_checker_path"),
                "external_checker_ran": bool(trim_result.get("external_checker_ran", False)),
                "external_checker_verified": False,
                "external_checker_exit_code": trim_result.get("exit_code"),
                "external_checker_stdout_excerpt": str(trim_result.get("stdout", ""))[:2000],
                "external_checker_stderr_excerpt": str(trim_result.get("stderr", ""))[:2000],
                "external_checker_timeout": bool(trim_result.get("timeout", False)),
                "external_checker_error": trim_result.get("error"),
            }
        )
        return XorDRATBridgeResult(DRATExport(None, drat_status), xor_status)

    xor_status = _base_xor_status(
        XOR_DRAT_VERIFIED,
        proof_base="original_cnf",
        proof_file="proof.drat",
        source="detected_cnf_pattern",
        external_verified=True,
    )
    xor_status["derived_clause_count"] = emitted
    drat_status = _base_drat_status(
        "EXPORTED",
        xor_status=xor_status,
        supported_reason="detected CNF XOR contradiction exported as end-to-end DRAT/RUP proof",
        proof_file="proof.drat",
        internal_verified=True,
    )
    drat_status.update(
        {
            "external_checker": trim_result.get("external_checker", "DRAT_TRIM"),
            "external_checker_path": trim_result.get("external_checker_path"),
            "external_checker_ran": True,
            "external_checker_verified": True,
            "external_checker_exit_code": trim_result.get("exit_code"),
            "external_checker_stdout_excerpt": str(trim_result.get("stdout", ""))[:2000],
            "external_checker_stderr_excerpt": str(trim_result.get("stderr", ""))[:2000],
            "external_checker_timeout": bool(trim_result.get("timeout", False)),
            "external_checker_error": None,
        }
    )
    return XorDRATBridgeResult(DRATExport(proof_text, drat_status), xor_status)
