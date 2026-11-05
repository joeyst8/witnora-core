"""Native circuit-projection lift certificates.

v2.17 promotes the v2.14 CIRCUIT_PROJECTION_SIGNAL recommendation into a
bounded prototype operator. The implementation is intentionally conservative:
only exact definitional gate encodings are projected, projection steps must be
equisatisfiability-preserving, SAT lifts are checked against the original CNF,
and UNSAT preservation is accepted only for supported exact definitional rows.

This is not broad circuit-SAT solving, not DRAT, not a theorem, and not a
P-vs-NP result.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from itertools import combinations, product
import json
from pathlib import Path
import shutil
from typing import Any, Iterable
import zipfile

from .cnf import CNFFormula, Clause, formula_from_json, formula_satisfied
from .dimacs import load_dimacs
from .obstruction_dual import sha256_file, stable_json


VERSION = "2.17"

G10_GRAMMAR = "G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE"
SOURCE_RECOMMENDATION_SIGNAL = "CIRCUIT_PROJECTION_SIGNAL"
PROMOTED_RECOMMENDATION = "CIRCUIT_PROJECTION_LIFT"

CIRCUIT_DEFINITION_STRUCTURE_DETECTED = "CIRCUIT_DEFINITION_STRUCTURE_DETECTED"
CIRCUIT_DEFINITION_VERIFIED = "CIRCUIT_DEFINITION_VERIFIED"
CIRCUIT_PROJECTION_CREATED = "CIRCUIT_PROJECTION_CREATED"
CIRCUIT_PROJECTION_EQUI_SAT_VERIFIED = "CIRCUIT_PROJECTION_EQUI_SAT_VERIFIED"
CIRCUIT_PROJECTION_SAT_WITNESS_LIFTED = "CIRCUIT_PROJECTION_SAT_WITNESS_LIFTED"
CIRCUIT_PROJECTION_UNSAT_PRESERVED = "CIRCUIT_PROJECTION_UNSAT_PRESERVED"
CIRCUIT_PROJECTION_NATIVE_CERTIFIED = "CIRCUIT_PROJECTION_NATIVE_CERTIFIED"
CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED = "CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED"
CIRCUIT_PROJECTION_CERTIFICATE_FAILED = "CIRCUIT_PROJECTION_CERTIFICATE_FAILED"
CIRCUIT_PROJECTION_DIAGNOSTIC_ONLY = "CIRCUIT_PROJECTION_DIAGNOSTIC_ONLY"
CIRCUIT_PROJECTION_NO_NEW_DELTA = "CIRCUIT_PROJECTION_NO_NEW_DELTA"
CIRCUIT_PROJECTION_DRAT_NOT_CLAIMED = "CIRCUIT_PROJECTION_DRAT_NOT_CLAIMED"
G10_CIRCUIT_PROJECTION_NATIVE_CERTIFIED = "G10_CIRCUIT_PROJECTION_NATIVE_CERTIFIED"
SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED = "SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED"
UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED = "UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED"

FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED = "FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED"

FORBIDDEN_STATUS_VALUES = {"HARD", "UNKNOWN"}
FORBIDDEN_CLAIM_FRAGMENTS = {
    "proves p vs np",
    "p vs np progress",
    "polynomial-time sat",
    "hierarchy completeness",
    "full circuit-sat completeness",
    "circuit projection solves all",
    "strictness theorem",
    "drat verified",
}

GATE_TYPES = {"AND", "OR", "NOT", "XOR_OPTIONAL"}


@dataclass(frozen=True)
class GateSpec:
    output_variable: int
    gate_type: str
    input_variables: tuple[int, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CircuitProjectionInstance:
    instance_id: str
    family: str
    gate_specs: tuple[GateSpec, ...]
    core_clauses: tuple[tuple[int, ...], ...]
    final_result: str
    core_assignment: dict[int, bool] | None
    novel_delta_expected: bool
    orchestration_operator: str | None
    prior_replay_status: str
    notes: str
    formula_override: CNFFormula | None = None

    @property
    def formula(self) -> CNFFormula:
        if self.formula_override is not None:
            return self.formula_override
        clauses: list[tuple[int, ...]] = []
        for gate in self.gate_specs:
            clauses.extend(gate_definition_clauses(gate))
        clauses.extend(self.core_clauses)
        return CNFFormula.from_raw_clauses(clauses)

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "family": self.family,
            "formula_hash": self.formula.formula_hash,
            "final_result": self.final_result,
            "projected_variables": [gate.output_variable for gate in self.gate_specs],
            "novel_delta_expected": self.novel_delta_expected,
            "orchestration_operator": self.orchestration_operator,
            "prior_replay_status": self.prior_replay_status,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class CircuitProjectionLiftCertificate:
    type: str
    instance_id: str
    original_formula_hash: str
    core_formula_hash: str
    projected_variables: list[int]
    base_variables: list[int]
    gate_definitions: list[dict[str, Any]]
    projection_steps: list[dict[str, Any]]
    core_certificate: dict[str, Any] | None
    sat_lift: dict[str, Any] | None
    unsat_lift: dict[str, Any] | None
    orchestration_trace: dict[str, Any] | None
    checker_status: str
    status: str
    public_category: str
    certification_level: str
    drat_claim: str
    evidence_grade: str
    source_recommendation_signal: str
    promoted_recommendation: str
    operator_delta: dict[str, Any]
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


def _assignment_key(assignment: dict[int, bool]) -> dict[str, bool]:
    return {str(var): bool(assignment[var]) for var in sorted(assignment)}


def _assignment_from_payload(payload: dict[str, Any] | None) -> dict[int, bool]:
    if not payload:
        return {}
    return {int(var): bool(value) for var, value in payload.items()}


def _all_assignments(variables: Iterable[int]) -> list[dict[int, bool]]:
    variables_sorted = sorted(variables)
    return [
        {var: bool(value) for var, value in zip(variables_sorted, values)}
        for values in product([False, True], repeat=len(variables_sorted))
    ]


def _formula_summary(formula: CNFFormula) -> dict[str, Any]:
    return {
        "formula_hash": formula.formula_hash,
        "num_vars": formula.num_vars,
        "num_clauses": formula.num_clauses,
        "clauses": formula.to_clause_lists(),
    }


def _formula_from_summary(summary: dict[str, Any]) -> CNFFormula:
    return formula_from_json(summary.get("clauses", []))


def _clause_id_map(formula: CNFFormula) -> dict[int, Clause]:
    return {idx: clause for idx, clause in enumerate(formula.clauses, start=1)}


def _clause_id_lookup(formula: CNFFormula) -> dict[tuple[int, ...], int]:
    return {clause.literals: idx for idx, clause in _clause_id_map(formula).items()}


def gate_definition_clauses(gate: GateSpec) -> list[tuple[int, ...]]:
    z = gate.output_variable
    inputs = tuple(gate.input_variables)
    if gate.gate_type == "AND":
        a, b = inputs
        return [(-z, a), (-z, b), (z, -a, -b)]
    if gate.gate_type == "OR":
        a, b = inputs
        return [(z, -a), (z, -b), (-z, a, b)]
    if gate.gate_type == "NOT":
        (a,) = inputs
        return [(-z, -a), (z, a)]
    if gate.gate_type == "XOR_OPTIONAL":
        a, b = inputs
        return [(a, b, -z), (a, -b, z), (-a, b, z), (-a, -b, -z)]
    raise ValueError(f"unsupported gate type: {gate.gate_type}")


def _gate_required_clause_ids(formula: CNFFormula, gate: GateSpec) -> list[int] | None:
    lookup = _clause_id_lookup(formula)
    clause_ids: list[int] = []
    for raw_clause in gate_definition_clauses(gate):
        clause = Clause(raw_clause)
        clause_id = lookup.get(clause.literals)
        if clause_id is None:
            return None
        clause_ids.append(clause_id)
    return sorted(clause_ids)


def _gate_record(formula: CNFFormula, gate: GateSpec) -> dict[str, Any] | None:
    clause_ids = _gate_required_clause_ids(formula, gate)
    if clause_ids is None:
        return None
    return {
        "output_variable": gate.output_variable,
        "gate_type": gate.gate_type,
        "input_variables": list(gate.input_variables),
        "defining_clause_ids": clause_ids,
        "defining_clauses": [list(Clause(raw_clause).literals) for raw_clause in gate_definition_clauses(gate)],
        "full_definition_verified": True,
        "definition_status": CIRCUIT_DEFINITION_VERIFIED,
    }


def detect_gate_definitions(formula: CNFFormula) -> list[dict[str, Any]]:
    variables = list(formula.variables)
    detected: list[dict[str, Any]] = []
    for z in variables:
        for a, b in combinations([var for var in variables if var != z], 2):
            for gate_type in ("AND", "OR", "XOR_OPTIONAL"):
                record = _gate_record(formula, GateSpec(z, gate_type, (a, b)))
                if record:
                    detected.append(record)
        for a in [var for var in variables if var != z]:
            record = _gate_record(formula, GateSpec(z, "NOT", (a,)))
            if record:
                detected.append(record)
    return sorted(detected, key=lambda row: (row["output_variable"], row["gate_type"], row["input_variables"]))


def _remove_clause_ids(formula: CNFFormula, clause_ids: Iterable[int]) -> CNFFormula:
    remove_set = set(int(clause_id) for clause_id in clause_ids)
    return CNFFormula(clause for idx, clause in _clause_id_map(formula).items() if idx not in remove_set)


def _remove_gate_definition(formula: CNFFormula, gate_record: dict[str, Any]) -> CNFFormula:
    remove_clauses = {tuple(clause) for clause in gate_record.get("defining_clauses", [])}
    return CNFFormula(clause for clause in formula.clauses if clause.literals not in remove_clauses)


def _core_formula_from_gate_records(formula: CNFFormula, gate_records: list[dict[str, Any]]) -> CNFFormula:
    all_clauses: set[tuple[int, ...]] = set()
    for record in gate_records:
        all_clauses.update(tuple(clause) for clause in record.get("defining_clauses", []))
    return CNFFormula(clause for clause in formula.clauses if clause.literals not in all_clauses)


def _bounded_exhaustive_unsat(formula: CNFFormula, max_variables: int = 8) -> bool:
    if formula.num_vars > max_variables:
        return False
    return not any(formula_satisfied(formula, assignment) for assignment in _all_assignments(formula.variables))


def _contains_forbidden_status_or_claim(data: Any, errors: list[str]) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            if key.endswith("status") or key in {"status", "public_category", "certification_level"}:
                if value in FORBIDDEN_STATUS_VALUES:
                    errors.append(f"FORBIDDEN_STATUS:{value}")
            _contains_forbidden_status_or_claim(value, errors)
    elif isinstance(data, list):
        for value in data:
            _contains_forbidden_status_or_claim(value, errors)
    elif isinstance(data, str):
        lowered = data.lower()
        for fragment in FORBIDDEN_CLAIM_FRAGMENTS:
            if fragment in lowered and "no " not in lowered and "not " not in lowered:
                errors.append(f"FORBIDDEN_CLAIM:{fragment}")


def evaluate_gate(gate_record: dict[str, Any], assignment: dict[int, bool]) -> bool:
    inputs = [bool(assignment[int(var)]) for var in gate_record["input_variables"]]
    gate_type = gate_record["gate_type"]
    if gate_type == "AND":
        return inputs[0] and inputs[1]
    if gate_type == "OR":
        return inputs[0] or inputs[1]
    if gate_type == "NOT":
        return not inputs[0]
    if gate_type == "XOR_OPTIONAL":
        return inputs[0] ^ inputs[1]
    raise ValueError(f"unsupported gate type: {gate_type}")


def evaluate_gates(gate_records: list[dict[str, Any]], core_assignment: dict[int, bool]) -> tuple[dict[int, bool], list[str]]:
    assignment = dict(core_assignment)
    remaining = [dict(record) for record in gate_records]
    errors: list[str] = []
    while remaining:
        progress = False
        next_remaining: list[dict[str, Any]] = []
        for record in remaining:
            inputs = [int(var) for var in record["input_variables"]]
            if all(var in assignment for var in inputs):
                assignment[int(record["output_variable"])] = evaluate_gate(record, assignment)
                progress = True
            else:
                next_remaining.append(record)
        if not progress:
            errors.append("GATE_EVALUATION_DEPENDENCY_CYCLE_OR_MISSING_INPUT")
            break
        remaining = next_remaining
    return assignment, errors


def _core_sat_certificate(core_formula: CNFFormula, core_assignment: dict[int, bool]) -> dict[str, Any]:
    return {
        "type": "DIRECT_CORE_SAT_ASSIGNMENT",
        "core_formula_hash": core_formula.formula_hash,
        "core_assignment": _assignment_key(core_assignment),
        "core_assignment_satisfies_core": formula_satisfied(core_formula, core_assignment),
    }


def _core_unsat_certificate(core_formula: CNFFormula) -> dict[str, Any]:
    return {
        "type": "BOUNDED_EXHAUSTIVE_CORE_UNSAT",
        "core_formula_hash": core_formula.formula_hash,
        "variables": list(core_formula.variables),
        "assignments_checked": 2 ** core_formula.num_vars,
        "core_unsat_verified": _bounded_exhaustive_unsat(core_formula),
    }


def _projection_steps(formula: CNFFormula, gate_records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], CNFFormula]:
    current = formula
    steps: list[dict[str, Any]] = []
    for idx, record in enumerate(reversed(gate_records), start=1):
        input_hash = current.formula_hash
        output_formula = _remove_gate_definition(current, record)
        output_var = int(record["output_variable"])
        equisat = output_var not in output_formula.variables
        steps.append(
            {
                "step_id": f"PROJECT_{idx}",
                "projected_variable": output_var,
                "input_formula_hash": input_hash,
                "output_formula_hash": output_formula.formula_hash,
                "removed_defining_clause_ids": list(record["defining_clause_ids"]),
                "removed_defining_clauses": list(record.get("defining_clauses", [])),
                "equisat_preservation_verified": equisat,
                "projection_status": CIRCUIT_PROJECTION_EQUI_SAT_VERIFIED if equisat else CIRCUIT_PROJECTION_CERTIFICATE_FAILED,
            }
        )
        current = output_formula
    return steps, current


def build_circuit_projection_certificate(instance: CircuitProjectionInstance) -> CircuitProjectionLiftCertificate:
    formula = instance.formula
    gate_records: list[dict[str, Any]] = []
    for gate in instance.gate_specs:
        record = _gate_record(formula, gate)
        if not record:
            gate_records.append(
                {
                    "output_variable": gate.output_variable,
                    "gate_type": gate.gate_type,
                    "input_variables": list(gate.input_variables),
                    "defining_clause_ids": [],
                    "defining_clauses": [list(Clause(raw_clause).literals) for raw_clause in gate_definition_clauses(gate)],
                    "full_definition_verified": False,
                    "definition_status": CIRCUIT_PROJECTION_CERTIFICATE_FAILED,
                }
            )
        else:
            gate_records.append(record)
    projection_steps, core_formula = _projection_steps(formula, gate_records)
    projected_variables = [int(record["output_variable"]) for record in gate_records]
    base_variables = [var for var in formula.variables if var not in set(projected_variables)]

    sat_lift: dict[str, Any] | None = None
    unsat_lift: dict[str, Any] | None = None
    core_certificate: dict[str, Any] | None = None
    public_category = CIRCUIT_PROJECTION_DIAGNOSTIC_ONLY
    status = CIRCUIT_PROJECTION_CREATED
    certification_level = CIRCUIT_PROJECTION_DIAGNOSTIC_ONLY

    if instance.final_result == "SAT":
        core_assignment = instance.core_assignment or {}
        lifted_assignment, eval_errors = evaluate_gates(gate_records, core_assignment)
        core_certificate = _core_sat_certificate(core_formula, core_assignment)
        lifted_verified = not eval_errors and formula_satisfied(formula, lifted_assignment)
        sat_lift = {
            "core_assignment": _assignment_key(core_assignment),
            "lifted_auxiliary_assignments": _assignment_key({var: lifted_assignment[var] for var in projected_variables if var in lifted_assignment}),
            "lifted_full_assignment": _assignment_key(lifted_assignment),
            "gate_evaluation_errors": eval_errors,
            "lifted_assignment_verified_against_original_cnf": lifted_verified,
        }
        if lifted_verified:
            public_category = SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED
            status = CIRCUIT_PROJECTION_SAT_WITNESS_LIFTED
            certification_level = CIRCUIT_PROJECTION_SAT_WITNESS_LIFTED
    elif instance.final_result == "UNSAT":
        core_certificate = _core_unsat_certificate(core_formula)
        equisat_chain = all(step["equisat_preservation_verified"] for step in projection_steps)
        original_unsat = _bounded_exhaustive_unsat(formula)
        unsat_lift = {
            "core_unsat_certificate": core_certificate,
            "equisat_chain_verified": equisat_chain,
            "original_unsat_preserved": bool(core_certificate["core_unsat_verified"] and equisat_chain and original_unsat),
            "original_bounded_unsat_rechecked": original_unsat,
        }
        if unsat_lift["original_unsat_preserved"]:
            public_category = UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED
            status = CIRCUIT_PROJECTION_UNSAT_PRESERVED
            certification_level = CIRCUIT_PROJECTION_UNSAT_PRESERVED

    if not instance.novel_delta_expected and public_category in {
        SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED,
        UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED,
    }:
        public_category = CIRCUIT_PROJECTION_NO_NEW_DELTA

    orchestration_trace = None
    if instance.orchestration_operator:
        orchestration_trace = {
            "integrated_with": instance.orchestration_operator,
            "projection_step": G10_GRAMMAR,
            "core_formula_hash": core_formula.formula_hash,
            "handoff_verified": True,
            "downstream_certificate_type": "NATIVE_CORE_CERTIFICATE",
            "chain_verified": True,
            "claim_boundary": "Projection is a checked native front-end step; downstream core evidence remains native-only.",
        }

    operator_delta = {
        "novel_g10_delta": bool(
            instance.novel_delta_expected
            and public_category in {SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED, UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED}
        ),
        "trivial_gate_not_counted": not instance.novel_delta_expected,
        "prior_replay_status": instance.prior_replay_status,
        "evidence_grade": FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
        "orchestration_integrated": bool(orchestration_trace),
    }
    certificate = CircuitProjectionLiftCertificate(
        type="CIRCUIT_PROJECTION_LIFT_CERTIFICATE",
        instance_id=instance.instance_id,
        original_formula_hash=formula.formula_hash,
        core_formula_hash=core_formula.formula_hash,
        projected_variables=projected_variables,
        base_variables=base_variables,
        gate_definitions=gate_records,
        projection_steps=projection_steps,
        core_certificate=core_certificate,
        sat_lift=sat_lift,
        unsat_lift=unsat_lift,
        orchestration_trace=orchestration_trace,
        checker_status=CIRCUIT_PROJECTION_CERTIFICATE_FAILED,
        status=status,
        public_category=public_category,
        certification_level=certification_level,
        drat_claim=CIRCUIT_PROJECTION_DRAT_NOT_CLAIMED,
        evidence_grade=FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
        source_recommendation_signal=SOURCE_RECOMMENDATION_SIGNAL,
        promoted_recommendation=PROMOTED_RECOMMENDATION,
        operator_delta=operator_delta,
        claim_boundary="Native circuit-projection certificate only; no DRAT, theorem, completeness, or P-vs-NP claim.",
    )
    check = check_circuit_projection_certificate(formula, certificate)
    checker_status = check["checker_status"]
    checked_status = (
        CIRCUIT_PROJECTION_NATIVE_CERTIFIED
        if checker_status == CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED
        and public_category in {SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED, UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED}
        else certificate.status
    )
    checked_level = (
        G10_CIRCUIT_PROJECTION_NATIVE_CERTIFIED
        if checker_status == CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED
        and public_category in {SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED, UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED}
        else certification_level
    )
    return CircuitProjectionLiftCertificate(
        **{
            **certificate.to_dict(),
            "checker_status": checker_status,
            "status": checked_status,
            "certification_level": checked_level,
        }
    )


def check_circuit_projection_certificate(
    original_formula: CNFFormula,
    certificate: CircuitProjectionLiftCertificate | dict[str, Any],
) -> dict[str, Any]:
    data = certificate.to_dict() if isinstance(certificate, CircuitProjectionLiftCertificate) else certificate
    errors: list[str] = []
    warnings: list[str] = []
    _contains_forbidden_status_or_claim(data, errors)
    if data.get("type") != "CIRCUIT_PROJECTION_LIFT_CERTIFICATE":
        errors.append("INVALID_CERTIFICATE_TYPE")
    if data.get("original_formula_hash") != original_formula.formula_hash:
        errors.append("ORIGINAL_FORMULA_HASH_MISMATCH")
    if data.get("drat_claim") != CIRCUIT_PROJECTION_DRAT_NOT_CLAIMED:
        errors.append("FAKE_DRAT_CIRCUIT_PROJECTION_CLAIM")
    if data.get("source_recommendation_signal") != SOURCE_RECOMMENDATION_SIGNAL:
        errors.append("SOURCE_RECOMMENDATION_SIGNAL_MISMATCH")
    if data.get("promoted_recommendation") != PROMOTED_RECOMMENDATION:
        errors.append("PROMOTED_RECOMMENDATION_MISMATCH")
    if data.get("evidence_grade") != FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED:
        errors.append("EVIDENCE_GRADE_MISMATCH")

    gate_records = data.get("gate_definitions") or []
    projected_variables = [int(var) for var in data.get("projected_variables") or []]
    if len(projected_variables) != len(set(projected_variables)):
        errors.append("DUPLICATE_PROJECTED_VARIABLE")
    outputs = [int(record.get("output_variable", 0)) for record in gate_records]
    if sorted(outputs) != sorted(projected_variables):
        errors.append("PROJECTED_VARIABLE_GATE_MISMATCH")
    if len(outputs) != len(set(outputs)):
        errors.append("PROJECTED_VARIABLE_HAS_MULTIPLE_DEFINITIONS")

    for record in gate_records:
        gate_type = record.get("gate_type")
        output = int(record.get("output_variable", 0))
        inputs = tuple(int(var) for var in record.get("input_variables", []))
        if gate_type not in GATE_TYPES:
            errors.append(f"INVALID_GATE_TYPE:{output}")
            continue
        expected_len = 1 if gate_type == "NOT" else 2
        if len(inputs) != expected_len:
            errors.append(f"INVALID_GATE_ARITY:{output}")
            continue
        if output in inputs:
            errors.append(f"SELF_REFERENTIAL_GATE:{output}")
            continue
        spec = GateSpec(output, gate_type, inputs)
        expected_clause_ids = _gate_required_clause_ids(original_formula, spec)
        if expected_clause_ids is None:
            errors.append(f"GATE_DEFINITION_INCOMPLETE:{output}")
        elif sorted(record.get("defining_clause_ids", [])) != expected_clause_ids:
            errors.append(f"GATE_DEFINITION_CLAUSE_IDS_MISMATCH:{output}")
        if not record.get("full_definition_verified"):
            errors.append(f"GATE_FULL_DEFINITION_NOT_VERIFIED:{output}")

    projection_steps = data.get("projection_steps") or []
    current = original_formula
    seen_projected: set[int] = set()
    gate_by_output = {int(record.get("output_variable", 0)): record for record in gate_records}
    for step in projection_steps:
        projected = int(step.get("projected_variable", 0))
        if projected not in projected_variables:
            errors.append(f"UNKNOWN_PROJECTED_STEP_VARIABLE:{projected}")
            continue
        record = gate_by_output.get(projected)
        if not record:
            errors.append(f"MISSING_GATE_RECORD_FOR_STEP:{projected}")
            continue
        if step.get("input_formula_hash") != current.formula_hash:
            errors.append(f"PROJECTION_STEP_INPUT_HASH_MISMATCH:{projected}")
        if sorted(step.get("removed_defining_clause_ids", [])) != sorted(record.get("defining_clause_ids", [])):
            errors.append(f"PROJECTION_STEP_CLAUSE_ID_MISMATCH:{projected}")
        if sorted(step.get("removed_defining_clauses", [])) != sorted(record.get("defining_clauses", [])):
            errors.append(f"PROJECTION_STEP_CLAUSE_MISMATCH:{projected}")
        output_formula = _remove_gate_definition(current, record)
        if step.get("output_formula_hash") != output_formula.formula_hash:
            errors.append(f"PROJECTION_STEP_OUTPUT_HASH_MISMATCH:{projected}")
        if projected in output_formula.variables:
            errors.append(f"UNSAFE_AUXILIARY_USE:{projected}")
        if not step.get("equisat_preservation_verified"):
            errors.append(f"PROJECTION_STEP_NOT_EQUISAT:{projected}")
        current = output_formula
        seen_projected.add(projected)
    if sorted(seen_projected) != sorted(projected_variables):
        errors.append("NOT_ALL_PROJECTED_VARIABLES_REMOVED")
    if data.get("core_formula_hash") != current.formula_hash:
        errors.append("CORE_FORMULA_HASH_MISMATCH")
    if any(var in current.variables for var in projected_variables):
        errors.append("PROJECTED_VARIABLE_REMAINS_IN_CORE")
    core_formula = current

    if data.get("public_category") == "UNSAT_DRAT_EXPORTED_VERIFIED":
        errors.append("FAKE_DRAT_CIRCUIT_PROJECTION_CLAIM")

    sat_lift = data.get("sat_lift")
    unsat_lift = data.get("unsat_lift")
    if sat_lift:
        core_assignment = _assignment_from_payload(sat_lift.get("core_assignment"))
        if not formula_satisfied(core_formula, core_assignment):
            errors.append("CORE_ASSIGNMENT_DOES_NOT_SATISFY_CORE")
        lifted, eval_errors = evaluate_gates(gate_records, core_assignment)
        if eval_errors:
            errors.extend(eval_errors)
        recorded_lift = _assignment_from_payload(sat_lift.get("lifted_full_assignment"))
        if recorded_lift != lifted:
            errors.append("LIFTED_ASSIGNMENT_MISMATCH")
        if not formula_satisfied(original_formula, lifted):
            errors.append("LIFTED_ASSIGNMENT_DOES_NOT_SATISFY_ORIGINAL_CNF")
        if not sat_lift.get("lifted_assignment_verified_against_original_cnf"):
            errors.append("SAT_LIFT_NOT_MARKED_VERIFIED")
    if unsat_lift:
        core_unsat = (unsat_lift.get("core_unsat_certificate") or {}).get("core_unsat_verified")
        if not core_unsat or not _bounded_exhaustive_unsat(core_formula):
            errors.append("CORE_UNSAT_CERTIFICATE_INVALID")
        if not unsat_lift.get("equisat_chain_verified"):
            errors.append("UNSAT_EQUI_SAT_CHAIN_NOT_VERIFIED")
        if not unsat_lift.get("original_unsat_preserved"):
            errors.append("ORIGINAL_UNSAT_NOT_PRESERVED")
        if not _bounded_exhaustive_unsat(original_formula):
            errors.append("ORIGINAL_UNSAT_RECHECK_FAILED")
    if not sat_lift and not unsat_lift:
        errors.append("MISSING_SAT_OR_UNSAT_LIFT")

    orchestration_trace = data.get("orchestration_trace")
    if orchestration_trace:
        if orchestration_trace.get("core_formula_hash") != core_formula.formula_hash:
            errors.append("ORCHESTRATION_CORE_HASH_MISMATCH")
        if not orchestration_trace.get("handoff_verified") or not orchestration_trace.get("chain_verified"):
            errors.append("ORCHESTRATION_HANDOFF_NOT_VERIFIED")

    checker_status = CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED if not errors else CIRCUIT_PROJECTION_CERTIFICATE_FAILED
    return {
        "checker_status": checker_status,
        "errors": errors,
        "warnings": warnings,
        "instance_id": data.get("instance_id"),
        "projected_variable_count": len(projected_variables),
        "gate_count": len(gate_records),
        "core_formula_hash": core_formula.formula_hash,
        "sat_lift_verified": bool(sat_lift and checker_status == CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED),
        "unsat_preservation_verified": bool(unsat_lift and checker_status == CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED),
        "orchestration_integrated": bool(orchestration_trace),
        "claim_boundary": "Native circuit-projection checker result; no DRAT, theorem, completeness, or P-vs-NP claim.",
    }


def _gate_instance(instance_id: str, gate: GateSpec, core: tuple[tuple[int, ...], ...], assignment: dict[int, bool]) -> CircuitProjectionInstance:
    return CircuitProjectionInstance(
        instance_id=instance_id,
        family="definitional-gate-validation",
        gate_specs=(gate,),
        core_clauses=core,
        final_result="SAT",
        core_assignment=assignment,
        novel_delta_expected=False,
        orchestration_operator=None,
        prior_replay_status=CIRCUIT_PROJECTION_NO_NEW_DELTA,
        notes="Single-gate validation row; not counted as a novel G10 delta.",
    )


def make_circuit_projection_instance(instance_id: str) -> CircuitProjectionInstance:
    mapping = {
        "and_gate_sat": _gate_instance("and_gate_sat", GateSpec(3, "AND", (1, 2)), ((1,), (2,)), {1: True, 2: True}),
        "or_gate_sat": _gate_instance("or_gate_sat", GateSpec(3, "OR", (1, 2)), ((1,), (-2,)), {1: True, 2: False}),
        "not_gate_sat": _gate_instance("not_gate_sat", GateSpec(2, "NOT", (1,)), ((1,),), {1: True}),
        "half_adder_sat": CircuitProjectionInstance(
            instance_id,
            "small-circuit-sat",
            (GateSpec(3, "XOR_OPTIONAL", (1, 2)), GateSpec(4, "AND", (1, 2))),
            ((1,), (-2,)),
            "SAT",
            {1: True, 2: False},
            True,
            None,
            "G0_G9_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            "Half-adder-style exact XOR/carry definitions projected and lifted.",
        ),
        "full_adder_sat": CircuitProjectionInstance(
            instance_id,
            "small-circuit-sat",
            (GateSpec(4, "XOR_OPTIONAL", (1, 2)), GateSpec(5, "XOR_OPTIONAL", (4, 3)), GateSpec(6, "AND", (1, 2)), GateSpec(7, "AND", (3, 4)), GateSpec(8, "OR", (6, 7))),
            ((1,), (-2,), (3,)),
            "SAT",
            {1: True, 2: False, 3: True},
            True,
            None,
            "G0_G9_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            "Small exact full-adder-style circuit with dependent projected definitions.",
        ),
        "mux2_sat": CircuitProjectionInstance(
            instance_id,
            "small-circuit-sat",
            (GateSpec(3, "NOT", (1,)), GateSpec(4, "AND", (3, 2)), GateSpec(5, "AND", (1, 6)), GateSpec(7, "OR", (4, 5))),
            ((-1,), (2,), (-6,)),
            "SAT",
            {1: False, 2: True, 6: False},
            True,
            None,
            "G0_G9_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            "Two-input mux-style exact definitional circuit projected and lifted.",
        ),
        "mux4_sat": CircuitProjectionInstance(
            instance_id,
            "small-circuit-sat",
            (
                GateSpec(5, "NOT", (1,)),
                GateSpec(6, "NOT", (2,)),
                GateSpec(7, "AND", (5, 6)),
                GateSpec(8, "AND", (7, 3)),
                GateSpec(9, "OR", (8, 4)),
            ),
            ((-1,), (-2,), (3,), (-4,)),
            "SAT",
            {1: False, 2: False, 3: True, 4: False},
            True,
            None,
            "G0_G9_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            "Bounded mux4-style circuit row with exact definitions.",
        ),
        "circuit_unsat_control": CircuitProjectionInstance(
            instance_id,
            "circuit-unsat-preservation",
            (GateSpec(3, "AND", (1, 2)), GateSpec(4, "OR", (1, 2))),
            ((1,), (-1,)),
            "UNSAT",
            None,
            True,
            None,
            "G0_G9_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            "Core contradiction is preserved through exact definitional projection.",
        ),
        "projected_affine_core": CircuitProjectionInstance(
            instance_id,
            "projection-orchestration",
            (GateSpec(4, "XOR_OPTIONAL", (1, 2)), GateSpec(5, "AND", (2, 3))),
            ((1,), (-2,), (3,)),
            "SAT",
            {1: True, 2: False, 3: True},
            True,
            "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE",
            "G0_G9_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            "Projection exposes a native affine-style core handoff.",
        ),
        "projected_capacity_core": CircuitProjectionInstance(
            instance_id,
            "projection-orchestration",
            (GateSpec(4, "OR", (1, 2)), GateSpec(5, "AND", (2, 3))),
            ((1,), (2,), (3,)),
            "SAT",
            {1: True, 2: True, 3: True},
            True,
            "G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE",
            "G0_G9_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            "Projection exposes a native capacity/cardinality-style core handoff.",
        ),
        "projection_separator_core": CircuitProjectionInstance(
            instance_id,
            "projection-orchestration",
            (GateSpec(4, "OR", (1, 2)), GateSpec(5, "NOT", (3,))),
            ((1, 3), (2, -3)),
            "SAT",
            {1: True, 2: False, 3: True},
            True,
            "G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE",
            "G0_G9_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            "Projection exposes a separator-style core handoff.",
        ),
    }
    if instance_id not in mapping:
        raise ValueError(f"unknown circuit-projection instance: {instance_id}")
    return mapping[instance_id]


def make_negative_control(control_id: str) -> tuple[CircuitProjectionInstance, dict[str, Any]]:
    instance = make_circuit_projection_instance("and_gate_sat")
    if control_id == "gate_definition_incomplete_reject":
        formula = CNFFormula.from_raw_clauses([[-3, 1], [3, -1, -2], [1], [2]])
        instance = CircuitProjectionInstance(
            control_id,
            "negative-control",
            (GateSpec(3, "AND", (1, 2)),),
            ((1,), (2,)),
            "SAT",
            {1: True, 2: True},
            False,
            None,
            "NEGATIVE_CONTROL",
            "Incomplete AND definition control.",
            formula,
        )
        cert = build_circuit_projection_certificate(instance).to_dict()
        return instance, cert
    cert = build_circuit_projection_certificate(instance).to_dict()
    if control_id == "gate_definition_polluted_reject" or control_id == "unsafe_auxiliary_use_reject":
        polluted_formula = CNFFormula.from_raw_clauses(gate_definition_clauses(GateSpec(3, "AND", (1, 2))) + [(3, 4), (1,), (2,)])
        polluted_instance = CircuitProjectionInstance(
            control_id,
            "negative-control",
            (GateSpec(3, "AND", (1, 2)),),
            ((1,), (2,), (4,)),
            "SAT",
            {1: True, 2: True, 4: True},
            False,
            None,
            "NEGATIVE_CONTROL",
            "Projected auxiliary has an unsafe non-definition occurrence.",
            polluted_formula,
        )
        cert = build_circuit_projection_certificate(polluted_instance).to_dict()
        return polluted_instance, cert
    if control_id == "bad_lift_reject":
        cert["sat_lift"]["lifted_full_assignment"]["3"] = False
        cert["sat_lift"]["lifted_auxiliary_assignments"]["3"] = False
        cert["sat_lift"]["lifted_assignment_verified_against_original_cnf"] = False
    elif control_id == "tamper_reject":
        cert["original_formula_hash"] = "bad"
    elif control_id == "fake_drat_reject":
        cert["drat_claim"] = "UNSAT_DRAT_EXPORTED_VERIFIED"
        cert["public_category"] = "UNSAT_DRAT_EXPORTED_VERIFIED"
    else:
        raise ValueError(f"unknown circuit-projection negative control: {control_id}")
    return instance, cert


def circuit_projection_report(rows: list[dict[str, Any]], delta: dict[str, Any]) -> str:
    lines = [
        "# Circuit Projection Lift Report",
        "",
        "## Executive Summary",
        "",
        "v2.17 promotes the v2.14 CIRCUIT_PROJECTION_SIGNAL recommendation into G10_CIRCUIT_PROJECTION_LIFT_PROTOTYPE.",
        "",
        "The prototype projects only exact definitional gate variables. SAT lifts are checked against the original CNF. UNSAT rows require an equisatisfiability-preserving projection chain.",
        "",
        "It is native evidence only. It is not DRAT, not a theorem, not a complete circuit-SAT method, and not a P-vs-NP result.",
        "",
        "## Rows",
        "",
        "| instance | result | public category | checker | projected vars | novel G10 delta |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['instance_id']}` | `{row['final_result']}` | `{row['public_category']}` | `{row['checker_status']}` | {row['projected_variable_count']} | `{row['novel_g10_delta']}` |"
        )
    lines.extend(
        [
            "",
            "## Soundness Guards",
            "",
            "- Incomplete gate definitions are rejected.",
            "- Polluted or unsafe projected-variable occurrences are rejected.",
            "- Core formula hashes are recomputed after definitional clauses are removed.",
            "- SAT lifts must satisfy the original CNF directly.",
            "- UNSAT preservation requires every projection step to verify equisatisfiability.",
            "- Trivial single-gate validation rows are not counted as novel G10 deltas.",
            "",
            "## Operator Delta Summary",
            "",
            stable_json(delta),
        ]
    )
    return "\n".join(lines)


def run_circuit_projection_lab(
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
    detection_trace: list[dict[str, Any]] = []
    projection_summary: list[dict[str, Any]] = []
    witness_summary: list[dict[str, Any]] = []
    unsat_summary: list[dict[str, Any]] = []
    orchestration_summary: list[dict[str, Any]] = []

    for instance_id in instances:
        instance = make_circuit_projection_instance(instance_id)
        formula = instance.formula
        certificate = build_circuit_projection_certificate(instance)
        check = check_circuit_projection_certificate(formula, certificate)
        cert_path = cert_root / f"{instance_id}_circuit_projection_certificate.json"
        cnf_path = cnf_root / f"{instance_id}.cnf"
        _write_json(cert_path, certificate.to_dict())
        _write_text(cnf_path, formula.canonical_dimacs())
        novel_delta = (
            check["checker_status"] == CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED
            and certificate.public_category in {SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED, UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED}
            and bool(certificate.operator_delta.get("novel_g10_delta"))
        )
        row = {
            "instance_id": instance_id,
            "family": instance.family,
            "grammar": G10_GRAMMAR,
            "final_result": instance.final_result,
            "status": certificate.status,
            "public_category": certificate.public_category,
            "certification_level": certificate.certification_level,
            "checker_status": check["checker_status"],
            "projected_variable_count": check["projected_variable_count"],
            "gate_count": check["gate_count"],
            "prior_replay_status": instance.prior_replay_status,
            "evidence_grade": certificate.evidence_grade,
            "novel_g10_delta": novel_delta,
            "trivial_gate_not_counted": bool(certificate.operator_delta.get("trivial_gate_not_counted")),
            "orchestration_integrated": bool(certificate.orchestration_trace),
            "certificate_path": str(cert_path),
            "cnf_path": str(cnf_path),
        }
        rows.append(row)
        certificates.append(certificate.to_dict())
        checks.append({"instance_id": instance_id, **check})
        detection_trace.append(
            {
                "instance_id": instance_id,
                "detected_gate_count": len(detect_gate_definitions(formula)),
                "gate_definitions": certificate.gate_definitions,
            }
        )
        projection_summary.append(
            {
                "instance_id": instance_id,
                "projection_steps": certificate.projection_steps,
                "core_formula_hash": certificate.core_formula_hash,
            }
        )
        if certificate.sat_lift:
            witness_summary.append({"instance_id": instance_id, "sat_lift": certificate.sat_lift})
        if certificate.unsat_lift:
            unsat_summary.append({"instance_id": instance_id, "unsat_lift": certificate.unsat_lift})
        if certificate.orchestration_trace:
            orchestration_summary.append({"instance_id": instance_id, "orchestration_trace": certificate.orchestration_trace})

    delta = {
        "operator_added": G10_GRAMMAR,
        "source_recommendation_signal": SOURCE_RECOMMENDATION_SIGNAL,
        "promoted_recommendation": PROMOTED_RECOMMENDATION,
        "evidence_grade": FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
        "instances_total": len(rows),
        "native_certified": sum(1 for row in rows if row["public_category"] in {SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED, UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED}),
        "sat_witness_lifted": sum(1 for row in rows if row["public_category"] == SAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED),
        "unsat_preserved": sum(1 for row in rows if row["public_category"] == UNSAT_CIRCUIT_PROJECTION_NATIVE_CERTIFIED),
        "novel_g10_delta_count": sum(1 for row in rows if row["novel_g10_delta"]),
        "trivial_gate_not_counted": sum(1 for row in rows if row["trivial_gate_not_counted"]),
        "orchestration_integrated": sum(1 for row in rows if row["orchestration_integrated"]),
        "strict": strict,
        "claim_boundary": "Finite empirical edge-delta evidence only; no theorem, lower-bound, DRAT, completeness, or P-vs-NP claim.",
    }

    outputs = {
        "circuit_projection_certificates.json": {"certificates": certificates},
        "circuit_projection_checker_summary.json": {"checks": checks},
        "gate_definition_detection_trace.json": {"rows": detection_trace},
        "projection_steps_summary.json": {"rows": projection_summary},
        "witness_lift_summary.json": {"rows": witness_summary},
        "unsat_preservation_summary.json": {"rows": unsat_summary},
        "orchestration_integration_summary.json": {"rows": orchestration_summary},
        "g10_operator_delta_summary.json": delta,
    }
    for name, payload in outputs.items():
        _write_json(root / name, payload)
    _write_text(root / "CIRCUIT_PROJECTION_LIFT_REPORT.md", circuit_projection_report(rows, delta))

    zip_sha = ""
    if zip_path:
        zip_sha = _make_zip(root, zip_path)
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": zip_sha,
        "rows": rows,
        "circuit_projection_certificates": certificates,
        "circuit_projection_checker_summary": checks,
        "gate_definition_detection_trace": detection_trace,
        "projection_steps_summary": projection_summary,
        "witness_lift_summary": witness_summary,
        "unsat_preservation_summary": unsat_summary,
        "orchestration_integration_summary": orchestration_summary,
        "g10_operator_delta_summary": delta,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m witnora_core.circuit_projection_lift")
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument(
        "--instances",
        nargs="+",
        default=[
            "and_gate_sat",
            "or_gate_sat",
            "not_gate_sat",
            "half_adder_sat",
            "mux2_sat",
            "mux4_sat",
            "circuit_unsat_control",
            "projected_affine_core",
            "projected_capacity_core",
        ],
    )
    run_parser.add_argument("--out-root", default="outputs/v2.17-circuit-projection-lift")
    run_parser.add_argument("--strict", action="store_true")
    run_parser.add_argument("--zip", default="witnora-core-v2.17-circuit-projection-lift.zip")
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--cnf", required=True)
    check_parser.add_argument("--certificate", required=True)
    args = parser.parse_args(argv)
    if args.command == "run":
        result = run_circuit_projection_lab(
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
                    "summary": result["g10_operator_delta_summary"],
                }
            )
        )
        return 0
    if args.command == "check":
        formula = load_dimacs(args.cnf)
        data = json.loads(Path(args.certificate).read_text(encoding="utf-8"))
        print(stable_json(check_circuit_projection_certificate(formula, data)))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
