"""DIMACS import/export with strict validation."""

from __future__ import annotations

from pathlib import Path

from .cnf import CNFFormula, CNFError


class DIMACSError(CNFError):
    """Raised for invalid DIMACS input."""


def parse_dimacs_with_raw(text: str) -> tuple[CNFFormula, list[list[int]]]:
    """Return canonical formula and exact pre-normalization parsed clauses."""
    if not text.strip():
        raise DIMACSError("empty file")

    header_seen = False
    declared_vars: int | None = None
    declared_clauses: int | None = None
    clauses: list[list[int]] = []
    current: list[int] = []

    for line_no, raw_line in enumerate(text.splitlines(), start=1):
        line = raw_line.strip()
        if not line or line.startswith("c"):
            continue
        tokens = line.split()
        if tokens[0] == "p":
            if header_seen:
                raise DIMACSError(f"duplicate header at line {line_no}")
            if len(tokens) != 4 or tokens[1] != "cnf":
                raise DIMACSError(f"invalid header at line {line_no}")
            try:
                declared_vars = int(tokens[2])
                declared_clauses = int(tokens[3])
            except ValueError as exc:
                raise DIMACSError(f"non-integer header value at line {line_no}") from exc
            if declared_vars < 0 or declared_clauses < 0:
                raise DIMACSError("header counts must be non-negative")
            header_seen = True
            continue
        if not header_seen:
            raise DIMACSError(f"missing header before clauses at line {line_no}")
        for token in tokens:
            try:
                lit = int(token)
            except ValueError as exc:
                raise DIMACSError(f"non-integer token {token!r} at line {line_no}") from exc
            if lit == 0:
                clauses.append(current)
                current = []
                continue
            if declared_vars is not None and abs(lit) > declared_vars:
                raise DIMACSError(
                    f"variable id {abs(lit)} exceeds header variable count {declared_vars}"
                )
            current.append(lit)

    if not header_seen:
        raise DIMACSError("invalid or missing header")
    if current:
        raise DIMACSError("missing terminating 0")
    if declared_clauses is not None and len(clauses) != declared_clauses:
        raise DIMACSError(
            f"header declares {declared_clauses} clauses but file contains {len(clauses)}"
        )

    try:
        return CNFFormula.from_raw_clauses(clauses), clauses
    except CNFError as exc:
        raise DIMACSError(str(exc)) from exc


def parse_dimacs(text: str) -> CNFFormula:
    return parse_dimacs_with_raw(text)[0]


def load_dimacs_with_raw(path: str | Path) -> tuple[CNFFormula, list[list[int]]]:
    """Read once; retain the clause parse from the same input bytes."""
    return parse_dimacs_with_raw(Path(path).read_text(encoding="utf-8"))


def load_dimacs(path: str | Path) -> CNFFormula:
    return load_dimacs_with_raw(path)[0]


def export_dimacs(formula: CNFFormula) -> str:
    return formula.canonical_dimacs()
