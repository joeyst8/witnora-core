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


def _normalize_xor_variables(variables: Iterable[int],
                             *, backend="python") -> tuple[int, ...]:
    """Canonical GF(2) support: validate, toggle occurrence, then sort.

    This mirrors the verified Lean toggle-and-sort model. Only positive
    integer-valued IDs are within the intended domain; the existing int()
    coercion is retained for compatibility and must be treated explicitly
    in a future Python-language refinement proof.
    """
    if backend == "rust":
        from witnora_ve import xor_normalize_variables_native
        normalized = []
        for raw_var in variables:
            var = int(raw_var)
            if var <= 0:
                raise ValueError(f"XOR variable IDs must be positive: {raw_var!r}")
            normalized.append(var)
        return tuple(xor_normalize_variables_native(normalized))
    if backend != "python":
        raise ValueError("unknown XOR backend")
    active: set[int] = set()
    for raw_var in variables:
        var = int(raw_var)
        if var <= 0:
            raise ValueError(f"XOR variable IDs must be positive: {raw_var!r}")
        if var in active:
            active.remove(var)
        else:
            active.add(var)
    return tuple(sorted(active))


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
        canonical = _normalize_xor_variables(variables)
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

    def evaluate(self, assignment: dict[int, bool], *, backend="python") -> bool | None:
        if backend == "rust":
            from witnora_ve import xor_evaluate_native
            return xor_evaluate_native(list(self.variables), self.rhs,
                                       [(v, bool(assignment[v]))
                                        for v in self.variables if v in assignment])
        if backend != "python":
            raise ValueError("unknown XOR backend")
        value = self.rhs
        for var in self.variables:
            if var not in assignment:
                return None
            value ^= int(bool(assignment[var]))
        return value == 0

    def substitute(self, assignment: dict[int, bool], *, backend="python") -> "XorEquation":
        if backend == "rust":
            from witnora_ve import xor_substitute_native
            remaining, rhs = xor_substitute_native(
                list(self.variables), self.rhs,
                [(v, bool(assignment[v])) for v in self.variables
                 if v in assignment])
            return XorEquation(
                remaining, rhs, source=self.source,
                source_clauses=self.source_clauses,
                pattern_size=self.pattern_size,
                detection_mode=self.detection_mode,
                source_clauses_removed=self.source_clauses_removed,
                extra_clauses_touching_variables=self.extra_clauses_touching_variables,
                exact_full_encoding=self.exact_full_encoding,
                safe_use=self.safe_use)
        if backend != "python":
            raise ValueError("unknown XOR backend")
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

    def substitute(self, assignment: dict[int, bool], *, backend="python") -> "XorSystem":
        if backend == "rust":
            from witnora_ve import xor_system_substitute_native
            relevant = sorted({v for eq in self.equations for v in eq.variables})
            bindings = [(v, bool(assignment[v])) for v in relevant if v in assignment]
            results = xor_system_substitute_native(
                [(list(eq.variables), eq.rhs) for eq in self.equations], bindings)
            updated = []
            for eq, (variables, rhs) in zip(self.equations, results):
                updated.append(XorEquation(
                    variables, rhs, source=eq.source,
                    source_clauses=eq.source_clauses,
                    pattern_size=eq.pattern_size,
                    detection_mode=eq.detection_mode,
                    source_clauses_removed=eq.source_clauses_removed,
                    extra_clauses_touching_variables=eq.extra_clauses_touching_variables,
                    exact_full_encoding=eq.exact_full_encoding,
                    safe_use=eq.safe_use))
            return XorSystem(updated, diagnostics=self.diagnostics)
        if backend != "python":
            raise ValueError("unknown XOR backend")
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


def parse_xor_lines(text: str, *, backend="python") -> XorSystem:
    if backend == "rust":
        from witnora_ve import xor_parse_lines_native
        return XorSystem(XorEquation(variables, rhs, source="sidecar")
                         for variables, rhs in xor_parse_lines_native(text))
    if backend != "python":
        raise ValueError("unknown XOR backend")
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


def solve_xor_system_gaussian(system: XorSystem, *, backend="python") -> dict[str, Any]:
    if backend == "rust":
        from witnora_ve import xor_gaussian_native
        (unsat, assignment, pivots, free, forced,
         events, rref) = xor_gaussian_native(
             [(list(eq.variables), eq.rhs) for eq in system.equations])
        trace = []
        for kind, first, second, before, after, rhs in events:
            if kind == 0:
                trace.append({"type": "input_row", "row_index": first,
                              "variables": before, "rhs": rhs})
            elif kind == 1:
                trace.append({"type": "pivot", "pivot": first,
                              "variables": before, "rhs": rhs})
            elif kind == 2:
                trace.append({"type": "xor_eliminate", "pivot": first,
                              "before": before, "after": after, "rhs": rhs})
            elif kind == 3:
                trace.append({"type": "contradiction", "row_index": first})
            elif kind == 4:
                trace.append({"type": "back_eliminate", "pivot": first,
                              "using": second, "variables": before, "rhs": rhs})
            else:
                raise AssertionError("unknown native XOR trace event")
        if unsat:
            return {"status": XOR_UNSAT, "assignment": {}, "rank": len(pivots),
                    "pivot_variables": pivots, "free_variables": [],
                    "forced_assignments": {}, "elimination_trace": trace,
                    "contradiction": {"variables": [], "rhs": 1}}
        return {"status": XOR_SAT,
                "assignment": {str(v): bool(value) for v, value in assignment},
                "rank": len(pivots), "pivot_variables": pivots,
                "free_variables": free,
                "forced_assignments": {str(v): bool(bit) for v, bit in forced},
                "elimination_trace": trace,
                "rref_rows": [{"pivot": p, "variables": vs, "rhs": rhs}
                              for p, vs, rhs in rref]}
    if backend != "python":
        raise ValueError("unknown XOR backend")
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


def verify_xor_assignment(system: XorSystem, assignment: dict[int, bool],
                          *, backend="python") -> bool:
    if backend == "rust":
        from witnora_ve import xor_verify_assignment_native
        bindings = [(v, bool(assignment[v])) for v in system.variables
                    if v in assignment]
        return xor_verify_assignment_native(
            [(list(eq.variables), eq.rhs) for eq in system.equations], bindings)
    if backend != "python":
        raise ValueError("unknown XOR backend")
    return all(eq.evaluate(assignment) is True for eq in system.equations)


def _clause_for_forbidden_assignment(variables: tuple[int, ...], bits: tuple[int, ...]) -> tuple[int, ...]:
    return tuple(sorted((-var if bit else var) for var, bit in zip(variables, bits)))


def canonical_xor_cnf_clauses(variables: Iterable[int], rhs: int,
                              *, backend="python", max_native_variables=16) -> set[tuple[int, ...]]:
    """Return the exact full CNF encoding of a positive-variable XOR equation."""

    canonical = _normalize_xor_variables(variables)
    target_rhs = int(rhs) & 1
    if backend == "rust":
        from witnora_ve import xor_canonical_cnf_native
        return {tuple(clause) for clause in xor_canonical_cnf_native(
            list(canonical), target_rhs, max_native_variables)}
    if backend != "python":
        raise ValueError("unknown XOR backend")
    if not canonical:
        # XOR over no variables is 0: 0=0 is tautological, 0=1 requires
        # the empty CNF clause (the canonical contradiction).
        return {()} if target_rhs else set()
    return {
        _clause_for_forbidden_assignment(canonical, bits)
        for bits in itertools.product((0, 1), repeat=len(canonical))
        if sum(bits) % 2 != target_rhs
    }


def _extra_touching_clauses(
    formula_clauses: set[tuple[int, ...]],
    variables: tuple[int, ...],
    source_clauses: Iterable[tuple[int, ...]],
    *, backend="python",
) -> tuple[tuple[int, ...], ...]:
    if backend == "rust":
        from witnora_ve import xor_extra_touching_clauses_native
        return tuple(tuple(clause) for clause in xor_extra_touching_clauses_native(
            [list(clause) for clause in formula_clauses], list(variables),
            [list(clause) for clause in source_clauses]))
    if backend != "python":
        raise ValueError("unknown XOR backend")
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
    *, backend="python",
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
            backend=backend,
        ),
        exact_full_encoding=True,
        safe_use=True,
    )


def detect_cnf_xor_patterns(
    formula: CNFFormula,
    *,
    include_3var: bool = True,
    max_k: int = 6,
    backend="python",
) -> XorSystem:
    if backend not in ("python", "rust", "rust_full"):
        raise ValueError("unknown XOR backend")
    clauses = {tuple(clause.literals) for clause in formula.clauses}
    equations: list[XorEquation] = []
    diagnostics: list[dict[str, Any]] = []
    seen: set[tuple[tuple[int, ...], int]] = set()

    if max_k < 2:
        return XorSystem(diagnostics=[{"reason": XOR_PATTERN_SKIPPED_MAX_K, "max_k": int(max_k)}])
    if backend == "rust_full":
        from witnora_ve import xor_detect_cnf_patterns_native
        found, native_diagnostics = xor_detect_cnf_patterns_native(
            [list(clause) for clause in clauses], include_3var, max_k)
        equations = [XorEquation(
            variables, rhs, source="detected_cnf_pattern",
            source_clauses=source_clauses, pattern_size=len(variables),
            detection_mode=XOR_DETECTION_IMPLIED_ONLY,
            source_clauses_removed=False,
            extra_clauses_touching_variables=extra,
            exact_full_encoding=True, safe_use=True)
            for variables, rhs, source_clauses, extra in found]
        diagnostics = []
        for kind, variables, k, fourth, fifth in native_diagnostics:
            if kind == 0:
                diagnostics.append({"reason": XOR_PATTERN_SKIPPED_MAX_K,
                                    "variables": variables, "pattern_size": k,
                                    "max_k": fourth, "clause_count": fifth})
            elif kind == 1:
                diagnostics.append({"reason": "XOR_PATTERN_NOT_EXACT_FULL_ENCODING",
                                    "variables": variables, "pattern_size": k,
                                    "expected_clause_count": fourth,
                                    "actual_clause_count": fifth})
            else:
                raise AssertionError("unknown native XOR diagnostic")
        return XorSystem(equations, diagnostics=diagnostics)
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
            required = canonical_xor_cnf_clauses(variables, rhs, backend=backend)
            if group == required:
                equations.append(
                    _detected_equation(
                        variables,
                        rhs,
                        required,
                        clauses,
                        backend=backend,
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
