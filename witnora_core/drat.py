"""Conservative DRAT-style export for supported Witnora UNSAT paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .certificate import CollapsePath, SAT, UNSAT
from .cnf import CNFFormula, Clause, has_tautology
from .drat_check import check_drat_text


@dataclass
class DRATExport:
    proof_text: str | None
    status: dict[str, Any]


def _clause_line(clause: list[int] | tuple[int, ...]) -> str:
    if not clause:
        return "0"
    return " ".join(str(lit) for lit in clause) + " 0"


def _delete_line(clause: list[int] | tuple[int, ...]) -> str:
    if not clause:
        return "d 0"
    return "d " + " ".join(str(lit) for lit in clause) + " 0"


def _canonical(clause: list[int] | tuple[int, ...]) -> tuple[int, ...]:
    return Clause(clause).literals


def _resolve_raw(pos_clause: tuple[int, ...], neg_clause: tuple[int, ...], var: int) -> tuple[int, ...] | None:
    raw = [lit for lit in pos_clause if lit != var] + [
        lit for lit in neg_clause if lit != -var
    ]
    if has_tautology(raw):
        return None
    return Clause(raw).literals


def _base_status(
    export_status: str,
    *,
    supported_reason: str | None = None,
    unsupported_reason: str | None = None,
    internal_verified: bool = False,
    proof_file: str | None = None,
) -> dict[str, Any]:
    return {
        "drat_export_status": export_status,
        "supported_reason": supported_reason,
        "unsupported_reason": unsupported_reason,
        "external_checker": "NOT_RUN",
        "external_checker_verified": False,
        "internal_drat_checker_verified": internal_verified,
        "proof_file": proof_file,
    }


def _active_delete(active: set[tuple[int, ...]], clause: list[int]) -> None:
    active.discard(_canonical(clause))


def _active_add(active: set[tuple[int, ...]], clause: list[int]) -> None:
    active.add(_canonical(clause))


def _export_lines(original_formula: CNFFormula, path: CollapsePath) -> tuple[list[str], str | None]:
    if path.status == SAT:
        return [], "NOT_APPLICABLE_SAT"
    if path.status != UNSAT:
        return [], "NOT_UNSAT"
    if any(
        step.type == "2SAT_SOLVE" and step.details.get("status") == "UNSAT"
        for step in path.steps
    ):
        return [], "2SAT_SCC_TO_DRAT_NOT_IMPLEMENTED"

    active = {clause.literals for clause in original_formula.clauses}
    lines: list[str] = []

    for step in path.steps:
        step_type = step.type
        if step_type == "UP":
            for item in step.details.get("shortened_clauses", []):
                shortened = list(item.get("to", []))
                lines.append(_clause_line(shortened))
                _active_add(active, shortened)
                if shortened == []:
                    return lines, None
            for clause in step.removed_clauses:
                lines.append(_delete_line(clause))
                _active_delete(active, clause)
            continue

        if step_type in {"PLE", "SUB", "BCE"}:
            for clause in step.removed_clauses:
                lines.append(_delete_line(clause))
                _active_delete(active, clause)
            continue

        if step_type == "VE":
            var = int(step.reconstruction_data.get("eliminated_variable", 0))
            if var <= 0:
                return lines, "VE_ELIMINATED_VARIABLE_MISSING"
            pos = sorted(clause for clause in active if var in clause)
            neg = sorted(clause for clause in active if -var in clause)
            expected: set[tuple[int, ...]] = set()
            for pos_clause in pos:
                for neg_clause in neg:
                    resolvent = _resolve_raw(pos_clause, neg_clause, var)
                    if resolvent is not None:
                        expected.add(resolvent)
            logged = {_canonical(clause) for clause in step.added_clauses}
            if expected != logged:
                return lines, "VE_RESOLVENT_LOG_MISMATCH"
            for resolvent in sorted(expected):
                lines.append(_clause_line(resolvent))
                _active_add(active, list(resolvent))
                if resolvent == ():
                    return lines, None
            for clause in step.removed_clauses:
                lines.append(_delete_line(clause))
                _active_delete(active, clause)
            continue

        if step_type in {"CD", "TREEWIDTH_SOLVE"}:
            continue

        if step_type == "2SAT_SOLVE":
            continue

        return lines, f"UNSUPPORTED_STEP_{step_type}"

    if any(clause == () for clause in active):
        lines.append("0")
        return lines, None
    return lines, "NO_EXPLICIT_EMPTY_CLAUSE_DERIVED"


def export_drat_for_path(original_formula: CNFFormula, path: CollapsePath) -> DRATExport:
    lines, unsupported = _export_lines(original_formula, path)
    if unsupported == "NOT_APPLICABLE_SAT":
        return DRATExport(
            None,
            _base_status(
                "NOT_APPLICABLE_SAT",
                unsupported_reason="SAT certificates use assignment verification, not DRAT",
            ),
        )
    if unsupported == "NOT_UNSAT":
        return DRATExport(
            None,
            _base_status("UNSUPPORTED", unsupported_reason="result is not UNSAT"),
        )
    if unsupported is not None:
        return DRATExport(
            None,
            _base_status("UNSUPPORTED", unsupported_reason=unsupported),
        )

    proof_text = "\n".join(lines) + "\n"
    checked = check_drat_text(original_formula, proof_text)
    if not checked.get("verified"):
        return DRATExport(
            proof_text,
            _base_status(
                "FAILED",
                supported_reason="generated proof failed internal RUP-subset check",
                unsupported_reason=str(checked.get("error")),
                internal_verified=False,
                proof_file="proof.drat",
            ),
        )
    return DRATExport(
        proof_text,
        _base_status(
            "EXPORTED",
            supported_reason="RUP-checkable UNSAT path with explicit empty clause",
            internal_verified=True,
            proof_file="proof.drat",
        ),
    )
