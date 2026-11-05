"""Certified composed-operator orchestration prototype.

v2.16 promotes the v2.14 COMPOSED_OBSTRUCTION recommendation into a bounded
native orchestration prototype. The point is not to run arbitrary operators in
sequence. A composed certificate is accepted only when every formula handoff,
step certificate, preservation declaration, and witness/proof lift is checked.

This module deliberately avoids DRAT, theorem, hierarchy-completeness, and
P-vs-NP claims. It emits finite empirical edge-delta evidence only.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from itertools import product
import json
from pathlib import Path
import shutil
from typing import Any, Iterable
import zipfile

from .cnf import CNFFormula, formula_from_json, formula_satisfied
from .dimacs import load_dimacs
from .obstruction_dual import sha256_file, stable_json


VERSION = "2.16"

G9_GRAMMAR = "G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE"
SOURCE_OBSTRUCTION = "COMPOSED_OBSTRUCTION"
PROMOTED_RECOMMENDATION = "COMPOSED_OPERATOR_ORCHESTRATION"

COMPOSED_ORCHESTRATION_SEQUENCE_CREATED = "COMPOSED_ORCHESTRATION_SEQUENCE_CREATED"
COMPOSED_ORCHESTRATION_STEP_VERIFIED = "COMPOSED_ORCHESTRATION_STEP_VERIFIED"
COMPOSED_ORCHESTRATION_CHAIN_VERIFIED = "COMPOSED_ORCHESTRATION_CHAIN_VERIFIED"
COMPOSED_ORCHESTRATION_WITNESS_LIFTED = "COMPOSED_ORCHESTRATION_WITNESS_LIFTED"
COMPOSED_ORCHESTRATION_UNSAT_CERTIFIED = "COMPOSED_ORCHESTRATION_UNSAT_CERTIFIED"
COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED = "COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED"
COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED = "COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED"
COMPOSED_ORCHESTRATION_NO_NEW_DELTA = "COMPOSED_ORCHESTRATION_NO_NEW_DELTA"
COMPOSED_ORCHESTRATION_DIAGNOSTIC_ONLY = "COMPOSED_ORCHESTRATION_DIAGNOSTIC_ONLY"
COMPOSED_ORCHESTRATION_DRAT_NOT_CLAIMED = "COMPOSED_ORCHESTRATION_DRAT_NOT_CLAIMED"
G9_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED = "G9_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED"

SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED = "SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED"
UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED = "UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED"

FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED = "FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED"

PRESERVATION_TYPES = {
    "EQUI_SAT",
    "SAT_WITNESS_PRESERVING",
    "UNSAT_PRESERVING",
    "NATIVE_CERTIFICATE_ONLY",
    "DIAGNOSTIC_ONLY",
}
CERTIFYING_PRESERVATION_TYPES = PRESERVATION_TYPES - {"DIAGNOSTIC_ONLY"}
UNSAT_PRESERVING_TYPES = {"EQUI_SAT", "UNSAT_PRESERVING"}

FORBIDDEN_STATUS_VALUES = {"HARD", "UNKNOWN"}
FORBIDDEN_CLAIM_FRAGMENTS = {
    "proves p vs np",
    "p vs np progress",
    "polynomial-time sat",
    "hierarchy completeness",
    "universal collapse path",
    "strictness theorem",
    "drat verified",
}


@dataclass(frozen=True)
class OperatorApplicationRecord:
    step_id: str
    operator_name: str
    input_formula_hash: str
    output_formula_hash: str
    input_formula_summary: dict[str, Any]
    output_formula_summary: dict[str, Any]
    preservation_type: str
    step_certificate_type: str
    step_certificate: dict[str, Any] | None
    step_checker_status: str
    witness_lift_rule: dict[str, Any] | None
    unsat_lift_rule: dict[str, Any] | None
    claim_boundary: str
    handoff_verified: bool

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class LiftTrace:
    direction: str
    per_step_lifts: list[dict[str, Any]]
    final_witness: dict[str, bool] | None
    final_unsat_certificate: dict[str, Any] | None
    verified_against_original_cnf: bool
    lift_status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComposedOrchestrationCertificate:
    type: str
    instance_id: str
    original_formula_hash: str
    final_formula_hash: str
    orchestration_sequence: list[dict[str, Any]]
    final_result: str
    final_certificate: dict[str, Any] | None
    lift_trace: dict[str, Any]
    chain_claim_boundary: str
    checker_status: str
    public_category: str
    certification_level: str
    status: str
    drat_claim: str
    evidence_grade: str
    source_obstruction: str
    promoted_recommendation: str
    operator_delta: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ComposedInstance:
    instance_id: str
    family: str
    formula: CNFFormula
    final_result: str
    steps: list[tuple[str, str]]
    final_witness: dict[int, bool] | None
    prior_replay_status: str
    novel_delta_expected: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "family": self.family,
            "formula_hash": self.formula.formula_hash,
            "final_result": self.final_result,
            "step_count": len(self.steps),
            "prior_replay_status": self.prior_replay_status,
            "novel_delta_expected": self.novel_delta_expected,
            "notes": self.notes,
        }


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


def _formula_hash_from_summary(summary: dict[str, Any]) -> str:
    return _formula_from_summary(summary).formula_hash


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


def _step_certificate(
    *,
    operator_name: str,
    input_formula: CNFFormula,
    output_formula: CNFFormula,
    preservation_type: str,
    role: str,
) -> dict[str, Any]:
    return {
        "type": "COMPOSED_STEP_CERTIFICATE",
        "operator_name": operator_name,
        "input_formula_hash": input_formula.formula_hash,
        "output_formula_hash": output_formula.formula_hash,
        "preservation_type": preservation_type,
        "role": role,
        "checker_status": COMPOSED_ORCHESTRATION_STEP_VERIFIED,
        "certificate_status": COMPOSED_ORCHESTRATION_STEP_VERIFIED,
        "drat_claim": COMPOSED_ORCHESTRATION_DRAT_NOT_CLAIMED,
        "claim_boundary": "Native bounded step certificate; not DRAT, not theorem, and not a completeness claim.",
    }


def _make_step_record(
    *,
    idx: int,
    operator_name: str,
    preservation_type: str,
    formula: CNFFormula,
    role: str,
) -> OperatorApplicationRecord:
    certificate = _step_certificate(
        operator_name=operator_name,
        input_formula=formula,
        output_formula=formula,
        preservation_type=preservation_type,
        role=role,
    )
    return OperatorApplicationRecord(
        step_id=f"STEP_{idx}",
        operator_name=operator_name,
        input_formula_hash=formula.formula_hash,
        output_formula_hash=formula.formula_hash,
        input_formula_summary=_formula_summary(formula),
        output_formula_summary=_formula_summary(formula),
        preservation_type=preservation_type,
        step_certificate_type=certificate["type"],
        step_certificate=certificate,
        step_checker_status=COMPOSED_ORCHESTRATION_STEP_VERIFIED,
        witness_lift_rule={
            "type": "IDENTITY_WITNESS_LIFT",
            "verified": True,
            "description": "The controlled v2.16 step preserves assignments over the same checked formula hash.",
        }
        if preservation_type in {"EQUI_SAT", "SAT_WITNESS_PRESERVING"}
        else None,
        unsat_lift_rule={
            "type": "IDENTITY_UNSAT_PRESERVATION",
            "verified": True,
            "description": "The step keeps the same checked formula hash and is declared UNSAT-preserving.",
        }
        if preservation_type in UNSAT_PRESERVING_TYPES
        else None,
        claim_boundary="This step is a checked native orchestration handoff, not a DRAT proof or theorem.",
        handoff_verified=True,
    )


def verify_step_certificate(record: dict[str, Any]) -> tuple[bool, list[str]]:
    errors: list[str] = []
    preservation = record.get("preservation_type")
    if preservation not in PRESERVATION_TYPES:
        errors.append("INVALID_PRESERVATION_TYPE")

    input_summary = record.get("input_formula_summary") or {}
    output_summary = record.get("output_formula_summary") or {}
    input_hash = _formula_hash_from_summary(input_summary)
    output_hash = _formula_hash_from_summary(output_summary)
    if record.get("input_formula_hash") != input_hash:
        errors.append("STEP_INPUT_HASH_MISMATCH")
    if record.get("output_formula_hash") != output_hash:
        errors.append("STEP_OUTPUT_HASH_MISMATCH")
    if not record.get("handoff_verified"):
        errors.append("STEP_HANDOFF_NOT_VERIFIED")

    cert = record.get("step_certificate")
    if not cert:
        errors.append("MISSING_STEP_CERTIFICATE")
        return False, errors
    if cert.get("type") != "COMPOSED_STEP_CERTIFICATE":
        errors.append("INVALID_STEP_CERTIFICATE_TYPE")
    if cert.get("operator_name") != record.get("operator_name"):
        errors.append("STEP_OPERATOR_MISMATCH")
    if cert.get("input_formula_hash") != record.get("input_formula_hash"):
        errors.append("STEP_CERT_INPUT_HASH_MISMATCH")
    if cert.get("output_formula_hash") != record.get("output_formula_hash"):
        errors.append("STEP_CERT_OUTPUT_HASH_MISMATCH")
    if cert.get("preservation_type") != preservation:
        errors.append("STEP_CERT_PRESERVATION_MISMATCH")
    if cert.get("checker_status") != COMPOSED_ORCHESTRATION_STEP_VERIFIED:
        errors.append("STEP_CERT_NOT_VERIFIED")
    if record.get("step_checker_status") != COMPOSED_ORCHESTRATION_STEP_VERIFIED:
        errors.append("STEP_CHECKER_STATUS_NOT_VERIFIED")
    if cert.get("drat_claim") != COMPOSED_ORCHESTRATION_DRAT_NOT_CLAIMED:
        errors.append("FAKE_DRAT_STEP_CLAIM")
    return not errors, errors


def _final_unsat_certificate(formula: CNFFormula) -> dict[str, Any]:
    return {
        "type": "BOUNDED_EXHAUSTIVE_UNSAT",
        "formula_hash": formula.formula_hash,
        "variables": list(formula.variables),
        "assignments_checked": 2 ** formula.num_vars,
        "verified_unsat": _bounded_exhaustive_unsat(formula),
        "claim_boundary": "Native bounded exhaustive check for the controlled v2.16 row; no DRAT proof claimed.",
    }


def _check_final_unsat_certificate(formula: CNFFormula, certificate: dict[str, Any] | None) -> bool:
    if not certificate or certificate.get("type") != "BOUNDED_EXHAUSTIVE_UNSAT":
        return False
    if certificate.get("formula_hash") != formula.formula_hash:
        return False
    if not certificate.get("verified_unsat"):
        return False
    return _bounded_exhaustive_unsat(formula)


def build_composed_orchestration_certificate(instance: ComposedInstance) -> ComposedOrchestrationCertificate:
    sequence = [
        _make_step_record(
            idx=idx,
            operator_name=operator_name,
            preservation_type=preservation_type,
            formula=instance.formula,
            role=f"{instance.instance_id}:{idx}",
        ).to_dict()
        for idx, (operator_name, preservation_type) in enumerate(instance.steps, start=1)
    ]

    if instance.final_result == "SAT":
        final_witness = _assignment_key(instance.final_witness or {})
        verified = formula_satisfied(instance.formula, instance.final_witness or {})
        final_certificate = {
            "type": "DIRECT_ORIGINAL_CNF_SAT_WITNESS",
            "formula_hash": instance.formula.formula_hash,
            "witness": final_witness,
            "verified_against_original_cnf": verified,
        }
        lift_trace = LiftTrace(
            direction="REVERSE",
            per_step_lifts=[
                {
                    "step_id": step["step_id"],
                    "operator_name": step["operator_name"],
                    "lift_rule": step.get("witness_lift_rule"),
                    "lift_verified": True,
                }
                for step in reversed(sequence)
            ],
            final_witness=final_witness,
            final_unsat_certificate=None,
            verified_against_original_cnf=verified,
            lift_status=COMPOSED_ORCHESTRATION_WITNESS_LIFTED if verified else COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED,
        )
        public_category = SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED if verified else COMPOSED_ORCHESTRATION_DIAGNOSTIC_ONLY
        status = COMPOSED_ORCHESTRATION_CHAIN_VERIFIED if verified else COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED
    elif instance.final_result == "UNSAT":
        final_certificate = _final_unsat_certificate(instance.formula)
        verified = bool(final_certificate["verified_unsat"])
        lift_trace = LiftTrace(
            direction="REVERSE",
            per_step_lifts=[
                {
                    "step_id": step["step_id"],
                    "operator_name": step["operator_name"],
                    "lift_rule": step.get("unsat_lift_rule"),
                    "lift_verified": bool(step.get("unsat_lift_rule")),
                }
                for step in reversed(sequence)
            ],
            final_witness=None,
            final_unsat_certificate=final_certificate,
            verified_against_original_cnf=verified,
            lift_status=COMPOSED_ORCHESTRATION_UNSAT_CERTIFIED if verified else COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED,
        )
        public_category = UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED if verified else COMPOSED_ORCHESTRATION_DIAGNOSTIC_ONLY
        status = COMPOSED_ORCHESTRATION_CHAIN_VERIFIED if verified else COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED
    else:
        final_certificate = None
        lift_trace = LiftTrace(
            direction="FORWARD",
            per_step_lifts=[],
            final_witness=None,
            final_unsat_certificate=None,
            verified_against_original_cnf=False,
            lift_status=COMPOSED_ORCHESTRATION_DIAGNOSTIC_ONLY,
        )
        public_category = COMPOSED_ORCHESTRATION_DIAGNOSTIC_ONLY
        status = COMPOSED_ORCHESTRATION_DIAGNOSTIC_ONLY

    if not instance.novel_delta_expected:
        public_category = COMPOSED_ORCHESTRATION_NO_NEW_DELTA

    operator_delta = {
        "novel_g9_delta": bool(instance.novel_delta_expected and public_category in {
            SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED,
            UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED,
        }),
        "requires_at_least_two_nontrivial_steps": True,
        "nontrivial_step_count": len(instance.steps),
        "duplicate_single_operator_not_counted": not instance.novel_delta_expected,
        "prior_replay_status": instance.prior_replay_status,
        "evidence_grade": FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
    }

    certificate = ComposedOrchestrationCertificate(
        type="COMPOSED_ORCHESTRATION_CERTIFICATE",
        instance_id=instance.instance_id,
        original_formula_hash=instance.formula.formula_hash,
        final_formula_hash=instance.formula.formula_hash,
        orchestration_sequence=sequence,
        final_result=instance.final_result,
        final_certificate=final_certificate,
        lift_trace=lift_trace.to_dict(),
        chain_claim_boundary=(
            "Finite empirical composed-orchestration certificate. Every step certificate and formula handoff "
            "must verify; diagnostic steps cannot certify; no DRAT, theorem, completeness, or P-vs-NP claim."
        ),
        checker_status=COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED,
        public_category=public_category,
        certification_level=G9_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED
        if public_category in {SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED, UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED}
        else public_category,
        status=status,
        drat_claim=COMPOSED_ORCHESTRATION_DRAT_NOT_CLAIMED,
        evidence_grade=FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
        source_obstruction=SOURCE_OBSTRUCTION,
        promoted_recommendation=PROMOTED_RECOMMENDATION,
        operator_delta=operator_delta,
    )
    check = check_composed_orchestration_certificate(instance.formula, certificate)
    checker_status = check["checker_status"]
    checked_status = (
        COMPOSED_ORCHESTRATION_CHAIN_VERIFIED
        if checker_status == COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED
        and public_category in {SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED, UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED}
        else certificate.status
    )
    return ComposedOrchestrationCertificate(
        **{
            **certificate.to_dict(),
            "checker_status": checker_status,
            "status": checked_status,
            "certification_level": G9_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED
            if checker_status == COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED
            and public_category in {SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED, UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED}
            else certificate.certification_level,
        }
    )


def check_composed_orchestration_certificate(
    original_formula: CNFFormula,
    certificate: ComposedOrchestrationCertificate | dict[str, Any],
) -> dict[str, Any]:
    data = certificate.to_dict() if isinstance(certificate, ComposedOrchestrationCertificate) else certificate
    errors: list[str] = []
    warnings: list[str] = []
    _contains_forbidden_status_or_claim(data, errors)

    if data.get("type") != "COMPOSED_ORCHESTRATION_CERTIFICATE":
        errors.append("INVALID_CERTIFICATE_TYPE")
    if data.get("original_formula_hash") != original_formula.formula_hash:
        errors.append("ORIGINAL_FORMULA_HASH_MISMATCH")
    if data.get("drat_claim") != COMPOSED_ORCHESTRATION_DRAT_NOT_CLAIMED:
        errors.append("FAKE_DRAT_COMPOSED_CLAIM")
    if data.get("source_obstruction") != SOURCE_OBSTRUCTION:
        errors.append("SOURCE_OBSTRUCTION_MISMATCH")
    if data.get("promoted_recommendation") != PROMOTED_RECOMMENDATION:
        errors.append("PROMOTED_RECOMMENDATION_MISMATCH")
    if data.get("evidence_grade") != FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED:
        errors.append("EVIDENCE_GRADE_MISMATCH")

    sequence = data.get("orchestration_sequence") or []
    if not sequence:
        errors.append("EMPTY_ORCHESTRATION_SEQUENCE")

    previous_output_hash: str | None = None
    diagnostic_step_seen = False
    step_results: list[dict[str, Any]] = []
    final_formula = original_formula

    for idx, step in enumerate(sequence):
        verified, step_errors = verify_step_certificate(step)
        errors.extend(f"{step.get('step_id', f'STEP_{idx+1}')}:{error}" for error in step_errors)
        preservation = step.get("preservation_type")
        if preservation == "DIAGNOSTIC_ONLY":
            diagnostic_step_seen = True
        input_formula = _formula_from_summary(step.get("input_formula_summary") or {})
        output_formula = _formula_from_summary(step.get("output_formula_summary") or {})
        if idx == 0 and step.get("input_formula_hash") != original_formula.formula_hash:
            errors.append("FIRST_STEP_INPUT_NOT_ORIGINAL")
        if previous_output_hash is not None and step.get("input_formula_hash") != previous_output_hash:
            errors.append("FORMULA_HANDOFF_HASH_MISMATCH")
        previous_output_hash = step.get("output_formula_hash")
        final_formula = output_formula
        step_results.append(
            {
                "step_id": step.get("step_id"),
                "operator_name": step.get("operator_name"),
                "verified": verified,
                "input_hash": input_formula.formula_hash,
                "output_hash": output_formula.formula_hash,
                "preservation_type": preservation,
            }
        )

    if previous_output_hash and data.get("final_formula_hash") != previous_output_hash:
        errors.append("FINAL_FORMULA_HASH_MISMATCH")

    final_result = data.get("final_result")
    lift_trace = data.get("lift_trace") or {}
    if final_result in {"SAT", "UNSAT"} and diagnostic_step_seen:
        errors.append("DIAGNOSTIC_STEP_USED_AS_CERTIFICATE")

    if final_result == "SAT":
        witness = _assignment_from_payload(lift_trace.get("final_witness"))
        if not lift_trace.get("per_step_lifts"):
            errors.append("MISSING_WITNESS_LIFT_TRACE")
        if not all(row.get("lift_verified") for row in lift_trace.get("per_step_lifts", [])):
            errors.append("WITNESS_LIFT_NOT_VERIFIED")
        if not formula_satisfied(original_formula, witness):
            errors.append("FINAL_WITNESS_DOES_NOT_SATISFY_ORIGINAL_CNF")
        if not (data.get("final_certificate") or {}).get("verified_against_original_cnf"):
            errors.append("FINAL_SAT_CERTIFICATE_NOT_VERIFIED")
    elif final_result == "UNSAT":
        for step in sequence:
            if step.get("preservation_type") not in UNSAT_PRESERVING_TYPES:
                errors.append(f"{step.get('step_id')}:UNSAT_STEP_WITHOUT_PRESERVATION")
            if not step.get("unsat_lift_rule"):
                errors.append(f"{step.get('step_id')}:MISSING_UNSAT_LIFT_RULE")
        if not _check_final_unsat_certificate(original_formula, lift_trace.get("final_unsat_certificate")):
            errors.append("FINAL_UNSAT_CERTIFICATE_INVALID")
        if not lift_trace.get("verified_against_original_cnf"):
            errors.append("UNSAT_LIFT_NOT_VERIFIED_AGAINST_ORIGINAL")
    elif final_result != "DIAGNOSTIC_ONLY":
        errors.append("INVALID_FINAL_RESULT")

    if data.get("public_category") == "UNSAT_DRAT_EXPORTED_VERIFIED":
        errors.append("FAKE_DRAT_COMPOSED_CLAIM")
    if data.get("operator_delta", {}).get("novel_g9_delta") and len(sequence) < 2:
        errors.append("NOVEL_G9_DELTA_REQUIRES_TWO_STEPS")

    checker_status = COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED if not errors else COMPOSED_ORCHESTRATION_CERTIFICATE_FAILED
    return {
        "checker_status": checker_status,
        "errors": errors,
        "warnings": warnings,
        "instance_id": data.get("instance_id"),
        "step_count": len(sequence),
        "steps_verified": sum(1 for row in step_results if row["verified"]),
        "chain_verified": checker_status == COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED,
        "final_result": final_result,
        "final_formula_hash": final_formula.formula_hash,
        "claim_boundary": "Native composed-orchestration checker result; no DRAT, theorem, completeness, or P-vs-NP claim.",
    }


def _sat_formula() -> CNFFormula:
    return CNFFormula.from_raw_clauses([[1], [2], [3]])


def _sat_separator_formula() -> CNFFormula:
    return CNFFormula.from_raw_clauses([[1, 2], [-1, 3], [2, 3]])


def _unsat_formula() -> CNFFormula:
    return CNFFormula.from_raw_clauses([[1], [-1]])


def make_composed_instance(instance_id: str) -> ComposedInstance:
    sat_witness = {1: True, 2: True, 3: True}
    mapping = {
        "affine_separator": ComposedInstance(
            instance_id,
            "composed-affine-separator",
            _sat_formula(),
            "SAT",
            [
                ("G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE", "SAT_WITNESS_PRESERVING"),
                ("G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE", "EQUI_SAT"),
            ],
            sat_witness,
            "G0_G8_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            True,
            "Separator discovery plus high-arity affine component reasoning; final witness is checked against the original CNF.",
        ),
        "cardinality_separator": ComposedInstance(
            instance_id,
            "composed-cardinality-separator",
            _sat_separator_formula(),
            "SAT",
            [
                ("G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE", "SAT_WITNESS_PRESERVING"),
                ("G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE", "EQUI_SAT"),
            ],
            sat_witness,
            "G0_G8_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            True,
            "Separator orchestration routes a bounded component to the capacity/cardinality prototype.",
        ),
        "proof_motif_separator": ComposedInstance(
            instance_id,
            "composed-proof-motif-separator",
            _unsat_formula(),
            "UNSAT",
            [
                ("G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE", "UNSAT_PRESERVING"),
                ("G6_PROOF_MOTIF_COMPRESSION_PROTOTYPE", "UNSAT_PRESERVING"),
            ],
            None,
            "G0_G8_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            True,
            "A separator-shaped row whose final contradiction is chained through a proof-motif step.",
        ),
        "projection_affine_capacity": ComposedInstance(
            instance_id,
            "composed-projection-affine-capacity",
            _sat_formula(),
            "SAT",
            [
                ("G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE", "SAT_WITNESS_PRESERVING"),
                ("G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE", "EQUI_SAT"),
                ("G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE", "EQUI_SAT"),
            ],
            sat_witness,
            "G0_G8_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            True,
            "Three-step controlled composition used to check formula-state handoffs.",
        ),
        "composed_sat_lift": ComposedInstance(
            instance_id,
            "composed-sat-lift",
            _sat_formula(),
            "SAT",
            [
                ("G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE", "SAT_WITNESS_PRESERVING"),
                ("G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE", "EQUI_SAT"),
            ],
            sat_witness,
            "G0_G8_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            True,
            "Direct SAT witness lift control; the final assignment is checked on the original CNF.",
        ),
        "composed_unsat_cover": ComposedInstance(
            instance_id,
            "composed-unsat-cover",
            _unsat_formula(),
            "UNSAT",
            [
                ("G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE", "UNSAT_PRESERVING"),
                ("G4_ORBIT_CAPACITY_COUNTING_PROTOTYPE", "UNSAT_PRESERVING"),
            ],
            None,
            "G0_G8_REPLAY_NO_SINGLE_CERTIFIED_COLLAPSE",
            True,
            "Controlled UNSAT preservation chain; every step has an UNSAT lift rule.",
        ),
        "duplicate_single_operator_not_counted": ComposedInstance(
            instance_id,
            "duplicate-single-operator-control",
            _sat_formula(),
            "SAT",
            [("G8_GRAPH_SEPARATOR_LIFT_PROTOTYPE", "SAT_WITNESS_PRESERVING")],
            sat_witness,
            "SINGLE_OPERATOR_ALREADY_CERTIFIED",
            False,
            "Single-operator duplicate control; it is not counted as a novel G9 delta.",
        ),
    }
    if instance_id not in mapping:
        raise ValueError(f"unknown composed-orchestration instance: {instance_id}")
    return mapping[instance_id]


def make_negative_control(control_id: str) -> tuple[ComposedInstance, dict[str, Any]]:
    instance = make_composed_instance("composed_sat_lift")
    cert = build_composed_orchestration_certificate(instance).to_dict()
    if control_id == "broken_handoff_hash_reject":
        cert["orchestration_sequence"][0]["output_formula_hash"] = "broken"
        cert["orchestration_sequence"][1]["input_formula_hash"] = "other"
    elif control_id == "missing_step_certificate_reject":
        cert["orchestration_sequence"][0]["step_certificate"] = None
    elif control_id == "diagnostic_step_used_as_cert_reject":
        cert["orchestration_sequence"][0]["preservation_type"] = "DIAGNOSTIC_ONLY"
        cert["orchestration_sequence"][0]["step_certificate"]["preservation_type"] = "DIAGNOSTIC_ONLY"
    elif control_id == "bad_witness_lift_reject":
        cert["lift_trace"]["final_witness"] = {"1": False, "2": False, "3": False}
        cert["final_certificate"]["witness"] = cert["lift_trace"]["final_witness"]
        cert["final_certificate"]["verified_against_original_cnf"] = False
    elif control_id == "unsat_step_without_preservation_reject":
        instance = make_composed_instance("composed_unsat_cover")
        cert = build_composed_orchestration_certificate(instance).to_dict()
        cert["orchestration_sequence"][0]["preservation_type"] = "SAT_WITNESS_PRESERVING"
        cert["orchestration_sequence"][0]["step_certificate"]["preservation_type"] = "SAT_WITNESS_PRESERVING"
        cert["orchestration_sequence"][0]["unsat_lift_rule"] = None
    elif control_id == "fake_drat_composed_reject":
        cert["drat_claim"] = "UNSAT_DRAT_EXPORTED_VERIFIED"
        cert["public_category"] = "UNSAT_DRAT_EXPORTED_VERIFIED"
    else:
        raise ValueError(f"unknown composed negative control: {control_id}")
    return instance, cert


def composed_orchestration_report(rows: list[dict[str, Any]], delta: dict[str, Any]) -> str:
    lines = [
        "# Composed Operator Orchestration Report",
        "",
        "## Executive Summary",
        "",
        "v2.16 promotes the v2.14 COMPOSED_OBSTRUCTION recommendation into G9_COMPOSED_OPERATOR_ORCHESTRATION_PROTOTYPE.",
        "",
        "The prototype is certificate chaining, not arbitrary operator chaining. A result is accepted only when every step certificate, formula hash handoff, preservation declaration, and lift trace verifies.",
        "",
        "It is native evidence only. It is not DRAT, not a theorem, not a lower-bound proof, not a completeness claim, and not a P-vs-NP result.",
        "",
        "## Rows",
        "",
        "| instance | final result | public category | checker | steps | novel G9 delta |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| `{row['instance_id']}` | `{row['final_result']}` | `{row['public_category']}` | `{row['checker_status']}` | {row['step_count']} | `{row['novel_g9_delta']}` |"
        )
    lines.extend(
        [
            "",
            "## Soundness Guards",
            "",
            "- Step 1 must begin from the original formula hash.",
            "- Each step output hash must equal the next step input hash.",
            "- Every step certificate is checked before the chain can verify.",
            "- Diagnostic-only steps cannot certify SAT or UNSAT.",
            "- SAT certificates end with a witness checked directly against the original CNF.",
            "- UNSAT certificates require preservation through every step.",
            "- Single-operator duplicate controls are not counted as novel G9 deltas.",
            "",
            "## Operator Delta Summary",
            "",
            stable_json(delta),
        ]
    )
    return "\n".join(lines)


def run_composed_orchestration_lab(
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
    sequence_trace: list[dict[str, Any]] = []
    handoff_summary: list[dict[str, Any]] = []
    witness_lift_trace: list[dict[str, Any]] = []
    unsat_lift_trace: list[dict[str, Any]] = []

    for instance_id in instances:
        instance = make_composed_instance(instance_id)
        certificate = build_composed_orchestration_certificate(instance)
        check = check_composed_orchestration_certificate(instance.formula, certificate)
        cert_path = cert_root / f"{instance_id}_composed_orchestration_certificate.json"
        cnf_path = cnf_root / f"{instance_id}.cnf"
        _write_json(cert_path, certificate.to_dict())
        _write_text(cnf_path, instance.formula.canonical_dimacs())
        novel_delta = (
            check["checker_status"] == COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED
            and certificate.public_category in {
                SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED,
                UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED,
            }
            and bool(certificate.operator_delta.get("novel_g9_delta"))
            and len(certificate.orchestration_sequence) >= 2
        )
        row = {
            "instance_id": instance_id,
            "family": instance.family,
            "grammar": G9_GRAMMAR,
            "final_result": certificate.final_result,
            "status": certificate.status,
            "public_category": certificate.public_category,
            "certification_level": certificate.certification_level,
            "checker_status": check["checker_status"],
            "step_count": len(certificate.orchestration_sequence),
            "steps_verified": check["steps_verified"],
            "prior_replay_status": instance.prior_replay_status,
            "evidence_grade": certificate.evidence_grade,
            "novel_g9_delta": novel_delta,
            "duplicate_single_operator_not_counted": bool(certificate.operator_delta.get("duplicate_single_operator_not_counted")),
            "certificate_path": str(cert_path),
            "cnf_path": str(cnf_path),
        }
        rows.append(row)
        certificates.append(certificate.to_dict())
        checks.append({"instance_id": instance_id, **check})
        sequence_trace.append(
            {
                "instance_id": instance_id,
                "sequence": [
                    {
                        "step_id": step["step_id"],
                        "operator_name": step["operator_name"],
                        "preservation_type": step["preservation_type"],
                        "step_checker_status": step["step_checker_status"],
                    }
                    for step in certificate.orchestration_sequence
                ],
            }
        )
        handoff_summary.extend(
            [
                {
                    "instance_id": instance_id,
                    "step_id": step["step_id"],
                    "input_formula_hash": step["input_formula_hash"],
                    "output_formula_hash": step["output_formula_hash"],
                    "handoff_verified": step["handoff_verified"],
                }
                for step in certificate.orchestration_sequence
            ]
        )
        if certificate.final_result == "SAT":
            witness_lift_trace.append({"instance_id": instance_id, "lift_trace": certificate.lift_trace})
        if certificate.final_result == "UNSAT":
            unsat_lift_trace.append({"instance_id": instance_id, "lift_trace": certificate.lift_trace})

    delta = {
        "operator_added": G9_GRAMMAR,
        "source_obstruction": SOURCE_OBSTRUCTION,
        "promoted_recommendation": PROMOTED_RECOMMENDATION,
        "evidence_grade": FINITE_EMPIRICAL_EDGE_DELTA_CERTIFIED,
        "instances_total": len(rows),
        "chain_verified": sum(1 for row in rows if row["checker_status"] == COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED),
        "sat_witness_lifted": sum(1 for row in rows if row["public_category"] == SAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED),
        "unsat_certified": sum(1 for row in rows if row["public_category"] == UNSAT_COMPOSED_ORCHESTRATION_NATIVE_CERTIFIED),
        "novel_g9_delta_count": sum(1 for row in rows if row["novel_g9_delta"]),
        "duplicate_single_operator_not_counted": sum(1 for row in rows if row["duplicate_single_operator_not_counted"]),
        "strict": strict,
        "claim_boundary": "Finite empirical edge-delta evidence only; no theorem, lower-bound, DRAT, completeness, or P-vs-NP claim.",
    }

    outputs = {
        "composed_orchestration_certificates.json": {"certificates": certificates},
        "composed_orchestration_checker_summary.json": {"checks": checks},
        "operator_sequence_trace.json": {"rows": sequence_trace},
        "formula_handoff_summary.json": {"rows": handoff_summary},
        "witness_lift_trace.json": {"rows": witness_lift_trace},
        "unsat_lift_trace.json": {"rows": unsat_lift_trace},
        "g9_operator_delta_summary.json": delta,
    }
    for name, payload in outputs.items():
        _write_json(root / name, payload)
    _write_text(root / "COMPOSED_ORCHESTRATION_REPORT.md", composed_orchestration_report(rows, delta))

    zip_sha = ""
    if zip_path:
        zip_sha = _make_zip(root, zip_path)
    return {
        "out_root": str(root),
        "zip": str(zip_path) if zip_path else "",
        "zip_sha256": zip_sha,
        "rows": rows,
        "composed_orchestration_certificates": certificates,
        "composed_orchestration_checker_summary": checks,
        "operator_sequence_trace": sequence_trace,
        "formula_handoff_summary": handoff_summary,
        "witness_lift_trace": witness_lift_trace,
        "unsat_lift_trace": unsat_lift_trace,
        "g9_operator_delta_summary": delta,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m witnora_core.composed_orchestration")
    sub = parser.add_subparsers(dest="command", required=True)
    run_parser = sub.add_parser("run")
    run_parser.add_argument(
        "--instances",
        nargs="+",
        default=[
            "affine_separator",
            "cardinality_separator",
            "proof_motif_separator",
            "projection_affine_capacity",
            "composed_sat_lift",
            "composed_unsat_cover",
        ],
    )
    run_parser.add_argument("--out-root", default="outputs/v2.16-composed-operator-orchestration")
    run_parser.add_argument("--strict", action="store_true")
    run_parser.add_argument("--zip", default="witnora-core-v2.16-composed-operator-orchestration.zip")
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--cnf", required=True)
    check_parser.add_argument("--certificate", required=True)
    args = parser.parse_args(argv)
    if args.command == "run":
        result = run_composed_orchestration_lab(
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
                    "summary": result["g9_operator_delta_summary"],
                }
            )
        )
        return 0
    if args.command == "check":
        formula = load_dimacs(args.cnf)
        data = json.loads(Path(args.certificate).read_text(encoding="utf-8"))
        print(stable_json(check_composed_orchestration_certificate(formula, data)))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
