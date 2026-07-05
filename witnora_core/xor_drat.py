"""Bounded XOR-to-DRAT bridge for detected-CNF XOR contradictions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from tempfile import TemporaryDirectory
import time
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
XOR_DRAT_SKIPPED_TIME_CAP = "SKIPPED_TIME_CAP"
XOR_DRAT_SKIPPED_PROOF_BYTES_CAP = "SKIPPED_PROOF_BYTES_CAP"
XOR_DRAT_UNSUPPORTED_SIDECAR_ORIGINAL_CNF = "UNSUPPORTED_SIDECAR_ORIGINAL_CNF"
XOR_DRAT_INTERNAL_RUP_FAILED = "INTERNAL_RUP_FAILED"
XOR_DRAT_DRAT_TRIM_FAILED = "DRAT_TRIM_FAILED"
XOR_DRAT_DRAT_TRIM_NOT_AVAILABLE = "DRAT_TRIM_NOT_AVAILABLE"
XOR_DRAT_UNSUPPORTED_XOR_STRUCTURE = "UNSUPPORTED_XOR_STRUCTURE"
INTERNAL_RUP_CHECK_PROOF_CLAUSE_CAP = 20000


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


def _resolve_fast(a: tuple[int, ...], b: tuple[int, ...], pivot: int) -> tuple[int, ...] | None:
    """Resolve two canonical clauses with less allocation in proof generation."""

    literals = set(a)
    literals.discard(pivot)
    for lit in b:
        if lit == -pivot:
            continue
        if -lit in literals:
            return None
        literals.add(lit)
    for lit in tuple(literals):
        if -lit in literals:
            return None
    return tuple(sorted(literals))


def _base_xor_status(
    status: str,
    *,
    proof_base: str | None = None,
    proof_file: str | None = None,
    source: str | None = None,
    reason: str | None = None,
    external_verified: bool = False,
    diagnostics: dict[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "xor_drat_bridge": external_verified,
        "xor_drat_status": status,
        "skip_reason": reason if status != XOR_DRAT_VERIFIED else None,
        "proof_base": proof_base,
        "proof_file": proof_file,
        "source": source,
        "external_drat": external_verified,
        "drat_claim": "EXPORTED_VERIFIED" if external_verified else ("FAILED" if status == XOR_DRAT_FAILED else "NOT_EXPORTED"),
        "xor_native_trace_retained": True,
        "reason": reason,
    }
    if diagnostics:
        payload.update(diagnostics)
    return payload


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


def _max_trace_width(trace: Iterable[dict[str, Any]], detected: Iterable[XorEquation]) -> int:
    widest = max((len(eq.variables) for eq in detected), default=0)
    for item in trace:
        for key in ("variables", "before", "after"):
            if key in item:
                widest = max(widest, len(item[key]))
    return widest


def _xor_rows_from_equations(equations: Iterable[XorEquation]) -> list[tuple[frozenset[int], int]]:
    return [(frozenset(eq.variables), int(eq.rhs) & 1) for eq in equations if eq.variables or eq.rhs]


def _xor_row_key(row: tuple[frozenset[int], int]) -> tuple[tuple[int, ...], int]:
    return (tuple(sorted(row[0])), row[1])


def _sparse_xor_elimination_order(equations: Iterable[XorEquation]) -> tuple[list[int], dict[str, Any]]:
    """Return a deterministic sparse variable order for the XOR contradiction core.

    This is diagnostic/proof-order selection only.  The emitted proof remains
    clause-level and must still pass the internal RUP checker and drat-trim.
    """

    rows = _xor_rows_from_equations(equations)
    order: list[int] = []
    initial_width = max((len(vars_) for vars_, _rhs in rows), default=0)
    peak_width = initial_width
    final_width = 0
    contradiction_seen = any(not vars_ and rhs == 1 for vars_, rhs in rows)

    while rows and not contradiction_seen:
        variables = sorted({var for vars_, _rhs in rows for var in vars_})
        if not variables:
            break
        best: tuple[Any, int, int, list[tuple[frozenset[int], int]], int] | None = None
        for variable in variables:
            containing = [row for row in rows if variable in row[0]]
            if not containing:
                continue
            not_containing = [row for row in rows if variable not in row[0]]
            pivot_options = sorted(containing, key=lambda row: (len(row[0]), _xor_row_key(row)))
            for pivot_index, pivot in enumerate(pivot_options):
                generated: list[tuple[frozenset[int], int]] = []
                seen = { _xor_row_key(row) for row in not_containing }
                local_peak = max((len(row[0]) for row in not_containing), default=0)
                local_contradiction = False
                for other in containing:
                    if other == pivot:
                        continue
                    new_vars = pivot[0] ^ other[0]
                    new_rhs = pivot[1] ^ other[1]
                    local_peak = max(local_peak, len(new_vars))
                    if not new_vars and new_rhs == 1:
                        local_contradiction = True
                    if not new_vars and new_rhs == 0:
                        continue
                    new_row = (frozenset(new_vars), new_rhs)
                    key = _xor_row_key(new_row)
                    if key not in seen:
                        seen.add(key)
                        generated.append(new_row)
                candidate_rows = not_containing + generated
                score = (
                    0 if local_contradiction else 1,
                    local_peak,
                    len(generated),
                    sum(len(row[0]) for row in candidate_rows),
                    len(containing),
                    variable,
                    pivot_index,
                )
                if best is None or score < best[0]:
                    best = (score, variable, pivot_index, candidate_rows, local_peak)
        if best is None:
            break
        _score, variable, _pivot_index, rows, local_peak = best
        order.append(variable)
        peak_width = max(peak_width, local_peak)
        for vars_, rhs in rows:
            if not vars_ and rhs == 1:
                contradiction_seen = True
                final_width = 0
                break

    remaining = sorted({var for vars_, _rhs in rows for var in vars_ if var not in set(order)})
    order.extend(remaining)
    return order, {
        "strategy": "sparse_min_fill",
        "row_width_initial": initial_width,
        "row_width_peak": peak_width,
        "row_width_final_contradiction": final_width,
        "xor_elimination_order": order,
    }


def _proof_order(solution: dict[str, Any], system: XorSystem) -> list[int]:
    pivots = [
        int(item["pivot"])
        for item in solution.get("elimination_trace", [])
        if item.get("type") == "pivot" and "pivot" in item
    ]
    return pivots + [var for var in system.variables if var not in set(pivots)]


def _gaussian_order_stats(solution: dict[str, Any], system: XorSystem, detected: list[XorEquation]) -> dict[str, Any]:
    order = _proof_order(solution, system)
    return {
        "strategy": "gaussian_pivot_order",
        "row_width_initial": max((len(eq.variables) for eq in detected), default=0),
        "row_width_peak": _max_trace_width(solution.get("elimination_trace", []), detected),
        "row_width_final_contradiction": 0 if solution.get("status") == "UNSAT" else None,
        "xor_elimination_order": order,
    }


def _choose_order(solution: dict[str, Any], system: XorSystem, detected: list[XorEquation]) -> dict[str, Any]:
    return _gaussian_order_stats(solution, system, detected)


def _diagnostics(
    original_formula: CNFFormula,
    detected: list[XorEquation],
    *,
    row_width: int = 0,
    max_row_width_cap: int,
    max_proof_clauses: int,
    max_proof_bytes: int,
    timeout_seconds: float | None,
    proof_clause_count_estimate: int = 0,
    proof_clause_count_actual: int = 0,
    proof_clause_max_width: int = 0,
    internal_rup_status: str = "NOT_RUN",
    drat_trim_status: str = "NOT_RUN",
    drat_trim_runtime_seconds: float | None = None,
    proof_file_size_bytes: int = 0,
    proof_generation_runtime_seconds: float | None = None,
    internal_rup_runtime_seconds: float | None = None,
    xor_elimination_order: list[int] | None = None,
    xor_elimination_order_strategy: str | None = None,
    row_width_initial: int | None = None,
    row_width_peak: int | None = None,
    row_width_final_contradiction: int | None = None,
) -> dict[str, Any]:
    return {
        "row_width": int(row_width),
        "max_row_width_cap": int(max_row_width_cap),
        "row_width_initial": int(row_width_initial if row_width_initial is not None else row_width),
        "row_width_peak": int(row_width_peak if row_width_peak is not None else row_width),
        "row_width_final_contradiction": row_width_final_contradiction,
        "xor_elimination_order": list(xor_elimination_order or []),
        "xor_elimination_order_strategy": xor_elimination_order_strategy,
        "proof_clause_count_estimate": int(proof_clause_count_estimate),
        "proof_clause_count_actual": int(proof_clause_count_actual),
        "max_proof_clause_cap": int(max_proof_clauses),
        "max_proof_bytes": int(max_proof_bytes),
        "xor_drat_timeout_seconds": timeout_seconds,
        "proof_generation_runtime_seconds": proof_generation_runtime_seconds,
        "internal_rup_runtime_seconds": internal_rup_runtime_seconds,
        "internal_rup_status": internal_rup_status,
        "drat_trim_status": drat_trim_status,
        "drat_trim_runtime_seconds": drat_trim_runtime_seconds,
        "proof_file_size_bytes": int(proof_file_size_bytes),
        "proof_clause_max_width": int(proof_clause_max_width),
        "original_num_vars": original_formula.num_vars,
        "original_num_clauses": original_formula.num_clauses,
        "detected_xor_equations": len(detected),
        "max_detected_xor_arity": max((len(eq.variables) for eq in detected), default=0),
    }


def _line_size(clause: tuple[int, ...]) -> int:
    return len(_clause_line(clause)) + 1


def _variable_elimination_refutation(
    original_formula: CNFFormula,
    support_clauses: set[tuple[int, ...]],
    order: list[int],
    *,
    max_proof_clauses: int,
    max_proof_bytes: int,
    timeout_seconds: float | None,
) -> tuple[str | None, str | None, dict[str, Any]]:
    active = {clause.literals for clause in original_formula.clauses}
    if not support_clauses <= active:
        return None, "DETECTED_XOR_SOURCE_CLAUSE_MISSING_FROM_ORIGINAL", {
            "proof_clause_count_actual": 0,
            "proof_clause_max_width": 0,
            "proof_file_size_bytes": 0,
        }

    focus = set(support_clauses)
    lines: list[str] = []
    emitted = 0
    proof_bytes = 0
    max_width = 0
    started = time.perf_counter()

    if () in focus:
        return "0\n", None, {
            "proof_clause_count_actual": 1,
            "proof_clause_max_width": 0,
            "proof_file_size_bytes": 2,
        }

    for variable in order:
        if timeout_seconds is not None and time.perf_counter() - started > timeout_seconds:
            return None, XOR_DRAT_SKIPPED_TIME_CAP, {
                "proof_clause_count_actual": emitted,
                "proof_clause_max_width": max_width,
                "proof_file_size_bytes": proof_bytes,
            }
        positive = sorted(clause for clause in focus if variable in clause)
        negative = sorted(clause for clause in focus if -variable in clause)
        if not positive and not negative:
            continue
        for left in positive:
            for right in negative:
                resolvent = _resolve_fast(left, right, variable)
                if resolvent is None:
                    continue
                max_width = max(max_width, len(resolvent))
                if resolvent in focus:
                    continue
                if emitted + 1 > max_proof_clauses:
                    return None, XOR_DRAT_SKIPPED_PROOF_SIZE_CAP, {
                        "proof_clause_count_actual": emitted,
                        "proof_clause_max_width": max_width,
                        "proof_file_size_bytes": proof_bytes,
                    }
                next_size = proof_bytes + _line_size(resolvent)
                if next_size > max_proof_bytes:
                    return None, XOR_DRAT_SKIPPED_PROOF_BYTES_CAP, {
                        "proof_clause_count_actual": emitted,
                        "proof_clause_max_width": max_width,
                        "proof_file_size_bytes": proof_bytes,
                    }
                line = _clause_line(resolvent)
                lines.append(line)
                emitted += 1
                proof_bytes = next_size
                focus.add(resolvent)
                if resolvent == ():
                    return "\n".join(lines) + "\n", None, {
                        "proof_clause_count_actual": emitted,
                        "proof_clause_max_width": max_width,
                        "proof_file_size_bytes": proof_bytes,
                    }
                if timeout_seconds is not None and time.perf_counter() - started > timeout_seconds:
                    return None, XOR_DRAT_SKIPPED_TIME_CAP, {
                        "proof_clause_count_actual": emitted,
                        "proof_clause_max_width": max_width,
                        "proof_file_size_bytes": proof_bytes,
                    }
        for clause in positive:
            focus.discard(clause)
        for clause in negative:
            focus.discard(clause)

    return None, "VARIABLE_ELIMINATION_DID_NOT_DERIVE_EMPTY", {
        "proof_clause_count_actual": emitted,
        "proof_clause_max_width": max_width,
        "proof_file_size_bytes": proof_bytes,
    }


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
    max_proof_bytes: int = 5_000_000,
    timeout_seconds: float | None = 120.0,
) -> XorDRATBridgeResult:
    empty_diagnostics = _diagnostics(
        original_formula,
        [],
        max_row_width_cap=max_row_width,
        max_proof_clauses=max_proof_clauses,
        max_proof_bytes=max_proof_bytes,
        timeout_seconds=timeout_seconds,
    )
    if path.status != XOR_UNSAT_NATIVE:
        xor_status = _base_xor_status("NOT_APPLICABLE", reason="result is not XOR-native UNSAT", diagnostics=empty_diagnostics)
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
            diagnostics={**empty_diagnostics, "drat_trim_status": XOR_DRAT_DRAT_TRIM_NOT_AVAILABLE},
        )
        return XorDRATBridgeResult(
            DRATExport(None, _base_drat_status("UNSUPPORTED", xor_status=xor_status, unsupported_reason=xor_status["reason"])),
            xor_status,
        )

    detected = _detected_equations(path)
    base_diagnostics = _diagnostics(
        original_formula,
        detected,
        max_row_width_cap=max_row_width,
        max_proof_clauses=max_proof_clauses,
        max_proof_bytes=max_proof_bytes,
        timeout_seconds=timeout_seconds,
        proof_clause_count_estimate=sum(1 << max(0, len(eq.variables) - 1) for eq in detected),
    )
    if not detected:
        xor_status = _base_xor_status(
            XOR_DRAT_UNSUPPORTED_SIDECAR_ORIGINAL_CNF,
            reason="XOR contradiction is not implied by detected CNF XOR clauses alone",
            diagnostics=base_diagnostics,
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
            diagnostics=base_diagnostics,
        )
        return XorDRATBridgeResult(
            DRATExport(None, _base_drat_status("UNSUPPORTED", xor_status=xor_status, unsupported_reason=xor_status["reason"])),
            xor_status,
        )

    order_info = _choose_order(detected_solution, XorSystem(detected), detected)
    base_diagnostics.update(
        {
            "row_width": int(order_info["row_width_peak"]),
            "row_width_initial": int(order_info["row_width_initial"]),
            "row_width_peak": int(order_info["row_width_peak"]),
            "row_width_final_contradiction": order_info["row_width_final_contradiction"],
            "xor_elimination_order": list(order_info["xor_elimination_order"]),
            "xor_elimination_order_strategy": order_info["strategy"],
        }
    )
    if int(order_info["row_width_peak"]) > max_row_width:
        xor_status = _base_xor_status(
            XOR_DRAT_SKIPPED_ROW_WIDTH_CAP,
            reason=f"detected XOR row width {order_info['row_width_peak']} exceeds cap {max_row_width}",
            diagnostics=base_diagnostics,
        )
        return XorDRATBridgeResult(
            DRATExport(None, _base_drat_status("UNSUPPORTED", xor_status=xor_status, unsupported_reason=xor_status["reason"])),
            xor_status,
        )

    proof_started = time.perf_counter()
    proof_text, error, proof_stats = _variable_elimination_refutation(
        original_formula,
        _source_clauses(detected),
        list(order_info["xor_elimination_order"]),
        max_proof_clauses=max_proof_clauses,
        max_proof_bytes=max_proof_bytes,
        timeout_seconds=timeout_seconds,
    )
    proof_runtime = round(time.perf_counter() - proof_started, 6)
    proof_diagnostics = {**base_diagnostics, **proof_stats, "proof_generation_runtime_seconds": proof_runtime}
    if error is not None or proof_text is None:
        status_name = error if error in {
            XOR_DRAT_SKIPPED_PROOF_SIZE_CAP,
            XOR_DRAT_SKIPPED_PROOF_BYTES_CAP,
            XOR_DRAT_SKIPPED_TIME_CAP,
        } else XOR_DRAT_FAILED
        xor_status = _base_xor_status(status_name, reason=error, source="detected_cnf_pattern", diagnostics=proof_diagnostics)
        return XorDRATBridgeResult(
            DRATExport(None, _base_drat_status("FAILED" if status_name == XOR_DRAT_FAILED else "UNSUPPORTED", xor_status=xor_status, unsupported_reason=error)),
            xor_status,
        )

    internal_started = time.perf_counter()
    internal = check_drat_text(original_formula, proof_text, strict_deletions=False)
    internal_runtime = round(time.perf_counter() - internal_started, 6)
    if not internal.get("verified"):
        xor_status = _base_xor_status(
            XOR_DRAT_INTERNAL_RUP_FAILED,
            source="detected_cnf_pattern",
            reason=f"internal RUP-subset checker rejected proof: {internal.get('error')}",
            diagnostics={
                **proof_diagnostics,
                "internal_rup_status": str(internal.get("error") or "FAILED"),
                "internal_rup_runtime_seconds": internal_runtime,
            },
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
        trim_started = time.perf_counter()
        trim_result = run_drat_trim(original_path, proof_path, drat_trim_path)
        trim_runtime = round(time.perf_counter() - trim_started, 6)

    if not trim_result.get("external_checker_verified", False):
        xor_status = _base_xor_status(
            XOR_DRAT_DRAT_TRIM_FAILED,
            source="detected_cnf_pattern",
            reason=f"drat-trim did not verify proof: {trim_result.get('error')}",
            diagnostics={
                **proof_diagnostics,
                "internal_rup_status": "VERIFIED",
                "internal_rup_runtime_seconds": internal_runtime,
                "drat_trim_status": "FAILED",
                "drat_trim_runtime_seconds": trim_runtime,
            },
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
        diagnostics={
            **proof_diagnostics,
            "internal_rup_status": "VERIFIED",
            "internal_rup_runtime_seconds": internal_runtime,
            "drat_trim_status": "VERIFIED",
            "drat_trim_runtime_seconds": trim_runtime,
        },
    )
    xor_status["derived_clause_count"] = proof_stats.get("proof_clause_count_actual", 0)
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
