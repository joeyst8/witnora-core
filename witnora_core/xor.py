"""Conservative XOR/affine reasoning over GF(2)."""

from __future__ import annotations

from dataclasses import dataclass, field
import itertools
from typing import Any, Iterable

from .cnf import CNFFormula, Clause

XOR_SAT = "SAT"
XOR_UNSAT = "UNSAT"
XOR_DETECTION_IMPLIED_ONLY = "IMPLIED_CONSTRAINT_ONLY"
XOR_DETECTION_SIDECAR = "EXPLICIT_SIDECAR"
XOR_PATTERN_SKIPPED_MAX_K = "XOR_PATTERN_SKIPPED_MAX_K"


@dataclass(frozen=True)
class XorEquation:
    variables: tuple[int, ...]
    rhs: int
    source: str = "sidecar"
    source_clauses: tuple[tuple[int, ...], ...] = field(default_factory=tuple)
    pattern_size: int | None = None
    detection_mode: str = XOR_DETECTION_SIDECAR
    source_clauses_removed: bool = False
    extra_clauses_touching_variables: tuple[tuple[int, ...], ...] = field(default_factory=tuple)
    exact_full_encoding: bool = False
    safe_use: bool = True

    def __init__(
        self,
        variables: Iterable[int],
        rhs: int,
        *,
        source: str = "sidecar",
        source_clauses: Iterable[Iterable[int]] = (),
        pattern_size: int | None = None,
        detection_mode: str | None = None,
        source_clauses_removed: bool = False,
        extra_clauses_touching_variables: Iterable[Iterable[int]] = (),
        exact_full_encoding: bool = False,
        safe_use: bool = True,
    ):
        counts: dict[int, int] = {}
        for var in variables:
            if int(var) <= 0:
                raise ValueError(f"XOR variable IDs must be positive: {var!r}")
            counts[int(var)] = counts.get(int(var), 0) ^ 1
        canonical = tuple(sorted(var for var, parity in counts.items() if parity))
        object.__setattr__(self, "variables", canonical)
        object.__setattr__(self, "rhs", int(rhs) & 1)
        object.__setattr__(self, "source", source)
        object.__setattr__(
            self,
            "source_clauses",
            tuple(tuple(sorted(int(lit) for lit in clause)) for clause in source_clauses),
        )
        object.__setattr__(self, "pattern_size", pattern_size)
        object.__setattr__(
            self,
            "detection_mode",
            detection_mode or (XOR_DETECTION_IMPLIED_ONLY if source == "detected_cnf_pattern" else XOR_DETECTION_SIDECAR),
        )
        object.__setattr__(self, "source_clauses_removed", bool(source_clauses_removed))
        object.__setattr__(
            self,
            "extra_clauses_touching_variables",
            tuple(
                tuple(sorted(int(lit) for lit in clause))
                for clause in extra_clauses_touching_variables
            ),
        )
        object.__setattr__(self, "exact_full_encoding", bool(exact_full_encoding))
        object.__setattr__(self, "safe_use", bool(safe_use))

    @property
    def is_tautology(self) -> bool:
        return not self.variables and self.rhs == 0

    @property
    def is_contradiction(self) -> bool:
        return not self.variables and self.rhs == 1

    def evaluate(self, assignment: dict[int, bool]) -> bool | None:
        value = self.rhs
        for var in self.variables:
            if var not in assignment:
                return None
            value ^= int(bool(assignment[var]))
        return value == 0

    def substitute(self, assignment: dict[int, bool]) -> "XorEquation":
        rhs = self.rhs
        remaining: list[int] = []
        for var in self.variables:
            if var in assignment:
                rhs ^= int(bool(assignment[var]))
            else:
                remaining.append(var)
        return XorEquation(
            remaining,
            rhs,
            source=self.source,
            source_clauses=self.source_clauses,
            pattern_size=self.pattern_size,
            detection_mode=self.detection_mode,
            source_clauses_removed=self.source_clauses_removed,
            extra_clauses_touching_variables=self.extra_clauses_touching_variables,
            exact_full_encoding=self.exact_full_encoding,
            safe_use=self.safe_use,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "variables": list(self.variables),
            "rhs": self.rhs,
            "source": self.source,
            "pattern_size": self.pattern_size,
            "source_clauses": [list(clause) for clause in self.source_clauses],
            "detection_mode": self.detection_mode,
            "source_clauses_removed": self.source_clauses_removed,
            "extra_clauses_touching_variables": [
                list(clause) for clause in self.extra_clauses_touching_variables
            ],
            "exact_full_encoding": self.exact_full_encoding,
            "safe_use": self.safe_use,
        }


@dataclass(frozen=True)
class XorSystem:
    equations: tuple[XorEquation, ...]
    diagnostics: tuple[dict[str, Any], ...]

    def __init__(
        self,
        equations: Iterable[XorEquation] = (),
        diagnostics: Iterable[dict[str, Any]] = (),
    ):
        kept = [eq for eq in equations if not eq.is_tautology]
        object.__setattr__(
            self,
            "equations",
            tuple(sorted(kept, key=lambda eq: (eq.variables, eq.rhs, eq.source))),
        )
        object.__setattr__(
            self,
            "diagnostics",
            tuple(sorted((dict(item) for item in diagnostics), key=lambda item: repr(sorted(item.items())))),
        )

    @property
    def variables(self) -> tuple[int, ...]:
        return tuple(sorted({var for eq in self.equations for var in eq.variables}))

    def substitute(self, assignment: dict[int, bool]) -> "XorSystem":
        return XorSystem(
            (eq.substitute(assignment) for eq in self.equations),
            diagnostics=self.diagnostics,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "equations": [eq.to_dict() for eq in self.equations],
            "variables": list(self.variables),
            "diagnostics": list(self.diagnostics),
        }


def parse_xor_lines(text: str) -> XorSystem:
    equations: list[XorEquation] = []
    for line_number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("c "):
            continue
        parts = line.replace("=", " = ").split()
        if len(parts) < 4 or parts[0] != "xor" or "=" not in parts:
            raise ValueError(f"invalid XOR line {line_number}: {raw!r}")
        eq_index = parts.index("=")
        if eq_index == 1 or eq_index != len(parts) - 2:
            raise ValueError(f"invalid XOR line {line_number}: {raw!r}")
        variables = [int(token) for token in parts[1:eq_index]]
        rhs = int(parts[-1])
        if rhs not in {0, 1}:
            raise ValueError(f"invalid XOR rhs on line {line_number}: {rhs!r}")
        equations.append(XorEquation(variables, rhs, source="sidecar"))
    return XorSystem(equations)


def _xor_rows(a: tuple[set[int], int], b: tuple[set[int], int]) -> tuple[set[int], int]:
    return (set(a[0]) ^ set(b[0]), a[1] ^ b[1])


def solve_xor_system_gaussian(system: XorSystem) -> dict[str, Any]:
    rows: list[tuple[set[int], int]] = [
        (set(eq.variables), eq.rhs) for eq in system.equations
    ]
    pivot_rows: dict[int, tuple[set[int], int]] = {}
    trace: list[dict[str, Any]] = []

    for index, original in enumerate(rows):
        row = (set(original[0]), original[1])
        trace.append({"type": "input_row", "row_index": index, "variables": sorted(row[0]), "rhs": row[1]})
        while row[0]:
            pivot = min(row[0])
            if pivot not in pivot_rows:
                pivot_rows[pivot] = (set(row[0]), row[1])
                trace.append({"type": "pivot", "pivot": pivot, "variables": sorted(row[0]), "rhs": row[1]})
                break
            before = sorted(row[0])
            row = _xor_rows(row, pivot_rows[pivot])
            trace.append(
                {
                    "type": "xor_eliminate",
                    "pivot": pivot,
                    "before": before,
                    "after": sorted(row[0]),
                    "rhs": row[1],
                }
            )
        if not row[0] and row[1] == 1:
            trace.append({"type": "contradiction", "row_index": index})
            return {
                "status": XOR_UNSAT,
                "assignment": {},
                "rank": len(pivot_rows),
                "pivot_variables": sorted(pivot_rows),
                "free_variables": [],
                "forced_assignments": {},
                "elimination_trace": trace,
                "contradiction": {"variables": [], "rhs": 1},
            }

    # Reduced row echelon form for deterministic assignments and forced values.
    for pivot in sorted(pivot_rows, reverse=True):
        row = pivot_rows[pivot]
        for higher in sorted((p for p in pivot_rows if p > pivot), reverse=True):
            if higher in row[0]:
                row = _xor_rows(row, pivot_rows[higher])
                trace.append(
                    {
                        "type": "back_eliminate",
                        "pivot": pivot,
                        "using": higher,
                        "variables": sorted(row[0]),
                        "rhs": row[1],
                    }
                )
        pivot_rows[pivot] = row

    pivots = sorted(pivot_rows)
    free = sorted(set(system.variables) - set(pivots))
    assignment: dict[int, bool] = {var: False for var in free}
    for pivot in sorted(pivots, reverse=True):
        variables, rhs = pivot_rows[pivot]
        value = rhs
        for var in variables:
            if var == pivot:
                continue
            value ^= int(assignment.get(var, False))
        assignment[pivot] = bool(value)
    forced = {
        pivot: bool(rhs)
        for pivot, (variables, rhs) in pivot_rows.items()
        if variables == {pivot}
    }
    return {
        "status": XOR_SAT,
        "assignment": {str(var): bool(assignment[var]) for var in sorted(assignment)},
        "rank": len(pivots),
        "pivot_variables": pivots,
        "free_variables": free,
        "forced_assignments": {str(var): value for var, value in sorted(forced.items())},
        "elimination_trace": trace,
        "rref_rows": [
            {"pivot": pivot, "variables": sorted(pivot_rows[pivot][0]), "rhs": pivot_rows[pivot][1]}
            for pivot in pivots
        ],
    }


def reconstruct_assignment(solution: dict[str, Any]) -> dict[int, bool]:
    return {int(var): bool(value) for var, value in solution.get("assignment", {}).items()}


def verify_xor_assignment(system: XorSystem, assignment: dict[int, bool]) -> bool:
    return all(eq.evaluate(assignment) is True for eq in system.equations)


def _clause_for_forbidden_assignment(variables: tuple[int, ...], bits: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted((-var if bit else var) for var, bit in zip(variables, bits)))


def canonical_xor_cnf_clauses(variables: Iterable[int], rhs: int) -> set[tuple[int, ...]]:
    """Return the exact full CNF encoding of a positive-variable XOR equation."""

    canonical = tuple(sorted({int(var) for var in variables}))
    if any(var <= 0 for var in canonical):
        raise ValueError("XOR CNF variables must be positive")
    if not canonical:
        return set()
    target_rhs = int(rhs) & 1
    return {
        _clause_for_forbidden_assignment(canonical, bits)
        for bits in itertools.product((0, 1), repeat=len(canonical))
        if sum(bits) % 2 != target_rhs
    }


def _extra_touching_clauses(
    formula_clauses: set[tuple[int, ...]],
    variables: tuple[int, ...],
    source_clauses: Iterable[tuple[int, ...]],
) -> tuple[tuple[int, ...], ...]:
    variable_set = set(variables)
    source_set = set(source_clauses)
    return tuple(
        sorted(
            clause
            for clause in formula_clauses
            if clause not in source_set and any(abs(lit) in variable_set for lit in clause)
        )
    )


def _detected_equation(
    variables: tuple[int, ...],
    rhs: int,
    source_clauses: Iterable[tuple[int, ...]],
    formula_clauses: set[tuple[int, ...]],
) -> XorEquation:
    source_tuple = tuple(sorted(source_clauses))
    return XorEquation(
        variables,
        rhs,
        source="detected_cnf_pattern",
        source_clauses=source_tuple,
        pattern_size=len(variables),
        detection_mode=XOR_DETECTION_IMPLIED_ONLY,
        source_clauses_removed=False,
        extra_clauses_touching_variables=_extra_touching_clauses(
            formula_clauses,
            variables,
            source_tuple,
        ),
        exact_full_encoding=True,
        safe_use=True,
    )


def detect_cnf_xor_patterns(
    formula: CNFFormula,
    *,
    include_3var: bool = True,
    max_k: int = 6,
) -> XorSystem:
    clauses = {tuple(clause.literals) for clause in formula.clauses}
    equations: list[XorEquation] = []
    diagnostics: list[dict[str, Any]] = []
    seen: set[tuple[tuple[int, ...], int]] = set()

    if max_k < 2:
        return XorSystem(diagnostics=[{"reason": XOR_PATTERN_SKIPPED_MAX_K, "max_k": int(max_k)}])
    effective_max_k = int(max_k)
    if not include_3var:
        effective_max_k = min(effective_max_k, 2)

    groups: dict[tuple[int, ...], set[tuple[int, ...]]] = {}
    for clause in clauses:
        variables = tuple(sorted({abs(lit) for lit in clause}))
        if len(variables) != len(clause):
            continue
        groups.setdefault(variables, set()).add(clause)

    for variables, group in sorted(groups.items()):
        k = len(variables)
        if k < 2:
            continue
        if k > effective_max_k:
            diagnostics.append(
                {
                    "reason": XOR_PATTERN_SKIPPED_MAX_K,
                    "variables": list(variables),
                    "pattern_size": k,
                    "max_k": effective_max_k,
                    "clause_count": len(group),
                }
            )
            continue
        expected_count = 1 << (k - 1)
        if len(group) != expected_count:
            diagnostics.append(
                {
                    "reason": "XOR_PATTERN_NOT_EXACT_FULL_ENCODING",
                    "variables": list(variables),
                    "pattern_size": k,
                    "expected_clause_count": expected_count,
                    "actual_clause_count": len(group),
                }
            )
            continue
        for rhs in (0, 1):
            key = (variables, rhs)
            if key in seen:
                continue
            required = canonical_xor_cnf_clauses(variables, rhs)
            if group == required:
                equations.append(
                    _detected_equation(
                        variables,
                        rhs,
                        required,
                        clauses,
                    )
                )
                seen.add(key)
                break
        else:
            diagnostics.append(
                {
                    "reason": "XOR_PATTERN_NOT_EXACT_FULL_ENCODING",
                    "variables": list(variables),
                    "pattern_size": k,
                    "expected_clause_count": expected_count,
                    "actual_clause_count": len(group),
                }
            )
    return XorSystem(equations, diagnostics=diagnostics)


def xor_metadata(
    system: XorSystem,
    solution: dict[str, Any],
    *,
    verified: bool,
    detected_system: XorSystem | None = None,
) -> dict[str, Any]:
    detected = detected_system or XorSystem()
    return {
        "xor_system": system.to_dict(),
        "xor_trace": {
            "gaussian_elimination_trace": solution.get("elimination_trace", []),
            "rank": solution.get("rank", 0),
            "pivot_variables": solution.get("pivot_variables", []),
            "free_variables": solution.get("free_variables", []),
            "rref_rows": solution.get("rref_rows", []),
            "detected_diagnostics": list(detected.diagnostics),
        },
        "xor_status": {
            "xor_status": solution.get("status"),
            "assignment": solution.get("assignment", {}),
            "forced_assignments": solution.get("forced_assignments", {}),
            "contradiction": solution.get("contradiction"),
            "verified": bool(verified),
            "detected_equations": [eq.to_dict() for eq in detected.equations],
            "detected_diagnostics": list(detected.diagnostics),
            "external_drat": False,
            "drat_claim": "NOT_EXPORTED",
        },
    }
