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
            "safe_use": self.safe_use,
        }


@dataclass(frozen=True)
class XorSystem:
    equations: tuple[XorEquation, ...]

    def __init__(self, equations: Iterable[XorEquation] = ()):
        kept = [eq for eq in equations if not eq.is_tautology]
        object.__setattr__(
            self,
            "equations",
            tuple(sorted(kept, key=lambda eq: (eq.variables, eq.rhs, eq.source))),
        )

    @property
    def variables(self) -> tuple[int, ...]:
        return tuple(sorted({var for eq in self.equations for var in eq.variables}))

    def substitute(self, assignment: dict[int, bool]) -> "XorSystem":
        return XorSystem(eq.substitute(assignment) for eq in self.equations)

    def to_dict(self) -> dict[str, Any]:
        return {
            "equations": [eq.to_dict() for eq in self.equations],
            "variables": list(self.variables),
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
        safe_use=True,
    )


def detect_cnf_xor_patterns(formula: CNFFormula, *, include_3var: bool = True) -> XorSystem:
    clauses = {tuple(clause.literals) for clause in formula.clauses}
    equations: list[XorEquation] = []
    seen: set[tuple[tuple[int, ...], int]] = set()

    variables = formula.variables
    for x, y in itertools.combinations(variables, 2):
        eq0 = (tuple(sorted((x, y))), 0)
        eq1 = (tuple(sorted((x, y))), 1)
        equality_clauses = (tuple(sorted((-x, y))), tuple(sorted((x, -y))))
        disequality_clauses = (tuple(sorted((x, y))), tuple(sorted((-x, -y))))
        if all(clause in clauses for clause in equality_clauses) and eq0 not in seen:
            equations.append(
                _detected_equation((x, y), 0, equality_clauses, clauses)
            )
            seen.add(eq0)
        if all(clause in clauses for clause in disequality_clauses) and eq1 not in seen:
            equations.append(
                _detected_equation((x, y), 1, disequality_clauses, clauses)
            )
            seen.add(eq1)

    if include_3var:
        for triple in itertools.combinations(variables, 3):
            for rhs in (0, 1):
                key = (tuple(triple), rhs)
                if key in seen:
                    continue
                required = tuple(
                    _clause_for_forbidden_assignment(triple, bits)
                    for bits in itertools.product((0, 1), repeat=3)
                    if (bits[0] ^ bits[1] ^ bits[2]) != rhs
                )
                if all(clause in clauses for clause in required):
                    equations.append(
                        _detected_equation(
                            triple,
                            rhs,
                            required,
                            clauses,
                        )
                    )
                    seen.add(key)
    return XorSystem(equations)


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
        },
        "xor_status": {
            "xor_status": solution.get("status"),
            "assignment": solution.get("assignment", {}),
            "forced_assignments": solution.get("forced_assignments", {}),
            "contradiction": solution.get("contradiction"),
            "verified": bool(verified),
            "detected_equations": [eq.to_dict() for eq in detected.equations],
            "external_drat": False,
            "drat_claim": "NOT_EXPORTED",
        },
    }
