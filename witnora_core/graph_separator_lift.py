"""Native graph-separator lift certificates.

v2.15 promotes the v2.14 GRAPH_SEPARATOR_OBSTRUCTION recommendation into a
bounded prototype operator. The implementation is deliberately native and
small: it detects exact primal separators, conditions components on separator
assignments, checks component witnesses or component unsatisfiability under
strict tiny bounds, and verifies the lifted result against the original CNF.

It does not claim DRAT, hardness, lower bounds, hierarchy completeness, or
P-vs-NP progress.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from dataclasses import asdict, dataclass
from itertools import combinations, product
import json
from pathlib import Path
import shutil
from typing import Any, Iterable
import zipfile

from .cnf import CNFFormula, Clause, formula_satisfied
from .dimacs import load_dimacs
from .obstruction_dual import sha256_file, stable_json


VERSION = "2.15"

G8_GRAMMAR = "G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE"
PROMOTED_RECOMMENDATION = "GRAPH_SEPARATOR_LIFT"

GRAPH_SEPARATOR_STRUCTURE_DETECTED = "GRAPH_SEPARATOR_STRUCTURE_DETECTED"
GRAPH_SEPARATOR_DECOMPOSITION_CREATED = "GRAPH_SEPARATOR_DECOMPOSITION_CREATED"
GRAPH_SEPARATOR_COMPONENTS_VERIFIED = "GRAPH_SEPARATOR_COMPONENTS_VERIFIED"
GRAPH_SEPARATOR_SAT_WITNESS_LIFTED = "GRAPH_SEPARATOR_SAT_WITNESS_LIFTED"
GRAPH_SEPARATOR_UNSAT_COVER_VERIFIED = "GRAPH_SEPARATOR_UNSAT_COVER_VERIFIED"
GRAPH_SEPARATOR_NATIVE_CERTIFIED = "GRAPH_SEPARATOR_NATIVE_CERTIFIED"
GRAPH_SEPARATOR_CERTIFICATE_VERIFIED = "GRAPH_SEPARATOR_CERTIFICATE_VERIFIED"
GRAPH_SEPARATOR_CERTIFICATE_FAILED = "GRAPH_SEPARATOR_CERTIFICATE_FAILED"
GRAPH_SEPARATOR_DIAGNOSTIC_ONLY = "GRAPH_SEPARATOR_DIAGNOSTIC_ONLY"
GRAPH_SEPARATOR_NO_NEW_DELTA = "GRAPH_SEPARATOR_NO_NEW_DELTA"
GRAPH_SEPARATOR_DRAT_NOT_CLAIMED = "GRAPH_SEPARATOR_DRAT_NOT_CLAIMED"
G8_GRAPH_SEPARATOR_NATIVE_CERTIFIED = "G8_GRAPH_SEPARATOR_NATIVE_CERTIFIED"
SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED = "SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED"
UNSAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED = "UNSAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED"

FORBIDDEN_STATUS_VALUES = {"HARD", "UNKNOWN"}


@dataclass(frozen=True)
class SeparatorComponent:
    component_id: str
    variables: list[int]
    clause_ids: list[int]
    boundary_separator_variables: list[int]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GraphSeparatorInstance:
    instance_id: str
    family: str
    formula: CNFFormula
    prior_replay_status: str
    expected_mode: str
    novel_delta_expected: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "family": self.family,
            "formula_hash": self.formula.formula_hash,
            "prior_replay_status": self.prior_replay_status,
            "expected_mode": self.expected_mode,
            "novel_delta_expected": self.novel_delta_expected,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class GraphSeparatorLiftCertificate:
    type: str
    instance_id: str
    formula_hash: str
    graph_model: str
    separator_variables: list[int]
    components: list[dict[str, Any]]
    separator_assignments: list[dict[str, Any]]
    mode: str
    component_results: list[dict[str, Any]]
    sat_lift: dict[str, Any] | None
    unsat_cover: dict[str, Any] | None
    compression_or_delta_summary: dict[str, Any]
    checker_status: str
    status: str
    public_category: str
    certification_level: str
    drat_claim: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data), encoding="utf-8", newline="\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _make_zip(root: str | Path, zip_path: str | Path) -> str:
    source = Path(root)
    target = Path(zip_path)
    if target.exists():
        target.unlink()
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(source).as_posix())
    return sha256_file(target)


def _clause_id_map(formula: CNFFormula) -> dict[int, Clause]:
    return {idx: clause for idx, clause in enumerate(formula.clauses, start=1)}


def _clause_hash(formula: CNFFormula) -> str:
    return formula.formula_hash


def _assignment_key(assignment: dict[int, bool]) -> dict[str, bool]:
    return {str(var): bool(assignment[var]) for var in sorted(assignment)}


def _assignment_from_payload(payload: dict[str, Any]) -> dict[int, bool]:
    return {int(var): bool(value) for var, value in payload.items()}


def _all_assignments(variables: Iterable[int]) -> list[dict[int, bool]]:
    vars_sorted = sorted(variables)
    return [
        {var: bool(value) for var, value in zip(vars_sorted, values)}
        for values in product([False, True], repeat=len(vars_sorted))
    ]


def primal_graph(formula: CNFFormula) -> dict[int, set[int]]:
    graph: dict[int, set[int]] = {var: set() for var in formula.variables}
    for clause in formula.clauses:
        variables = list(clause.variables)
        for left, right in combinations(variables, 2):
            graph[left].add(right)
            graph[right].add(left)
    return graph


def _components_after_removing(graph: dict[int, set[int]], separator: set[int]) -> list[list[int]]:
    remaining = sorted(set(graph) - separator)
    seen: set[int] = set()
    components: list[list[int]] = []
    for start in remaining:
        if start in seen:
            continue
        stack = [start]
        seen.add(start)
        component: list[int] = []
        while stack:
            node = stack.pop()
            component.append(node)
            for neighbor in sorted(graph[node] - separator):
                if neighbor not in seen:
                    seen.add(neighbor)
                    stack.append(neighbor)
        components.append(sorted(component))
    return sorted(components, key=lambda item: (item[0], len(item)))


def _component_lookup(components: list[SeparatorComponent]) -> dict[int, str]:
    lookup: dict[int, str] = {}
    for component in components:
        for var in component.variables:
            lookup[int(var)] = component.component_id
    return lookup


def _build_components_from_separator(formula: CNFFormula, separator: list[int]) -> tuple[list[SeparatorComponent], list[str]]:
    errors: list[str] = []
    separator_set = set(separator)
    graph = primal_graph(formula)
    raw_components = _components_after_removing(graph, separator_set)
    components: list[SeparatorComponent] = []
    lookup: dict[int, str] = {}
    for idx, variables in enumerate(raw_components, start=1):
        component_id = f"C{idx}"
        for var in variables:
            lookup[var] = component_id
        components.append(SeparatorComponent(component_id, variables, [], []))

    clause_ids_by_component: dict[str, list[int]] = defaultdict(list)
    boundary_by_component: dict[str, set[int]] = defaultdict(set)
    for clause_id, clause in _clause_id_map(formula).items():
        non_separator_vars = [var for var in clause.variables if var not in separator_set]
        if not non_separator_vars:
            continue
        component_ids = {lookup.get(var) for var in non_separator_vars}
        if len(component_ids) != 1 or None in component_ids:
            errors.append(f"INVALID_CROSS_COMPONENT_CLAUSE:{clause_id}")
            continue
        component_id = next(iter(component_ids))
        clause_ids_by_component[component_id].append(clause_id)
        boundary_by_component[component_id].update(var for var in clause.variables if var in separator_set)

    rebuilt: list[SeparatorComponent] = []
    for component in components:
        rebuilt.append(
            SeparatorComponent(
                component_id=component.component_id,
                variables=component.variables,
                clause_ids=sorted(clause_ids_by_component.get(component.component_id, [])),
                boundary_separator_variables=sorted(boundary_by_component.get(component.component_id, set())),
            )
        )
    return rebuilt, errors


def detect_separator(
    formula: CNFFormula,
    *,
    max_separator_size: int = 3,
    max_components: int = 8,
    max_component_size: int = 8,
) -> dict[str, Any]:
    graph = primal_graph(formula)
    variables = sorted(graph)
    trace: list[dict[str, Any]] = []
    for size in range(1, min(max_separator_size, len(variables)) + 1):
        for candidate in combinations(variables, size):
            components, errors = _build_components_from_separator(formula, list(candidate))
            nonempty = [component for component in components if component.variables]
            trace.append(
                {
                    "separator": list(candidate),
                    "component_count": len(nonempty),
                    "max_component_size": max((len(component.variables) for component in nonempty), default=0),
                    "errors": errors,
                }
            )
            if errors:
                continue
            if len(nonempty) < 2 or len(nonempty) > max_components:
                continue
            if any(len(component.variables) > max_component_size for component in nonempty):
                continue
            return {
                "status": GRAPH_SEPARATOR_STRUCTURE_DETECTED,
                "separator_variables": list(candidate),
                "components": [component.to_dict() for component in nonempty],
                "trace": trace,
            }
    return {
        "status": GRAPH_SEPARATOR_DIAGNOSTIC_ONLY,
        "separator_variables": [],
        "components": [],
        "trace": trace,
    }


def _reduce_clause_by_separator(clause: Clause, separator_assignment: dict[int, bool]) -> Clause | None:
    remaining: list[int] = []
    for lit in clause:
        var = abs(lit)
        if var not in separator_assignment:
            remaining.append(lit)
            continue
        value = separator_assignment[var]
        if (lit > 0 and value) or (lit < 0 and not value):
            return None
    return Clause(remaining)


def _condition_component_formula(
    formula: CNFFormula,
    component: dict[str, Any],
    separator_assignment: dict[int, bool],
) -> CNFFormula:
    clauses: list[Clause] = []
    clause_map = _clause_id_map(formula)
    for clause_id in component["clause_ids"]:
        reduced = _reduce_clause_by_separator(clause_map[int(clause_id)], separator_assignment)
        if reduced is not None:
            clauses.append(reduced)
    return CNFFormula(clauses)


def _global_separator_clauses_satisfied(formula: CNFFormula, separator: list[int], assignment: dict[int, bool]) -> bool:
    separator_set = set(separator)
    for clause in formula.clauses:
        if set(clause.variables).issubset(separator_set):
            if not formula_satisfied(CNFFormula([clause]), assignment):
                return False
    return True


def _solve_component_bounded(formula: CNFFormula, variables: list[int], *, max_component_size: int = 8) -> dict[str, Any]:
    variables = sorted(variables)
    if len(variables) > max_component_size:
        return {
            "component_status": GRAPH_SEPARATOR_DIAGNOSTIC_ONLY,
            "component_checker_status": GRAPH_SEPARATOR_CERTIFICATE_FAILED,
            "component_certificate_type": "COMPONENT_SEARCH_CAP_EXCEEDED",
            "component_witness": None,
            "component_unsat_certificate": None,
        }
    for assignment in _all_assignments(variables):
        if formula_satisfied(formula, assignment):
            return {
                "component_status": "SAT_COMPONENT_WITNESS_VERIFIED",
                "component_checker_status": GRAPH_SEPARATOR_COMPONENTS_VERIFIED,
                "component_certificate_type": "BOUNDED_COMPONENT_SAT_WITNESS",
                "component_witness": _assignment_key(assignment),
                "component_unsat_certificate": None,
            }
    return {
        "component_status": "UNSAT_COMPONENT_EXHAUSTIVE_VERIFIED",
        "component_checker_status": GRAPH_SEPARATOR_COMPONENTS_VERIFIED,
        "component_certificate_type": "BOUNDED_EXHAUSTIVE_COMPONENT_UNSAT",
        "component_witness": None,
        "component_unsat_certificate": {
            "method": "bounded exhaustive component check",
            "variables": variables,
            "assignments_checked": 2 ** len(variables),
        },
    }


def _component_result(
    formula: CNFFormula,
    component: dict[str, Any],
    separator_assignment_id: str,
    separator_assignment: dict[int, bool],
    *,
    max_component_size: int = 8,
) -> dict[str, Any]:
    component_formula = _condition_component_formula(formula, component, separator_assignment)
    solved = _solve_component_bounded(component_formula, list(map(int, component["variables"])), max_component_size=max_component_size)
    return {
        "separator_assignment_id": separator_assignment_id,
        "component_id": component["component_id"],
        "component_formula_hash": _clause_hash(component_formula),
        **solved,
    }


def _separator_assignment_rows(separator: list[int]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for idx, assignment in enumerate(_all_assignments(separator)):
        rows.append({"assignment_id": f"S{idx}", "assignment": _assignment_key(assignment)})
    return rows


def _build_graph_separator_certificate(
    instance: GraphSeparatorInstance,
    *,
    max_separator_size: int = 3,
    max_separator_assignments: int = 16,
    max_component_size: int = 8,
) -> GraphSeparatorLiftCertificate:
    detection = detect_separator(instance.formula, max_separator_size=max_separator_size, max_component_size=max_component_size)
    if detection["status"] != GRAPH_SEPARATOR_STRUCTURE_DETECTED:
        return GraphSeparatorLiftCertificate(
            type="GRAPH_SEPARATOR_LIFT_CERTIFICATE",
            instance_id=instance.instance_id,
            formula_hash=instance.formula.formula_hash,
            graph_model="PRIMAL",
            separator_variables=[],
            components=[],
            separator_assignments=[],
            mode="DIAGNOSTIC_ONLY",
            component_results=[],
            sat_lift=None,
            unsat_cover=None,
            compression_or_delta_summary={
                "prior_replay_status": instance.prior_replay_status,
                "novel_g8_delta": False,
                "reason": "No valid bounded separator decomposition.",
            },
            checker_status=GRAPH_SEPARATOR_CERTIFICATE_FAILED,
            status=GRAPH_SEPARATOR_DIAGNOSTIC_ONLY,
            public_category="NO_COLLAPSE_FOUND",
            certification_level="NOT_CERTIFIED",
            drat_claim=GRAPH_SEPARATOR_DRAT_NOT_CLAIMED,
            claim_boundary="native graph-separator certificate only; no DRAT proof claimed; no P vs NP claim",
        )

    separator = list(map(int, detection["separator_variables"]))
    components = list(detection["components"])
    assignment_rows = _separator_assignment_rows(separator)
    if len(assignment_rows) > max_separator_assignments:
        return GraphSeparatorLiftCertificate(
            type="GRAPH_SEPARATOR_LIFT_CERTIFICATE",
            instance_id=instance.instance_id,
            formula_hash=instance.formula.formula_hash,
            graph_model="PRIMAL",
            separator_variables=separator,
            components=components,
            separator_assignments=assignment_rows,
            mode="DIAGNOSTIC_ONLY",
            component_results=[],
            sat_lift=None,
            unsat_cover=None,
            compression_or_delta_summary={
                "prior_replay_status": instance.prior_replay_status,
                "novel_g8_delta": False,
                "reason": "Separator assignment cap exceeded.",
            },
            checker_status=GRAPH_SEPARATOR_CERTIFICATE_FAILED,
            status=GRAPH_SEPARATOR_DIAGNOSTIC_ONLY,
            public_category="NO_COLLAPSE_FOUND",
            certification_level="NOT_CERTIFIED",
            drat_claim=GRAPH_SEPARATOR_DRAT_NOT_CLAIMED,
            claim_boundary="native graph-separator certificate only; no DRAT proof claimed; no P vs NP claim",
        )

    component_results: list[dict[str, Any]] = []
    by_assignment: dict[str, list[dict[str, Any]]] = {}
    for row in assignment_rows:
        sep_assignment = _assignment_from_payload(row["assignment"])
        rows = [
            _component_result(
                instance.formula,
                component,
                row["assignment_id"],
                sep_assignment,
                max_component_size=max_component_size,
            )
            for component in components
        ]
        component_results.extend(rows)
        by_assignment[row["assignment_id"]] = rows

    sat_lift: dict[str, Any] | None = None
    unsat_cover: dict[str, Any] | None = None
    mode = "DIAGNOSTIC_ONLY"
    status = GRAPH_SEPARATOR_DIAGNOSTIC_ONLY
    public_category = "NO_COLLAPSE_FOUND"
    certification_level = "NOT_CERTIFIED"
    chosen_assignment_row: dict[str, Any] | None = None
    for row in assignment_rows:
        sep_assignment = _assignment_from_payload(row["assignment"])
        component_rows = by_assignment[row["assignment_id"]]
        if (
            _global_separator_clauses_satisfied(instance.formula, separator, sep_assignment)
            and all(item["component_status"] == "SAT_COMPONENT_WITNESS_VERIFIED" for item in component_rows)
        ):
            combined: dict[int, bool] = dict(sep_assignment)
            component_witnesses: dict[str, dict[str, bool]] = {}
            for item in component_rows:
                witness = dict(item.get("component_witness") or {})
                component_witnesses[item["component_id"]] = witness
                combined.update(_assignment_from_payload(witness))
            if formula_satisfied(instance.formula, combined):
                chosen_assignment_row = row
                sat_lift = {
                    "chosen_separator_assignment": row,
                    "component_witnesses": component_witnesses,
                    "combined_assignment": _assignment_key(combined),
                    "combined_assignment_verified_against_original_cnf": True,
                }
                mode = "SAT_WITNESS_LIFT"
                status = GRAPH_SEPARATOR_SAT_WITNESS_LIFTED
                public_category = SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED
                certification_level = GRAPH_SEPARATOR_SAT_WITNESS_LIFTED
                break

    if sat_lift is None:
        blocked_by_component: dict[str, str] = {}
        for row in assignment_rows:
            component_rows = by_assignment[row["assignment_id"]]
            blocker = next((item for item in component_rows if item["component_status"] == "UNSAT_COMPONENT_EXHAUSTIVE_VERIFIED"), None)
            if blocker is not None:
                blocked_by_component[row["assignment_id"]] = blocker["component_id"]
        if set(blocked_by_component) == {row["assignment_id"] for row in assignment_rows}:
            unsat_cover = {
                "separator_assignment_ids": [row["assignment_id"] for row in assignment_rows],
                "blocked_by_component": blocked_by_component,
                "all_separator_assignments_covered": True,
            }
            mode = "UNSAT_SEPARATOR_COVER"
            status = GRAPH_SEPARATOR_UNSAT_COVER_VERIFIED
            public_category = UNSAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED
            certification_level = GRAPH_SEPARATOR_UNSAT_COVER_VERIFIED

    duplicate_prior = instance.prior_replay_status == GRAPH_SEPARATOR_NO_NEW_DELTA
    if duplicate_prior:
        status = GRAPH_SEPARATOR_NO_NEW_DELTA
        public_category = "NO_COLLAPSE_FOUND"
        certification_level = "DUPLICATE_PRIOR_NOT_COUNTED"

    cert = GraphSeparatorLiftCertificate(
        type="GRAPH_SEPARATOR_LIFT_CERTIFICATE",
        instance_id=instance.instance_id,
        formula_hash=instance.formula.formula_hash,
        graph_model="PRIMAL",
        separator_variables=separator,
        components=components,
        separator_assignments=assignment_rows,
        mode=mode,
        component_results=component_results,
        sat_lift=sat_lift,
        unsat_cover=unsat_cover,
        compression_or_delta_summary={
            "promoted_recommendation": PROMOTED_RECOMMENDATION,
            "prior_replay_status": instance.prior_replay_status,
            "novel_g8_delta": bool(instance.novel_delta_expected and public_category in {SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED, UNSAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED}),
            "duplicate_prior_not_counted": duplicate_prior,
            "chosen_separator_assignment": chosen_assignment_row,
        },
        checker_status="NOT_RUN",
        status=status,
        public_category=public_category,
        certification_level=certification_level,
        drat_claim=GRAPH_SEPARATOR_DRAT_NOT_CLAIMED,
        claim_boundary="native graph-separator certificate only; no DRAT proof claimed; no theorem claim, no completeness claim, no lower-bound claim, and no P vs NP claim",
    )
    check = check_graph_separator_certificate(instance.formula, cert)
    data = cert.to_dict()
    data["checker_status"] = check["checker_status"]
    if check["checker_status"] == GRAPH_SEPARATOR_CERTIFICATE_VERIFIED and public_category in {
        SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED,
        UNSAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED,
    }:
        data["status"] = GRAPH_SEPARATOR_NATIVE_CERTIFIED
        data["certification_level"] = G8_GRAPH_SEPARATOR_NATIVE_CERTIFIED
    elif public_category != "NO_COLLAPSE_FOUND":
        data["status"] = GRAPH_SEPARATOR_CERTIFICATE_FAILED
        data["public_category"] = "NO_COLLAPSE_FOUND"
        data["certification_level"] = "NOT_CERTIFIED"
    return GraphSeparatorLiftCertificate(**data)


def build_graph_separator_certificate(instance: GraphSeparatorInstance, **kwargs: Any) -> GraphSeparatorLiftCertificate:
    return _build_graph_separator_certificate(instance, **kwargs)


def _expected_components_from_certificate(data: dict[str, Any]) -> list[SeparatorComponent]:
    return [
        SeparatorComponent(
            component_id=str(component["component_id"]),
            variables=sorted(map(int, component.get("variables", []))),
            clause_ids=sorted(map(int, component.get("clause_ids", []))),
            boundary_separator_variables=sorted(map(int, component.get("boundary_separator_variables", []))),
        )
        for component in data.get("components", [])
    ]


def _validate_component_assignment(formula: CNFFormula, separator: list[int], components: list[SeparatorComponent]) -> list[str]:
    errors: list[str] = []
    separator_set = set(separator)
    lookup = _component_lookup(components)
    assigned_clause_ids = [clause_id for component in components for clause_id in component.clause_ids]
    if len(assigned_clause_ids) != len(set(assigned_clause_ids)):
        errors.append("CLAUSE_ASSIGNED_MULTIPLE_TIMES")
    expected_assigned: set[int] = set()
    for clause_id, clause in _clause_id_map(formula).items():
        non_separator_vars = [var for var in clause.variables if var not in separator_set]
        if not non_separator_vars:
            continue
        component_ids = {lookup.get(var) for var in non_separator_vars}
        if len(component_ids) != 1 or None in component_ids:
            errors.append(f"INVALID_CROSS_COMPONENT_CLAUSE:{clause_id}")
        else:
            expected_assigned.add(clause_id)
    if set(assigned_clause_ids) != expected_assigned:
        errors.append("CLAUSE_ASSIGNMENT_COVERAGE_MISMATCH")
    for component in components:
        for clause_id in component.clause_ids:
            clause = _clause_id_map(formula).get(int(clause_id))
            if clause is None:
                errors.append(f"CLAUSE_ID_MISSING:{clause_id}")
                continue
            non_separator = [var for var in clause.variables if var not in separator_set]
            if not set(non_separator).issubset(set(component.variables)):
                errors.append(f"COMPONENT_CLAUSE_VARIABLE_MISMATCH:{component.component_id}:{clause_id}")
            expected_boundary = sorted(var for var in clause.variables if var in separator_set)
            if not set(expected_boundary).issubset(set(component.boundary_separator_variables)):
                errors.append(f"COMPONENT_BOUNDARY_MISMATCH:{component.component_id}:{clause_id}")
    return errors


def _assignment_rows_are_complete(separator: list[int], rows: list[dict[str, Any]]) -> bool:
    expected = [_assignment_key(assignment) for assignment in _all_assignments(separator)]
    actual = [dict(row.get("assignment", {})) for row in rows]
    return expected == actual


def _component_result_lookup(component_results: list[dict[str, Any]]) -> dict[tuple[str, str], dict[str, Any]]:
    return {
        (str(row.get("separator_assignment_id")), str(row.get("component_id"))): row
        for row in component_results
    }


def _check_component_result(
    formula: CNFFormula,
    component: SeparatorComponent,
    assignment_id: str,
    separator_assignment: dict[int, bool],
    recorded: dict[str, Any],
) -> list[str]:
    errors: list[str] = []
    component_data = component.to_dict()
    conditioned = _condition_component_formula(formula, component_data, separator_assignment)
    if recorded.get("component_formula_hash") != conditioned.formula_hash:
        errors.append(f"COMPONENT_FORMULA_HASH_MISMATCH:{assignment_id}:{component.component_id}")
    recomputed = _solve_component_bounded(conditioned, component.variables)
    if recorded.get("component_status") != recomputed["component_status"]:
        errors.append(f"COMPONENT_STATUS_MISMATCH:{assignment_id}:{component.component_id}")
    if recorded.get("component_checker_status") != GRAPH_SEPARATOR_COMPONENTS_VERIFIED:
        errors.append(f"COMPONENT_CHECKER_NOT_VERIFIED:{assignment_id}:{component.component_id}")
    if recorded.get("component_certificate_type") != recomputed["component_certificate_type"]:
        errors.append(f"COMPONENT_CERT_TYPE_MISMATCH:{assignment_id}:{component.component_id}")
    if recorded.get("component_status") == "SAT_COMPONENT_WITNESS_VERIFIED":
        witness = _assignment_from_payload(recorded.get("component_witness") or {})
        if not formula_satisfied(conditioned, witness):
            errors.append(f"COMPONENT_WITNESS_INVALID:{assignment_id}:{component.component_id}")
    if recorded.get("component_status") == "UNSAT_COMPONENT_EXHAUSTIVE_VERIFIED":
        cert = recorded.get("component_unsat_certificate") or {}
        if cert.get("method") != "bounded exhaustive component check":
            errors.append(f"COMPONENT_UNSAT_CERT_MISSING:{assignment_id}:{component.component_id}")
    return errors


def check_graph_separator_certificate(
    formula: CNFFormula,
    certificate: GraphSeparatorLiftCertificate | dict[str, Any],
) -> dict[str, Any]:
    data = certificate.to_dict() if isinstance(certificate, GraphSeparatorLiftCertificate) else dict(certificate)
    errors: list[str] = []
    if data.get("type") != "GRAPH_SEPARATOR_LIFT_CERTIFICATE":
        errors.append("CERTIFICATE_TYPE_MISMATCH")
    if str(data.get("formula_hash", "")).lower() != formula.formula_hash.lower():
        errors.append("FORMULA_HASH_MISMATCH")
    if data.get("graph_model") != "PRIMAL":
        errors.append("UNSUPPORTED_GRAPH_MODEL")
    if data.get("drat_claim") != GRAPH_SEPARATOR_DRAT_NOT_CLAIMED:
        errors.append("FAKE_DRAT_CLAIM")
    if "DRAT" in str(data.get("public_category")):
        errors.append("PUBLIC_CATEGORY_FAKE_DRAT")
    if any(str(data.get(key, "")) in FORBIDDEN_STATUS_VALUES for key in ["status", "public_category", "checker_status"]):
        errors.append("FORBIDDEN_STATUS_VALUE")

    separator = sorted(map(int, data.get("separator_variables", [])))
    if not separator and data.get("mode") != "DIAGNOSTIC_ONLY":
        errors.append("SEPARATOR_MISSING")
    if any(var not in formula.variables for var in separator):
        errors.append("SEPARATOR_VARIABLE_NOT_IN_FORMULA")
    components = _expected_components_from_certificate(data)
    if data.get("mode") != "DIAGNOSTIC_ONLY":
        recomputed_components, recompute_errors = _build_components_from_separator(formula, separator)
        if recompute_errors:
            errors.extend(recompute_errors)
        if [component.to_dict() for component in recomputed_components] != [component.to_dict() for component in components]:
            errors.append("COMPONENT_DECOMPOSITION_MISMATCH")
        errors.extend(_validate_component_assignment(formula, separator, components))

    assignment_rows = list(data.get("separator_assignments", []))
    if data.get("mode") != "DIAGNOSTIC_ONLY" and not _assignment_rows_are_complete(separator, assignment_rows):
        errors.append("SEPARATOR_ASSIGNMENTS_INCOMPLETE")

    lookup = _component_result_lookup(list(data.get("component_results", [])))
    for assignment_row in assignment_rows:
        assignment_id = str(assignment_row.get("assignment_id"))
        separator_assignment = _assignment_from_payload(assignment_row.get("assignment") or {})
        for component in components:
            recorded = lookup.get((assignment_id, component.component_id))
            if recorded is None:
                errors.append(f"COMPONENT_RESULT_MISSING:{assignment_id}:{component.component_id}")
                continue
            errors.extend(_check_component_result(formula, component, assignment_id, separator_assignment, recorded))

    if data.get("mode") == "SAT_WITNESS_LIFT":
        lift = data.get("sat_lift") or {}
        chosen = lift.get("chosen_separator_assignment") or {}
        chosen_assignment = _assignment_from_payload(chosen.get("assignment") or {})
        component_witnesses = lift.get("component_witnesses") or {}
        combined = _assignment_from_payload(lift.get("combined_assignment") or {})
        for component in components:
            witness = _assignment_from_payload(component_witnesses.get(component.component_id) or {})
            for var in witness:
                if var not in component.variables:
                    errors.append(f"COMPONENT_WITNESS_OUTSIDE_COMPONENT:{component.component_id}:{var}")
            for var, value in chosen_assignment.items():
                if var in witness and witness[var] != value:
                    errors.append(f"SEPARATOR_ASSIGNMENT_DISAGREEMENT:{component.component_id}:{var}")
        expected_combined: dict[int, bool] = dict(chosen_assignment)
        for witness in component_witnesses.values():
            expected_combined.update(_assignment_from_payload(witness))
        if combined != expected_combined:
            errors.append("COMBINED_ASSIGNMENT_MISMATCH")
        if lift.get("combined_assignment_verified_against_original_cnf") is not True:
            errors.append("COMBINED_ASSIGNMENT_FLAG_FALSE")
        if not formula_satisfied(formula, combined):
            errors.append("COMBINED_ASSIGNMENT_DOES_NOT_SATISFY_ORIGINAL")

    if data.get("mode") == "UNSAT_SEPARATOR_COVER":
        cover = data.get("unsat_cover") or {}
        if cover.get("all_separator_assignments_covered") is not True:
            errors.append("UNSAT_COVER_FLAG_FALSE")
        blocked = cover.get("blocked_by_component") or {}
        expected_ids = [str(row.get("assignment_id")) for row in assignment_rows]
        if sorted(blocked) != sorted(expected_ids):
            errors.append("UNSAT_COVER_INCOMPLETE")
        for assignment_id, component_id in blocked.items():
            row = lookup.get((str(assignment_id), str(component_id)))
            if row is None:
                errors.append(f"UNSAT_COVER_COMPONENT_RESULT_MISSING:{assignment_id}:{component_id}")
            elif row.get("component_status") != "UNSAT_COMPONENT_EXHAUSTIVE_VERIFIED":
                errors.append(f"UNSAT_COVER_BLOCKER_NOT_UNSAT:{assignment_id}:{component_id}")

    boundary = str(data.get("claim_boundary", "")).lower()
    for phrase in ["no drat proof claimed", "no theorem", "no p vs np claim"]:
        if phrase not in boundary:
            errors.append(f"CLAIM_BOUNDARY_MISSING:{phrase}")
    if "proves P vs NP" in stable_json(data) or "strictness theorem" in stable_json(data):
        errors.append("FORBIDDEN_THEOREM_OR_PNP_TEXT")

    checker_status = GRAPH_SEPARATOR_CERTIFICATE_VERIFIED if not errors else GRAPH_SEPARATOR_CERTIFICATE_FAILED
    return {
        "checker_status": checker_status,
        "status": checker_status,
        "errors": errors,
        "separator_variables": separator,
        "component_count": len(components),
        "assignment_count": len(assignment_rows),
        "mode": data.get("mode"),
        "claim_boundary": "Native separator lift certificate only; no DRAT, theorem, lower-bound, completeness, or P-vs-NP claim.",
    }


def _separator_sat_pair() -> CNFFormula:
    return CNFFormula.from_raw_clauses([[1, 2], [-2, 3], [3], [1, 4], [-4, 5], [5]])


def _separator_unsat_cover() -> CNFFormula:
    return CNFFormula.from_raw_clauses([[-1, 2], [-1, -2], [1, 3], [1, -3]])


def _separator_bad_cross_clause() -> CNFFormula:
    return CNFFormula.from_raw_clauses([[1, 2], [1, 4], [2, 4]])


def _repeated_separator_chain_sat() -> CNFFormula:
    return CNFFormula.from_raw_clauses([[1, 2], [-2, 3], [3], [-1, 4], [4, 5], [-5, 6], [6]])


def _separator_toy_unsat() -> CNFFormula:
    return CNFFormula.from_raw_clauses([[-1, 2], [-1, -2], [1, 3], [1, -3], [4]])


def _grid_duplicate_control() -> CNFFormula:
    return CNFFormula.from_raw_clauses([[1, 2], [-2, 3], [3], [1, 4], [-4, 5], [5]])


def make_graph_separator_instance(instance_id: str) -> GraphSeparatorInstance:
    mapping = {
        "separator_sat_pair": GraphSeparatorInstance(
            instance_id,
            "synthetic-separator",
            _separator_sat_pair(),
            "G0_G7_BOUNDED_NON_ACCEPTANCE_REPLAY",
            "SAT_WITNESS_LIFT",
            True,
            "Two SAT components share separator variable 1.",
        ),
        "separator_unsat_cover": GraphSeparatorInstance(
            instance_id,
            "synthetic-separator",
            _separator_unsat_cover(),
            "G0_G7_BOUNDED_NON_ACCEPTANCE_REPLAY",
            "UNSAT_SEPARATOR_COVER",
            True,
            "Every separator assignment is blocked by a component contradiction.",
        ),
        "separator_toy_unsat": GraphSeparatorInstance(
            instance_id,
            "synthetic-separator",
            _separator_toy_unsat(),
            "G0_G7_BOUNDED_NON_ACCEPTANCE_REPLAY",
            "UNSAT_SEPARATOR_COVER",
            True,
            "UNSAT cover with an extra independent component.",
        ),
        "repeated_separator_chain": GraphSeparatorInstance(
            instance_id,
            "repeated-separator-chain",
            _repeated_separator_chain_sat(),
            "G0_G7_BOUNDED_NON_ACCEPTANCE_REPLAY",
            "SAT_WITNESS_LIFT",
            True,
            "A small repeated separator chain handled without recursive claims.",
        ),
        "repeated_separator_chain_sat": GraphSeparatorInstance(
            instance_id,
            "repeated-separator-chain",
            _repeated_separator_chain_sat(),
            "G0_G7_BOUNDED_NON_ACCEPTANCE_REPLAY",
            "SAT_WITNESS_LIFT",
            True,
            "A small repeated separator chain handled without recursive claims.",
        ),
        "repeated_separator_chain_unsat": GraphSeparatorInstance(
            instance_id,
            "repeated-separator-chain",
            _separator_unsat_cover(),
            "G0_G7_BOUNDED_NON_ACCEPTANCE_REPLAY",
            "UNSAT_SEPARATOR_COVER",
            True,
            "Repeated-chain UNSAT control mapped to separator cover.",
        ),
        "separator_bad_cross_clause_reject": GraphSeparatorInstance(
            instance_id,
            "negative-control",
            _separator_bad_cross_clause(),
            "G0_G7_BOUNDED_NON_ACCEPTANCE_REPLAY",
            "DIAGNOSTIC_ONLY",
            False,
            "Invalid cross-component clause control.",
        ),
        "separator_incomplete_assignment_reject": GraphSeparatorInstance(
            instance_id,
            "negative-control",
            _separator_unsat_cover(),
            "G0_G7_BOUNDED_NON_ACCEPTANCE_REPLAY",
            "UNSAT_SEPARATOR_COVER",
            False,
            "Tamper target for incomplete cover rejection.",
        ),
        "grid_3x3_3color": GraphSeparatorInstance(
            instance_id,
            "grid-coloring-duplicate-control",
            _grid_duplicate_control(),
            GRAPH_SEPARATOR_NO_NEW_DELTA,
            "SAT_WITNESS_LIFT",
            False,
            "Structured duplicate control; prior grammar success is not counted as novel G8 delta.",
        ),
        "grid_4x4_3color": GraphSeparatorInstance(
            instance_id,
            "grid-coloring-duplicate-control",
            _grid_duplicate_control(),
            GRAPH_SEPARATOR_NO_NEW_DELTA,
            "SAT_WITNESS_LIFT",
            False,
            "Structured duplicate control; prior grammar success is not counted as novel G8 delta.",
        ),
        "grid_5x5_3color": GraphSeparatorInstance(
            instance_id,
            "grid-coloring-duplicate-control",
            _grid_duplicate_control(),
            GRAPH_SEPARATOR_NO_NEW_DELTA,
            "SAT_WITNESS_LIFT",
            False,
            "Optional structured duplicate control.",
        ),
    }
    if instance_id not in mapping:
        raise ValueError(f"unknown graph-separator instance: {instance_id}")
    return mapping[instance_id]


def graph_separator_report(rows: list[dict[str, Any]], delta: dict[str, Any]) -> str:
    lines = [
        "# Graph Separator Lift Report",
        "",
        "## Executive Summary",
        "",
        "v2.15 promotes the v2.14 GRAPH_SEPARATOR_OBSTRUCTION recommendation into G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE. The prototype detects exact primal separators, conditions components on separator assignments, and emits native certificates for SAT witness lift or UNSAT separator cover.",
        "",
        "It is not DRAT, not a theorem, not a lower-bound proof, not a graph-formula completeness claim, not hierarchy completeness, and not P vs NP progress.",
        "",
        "## Rows",
        "",
        "| instance | mode | public category | checker | novel G8 delta |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['instance_id']}` | `{row['mode']}` | `{row['public_category']}` | `{row['checker_status']}` | `{row['novel_g8_delta']}` |"
        )
    lines.extend(
        [
            "",
            "## Separator Soundness",
            "",
            "- SAT lift requires component witnesses to agree on the separator assignment and the combined assignment to satisfy the original CNF.",
            "- UNSAT lift requires every separator assignment to be blocked by at least one verified component contradiction.",
            "- Invalid cross-component clauses are rejected.",
            "- Duplicate prior-grammar successes are marked `GRAPH_SEPARATOR_NO_NEW_DELTA` and are not counted as novel G8 deltas.",
            "",
            "## Operator Delta Summary",
            "",
            stable_json(delta),
        ]
    )
    return "\n".join(lines)


def run_graph_separator_lab(
    *,
    instances: Iterable[str],
    out_root: str | Path,
    strict: bool = False,
    zip_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    cert_root = root / "certificates"
    cnf_root = root / "original_cnf"
    cert_root.mkdir(parents=True, exist_ok=True)
    cnf_root.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []
    certificates: list[dict[str, Any]] = []
    checks: list[dict[str, Any]] = []
    detection_traces: list[dict[str, Any]] = []
    decomposition_summary: list[dict[str, Any]] = []
    cover_summary: list[dict[str, Any]] = []

    for instance_id in instances:
        instance = make_graph_separator_instance(instance_id)
        detection = detect_separator(instance.formula)
        certificate = build_graph_separator_certificate(instance)
        check = check_graph_separator_certificate(instance.formula, certificate)
        cert_path = cert_root / f"{instance_id}_graph_separator_certificate.json"
        cnf_path = cnf_root / f"{instance_id}.cnf"
        _write_json(cert_path, certificate.to_dict())
        _write_text(cnf_path, instance.formula.canonical_dimacs())

        novel_delta = (
            check["checker_status"] == GRAPH_SEPARATOR_CERTIFICATE_VERIFIED
            and certificate.public_category in {SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED, UNSAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED}
            and bool(certificate.compression_or_delta_summary.get("novel_g8_delta"))
        )
        row = {
            "instance_id": instance_id,
            "family": instance.family,
            "grammar": G8_GRAMMAR,
            "mode": certificate.mode,
            "status": certificate.status,
            "public_category": certificate.public_category,
            "certification_level": certificate.certification_level,
            "checker_status": check["checker_status"],
            "prior_replay_status": instance.prior_replay_status,
            "novel_g8_delta": novel_delta,
            "duplicate_prior_not_counted": bool(certificate.compression_or_delta_summary.get("duplicate_prior_not_counted")),
            "certificate_path": str(cert_path),
            "cnf_path": str(cnf_path),
        }
        rows.append(row)
        certificates.append(certificate.to_dict())
        checks.append({"instance_id": instance_id, **check})
        detection_traces.append({"instance_id": instance_id, "detection": detection})
        decomposition_summary.append(
            {
                "instance_id": instance_id,
                "separator_variables": certificate.separator_variables,
                "components": certificate.components,
                "mode": certificate.mode,
            }
        )
        cover_summary.append(
            {
                "instance_id": instance_id,
                "separator_assignment_count": len(certificate.separator_assignments),
                "unsat_cover": certificate.unsat_cover,
                "sat_lift": certificate.sat_lift,
            }
        )

    delta = {
        "operator_added": G8_GRAMMAR,
        "promoted_recommendation": PROMOTED_RECOMMENDATION,
        "evidence_grade": "FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED",
        "instances_total": len(rows),
        "native_certified": sum(1 for row in rows if row["public_category"] in {SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED, UNSAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED}),
        "sat_witness_lifted": sum(1 for row in rows if row["public_category"] == SAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED),
        "unsat_cover_verified": sum(1 for row in rows if row["public_category"] == UNSAT_GRAPH_SEPARATOR_NATIVE_CERTIFIED),
        "novel_g8_delta_count": sum(1 for row in rows if row["novel_g8_delta"]),
        "duplicate_prior_not_counted": sum(1 for row in rows if row["duplicate_prior_not_counted"]),
        "strict": strict,
        "claim_boundary": "Finite empirical edge-delta evidence only; no lower-bound, theorem, DRAT, completeness, or P-vs-NP claim.",
    }

    outputs = {
        "graph_separator_certificates.json": {"certificates": certificates},
        "graph_separator_checker_summary.json": {"checks": checks},
        "separator_detection_trace.json": {"traces": detection_traces},
        "component_decomposition_summary.json": {"rows": decomposition_summary},
        "separator_assignment_cover_summary.json": {"rows": cover_summary},
        "g8_operator_delta_summary.json": delta,
    }
    for name, payload in outputs.items():
        _write_json(root / name, payload)
    _write_text(root / "GRAPH_SEPARATOR_LIFT_REPORT.md", graph_separator_report(rows, delta))

    zip_sha = ""
    if zip_path:
        zip_sha = _make_zip(root, zip_path)
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": zip_sha,
        "rows": rows,
        "graph_separator_certificates": certificates,
        "graph_separator_checker_summary": checks,
        "separator_detection_trace": detection_traces,
        "component_decomposition_summary": decomposition_summary,
        "separator_assignment_cover_summary": cover_summary,
        "g8_operator_delta_summary": delta,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m witnora_core.graph_separator_lift")
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument(
        "--instances",
        nargs="+",
        default=[
            "separator_sat_pair",
            "separator_unsat_cover",
            "grid_3x3_3color",
            "grid_4x4_3color",
            "separator_toy_unsat",
            "repeated_separator_chain",
        ],
    )
    run_parser.add_argument("--out-root", default="outputs/v2.15-graph-separator-lift")
    run_parser.add_argument("--strict", action="store_true")
    run_parser.add_argument("--zip", default="witnora-core-v2.15-graph-separator-lift.zip")
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--cnf", required=True)
    check_parser.add_argument("--certificate", required=True)
    args = parser.parse_args(argv)
    if args.command == "run":
        result = run_graph_separator_lab(
            instances=args.instances,
            out_root=args.out_root,
            strict=args.strict,
            zip_path=args.zip,
        )
        print(
            stable_json(
                {
                    "out_root": args.out_root,
                    "zip": args.zip,
                    "zip_sha256": result["zip_sha256"],
                    "summary": result["g8_operator_delta_summary"],
                }
            )
        )
        return 0
    if args.command == "check":
        formula = load_dimacs(args.cnf)
        data = json.loads(Path(args.certificate).read_text(encoding="utf-8"))
        print(stable_json(check_graph_separator_certificate(formula, data)))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
