"""Bounded separator-affine family theorem artifacts for Witnora v2.22.

The v2.22 layer is deliberately narrow. It recognizes CNFs with a fixed-size
variable separator whose separator-conditioned residual components are exact
GF(2) affine CNFs accepted by G5. SAT requires one separator assignment where
all residual components are SAT. UNSAT requires a complete cover: every
separator assignment has at least one affine-UNSAT component.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from itertools import combinations, product
import json
from pathlib import Path
import shutil
from typing import Any, Iterable
import zipfile

from .cnf import CNFFormula, Clause, clause_satisfied, formula_satisfied
from .dimacs import load_dimacs, load_dimacs_with_document_evidence
from .obstruction_dual import sha256_file, stable_json
from .operator_genesis import (
    AFFINE_RESIDUE_CERTIFICATE_VERIFIED,
    AffineResidueInstance,
    build_affine_residue_certificate,
    check_affine_residue_certificate,
)
from .xor import canonical_xor_cnf_clauses


VERSION = "2.22"
G14_GRAMMAR = "G14_BOUNDED_SEPARATOR_AFFINE_FAMILY_THEOREM"

SEPARATOR_AFFINE_FAMILY_RECOGNIZED = "SEPARATOR_AFFINE_FAMILY_RECOGNIZED"
SEPARATOR_AFFINE_SEPARATOR_VERIFIED = "SEPARATOR_AFFINE_SEPARATOR_VERIFIED"
SEPARATOR_AFFINE_COMPONENTS_EXTRACTED = "SEPARATOR_AFFINE_COMPONENTS_EXTRACTED"
SEPARATOR_AFFINE_COMPONENT_AFFINE_VERIFIED = "SEPARATOR_AFFINE_COMPONENT_AFFINE_VERIFIED"
SEPARATOR_AFFINE_ASSIGNMENT_ENUMERATION_VERIFIED = "SEPARATOR_AFFINE_ASSIGNMENT_ENUMERATION_VERIFIED"
SEPARATOR_AFFINE_SAT_WITNESS_LIFTED = "SEPARATOR_AFFINE_SAT_WITNESS_LIFTED"
SEPARATOR_AFFINE_UNSAT_COVER_VERIFIED = "SEPARATOR_AFFINE_UNSAT_COVER_VERIFIED"
SEPARATOR_AFFINE_CERTIFICATE_VERIFIED = "SEPARATOR_AFFINE_CERTIFICATE_VERIFIED"
SEPARATOR_AFFINE_CERTIFICATE_FAILED = "SEPARATOR_AFFINE_CERTIFICATE_FAILED"
SEPARATOR_AFFINE_THEOREM_SKETCH_VERIFIED = "SEPARATOR_AFFINE_THEOREM_SKETCH_VERIFIED"
SEPARATOR_AFFINE_FAMILY_THEOREM_RESTRICTED = "SEPARATOR_AFFINE_FAMILY_THEOREM_RESTRICTED"
SEPARATOR_AFFINE_NO_FAKE_GENERALIZATION = "SEPARATOR_AFFINE_NO_FAKE_GENERALIZATION"
G14_SEPARATOR_AFFINE_NATIVE_CERTIFIED = "G14_SEPARATOR_AFFINE_NATIVE_CERTIFIED"

SAT_CERTIFIED = "SAT_CERTIFIED"
UNSAT_CERTIFIED = "UNSAT_CERTIFIED"
DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"
ALL_COMPONENTS_SAT = "ALL_COMPONENTS_SAT"
SOME_COMPONENT_UNSAT = "SOME_COMPONENT_UNSAT"

FORBIDDEN_STATUS_VALUES = {"HARD", "UNKNOWN", "PNP_PROGRESS", "COMPLETE_SAT", "THEOREM_PROVEN_UNQUALIFIED"}
FORBIDDEN_CLAIM_FRAGMENTS = {
    "p vs np progress",
    "all sat",
    "complete sat",
    "hierarchy completeness",
    "drat proof claimed",
    "theorem proven unqualified",
    "polynomial-time sat for arbitrary formulas",
}


@dataclass(frozen=True)
class SeparatorAffineFamilyInstance:
    instance_id: str
    formula: CNFFormula
    separator_variables: list[int]
    separator_bound_c: int
    affine_arity_bound_r: int
    expected_result: str
    family: str
    n: int
    control_kind: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "formula_hash": self.formula.formula_hash,
            "separator_variables": self.separator_variables,
            "separator_bound_c": self.separator_bound_c,
            "affine_arity_bound_r": self.affine_arity_bound_r,
            "expected_result": self.expected_result,
            "family": self.family,
            "n": self.n,
            "control_kind": self.control_kind,
        }


@dataclass(frozen=True)
class SeparatorAffineFamilyCertificate:
    type: str
    instance_id: str
    formula_hash: str
    grammar: str
    family_parameters: dict[str, Any]
    separator_variables: list[int]
    primal_graph_summary: dict[str, Any]
    separator_verification: dict[str, Any]
    separator_assignments: list[dict[str, Any]]
    final_result: str
    sat_witness: dict[str, Any] | None
    unsat_cover: dict[str, Any] | None
    polynomial_bound_record: dict[str, Any]
    theorem_record_reference: str
    checker_status: str
    status: str
    public_category: str
    claim_boundary: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(stable_json(data) + "\n", encoding="utf-8", newline="\n")


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


def _assignment_key(assignment: dict[int, bool]) -> dict[str, bool]:
    return {str(var): bool(assignment[var]) for var in sorted(assignment)}


def _assignment_from_payload(payload: dict[str, Any] | None) -> dict[int, bool]:
    return {int(var): bool(value) for var, value in (payload or {}).items()}


def _all_assignments(variables: Iterable[int]) -> list[dict[int, bool]]:
    vars_sorted = sorted(variables)
    return [
        {var: bool(value) for var, value in zip(vars_sorted, values)}
        for values in product([False, True], repeat=len(vars_sorted))
    ]


def _clause_id_map(formula: CNFFormula) -> dict[int, Clause]:
    return {idx: clause for idx, clause in enumerate(formula.clauses, start=1)}


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


def _component_dicts(formula: CNFFormula, separator: list[int]) -> list[dict[str, Any]]:
    separator_set = set(separator)
    raw = _components_after_removing(primal_graph(formula), separator_set)
    components: list[dict[str, Any]] = []
    lookup: dict[int, str] = {}
    for idx, variables in enumerate(raw, start=1):
        cid = f"C{idx}"
        for var in variables:
            lookup[var] = cid
        components.append({"component_id": cid, "variables": variables, "clause_ids": [], "boundary_separator_variables": []})
    clause_ids: dict[str, list[int]] = defaultdict(list)
    boundary: dict[str, set[int]] = defaultdict(set)
    for clause_id, clause in _clause_id_map(formula).items():
        non_separator = [var for var in clause.variables if var not in separator_set]
        if not non_separator:
            continue
        cids = {lookup.get(var) for var in non_separator}
        if len(cids) == 1 and None not in cids:
            cid = next(iter(cids))
            clause_ids[cid].append(clause_id)
            boundary[cid].update(var for var in clause.variables if var in separator_set)
    for component in components:
        cid = component["component_id"]
        component["clause_ids"] = sorted(clause_ids.get(cid, []))
        component["boundary_separator_variables"] = sorted(boundary.get(cid, set()))
    return components


def _reduce_clause(clause: Clause, assignment: dict[int, bool]) -> Clause | None:
    remaining: list[int] = []
    for lit in clause:
        var = abs(lit)
        if var not in assignment:
            remaining.append(lit)
            continue
        value = assignment[var]
        if (lit > 0 and value) or (lit < 0 and not value):
            return None
    return Clause(remaining)


def _condition_by_separator(
    formula: CNFFormula,
    separator_assignment: dict[int, bool],
    components: list[dict[str, Any]],
) -> tuple[CNFFormula, dict[str, CNFFormula], list[str]]:
    errors: list[str] = []
    lookup: dict[int, str] = {}
    for component in components:
        for var in component["variables"]:
            lookup[int(var)] = str(component["component_id"])
    component_clauses: dict[str, list[Clause]] = {str(component["component_id"]): [] for component in components}
    residual_clauses: list[Clause] = []
    for clause_id, clause in _clause_id_map(formula).items():
        reduced = _reduce_clause(clause, separator_assignment)
        if reduced is None:
            continue
        residual_clauses.append(reduced)
        if len(reduced) == 0:
            errors.append(f"EMPTY_RESIDUAL_CLAUSE:{clause_id}")
            continue
        cids = {lookup.get(var) for var in reduced.variables if var not in separator_assignment}
        if len(cids) != 1 or None in cids:
            errors.append(f"RESIDUAL_CLAUSE_SPANS_COMPONENTS:{clause_id}")
            continue
        component_clauses[next(iter(cids))].append(reduced)
    return (
        CNFFormula(residual_clauses),
        {cid: CNFFormula(clauses) for cid, clauses in component_clauses.items()},
        errors,
    )


def _guarded_xor_equation(selector: int, active_value: bool, variables: Iterable[int], parity_bit: int) -> list[list[int]]:
    guard_lit = -selector if active_value else selector
    return [sorted([guard_lit, *clause]) for clause in canonical_xor_cnf_clauses(variables, parity_bit)]


def _component_vars(index: int) -> tuple[int, int]:
    base = 2 + 2 * index
    return base, base + 1


def _add_component_equations(raw: list[list[int]], selector: int, index: int, false_parities: list[int], true_parities: list[int]) -> None:
    variables = _component_vars(index)
    for parity in false_parities:
        raw.extend(_guarded_xor_equation(selector, False, variables, parity))
    for parity in true_parities:
        raw.extend(_guarded_xor_equation(selector, True, variables, parity))


def _saf_formula(component_count: int, *, mode: str) -> CNFFormula:
    raw: list[list[int]] = []
    selector = 1
    for idx in range(component_count):
        if mode == "sat":
            _add_component_equations(raw, selector, idx, [idx % 2], [idx % 2])
        elif mode == "unsat_cover":
            if idx == 0:
                _add_component_equations(raw, selector, idx, [0, 1], [0])
            elif idx == 1:
                _add_component_equations(raw, selector, idx, [0], [0, 1])
            else:
                _add_component_equations(raw, selector, idx, [idx % 2], [idx % 2])
        elif mode == "mixed":
            if idx == 0:
                _add_component_equations(raw, selector, idx, [0, 1], [0])
            else:
                _add_component_equations(raw, selector, idx, [idx % 2], [idx % 2])
        elif mode == "balanced":
            _add_component_equations(raw, selector, idx, [0], [1])
        else:
            raise ValueError(f"unsupported SAF mode: {mode}")
    return CNFFormula.from_raw_clauses(raw)


def make_separator_affine_instance(instance_id: str) -> SeparatorAffineFamilyInstance:
    def valid(component_count: int, mode: str, expected: str, family: str) -> SeparatorAffineFamilyInstance:
        return SeparatorAffineFamilyInstance(
            instance_id=instance_id,
            formula=_saf_formula(component_count, mode=mode),
            separator_variables=[1],
            separator_bound_c=1,
            affine_arity_bound_r=2,
            expected_result=expected,
            family=family,
            n=component_count,
        )

    if instance_id.startswith("saf_sat_chain_"):
        n = int(instance_id.rsplit("_", 1)[1])
        return valid(n, "sat", SAT_CERTIFIED, "saf_sat_chain")
    if instance_id.startswith("saf_unsat_cover_"):
        n = int(instance_id.rsplit("_", 1)[1])
        return valid(n, "unsat_cover", UNSAT_CERTIFIED, "saf_unsat_cover")
    if instance_id.startswith("saf_mixed_components_"):
        n = int(instance_id.rsplit("_", 1)[1])
        return valid(n, "mixed", SAT_CERTIFIED, "saf_mixed_components")
    if instance_id.startswith("saf_balanced_sat_"):
        n = int(instance_id.rsplit("_", 1)[1])
        return valid(n, "balanced", SAT_CERTIFIED, "saf_balanced_sat")

    if instance_id == "invalid_large_separator":
        raw: list[list[int]] = []
        # Both variables 1 and 2 are needed to disconnect the components.
        for idx in range(4):
            variables = _component_vars(idx)
            for clause in canonical_xor_cnf_clauses(variables, idx % 2):
                raw.append(sorted([1, *clause]))
                raw.append(sorted([-1, 2, *clause]))
                raw.append(sorted([-2, *clause]))
        return SeparatorAffineFamilyInstance(instance_id, CNFFormula.from_raw_clauses(raw), [1, 2], 1, 2, DIAGNOSTIC_ONLY, "control", 4, "INVALID_LARGE_SEPARATOR")
    if instance_id == "non_affine_component":
        formula = _saf_formula(4, mode="sat")
        raw = formula.to_clause_lists()
        raw.append([2, 3, 4])
        return SeparatorAffineFamilyInstance(instance_id, CNFFormula.from_raw_clauses(raw), [1], 1, 2, DIAGNOSTIC_ONLY, "control", 4, "NON_AFFINE_COMPONENT")
    if instance_id == "invalid_cross_clause":
        formula = _saf_formula(4, mode="sat")
        raw = formula.to_clause_lists()
        raw.append([2, 4])
        return SeparatorAffineFamilyInstance(instance_id, CNFFormula.from_raw_clauses(raw), [1], 1, 2, DIAGNOSTIC_ONLY, "control", 4, "INVALID_CROSS_CLAUSE")
    if instance_id in {
        "incomplete_unsat_cover",
        "bad_component_affine_certificate",
        "bad_sat_witness",
        "tamper_certificate",
        "tamper_separator_assignment",
        "fake_drat_claim",
        "fake_pnp_claim",
        "fake_completeness_claim",
        "hard_unknown_status_reject",
    }:
        base = valid(4, "unsat_cover" if instance_id == "incomplete_unsat_cover" else "sat", SAT_CERTIFIED, "control")
        return SeparatorAffineFamilyInstance(
            instance_id=instance_id,
            formula=base.formula,
            separator_variables=base.separator_variables,
            separator_bound_c=base.separator_bound_c,
            affine_arity_bound_r=base.affine_arity_bound_r,
            expected_result=UNSAT_CERTIFIED if instance_id == "incomplete_unsat_cover" else SAT_CERTIFIED,
            family="control",
            n=4,
            control_kind=instance_id.upper(),
        )
    raise ValueError(f"unsupported separator-affine instance: {instance_id}")


def _affine_component_certificate(instance_id: str, component_formula: CNFFormula, *, max_arity: int) -> dict[str, Any]:
    affine_instance = AffineResidueInstance(
        instance_id=instance_id,
        equations=(),
        formula=component_formula,
        family="separator-affine-component",
        expected_outcome="component",
        g1_result="NOT_APPLICABLE",
        description="Residual component in SAF(c,r).",
    )
    cert = build_affine_residue_certificate(affine_instance, max_arity=max_arity).to_dict()
    return cert


def build_separator_affine_certificate(instance: SeparatorAffineFamilyInstance) -> SeparatorAffineFamilyCertificate:
    separator = list(instance.separator_variables)
    c = int(instance.separator_bound_c)
    r = int(instance.affine_arity_bound_r)
    components = _component_dicts(instance.formula, separator)
    assignments = _all_assignments(separator)
    assignment_records: list[dict[str, Any]] = []
    all_sat_record: dict[str, Any] | None = None
    blocked_by: dict[str, str] = {}
    component_certificate_size = 0
    for idx, assignment in enumerate(assignments, start=1):
        assignment_id = f"S{idx}"
        residual_formula, component_formulas, localization_errors = _condition_by_separator(instance.formula, assignment, components)
        component_records: list[dict[str, Any]] = []
        assignment_all_sat = not localization_errors
        first_unsat: str | None = None
        for component in components:
            cid = component["component_id"]
            component_formula = component_formulas[cid]
            affine_cert = _affine_component_certificate(f"{instance.instance_id}_{assignment_id}_{cid}", component_formula, max_arity=r)
            component_certificate_size += len(stable_json(affine_cert))
            affine_check = check_affine_residue_certificate(component_formula, affine_cert, max_arity=r)
            gf2_status = affine_check.get("gf2_status")
            component_result = "SAT" if affine_check["status"] == AFFINE_RESIDUE_CERTIFICATE_VERIFIED and gf2_status == "SAT" else "UNSAT" if affine_check["status"] == AFFINE_RESIDUE_CERTIFICATE_VERIFIED and gf2_status == "UNSAT" else DIAGNOSTIC_ONLY
            if component_result != "SAT":
                assignment_all_sat = False
            if component_result == "UNSAT" and first_unsat is None:
                first_unsat = cid
            component_records.append(
                {
                    "component_id": cid,
                    "variable_set": component["variables"],
                    "residual_component_hash": component_formula.formula_hash,
                    "affine_detection_status": SEPARATOR_AFFINE_COMPONENT_AFFINE_VERIFIED
                    if affine_check["status"] == AFFINE_RESIDUE_CERTIFICATE_VERIFIED
                    else SEPARATOR_AFFINE_CERTIFICATE_FAILED,
                    "affine_certificate": affine_cert,
                    "component_result": component_result,
                    "component_witness": affine_cert.get("solution") if component_result == "SAT" else None,
                    "component_unsat_certificate": affine_cert if component_result == "UNSAT" else None,
                }
            )
        assignment_result = ALL_COMPONENTS_SAT if assignment_all_sat else SOME_COMPONENT_UNSAT if first_unsat else DIAGNOSTIC_ONLY
        record = {
            "assignment_id": assignment_id,
            "separator_assignment": _assignment_key(assignment),
            "residual_formula_hash": residual_formula.formula_hash,
            "component_records": component_records,
            "assignment_result": assignment_result,
            "localization_errors": localization_errors,
        }
        assignment_records.append(record)
        if assignment_result == ALL_COMPONENTS_SAT and all_sat_record is None:
            all_sat_record = record
        if first_unsat:
            blocked_by[assignment_id] = first_unsat

    final_result = SAT_CERTIFIED if all_sat_record is not None else UNSAT_CERTIFIED if len(blocked_by) == len(assignments) else DIAGNOSTIC_ONLY
    sat_witness = None
    unsat_cover = None
    if final_result == SAT_CERTIFIED and all_sat_record is not None:
        chosen_assignment = _assignment_from_payload(all_sat_record["separator_assignment"])
        combined = dict(chosen_assignment)
        component_witnesses: dict[str, dict[str, bool]] = {}
        for component_record in all_sat_record["component_records"]:
            witness = dict(component_record["component_witness"] or {})
            component_witnesses[component_record["component_id"]] = witness
            combined.update(_assignment_from_payload(witness))
        sat_witness = {
            "chosen_separator_assignment": all_sat_record["separator_assignment"],
            "component_witnesses": component_witnesses,
            "combined_assignment": _assignment_key(combined),
            "verified_against_original_cnf": formula_satisfied(instance.formula, combined),
        }
    elif final_result == UNSAT_CERTIFIED:
        unsat_cover = {
            "every_separator_assignment_covered": len(blocked_by) == len(assignments),
            "covering_unsat_component_per_assignment": blocked_by,
            "affine_unsat_certificates": [
                {
                    "assignment_id": record["assignment_id"],
                    "component_id": blocked_by.get(record["assignment_id"]),
                    "affine_certificate": next(
                        (
                            component["component_unsat_certificate"]
                            for component in record["component_records"]
                            if component["component_id"] == blocked_by.get(record["assignment_id"])
                        ),
                        None,
                    ),
                }
                for record in assignment_records
                if record["assignment_id"] in blocked_by
            ],
        }

    data = {
        "type": "SEPARATOR_AFFINE_FAMILY_CERTIFICATE",
        "instance_id": instance.instance_id,
        "formula_hash": instance.formula.formula_hash,
        "grammar": G14_GRAMMAR,
        "family_parameters": {
            "separator_bound_c": c,
            "affine_arity_bound_r": r,
            "separator_size": len(separator),
        },
        "separator_variables": separator,
        "primal_graph_summary": {
            "graph_model": "PRIMAL",
            "variable_count": len(instance.formula.variables),
            "edge_count": sum(len(v) for v in primal_graph(instance.formula).values()) // 2,
        },
        "separator_verification": {
            "separator_valid": len(separator) <= c,
            "components_after_removal": components,
            "no_cross_component_clause_after_separator_assignment": True,
        },
        "separator_assignments": assignment_records,
        "final_result": final_result,
        "sat_witness": sat_witness,
        "unsat_cover": unsat_cover,
        "polynomial_bound_record": {
            "separator_assignment_count": len(assignments),
            "component_certificate_total_size": component_certificate_size,
            "certificate_size_bound_claim": "O(n^c * 2^c * poly(n)) recognition and polynomial certificate size for fixed c and supported affine bound r.",
            "checker_time_bound_claim": "Polynomial for fixed separator bound c and supported exact affine extraction arity r; exponential dependence on c is explicit.",
        },
        "theorem_record_reference": "theory/BOUNDED_SEPARATOR_AFFINE_COLLAPSE_THEOREM.md",
        "checker_status": "NOT_RUN",
        "status": SEPARATOR_AFFINE_FAMILY_RECOGNIZED,
        "public_category": SEPARATOR_AFFINE_FAMILY_THEOREM_RESTRICTED,
        "claim_boundary": "Restricted SAF(c,r) family theorem sketch with native certificates; no DRAT, no all-SAT, no hierarchy-completeness, and no P-vs-NP claim.",
    }

    if instance.control_kind == "BAD_COMPONENT_AFFINE_CERTIFICATE":
        data["separator_assignments"][0]["component_records"][0]["affine_certificate"]["formula_hash"] = "tampered"
    elif instance.control_kind == "BAD_SAT_WITNESS":
        if data["sat_witness"]:
            first = next(iter(data["sat_witness"]["combined_assignment"]))
            data["sat_witness"]["combined_assignment"][first] = not data["sat_witness"]["combined_assignment"][first]
            data["sat_witness"]["verified_against_original_cnf"] = False
    elif instance.control_kind in {"TAMPER_CERTIFICATE", "TAMPER_SEPARATOR_ASSIGNMENT"}:
        data["separator_assignments"][0]["separator_assignment"][str(separator[0])] = not data["separator_assignments"][0]["separator_assignment"][str(separator[0])]
    elif instance.control_kind == "FAKE_DRAT_CLAIM":
        data["claim_boundary"] += " DRAT proof claimed."
    elif instance.control_kind == "FAKE_PNP_CLAIM":
        data["claim_boundary"] += " P vs NP progress."
    elif instance.control_kind == "FAKE_COMPLETENESS_CLAIM":
        data["claim_boundary"] += " hierarchy completeness and all SAT."
    elif instance.control_kind == "HARD_UNKNOWN_STATUS_REJECT":
        data["status"] = "UNKNOWN"
    elif instance.instance_id == "incomplete_unsat_cover":
        if data["unsat_cover"] and data["unsat_cover"]["covering_unsat_component_per_assignment"]:
            first_key = sorted(data["unsat_cover"]["covering_unsat_component_per_assignment"])[0]
            del data["unsat_cover"]["covering_unsat_component_per_assignment"][first_key]
            data["unsat_cover"]["every_separator_assignment_covered"] = False

    check = check_separator_affine_certificate(instance.formula, data)
    data["checker_status"] = check["checker_status"]
    data["status"] = (
        SEPARATOR_AFFINE_SAT_WITNESS_LIFTED
        if check["checker_status"] == SEPARATOR_AFFINE_CERTIFICATE_VERIFIED and final_result == SAT_CERTIFIED
        else SEPARATOR_AFFINE_UNSAT_COVER_VERIFIED
        if check["checker_status"] == SEPARATOR_AFFINE_CERTIFICATE_VERIFIED and final_result == UNSAT_CERTIFIED
        else SEPARATOR_AFFINE_CERTIFICATE_FAILED
    )
    if instance.control_kind == "HARD_UNKNOWN_STATUS_REJECT":
        data["status"] = "UNKNOWN"
        data["checker_status"] = SEPARATOR_AFFINE_CERTIFICATE_FAILED
    return SeparatorAffineFamilyCertificate(**data)


def _same_components(left: list[dict[str, Any]], right: list[dict[str, Any]]) -> bool:
    """Check exact recomputed component metadata, not just vertex sets."""
    return left == right


def _branch_partition_exact(
    residual: CNFFormula, components: dict[str, CNFFormula],
) -> bool:
    """Every surviving clause must occur exactly once across components."""
    expected = Counter(tuple(clause) for clause in residual.clauses)
    actual = Counter(
        tuple(clause)
        for component in components.values()
        for clause in component.clauses
    )
    return expected == actual


def _status_values(data: Any) -> list[str]:
    values: list[str] = []
    if isinstance(data, dict):
        for key, value in data.items():
            if key in {"status", "checker_status", "public_category", "final_result", "assignment_result", "component_result"} and isinstance(value, str):
                values.append(value)
            values.extend(_status_values(value))
    elif isinstance(data, list):
        for item in data:
            values.extend(_status_values(item))
    return values


def _affine_source_clause_coverage(affine_cert: dict[str, Any]) -> set[int]:
    covered: set[int] = set()
    for equation in affine_cert.get("equations", []):
        covered.update(int(clause_id) for clause_id in equation.get("source_clause_ids", []))
    return covered


def check_separator_affine_certificate(
    formula: CNFFormula,
    certificate: SeparatorAffineFamilyCertificate | dict[str, Any],
) -> dict[str, Any]:
    data = certificate.to_dict() if isinstance(certificate, SeparatorAffineFamilyCertificate) else dict(certificate)
    errors: list[str] = []
    if data.get("type") != "SEPARATOR_AFFINE_FAMILY_CERTIFICATE":
        errors.append("BAD_CERTIFICATE_TYPE")
    if data.get("grammar") != G14_GRAMMAR:
        errors.append("BAD_GRAMMAR")
    if str(data.get("formula_hash", "")).lower() != formula.formula_hash.lower():
        errors.append("FORMULA_HASH_MISMATCH")
    params = data.get("family_parameters", {})
    c = int(params.get("separator_bound_c", -1))
    r = int(params.get("affine_arity_bound_r", -1))
    separator = [int(var) for var in data.get("separator_variables", [])]
    if any(var not in formula.variables for var in separator):
        errors.append("SEPARATOR_VARIABLE_NOT_IN_FORMULA")
    if len(set(separator)) != len(separator):
        errors.append("SEPARATOR_VARIABLE_DUPLICATE")
    if len(separator) > c:
        errors.append("SEPARATOR_SIZE_OVER_BOUND")
    if int(params.get("separator_size", -1)) != len(separator):
        errors.append("SEPARATOR_SIZE_MISMATCH")

    recomputed_components = _component_dicts(formula, separator)
    claimed_components = list(data.get("separator_verification", {}).get("components_after_removal", []))
    if not _same_components(claimed_components, recomputed_components):
        errors.append("COMPONENTS_AFTER_REMOVAL_MISMATCH")
    seen_vars: set[int] = set()
    for component in claimed_components:
        for var in component.get("variables", []):
            var = int(var)
            if var in seen_vars:
                errors.append("NON_SEPARATOR_VARIABLE_IN_MULTIPLE_COMPONENTS")
            seen_vars.add(var)

    assignments = _all_assignments(separator)
    records = {record.get("assignment_id"): record for record in data.get("separator_assignments", [])}
    if len(records) != 2 ** len(separator):
        errors.append("SEPARATOR_ASSIGNMENT_COUNT_MISMATCH")
    all_sat_assignment: dict[str, Any] | None = None
    cover: dict[str, str] = {}
    for idx, assignment in enumerate(assignments, start=1):
        assignment_id = f"S{idx}"
        record = records.get(assignment_id)
        if record is None:
            errors.append(f"SEPARATOR_ASSIGNMENT_MISSING:{assignment_id}")
            continue
        if _assignment_from_payload(record.get("separator_assignment")) != assignment:
            errors.append(f"SEPARATOR_ASSIGNMENT_TAMPER:{assignment_id}")
        residual_formula, component_formulas, localization_errors = _condition_by_separator(formula, assignment, recomputed_components)
        if localization_errors:
            errors.extend(localization_errors)
        if not _branch_partition_exact(residual_formula, component_formulas):
            errors.append(f"RESIDUAL_CLAUSE_PARTITION_MISMATCH:{assignment_id}")
        if str(record.get("residual_formula_hash", "")).lower() != residual_formula.formula_hash.lower():
            errors.append(f"RESIDUAL_FORMULA_HASH_MISMATCH:{assignment_id}")
        component_records = {item.get("component_id"): item for item in record.get("component_records", [])}
        component_results: dict[str, str] = {}
        for component in recomputed_components:
            cid = component["component_id"]
            component_record = component_records.get(cid)
            if component_record is None:
                errors.append(f"COMPONENT_RECORD_MISSING:{assignment_id}:{cid}")
                continue
            component_formula = component_formulas[cid]
            if str(component_record.get("residual_component_hash", "")).lower() != component_formula.formula_hash.lower():
                errors.append(f"COMPONENT_HASH_MISMATCH:{assignment_id}:{cid}")
            affine_cert = component_record.get("affine_certificate") or {}
            affine_check = check_affine_residue_certificate(component_formula, affine_cert, max_arity=r)
            if affine_check["status"] != AFFINE_RESIDUE_CERTIFICATE_VERIFIED:
                errors.append(f"COMPONENT_AFFINE_CERT_FAILED:{assignment_id}:{cid}")
            covered_clause_ids = _affine_source_clause_coverage(affine_cert)
            expected_clause_ids = set(range(1, len(component_formula.clauses) + 1))
            if covered_clause_ids != expected_clause_ids:
                errors.append(f"COMPONENT_NOT_EXACT_AFFINE:{assignment_id}:{cid}")
            gf2_status = affine_check.get("gf2_status")
            expected_component_result = "SAT" if gf2_status == "SAT" else "UNSAT" if gf2_status == "UNSAT" else DIAGNOSTIC_ONLY
            component_results[cid] = expected_component_result
            if component_record.get("component_result") != expected_component_result:
                errors.append(f"COMPONENT_RESULT_MISMATCH:{assignment_id}:{cid}")
            if expected_component_result == "SAT":
                witness = _assignment_from_payload(component_record.get("component_witness"))
                if not witness or not formula_satisfied(component_formula, witness):
                    errors.append(f"COMPONENT_SAT_WITNESS_INVALID:{assignment_id}:{cid}")
        expected_assignment_result = ALL_COMPONENTS_SAT if component_results and all(value == "SAT" for value in component_results.values()) and not localization_errors else SOME_COMPONENT_UNSAT if any(value == "UNSAT" for value in component_results.values()) else DIAGNOSTIC_ONLY
        if record.get("assignment_result") != expected_assignment_result:
            errors.append(f"ASSIGNMENT_RESULT_MISMATCH:{assignment_id}")
        if expected_assignment_result == ALL_COMPONENTS_SAT and all_sat_assignment is None:
            all_sat_assignment = record
        if expected_assignment_result == SOME_COMPONENT_UNSAT:
            cover[assignment_id] = next(cid for cid, value in component_results.items() if value == "UNSAT")

    final_result = data.get("final_result")
    if final_result == SAT_CERTIFIED:
        if all_sat_assignment is None:
            errors.append("SAT_WITHOUT_ALL_COMPONENTS_SAT_ASSIGNMENT")
        sat = data.get("sat_witness") or {}
        combined = _assignment_from_payload(sat.get("combined_assignment"))
        if not combined or sat.get("verified_against_original_cnf") is not True or not formula_satisfied(formula, combined):
            errors.append("SAT_WITNESS_DOES_NOT_SATISFY_ORIGINAL_CNF")
    elif final_result == UNSAT_CERTIFIED:
        if len(cover) != 2 ** len(separator):
            errors.append("UNSAT_COVER_INCOMPLETE")
        unsat_cover = data.get("unsat_cover") or {}
        if unsat_cover.get("every_separator_assignment_covered") is not True:
            errors.append("UNSAT_COVER_FLAG_FALSE")
        claimed_cover = {str(k): str(v) for k, v in (unsat_cover.get("covering_unsat_component_per_assignment") or {}).items()}
        if claimed_cover != cover:
            errors.append("UNSAT_COVER_COMPONENT_MISMATCH")
    else:
        errors.append("FINAL_RESULT_NOT_CERTIFIED")

    poly = data.get("polynomial_bound_record", {})
    if int(poly.get("separator_assignment_count", -1)) != 2 ** len(separator):
        errors.append("POLYNOMIAL_BOUND_ASSIGNMENT_COUNT_MISMATCH")
    bound_text = f"{poly.get('certificate_size_bound_claim', '')} {poly.get('checker_time_bound_claim', '')}".lower()
    if "fixed" not in bound_text or "c" not in bound_text:
        errors.append("POLYNOMIAL_BOUND_NOT_FIXED_C_SCOPED")

    claim_boundary = str(data.get("claim_boundary", "")).lower()
    for fragment in FORBIDDEN_CLAIM_FRAGMENTS:
        if fragment in claim_boundary:
            errors.append("FORBIDDEN_CLAIM:" + fragment.upper().replace(" ", "_"))
    forbidden_statuses = sorted(set(_status_values(data)) & FORBIDDEN_STATUS_VALUES)
    if forbidden_statuses:
        errors.append("FORBIDDEN_STATUS:" + ",".join(forbidden_statuses))
    if "drat proof claimed" in claim_boundary:
        errors.append("FAKE_DRAT_CLAIM")

    checker_status = SEPARATOR_AFFINE_CERTIFICATE_VERIFIED if not errors else SEPARATOR_AFFINE_CERTIFICATE_FAILED
    return {
        "checker_status": checker_status,
        "status": checker_status,
        "errors": errors,
        "separator_size": len(separator),
        "component_count": len(recomputed_components),
        "separator_assignment_count": 2 ** len(separator),
        "final_result": final_result,
        "claim_boundary": "Restricted SAF(c,r) native certificate check only; no DRAT, no completeness, no P-vs-NP claim.",
    }


def recognize_separator_affine_family(formula: CNFFormula, *, c: int = 1, r: int = 2) -> dict[str, Any]:
    variables = list(formula.variables)
    trace: list[dict[str, Any]] = []
    for size in range(1, min(c, len(variables)) + 1):
        for candidate in combinations(variables, size):
            components = _component_dicts(formula, list(candidate))
            ok = len(components) >= 2
            reason = "candidate accepted"
            for assignment in _all_assignments(candidate):
                _, component_formulas, localization_errors = _condition_by_separator(formula, assignment, components)
                if localization_errors:
                    ok = False
                    reason = "residual clause spans components"
                    break
                for cid, component_formula in component_formulas.items():
                    cert = _affine_component_certificate(f"recognition_{cid}", component_formula, max_arity=r)
                    if check_affine_residue_certificate(component_formula, cert, max_arity=r)["status"] != AFFINE_RESIDUE_CERTIFICATE_VERIFIED:
                        ok = False
                        reason = "component not exact affine"
                        break
                if not ok:
                    break
            row = {"separator": list(candidate), "component_count": len(components), "accepted": ok, "reason": reason}
            trace.append(row)
            if ok:
                return {
                    "status": SEPARATOR_AFFINE_FAMILY_RECOGNIZED,
                    "separator_variables": list(candidate),
                    "components": components,
                    "trace": trace,
                    "complexity": "O(n^c * 2^c * poly(n)) for fixed c and supported affine arity r.",
                }
    return {
        "status": DIAGNOSTIC_ONLY,
        "separator_variables": [],
        "components": [],
        "trace": trace,
        "complexity": "Recognition is polynomial only for fixed c; no SAF(c,r) row accepted.",
    }


def _report(rows: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    lines = [
        "# Bounded Separator-Affine Theorem Report",
        "",
        "v2.22 states a restricted family theorem for SAF(c,r): fixed-size primal separators whose separator-conditioned residual components are exact affine CNFs accepted by G5.",
        "",
        "SAT requires one separator assignment where every component is SAT. UNSAT requires every separator assignment to be covered by at least one affine-UNSAT component.",
        "",
        "This is not P vs NP progress, not all SAT, not hierarchy completeness, and not DRAT unless externally checked.",
        "",
        "## Summary",
        "",
        "```json",
        stable_json(summary),
        "```",
        "",
        "## Rows",
        "",
    ]
    for row in rows:
        lines.append(f"- {row['instance_id']}: {row['final_result']} / {row['checker_status']} / {row['family']}")
    lines.append("")
    return "\n".join(lines)


def run_separator_affine_family_lab(
    instances: Iterable[str],
    out_root: str | Path,
    *,
    strict: bool = False,
    zip_path: str | Path | None = "witnora-core-v2.22-bounded-separator-affine-family-theorem.zip",
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    certificates: list[dict[str, Any]] = []
    checker_rows: list[dict[str, Any]] = []
    recognition_rows: list[dict[str, Any]] = []
    cover_rows: list[dict[str, Any]] = []
    polynomial_rows: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for instance_id in instances:
        instance = make_separator_affine_instance(instance_id)
        cert = build_separator_affine_certificate(instance)
        cert_data = cert.to_dict()
        check = check_separator_affine_certificate(instance.formula, cert_data)
        recognition = recognize_separator_affine_family(instance.formula, c=instance.separator_bound_c, r=instance.affine_arity_bound_r)
        certificates.append(cert_data)
        checker_rows.append({"instance_id": instance_id, **check})
        recognition_rows.append({"instance_id": instance_id, "recognition": recognition})
        cover_rows.append(
            {
                "instance_id": instance_id,
                "final_result": cert.final_result,
                "assignment_count": len(cert.separator_assignments),
                "unsat_cover": cert.unsat_cover,
                "sat_witness_assignment": cert.sat_witness.get("chosen_separator_assignment") if cert.sat_witness else None,
            }
        )
        polynomial_rows.append({"instance_id": instance_id, **cert.polynomial_bound_record})
        rows.append(
            {
                "instance_id": instance_id,
                "family": instance.family,
                "n": instance.n,
                "final_result": cert.final_result,
                "checker_status": check["checker_status"],
                "control_kind": instance.control_kind,
            }
        )
        cnf_path = root / "original_cnf" / f"{instance_id}.cnf"
        cnf_path.parent.mkdir(parents=True, exist_ok=True)
        cnf_path.write_text(instance.formula.canonical_dimacs(), encoding="utf-8", newline="\n")

    verified = [row for row in rows if row["checker_status"] == SEPARATOR_AFFINE_CERTIFICATE_VERIFIED]
    controls = [row for row in rows if row["control_kind"]]
    summary = {
        "grammar": G14_GRAMMAR,
        "theorem": "Bounded Separator-Affine Collapse Theorem",
        "theorem_status": "RESTRICTED_FAMILY_THEOREM_PROOF_SKETCH",
        "scope": "SAF(c,r)",
        "instances_total": len(rows),
        "verified_certificates": len(verified),
        "sat_certified": sum(1 for row in verified if row["final_result"] == SAT_CERTIFIED),
        "unsat_certified": sum(1 for row in verified if row["final_result"] == UNSAT_CERTIFIED),
        "controls_rejected": sum(1 for row in controls if row["checker_status"] == SEPARATOR_AFFINE_CERTIFICATE_FAILED),
        "polynomiality_boundary": "Polynomial only for fixed separator bound c and supported exact affine extraction arity r.",
        "sat_rule": "There exists one separator assignment alpha for which all components are SAT.",
        "unsat_rule": "Every separator assignment alpha is covered by at least one affine-UNSAT component.",
        "claim_boundary": "Restricted SAF(c,r) family theorem sketch; no P-vs-NP, all-SAT, hierarchy-completeness, or fake DRAT claim.",
        "strict": bool(strict),
    }
    claim_boundary = [
        {
            "claim": "restricted family theorem",
            "allowed": "Bounded Separator-Affine Collapse Theorem for SAF(c,r).",
            "forbidden": "All separator formulas or all SAT.",
        },
        {
            "claim": "polynomial time",
            "allowed": "Polynomial for fixed c and supported affine extraction.",
            "forbidden": "Polynomial-time SAT for arbitrary formulas.",
        },
        {
            "claim": "native certificate",
            "allowed": "Native separator-affine certificate.",
            "forbidden": "DRAT proof unless externally checked.",
        },
    ]
    evidence = {
        "uses": ["G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE", "G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE"],
        "supporting_releases": ["v2.6-affine-residue-collapse", "v2.15-graph-separator-lift", "v2.21-theoremization-g9-g13-soundness"],
        "finite_tests_note": "Finite n tests support implementation only; theorem content comes from the SAF(c,r) definition and proof sketch.",
    }
    _write_json(root / "separator_affine_family_certificates.json", {"certificates": certificates})
    _write_json(root / "separator_affine_checker_summary.json", {"checks": checker_rows})
    _write_json(root / "separator_affine_family_recognition_summary.json", {"recognition": recognition_rows})
    _write_json(root / "separator_assignment_cover_summary.json", {"rows": cover_rows})
    _write_json(root / "polynomial_bound_summary.json", {"rows": polynomial_rows})
    _write_json(root / "g14_family_theorem_summary.json", summary)
    _write_json(root / "theorem_evidence_linkage.json", evidence)
    _write_json(root / "claim_boundary_audit.json", claim_boundary)
    _write_text(root / "BOUNDED_SEPARATOR_AFFINE_THEOREM_REPORT.md", _report(rows, summary))
    if strict and not all((not row["control_kind"] and row["checker_status"] == SEPARATOR_AFFINE_CERTIFICATE_VERIFIED) or (row["control_kind"] and row["checker_status"] == SEPARATOR_AFFINE_CERTIFICATE_FAILED) for row in rows):
        raise RuntimeError("strict separator-affine lab failed")
    digest = _make_zip(root, zip_path) if zip_path else ""
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": digest,
        "rows": rows,
        "separator_affine_family_certificates": certificates,
        "separator_affine_checker_summary": checker_rows,
        "separator_affine_family_recognition_summary": recognition_rows,
        "separator_assignment_cover_summary": cover_rows,
        "polynomial_bound_summary": polynomial_rows,
        "g14_family_theorem_summary": summary,
        "theorem_evidence_linkage": evidence,
    }


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _cmd_run(args: argparse.Namespace) -> int:
    result = run_separator_affine_family_lab(args.instances, args.out_root, strict=args.strict, zip_path=args.zip)
    print(stable_json({"out_root": result["out_root"], "zip": result["zip"], "zip_sha256": result["zip_sha256"], "summary": result["g14_family_theorem_summary"]}))
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    if args.lean:
        formula, raw_clauses, source_tokens, source_spellings, source_text = load_dimacs_with_document_evidence(args.cnf)
    else:
        formula = load_dimacs(args.cnf)
    cert = _load_json(args.certificate)
    result = check_separator_affine_certificate(formula, cert)
    if not args.lean:
        print(stable_json(result))
        return 0 if result["checker_status"] == SEPARATOR_AFFINE_CERTIFICATE_VERIFIED else 1
    from .lean_g14_gate import verify_g14_unsat_cover_with_lean
    formal = verify_g14_unsat_cover_with_lean(
        formula, cert, timeout_seconds=args.lean_timeout,
        raw_clauses=raw_clauses, source_tokens=source_tokens,
            source_spellings=source_spellings, source_text=source_text,
    )
    print(stable_json({"native_check": result, "lean_cover_check": formal}))
    return 0 if formal["verified"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m witnora_core.separator_affine_family_theorem")
    sub = parser.add_subparsers(dest="cmd", required=True)
    run = sub.add_parser("run")
    run.add_argument(
        "--instances",
        nargs="+",
        default=[
            "saf_sat_chain_4",
            "saf_sat_chain_8",
            "saf_unsat_cover_4",
            "saf_unsat_cover_8",
            "saf_mixed_components_6",
            "invalid_large_separator",
            "non_affine_component",
            "invalid_cross_clause",
            "incomplete_unsat_cover",
            "tamper_certificate",
        ],
    )
    run.add_argument("--out-root", default="outputs/v2.22-bounded-separator-affine-family-theorem")
    run.add_argument("--strict", action="store_true")
    run.add_argument("--zip", default="witnora-core-v2.22-bounded-separator-affine-family-theorem.zip")
    run.set_defaults(func=_cmd_run)
    check = sub.add_parser("check")
    check.add_argument("--cnf", required=True)
    check.add_argument("--certificate", required=True)
    check.add_argument("--lean", action="store_true", help="require a Lean G5 proof for each UNSAT-cover branch")
    check.add_argument("--lean-timeout", type=int, default=120)
    check.set_defaults(func=_cmd_check)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
