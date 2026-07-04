"""Conservative DRAT-style export for supported Witnora UNSAT paths."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .certificate import CollapsePath, SAT, UNSAT
from .cnf import CNFFormula, Clause, has_tautology
from .drat_check import CHECKED_AGAINST, check_drat_text, is_rup

PROOF_SCOPE_END_TO_END = "END_TO_END_FROM_ORIGINAL_CNF"
PROOF_SCOPE_FINAL_STATE_ONLY_UNSUPPORTED = "FINAL_STATE_ONLY_UNSUPPORTED"


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
    proof_scope: str | None = None,
) -> dict[str, Any]:
    return {
        "drat_export_status": export_status,
        "proof_scope": proof_scope,
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
    }


def _active_delete(active: set[tuple[int, ...]], clause: list[int]) -> str | None:
    canonical = _canonical(clause)
    if canonical not in active:
        return "DELETION_CLAUSE_NOT_ACTIVE"
    active.remove(canonical)
    return None


def _active_add(active: set[tuple[int, ...]], clause: list[int]) -> None:
    active.add(_canonical(clause))


def _append_rup_addition(
    lines: list[str],
    active: set[tuple[int, ...]],
    clause: tuple[int, ...],
) -> str | None:
    if not is_rup(active, clause):
        return "ADDITION_NOT_RUP_CHECKABLE_FROM_ACTIVE_ORIGINAL_PROOF_STATE"
    lines.append(_clause_line(clause))
    _active_add(active, list(clause))
    return None


def _append_deletion(
    lines: list[str],
    active: set[tuple[int, ...]],
    clause: list[int],
) -> str | None:
    error = _active_delete(active, clause)
    if error is not None:
        return error
    lines.append(_delete_line(clause))
    return None


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
                shortened = _canonical(list(item.get("to", [])))
                error = _append_rup_addition(lines, active, shortened)
                if error is not None:
                    return lines, error
                if shortened == ():
                    return lines, None
            for clause in step.removed_clauses:
                error = _append_deletion(lines, active, clause)
                if error is not None:
                    return lines, error
            continue

        if step_type in {"PLE", "SUB", "BCE"}:
            for clause in step.removed_clauses:
                error = _append_deletion(lines, active, clause)
                if error is not None:
                    return lines, error
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
                error = _append_rup_addition(lines, active, resolvent)
                if error is not None:
                    return lines, error
                if resolvent == ():
                    return lines, None
            for clause in step.removed_clauses:
                error = _append_deletion(lines, active, clause)
                if error is not None:
                    return lines, error
            continue

        if step_type in {"CD", "TREEWIDTH_SOLVE"}:
            continue

        if step_type == "2SAT_SOLVE":
            continue

        return lines, f"UNSUPPORTED_STEP_{step_type}"

    if any(clause == () for clause in active):
        error = _append_rup_addition(lines, active, ())
        if error is not None:
            return lines, error
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
                proof_scope=None,
            ),
        )
    if unsupported == "NOT_UNSAT":
        return DRATExport(
            None,
            _base_status(
                "UNSUPPORTED",
                unsupported_reason="result is not UNSAT",
                proof_scope=PROOF_SCOPE_FINAL_STATE_ONLY_UNSUPPORTED,
            ),
        )
    if unsupported is not None:
        return DRATExport(
            None,
            _base_status(
                "UNSUPPORTED",
                unsupported_reason=unsupported,
                proof_scope=PROOF_SCOPE_FINAL_STATE_ONLY_UNSUPPORTED,
            ),
        )

    proof_text = "\n".join(lines) + "\n"
    checked = check_drat_text(original_formula, proof_text, strict_deletions=True)
    if not checked.get("verified"):
        return DRATExport(
            proof_text,
            _base_status(
                "FAILED",
                supported_reason="generated end-to-end proof failed internal RUP-subset check",
                unsupported_reason=str(checked.get("error")),
                internal_verified=False,
                proof_file="proof.drat",
                proof_scope=PROOF_SCOPE_FINAL_STATE_ONLY_UNSUPPORTED,
            ),
        )
    return DRATExport(
        proof_text,
        _base_status(
            "EXPORTED",
            supported_reason="end-to-end RUP-checkable UNSAT path from original CNF",
            internal_verified=True,
            proof_file="proof.drat",
            proof_scope=PROOF_SCOPE_END_TO_END,
        ),
    )
