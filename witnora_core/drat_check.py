"""Minimal internal RUP-subset checker for Witnora-generated DRAT-style files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import subprocess
from typing import Iterable, Any

from .cnf import CNFFormula, Clause
from .dimacs import parse_dimacs

CHECKER = "witnora_internal_rup_subset_checker_v0.6.1"
CHECKED_AGAINST = "original.dimacs"

ClauseTuple = tuple[int, ...]


def _canonical_clause(literals: Iterable[int]) -> ClauseTuple:
    return Clause(literals).literals


def _parse_proof_line(line: str) -> tuple[bool, ClauseTuple]:
    tokens = line.strip().split()
    if not tokens:
        raise ValueError("empty proof line")
    deletion = tokens[0] == "d"
    if deletion:
        tokens = tokens[1:]
    if not tokens or tokens[-1] != "0":
        raise ValueError("proof line missing terminating 0")
    literals = [int(token) for token in tokens[:-1]]
    return deletion, _canonical_clause(literals)


def parse_drat_text(text: str) -> list[tuple[bool, ClauseTuple]]:
    proof: list[tuple[bool, ClauseTuple]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("c"):
            continue
        proof.append(_parse_proof_line(line))
    return proof


def _unit_propagation_conflicts(
    active: set[ClauseTuple],
    assumptions: list[int],
) -> bool:
    assignment: dict[int, bool] = {}

    def assign(lit: int) -> bool:
        var = abs(lit)
        value = lit > 0
        previous = assignment.get(var)
        if previous is not None:
            return previous == value
        assignment[var] = value
        return True

    for lit in assumptions:
        if not assign(lit):
            return True
    changed = True
    while changed:
        changed = False
        for clause in sorted(active):
            satisfied = False
            unassigned: list[int] = []
            for lit in clause:
                value = assignment.get(abs(lit))
                if value is None:
                    unassigned.append(lit)
                elif value == (lit > 0):
                    satisfied = True
                    break
            if satisfied:
                continue
            if not unassigned:
                return True
            if len(unassigned) == 1:
                if not assign(unassigned[0]):
                    return True
                changed = True
    return False


def is_rup(active: set[ClauseTuple], clause: ClauseTuple) -> bool:
    assumptions = [-lit for lit in clause]
    return _unit_propagation_conflicts(active, assumptions)


def _result(
    *,
    verified: bool,
    empty_clause_derived: bool,
    failed_line: int | None,
    error: str | None,
    warnings: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "verified": verified,
        "checker": CHECKER,
        "checked_against": CHECKED_AGAINST,
        "empty_clause_derived": empty_clause_derived,
        "failed_line": failed_line,
        "error": error,
        "warnings": warnings or [],
    }


def check_drat_text(
    original_formula: CNFFormula,
    proof_text: str,
    *,
    strict_deletions: bool = False,
) -> dict[str, Any]:
    """Check a RUP-subset proof from the original CNF clause database."""

    active = {clause.literals for clause in original_formula.clauses}
    try:
        proof = parse_drat_text(proof_text)
    except Exception as exc:
        return _result(
            verified=False,
            empty_clause_derived=False,
            failed_line=None,
            error=str(exc),
        )

    empty_derived = False
    warnings: list[str] = []
    for line_no, (deletion, clause) in enumerate(proof, start=1):
        if deletion:
            if clause in active:
                active.remove(clause)
            else:
                message = "deletion clause not present in active database"
                if strict_deletions:
                    return _result(
                        verified=False,
                        empty_clause_derived=empty_derived,
                        failed_line=line_no,
                        error=message,
                        warnings=warnings,
                    )
                warnings.append(f"line {line_no}: {message}")
            continue
        if not is_rup(active, clause):
            return _result(
                verified=False,
                empty_clause_derived=empty_derived,
                failed_line=line_no,
                error="addition is not RUP-checkable",
                warnings=warnings,
            )
        active.add(clause)
        if clause == ():
            empty_derived = True
            return _result(
                verified=True,
                empty_clause_derived=True,
                failed_line=None,
                error=None,
                warnings=warnings,
            )

    return _result(
        verified=False,
        empty_clause_derived=empty_derived,
        failed_line=None,
        error="empty clause was not derived",
        warnings=warnings,
    )


def check_drat_files(
    original_dimacs: str | Path,
    proof_drat: str | Path,
    *,
    external_drat_trim: str | Path | None = None,
    strict_deletions: bool = False,
) -> dict[str, Any]:
    formula = parse_dimacs(Path(original_dimacs).read_text(encoding="utf-8"))
    proof_text = Path(proof_drat).read_text(encoding="utf-8")
    result = check_drat_text(formula, proof_text, strict_deletions=strict_deletions)
    result["external_checker"] = "NOT_RUN"
    result["external_checker_verified"] = False
    if external_drat_trim is not None:
        proc = subprocess.run(
            [str(external_drat_trim), str(original_dimacs), str(proof_drat)],
            capture_output=True,
            text=True,
            check=False,
        )
        result["external_checker"] = "DRAT_TRIM"
        result["external_checker_verified"] = proc.returncode == 0
        result["external_checker_returncode"] = proc.returncode
        result["external_checker_stdout"] = proc.stdout
        result["external_checker_stderr"] = proc.stderr
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Witnora internal RUP-subset DRAT checker")
    parser.add_argument("original_dimacs")
    parser.add_argument("proof_drat")
    parser.add_argument("--external-drat-trim")
    args = parser.parse_args(argv)
    result = check_drat_files(
        args.original_dimacs,
        args.proof_drat,
        external_drat_trim=args.external_drat_trim,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result.get("verified") else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
