"""Planner-guided execution certificates.

v2.20 closes the v2.19 planning loop on finite controlled fixtures. A verified
plan is still not execution. This module accepts only a separate execution
certificate whose operator step certificates, formula handoffs, and result
obligations verify.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any, Iterable
import zipfile

from .circuit_projection_lift import (
    CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED,
    CircuitProjectionInstance,
    GateSpec,
    build_circuit_projection_certificate,
    check_circuit_projection_certificate,
    make_circuit_projection_instance,
)
from .cnf import CNFFormula, formula_from_json, formula_satisfied
from .collapse_planner import (
    CIRCUIT_PROJECTION_SIGNAL,
    COLLAPSE_PLANNER_PLAN_VERIFIED,
    COMPOSED_OBSTRUCTION,
    EXECUTION_REQUIRED,
    GRAPH_SEPARATOR_OBSTRUCTION,
    PROOF_MOTIF_NEAR_MISS,
    PlannerInstance,
    build_collapse_plan_certificate,
    check_collapse_plan_certificate,
    operator_portfolio,
)
from .composed_orchestration import (
    COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED,
    build_composed_orchestration_certificate,
    check_composed_orchestration_certificate,
    make_composed_instance,
)
from .dimacs import load_dimacs
from .graph_separator_lift import (
    GRAPH_SEPARATOR_CERTIFICATE_VERIFIED,
    build_graph_separator_certificate,
    check_graph_separator_certificate,
    make_graph_separator_instance,
)
from .obstruction_dual import sha256_file, stable_json
from .operator_genesis import (
    AFFINE_RESIDUE_CERTIFICATE_VERIFIED,
    AffineResidueInstance,
    build_affine_residue_certificate,
    check_affine_residue_certificate,
    make_affine_residue_instance,
)
from .proof_motif_generalization import (
    PROOF_MOTIF_GENERALIZATION_VERIFIED,
    build_proof_motif_generalization_certificate,
    check_proof_motif_generalization_certificate,
    make_proof_motif_generalization_instance,
)


VERSION = "2.20"

G13_GRAMMAR = "G13_PLANNER_GUIDED_EXECUTION_PROTOTYPE"

PLANNER_EXECUTION_PLAN_LOADED = "PLANNER_EXECUTION_PLAN_LOADED"
PLANNER_EXECUTION_PLAN_VERIFIED = "PLANNER_EXECUTION_PLAN_VERIFIED"
PLANNER_EXECUTION_STARTED = "PLANNER_EXECUTION_STARTED"
PLANNER_EXECUTION_STEP_VERIFIED = "PLANNER_EXECUTION_STEP_VERIFIED"
PLANNER_EXECUTION_HANDOFF_VERIFIED = "PLANNER_EXECUTION_HANDOFF_VERIFIED"
PLANNER_EXECUTION_CHAIN_VERIFIED = "PLANNER_EXECUTION_CHAIN_VERIFIED"
PLANNER_EXECUTION_MATCH_VERIFIED = "PLANNER_EXECUTION_MATCH_VERIFIED"
PLANNER_EXECUTION_MISMATCH_VERIFIED = "PLANNER_EXECUTION_MISMATCH_VERIFIED"
PLANNER_EXECUTION_RESULT_CERTIFIED = "PLANNER_EXECUTION_RESULT_CERTIFIED"
PLANNER_EXECUTION_DIAGNOSTIC_ONLY = "PLANNER_EXECUTION_DIAGNOSTIC_ONLY"
PLANNER_EXECUTION_FAILED = "PLANNER_EXECUTION_FAILED"
PLANNER_EXECUTION_NO_FAKE_CLAIM = "PLANNER_EXECUTION_NO_FAKE_CLAIM"
G13_PLANNER_GUIDED_EXECUTION_NATIVE_CERTIFIED = "G13_PLANNER_GUIDED_EXECUTION_NATIVE_CERTIFIED"

PLANNER_EXECUTION_CERTIFICATE_VERIFIED = "PLANNER_EXECUTION_CERTIFICATE_VERIFIED"
PLANNER_EXECUTION_CERTIFICATE_FAILED = "PLANNER_EXECUTION_CERTIFICATE_FAILED"

FINITE_PLANNER_EXECUTION_VERIFIED = "FINITE_PLANNER_EXECUTION_VERIFIED"

MATCH = "MATCH"
PARTIAL_MATCH = "PARTIAL_MATCH"
MISMATCH = "MISMATCH"
EXECUTION_FAILED = "EXECUTION_FAILED"

SAT_CERTIFIED = "SAT_CERTIFIED"
UNSAT_CERTIFIED = "UNSAT_CERTIFIED"
DIAGNOSTIC_ONLY = "DIAGNOSTIC_ONLY"

EQUI_SAT = "EQUI_SAT"
SAT_WITNESS_PRESERVING = "SAT_WITNESS_PRESERVING"
UNSAT_PRESERVING = "UNSAT_PRESERVING"
NATIVE_CERTIFICATE_ONLY = "NATIVE_CERTIFICATE_ONLY"
DIAGNOSTIC_STEP = "DIAGNOSTIC_ONLY"
UNSAT_PRESERVING_TYPES = {EQUI_SAT, UNSAT_PRESERVING, NATIVE_CERTIFICATE_ONLY}

FORBIDDEN_STATUS_VALUES = {"HARD", "UNKNOWN"}
FORBIDDEN_CLAIM_FRAGMENTS = {
    "p vs np progress",
    "polynomial-time sat",
    "all plans succeed",
    "planner completeness",
    "theorem proven",
    "hierarchy completeness",
    "strictness theorem",
    "lower bound against g0",
    "drat verified",
}


@dataclass(frozen=True)
class PlannerExecutionInstance:
    instance_id: str
    formula: CNFFormula
    plan_instance: PlannerInstance
    expected_result_type: str
    control_kind: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "instance_id": self.instance_id,
            "formula_hash": self.formula.formula_hash,
            "plan_obstruction": self.plan_instance.obstruction_fingerprint,
            "expected_result_type": self.expected_result_type,
            "control_kind": self.control_kind,
        }


@dataclass(frozen=True)
class PlannerExecutionCertificate:
    type: str
    instance_id: str
    original_formula_hash: str
    plan_certificate_hash: str
    plan_certificate_summary: dict[str, Any]
    planned_chain: list[dict[str, Any]]
    actual_execution_chain: list[dict[str, Any]]
    comparison: dict[str, Any]
    execution_result: dict[str, Any]
    handoff_trace: dict[str, Any]
    witness_or_unsat_trace: dict[str, Any]
    evidence_grade: str
    drat_claim: str
    status: str
    claim_boundary: str
    checker_status: str
    public_category: str

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


def _payload_hash(data: Any) -> str:
    return hashlib.sha256(stable_json(data).encode("utf-8")).hexdigest()


def _formula_summary(formula: CNFFormula) -> dict[str, Any]:
    return {
        "formula_hash": formula.formula_hash,
        "num_vars": formula.num_vars,
        "num_clauses": formula.num_clauses,
        "clauses": formula.to_clause_lists(),
    }


def _formula_from_summary(summary: dict[str, Any]) -> CNFFormula:
    return formula_from_json(summary.get("clauses", []))


def _assignment_key(assignment: dict[int, bool] | None) -> dict[str, bool]:
    return {str(var): bool(assignment[var]) for var in sorted(assignment or {})}


def _assignment_from_payload(payload: dict[str, Any] | None) -> dict[int, bool]:
    return {int(var): bool(value) for var, value in (payload or {}).items()}


def _portfolio_by_name() -> dict[str, dict[str, Any]]:
    return {item.operator_name: item.to_dict() for item in operator_portfolio()}


def _step_status_from_check(operator_name: str, check: dict[str, Any]) -> bool:
    if operator_name == "CIRCUIT_PROJECTION_LIFT":
        return check.get("checker_status") == CIRCUIT_PROJECTION_CERTIFICATE_VERIFIED
    if operator_name == "HIGH_ARITY_AFFINE_RESIDUE":
        return check.get("status") == AFFINE_RESIDUE_CERTIFICATE_VERIFIED
    if operator_name == "PROOF_MOTIF_GENERALIZATION_CHECKER":
        return check.get("status") == PROOF_MOTIF_GENERALIZATION_VERIFIED
    if operator_name == "GRAPH_SEPARATOR_LIFT":
        return check.get("checker_status") == GRAPH_SEPARATOR_CERTIFICATE_VERIFIED
    if operator_name == "COMPOSED_OPERATOR_ORCHESTRATION":
        return check.get("checker_status") == COMPOSED_ORCHESTRATION_CERTIFICATE_VERIFIED
    return False


def _dispatch_step_certificate_check(operator_name: str, formula: CNFFormula, certificate: dict[str, Any]) -> dict[str, Any]:
    if operator_name == "CIRCUIT_PROJECTION_LIFT":
        return check_circuit_projection_certificate(formula, certificate)
    if operator_name == "HIGH_ARITY_AFFINE_RESIDUE":
        return check_affine_residue_certificate(formula, certificate)
    if operator_name == "PROOF_MOTIF_GENERALIZATION_CHECKER":
        return check_proof_motif_generalization_certificate(formula, certificate)
    if operator_name == "GRAPH_SEPARATOR_LIFT":
        return check_graph_separator_certificate(formula, certificate)
    if operator_name == "COMPOSED_OPERATOR_ORCHESTRATION":
        return check_composed_orchestration_certificate(formula, certificate)
    return {"checker_status": PLANNER_EXECUTION_CERTIFICATE_FAILED, "status": PLANNER_EXECUTION_CERTIFICATE_FAILED, "errors": ["UNKNOWN_OPERATOR_CHECKER"]}


def _custom_projection_affine_pair() -> tuple[CircuitProjectionInstance, AffineResidueInstance]:
    affine = make_affine_residue_instance("parity_arity_7_sat")
    core_assignment = {var: False for var in affine.formula.variables}
    core_assignment[1] = True
    projection = CircuitProjectionInstance(
        "projected_affine_plan_execution",
        "planner-guided-projected-affine",
        (GateSpec(8, "AND", (6, 7)),),
        tuple(tuple(clause) for clause in affine.formula.to_clause_lists()),
        "SAT",
        core_assignment,
        True,
        "G5_HIGH_ARITY_AFFINE_RESIDUE_PROTOTYPE",
        "G0_G12_REPLAY_NO_CERTIFIED_EXECUTION",
        "G13 projection handoff exposes an exact affine residue core.",
    )
    affine_core = AffineResidueInstance(
        "projected_affine_plan_execution_core",
        affine.equations,
        affine.formula,
        family="planner-guided-affine-core",
        expected_outcome="SAT",
        g1_result="AFFINE_OVER_G1_CAP",
        description="G5 core reached through a verified G10 projection handoff.",
    )
    return projection, affine_core


def _plan_for_formula(
    *,
    instance_id: str,
    formula: CNFFormula,
    fingerprint: str,
    features: dict[str, Any],
    family: str,
    description: str,
) -> PlannerInstance:
    return PlannerInstance(
        instance_id=instance_id,
        obstruction_fingerprint=fingerprint,
        structural_features=features,
        formula=formula,
        family=family,
        description=description,
    )


def make_planner_execution_instance(instance_id: str) -> PlannerExecutionInstance:
    if instance_id == "projected_affine_plan_execution":
        projection, _affine = _custom_projection_affine_pair()
        plan = _plan_for_formula(
            instance_id=instance_id,
            formula=projection.formula,
            fingerprint=CIRCUIT_PROJECTION_SIGNAL,
            features={"projected_core_signal": "affine", "execution_target": "G10_THEN_G5"},
            family="planner-guided-projection-affine",
            description="G12 plans G10 projection followed by G5 affine residue.",
        )
        return PlannerExecutionInstance(instance_id, projection.formula, plan, SAT_CERTIFIED)
    if instance_id == "circuit_plan_execution":
        projection = make_circuit_projection_instance("mux2_sat")
        plan = _plan_for_formula(
            instance_id=instance_id,
            formula=projection.formula,
            fingerprint=CIRCUIT_PROJECTION_SIGNAL,
            features={"projected_core_signal": "capacity", "execution_target": "G10_PREFIX"},
            family="planner-guided-circuit",
            description="G12 plans projection before downstream core reasoning; G13 verifies a conservative prefix execution.",
        )
        return PlannerExecutionInstance(instance_id, projection.formula, plan, SAT_CERTIFIED)
    if instance_id == "proof_motif_plan_execution":
        motif = make_proof_motif_generalization_instance("ladder_near_4")
        plan = _plan_for_formula(
            instance_id=instance_id,
            formula=motif.formula,
            fingerprint=PROOF_MOTIF_NEAR_MISS,
            features={"near_motif_sites": 4, "execution_target": "G11"},
            family="planner-guided-proof-motif",
            description="G12 plans G11 proof motif generalization.",
        )
        return PlannerExecutionInstance(instance_id, motif.formula, plan, UNSAT_CERTIFIED)
    if instance_id == "graph_separator_plan_execution":
        separator = make_graph_separator_instance("separator_sat_pair")
        plan = _plan_for_formula(
            instance_id=instance_id,
            formula=separator.formula,
            fingerprint=GRAPH_SEPARATOR_OBSTRUCTION,
            features={"separator_signal": "small", "execution_target": "G8_PREFIX"},
            family="planner-guided-separator",
            description="G12 plans separator lift and possible component subplans.",
        )
        return PlannerExecutionInstance(instance_id, separator.formula, plan, SAT_CERTIFIED)
    if instance_id == "composed_plan_execution":
        composed = make_composed_instance("composed_sat_lift")
        plan = _plan_for_formula(
            instance_id=instance_id,
            formula=composed.formula,
            fingerprint=COMPOSED_OBSTRUCTION,
            features={"subsignals": ["projection", "affine", "separator", "near_motif"], "execution_target": "G9"},
            family="planner-guided-composed",
            description="G12 proposes a composed path; G13 verifies a certified G9 execution wrapper.",
        )
        return PlannerExecutionInstance(instance_id, composed.formula, plan, SAT_CERTIFIED)
    if instance_id == "mismatch_control":
        projection = make_circuit_projection_instance("mux2_sat")
        plan = _plan_for_formula(
            instance_id=instance_id,
            formula=projection.formula,
            fingerprint=PROOF_MOTIF_NEAR_MISS,
            features={"near_motif_sites": 4, "execution_target": "G11"},
            family="planner-guided-mismatch-control",
            description="Valid plan but actual execution records a different checked operator sequence.",
        )
        return PlannerExecutionInstance(instance_id, projection.formula, plan, DIAGNOSTIC_ONLY, control_kind="MISMATCH")
    if instance_id == "failed_execution_control":
        projection, _affine = _custom_projection_affine_pair()
        plan = _plan_for_formula(
            instance_id=instance_id,
            formula=projection.formula,
            fingerprint=CIRCUIT_PROJECTION_SIGNAL,
            features={"projected_core_signal": "affine", "execution_target": "G10_THEN_G5"},
            family="planner-guided-failed-control",
            description="Valid plan but actual step certificate is corrupted.",
        )
        return PlannerExecutionInstance(instance_id, projection.formula, plan, EXECUTION_FAILED, control_kind="FAILED")
    controls = {
        "fake_execution_record_reject": "FAKE_EXECUTION",
        "fake_sat_unsat_result_reject": "FAKE_SAT_UNSAT",
        "fake_drat_execution_reject": "FAKE_DRAT",
        "unchecked_step_certificate_reject": "UNCHECKED_STEP",
        "bad_handoff_reject": "BAD_HANDOFF",
        "missing_actual_certificate_reject": "MISSING_CERT",
        "diagnostic_step_as_result_reject": "DIAGNOSTIC_AS_RESULT",
        "bad_witness_original_cnf_reject": "BAD_WITNESS",
        "unsat_without_preservation_reject": "UNSAT_NO_PRESERVATION",
        "plan_hash_tamper_reject": "PLAN_TAMPER",
        "unknown_operator_execution_reject": "UNKNOWN_OPERATOR",
        "hard_unknown_status_reject": "HARD_UNKNOWN",
    }
    if instance_id in controls:
        base = make_planner_execution_instance("projected_affine_plan_execution")
        return PlannerExecutionInstance(instance_id, base.formula, base.plan_instance, base.expected_result_type, controls[instance_id])
    raise ValueError(f"unknown planner-execution instance: {instance_id}")


def _actual_step(
    *,
    step_id: str,
    operator_name: str,
    input_formula: CNFFormula,
    output_formula: CNFFormula,
    certificate: dict[str, Any],
    preservation_type: str,
    sat_lift_status: str | None = None,
    unsat_preservation_status: str | None = None,
    force_checker_status: str | None = None,
) -> dict[str, Any]:
    portfolio = _portfolio_by_name()[operator_name]
    check = _dispatch_step_certificate_check(operator_name, input_formula, certificate)
    verified = _step_status_from_check(operator_name, check)
    checker_status = force_checker_status or (PLANNER_EXECUTION_STEP_VERIFIED if verified else PLANNER_EXECUTION_CERTIFICATE_FAILED)
    return {
        "step_id": step_id,
        "operator_name": operator_name,
        "grammar_id": portfolio["grammar_id"],
        "input_formula_hash": input_formula.formula_hash,
        "output_formula_hash": output_formula.formula_hash,
        "actual_certificate_type": portfolio["certificate_type"],
        "actual_certificate_hash": _payload_hash(certificate),
        "actual_checker_status": checker_status,
        "source_checker_result": check,
        "step_certificate": certificate,
        "preservation_type": preservation_type,
        "sat_lift_status": sat_lift_status,
        "unsat_preservation_status": unsat_preservation_status,
        "handoff_verified": True,
        "claim_boundary": portfolio["claim_boundary"],
    }


def _build_projected_affine_execution(control_kind: str | None = None) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], list[CNFFormula]]:
    projection, affine = _custom_projection_affine_pair()
    g10_cert = build_circuit_projection_certificate(projection).to_dict()
    core_formula = CNFFormula.from_raw_clauses(projection.core_clauses)
    g5_cert = build_affine_residue_certificate(affine).to_dict()
    steps = [
        _actual_step(
            step_id="s1",
            operator_name="CIRCUIT_PROJECTION_LIFT",
            input_formula=projection.formula,
            output_formula=core_formula,
            certificate=g10_cert,
            preservation_type=EQUI_SAT,
            sat_lift_status="CIRCUIT_PROJECTION_SAT_WITNESS_LIFTED",
        ),
        _actual_step(
            step_id="s2",
            operator_name="HIGH_ARITY_AFFINE_RESIDUE",
            input_formula=core_formula,
            output_formula=core_formula,
            certificate=g5_cert,
            preservation_type=EQUI_SAT,
            sat_lift_status="AFFINE_RESIDUE_SAT_WITNESS_VERIFIED",
        ),
    ]
    lifted = _assignment_from_payload((g10_cert.get("sat_lift") or {}).get("lifted_full_assignment"))
    result = {
        "result_type": SAT_CERTIFIED,
        "result_certificate_type": "CIRCUIT_PLUS_AFFINE_SAT_WITNESS",
        "result_certificate_hash": _payload_hash({"g10": g10_cert, "g5": g5_cert}),
        "verified_against_original_cnf": formula_satisfied(projection.formula, lifted),
    }
    trace = {
        "sat_witness": _assignment_key(lifted),
        "witness_lift_trace": [
            {"step_id": "s1", "lift_status": "lifted auxiliary gates", "verified": True},
            {"step_id": "s2", "lift_status": "affine solution agrees with projected core", "verified": True},
        ],
        "unsat_preservation_trace": [],
        "original_cnf_verification_status": "SAT_WITNESS_VERIFIED_AGAINST_ORIGINAL_CNF",
    }
    return steps, result, trace, [projection.formula, core_formula]


def _build_execution_chain(instance: PlannerExecutionInstance) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any], list[CNFFormula]]:
    if instance.instance_id == "projected_affine_plan_execution" or instance.control_kind in {
        "FAKE_EXECUTION",
        "FAKE_SAT_UNSAT",
        "FAKE_DRAT",
        "UNCHECKED_STEP",
        "BAD_HANDOFF",
        "MISSING_CERT",
        "DIAGNOSTIC_AS_RESULT",
        "BAD_WITNESS",
        "UNSAT_NO_PRESERVATION",
        "PLAN_TAMPER",
        "UNKNOWN_OPERATOR",
        "HARD_UNKNOWN",
        "FAILED",
    }:
        steps, result, trace, formulas = _build_projected_affine_execution(instance.control_kind)
        if instance.control_kind == "FAILED":
            steps[0]["actual_checker_status"] = PLANNER_EXECUTION_CERTIFICATE_FAILED
            steps[0]["step_certificate"]["original_formula_hash"] = "0" * 64
            steps[0]["actual_certificate_hash"] = _payload_hash(steps[0]["step_certificate"])
            result = {"result_type": EXECUTION_FAILED, "result_certificate_type": None, "result_certificate_hash": None, "verified_against_original_cnf": False}
            trace = {"sat_witness": None, "witness_lift_trace": [], "unsat_preservation_trace": [], "original_cnf_verification_status": "EXECUTION_FAILED"}
        elif instance.control_kind == "FAKE_EXECUTION":
            result["result_type"] = SAT_CERTIFIED
            trace["execution_copied_from_plan"] = True
        elif instance.control_kind == "FAKE_SAT_UNSAT":
            trace["sat_witness"] = None
            result["verified_against_original_cnf"] = False
        elif instance.control_kind == "FAKE_DRAT":
            result["result_certificate_type"] = "UNSAT_DRAT_EXPORTED_VERIFIED"
        elif instance.control_kind == "UNCHECKED_STEP":
            steps[0]["actual_checker_status"] = "NOT_RUN"
        elif instance.control_kind == "BAD_HANDOFF":
            steps[1]["input_formula_hash"] = "bad-handoff"
        elif instance.control_kind == "MISSING_CERT":
            steps[0]["step_certificate"] = None
        elif instance.control_kind == "DIAGNOSTIC_AS_RESULT":
            steps[0]["preservation_type"] = DIAGNOSTIC_STEP
        elif instance.control_kind == "BAD_WITNESS":
            trace["sat_witness"] = {"1": False}
            result["verified_against_original_cnf"] = False
        elif instance.control_kind == "UNSAT_NO_PRESERVATION":
            result = {"result_type": UNSAT_CERTIFIED, "result_certificate_type": "NATIVE_UNSAT", "result_certificate_hash": _payload_hash(steps), "verified_against_original_cnf": False}
            trace = {"sat_witness": None, "witness_lift_trace": [], "unsat_preservation_trace": [{"step_id": "s1", "verified": False}], "original_cnf_verification_status": "UNSAT_PRESERVATION_MISSING"}
            steps[0]["preservation_type"] = SAT_WITNESS_PRESERVING
        elif instance.control_kind == "UNKNOWN_OPERATOR":
            steps[0]["operator_name"] = "UNREGISTERED_EXECUTION_OPERATOR"
        elif instance.control_kind == "HARD_UNKNOWN":
            steps[0]["actual_checker_status"] = "UNKNOWN"
        return steps, result, trace, formulas

    if instance.instance_id == "circuit_plan_execution":
        projection = make_circuit_projection_instance("mux2_sat")
        cert = build_circuit_projection_certificate(projection).to_dict()
        core_formula = CNFFormula.from_raw_clauses(projection.core_clauses)
        steps = [
            _actual_step(
                step_id="s1",
                operator_name="CIRCUIT_PROJECTION_LIFT",
                input_formula=projection.formula,
                output_formula=core_formula,
                certificate=cert,
                preservation_type=EQUI_SAT,
                sat_lift_status="CIRCUIT_PROJECTION_SAT_WITNESS_LIFTED",
            )
        ]
        witness = _assignment_from_payload((cert.get("sat_lift") or {}).get("lifted_full_assignment"))
        return (
            steps,
            {
                "result_type": SAT_CERTIFIED,
                "result_certificate_type": "CIRCUIT_PROJECTION_SAT_WITNESS",
                "result_certificate_hash": _payload_hash(cert),
                "verified_against_original_cnf": formula_satisfied(projection.formula, witness),
            },
            {
                "sat_witness": _assignment_key(witness),
                "witness_lift_trace": [{"step_id": "s1", "verified": True}],
                "unsat_preservation_trace": [],
                "original_cnf_verification_status": "SAT_WITNESS_VERIFIED_AGAINST_ORIGINAL_CNF",
            },
            [projection.formula, core_formula],
        )

    if instance.instance_id == "proof_motif_plan_execution":
        motif = make_proof_motif_generalization_instance("ladder_near_4")
        cert = build_proof_motif_generalization_certificate(motif).to_dict()
        steps = [
            _actual_step(
                step_id="s1",
                operator_name="PROOF_MOTIF_GENERALIZATION_CHECKER",
                input_formula=motif.formula,
                output_formula=motif.formula,
                certificate=cert,
                preservation_type=UNSAT_PRESERVING,
                unsat_preservation_status="PROOF_MOTIF_GENERALIZED_UNSAT_CERTIFIED",
            )
        ]
        return (
            steps,
            {
                "result_type": UNSAT_CERTIFIED,
                "result_certificate_type": "PROOF_MOTIF_GENERALIZATION_CERTIFICATE",
                "result_certificate_hash": _payload_hash(cert),
                "verified_against_original_cnf": True,
            },
            {
                "sat_witness": None,
                "witness_lift_trace": [],
                "unsat_preservation_trace": [{"step_id": "s1", "verified": True, "mode": "native macro-proof"}],
                "original_cnf_verification_status": "UNSAT_PRESERVATION_VERIFIED",
            },
            [motif.formula],
        )

    if instance.instance_id == "graph_separator_plan_execution":
        separator = make_graph_separator_instance("separator_sat_pair")
        cert = build_graph_separator_certificate(separator).to_dict()
        witness = _assignment_from_payload((cert.get("sat_lift") or {}).get("combined_assignment"))
        steps = [
            _actual_step(
                step_id="s1",
                operator_name="GRAPH_SEPARATOR_LIFT",
                input_formula=separator.formula,
                output_formula=separator.formula,
                certificate=cert,
                preservation_type=SAT_WITNESS_PRESERVING,
                sat_lift_status="GRAPH_SEPARATOR_SAT_WITNESS_LIFTED",
            )
        ]
        return (
            steps,
            {
                "result_type": SAT_CERTIFIED,
                "result_certificate_type": "GRAPH_SEPARATOR_LIFT_CERTIFICATE",
                "result_certificate_hash": _payload_hash(cert),
                "verified_against_original_cnf": formula_satisfied(separator.formula, witness),
            },
            {
                "sat_witness": _assignment_key(witness),
                "witness_lift_trace": [{"step_id": "s1", "verified": True}],
                "unsat_preservation_trace": [],
                "original_cnf_verification_status": "SAT_WITNESS_VERIFIED_AGAINST_ORIGINAL_CNF",
            },
            [separator.formula],
        )

    if instance.instance_id == "composed_plan_execution":
        composed = make_composed_instance("composed_sat_lift")
        cert = build_composed_orchestration_certificate(composed).to_dict()
        witness = _assignment_from_payload((cert.get("lift_trace") or {}).get("final_witness"))
        steps = [
            _actual_step(
                step_id="s1",
                operator_name="COMPOSED_OPERATOR_ORCHESTRATION",
                input_formula=composed.formula,
                output_formula=composed.formula,
                certificate=cert,
                preservation_type=NATIVE_CERTIFICATE_ONLY,
                sat_lift_status="COMPOSED_ORCHESTRATION_WITNESS_LIFTED",
            )
        ]
        return (
            steps,
            {
                "result_type": SAT_CERTIFIED,
                "result_certificate_type": "COMPOSED_ORCHESTRATION_CERTIFICATE",
                "result_certificate_hash": _payload_hash(cert),
                "verified_against_original_cnf": formula_satisfied(composed.formula, witness),
            },
            {
                "sat_witness": _assignment_key(witness),
                "witness_lift_trace": [{"step_id": "s1", "verified": True}],
                "unsat_preservation_trace": [],
                "original_cnf_verification_status": "SAT_WITNESS_VERIFIED_AGAINST_ORIGINAL_CNF",
            },
            [composed.formula],
        )

    if instance.instance_id == "mismatch_control":
        projection = make_circuit_projection_instance("mux2_sat")
        cert = build_circuit_projection_certificate(projection).to_dict()
        core_formula = CNFFormula.from_raw_clauses(projection.core_clauses)
        steps = [
            _actual_step(
                step_id="s1",
                operator_name="CIRCUIT_PROJECTION_LIFT",
                input_formula=projection.formula,
                output_formula=core_formula,
                certificate=cert,
                preservation_type=EQUI_SAT,
                sat_lift_status="CIRCUIT_PROJECTION_SAT_WITNESS_LIFTED",
            )
        ]
        return (
            steps,
            {"result_type": DIAGNOSTIC_ONLY, "result_certificate_type": None, "result_certificate_hash": None, "verified_against_original_cnf": False},
            {"sat_witness": None, "witness_lift_trace": [], "unsat_preservation_trace": [], "original_cnf_verification_status": "MISMATCH_NO_RESULT_CLAIM"},
            [projection.formula, core_formula],
        )

    raise ValueError(f"cannot build execution chain for {instance.instance_id}")


def _planned_chain_from_plan(plan_cert: dict[str, Any]) -> list[dict[str, Any]]:
    selected = plan_cert.get("selected_plan_id")
    for plan in plan_cert.get("proposed_plans", []):
        if plan.get("plan_id") == selected:
            return [dict(step) for step in plan.get("operator_sequence", [])]
    return []


def _compare_plan_to_actual(planned: list[dict[str, Any]], actual: list[dict[str, Any]]) -> dict[str, Any]:
    matched: list[dict[str, str]] = []
    mismatched: list[dict[str, Any]] = []
    for idx, (pstep, astep) in enumerate(zip(planned, actual), start=1):
        reasons: list[str] = []
        if pstep.get("operator_name") != astep.get("operator_name"):
            reasons.append("operator")
        if pstep.get("expected_certificate_type") != astep.get("actual_certificate_type"):
            reasons.append("certificate_type")
        if pstep.get("preservation_required") == "UNSAT_PRESERVATION" and astep.get("preservation_type") not in UNSAT_PRESERVING_TYPES:
            reasons.append("preservation")
        if reasons:
            mismatched.append({"planned_step": pstep.get("step_id"), "actual_step": astep.get("step_id"), "reasons": reasons})
        else:
            matched.append({"planned_step": pstep.get("step_id"), "actual_step": astep.get("step_id"), "operator_name": astep.get("operator_name")})
    missing = [step.get("step_id") for step in planned[len(actual) :]]
    extra = [step.get("step_id") for step in actual[len(planned) :]]
    if len(matched) == len(planned) == len(actual) and not mismatched:
        status = MATCH
    elif matched and not mismatched:
        status = PARTIAL_MATCH
    else:
        status = MISMATCH
    return {
        "comparison_status": status,
        "matched_steps": matched,
        "mismatched_steps": mismatched,
        "missing_steps": missing,
        "extra_steps": extra,
        "mismatch_reason": "; ".join(
            [f"mismatched={len(mismatched)}", f"missing={len(missing)}", f"extra={len(extra)}"]
        )
        if status != MATCH
        else None,
    }


def build_planner_execution_certificate(
    instance: PlannerExecutionInstance,
) -> tuple[PlannerExecutionCertificate, dict[str, Any]]:
    plan_cert = build_collapse_plan_certificate(instance.plan_instance).to_dict()
    actual_steps, result, witness_trace, formulas = _build_execution_chain(instance)
    if instance.control_kind == "PLAN_TAMPER":
        plan_cert["formula_hash"] = "0" * 64
    planned_chain = _planned_chain_from_plan(plan_cert)
    comparison = _compare_plan_to_actual(planned_chain, actual_steps)
    if result.get("result_type") == EXECUTION_FAILED:
        comparison["comparison_status"] = EXECUTION_FAILED
    formula_summaries = {_formula_summary(formula)["formula_hash"]: _formula_summary(formula) for formula in formulas}
    handoff_trace = {
        "formula_hashes": [formula.formula_hash for formula in formulas],
        "formula_summaries": formula_summaries,
        "step_input_output_hashes": [
            {"step_id": step["step_id"], "input_formula_hash": step["input_formula_hash"], "output_formula_hash": step["output_formula_hash"]}
            for step in actual_steps
        ],
        "all_handoffs_verified": all(step.get("handoff_verified") for step in actual_steps),
    }
    status = (
        PLANNER_EXECUTION_MATCH_VERIFIED
        if comparison["comparison_status"] == MATCH
        else PLANNER_EXECUTION_MISMATCH_VERIFIED
        if comparison["comparison_status"] in {PARTIAL_MATCH, MISMATCH}
        else PLANNER_EXECUTION_DIAGNOSTIC_ONLY
    )
    public_category = (
        "SAT_PLANNER_GUIDED_EXECUTION_NATIVE_CERTIFIED"
        if result.get("result_type") == SAT_CERTIFIED and comparison["comparison_status"] == MATCH
        else "UNSAT_PLANNER_GUIDED_EXECUTION_NATIVE_CERTIFIED"
        if result.get("result_type") == UNSAT_CERTIFIED and comparison["comparison_status"] == MATCH
        else "PLANNER_EXECUTION_DIAGNOSTIC_ONLY"
    )
    cert = PlannerExecutionCertificate(
        type="PLANNER_EXECUTION_CERTIFICATE",
        instance_id=instance.instance_id,
        original_formula_hash=instance.formula.formula_hash,
        plan_certificate_hash=_payload_hash(plan_cert),
        plan_certificate_summary={
            "type": plan_cert.get("type"),
            "instance_id": plan_cert.get("instance_id"),
            "formula_hash": plan_cert.get("formula_hash"),
            "selected_plan_id": plan_cert.get("selected_plan_id"),
            "execution_status": plan_cert.get("execution_status"),
            "checker_status": plan_cert.get("checker_status"),
            "claimed_result": plan_cert.get("claimed_result"),
        },
        planned_chain=planned_chain,
        actual_execution_chain=actual_steps,
        comparison=comparison,
        execution_result=result,
        handoff_trace=handoff_trace,
        witness_or_unsat_trace=witness_trace,
        evidence_grade=FINITE_PLANNER_EXECUTION_VERIFIED,
        drat_claim="PLANNER_EXECUTION_DRAT_NOT_CLAIMED",
        status=status,
        claim_boundary="Planner-guided execution certificate only; no theorem, completeness, strictness, or P-vs-NP claim.",
        checker_status="NOT_RUN",
        public_category=public_category,
    )
    check = check_planner_execution_certificate(instance.formula, plan_cert, cert)
    data = cert.to_dict()
    data["checker_status"] = check["checker_status"]
    data["status"] = check["status"]
    if check["checker_status"] != PLANNER_EXECUTION_CERTIFICATE_VERIFIED:
        data["public_category"] = "PLANNER_EXECUTION_DIAGNOSTIC_ONLY"
    return PlannerExecutionCertificate(**data), plan_cert


def _contains_forbidden_status_or_claim(data: Any, errors: list[str]) -> None:
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and value in FORBIDDEN_STATUS_VALUES:
                errors.append(f"FORBIDDEN_STATUS:{value}")
            _contains_forbidden_status_or_claim(value, errors)
    elif isinstance(data, list):
        for item in data:
            _contains_forbidden_status_or_claim(item, errors)
    elif isinstance(data, str):
        lowered = data.lower()
        for fragment in FORBIDDEN_CLAIM_FRAGMENTS:
            if fragment in lowered:
                errors.append(f"FORBIDDEN_CLAIM_FRAGMENT:{fragment}")


def check_planner_execution_certificate(
    original_formula: CNFFormula,
    plan_certificate: dict[str, Any],
    execution_certificate: PlannerExecutionCertificate | dict[str, Any],
) -> dict[str, Any]:
    data = execution_certificate.to_dict() if isinstance(execution_certificate, PlannerExecutionCertificate) else dict(execution_certificate)
    errors: list[str] = []
    warnings: list[str] = []
    _contains_forbidden_status_or_claim(data, errors)
    if data.get("type") != "PLANNER_EXECUTION_CERTIFICATE":
        errors.append("CERTIFICATE_TYPE_MISMATCH")
    if data.get("original_formula_hash") != original_formula.formula_hash:
        errors.append("ORIGINAL_FORMULA_HASH_MISMATCH")
    if data.get("plan_certificate_hash") != _payload_hash(plan_certificate):
        errors.append("PLAN_CERTIFICATE_HASH_MISMATCH")
    plan_check = check_collapse_plan_certificate(original_formula, plan_certificate)
    if plan_check.get("status") != COLLAPSE_PLANNER_PLAN_VERIFIED:
        errors.append("PLAN_CERTIFICATE_NOT_VERIFIED")
    if plan_certificate.get("execution_status") != EXECUTION_REQUIRED:
        errors.append("PLAN_DOES_NOT_REQUIRE_EXECUTION")
    if plan_certificate.get("claimed_result") not in {"PLAN_ONLY", "PLAN_ONLY_NO_RESULT"}:
        errors.append("PLAN_IS_NOT_PLAN_ONLY")
    if data.get("evidence_grade") != FINITE_PLANNER_EXECUTION_VERIFIED:
        errors.append("EVIDENCE_GRADE_MISMATCH")
    if data.get("drat_claim") != "PLANNER_EXECUTION_DRAT_NOT_CLAIMED":
        errors.append("FAKE_DRAT_EXECUTION_CLAIM")
    if data.get("execution_result", {}).get("result_certificate_type") == "UNSAT_DRAT_EXPORTED_VERIFIED":
        errors.append("FAKE_DRAT_EXECUTION_CLAIM")
    if data.get("witness_or_unsat_trace", {}).get("execution_copied_from_plan"):
        errors.append("FAKE_EXECUTION_RECORD")

    planned = _planned_chain_from_plan(plan_certificate)
    actual = list(data.get("actual_execution_chain") or [])
    if not actual:
        errors.append("ACTUAL_EXECUTION_CHAIN_MISSING")
    recomputed_comparison = _compare_plan_to_actual(planned, actual)
    if (data.get("execution_result") or {}).get("result_type") == EXECUTION_FAILED:
        recomputed_comparison["comparison_status"] = EXECUTION_FAILED
    recorded_comparison = data.get("comparison") or {}
    if recorded_comparison.get("comparison_status") != recomputed_comparison.get("comparison_status"):
        errors.append("COMPARISON_STATUS_NOT_RECOMPUTED")
    for key in ["matched_steps", "mismatched_steps", "missing_steps", "extra_steps"]:
        if recorded_comparison.get(key) != recomputed_comparison.get(key):
            errors.append(f"COMPARISON_{key.upper()}_MISMATCH")

    summaries = data.get("handoff_trace", {}).get("formula_summaries") or {}
    formula_by_hash = {original_formula.formula_hash: original_formula}
    for formula_hash, summary in summaries.items():
        formula = _formula_from_summary(summary)
        if formula.formula_hash != formula_hash:
            errors.append(f"FORMULA_SUMMARY_HASH_MISMATCH:{formula_hash}")
        formula_by_hash[formula_hash] = formula

    current_hash = original_formula.formula_hash
    diagnostic_step_seen = False
    steps_verified = 0
    portfolio = _portfolio_by_name()
    result = data.get("execution_result") or {}
    result_type = result.get("result_type")
    execution_failed_report = result_type == EXECUTION_FAILED
    for step in actual:
        operator = step.get("operator_name")
        if operator not in portfolio:
            errors.append(f"UNKNOWN_OPERATOR:{operator}")
            continue
        if step.get("grammar_id") != portfolio[operator]["grammar_id"]:
            errors.append(f"GRAMMAR_MISMATCH:{step.get('step_id')}")
        if step.get("actual_certificate_type") != portfolio[operator]["certificate_type"]:
            errors.append(f"CERTIFICATE_TYPE_MISMATCH:{step.get('step_id')}")
        if step.get("input_formula_hash") != current_hash:
            errors.append(f"HANDOFF_INPUT_HASH_MISMATCH:{step.get('step_id')}")
        input_formula = formula_by_hash.get(step.get("input_formula_hash"))
        output_formula = formula_by_hash.get(step.get("output_formula_hash"))
        if input_formula is None or output_formula is None:
            errors.append(f"FORMULA_HANDOFF_SUMMARY_MISSING:{step.get('step_id')}")
            continue
        cert = step.get("step_certificate")
        if not cert:
            errors.append(f"ACTUAL_STEP_CERTIFICATE_MISSING:{step.get('step_id')}")
            continue
        if step.get("actual_certificate_hash") != _payload_hash(cert):
            errors.append(f"ACTUAL_CERTIFICATE_HASH_MISMATCH:{step.get('step_id')}")
        check = _dispatch_step_certificate_check(operator, input_formula, cert)
        step_verified = _step_status_from_check(operator, check)
        if not step_verified and not execution_failed_report:
            errors.append(f"ACTUAL_STEP_CERTIFICATE_FAILED:{step.get('step_id')}")
        if step.get("actual_checker_status") != PLANNER_EXECUTION_STEP_VERIFIED and not (
            execution_failed_report and step.get("actual_checker_status") == PLANNER_EXECUTION_CERTIFICATE_FAILED
        ):
            errors.append(f"ACTUAL_STEP_NOT_VERIFIED:{step.get('step_id')}")
        elif step.get("actual_checker_status") == PLANNER_EXECUTION_STEP_VERIFIED:
            steps_verified += 1
        if step.get("preservation_type") == DIAGNOSTIC_STEP:
            diagnostic_step_seen = True
        if not step.get("handoff_verified"):
            errors.append(f"HANDOFF_FLAG_FALSE:{step.get('step_id')}")
        current_hash = step.get("output_formula_hash")

    if data.get("handoff_trace", {}).get("all_handoffs_verified") is not True:
        errors.append("HANDOFF_TRACE_FLAG_FALSE")
    if any(left.get("output_formula_hash") != right.get("input_formula_hash") for left, right in zip(actual, actual[1:])):
        errors.append("FORMULA_HANDOFF_HASH_MISMATCH")

    trace = data.get("witness_or_unsat_trace") or {}
    if diagnostic_step_seen and result_type in {SAT_CERTIFIED, UNSAT_CERTIFIED}:
        errors.append("DIAGNOSTIC_STEP_USED_AS_RESULT")
    if recorded_comparison.get("comparison_status") in {MISMATCH, EXECUTION_FAILED} and data.get("status") == PLANNER_EXECUTION_MATCH_VERIFIED:
        errors.append("MISMATCH_CERTIFIES_PLANNER_SUCCESS")
    if result_type == SAT_CERTIFIED:
        witness = _assignment_from_payload(trace.get("sat_witness"))
        if not witness:
            errors.append("SAT_WITNESS_MISSING")
        if result.get("verified_against_original_cnf") is not True:
            errors.append("SAT_RESULT_NOT_VERIFIED_AGAINST_ORIGINAL")
        if not formula_satisfied(original_formula, witness):
            errors.append("SAT_WITNESS_DOES_NOT_SATISFY_ORIGINAL_CNF")
    elif result_type == UNSAT_CERTIFIED:
        if not all(step.get("preservation_type") in UNSAT_PRESERVING_TYPES for step in actual):
            errors.append("UNSAT_STEP_WITHOUT_PRESERVATION")
        if not all(item.get("verified") for item in trace.get("unsat_preservation_trace", [])):
            errors.append("UNSAT_PRESERVATION_TRACE_NOT_VERIFIED")
    elif result_type == EXECUTION_FAILED:
        if result.get("verified_against_original_cnf"):
            errors.append("FAILED_EXECUTION_HAS_RESULT_CLAIM")
    elif result_type != DIAGNOSTIC_ONLY:
        errors.append("INVALID_EXECUTION_RESULT_TYPE")

    checker_status = PLANNER_EXECUTION_CERTIFICATE_VERIFIED if not errors else PLANNER_EXECUTION_CERTIFICATE_FAILED
    status = (
        PLANNER_EXECUTION_MATCH_VERIFIED
        if checker_status == PLANNER_EXECUTION_CERTIFICATE_VERIFIED and recorded_comparison.get("comparison_status") == MATCH
        else PLANNER_EXECUTION_MISMATCH_VERIFIED
        if checker_status == PLANNER_EXECUTION_CERTIFICATE_VERIFIED and recorded_comparison.get("comparison_status") in {PARTIAL_MATCH, MISMATCH}
        else PLANNER_EXECUTION_DIAGNOSTIC_ONLY
        if checker_status == PLANNER_EXECUTION_CERTIFICATE_VERIFIED
        else PLANNER_EXECUTION_CERTIFICATE_FAILED
    )
    return {
        "checker_status": checker_status,
        "status": status,
        "errors": errors,
        "warnings": warnings,
        "plan_status": plan_check.get("status"),
        "comparison_status": recorded_comparison.get("comparison_status"),
        "execution_result_type": result_type,
        "steps_verified": steps_verified,
        "handoffs_verified": checker_status == PLANNER_EXECUTION_CERTIFICATE_VERIFIED and not any("HANDOFF" in error for error in errors),
        "claim_boundary": "Planner-guided execution result only for this finite checked execution; no theorem, completeness, or P-vs-NP claim.",
    }


def _row_from_certificate(cert: PlannerExecutionCertificate) -> dict[str, Any]:
    data = cert.to_dict()
    return {
        "instance_id": data["instance_id"],
        "checker_status": data["checker_status"],
        "status": data["status"],
        "comparison_status": data["comparison"]["comparison_status"],
        "result_type": data["execution_result"]["result_type"],
        "step_count": len(data["actual_execution_chain"]),
        "matched_steps": len(data["comparison"]["matched_steps"]),
        "public_category": data["public_category"],
        "evidence_grade": data["evidence_grade"],
    }


def _report(rows: list[dict[str, Any]], delta: dict[str, Any]) -> str:
    lines = [
        "# Planner-Guided Execution Report",
        "",
        "v2.20 adds G13_PLANNER_GUIDED_EXECUTION_PROTOTYPE.",
        "",
        "A G12 plan is loaded and verified first, but it is not execution. G13 then checks a separate actual execution chain, formula handoffs, step certificates, and result obligations.",
        "",
        "Matching a plan does not prove all plans succeed. Mismatches and failed executions are reported without planner-success, SAT/UNSAT, DRAT, theorem, completeness, or P-vs-NP claims.",
        "",
        "## Delta Summary",
        "",
        "```json",
        stable_json(delta),
        "```",
        "",
        "## Rows",
        "",
    ]
    for row in rows:
        lines.append(f"- {row['instance_id']}: {row['comparison_status']} / {row['result_type']} / {row['checker_status']}")
    lines.append("")
    return "\n".join(lines)


def run_planner_execution_lab(
    instances: Iterable[str],
    out_root: str | Path,
    *,
    strict: bool = False,
    zip_path: str | Path | None = None,
) -> dict[str, Any]:
    root = Path(out_root)
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True, exist_ok=True)
    certificates: list[dict[str, Any]] = []
    plans: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    checker_rows: list[dict[str, Any]] = []
    for instance_id in instances:
        instance = make_planner_execution_instance(instance_id)
        cert, plan = build_planner_execution_certificate(instance)
        cert_data = cert.to_dict()
        certificates.append(cert_data)
        plans.append(plan)
        row = _row_from_certificate(cert)
        rows.append(row)
        checker_rows.append(
            {
                "instance_id": cert.instance_id,
                "checker_status": cert.checker_status,
                "status": cert.status,
                "comparison_status": cert.comparison["comparison_status"],
                "result_type": cert.execution_result["result_type"],
            }
        )
        cnf_path = root / "original_cnf" / f"{instance_id}.cnf"
        cnf_path.parent.mkdir(parents=True, exist_ok=True)
        cnf_path.write_text(instance.formula.canonical_dimacs(), encoding="utf-8", newline="\n")
        _write_json(root / "plans" / f"{instance_id}_plan.json", plan)
        _write_json(root / "certificates" / f"{instance_id}_execution.json", cert_data)

    verified = [row for row in rows if row["checker_status"] == PLANNER_EXECUTION_CERTIFICATE_VERIFIED]
    match_rows = [row for row in verified if row["comparison_status"] == MATCH]
    mismatch_rows = [row for row in verified if row["comparison_status"] in {PARTIAL_MATCH, MISMATCH}]
    failed_rows = [row for row in rows if row["result_type"] == EXECUTION_FAILED]
    delta = {
        "operator_added": G13_GRAMMAR,
        "evidence_grade": FINITE_PLANNER_EXECUTION_VERIFIED,
        "instances_total": len(rows),
        "verified_execution_certificates": len(verified),
        "match_count": len(match_rows),
        "mismatch_or_partial_count": len(mismatch_rows),
        "failed_execution_controls": len(failed_rows),
        "sat_certified_count": sum(1 for row in verified if row["result_type"] == SAT_CERTIFIED),
        "unsat_certified_count": sum(1 for row in verified if row["result_type"] == UNSAT_CERTIFIED),
        "negative_controls_rejected": sum(1 for row in rows if row["checker_status"] == PLANNER_EXECUTION_CERTIFICATE_FAILED),
        "claim_boundary": "Finite planner execution evidence only; no theorem, completeness, DRAT, or P-vs-NP claim.",
        "strict": bool(strict),
    }
    comparisons = [
        {
            "instance_id": cert["instance_id"],
            "comparison": cert["comparison"],
        }
        for cert in certificates
    ]
    handoff = [
        {
            "instance_id": cert["instance_id"],
            "handoff_trace": cert["handoff_trace"],
        }
        for cert in certificates
    ]
    witness_or_unsat = [
        {
            "instance_id": cert["instance_id"],
            "execution_result": cert["execution_result"],
            "witness_or_unsat_trace": cert["witness_or_unsat_trace"],
        }
        for cert in certificates
    ]
    _write_json(root / "planner_execution_certificates.json", certificates)
    _write_json(root / "planner_execution_checker_summary.json", checker_rows)
    _write_json(root / "plan_vs_execution_comparison.json", comparisons)
    _write_json(root / "execution_chain_summary.json", rows)
    _write_json(root / "handoff_verification_summary.json", handoff)
    _write_json(root / "witness_or_unsat_verification_summary.json", witness_or_unsat)
    _write_json(root / "g13_planner_execution_delta_summary.json", delta)
    _write_text(root / "PLANNER_GUIDED_EXECUTION_REPORT.md", _report(rows, delta))
    artifact_sha = None
    if zip_path is not None:
        artifact_sha = _make_zip(root, zip_path)
    return {
        "rows": rows,
        "certificates": certificates,
        "plans": plans,
        "planner_execution_checker_summary": checker_rows,
        "g13_planner_execution_delta_summary": delta,
        "out_root": str(root),
        "artifact_zip": str(zip_path) if zip_path else None,
        "artifact_sha256": artifact_sha,
    }


def _load_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def _cmd_check(args: argparse.Namespace) -> int:
    formula = load_dimacs(args.cnf)
    plan = _load_json(args.plan)
    execution = _load_json(args.execution)
    result = check_planner_execution_certificate(formula, plan, execution)
    print(stable_json(result))
    return 0 if result["checker_status"] == PLANNER_EXECUTION_CERTIFICATE_VERIFIED else 1


def _cmd_run(args: argparse.Namespace) -> int:
    result = run_planner_execution_lab(args.instances, args.out_root, strict=args.strict, zip_path=args.zip)
    print(
        stable_json(
            {
                "out_root": result["out_root"],
                "artifact_zip": result["artifact_zip"],
                "artifact_sha256": result["artifact_sha256"],
                "delta": result["g13_planner_execution_delta_summary"],
            }
        )
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m witnora_core.planner_execution")
    sub = parser.add_subparsers(dest="cmd", required=True)
    check = sub.add_parser("check")
    check.add_argument("--cnf", required=True)
    check.add_argument("--plan", required=True)
    check.add_argument("--execution", required=True)
    check.set_defaults(func=_cmd_check)
    run = sub.add_parser("run")
    run.add_argument("--instances", nargs="+", required=True)
    run.add_argument("--out-root", required=True)
    run.add_argument("--strict", action="store_true")
    run.add_argument("--zip")
    run.set_defaults(func=_cmd_run)
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
